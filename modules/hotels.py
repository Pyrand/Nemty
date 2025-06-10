import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from .hotels_mock import MOCK_HOTELS

load_dotenv()

class AmadeusAuth:
    def __init__(self):
        self.client_id = os.getenv("AMADEUS_API_KEY")
        self.client_secret = os.getenv("AMADEUS_API_SECRET")
        self.access_token = None
        self.token_expires = None

    def get_access_token(self):
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token

        if not self.client_id or not self.client_secret:
            print("[DEBUG] Amadeus API credentials not found")
            return None

        try:
            url = "https://test.api.amadeus.com/v1/security/oauth2/token"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }

            response = requests.post(url, headers=headers, data=data, timeout=10)

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)
                self.token_expires = datetime.now() + timedelta(seconds=expires_in - 300)
                print("[DEBUG] Amadeus access token received")
                return self.access_token
            else:
                print(f"[DEBUG] Amadeus token error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"[DEBUG] Amadeus token exception: {e}")
            return None

amadeus_auth = AmadeusAuth()

def translate_city_name(city_name):
    city = city_name.strip()
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"Translate the city name '{city}' to English. Only return the city name, do not add anything else."
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        english_city = response.choices[0].message.content.strip()
        print(f"[DEBUG] '{city}' → '{english_city}' (Translated with OpenAI)")
        return english_city
    except Exception as e:
        print(f"[DEBUG] OpenAI translation error: {e}")
        return city

def get_city_geocode(city_name):
    token = amadeus_auth.get_access_token()
    if not token:
        return None
    try:
        url = "https://test.api.amadeus.com/v1/reference-data/locations/cities"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "keyword": city_name,
            "max": 1
        }
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            locations = data.get("data", [])
            if locations:
                location = locations[0]
                return {
                    "latitude": location.get("geoCode", {}).get("latitude"),
                    "longitude": location.get("geoCode", {}).get("longitude"),
                    "iata_code": location.get("iataCode")
                }
        else:
            print(f"[DEBUG] Amadeus geocode error: {response.status_code}")
    except Exception as e:
        print(f"[DEBUG] Geocode exception: {e}")
    return None

def search_hotels_by_geocode(latitude, longitude):
    token = amadeus_auth.get_access_token()
    if not token:
        return []
    try:
        url = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geocode"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": 20,
            "radiusUnit": "KM"
        }
        print(f"[DEBUG] Amadeus hotel search in progress: {latitude}, {longitude}")
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            hotels = data.get("data", [])
            hotel_ids = []
            for hotel in hotels[:3]:
                hotel_id = hotel.get("hotelId")
                if hotel_id:
                    hotel_ids.append(hotel_id)
            print(f"[DEBUG] Found hotel IDs: {hotel_ids}")
            return hotel_ids
        else:
            print(f"[DEBUG] Amadeus hotel search error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[DEBUG] Hotel search exception: {e}")
    return []

from concurrent.futures import ThreadPoolExecutor, as_completed

def get_hotel_offers(hotel_ids, adults=1, children=0):
    if not hotel_ids:
        return []
    token = amadeus_auth.get_access_token()
    if not token:
        return []
    checkin = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
    checkout = (datetime.now() + timedelta(days=91)).strftime("%Y-%m-%d")

    def fetch_offer(hotel_id):
        try:
            url = "https://test.api.amadeus.com/v3/shopping/hotel-offers"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "hotelIds": hotel_id,
                "adults": adults,
                "children": children,
                "checkInDate": checkin,
                "checkOutDate": checkout
            }
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                hotels_data = data.get("data", [])
                offers_list = []
                for hotel_data in hotels_data:
                    hotel = hotel_data.get("hotel", {})
                    name = hotel.get("name", "Unknown Name")
                    address = hotel.get("address", {})
                    city_name_addr = address.get("cityName", "")
                    country = address.get("countryCode", "")
                    location = f"{city_name_addr}, {country}" if city_name_addr else "No location info"
                    offers = hotel_data.get("offers", [])
                    price_info = "No price info"
                    if offers:
                        price = offers[0].get("price", {})
                        total = price.get("total")
                        currency = price.get("currency", "USD")
                        if total:
                            price_info = f"{total} {currency}"
                    rating = f"⭐ {round(8.0 + (hash(name) % 20) / 10, 1)}/10"
                    formatted_hotel = f"{name} - {location} - {price_info} ({rating})"
                    offers_list.append(formatted_hotel)
                return offers_list
            else:
                return []
        except Exception as e:
            print(f"[DEBUG] Hotel offers exception: {e}")
            return []

    all_offers = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_offer, hotel_id) for hotel_id in hotel_ids[:10]]
        for future in as_completed(futures):
            try:
                result = future.result()
                all_offers.extend(result)
            except Exception as e:
                print(f"[DEBUG] Thread error: {e}")

    return all_offers[:3] if all_offers else []

def extract_guests_from_message(user_message):
    try:
        from openai import OpenAI
        import os
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = (
            "The user is looking for a hotel. Extract the number of adults and children separately from the sentence. "
            "Return only in this format: adults: <number of adults>, children: <number of children>. "
            "If no number is mentioned, write adults: 1, children: 0.\n"
            f"Sentence: {user_message}"
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        import re
        match = re.search(r"adults:\s*(\d+),\s*children:\s*(\d+)", result)
        if match:
            return int(match.group(1)), int(match.group(2))
        else:
            return 1, 0
    except Exception as e:
        print(f"[DEBUG] Error extracting guests: {e}")
        return 1, 0

def get_hotels_by_city(city_name, adults=1, children=0):
    print(f"[DEBUG] Searching hotels: {city_name}, adults: {adults}, children: {children}")
    
    city_name_eng = translate_city_name(city_name)
    if not city_name_eng or not city_name_eng.strip():
        return get_mock_hotels_by_city(city_name)
    
    geocode = get_city_geocode(city_name_eng)
    if not geocode or not geocode["latitude"] or not geocode["longitude"]:
        return get_mock_hotels_by_city(city_name)
    
    hotel_ids = search_hotels_by_geocode(geocode["latitude"], geocode["longitude"])
    if not hotel_ids:
        return get_mock_hotels_by_city(city_name)
    
    hotel_offers = get_hotel_offers(hotel_ids, adults=adults, children=children)
    if hotel_offers:
        return hotel_offers
    else:
        mock_hotels = get_mock_hotels_by_city(city_name)
        if not mock_hotels and city_name_eng.lower() != city_name.lower():
            mock_hotels = get_mock_hotels_by_city(city_name_eng)
        return mock_hotels

def get_mock_hotels_by_city(city_name):
    variations = [
        city_name.strip().lower(),
        city_name.strip().title(),
        city_name.strip().capitalize()
    ]
    try:
        from .hotels import translate_city_name
        eng = translate_city_name(city_name)
        variations.append(eng.lower())
        variations.append(eng.title())
    except Exception:
        pass

    for var in variations:
        if var in MOCK_HOTELS:
            return MOCK_HOTELS[var]
    return []
