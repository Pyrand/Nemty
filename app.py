from flask import Flask, render_template, request
from openai import OpenAI
import os
from dotenv import load_dotenv

# .env dosyasındaki API anahtarını al
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI istemcisi oluştur
client = OpenAI(api_key=api_key)

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    
    if request.method == "POST":
        user_input = request.form["message"]

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Sen bir akıllı seyahat danışmanısın."},
                    {"role": "user", "content": user_input}
                ]
            )

            response = completion.choices[0].message.content

        except Exception as e:
            response = f"Hata oluştu: {e}"

    return render_template("index.html", response=response)

if __name__ == "__main__":
    app.run(debug=True)
