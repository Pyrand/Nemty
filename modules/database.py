import sqlite3
import json
import fetch_otm_data
from modules.helpers import print_error

VALID_CATEGORIES = [
    "natural", "cultural", "beaches", "historic",
    "religion", "architecture", "foods", "museums",
    "sport", "amusements"
]

def query_local_database(city_preference=None, category_preference=None):
    conn = sqlite3.connect("destinations.db")
    cursor = conn.cursor()

    query = "SELECT name, city, description FROM places WHERE 1=1"
    params = []
    if city_preference:
        query += " AND LOWER(city) LIKE ?"
        params.append(f"%{city_preference}%")
    if category_preference:
        query += " AND LOWER(category) LIKE ?"
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
    if category_preference and category_preference not in VALID_CATEGORIES:
        print(f"⚠️ Geçersiz kategori: {category_preference}")
        return [("Kategori hatası", city_preference or "Bilinmiyor", f"'{category_preference}' kategorisi tanınmıyor.")]

    results = query_local_database(city_preference, category_preference)

    if results:
        print(f"✅ Veritabanından veri çekildi: {city_preference} / {category_preference}")
    else:
        print("🌐 Veritabanında bulunamadı, API'den çekiliyor...")
        fetch_from_opentripmap(city_preference, category_preference)
        results = query_local_database(city_preference, category_preference)

    return results
