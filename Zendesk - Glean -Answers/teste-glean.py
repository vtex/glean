import requests
import json
from typing import List, Dict
from config import GLEAN_API_URL, GLEAN_TOKEN


def process_message_fragment(message): # Process the message fragment, which is a JSON object, and return the message fragment string and citations
    message_fragment_str = '' # Initialize an empty string to store the message fragment
    message_fragment_citations = [] # Initialize an empty list to store citations from glean

    message_type = message['messageType'] # Get the message type
    fragments = message.get('fragments', []) # Get the fragments from the message
    citations = message.get('citations', []) # Get the citations from the message

    message_fragment_str = '' # Initialize an empty string to store the message fragment
    if message_type == 'CONTENT': # Check if the message type is CONTENT
        if fragments: # Check if there are fragments in the message
            for fragment in fragments: # Iterate through each fragment
                text = fragment.get('text', '') # Get the text from the fragment
                print(text, end='', flush=True)  # Print the text to the console without jumping lines and with flush being true, so that the text is always streamed
                message_fragment_str += text # Append the text to the message fragment string
        if citations: # Check if there are citations in the message
            print('\nSources:') # Print the sources header
            message_fragment_citations += citations # Append the citations to the message fragment citations list
            for idx, citation in enumerate(citations):  # Iterate through each citation, idx is the index
                sourceDocument = citation.get('sourceDocument', {}) # Get the source document from the citation
                if sourceDocument: # Check if the source document exists
                  source = citation['sourceDocument'] # Get the source document
                  print(f'Source {idx + 1}: Document title - {source.get("title", "No title")}, url: {source.get("url", "No URL")}')
 # Print the source document title and url
                sourcePerson = citation.get('sourcePerson', {}) # Get the source person from the citation
                if sourcePerson: # Check if the source person exists
                  source = citation['sourcePerson'] # Get the source person
                  print(f'Source {idx + 1}: Person name - {source["name"]}') # Print the source person name


    return message_fragment_str, message_fragment_citations # Return the message fragment string and citations


def make_content_message(author: str = 'USER', text: str = None, citations: List[Dict] = None): #build the json from user to glean or from glean to user
    # Create a content message JSON object
    message_json = { # Initialize the message JSON object
        'author': author, # Set the author of the message, standard is user, but in some cases can be GLEAN_AI
        'messageType': 'CONTENT' # Set the message type to CONTENT
    }
    if text: # Check if the text is provided
        message_json['fragments'] = [{'text': text}] # Add the text to the message JSON object
    if citations: # Check if the citations are provided
        message_json['citations'] = citations # Add the citations to the message JSON object
    return message_json # Return the message JSON object


def process_response_message_stream(response): # Process the response message stream and return the response message and chat session tracking token
    response_message_text = '' # Initialize an empty string to store the response message text
    response_message_citations = [] # Initialize an empty list to store the response message citations
    chat_session_tracking_token = None  # Initialize the chat session tracking token

    for line in response.iter_lines(): # Iterate through each line in the response stream
        if line: # Check if the line is not empty
            line_json = json.loads(line) # Parse the line as JSON
            messages = line_json.get('messages', []) # Get the messages from the line
            chat_session_tracking_token = line_json.get('chatSessionTrackingToken', None) # Get the chat session tracking token from the line
            for message_fragment in messages: # Iterate through each message fragment
                message_fragment_text, message_fragment_citations = process_message_fragment(message_fragment) # Process the message fragment
                response_message_text += message_fragment_text # Append the message fragment text to the response message text
                response_message_citations += message_fragment_citations # Append the message fragment citations to the response message citations

    return make_content_message(author='GLEAN_AI', text=response_message_text, citations=response_message_citations), chat_session_tracking_token # Return the response message and chat session tracking token


def send_conversation_message(url, headers, payload): # Send a conversation message to the chat API
    next_payload = payload # Initialize the next payload
    try: # Try to send the request
        with requests.post(url, headers=headers, json=payload, stream=True) as response: # Send the request and stream the response
            if response.status_code == 200: # Check if the response status code is 200
                response_message, chat_session_tracking_token = process_response_message_stream(response) # Process the response message stream
                # Add the response message to the next payload, most recent message first
                next_payload['messages'].insert(0, response_message) # Add the response message to the next payload
                next_payload['chatSessionTrackingToken'] = chat_session_tracking_token # Add the chat session tracking token to the next payload
            else: # Check if the response status code is not 200
                print(f'Status code: {response.status_code}, error: {response.text}') # Print the status code and error message
                exit(1) # Exit the program with status code 1
    except requests.exceptions.RequestException as e: # Handle request exceptions
        print(f'Request Exception: {str(e)}') # Print the request exception message
        exit(1) # Exit the program with status code 1
    return next_payload # Return the next payload


def main(): # Main function to execute the script
    url = GLEAN_API_URL
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GLEAN_TOKEN}'
    }

    # Initialize the payload
    payload = {
        'stream': True,  # Set to False to toggle off streaming mode
        'messages': [] # Initialize the messages list
    }

    first_user_message = make_content_message(text='What are the holidays this year?') # Create the first user message
    second_user_message = make_content_message(text='What about this month?') # Create the second user message

    user_messages_list = [first_user_message, second_user_message] # Create a list of user messages

    for user_message in user_messages_list: # Iterate through each user message
        print(f'User message: {user_message["fragments"][0]["text"]}', flush=True) # Print the user message to the console
        print('Response: ', flush=True) # Print the response header
        payload['messages'].insert(0, user_message) # Add the user message to the payload, most recent message first
        payload = send_conversation_message(url, headers, payload)  # Send conversation message and get next payload


if __name__ == '__main__': # Check if the script is being run directly
    main() # Call the main function to execute the script