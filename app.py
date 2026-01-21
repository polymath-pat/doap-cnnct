import os
import requests
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# we vibe coding now boi...
app = Flask(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix

# Add this right after app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize Limiter
# storage_uri="memory://" is fine for single instances. 
# Use Redis if you scale to multiple containers.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

@app.route('/test')
@limiter.limit("5 per minute") # Specific rate limit for this route
def network_check():
    target = request.args.get('target')

    if not target:
        return jsonify({"error": "Target missing. Usage: /test?target=1.1.1.1"}), 400

    if not target.startswith(('http://', 'https://')):
        target = f'http://{target}'

    try:
        response = requests.get(target, timeout=5)
        return jsonify({
            "status": "Connected",
            "destination": target,
            "http_code": response.status_code,
            "body": response.text[:200]
        })
    except Exception as e:
        return jsonify({"status": "Failed", "error": str(e)}), 500

# Custom error handler for when users hit the limit
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "You are doing that too much. Please try again later.",
        "limit": str(e.description)
    }), 429

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
