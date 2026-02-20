from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import httpx
import os
import math
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/places", tags=["places"])

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Doctor type to search keyword mapping
DOCTOR_TYPE_KEYWORDS = {
    "podiatrist": "podiatrist",
    "physician": "physician",
    "diabetologist": "diabetologist"
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in km using Haversine formula"""
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


async def get_road_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> dict:
    """Get road distance using Distance Matrix API"""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "key": GOOGLE_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if data.get("status") != "OK":
            return None
        
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return None
        
        return {
            "distance_text": element["distance"]["text"],
            "distance_meters": element["distance"]["value"],
            "duration_text": element["duration"]["text"]
        }
    except Exception as e:
        print(f"[DISTANCE MATRIX] Error: {e}")
        return None


async def search_places_new_api(query: str, latitude: float, longitude: float, radius: int) -> list:
    """Use Google Places API (New) Text Search"""
    url = "https://places.googleapis.com/v1/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.nationalPhoneNumber,places.currentOpeningHours,places.regularOpeningHours,places.location,places.googleMapsUri,places.websiteUri"
    }
    
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
        "maxResultCount": 20
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers)
        data = response.json()
    
    print(f"[PLACES API NEW] Query: {query}, Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"[PLACES API NEW] Error: {data}")
        return []
    
    return data.get("places", [])


@router.get("/nearby")
async def get_nearby_doctors(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius: int = Query(5000, description="Search radius in meters (default 5km)"),
    doctor_types: Optional[str] = Query(None, description="Comma-separated doctor types: podiatrist,physician,diabetologist")
):
    """
    Fetch nearby doctors within specified radius using Google Places API (New).
    Returns list of doctors with contact info, ratings, and distance.
    """
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google Places API key not configured")
    
    print(f"[PLACES API] Searching at lat={latitude}, lng={longitude}, radius={radius}")
    
    # Parse doctor types
    queries = []
    if doctor_types:
        for dt in doctor_types.split(","):
            dt = dt.strip()
            if dt in DOCTOR_TYPE_KEYWORDS:
                queries.append(f"{DOCTOR_TYPE_KEYWORDS[dt]} doctor near me")
    
    # Default: search for hospitals
    if not queries:
        queries = ["hospital near me"]
    
    all_places = []
    seen_place_ids = set()
    
    for query in queries:
        places = await search_places_new_api(query, latitude, longitude, radius)
        
        for place in places:
            place_id = place.get("id")
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)
            
            # Get location
            location = place.get("location", {})
            place_lat = location.get("latitude", 0)
            place_lng = location.get("longitude", 0)
            
            # Calculate straight-line distance for filtering
            distance_km = haversine_distance(latitude, longitude, place_lat, place_lng)
            
            # Filter by radius (using straight-line for initial filter)
            if distance_km > (radius / 1000):
                continue
            
            # Get road distance using Distance Matrix API
            road_distance = await get_road_distance(latitude, longitude, place_lat, place_lng)
            
            if road_distance:
                distance_text = road_distance["distance_text"]
                distance_meters = road_distance["distance_meters"]
                duration_text = road_distance["duration_text"]
            else:
                # Fallback to straight-line distance
                distance_text = f"{distance_km:.1f} km"
                distance_meters = int(distance_km * 1000)
                duration_text = None
            
            # Get opening hours
            current_hours = place.get("currentOpeningHours", {})
            regular_hours = place.get("regularOpeningHours", {})
            
            all_places.append({
                "place_id": place_id,
                "name": place.get("displayName", {}).get("text", "Unknown"),
                "address": place.get("formattedAddress", ""),
                "rating": place.get("rating"),
                "user_ratings_total": place.get("userRatingCount", 0),
                "phone": place.get("nationalPhoneNumber"),
                "website": place.get("websiteUri"),
                "opening_hours": current_hours.get("weekdayDescriptions", []),
                "open_now": current_hours.get("openNow"),
                "next_open_close": current_hours.get("nextOpenTime") or current_hours.get("nextCloseTime"),
                "regular_hours": regular_hours.get("periods", []),
                "distance_text": distance_text,
                "distance_meters": distance_meters,
                "location": {
                    "lat": place_lat,
                    "lng": place_lng
                },
                "google_maps_url": place.get("googleMapsUri", f"https://www.google.com/maps/place/?q=place_id:{place_id}")
            })
    
    # Sort by distance (nearest first)
    all_places.sort(key=lambda x: x.get("distance_meters") or float('inf'))
    
    return {
        "status": "success",
        "count": len(all_places),
        "places": all_places
    }
