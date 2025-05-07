import requests
from config import ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_DOMAIN

def autenticar():
    return (ZENDESK_EMAIL, ZENDESK_TOKEN), {"Content-Type": "application/json"}

def buscar_nome_formulario(ticket_form_id):
    # URL para buscar o formulário com base no ticket_form_id
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/ticket_forms/{ticket_form_id}.json"
    auth, headers = autenticar()

    resp = requests.get(url, auth=auth, headers=headers)

    if resp.status_code == 200:
        # Pega o nome do formulário
        form_name = resp.json().get("ticket_form", {}).get("name", "Desconhecido")
        return form_name
    else:
        return "Erro ao buscar formulário"

def buscar_formulario_para_tickets(tickets_ids):
    # Recebe uma lista de IDs de tickets e retorna os dados de formulário
    for ticket_id in tickets_ids:
        print(f"🔍 Buscando dados do formulário para o ticket ID: {ticket_id}")

        # 1. Buscar os dados do ticket
        url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
        auth, headers = autenticar()

        resp = requests.get(url, auth=auth, headers=headers)

        if resp.status_code == 200:
            ticket = resp.json().get("ticket", {})
            ticket_form_id = ticket.get("ticket_form_id")

            # 2. Buscar o nome do formulário usando o ticket_form_id
            form_name = buscar_nome_formulario(ticket_form_id)
            
            # Verifica se o nome do formulário corresponde a "💻Product"
            if ticket_form_id == 360001397472:
                print(f"📋 Ticket ID {ticket_id}:")
                print(f"  - ID do Formulário: {ticket_form_id}")
                print(f"  - Nome do Formulário: {form_name}")
        else:
            print(f"❌ Erro ao buscar ticket ID {ticket_id}: {resp.status_code} - {resp.text}")
        print("-" * 40)

# Exemplo de uso
if __name__ == "__main__":
    tickets_ids = [1220592, 1220963, 1217937, 1220592, 1196765, 1208527]  # Substitua pelos IDs reais
    buscar_formulario_para_tickets(tickets_ids)
