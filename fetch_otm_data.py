import requests
import sqlite3
import os
import json
import time
from dotenv import load_dotenv

load_dotenv(override=True)
OTM_API_KEY = os.getenv("OTM_API_KEY")

def create_table_if_not_exists():
    conn = sqlite3.connect("destinations.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            city TEXT,
            country TEXT,
            category TEXT,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

def fetch_places_for_city(city_name, country, lat, lon, category, radius=10000, limit=10):
    url = f"https://api.opentripmap.com/0.1/en/places/radius?radius={radius}&lon={lon}&lat={lat}&kinds={category}&format=json&limit={limit}&apikey={OTM_API_KEY}"
    
    try:
        response = requests.get(url)
        places = response.json()
        if not isinstance(places, list):
            print(f"Geçersiz yanıt: {places}")
            return
    except Exception as e:
        print(f"JSON decode hatası: {e}")
        return

    conn = sqlite3.connect("destinations.db")
    cursor = conn.cursor()

    for place in places:
        xid = place.get("xid")
        if not xid:
            continue

        time.sleep(1.0)
        detail_url = f"https://api.opentripmap.com/0.1/en/places/xid/{xid}?apikey={OTM_API_KEY}"
        detail_resp = requests.get(detail_url).json()

        name = detail_resp.get("name", "").strip()
        desc = detail_resp.get("wikipedia_extracts", {}).get("text", "Açıklama yok.")
        if not name:
            continue

        cursor.execute("INSERT INTO places (name, city, country, category, description) VALUES (?, ?, ?, ?, ?)",
                       (name, city_name, country, category, desc))

    conn.commit()
    conn.close()
    print(f"✅ {city_name}/{category} tamamlandı.")
    time.sleep(1.0)

def main():
    create_table_if_not_exists()
    with open("world_cities.json", "r", encoding="utf-8") as f:
        cities = json.load(f)

    categories = [
        "natural", "cultural", "beaches", "historic",
        "religion", "architecture", "foods", "museums", "sport", "amusements"
    ]

    for city in cities:
        city_name = city["city"]
        country = city["country"]
        lat = city["lat"]
        lon = city["lon"]

        for category in categories:
            try:
                print(f"⏳ {city_name} / {category} çekiliyor...")
                fetch_places_for_city(city_name, country, lat, lon, category)
            except Exception as e:
                print(f"❌ Hata: {city_name}/{category} - {e}")

if __name__ == "__main__":
    main()
