import sqlite3
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
from dotenv import load_dotenv
from modules.helpers import print_error, save_message, load_user_history
from modules.database import query_local_database, fetch_from_opentripmap, get_recommended_places
from modules.ai_tools import client, create_completion
from modules.flights import get_flights_by_cities
from modules.hotels import get_hotels_by_city, extract_guests_from_message
from modules.auth import register_user, login_user

load_dotenv()

app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    if "user" not in session:
        return jsonify({"response": "Not logged in.", "flights": []})

    username = session["user"]
    user_input = request.json.get("message")

    chat_history = load_user_history(username, for_model=True)


    if not any(msg.get("role") == "system" for msg in chat_history):
        system_msg = {
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
                "Do not ever translate your response or change the language. If the user's message is in English, always answer in English. If the user's message is in Turkish, always answer in Turkish. Never reply in a different language."
            )
        }
        
        save_message(username, "system", system_msg["content"])
        chat_history.insert(0, system_msg)

    chat_history.append({"role": "user", "content": user_input})
    save_message(username, "user", user_input)

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

                    reply = "\n".join([f"- {name} ({city}): {desc}" for name, city, desc in result]) if result else "No suitable results found in the database."
                    chat_history.append({"role": "function", "name": "get_recommended_places", "content": reply})
                    save_message(username, "function", reply, name="get_recommended_places")

                    if from_city and to_city:
                        flight_data = get_flights_by_cities(from_city, to_city)
                        save_message(username, "flight_results", "\n".join(flight_data))
                        print(f"[DEBUG] Flight data: {flight_data}")

                    completion = create_completion(messages=chat_history)
                    ai_reply = completion.choices[0].message.content
                    break
        else:
            ai_reply = response_msg.content

    except Exception as e:
        ai_reply = f"An error occurred: {e}"

    save_message(username, "assistant", ai_reply)

    # --- FRONTEND’E GÖNDERMEK İÇİN TÜM GEÇMİŞİ AL ---
    user_history = load_user_history(username, for_model=False)

    return jsonify({"response": ai_reply, "history": user_history, "flights": flight_data})

@app.route("/hotels", methods=["POST"])
def hotels():
    print("[DEBUG] /hotels endpoint called")
    try:
        request_data = request.get_json()
        print(f"[DEBUG] Request data: {request_data}")

        city = request_data.get("city") if request_data else None
        user_message = request_data.get("message") if request_data else ""
        print(f"[DEBUG] Extracted city: {city}")
        print(f"[DEBUG] Extracted message: {user_message}")

        if not city:
            print("[DEBUG] No city provided")
            return jsonify({"hotels": ["City name not specified."]})

        adults, children = extract_guests_from_message(user_message)
        print(f"[DEBUG] Extracted adults: {adults}, children: {children}")

        print(f"[DEBUG] Calling get_hotels_by_city with: {city}")
        hotels_result = get_hotels_by_city(city, adults=adults, children=children)
        print(f"[DEBUG] Hotels result: {hotels_result}")

        # === BURADA SONUÇLARI KAYDET ===
        if "user" in session and hotels_result:
            save_message(session["user"], "hotel_results", "\n".join(hotels_result))

        return jsonify({"hotels": hotels_result})

    except Exception as e:
        print(f"[DEBUG] Error in /hotels endpoint: {e}")
        return jsonify({"hotels": [f"An error occurred: {str(e)}"]})


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    phone = data.get("phone")

    success, msg = register_user(username, password, email, phone)
    if success:
        session["user"] = username
    return jsonify({"success": success, "message": msg})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    success, msg = login_user(username, password)
    if success:
        session["user"] = username
    return jsonify({"success": success, "message": msg})

@app.route("/api/history", methods=["GET"])
def api_history():
    if "user" not in session:
        return jsonify({"history": [], "flights": [], "hotels": []})
    username = session["user"]

    from modules.helpers import load_user_history

    chat_history = load_user_history(username, for_model=False)

    # Son eklenen uçuş ve otel sonuçlarını getir
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content FROM user_messages
        WHERE username = ? AND role = 'flight_results'
        ORDER BY created_at DESC LIMIT 1
    """, (username,))
    flight_row = cursor.fetchone()
    flight_results = flight_row[0].split('\n') if flight_row else []

    cursor.execute("""
        SELECT content FROM user_messages
        WHERE username = ? AND role = 'hotel_results'
        ORDER BY created_at DESC LIMIT 1
    """, (username,))
    hotel_row = cursor.fetchone()
    hotel_results = hotel_row[0].split('\n') if hotel_row else []

    conn.close()
    return jsonify({
        "history": chat_history,
        "flights": flight_results,
        "hotels": hotel_results
    })


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"success": True})

@app.route("/api/check-login")
def check_login():
    return jsonify({"logged_in": "user" in session, "user": session.get("user")})

@app.route("/reset", methods=["GET"])
def reset():
    if "user" in session:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_messages WHERE username = ?", (session["user"],))
        conn.commit()
        conn.close()
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    app.run(debug=True)
