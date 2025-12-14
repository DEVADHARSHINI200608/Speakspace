from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import dateparser
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===================== GLOBAL STATE =====================
RECENT_CUSTOMER = None
PENDING_MEETING = None


# ===================== UTILS =====================
def clean_name(name):
    return name.strip().title()


# ===================== CUSTOMER =====================
def extract_customer_name(text):
    patterns = [
        r"customer is ([a-zA-Z ]+)",
        r"meeting with ([a-zA-Z ]+)",
        r"client is ([a-zA-Z ]+)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return clean_name(m.group(1))
    return None


# ===================== DURATION =====================
def extract_duration(text):
    match = re.search(r"(\d+)\s*(minute|min|minutes)", text)
    if match:
        return int(match.group(1))

    word_map = {
        "five": 5, "ten": 10, "fifteen": 15,
        "twenty": 20, "thirty": 30
    }

    for word, val in word_map.items():
        if word in text and "minute" in text:
            return val

    if "half hour" in text:
        return 30

    return None


# ===================== DATE + TIME =====================
def extract_datetime(text):
    """
    Handles:
    - today
    - tomorrow
    - next tuesday
    - monday at 11:30
    """
    settings = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now()
    }

    return dateparser.parse(text, settings=settings)


# ===================== MAIN API =====================
@app.post("/process")
def process():
    global RECENT_CUSTOMER, PENDING_MEETING

    transcript = request.json.get("transcript", "").lower()

    # ---------- CONFIRM ----------
    if PENDING_MEETING:
        if any(x in transcript for x in ["yes", "confirm", "ok"]):
            data = PENDING_MEETING
            PENDING_MEETING = None
            return jsonify({
                "message": "Meeting confirmed",
                **data
            })

        if any(x in transcript for x in ["no", "cancel"]):
            PENDING_MEETING = None
            return jsonify({"message": "Meeting cancelled"})

    # ---------- CUSTOMER ----------
    name = extract_customer_name(transcript)
    if name and "meeting" not in transcript:
        RECENT_CUSTOMER = name
        return jsonify({
            "message": "Customer set",
            "customer": name
        })

    # ---------- MEETING ----------
    if "meeting" in transcript or "schedule" in transcript:

        if name:
            RECENT_CUSTOMER = name

        customer = RECENT_CUSTOMER or "Unknown"

        start_dt = extract_datetime(transcript)
        duration = extract_duration(transcript)

        if not start_dt:
            return jsonify({"error": "Date or time not understood"})

        end_dt = None
        if duration:
            end_dt = start_dt + timedelta(minutes=duration)

        meeting = {
            "customer": customer,
            "date": start_dt.strftime("%d-%m-%Y"),
            "day": start_dt.strftime("%A"),
            "start_time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p") if end_dt else "Unknown",
            "duration_minutes": duration
        }

        PENDING_MEETING = meeting

        return jsonify({
            "message": "Confirmation required",
            **meeting,
            "spoken_text": (
                f"Meeting with {customer} on {meeting['day']} "
                f"at {meeting['start_time']}. Confirm?"
            )
        })

    return jsonify({"message": "No action detected"})


# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)