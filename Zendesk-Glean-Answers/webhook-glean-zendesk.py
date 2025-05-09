from dotenv import load_dotenv
load_dotenv()

import requests
import json
import datetime
import threading
import os
import logging
import warnings
import boto3 # AWS SDK para Python, para interagir com DynamoDB
from botocore.exceptions import ClientError # Para tratamento de erros do Boto3

from flask import Flask, request


# Configura o logging para registrar informações úteis no CloudWatch
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")

def get_env_variable(var_name, default_value=None, is_secret=False, var_type=str):
    """
    Busca uma variável de ambiente, registra e lança erro se obrigatória e não encontrada.
    Converte para o tipo especificado.
    """
    value_str = os.environ.get(var_name)

    if value_str is None:
        if default_value is not None:
            return default_value
        else:
            logging.error(f"Variável de ambiente obrigatória '{var_name}' não definida.")
            raise ValueError(f"Variável de ambiente obrigatória '{var_name}' não definida.")

    try:
        if var_type == bool:
            return value_str.lower() in ('true', '1', 't', 'yes', 'y')
        return var_type(value_str)
    except ValueError:
        logging.error(f"Não foi possível converter a variável de ambiente '{var_name}' ('{value_str}') para o tipo {var_type}.")
        raise ValueError(f"Variável de ambiente '{var_name}' com formato inválido.")

##--------------------------------------------------------------------------##
# Funções de interação com APIs (Zendesk, Glean)
##--------------------------------------------------------------------------##

def _get_zendesk_auth_details():
    """Retorna detalhes de autenticação e domínio do Zendesk a partir de variáveis de ambiente."""
    domain = get_env_variable('ZENDESK_SUBDOMAIN')
    email = get_env_variable('ZENDESK_EMAIL')
    token = get_env_variable('ZENDESK_API_TOKEN', is_secret=True)
    return domain, email, token

def _get_glean_auth_details():
    """Retorna detalhes de autenticação e URL da API Glean a partir de variáveis de ambiente."""
    token = get_env_variable('GLEAN_TOKEN', is_secret=True)
    api_url = get_env_variable('GLEAN_API_URL')
    return token, api_url

def buscar_dados_completos_do_ticket(ticket_id):
    """Busca os dados completos do ticket via API do Zendesk."""
    zendesk_domain, zendesk_email, zendesk_api_token = _get_zendesk_auth_details()
    url = f"https://{zendesk_domain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (zendesk_email, zendesk_api_token)
    
    logging.info(f"Buscando dados completos para o ticket ID: {ticket_id}")
    try:
        timeout_seconds = get_env_variable('ZENDESK_API_TIMEOUT', default_value=10, var_type=int)
        response = requests.get(url, auth=auth, timeout=timeout_seconds)
        response.raise_for_status() 
        return response.json().get("ticket", {}) 
    except requests.exceptions.Timeout:
        logging.error(f"Timeout ao buscar dados completos do ticket {ticket_id} da API do Zendesk.")
    except requests.exceptions.HTTPError as http_err:
        # Log response text if available for better debugging
        response_text = ""
        if 'response' in locals() and hasattr(response, 'text'):
            response_text = response.text
        logging.error(f"Erro HTTP ao buscar dados completos do ticket {ticket_id}: {http_err} - {response_text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro de requisição ao buscar dados completos do ticket {ticket_id}: {req_err}")
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON dos dados completos do ticket {ticket_id}.")
    return {}

def buscar_comentarios_do_ticket(ticket_id):
    """Busca os comentários do ticket via API do Zendesk."""
    zendesk_domain, zendesk_email, zendesk_api_token = _get_zendesk_auth_details()
    zendesk_headers = {'Content-Type': 'application/json'}
    url = f"https://{zendesk_domain}.zendesk.com/api/v2/tickets/{ticket_id}/comments.json"
    auth = (zendesk_email, zendesk_api_token)

    logging.info(f"Buscando comentários para o ticket ID: {ticket_id}")
    try:
        timeout_seconds = get_env_variable('ZENDESK_API_TIMEOUT', default_value=10, var_type=int)
        response = requests.get(url, headers=zendesk_headers, auth=auth, timeout=timeout_seconds)
        response.raise_for_status()
        return response.json().get("comments", [])
    except requests.exceptions.Timeout:
        logging.error(f"Timeout ao buscar comentários do ticket {ticket_id} da API do Zendesk.")
    except requests.exceptions.HTTPError as http_err:
        response_text = ""
        if 'response' in locals() and hasattr(response, 'text'):
            response_text = response.text
        logging.error(f"Erro HTTP ao buscar comentários do ticket {ticket_id}: {http_err} - {response_text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro de requisição ao buscar comentários do ticket {ticket_id}: {req_err}")
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON dos comentários do ticket {ticket_id}.")
    return []

