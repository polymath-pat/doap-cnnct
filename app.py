import os
import requests
from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def test_connection():
    # Get 'target' from URL params, e.g., /?target=http://1.1.1.1
    target = request.args.get('target', 'https://httpbin.org/ip')
    
    try:
        # We set a short timeout so the app doesn't hang if the IP is blocked
        response = requests.get(target, timeout=5)
        return {
            "status": "Success",
            "target": target,
            "http_code": response.status_code,
            "body_preview": response.text[:200]
        }
    except Exception as e:
        return {
            "status": "Failed",
            "target": target,
            "error": str(e)
        }, 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
