from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from openai import OpenAI
import os
import sqlite3
import json
from dotenv import load_dotenv
import fetch_otm_data

load_dotenv()

# OpenAI ayarı
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Flask ayarı
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Yardımcı fonksiyonlar
def print_error(e):
    print(f"❌ Hata: {e}")

def query_local_database(city_preference=None, category_preference=None):
    conn = sqlite3.connect("destinations.db")
    cursor = conn.cursor()

    query = "SELECT name, city, description FROM places WHERE 1=1"
    params = []
    if city_preference:
        query += " AND city LIKE ?"
        params.append(f"%{city_preference}%")
    if category_preference:
        query += " AND category LIKE ?"
        params.append(f"%{category_preference}%")

    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()

    return results

def fetch_from_opentripmap(city_preference, category_preference):
    try:
        with open("world_cities.json", "r", encoding="utf-8") as f:
            cities = json.load(f)

        match = next((c for c in cities if c["city"].lower() == city_preference.lower()), None)
        if match:
            fetch_otm_data.fetch_places_for_city(
                match["city"], match["country"], match["lat"], match["lon"], category_preference
            )
    except Exception as e:
        print_error(e)

def get_recommended_places(city_preference=None, category_preference=None):
    results = query_local_database(city_preference, category_preference)

    if results:
        print(f"✅ Veritabanından veri çekildi: {city_preference} / {category_preference}")
    else:
        print("🌐 Veritabanında bulunamadı, API'den çekiliyor...")
        fetch_from_opentripmap(city_preference, category_preference)
        results = query_local_database(city_preference, category_preference)

    return results


def create_completion(messages, tools=None, tool_choice=None):
    params = {
        "model": "gpt-4o",
        "messages": messages
    }
    if tools is not None:
        params["tools"] = tools
    if tool_choice is not None and tools is not None:
        params["tool_choice"] = tool_choice

    return client.chat.completions.create(**params)

# Routes
@app.route("/")
def index():
    session["chat_history"] = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    if "chat_history" not in session:
        session["chat_history"] = []

    chat_history = session["chat_history"]

    if not chat_history:
        chat_history.append({
            "role": "system",
            "content": (
                "You are a helpful and concise travel assistant. "
                "The user may describe their vacation preferences in any language. "
                "You must infer the city and the vacation category, and internally translate only the city name and category name into English for database function calls. "
                "Your responses to the user must always remain in the same language the user used. "
                "When you receive results from the get_recommended_places function, you must prioritize suggesting places from that list. "
                "If the number of places from the database/API is insufficient to fully cover the user's request (e.g., building a multi-day travel plan), "
                "you are allowed to supplement your response by suggesting additional places based on your own knowledge of the city and category. "
                "If no places are available at all, you may politely inform the user that no suggestions were found. "
                "Focus on creating complete and helpful travel suggestions without overexplaining."
            )
        })

    chat_history.append({"role": "user", "content": user_input})

    try:
        completion = create_completion(
            messages=chat_history,
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_recommended_places",
                    "description": "Get travel suggestions from database based on city and category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_preference": {"type": "string", "description": "City name"},
                            "category_preference": {"type": "string", "description": "Category like natural, cultural, etc."}
                        },
                        "required": ["city_preference", "category_preference"]
                    }
                }
            }],
            tool_choice="auto"
        )

        response_msg = completion.choices[0].message

        if response_msg.tool_calls:
            for call in response_msg.tool_calls:
                if call.function.name == "get_recommended_places":
                    args = json.loads(call.function.arguments)
                    result = get_recommended_places(**args)

                    reply = "\n".join([f"- {name} ({city}): {desc}" for name, city, desc in result]) if result else "Veritabanında uygun sonuç bulunamadı."

                    chat_history.append({"role": "function", "name": "get_recommended_places", "content": reply})

                    completion = create_completion(messages=chat_history)
                    ai_reply = completion.choices[0].message.content
                    break
        else:
            ai_reply = response_msg.content

    except Exception as e:
        ai_reply = f"Hata oluştu: {e}"

    chat_history.append({"role": "assistant", "content": ai_reply})
    session["chat_history"] = chat_history

    return jsonify({"response": ai_reply, "history": chat_history})

@app.route("/reset", methods=["GET"])
def reset():
    session.pop("chat_history", None)
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)
