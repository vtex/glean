from flask import Flask, request, jsonify
import requests
import pandas as pd
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

@app.route('/zendesk-to-glean', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook recebido!")

    # Pega o ticket ID do payload do Zendesk
    ticket_id = data.get("ticket", {}).get("id") or data.get("detail", {}).get("id")
    if not ticket_id:
        return jsonify({"error": "Ticket ID não encontrado no payload"}), 400

    # Coleta os dados do ticket e comentários
    ticket = get_ticket_details(ticket_id)
    comments = get_ticket_comments(ticket_id)

    # Organiza os dados em um DataFrame
    ticket_df = pd.DataFrame([ticket])
    comments_df = pd.DataFrame([{
        "author": c["author_id"],
        "created_at": c["created_at"],
        "public": c["public"],
        "body": c["body"]
    } for c in comments])

    # Salva os dois DataFrames no mesmo Excel (em abas diferentes)
    filename = f"ticket_{ticket_id}.xlsx"
    with pd.ExcelWriter(filename) as writer:
        ticket_df.to_excel(writer, sheet_name="Ticket Info", index=False)
        comments_df.to_excel(writer, sheet_name="Comments", index=False)

    print(f"Arquivo salvo: {filename}")
    return jsonify({"message": f"Informações do ticket {ticket_id} salvas com sucesso!"}), 200

if __name__ == '__main__':
    app.run(port=5000)