def get_user_info(user_id):
    """Busca informações do usuário (email e grupos) no Zendesk."""
    zendesk_domain, zendesk_email, zendesk_api_token = _get_zendesk_auth_details()
    zendesk_headers = {'Content-Type': 'application/json'}
    auth = (zendesk_email, zendesk_api_token)
    timeout_seconds = get_env_variable('ZENDESK_API_TIMEOUT', default_value=10, var_type=int)

    email = "Email não encontrado" # Default value
    group_names = []

    user_url = f"https://{zendesk_domain}.zendesk.com/api/v2/users/{user_id}.json"
    logging.info(f"Buscando informações do usuário ID: {user_id}")
    try:
        res_user = requests.get(user_url, headers=zendesk_headers, auth=auth, timeout=timeout_seconds)
        res_user.raise_for_status()
        user_data = res_user.json().get("user", {})
        email = user_data.get("email", email) # Keeps default if not found
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar email do usuário {user_id}: {e}")
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON do usuário {user_id}.")

    groups_url = f"https://{zendesk_domain}.zendesk.com/api/v2/users/{user_id}/groups.json"
    logging.info(f"Buscando grupos para o usuário ID: {user_id}")
    try:
        res_groups = requests.get(groups_url, headers=zendesk_headers, auth=auth, timeout=timeout_seconds)
        res_groups.raise_for_status()
        groups_data = res_groups.json().get("groups", [])
        group_names = [g.get("name", "Nome do Grupo Ausente") for g in groups_data]
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao buscar grupos do usuário {user_id}: {e}")
        group_names.append("Erro ao buscar grupos") 
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON dos grupos do usuário {user_id}.")
        group_names.append("Erro ao buscar grupos (JSON)")
    return email, group_names

def gerar_texto_completo_do_ticket(ticket_id, ticket_details, comentarios):
    """Gera um texto consolidado com informações do ticket e comentários."""
    subject = ticket_details.get("subject", "Sem assunto")

    conteudo = f"-------------\nTicket ID: {ticket_id}\n"
    conteudo += f" - subject: {subject}\n"

    ignore_emails_str = get_env_variable("IGNORE_COMMENT_EMAILS", default_value="sistema@vtex.com.br,glean@vtex.com")
    ignore_emails = {email.strip() for email in ignore_emails_str.split(',') if email.strip()} # Ensure no empty strings

    for idx, comentario in enumerate(comentarios, start=1):
        corpo = comentario.get("body", "").replace("\n", " ").strip()
        autor_id = comentario.get("author_id")

        if autor_id is None:
            autor_email_str = "Autor Desconhecido"
            grupos_str = "N/A"
        else:
            autor_email, grupos = get_user_info(autor_id) # This function now returns defaults on error
            autor_email_str = str(autor_email) 
            grupos_str = ", ".join(grupos) if grupos else "Nenhum grupo"

        if autor_email_str in ignore_emails:
            logging.info(f"Ignorando comentário de {autor_email_str} no ticket {ticket_id}")
            continue
        conteudo += f" - comentário {idx} ({autor_email_str} | Grupos: {grupos_str}): {corpo}\n"
    return conteudo

