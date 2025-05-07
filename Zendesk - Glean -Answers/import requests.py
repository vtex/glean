import requests
import pandas as pd
from config import ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_DOMAIN

def buscar_nome_dos_campos():
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/ticket_fields.json"
    auth = (ZENDESK_EMAIL, ZENDESK_TOKEN)
    headers = {"Content-Type": "application/json"}

    response = requests.get(url, auth=auth, headers=headers)
    if response.status_code == 200:
        campos = response.json().get("ticket_fields", [])
        return {campo["id"]: campo["title"] for campo in campos}
    else:
        print(f"❌ Erro ao buscar ticket_fields: {response.status_code} - {response.text}")
        return {}

def buscar_ticket_completo(ticket_id):
    url = f"https://{ZENDESK_DOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    auth = (ZENDESK_EMAIL, ZENDESK_TOKEN)
    headers = {"Content-Type": "application/json"}

    campos_nomes = buscar_nome_dos_campos()
    response = requests.get(url, auth=auth, headers=headers)

    if response.status_code == 200:
        ticket = response.json().get("ticket", {})
        custom_fields = ticket.get("custom_fields", [])

        dados = []
        for field in custom_fields:
            field_id = field.get("id")
            field_value = field.get("value")
            field_name = campos_nomes.get(field_id, "Nome não encontrado")

            dados.append({
                "ID": field_id,
                "Nome": field_name,
                "Valor": field_value
            })

        # Salvar em planilha
        df = pd.DataFrame(dados)
        nome_arquivo = f"ticket_{ticket_id}_campos.xlsx"
        df.to_excel(nome_arquivo, index=False)
        print(f"📁 Planilha salva como: {nome_arquivo}")

    else:
        print(f"❌ Erro ao buscar ticket: {response.status_code} - {response.text}")

if __name__ == "__main__":
    buscar_ticket_completo(1220592)

