import requests

url = "https://aerodatabox.p.rapidapi.com/airports/search/term"
querystring = {"q": "istanbul"}

headers = {
    "x-rapidapi-key": "84d0e3aefcmsh7b9d0212fdc6ed4p1f556bjsn3f45cd131b3f",
    "x-rapidapi-host": "aerodatabox.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
print(response.status_code)
print(response.text)