def ask_glean(texto_ticket_completo, application_id):
    """Envia o texto do ticket para a Glean e retorna a resposta e o token."""
    glean_token, glean_api_url = _get_glean_auth_details()
    glean_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {glean_token}'
    }
    system_prompt = get_env_variable(
        "GLEAN_SYSTEM_PROMPT",
        default_value=(
            "Você receberá o conteúdo de um ticket do Zendesk. A estrutura será assim:\n\n"
            "-------------\nTicket ID: <número>\n"
            " - subject: <assunto do ticket>\n"
            " - comentário 1 (<autor> | Grupos: <grupos>): <conteúdo>\n"
            "...\n\n"
            "Com base nisso, gere uma sugestão de resposta para resolver o problema do cliente de forma clara e útil.\n\n"
            "A resposta deve ser educada e profissional, mantendo um tom amigável.\n\n"
        )
    )
    payload = {
        'stream': True,
        'applicationId': application_id,
        'messages': list(reversed([
            make_system_message(system_prompt),
            make_content_message(text=texto_ticket_completo)
        ]))
    }
    
    if get_env_variable("SAVE_GLEAN_PAYLOAD", default_value="False", var_type=bool):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        extracted_ticket_id_str = "unknown_ticket"
        try:
            # Best effort to extract ticket_id from the generated text for filename
            # Assumes "Ticket ID: <id>" is the second line of texto_ticket_completo
            lines = texto_ticket_completo.strip().splitlines()
            if len(lines) > 1 and lines[1].startswith("Ticket ID: "):
                extracted_ticket_id_str = lines[1].split(': ')[1].strip()
        except Exception: # Catch all for safety during string manipulation
            logging.warning("Could not reliably extract ticket_id for payload filename.", exc_info=True)

        filename = f"/tmp/envio_glean_{timestamp}_ticket_{extracted_ticket_id_str}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("Payload enviado para a Glean:\n\n")
                f.write(json.dumps(payload, indent=2))
            logging.info(f"Payload para Glean salvo em {filename}")
        except IOError as e:
            logging.error(f"Erro ao salvar payload da Glean em arquivo: {e}")

    logging.info(f"Enviando requisição para Glean para application_id: {application_id}")
    reply, token = None, None # Initialize
    try:
        timeout_seconds = get_env_variable('GLEAN_API_TIMEOUT', default_value=30, var_type=int)
        response = requests.post(glean_api_url, headers=glean_headers, json=payload, stream=True, timeout=timeout_seconds)
        response.raise_for_status()
        logging.info(f"Resposta da Glean recebida com status {response.status_code}")
        reply, token = process_response_message_stream(response)
    except requests.exceptions.Timeout:
        logging.error(f"Timeout ao chamar API da Glean.")
    except requests.exceptions.HTTPError as http_err:
        response_text = ""
        if 'response' in locals() and hasattr(response, 'text'):
            response_text = response.text
        logging.error(f"Erro HTTP da API da Glean: {http_err} - {response_text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro de requisição para API da Glean: {req_err}")
    except Exception as e: # Catch any other unexpected error during Glean call or response processing
        logging.error(f"Erro inesperado ao chamar Glean ou processar resposta: {e}", exc_info=True) 
    return reply, token

def make_system_message(text):
    """Cria uma mensagem de sistema para a API da Glean."""
    return {"author": "SYSTEM", 
            "messageType": "CONTENT", 
            "fragments": [{"text": text}]}

def make_content_message(author='USER', text=None, citations=None):
    """Cria uma mensagem de conteúdo para a API da Glean."""
    message = {'author': author, 'messageType': 'CONTENT'}
    if text: message['fragments'] = [{'text': text}]
    if citations: message['citations'] = citations # Note: Glean's API might expect citations in a specific part of the request
    return message

