from flask import Flask, request, jsonify, render_template
import requests
import json
from flask_sqlalchemy import SQLAlchemy
from datetime import date

app = Flask(__name__)

# DATABASE CONFIG
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gym.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# WORKOUT TABLE
class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String(200))
    sets = db.Column(db.Integer)
    reps = db.Column(db.String(20))
    date = db.Column(db.Date)
    completed = db.Column(db.Boolean, default=False)

# CHAT HISTORY TABLE
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500))
    response = db.Column(db.Text)

API_KEY = "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"

# HOME PAGE
@app.route("/")
def home():
    return render_template("chat.html")

# CHAT PAGE
@app.route("/chat")
def chat_page():
    return render_template("chat.html")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# HISTORY PAGE
@app.route("/history")
def history():
    return render_template("history.html")

# AI WORKOUT
@app.route("/ask-ai", methods=["POST"])
def ask_ai():

    data = request.json
    question = data.get("question")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct",
        "messages": [
            {
                "role": "system",
                "content": """
You are a professional gym trainer.

Always respond ONLY in JSON format.

Example:

{
 "workout":[
  {"exercise":"Bench Press","sets":3,"reps":"8-12"},
  {"exercise":"Incline Dumbbell Press","sets":3,"reps":"10-12"},
  {"exercise":"Push Ups","sets":3,"reps":"15"}
 ]
}

Rules:
- Only return JSON
- Do not explain anything
- reps must be text like "8-12"
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    result = response.json()

    workout = []
    answer_text = ""

    if "choices" in result:
        answer = result["choices"][0]["message"]["content"]
        answer_text = answer

        try:
            workout_data = json.loads(answer)
            workout = workout_data.get("workout", [])
        except:
            workout = []

    # SAVE WORKOUTS
    for ex in workout:
        new_workout = Workout(
            exercise=ex["exercise"],
            sets=ex["sets"],
            reps=ex["reps"],
            date=date.today()
        )
        db.session.add(new_workout)

    # SAVE CHAT
    new_chat = Chat(
        question=question,
        response=answer_text
    )

    db.session.add(new_chat)
    db.session.commit()

    return jsonify({
        "question": question,
        "workout": workout
    })

# GET CHAT HISTORY
@app.route("/chat-history")
def chat_history():

    chats = Chat.query.all()

    data = []

    for c in chats:
        data.append({
            "question": c.question,
            "response": c.response
        })

    return jsonify({"history": data})

# GET TODAY WORKOUT
@app.route("/today-workout")
def today_workout():

    today = date.today()

    workouts = Workout.query.filter_by(date=today).all()

    data = []

    for w in workouts:
        data.append({
            "id": w.id,
            "exercise": w.exercise,
            "sets": w.sets,
            "reps": w.reps,
            "completed": w.completed
        })

    return jsonify({"today_workout": data})

# COMPLETE WORKOUT
@app.route("/complete-workout/<int:id>", methods=["POST"])
def complete_workout(id):

    workout = Workout.query.get(id)

    if workout:
        workout.completed = True
        db.session.commit()
        return jsonify({"message": "Workout completed"})

    return jsonify({"error": "Workout not found"})

# CREATE DATABASE
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)