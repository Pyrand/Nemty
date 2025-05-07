import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
AERO_API_KEY = os.getenv("AERO_API_KEY")

# ICAO eşlemesi (şehirlere göre)
CITY_TO_ICAO = {
    "istanbul": "LTFM",
    "ankara": "LTAC",
    "londra": "EGLL",
    "london": "EGLL",
    "paris": "LFPG",
    "berlin": "EDDB",
    "roma": "LIRF",
    "madrid": "LEMD"
    # ihtiyaç olursa buraya eklenir
}

def get_flights_by_city_arrival(arrival_city, departure_icao="LTFM"):
    arrival_city = arrival_city.lower()
    arrival_icao = CITY_TO_ICAO.get(arrival_city)

    if not arrival_icao:
        return [f"'{arrival_city}' için ICAO kodu tanımlı değil."]

    now = datetime.utcnow()
    start_time = now.strftime("%Y-%m-%dT%H:00")
    end_time = (now + timedelta(hours=6)).strftime("%Y-%m-%dT%H:00")  # max 12 saat sınırı

    url = f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{departure_icao}/{start_time}/{end_time}"

    querystring = {
        "direction": "Departure",
        "withLeg": "false",
        "withCancelled": "false",
        "withCodeshared": "true",
        "withCargo": "false",
        "withPrivate": "false"
    }

    headers = {
        "x-rapidapi-key": AERO_API_KEY,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        return [f"Hata: {response.status_code} - {response.text}"]

    flights = response.json().get("departures", [])

    filtered = [
        f for f in flights
        if f.get("arrival", {}).get("airport", {}).get("icao") == arrival_icao
    ]

    results = []
    for flight in filtered:
        airline = flight.get("airline", {}).get("name", "Bilinmiyor")
        flight_number = flight.get("number", "N/A")
        departure_time = flight.get("departure", {}).get("scheduledTimeLocal", "Yok")
        results.append(f"{airline} {flight_number} - Kalkış: {departure_time}")

    return results
