import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/test')
def network_check():
    # This pulls the 'target' from the URL. 
    # Example: /test?target=http://93.184.216.34
    target = request.args.get('target')

    if not target:
        return jsonify({
            "error": "Please provide a target. Usage: /test?target=http://<IP_OR_URL>"
        }), 400

    # Ensure the target has a scheme; if it's just an IP, we'll assume http
    if not target.startswith(('http://', 'https://')):
        target = f'http://{target}'

    try:
        # 5-second timeout ensures the app doesn't hang on dead IPs
        response = requests.get(target, timeout=5)
        return jsonify({
            "status": "Connected",
            "destination": target,
            "http_code": response.status_code,
            "headers": dict(response.headers),
            "content_preview": response.text[:250]
        })
    except requests.exceptions.ConnectTimeout:
        return jsonify({"status": "Failed", "error": "Connection Timed Out"}), 504
    except requests.exceptions.ConnectionError as e:
        return jsonify({"status": "Failed", "error": f"Connection Refused: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)