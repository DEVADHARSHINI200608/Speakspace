from flask import Flask, request, jsonify
import re
from datetime import datetime, timedelta
import dateparser
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ===================== GLOBAL STATE =====================
RECENT_CUSTOMER = None
PENDING_MEETING = None


# ===================== UTILS =====================
def clean_name(name):
    name = re.sub(r"^(to|is)\s+", "", name.strip(), flags=re.IGNORECASE)
    return name.title()


# ===================== CUSTOMER NAME =====================
def extract_customer_name(text):
    patterns = [
        r"change customer name to\s+([a-zA-Z ]+)",
        r"set customer to\s+([a-zA-Z ]+)",
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
import re

def extract_duration(text):
    text = text.lower()

    units = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16,
        "seventeen": 17, "eighteen": 18, "nineteen": 19
    }

    tens = {
        "twenty": 20, "thirty": 30,
        "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70,
        "eighty": 80, "ninety": 90
    }

    # 1️⃣ Numeric → "10 minutes"
    match = re.search(r"(\d+)\s*(min|mins|minutes)", text)
    if match:
        return int(match.group(1))

    # 2️⃣ Word numbers → "sixteen minutes", "twenty five minutes"
    words = text.split()

    for i in range(len(words)):
        if words[i] in units:
            number = units[words[i]]
            if i + 1 < len(words) and words[i + 1] in tens:
                number += tens[words[i + 1]]
            if "minute" in text:
                return number

        if words[i] in tens:
            number = tens[words[i]]
            if i + 1 < len(words) and words[i + 1] in units:
                number += units[words[i + 1]]
            if "minute" in text:
                return number

    # 3️⃣ Half hour
    if "half hour" in text or "half an hour" in text:
        return 30

    return None



# ===================== TIME =====================
def extract_time(text):
    full = re.search(
        r"\b(\d{1,2}(:\d{2})?\s*(am|pm))\b",
        text,
        re.IGNORECASE
    )
    if full:
        return dateparser.parse(full.group(1))

    partial = re.search(r"\b(\d{1,2}(:\d{2})?)\b", text)
    if partial:
        return "NEEDS_AMPM"

    natural = {
        "morning": "9 am",
        "afternoon": "3 pm",
        "evening": "7 pm",
        "night": "9 pm"
    }
    for k, v in natural.items():
        if k in text:
            return dateparser.parse(v)

    return None


# ===================== DAY =====================
def extract_day(text):
    days = [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]
    for d in days:
        if d in text:
            return d.capitalize()
    return None


# ===================== MAIN API =====================
@app.post("/process")
def process():
    global RECENT_CUSTOMER, PENDING_MEETING

    transcript = request.json.get("transcript", "").lower()

    # ---------- CONFIRM ----------
    if PENDING_MEETING:
        if any(x in transcript for x in ["yes", "confirm", "okay"]):
            data = PENDING_MEETING
            PENDING_MEETING = None
            return jsonify({
                "message": "Meeting confirmed",
                **data,
                "spoken_text": "Your meeting has been confirmed."
            })

        if any(x in transcript for x in ["no", "cancel", "stop"]):
            PENDING_MEETING = None
            return jsonify({
                "message": "Meeting cancelled",
                "spoken_text": "Meeting cancelled."
            })

    # ---------- RESET ----------
    if "clear customer" in transcript or "reset customer" in transcript:
        RECENT_CUSTOMER = None
        return jsonify({
            "message": "Customer cleared",
            "spoken_text": "Customer context cleared."
        })

    name = extract_customer_name(transcript)

    # ---------- CUSTOMER ONLY ----------
    if name and "meeting" not in transcript:
        RECENT_CUSTOMER = name
        return jsonify({
            "message": "Customer updated",
            "customer": name,
            "spoken_text": f"Customer name updated to {name}"
        })

    # ---------- MEETING ----------
    if "meeting" in transcript or "schedule" in transcript:

        if name:
            RECENT_CUSTOMER = name

        customer = RECENT_CUSTOMER or "Unknown"

        day = extract_day(transcript)
        if not day:
            return jsonify({
                "error": "Day missing",
                "spoken_text": "Please mention the meeting day."
            }), 400

        today = datetime.now()
        idx = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].index(day)
        days_ahead = (idx - today.weekday()) % 7 or 7
        meeting_dt = today + timedelta(days=days_ahead)

        date = meeting_dt.strftime("%d-%m-%Y")

        start_dt = extract_time(transcript)

        if start_dt == "NEEDS_AMPM":
            return jsonify({
                "error": "AM/PM missing",
                "spoken_text": "Please specify AM or PM."
            }), 400

        if not start_dt:
            return jsonify({
                "error": "Time missing",
                "spoken_text": "Please mention meeting time."
            }), 400

        start_time = start_dt.strftime("%I:%M %p")

        duration = extract_duration(transcript)
        end_time = (start_dt + timedelta(minutes=duration)).strftime("%I:%M %p")

        PENDING_MEETING = {
            "customer": customer,
            "day": day,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration
        }

        return jsonify({
            "message": "Confirmation required",
            **PENDING_MEETING,
            "spoken_text": (
                f"Meeting with {customer} on {day} "
                f"from {start_time} to {end_time}. Confirm?"
            )
        })

    return jsonify({"message": "No action detected"})


# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)
