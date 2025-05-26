import requests
import os

def get_hotels_by_city(city_name):
    url = "https://booking-com.p.rapidapi.com/v1/hotels/search"
    querystring = {
        "locale": "en-us",
        "dest_type": "city",
        "order_by": "popularity",
        "units": "metric",
        "adults_number": "1",
        "dest_id": "",   # Burası için aşağıda şehir ID'si bulacağız
        "checkin_date": "2025-06-01",
        "checkout_date": "2025-06-02",
        "room_number": "1",
        "children_number": "0",
        "children_ages": ""
    }
    # Önce şehir ID’si gerekiyor!
    city_url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"
    city_query = {"name": city_name, "locale": "en-us"}
    headers = {
        "X-RapidAPI-Key": os.getenv("BOOKING_API_KEY"),
        "X-RapidAPI-Host": "booking-com.p.rapidapi.com"
    }

    # Şehir ID’si al
    city_resp = requests.get(city_url, headers=headers, params=city_query)
    cities = city_resp.json()
    if not cities:
        return [f"{city_name} için otel bulunamadı."]
    dest_id = cities[0]["dest_id"]
    querystring["dest_id"] = dest_id

    # Otel listesini al
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    hotels = []
    for h in data.get("result", [])[:3]:  # İlk 3 oteli göster
        name = h.get("hotel_name", "Bilinmiyor")
        price = h.get("min_total_price", "Fiyat yok")
        address = h.get("address", "Adres yok")
        currency = h.get("currencycode", "")
        hotels.append(f"{name} - {address} - {price} {currency}")
    return hotels or [f"{city_name} için otel bulunamadı."]
