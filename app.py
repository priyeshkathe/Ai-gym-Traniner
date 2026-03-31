from flask import Flask, render_template, request, jsonify, redirect, session
import sqlite3
import requests
from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # Loaded from .env, do not hardcode


# ---------------- DATABASE ---------------- #

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        role TEXT,
        content TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- AUTH ---------------- #

@app.route("/", methods=["GET","POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            error = "Please enter username and password"

        else:
            conn = get_db()

            user = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            ).fetchone()

            if user is None:
                error = "User does not exist"

            elif user["password"] != password:
                error = "Incorrect password"

            else:
                session["user_id"] = user["id"]
                return redirect("/dashboard")

    return render_template("login.html", error=error)
@app.route("/register", methods=["GET","POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if not username or not password:
            error = "Please fill all fields"

        else:
            conn = get_db()

            existing = conn.execute(
                "SELECT * FROM users WHERE username=?",
                (username,)
            ).fetchone()

            if existing:
                error = "Username already exists"

            else:
                conn.execute(
                    "INSERT INTO users(username,password) VALUES (?,?)",
                    (username,password)
                )

                conn.commit()

                return redirect("/")

    return render_template("register.html", error=error)

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/")

    return render_template("dashboard.html")


# ---------------- CHAT SYSTEM ---------------- #

@app.route("/create_chat")
def create_chat():

    if "user_id" not in session:
        return jsonify({"error": "not logged in"})

    conn = get_db()

    cur = conn.execute(
        "INSERT INTO chats(user_id,title) VALUES (?,?)",
        (session["user_id"], "New Chat")
    )

    conn.commit()

    return jsonify({"chat_id": cur.lastrowid})


@app.route("/get_chats")
def get_chats():

    conn = get_db()

    chats = conn.execute(
        "SELECT * FROM chats WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)
    ).fetchall()

    return jsonify([dict(c) for c in chats])


@app.route("/get_messages/<chat_id>")
def get_messages(chat_id):

    conn = get_db()

    messages = conn.execute(
        "SELECT role,content FROM messages WHERE chat_id=?",
        (chat_id,)
    ).fetchall()

    return jsonify([dict(m) for m in messages])


@app.route("/delete_chat/<chat_id>")
def delete_chat(chat_id):

    conn = get_db()

    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))

    conn.commit()

    return "ok"

GYM_KEYWORDS = [
    "gym","workout","exercise","fitness","muscle","protein",
    "weight","diet","training","cardio","strength","body",
    "fat","calories","bench","squat","deadlift","pushup",
    "pullup","biceps","triceps","abs","legs","shoulder"
]

def is_gym_related(text):
    text = text.lower()
    return any(word in text for word in GYM_KEYWORDS)

import random

FUNNY_RESPONSES = [
    "Bro I'm a gym trainer, not Google 🤨 Ask me something about workouts.",
    
    "That question won't build your muscles 💪 Ask me about gym training!",
    
    "I'm here to grow your biceps, not answer random questions 😂",
    
    "Wrong gym bro! Ask about workouts, diet, or fitness.",

    "If the question doesn't burn calories, I won't answer it 🔥",
    
    "I only train muscles, not answer everything in the universe 😎"
]

# ---------------- AI CHAT ---------------- #

@app.route("/chat", methods=["POST"])
def chat():

    user_message = request.json["message"]
    chat_id = request.json["chat_id"]
    # Check if message is gym related
    if not is_gym_related(user_message):

        reply = random.choice(FUNNY_RESPONSES)

        conn = get_db()

        conn.execute(
            "INSERT INTO messages(chat_id,role,content) VALUES (?,?,?)",
            (chat_id, "assistant", reply)
        )

        conn.commit()

        return jsonify({"reply": reply})

    conn = get_db()

    # Save user message
    conn.execute(
        "INSERT INTO messages(chat_id,role,content) VALUES (?,?,?)",
        (chat_id, "user", user_message)
    )

    prompt = f"""
You are a professional AI gym trainer.

Always format your responses clearly using:

- Headings
- Bullet points
- Numbered lists
- Short sections
- Line spacing

Avoid long paragraphs.

User question:
{user_message}


"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    data = response.json()

    reply = data["choices"][0]["message"]["content"]

    # Save bot message
    conn.execute(
        "INSERT INTO messages(chat_id,role,content) VALUES (?,?,?)",
        (chat_id, "assistant", reply)
    )

    # Update title if first message
    title = user_message[:30]

    conn.execute(
        "UPDATE chats SET title=? WHERE id=?",
        (title, chat_id)
    )

    conn.commit()

    return jsonify({"reply": reply})


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