def process_response_message_stream(response):
    """Processa o stream de resposta da Glean, extraindo texto e citações."""
    resposta_texto = ''
    todas_citacoes = []
    token_glean = None 
    
    logging.info("Iniciando o processamento do stream da resposta da Glean...")
    decoded_line = "" # Initialize for potential error logging in except block
    try:
        for line in response.iter_lines():
            if line: # Filter out keep-alive new lines
                decoded_line = line.decode('utf-8') # Decode bytes to string
                line_json = json.loads(decoded_line) # Parse JSON string
                
                messages = line_json.get('messages', [])
                for msg in messages:
                    if token_glean is None: # Capture the first messageTrackingToken
                        token_glean = msg.get('messageTrackingToken')
                    texto_fragmento, citacoes_fragmento = process_message_fragment(msg)
                    resposta_texto += texto_fragmento
                    if citacoes_fragmento: # Ensure it's not None or empty
                        todas_citacoes.extend(citacoes_fragmento)
    except json.JSONDecodeError as e:
        logging.error(f"Erro ao decodificar linha do stream da Glean: {e}. Linha: '{decoded_line}'")
    except Exception as e:
        logging.error(f"Erro ao processar stream da Glean: {e}", exc_info=True)

    # Format unique citations
    citacoes_unicas_formatadas = ""
    if todas_citacoes:
        urls_vistas = set()
        citacoes_unicas_lista = []
        for citacao in todas_citacoes:
            url = citacao.get("url") or citacao.get("sourceDocument", {}).get("url")
            if url and url not in urls_vistas:
                urls_vistas.add(url)
                citacoes_unicas_lista.append(citacao)
        
        if citacoes_unicas_lista:
            citacoes_unicas_formatadas += "\n\n🔍 *Fontes mencionadas pela Glean:*\n"
            for i, citacao_obj in enumerate(citacoes_unicas_lista, start=1):
                # Prioritize text, then title, then URL for display
                fonte_texto = citacao_obj.get("text", "").strip() or \
                              citacao_obj.get("sourceDocument", {}).get("title", "").strip() or \
                              citacao_obj.get("url", "").strip() or \
                              citacao_obj.get("sourceDocument", {}).get("url", "").strip()
                if not fonte_texto: continue # Skip if no useful text/URL

                url_citacao = citacao_obj.get("url") or citacao_obj.get("sourceDocument", {}).get("url")
                if url_citacao:
                    citacoes_unicas_formatadas += f"{i}. [{fonte_texto}]({url_citacao})\n"
                else:
                    citacoes_unicas_formatadas += f"{i}. {fonte_texto}\n"
    
    resposta_final = resposta_texto + citacoes_unicas_formatadas
    logging.info(f"Processamento do stream da Glean concluído. Token presente: {token_glean is not None}")
    return resposta_final, token_glean

def process_message_fragment(message):
    """Extrai texto e citações de um fragmento de mensagem da Glean."""
    text = ''
    citations = [] # Initialize as empty list
    if message.get('messageType') == 'CONTENT':
        for fragment in message.get('fragments', []):
            text += fragment.get('text', '') # Safely get text
        # Citations are usually part of the message object, not inside fragments
        message_citations = message.get('citations')
        if message_citations: # Check if citations exist and is not None
             citations.extend(message_citations)
    return text, citations

def salvar_resposta_em_txt(ticket_id, resposta_glean):
    """Salva a resposta da Glean em um arquivo TXT no diretório /tmp/ (para debug)."""
    if not get_env_variable("SAVE_GLEAN_RESPONSE_TXT", default_value="False", var_type=bool):
        return # Skip saving if not enabled

    file_path = f"/tmp/resposta_glean_ticket_{ticket_id}.txt"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(resposta_glean)
        logging.info(f"Resposta da Glean para ticket {ticket_id} salva em {file_path}")
    except IOError as e:
        logging.error(f"Erro ao salvar resposta da Glean para ticket {ticket_id} em TXT: {e}")

