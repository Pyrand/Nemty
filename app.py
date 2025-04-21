from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

app = Flask(__name__)
chat_history = []

def get_recommended_places(city_preference=None, category_preference=None):
    import fetch_otm_data  # Dinamik çağır, çünkü bazen Flask içinde sorun çıkabiliyor

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

    if not results:
        # Eğer sonuç yoksa OpenTripMap'ten çek
        print("🌐 Veritabanında sonuç bulunamadı, API'den çekiliyor...")

        # Şehir bilgisi (enlem-boylam) world_cities.json içinden bulunmalı
        try:
            import json
            with open("world_cities.json", "r", encoding="utf-8") as f:
                cities = json.load(f)

            match = next((c for c in cities if c["city"].lower() == city_preference.lower()), None)
            if match:
                fetch_otm_data.fetch_places_for_city(
                    match["city"], match["country"], match["lat"], match["lon"], category_preference
                )

                # Tekrar veri tabanını sorgula
                cursor.execute(query, params)
                results = cursor.fetchall()

        except Exception as e:
            print(f"❌ API çekme hatası: {e}")

    conn.close()
    return results[:2]


@app.route("/")
def index():
    global chat_history
    chat_history = []
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global chat_history
    user_input = request.json.get("message")

    if not chat_history:
        chat_history.append({
            "role": "system",
            "content": (
                "You are a helpful and concise travel assistant. "
                "The user may describe their vacation preferences in any way. "
                "Try to infer the vacation type (nature, beach, culture, food, religion, architecture, etc.) and location if possible. "
                "You can use the get_recommended_places(city, category) function to look into a travel database if it makes sense, "
                "but you are not required to do so. Only use it if you are confident that a location and category can be matched. "
                "Avoid repeating results or overexplaining. Focus on short, useful suggestions. "
                "Categories available in the database include: natural, cultural, beaches, historic, religion, architecture, foods, museums, sport, amusements."
            )
        })

    chat_history.append({"role": "user", "content": user_input})

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
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

        # Eğer AI fonksiyonu çağırmak istiyorsa:
        if response_msg.tool_calls:
            for call in response_msg.tool_calls:
                if call.function.name == "get_recommended_places":
                    args = call.function.arguments
                    import json
                    args = json.loads(args)
                    result = get_recommended_places(**args)

                    if result:
                        reply = "\n".join([f"- {name} ({city}): {desc}" for name, city, desc in result])
                    else:
                        reply = "Veritabanında uygun sonuç bulunamadı."

                    chat_history.append({
                        "role": "function",
                        "name": "get_recommended_places",
                        "content": reply
                    })

                    # Fonksiyon yanıtını tekrar modelin yorumlaması için gönder
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=chat_history
                    )
                    ai_reply = completion.choices[0].message.content
                    break
        else:
            ai_reply = response_msg.content

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
