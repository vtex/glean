from flask import Flask, request, jsonify
import requests
from config import ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN

app = Flask(__name__)

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

def salvar_ticket_em_txt(ticket_id, detalhes_ticket, comentarios):
    subject = detalhes_ticket.get("subject", "Não informado")
    priority = detalhes_ticket.get("priority", "Não informado")
    status = detalhes_ticket.get("status", "Não informado")

    conteudo = f"-------------\n"
    conteudo += f"Ticket ID: {ticket_id}\n"
    conteudo += f" - subject: {subject}\n"
    conteudo += f" - priority: {priority}\n"
    conteudo += f" - status: {status}\n"

    for idx, comentario in enumerate(comentarios, start=1):
        corpo = comentario.get("body", "").replace("\n", " ").strip()
        conteudo += f" - comentário {idx}: {corpo}\n"

    nome_arquivo = f"ticket_{ticket_id}.txt"
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(conteudo)

    print(f"Ticket salvo como {nome_arquivo}")

@app.route('/zendesk-to-glean', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook recebido!")

    ticket_id = data.get("ticket", {}).get("id") or data.get("detail", {}).get("id")
    if not ticket_id:
        return jsonify({"error": "Ticket ID não encontrado no payload"}), 400

    ticket = get_ticket_details(ticket_id)
    comments = get_ticket_comments(ticket_id)

    salvar_ticket_em_txt(ticket_id, ticket, comments)

    return jsonify({"message": f"Informações do ticket {ticket_id} salvas com sucesso!"}), 200

if __name__ == '__main__':
    app.run(port=5000)
