# Zendesk ↔ Glean Integration

> A set of scripts and utilities to integrate Zendesk tickets with the Glean conversational AI API.

## Requirements

- Python 3.7+
- Install dependencies:
  ```bash
  pip install Flask requests python-dotenv
  ```

## Configuration

This project uses environment variables for all credentials and endpoints. Create a `.env` file in the project root (or set these variables in your environment):

```bash
ZENDESK_SUBDOMAIN=your_zendesk_subdomain
ZENDESK_EMAIL=your_email_or_email/token
ZENDESK_API_TOKEN=your_zendesk_api_token
ZENDESK_TOKEN=your_zendesk_api_token  # optional alias for ZENDESK_API_TOKEN
GLEAN_API_URL=https://your-glean-endpoint/rest/api/v1/chat
GLEAN_FEEDBACK_URL=https://your-glean-endpoint/rest/api/v1/feedback  # optional
GLEAN_TOKEN=your_glean_api_token
```

Optionally install `python-dotenv` to auto-load the `.env` file.

## Scripts Overview

All scripts live under the `Zendesk - Glean -Answers/` directory:

- **[V1]- webhook-enviando-glean.py**: Flask app listening on `POST /zendesk-to-glean`. Receives Zendesk webhooks, fetches ticket & comments, sends to Glean, and saves the response to `resposta_ticket_<ticket_id>.txt`.
- **[V1] - post-ticket-zendesk.py**: Posts an internal note to a specified Zendesk ticket via API.
- **exportar-zendesk-ticketsinfo.py**: Exports ticket data and comments to an Excel file.
- **teste-flask.py**: Simple Flask test endpoint example.
- **teste-glean.py**: Example script for a basic Glean API call.
- **trackingtoken.py**: Example of retrieving a Glean chat session tracking token.
- **gleancall.py**: Example of sending feedback to the Glean API.
- **webhook-com-excel.py**, **webhook-com-txt-estruturado.py**, **webhook-txt-estruturado-com-email.py**: Legacy webhook handlers that export to Excel/TXT or send via email.

## Usage

To start the main webhook server:

```bash
cd "Zendesk - Glean -Answers"
python "[V1]- webhook-enviando-glean.py"
```

This will launch a Flask server on port `5001`. Configure your Zendesk webhook to `POST` to:

```
http://<host>:5001/zendesk-to-glean
```

Responses from Glean will be saved in the project root as:
```
resposta_ticket_<ticket_id>.txt
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for a visual overview of components and data flows.
