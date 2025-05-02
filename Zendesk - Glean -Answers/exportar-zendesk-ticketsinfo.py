import requests
import pandas as pd
from config import ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN

# Exemplo de ID de ticket (substitua conforme necessário)
TICKET_ID = 1208260

url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{TICKET_ID}/comments.json" 

response = requests.get(url, auth=(ZENDESK_EMAIL, ZENDESK_API_TOKEN))

if response.status_code == 200:
    comments = response.json()["comments"]
    # Organiza os comentários em um DataFrame
    df = pd.DataFrame([{
        "author": c["author_id"],
        "created_at": c["created_at"],
        "public": c["public"],
        "body": c["body"]
    } for c in comments])

    df.to_excel("comentarios_ticket.xlsx", index=False)
    print("Arquivo salvo com sucesso!")
else:
    print(f"Erro ao buscar comentários: {response.status_code}")
