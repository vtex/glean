import pandas as pd
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

from config import GLEAN_FEEDBACK_URL, GLEAN_TOKEN, EXCEL_PATH

def buscar_tracking_token(ticket_id):
    try:
        df = pd.read_excel(EXCEL_PATH)
        linhas = df[df['ticket_id'] == ticket_id]
        print(linhas)
        if not linhas.empty:
            return linhas['tracking_token'].tolist()
        else:
            print("❌ Ticket ID não encontrado na planilha.")
            return []
    except Exception as e:
        print(f"❌ Erro ao ler a planilha: {e}")
        return []

def enviar_feedback_para_glean(tracking_token, feedback):
    evento = {
        "positive": "UPVOTE",
        "negative": "DOWNVOTE"
    }.get(feedback.lower())

    if not evento:
        print(f"❌ Tipo de feedback inválido: {feedback}")
        return

    payload = {
        "trackingTokens": [tracking_token],
        "event": evento
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLEAN_TOKEN}"
    }
    response = requests.post(GLEAN_FEEDBACK_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Feedback '{evento}' enviado para token {tracking_token}.")
    else:
        print(f"❌ Erro ao enviar feedback para Glean: {response.status_code} - {response.text}")

@app.route("/webhook/feedback", methods=["POST"])
def receber_webhook_feedback():
    data = request.json
    print(f"request data: {request.data}")
    print(f"request headers: {request.headers}")
    print(f"parsed JSON: {data}")
    ticket = data.get("ticket", {})
    ticket_id = ticket.get("id")
    feedback = ticket.get("feedback")
    print(f"Recebendo feedback: {feedback} para o ticket ID: {ticket_id}")
    if not ticket_id or feedback not in ["positive", "negative"]:
        return jsonify({"error": "Campos 'id' e 'feedback' são obrigatórios e válidos."}), 400

    tracking_tokens = buscar_tracking_token(ticket_id)
    if not tracking_tokens:
        return jsonify({"error": "Tracking token não encontrado para o ticket informado."}), 404

    for token in tracking_tokens:
        enviar_feedback_para_glean(token, feedback)

    return jsonify({"status": f"Feedback enviado para {len(tracking_tokens)} token(s)."}), 200

if __name__ == "__main__":
    app.run(port=5001, debug=True)
