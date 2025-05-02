from flask import Flask, request

app = Flask(__name__)

@app.route('/zendesk-to-glean', methods=['POST'])
def handle_zendesk_message():
    data = request.json
    print("Recebi isso do Zendesk:", data)
    # Aqui você pode chamar a Glean, por exemplo
    return "OK", 200

if __name__ == '__main__':
    app.run(port=5000)
