import requests
import json

# 1. Envia uma pergunta para o chat
from config import GLEAN_API_URL, GLEAN_FEEDBACK_URL, GLEAN_TOKEN

def send_chat_and_get_token():
    url = GLEAN_API_URL
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GLEAN_TOKEN}'
    }
    data = {
        'stream': False,
        'messages': [{
            'author': 'USER',
            'fragments': [{'text': 'Give me one holiday this year'}]
        }],
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        response_json = response.json()
        print("🧪 Estrutura da resposta JSON:")
        print(json.dumps(response_json, indent=2))
        messages = response_json.get('messages', [])
        for i, message in enumerate(messages):
            print(f"\n📬 Mensagem {i + 1}:")
            print(json.dumps(message, indent=2))
            tracking_token = message.get('messageTrackingToken')
            if tracking_token:
                print(f"✅ Tracking token encontrado: {tracking_token}")
                return tracking_token

        messages = response_json.get('messages', [])
    else:
        print(f"Erro na chamada do chat: {response.status_code} - {response.text}")
        return None

# 2. Envia o feedback usando o tracking token
def send_feedback(tracking_token):
    url = GLEAN_FEEDBACK_URL
    payload = {
        "trackingTokens": [tracking_token],
        "event": "VIEW"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GLEAN_TOKEN}"
    }

    response = requests.post(url, json=payload, headers=headers)
    print(f"Feedback enviado! Status: {response.status_code}")
    print(response.text)

# 3. Execução principal
def main():
    token = send_chat_and_get_token()
    if token:
        send_feedback(token)
    else:
        print("❌ Não foi possível obter o tracking token.")

if __name__ == '__main__':
    main()
