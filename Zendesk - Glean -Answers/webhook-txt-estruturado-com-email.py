from flask import Flask, request, jsonify
import requests
from config import ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN

app = Flask(__name__)

user_cache = {}
group_cache = {}

def get_ticket_details(ticket_id):
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    response = requests.get(url, auth=(ZENDESK_EMAIL, ZENDESK_API_TOKEN))
    if response.status_code == 200:
        return response.json()["ticket"]
    else:
        print(f"Erro ao buscar ticket: {response.status_code}")
        return {}

def get_ticket_comments(ticket_id):
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}/comments.json"
    response = requests.get(url, auth=(ZENDESK_EMAIL, ZENDESK_API_TOKEN))
    if response.status_code == 200:
        return response.json()["comments"]
    else:
        print(f"Erro ao buscar comentários: {response.status_code}")
        return []

def get_user_groups(user_id):
    if user_id in group_cache:
        return group_cache[user_id]

    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/{user_id}/groups.json"
    response = requests.get(url, auth=(ZENDESK_EMAIL, ZENDESK_API_TOKEN))
    if response.status_code == 200:
        groups = response.json()["groups"]
        group_names = [g["name"] for g in groups]
        group_cache[user_id] = group_names
        return group_names
    else:
        print(f"Erro ao buscar grupos do usuário {user_id}: {response.status_code}")
        return ["Erro ao buscar grupos"]

def get_user_info(user_id):
    if user_id in user_cache:
        return user_cache[user_id]

    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users/{user_id}.json"
    response = requests.get(url, auth=(ZENDESK_EMAIL, ZENDESK_API_TOKEN))
    if response.status_code == 200:
        user_data = response.json()["user"]
        email = user_data.get("email", "Email não encontrado")
        groups = get_user_groups(user_id)
        user_cache[user_id] = (email, groups)
        return email, groups
    else:
        print(f"Erro ao buscar usuário {user_id}: {response.status_code}")
        return "Erro ao buscar email", ["Erro ao buscar grupos"]

def salvar_ticket_em_txt(ticket_id, ticket, comentarios):
    subject = ticket.get("subject", "Sem assunto")
    priority = ticket.get("priority", "Sem prioridade")
    status = ticket.get("status", "Sem status")

    conteudo = f"-------------\nTicket ID: {ticket_id}\n"
    conteudo += f" - subject: {subject}\n"
    conteudo += f" - priority: {priority}\n"
    conteudo += f" - status: {status}\n"

    for idx, comentario in enumerate(comentarios, start=1):
        corpo = comentario.get("body", "").replace("\n", " ").strip()
        autor_id = comentario.get("author_id")
        autor_email, grupos = get_user_info(autor_id)
        grupos_str = ", ".join(grupos)
        conteudo += f" - comentário {idx} ({autor_email} | Grupos: {grupos_str}): {corpo}\n"

    nome_arquivo = f"ticket_{ticket_id}.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Arquivo salvo: {nome_arquivo}")

@app.route('/zendesk-to-glean', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook recebido!")

    ticket_id = data.get("ticket", {}).get("id") or data.get("detail", {}).get("id")
    if not ticket_id:
        return jsonify({"error": "Ticket ID não encontrado no payload"}), 400

    ticket = get_ticket_details(ticket_id)
    comentarios = get_ticket_comments(ticket_id)
    salvar_ticket_em_txt(ticket_id, ticket, comentarios)

    return jsonify({"message": f"Informações do ticket {ticket_id} salvas com sucesso!"}), 200

if __name__ == '__main__':
    app.run(port=5000)
