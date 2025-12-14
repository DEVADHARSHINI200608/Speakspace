from flask import Flask, request, jsonify
import re
from datetime import datetime, timedelta
import dateparser
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RECENT_CUSTOMER = None
PENDING_MEETING = None


# ===================== UTILS =====================
def clean_name(name):
    name = re.sub(r"^(to|is)\s+", "", name.strip(), flags=re.IGNORECASE)
    return name.title()


# ===================== CUSTOMER =====================
def extract_customer_name(text):
    patterns = [
        r"customer name is\s+([a-zA-Z ]+)",
        r"customer is\s+([a-zA-Z ]+)",
        r"client is\s+([a-zA-Z ]+)",
        r"meeting with\s+([a-zA-Z ]+?)(?:\s+on|\s+at|$)"
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return clean_name(m.group(1))
    return None


# ===================== DURATION =====================
def extract_duration(text):
    match = re.search(r"(\d+)\s*(min|mins|minutes)", text)
    if match:
        return int(match.group(1))

    words_to_numbers = {
        "five": 5, "ten": 10, "fifteen": 15,
        "sixteen": 16, "twenty": 20, "thirty": 30
    }
    for word, num in words_to_numbers.items():
        if word in text and "minute" in text:
            return num

    if "half hour" in text:
        return 30

    return None


# ===================== TIME =====================
def extract_time(text):
    return dateparser.parse(
        text,
        settings={"PREFER_DATES_FROM": "future"}
    )


# ===================== DATE =====================
def extract_date(text):
    parsed = dateparser.parse(
        text,
        settings={
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
    )
    return parsed.date() if parsed else None


# ===================== MAIN API =====================
@app.post("/process")
def process():
    global RECENT_CUSTOMER, PENDING_MEETING

    transcript = request.json.get("transcript", "").lower()

    # ---------- CONFIRM ----------
    if PENDING_MEETING:
        if any(w in transcript for w in ["yes", "confirm", "okay"]):
            data = PENDING_MEETING
            PENDING_MEETING = None
            return jsonify({
                "message": "Meeting confirmed",
                **data
            })

        if any(w in transcript for w in ["no", "cancel"]):
            PENDING_MEETING = None
            return jsonify({"message": "Meeting cancelled"})

    name = extract_customer_name(transcript)
    if name:
        RECENT_CUSTOMER = name

    if "meeting" not in transcript and "schedule" not in transcript:
        return jsonify({
            "message": "Customer updated",
            "customer": RECENT_CUSTOMER
        })

    # ---------- DATE & TIME ----------
    start_dt = extract_time(transcript)
    meeting_date = extract_date(transcript)

    duration = extract_duration(transcript)

    if start_dt and duration:
        end_dt = start_dt + timedelta(minutes=duration)
    else:
        end_dt = None

    PENDING_MEETING = {
        "customer": RECENT_CUSTOMER or "Unknown",
        "date": meeting_date.strftime("%d-%m-%Y") if meeting_date else "Unknown",
        "start_time": start_dt.strftime("%I:%M %p") if start_dt else "Unknown",
        "end_time": end_dt.strftime("%I:%M %p") if end_dt else "Unknown",
        "duration_minutes": duration
    }

    return jsonify({
        "message": "Confirmation required",
        **PENDING_MEETING
    })


if __name__ == "__main__":
    app.run(debug=True)