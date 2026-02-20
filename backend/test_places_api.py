import os
from dotenv import load_dotenv
import httpx
import asyncio
import json

load_dotenv()

async def test():
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    print(f"API Key (first 15 chars): {api_key[:15] if api_key else None}...")
    print(f"Full key length: {len(api_key) if api_key else 0}")
    
    url = 'https://places.googleapis.com/v1/places:searchText'
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': api_key,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress'
    }
    body = {
        'textQuery': 'doctor clinic',
        'locationBias': {
            'circle': {
                'center': {'latitude': 28.6139, 'longitude': 77.2090},
                'radius': 10000.0
            }
        },
        'maxResultCount': 5
    }
    
    print(f"\nSending request to: {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        try:
            data = response.json()
            print(f"Response:\n{json.dumps(data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")

if __name__ == '__main__':
    asyncio.run(test())
