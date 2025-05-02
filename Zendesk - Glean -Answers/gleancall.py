import requests
from config import GLEAN_FEEDBACK_URL, GLEAN_TOKEN

url = GLEAN_FEEDBACK_URL

payload = {
    "trackingTokens": ["b5caf8d336bb44d8bf81fa9a88bdb62e"],
    "event": "VIEW"
}
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GLEAN_TOKEN}"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)