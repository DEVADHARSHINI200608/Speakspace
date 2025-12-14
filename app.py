from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import dateparser
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===================== GLOBAL MEMORY =====================
RECENT_CUSTOMER = None
PENDING_MEETING = None

# ===================== SETTINGS =====================
DATEPARSER_SETTINGS = {
    "PREFER_DATES_FROM": "future",   # 🔥 key fix
    "RETURN_AS_TIMEZONE_AWARE": False
}

# ===================== UTILS =====================
def clean_name(name):
    return name.strip().title()

# ===================== CUSTOMER =====================
def extract_customer_name(text):
    patterns = [
        r"meeting with ([a-zA-Z ]+)",
        r"customer is ([a-zA-Z ]+)",
        r"client is ([a-zA-Z ]+)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return clean_name(m.group(1))
    return None

# ===================== DURATION =====================
def extract_duration(text):
    match = re.search(r"(\d+)\s*(minute|minutes|min)", text)
    if match:
        return int(match.group(1))
    return None

# ===================== DATETIME =====================
def extract_datetime(text):
    """
    Handles:
    - next Tuesday
    - tomorrow
    - today
    - explicit date
    - time like 4 pm, 11.30 am
    """
    return dateparser.parse(text, settings=DATEPARSER_SETTINGS)

# ===================== MAIN API =====================
@app.post("/process")
def process():
    global RECENT_CUSTOMER, PENDING_MEETING

    transcript = request.json.get("transcript", "").lower()

    # ---------- CONFIRM ----------
    if PENDING_MEETING:
        if "yes" in transcript or "confirm" in transcript:
            data = PENDING_MEETING
            PENDING_MEETING = None
            return jsonify({
                "message": "Meeting confirmed",
                **data
            })

        if "no" in transcript or "cancel" in transcript:
            PENDING_MEETING = None
            return jsonify({"message": "Meeting cancelled"})

    # ---------- EXTRACT ----------
    name = extract_customer_name(transcript)
    if name:
        RECENT_CUSTOMER = name

    customer = RECENT_CUSTOMER or "Unknown"

    dt = extract_datetime(transcript)
    duration = extract_duration(transcript)

    if not dt:
        return jsonify({"error": "Could not understand date/time"})

    start_time = dt
    end_time = start_time + timedelta(minutes=duration or 30)

    # ---------- SAVE ----------
    PENDING_MEETING = {
        "customer": customer,
        "date": start_time.strftime("%d-%m-%Y"),
        "day": start_time.strftime("%A"),
        "start_time": start_time.strftime("%I:%M %p"),
        "end_time": end_time.strftime("%I:%M %p"),
        "duration_minutes": duration or 30
    }

    return jsonify({
        "message": "Confirmation required",
        **PENDING_MEETING
    })

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)