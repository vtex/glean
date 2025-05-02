import requests
from config import ZENDESK_DOMAIN, ZENDESK_EMAIL, ZENDESK_TOKEN

def enviar_mensagem_zendesk(
    ticket_id,
    mensagem,
    publica=False,
    status=None,
    tags=None,
    agente_id=None
):
    """
    Envia uma mensagem para um ticket do Zendesk.

    Parâmetros:
    - ticket_id: ID do ticket
    - mensagem: texto da mensagem a ser enviada
    - publica: True para comentário público, False para nota interna
    - status: novo status do ticket (ex: 'open', 'pending', 'solved')
    - tags: lista de tags para adicionar ao ticket
    - agente_id: ID do agente para atribuir ao ticket
    """
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    ticket_data = {
        "comment": {
            "body": mensagem,
            "public": publica
        }
    }
    if status:
        ticket_data["status"] = status
    if tags:
        ticket_data["tags"] = tags
    if agente_id:
        ticket_data["assignee_id"] = agente_id
    payload = { "ticket": ticket_data }
    response = requests.put(
        url,
        json=payload,
        auth=(ZENDESK_EMAIL, ZENDESK_TOKEN),
        headers={ "Content-Type": "application/json" }
    )
    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar: {response.status_code} - {response.text}")



if __name__ == "__main__":
    ticket_id = 1203303
    mensagem = "Teste de envio via API para a Glean"
    print("entrou na função")  
    enviar_mensagem_zendesk(
        ticket_id=ticket_id,
        mensagem=mensagem,
        publica=False,  # Define como nota interna
        status=None,  # (Opcional) Ex: "open", "pending", "solved"
        tags=None,
        agente_id=None  # (Opcional) Defina um ID de agente se quiser atribuir
    )

