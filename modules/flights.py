import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
AERO_API_KEY = os.getenv("AERO_API_KEY")


def get_icao_list_by_city(city_name):
    url = "https://aerodatabox.p.rapidapi.com/airports/search/term"
    querystring = {"q": city_name}
    headers = {
        "x-rapidapi-key": AERO_API_KEY,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        return []

    data = response.json()
    items = data.get("items", [])
    icao_list = []

    for item in items:
        if item.get("countryCode") in ["TR", "GB", "FR"]:
            icao = item.get("icao")
            if icao:
                icao_list.append(icao)

    return icao_list


def get_flights_by_cities(from_city, to_city):
    print(f"[DEBUG] Gelen şehirler → from_city: {from_city}, to_city: {to_city}")

    from_icao_list = get_icao_list_by_city(from_city)
    to_icao_list = get_icao_list_by_city(to_city)

    print(f"[DEBUG] ICAO Kodları → from: {from_icao_list}, to: {to_icao_list}")

    if not from_icao_list:
        return [f"'{from_city}' için ICAO kodu bulunamadı."]
    if not to_icao_list:
        return [f"'{to_city}' için ICAO kodu bulunamadı."]

    now = datetime.utcnow()
    start_time = now.strftime("%Y-%m-%dT%H:00")
    end_time = (now + timedelta(hours=12)).strftime("%Y-%m-%dT%H:00")

    querystring = {
        "direction": "Departure",
        "withLeg": "true",
        "withCancelled": "false",
        "withCodeshared": "true",
        "withCargo": "false",
        "withPrivate": "false",
        "withLocation": "true"
    }

    headers = {
        "x-rapidapi-key": AERO_API_KEY,
        "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
    }

    flights = []

    for from_icao in from_icao_list:
        url = f"https://aerodatabox.p.rapidapi.com/flights/airports/icao/{from_icao}/{start_time}/{end_time}"
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            part = response.json().get("departures", [])
            flights.extend(part)

    print(f"[DEBUG] Toplam gelen uçuş sayısı: {len(flights)}")

    for f in flights:
        try:
            flight_number = f.get("number", "N/A")
            dep = f.get("departure", {}).get("airport", {}).get("name", "Yok")
            arr = f.get("arrival", {}).get("airport", {}).get("name", "Yok")
            arr_icao = f.get("arrival", {}).get("airport", {}).get("icao", "Yok")
            print(f"[DEBUG] {flight_number}: {dep} → {arr} ({arr_icao})")
        except Exception as e:
            print(f"[Uçuş log hatası] {e}")

    filtered = []
    for f in flights:
        arrival_icao = f.get("arrival", {}).get("airport", {}).get("icao", "").lower()
        arrival_city = f.get("arrival", {}).get("airport", {}).get("municipalityName", "").lower()
        arrival_name = f.get("arrival", {}).get("airport", {}).get("name", "").lower()
        if any(to.lower() == arrival_icao for to in to_icao_list) or \
           any(to_city.lower() in field for field in [arrival_city, arrival_name]):
            filtered.append(f)

    results = []
    for flight in filtered:
        airline = flight.get("airline", {}).get("name", "Bilinmiyor")
        flight_number = flight.get("number", "N/A")
        departure_time = (
            flight.get("departure", {}).get("scheduledTimeLocal")
            or "Kalkış saati bulunamadı"
        )
        results.append(f"{airline} {flight_number} - Kalkış: {departure_time}")

    return results or [f"{from_city.title()} → {to_city.title()} için uçuş bulunamadı."]
