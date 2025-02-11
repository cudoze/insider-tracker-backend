from flask import Flask, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

@app.route("/ticker-to-cik", methods=["GET"])
def get_ticker_to_cik():
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            "User-Agent": "Wesley Wells, Contact: wells.wes@outlook.com"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch ticker data", "details": f"SEC API responded with status {response.status_code}"}), 500

        data = response.json()
        mappings = {item["ticker"].upper(): str(item["cik_str"]).zfill(10) for item in data.values()}

        return jsonify(mappings)
    except Exception as e:
        return jsonify({"error": "Failed to fetch ticker data", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
