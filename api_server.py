from flask import Flask, request, jsonify
from efris_client import EfrisApiClient
import os

app = Flask(__name__)

# Initialize client (adjust as needed)
client = EfrisApiClient(tin='1015264035', test_mode=True)

@app.route('/api/<tin>/registration-details', methods=['GET'])
def get_registration_details(tin):
    try:
        # For simplicity, assuming validate_taxpayer returns the data
        # You may need to adjust based on actual API methods
        taxpayer_data = client.validate_taxpayer(tin)
        return jsonify({
            "status": {
                "returnCode": "00",
                "returnMessage": "SUCCESS"
            },
            "data": taxpayer_data
        })
    except Exception as e:
        return jsonify({
            "status": {
                "returnCode": "01",
                "returnMessage": "ERROR"
            },
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)