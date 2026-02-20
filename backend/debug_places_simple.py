import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=r'c:\Users\TAUHEED\Desktop\diassure\backend\.env')

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

async def search_places_debug():
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_PLACES_API_KEY not found in .env")
        return

    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location"
    }
    
    # Coordinates for a place likely to have doctors (e.g., Delhi, India based on username/context or just a known location)
    # Using New Delhi coordinates for testing: 28.6139, 77.2090
    latitude = 28.6139
    longitude = 77.2090
    radius = 5000
    query = "doctor clinic near me"
    
    body = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": float(radius)
            }
        },
        "maxResultCount": 5
    }
    
    print(f"Testing Google Places API with key: {GOOGLE_API_KEY[:5]}...{GOOGLE_API_KEY[-5:]}")
    print(f"URL: {url}")
    print(f"Body: {body}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(search_places_debug())