def post_internal_note_to_zendesk(ticket_id, note_text):
    """Posta uma nota interna no ticket do Zendesk."""
    zendesk_domain, zendesk_email, zendesk_api_token = _get_zendesk_auth_details()
    zendesk_headers = {'Content-Type': 'application/json'}
    url = f"https://{zendesk_domain}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (zendesk_email, zendesk_api_token)
    aviso_glean = get_env_variable(
        "ZENDESK_GLEAN_NOTE_PREAMBLE",
        default_value=(
            "⚠️ Esta é uma sugestão gerada automaticamente por uma versão *piloto* do Assistente Glean para Zendesk. "
            "Sou acionado ao marcar 'Glean' em qualquer ticket!\n\n"
            "Por favor, revise a veracidade e clareza da resposta antes de enviar ao cliente. "
            "Qualquer feedback pode ser enviado para #glean-hub!\n\n"
        )
    )
    payload = {
        "ticket": {
            "comment": {
                "body": aviso_glean + note_text,
                "public": False # Ensures it's an internal note
            }
        }
    }
    logging.info(f"Postando nota interna no ticket Zendesk ID: {ticket_id}")
    try:
        timeout_seconds = get_env_variable('ZENDESK_API_TIMEOUT', default_value=15, var_type=int)
        response = requests.put(url, headers=zendesk_headers, auth=auth, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
        logging.info(f"Nota interna postada com sucesso no ticket {ticket_id} do Zendesk.")
    except requests.exceptions.Timeout:
        logging.error(f"Timeout ao postar nota interna no ticket Zendesk {ticket_id}.")
    except requests.exceptions.HTTPError as http_err:
        response_text = ""
        if 'response' in locals() and hasattr(response, 'text'):
            response_text = response.text
        logging.error(f"Erro HTTP ao postar nota interna no Zendesk para ticket {ticket_id}: {http_err} - {response_text}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro de requisição ao postar nota interna no Zendesk para ticket {ticket_id}: {req_err}")

def buscar_formulario_para_tickets(ticket_id):
    """Busca o ID do formulário do ticket no Zendesk."""
    # This function is similar to buscar_dados_completos_do_ticket but only needs ticket_form_id
    # It can be optimized if only form_id is needed, but reusing is fine for now.
    ticket_data = buscar_dados_completos_do_ticket(ticket_id) # Reuses the more general function
    if ticket_data:
        ticket_form_id = ticket_data.get("ticket_form_id")
        if ticket_form_id is None:
            logging.warning(f"ID do formulário do ticket (ticket_form_id) não encontrado para o ticket {ticket_id}.")
        return ticket_form_id
    logging.error(f"Não foi possível obter dados do ticket {ticket_id} para buscar form_id.")
    return None

##--------------------------------------------------------------------------##
# Funções de Persistência de Token (Excel em /tmp/ ou DynamoDB)
##--------------------------------------------------------------------------##
def salvar_token_em_dynamodb(ticket_id, token_glean, application_id):
    """Salva o token da Glean e informações relacionadas em uma tabela DynamoDB."""
    table_name = get_env_variable("DYNAMODB_TOKENS_TABLE_NAME", default_value=None)
    if not table_name:
        logging.warning("Nome da tabela DynamoDB (DYNAMODB_TOKENS_TABLE_NAME) não configurado. Não salvando token no DynamoDB.")
        return

    try:
        aws_region = get_env_variable("AWS_REGION_DYNAMODB", default_value=os.environ.get("AWS_REGION"))
        # Initialize Boto3 client/resource. For Lambda, this can be done globally for "warm" reuse.
        # However, initializing per call is safer if region/credentials might change (though less common in Lambda).
        if 'dynamodb_resource' not in globals(): # Basic check for global client (can be improved)
            if not aws_region:
                logging.warning("Região da AWS para DynamoDB não configurada (AWS_REGION_DYNAMODB ou AWS_REGION). Tentando sem especificar (pode usar padrão do SDK).")
                dynamodb_resource = boto3.resource('dynamodb')
            else:
                logging.info(f"Inicializando recurso DynamoDB para região: {aws_region}")
                dynamodb_resource = boto3.resource('dynamodb', region_name=aws_region)
            # Store it globally for potential reuse in the same Lambda container invocation
            # globals()['dynamodb_resource'] = dynamodb_resource 
        # else:
            # dynamodb_resource = globals()['dynamodb_resource']

        # For simplicity and to ensure fresh client if config changes, initialize per call here.
        # For high-throughput, consider global client initialization.
        if not aws_region:
            dynamodb_resource_local = boto3.resource('dynamodb')
        else:
            dynamodb_resource_local = boto3.resource('dynamodb', region_name=aws_region)
        table = dynamodb_resource_local.Table(table_name)

    except Exception as e:
        logging.error(f"Erro ao inicializar o recurso DynamoDB para a tabela '{table_name}': {e}", exc_info=True)
        return

    timestamp_atual_utc = datetime.datetime.utcnow().isoformat() + "Z"
    item_to_save = {
        'ticket_id': str(ticket_id),             # Chave de Partição (PK)
        'timestamp_salvo_utc': timestamp_atual_utc, # Chave de Classificação (SK) - permite múltiplos tokens por ticket ao longo do tempo
        'glean_message_tracking_token': str(token_glean),
        'glean_application_id': str(application_id) # AJUSTE: Adicionado application_id
    }

    logging.info(f"Tentando salvar token Glean para ticket {ticket_id} na tabela DynamoDB '{table_name}'")
    try:
        table.put_item(Item=item_to_save)
        logging.info(f"✅ Token Glean salvo no DynamoDB para ticket {ticket_id}. Item: {json.dumps(item_to_save)}")
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        error_message = e.response.get("Error", {}).get("Message", "N/A")
        logging.error(f"Erro do cliente DynamoDB ({error_code}) ao salvar token para ticket {ticket_id} na tabela '{table_name}': {error_message}", exc_info=True)
    except Exception as e:
        logging.error(f"Erro inesperado ao salvar token no DynamoDB para ticket {ticket_id} na tabela '{table_name}': {e}", exc_info=True)

##--------------------------------------------------------------------------##
# Função principal de processamento do Webhook
##--------------------------------------------------------------------------##
def processa_ticket(payload_data):
    """
    Processa o payload do webhook do Zendesk.
    Esta função é chamada pelo lambda_handler (em `lambda_zendesk_glean.py`).
    """
    if not isinstance(payload_data, dict):
        logging.error(f"Payload (payload_data) recebido não é um dicionário: {type(payload_data)}")
        return

    ticket_info = payload_data.get("ticket", {})
    ticket_id = ticket_info.get("id") # Assume que o ID do ticket é um número ou string

    if not ticket_id: # Checa se ticket_id é None ou vazio
        logging.error(f"ID do Ticket (ticket.id) não encontrado ou inválido no payload: {json.dumps(payload_data)}")
        return

    # Converte ticket_id para string para consistência, especialmente se for usado como chave no DynamoDB
    ticket_id_str = str(ticket_id)
    logging.info(f"Iniciando processamento para Zendesk Ticket ID: {ticket_id_str}")

    # Carregar mapeamentos e IDs padrão de variáveis de ambiente
    # Usar valores padrão que indicam "não configurado" para facilitar o debug se as vars não estiverem setadas
    ps_zendesk_id_conf = get_env_variable('PS_ZENDESK_ID', default_value="FORM_ID_PS_NOT_SET")
    ps_id_conf = get_env_variable('PS_ID', default_value="APP_ID_PS_NOT_SET")
    fse_zendesk_id_conf = get_env_variable('FSE_ZENDESK_ID', default_value="FORM_ID_FSE_NOT_SET")
    fse_id_conf = get_env_variable('FSE_ID', default_value="APP_ID_FSE_NOT_SET") # Este é também o fallback
    fin_zendesk_id_conf = get_env_variable('FIN_ZENDESK_ID', default_value="FORM_ID_FIN_NOT_SET")
    fin_id_conf = get_env_variable('FIN_ID', default_value="APP_ID_FIN_NOT_SET")

    form_to_app_id_mapping = {
        ps_zendesk_id_conf: ps_id_conf,
        fse_zendesk_id_conf: fse_id_conf,
        fin_zendesk_id_conf: fin_id_conf,
    }
    # O fallback default_app_id deve ser um ID de aplicação Glean válido
    default_app_id = get_env_variable('DEFAULT_GLEAN_APP_ID', default_value=fse_id_conf)

    form_id_raw = buscar_formulario_para_tickets(ticket_id_str)
    application_id = default_app_id # Assume padrão inicialmente

    if form_id_raw is not None:
        form_id_str_map = str(form_id_raw) # form_id_str já usado acima, renomear para clareza
        logging.info(f"Form ID para ticket {ticket_id_str}: {form_id_str_map}")
        if form_id_str_map in form_to_app_id_mapping:
            # Verifica se o valor mapeado não é o placeholder de "não configurado"
            mapped_app_id = form_to_app_id_mapping[form_id_str_map]
            if "NOT_SET" not in mapped_app_id:
                application_id = mapped_app_id
                logging.info(f"Application ID da Glean correspondente ao form ID {form_id_str_map} encontrado: {application_id}")
            else:
                logging.warning(f"Form ID {form_id_str_map} mapeado para um App ID não configurado ('{mapped_app_id}'). Usando application_id padrão: {default_app_id}")
        else:
            logging.warning(f"Form ID {form_id_str_map} não mapeado. Usando application_id padrão: {default_app_id}")
    else:
        logging.warning(f"Não foi possível determinar o form_id para o ticket {ticket_id_str}. Usando application_id padrão: {default_app_id}")

    # Validação final do application_id
    if "NOT_SET" in application_id:
        logging.error(f"Application ID final ('{application_id}') para o ticket {ticket_id_str} indica uma configuração ausente. Verifique as variáveis de ambiente PS_ID, FSE_ID, FIN_ID ou DEFAULT_GLEAN_APP_ID. Processamento interrompido.")
        return

    logging.info(f"Application ID da Glean selecionado para o ticket {ticket_id_str}: {application_id}")

    ticket_details = buscar_dados_completos_do_ticket(ticket_id_str)
    if not ticket_details:
        logging.error(f"Não foi possível buscar detalhes completos para o ticket {ticket_id_str}. Processamento interrompido.")
        return

    comentarios = buscar_comentarios_do_ticket(ticket_id_str)
    texto_ticket_completo = gerar_texto_completo_do_ticket(ticket_id_str, ticket_details, comentarios)
    if not texto_ticket_completo.strip():
        logging.warning(f"Texto completo gerado para o ticket {ticket_id_str} está vazio. Não chamando a Glean.")
        return

    response_from_glean, token_glean = ask_glean(texto_ticket_completo, application_id)

    if token_glean:
        persistence_method = get_env_variable("TOKEN_PERSISTENCE_METHOD", default_value="dynamodb").lower()
        logging.info(f"Método de persistência de token selecionado: {persistence_method}")

        if persistence_method == "dynamodb":
            salvar_token_em_dynamodb(ticket_id_str, token_glean, application_id) # AJUSTE: Passando application_id
        else:
            logging.warning(f"Método de persistência de token '{persistence_method}' desconhecido. Token não salvo.")
    else:
        logging.warning(f"Nenhum token de rastreamento da Glean recebido para o ticket {ticket_id_str}.")

    if response_from_glean:
        post_internal_note_to_zendesk(ticket_id_str, response_from_glean)
        salvar_resposta_em_txt(ticket_id_str, response_from_glean) # Salva em /tmp/ se habilitado
    else:
        logging.warning(f"Nenhuma resposta (conteúdo) da Glean para o ticket {ticket_id_str}.")
    
    logging.info(f"Processamento do Zendesk Ticket ID: {ticket_id_str} concluído.")

##--------------------------------------------------------------------------##
## Bloco para execução local com Flask (para testes)
##--------------------------------------------------------------------------##
if __name__ == "__main__":
    flask_app = Flask(__name__)

    @flask_app.route("/zendesk-to-glean", methods=["POST"])
    def zendesk_webhook_flask_endpoint():
        """Endpoint Flask para receber webhooks do Zendesk (para testes locais)."""
        try:
            webhook_data = request.get_json()
            if webhook_data is None:
                logging.error("Payload JSON vazio ou malformado recebido no endpoint Flask local.")
                return {"status": "error", "message": "Payload JSON inválido"}, 400
        except Exception as e: # Werkzeug pode levantar BadRequest em JSON malformado
            logging.error(f"Erro ao obter JSON do request Flask local: {e}")
            return {"status": "error", "message": "Erro ao processar payload JSON"}, 400

        logging.info("Payload recebido (Flask local):")
        # Use ensure_ascii=False para imprimir caracteres acentuados corretamente se houver no payload
        logging.info(json.dumps(webhook_data, indent=2, ensure_ascii=False))
        
        logging.info("Simulando execução local. Certifique-se que as variáveis de ambiente para persistência (DynamoDB/Excel) e APIs estão configuradas se necessário.")

        try:
            processing_thread = threading.Thread(target=processa_ticket, args=(webhook_data,))
            processing_thread.daemon = True # Permite que o programa principal termine mesmo que o thread ainda esteja rodando
            processing_thread.start()
            logging.info("Thread de processamento (Flask local) iniciada.")
            return {"status": "received"}, 200
        except Exception as e:
            logging.error(f"Erro ao iniciar thread de processamento (Flask local): {e}", exc_info=True)
            return {"status": "error", "message": "Erro interno ao iniciar processamento"}, 500

    try:
        flask_host = get_env_variable('FLASK_RUN_HOST', default_value='0.0.0.0')
        flask_port = get_env_variable('FLASK_RUN_PORT', default_value=5001, var_type=int)
        flask_debug = get_env_variable('FLASK_DEBUG_MODE', default_value="False", var_type=bool)
        
        logging.info(f"Iniciando servidor Flask local em http://{flask_host}:{flask_port}/ (Debug: {flask_debug})")
        # Para testes locais com DynamoDB, certifique-se que suas credenciais AWS
        # estão configuradas no ambiente (ex: via `aws configure`, variáveis de ambiente AWS_ACCESS_KEY_ID, etc.).
        flask_app.run(host=flask_host, port=flask_port, debug=flask_debug)
    except ValueError as e: # Captura erro de get_env_variable
        logging.error(f"Erro ao carregar configuração para o servidor Flask local: {e}")
    except Exception as e: # Outros erros ao iniciar o Flask
        logging.error(f"Erro inesperado ao tentar iniciar o servidor Flask local: {e}", exc_info=True)

