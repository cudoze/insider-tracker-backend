import requests
import xml.etree.ElementTree as ET
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# SEC EDGAR API URL for insider transactions (Form 4 filings)
SEC_EDGAR_BASE_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("insider_trades.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insider_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cik TEXT,
            transaction_date TEXT,
            form_type TEXT,
            filing_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to fetch recent insider transactions
def fetch_insider_transactions(cik="0000320193", count=10):
    params = {
        "CIK": cik,
        "type": "4",
        "action": "getcompany",
        "output": "xml",
        "count": count
    }
    response = requests.get(SEC_EDGAR_BASE_URL, params=params, headers={"User-Agent": "WesleyApp/1.0"})
    if response.status_code == 200:
        return response.text
    return None

# Parse XML response to extract insider transactions
def parse_insider_transactions(xml_data, cik):
    root = ET.fromstring(xml_data)
    transactions = []
    for entry in root.findall("filings/filing"):
        transaction = {
            "cik": cik,
            "transaction_date": entry.find("dateFiled").text,
            "form_type": entry.find("type").text,
            "filing_url": "https://www.sec.gov" + entry.find("filingHref").text
        }
        transactions.append(transaction)
    return transactions

# Store transactions in the database
def store_transactions(transactions):
    conn = sqlite3.connect("insider_trades.db")
    cursor = conn.cursor()
    for transaction in transactions:
        cursor.execute('''
            INSERT INTO insider_trades (cik, transaction_date, form_type, filing_url)
            VALUES (?, ?, ?, ?)''',
            (transaction["cik"], transaction["transaction_date"], transaction["form_type"], transaction["filing_url"])
        )
    conn.commit()
    conn.close()

# API Endpoint to get and store insider transactions
@app.route("/insiders/<cik>", methods=["GET"])
def get_insider_transactions(cik):
    xml_data = fetch_insider_transactions(cik)
    if xml_data:
        transactions = parse_insider_transactions(xml_data, cik)
        store_transactions(transactions)
        return jsonify(transactions)
    return jsonify({"error": "Unable to fetch data"}), 500

# API Endpoint to retrieve stored transactions from the database
@app.route("/insiders/history/<cik>", methods=["GET"])
def get_stored_transactions(cik):
    conn = sqlite3.connect("insider_trades.db")
    cursor = conn.cursor()
    cursor.execute("SELECT transaction_date, form_type, filing_url FROM insider_trades WHERE cik = ? ORDER BY transaction_date DESC", (cik,))
    transactions = [{"transaction_date": row[0], "form_type": row[1], "filing_url": row[2]} for row in cursor.fetchall()]
    conn.close()
    return jsonify(transactions)

# API Endpoint to clear stored transactions (for maintenance)
@app.route("/insiders/clear", methods=["POST"])
def clear_transactions():
    conn = sqlite3.connect("insider_trades.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM insider_trades")
    conn.commit()
    conn.close()
    return jsonify({"message": "All transactions cleared"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
