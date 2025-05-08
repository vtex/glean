# -*- coding: utf-8 -*-
"""
AWS Lambda handler for Zendesk to Glean webhook.

This module loads the existing Flask-based webhook script and invokes its processa_ticket function asynchronously.
"""
import json
import os
import threading
import importlib.util

# Dynamically load the Flask-based webhook module
HERE = os.path.dirname(__file__)
MODULE_PATH = os.path.join(HERE, "[V1]- webhook-enviando-glean.py")
spec = importlib.util.spec_from_file_location("webhook_module", MODULE_PATH)
webhook_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(webhook_module)

# Alias the processing function
processa_ticket = webhook_module.processa_ticket

def lambda_handler(event, context):
    """
    AWS Lambda entry point for Zendesk to Glean webhook.
    """
    # Parse event body if present (API Gateway proxy integration)
    try:
        if isinstance(event, dict) and "body" in event:
            raw = event.get("body") or "{}"
            payload = json.loads(raw)
        else:
            payload = event
    except ValueError:
        payload = event

    print("Lambda payload recebido:", json.dumps(payload, indent=2))

    # Process the ticket asynchronously and return immediately
    thread = threading.Thread(target=processa_ticket, args=(payload,))
    thread.daemon = True
    thread.start()

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"status": "received"}),
    }