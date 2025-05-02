"""Configuration module. Load credentials and endpoints from environment variables."""
from pathlib import Path
import os
try:
    from dotenv import load_dotenv
    # Força o carregamento do .env a partir da raiz do projeto
    #env_path = Path(__file__).resolve().parent.parent / '.env'
    #load_dotenv(dotenv_path=env_path)
    load_dotenv()
except ImportError:
    pass



# Zendesk configuration
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')
ZENDESK_DOMAIN = os.getenv('ZENDESK_DOMAIN', ZENDESK_SUBDOMAIN)
ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL')
ZENDESK_TOKEN = os.getenv('ZENDESK_API_TOKEN') or os.getenv('ZENDESK_TOKEN')
ZENDESK_API_TOKEN = ZENDESK_TOKEN

# Glean configuration
GLEAN_API_URL = os.getenv('GLEAN_API_URL')
GLEAN_FEEDBACK_URL = os.getenv('GLEAN_FEEDBACK_URL')
GLEAN_TOKEN = os.getenv('GLEAN_TOKEN')
PS_ID=os.getenv('PS_ID')
NON_PS_ID=os.getenv('NON_PS_ID')
print("GLEAN_API_URL:", os.getenv("GLEAN_API_URL"))
