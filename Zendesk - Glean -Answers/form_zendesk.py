import requests
import pandas as pd
from config import ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_DOMAIN

def autenticar():
    return (ZENDESK_EMAIL, ZENDESK_TOKEN), {"Content-Type": "application/json"}

def buscar_ticket(ticket_id):
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth, headers = autenticar()
    resp = requests.get(url, auth=auth, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("ticket")
    else:
        raise Exception(f"Erro ao buscar ticket: {resp.status_code} - {resp.text}")

def buscar_nome_formulario(ticket_form_id):
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/ticket_forms/{ticket_form_id}.json"
    auth, headers = autenticar()
    resp = requests.get(url, auth=auth, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("ticket_form", {}).get("name", "Desconhecido")
    else:
        return "Erro ao buscar formulário"

def buscar_mapeamento_campos():
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/ticket_fields.json"
    auth, headers = autenticar()
    resp = requests.get(url, auth=auth, headers=headers)
    if resp.status_code == 200:
        campos = resp.json().get("ticket_fields", [])
        return {campo["id"]: campo["title"] for campo in campos}
    else:
        raise Exception(f"Erro ao buscar campos: {resp.status_code} - {resp.text}")

def extrair_dados_do_ticket(ticket_id):
    ticket = buscar_ticket(ticket_id)
    campos_nomes = buscar_mapeamento_campos()
    ticket_form_id = ticket.get("ticket_form_id")
    nome_formulario = buscar_nome_formulario(ticket_form_id) if ticket_form_id else "Nenhum"

    dados = []

    # Adiciona info do formulário como uma linha
    dados.append({
        "ID": "ticket_form_id",
        "Nome": "Formulário",
        "Valor": nome_formulario
    })

    # Campos personalizados
    for campo in ticket.get("custom_fields", []):
        id_campo = campo.get("id")
        nome_campo = campos_nomes.get(id_campo, "Nome não encontrado")
        valor = campo.get("value")
        dados.append({
            "ID": id_campo,
            "Nome": nome_campo,
            "Valor": valor
        })

    return dados

def salvar_em_excel(dados, ticket_id):
    df = pd.DataFrame(dados)
    nome_arquivo = f"ticket_{ticket_id}_dados.xlsx"
    df.to_excel(nome_arquivo, index=False)
    print(f"📁 Arquivo salvo: {nome_arquivo}")

if __name__ == "__main__":
    ticket_id = 1220592  # Substitua pelo ID real do ticket
    dados = extrair_dados_do_ticket(ticket_id)
    salvar_em_excel(dados, ticket_id)

