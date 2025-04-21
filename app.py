from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
chat_history = []

@app.route("/")
def index():
    global chat_history
    chat_history = []  # Sayfa ilk açıldığında (GET) sıfırla
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history
    user_input = request.json.get("message")

    if not chat_history:
        chat_history.append({
            "role": "system",
            "content": (
                "You are an experienced, friendly, and knowledgeable **travel advisor**. "
                "Based on the user's travel preferences, budget, and interests, you suggest cities, countries, activities, flights, and hotels. "
                "Your responses should be clear, inspiring, and helpful. "
                "Ask questions to better understand what the user wants."
            )
        })

    chat_history.append({"role": "user", "content": user_input})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=chat_history
        )
        ai_reply = completion.choices[0].message.content
    except Exception as e:
        ai_reply = f"Hata oluştu: {e}"

    chat_history.append({"role": "assistant", "content": ai_reply})

    return jsonify({
        "response": ai_reply,
        "history": chat_history
    })

@app.route("/reset", methods=["GET"])
def reset():
    global chat_history
    chat_history = []
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    app.run(debug=True)
