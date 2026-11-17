# Rafiki SMS: Offline AI Assistant for Africa

## The African Problem
Millions of people across rural Africa rely on basic feature phones and lack affordable mobile data or reliable internet access, locking them out of modern AI tools. **Rafiki SMS** bridges this digital divide by allowing anyone to text a standard phone number with any question—from agricultural advice to general knowledge—and receive concise, context-aware AI answers back via plain SMS, using their phone number as their automatic account ID.

## How to Run the Project

### 1. Prerequisites
- Python 3.10+
- A free [Google AI Studio](https://aistudio.google.com/) API key (`GEMINI_API_KEY`)
- A free [TextBee](https://textbee.dev/) account (`TEXTBEE_API_KEY` & `TEXTBEE_DEVICE_ID`) linked to an Android phone with an active SIM
- [ngrok](https://ngrok.com/) (to expose your local server to the TextBee webhook)[cite: 1]

### 2. Installation & Setup
Clone the repository and install the dependencies:
```bash
git clone [https://github.com/MrFriedman/africa-tech-hackathon.git](https://github.com/MrFriedman/africa-tech-hackathon.git)
cd africa-tech-hackathon
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
