🎙️ SpeakSpace Smart Meeting Scheduler

A backend AI workflow that converts voice notes into structured meeting schedules using natural language understanding.

Built for SpeakSpace Annual Hackathon.

🚀 Project Overview

People often record voice notes like:

“Schedule a meeting with Anu next Tuesday at 4 pm for sixteen minutes”

But voice notes are unstructured and cannot be directly used in calendars or workflows.

This project solves that by:

Taking voice transcripts from SpeakSpace

Extracting customer name, date, time, and duration

Converting them into structured JSON

Making the data ready for calendar integration & automation

🧠 Problem Statement

Voice notes are easy to record but hard to organize

Important details like date, time, duration are hidden inside text

Users manually re-enter meetings into calendars

No automated workflow from voice → action

💡 Solution

We built a Flask backend API that:

Accepts voice transcripts as JSON

Understands natural language

Extracts meeting details

Handles missing information gracefully

Returns structured data ready for UI or calendar use

🏗️ Tech Stack

Python

Flask

dateparser

Regex (NLP logic)

CORS enabled API

Render (Deployment)

📁 Project Structure
speakspace-backend/
│
├── app.py                # Main Flask application
├── requirements.txt      # Dependencies
├── README.md             # Project documentation

⚙️ Installation
1️⃣ Clone the Repository
git clone https://github.com/your-username/speakspace-backend.git
cd speakspace-backend

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate

3️⃣ Install Dependencies
pip install -r requirements.txt

▶️ Run the Project
python app.py


Server will start at:

http://127.0.0.1:5000

🔌 API Usage
Endpoint
POST /process

Request Body (JSON)
{
  "transcript": "Schedule a meeting with Anu next Tuesday at 4 pm for sixteen minutes"
}

Sample Response
{
  "message": "Confirmation required",
  "customer": "Anu",
  "day": "Tuesday",
  "date": "17-12-2025",
  "start_time": "04:00 PM",
  "end_time": "04:16 PM",
  "duration_minutes": 16,
  "spoken_text": "Meeting with Anu on Tuesday from 04:00 PM to 04:16 PM. Confirm?"
}

🧪 Testing with cURL
Windows PowerShell
Invoke-RestMethod -Method POST `
  -Uri https://speakspace-backend.onrender.com/process `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"transcript":"Customer is A"}'

🔁 How It Works (Flow)

🎤 Voice recorded in SpeakSpace

📝 SpeakSpace converts voice → text

📩 Transcript sent to backend API

🧠 Backend parses:

Customer name

Day & date

Time

Duration

📦 Structured JSON generated

📅 Ready for calendar / UI integration

⚠️ Smart Handling of Missing Data
Missing Info	Behavior
Customer	Defaults to Unknown
Start Time	Unknown
Duration	End time missing
Day	Unknown

No bad requests — system always responds gracefully.

🌍 Deployment

Hosted on Render

Auto-deploy enabled from GitHub

Public API endpoint ready for integration

🎯 Hackathon Fit (Why This Wins)

✔ Uses SpeakSpace voice workflow
✔ Real-world automation use case
✔ Clean backend logic
✔ Scalable for calendar, CRM, reminders
✔ Easy UI integration


🏁 Future Enhancements

Google Calendar integration

Multi-meeting handling

Voice confirmation loop

Database persistence

User authentication

👨‍💻 Author

Built by AKASUKI
For SpeakSpace Annual Hackathon