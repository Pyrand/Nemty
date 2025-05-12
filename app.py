from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
from dotenv import load_dotenv
from modules.helpers import print_error
from modules.database import query_local_database, fetch_from_opentripmap, get_recommended_places
from modules.ai_tools import client, create_completion
from modules.flights import get_flights_by_cities
from modules.helpers import print_error


load_dotenv()

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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
                "You must always translate city names into English before using them in function calls or database lookups."
                "Always extract both 'from_city' (departure city) and 'city_preference' (destination). These must be present in every call to the 'get_recommended_places' function. If they are not obvious, ask the user or make a reasonable guess."
                "You must always translate city names like from_city and city_preference into English before passing them to any function call or database query."
                "Your responses to the user must always remain in the same language the user used. "
                "When you receive results from the get_recommended_places function, you must prioritize suggesting places from that list. "
                "If the number of places from the database/API is insufficient to fully cover the user's request (e.g., building a multi-day travel plan), "
                "You are allowed to supplement your response by suggesting additional places based on your own knowledge of the city and category. "
                "If no places are available at all, you may politely inform the user that no suggestions were found. "
                "Focus on creating complete and helpful travel suggestions without overexplaining."
            )
        })

    chat_history.append({"role": "user", "content": user_input})

    ai_reply = ""
    flight_data = []

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
                            "from_city": {"type": "string", "description": "Departure city"},
                            "city_preference": {"type": "string", "description": "Destination city"},
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
                    import json
                    args = json.loads(call.function.arguments)

                    from_city = args.get("from_city", "").strip()
                    to_city = args.get("city_preference", "").strip()
                    category = args.get("category_preference", "").strip()

                    print(f"[DEBUG] from_city: {from_city}, to_city: {to_city}")

                    result = get_recommended_places(city_preference=to_city, category_preference=category)

                    reply = "\n".join([f"- {name} ({city}): {desc}" for name, city, desc in result]) if result else "Veritabanında uygun sonuç bulunamadı."
                    chat_history.append({"role": "function", "name": "get_recommended_places", "content": reply})

                    if from_city and to_city:
                        flight_data = get_flights_by_cities(from_city, to_city)
                        print(f"[DEBUG] Uçuş verileri: {flight_data}")

                    completion = create_completion(messages=chat_history)
                    ai_reply = completion.choices[0].message.content
                    break
        else:
            ai_reply = response_msg.content

    except Exception as e:
        ai_reply = f"Hata oluştu: {e}"

    chat_history.append({"role": "assistant", "content": ai_reply})
    session["chat_history"] = chat_history

    return jsonify({"response": ai_reply, "history": chat_history, "flights": flight_data})


@app.route("/reset", methods=["GET"])
def reset():
    session.pop("chat_history", None)
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)