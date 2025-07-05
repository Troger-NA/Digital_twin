from flask import Flask, request, jsonify
from graph import graph
import datetime

""" Api server para conectar los endpoints con el grafo"""

#Instancio server de flask
app = Flask(__name__)

#Defino funcion de log
def mock_log(message, response, error=None):
    """Mock logging function - solo imprime en consola"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if error:
        print(f"[MOCK LOG] {timestamp} - ERROR: {error}")
    else:
        print(f"[MOCK LOG] {timestamp} - User: {message[:50]}... - Response: {response[:50]}...")


#Defino ruta de chat, el endpoint principal
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            mock_log("", "", "Message is required")
            return jsonify({'error': 'Message is required'}), 400

        # Run the graph
        initial_state = {"messages": [{"role": "user", "content": message}]}
        result = graph.invoke(initial_state)
        
        response = result.get("response", "No response generated")
        
        # Mock log the interaction
        mock_log(message, response)
        
        return jsonify({'response': response})

    except Exception as e:
        mock_log("", "", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'OK', 'message': 'Mock Nico Clone API is running'})

if __name__ == '__main__':
    print("Starting Mock Nico Clone API Server...")
    app.run(host='0.0.0.0', port=5000, debug=True) 