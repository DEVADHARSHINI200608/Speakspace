from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

RECENT_CUSTOMER = None
PENDING_MEETING = None

# ------------------ HELPERS ------------------

def clean_name(name):
    return name.strip().title()


def extract_customer_name(text):
    """
    Extracts ONLY the name.
    Stops at: on / at / for
    """
    patterns = [
        r"meeting with ([a-zA-Z ]+?)(?: on | at | for |$)",
        r"customer is ([a-zA-Z ]+?)(?: on | at | for |$)",
        r"client is ([a-zA-Z ]+?)(?: on | at | for |$)"
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return clean_name(m.group(1))

    return None


def extract_duration(text):
    word_map = {
        "five": 5, "ten": 10, "fifteen": 15,
        "twenty": 20, "thirty": 30,
        "thirty five": 35
    }

    match = re.search(r"(\d+)\s*(min|minute|minutes)", text)
    if match:
        return int(match.group(1))

    for word, val in word_map.items():
        if word in text:
            return val

    return None


def extract_time(text):
    match = re.search(r"(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    ampm = match.group(3).lower()

    if ampm == "pm" and hour != 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0

    return hour, minute


def extract_day(text):
    days = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4,
        "saturday": 5, "sunday": 6
    }

    for day, idx in days.items():
        if day in text:
            return day.capitalize(), idx

    return None, None


def calculate_next_date(day_index, force_next):
    today = datetime.now()
    today_idx = today.weekday()

    diff = (day_index - today_idx) % 7

    if force_next or diff == 0:
        diff += 7

    return today + timedelta(days=diff)


# ------------------ API ------------------

@app.post("/process")
def process():
    global RECENT_CUSTOMER, PENDING_MEETING

    text = request.json.get("transcript", "").lower()

    # -------- CONFIRM --------
    if PENDING_MEETING:
        if any(w in text for w in ["yes", "confirm", "okay"]):
            data = PENDING_MEETING
            PENDING_MEETING = None
            return jsonify({"message": "Meeting confirmed", **data})

        if any(w in text for w in ["no", "cancel"]):
            PENDING_MEETING = None
            return jsonify({"message": "Meeting cancelled"})

    # -------- CUSTOMER ONLY --------
    name = extract_customer_name(text)
    if name and "meeting" not in text:
        RECENT_CUSTOMER = name
        return jsonify({"message": "Customer set", "customer": name})

    # -------- MEETING --------
    if "meeting" in text or "schedule" in text:
        if name:
            RECENT_CUSTOMER = name

        customer = RECENT_CUSTOMER or "Unknown"

        is_next = "next" in text
        day_name, day_idx = extract_day(text)

        if day_idx is None:
            return jsonify({"error": "Day not mentioned"})

        date_obj = calculate_next_date(day_idx, is_next)

        time_parts = extract_time(text)
        if not time_parts:
            return jsonify({"error": "Time not mentioned"})

        hour, minute = time_parts
        start_dt = date_obj.replace(hour=hour, minute=minute)

        duration = extract_duration(text) or 30
        end_dt = start_dt + timedelta(minutes=duration)

        meeting = {
            "customer": customer,
            "day": day_name,
            "date": date_obj.strftime("%d-%m-%Y"),
            "start_time": start_dt.strftime("%I:%M %p"),
            "end_time": end_dt.strftime("%I:%M %p"),
            "duration_minutes": duration
        }

        PENDING_MEETING = meeting

        return jsonify({
            "message": "Confirmation required",
            **meeting,
            "spoken_text": (
                f"Meeting with {customer} on {day_name} "
                f"at {meeting['start_time']} for {duration} minutes. Confirm?"
            )
        })

    return jsonify({"message": "No action detected"})


if __name__ == "__main__":
    app.run(debug=True)