import requests
import datetime
import math


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))


def recent_quakes(lat, lon, radius_km=300, min_mag=3.0, minutes=60):
    now = datetime.datetime.utcnow()
    starttime = (now - datetime.timedelta(minutes=minutes)).isoformat()
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": radius_km,
        "minmagnitude": min_mag,
        "starttime": starttime,
    }
    resp = requests.get(url, params=params, timeout=5)
    data = resp.json()
    return data.get("features", [])


def gdacs_events(lat, lon, radius_km=500):
    url = "https://www.gdacs.org/gdacsapi/api/events"
    params = {"within": f"{lat},{lon},{radius_km}"}
    resp = requests.get(url, params=params, timeout=5)
    data = resp.json()
    return data.get("results", [])