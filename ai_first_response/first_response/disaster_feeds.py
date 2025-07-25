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
    try:
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
        
        # Check if response is successful
        if resp.status_code != 200:
            print(f"USGS API returned status code: {resp.status_code}")
            return []
        
        # Try to parse JSON
        data = resp.json()
        return data.get("features", [])
    except requests.exceptions.RequestException as e:
        print(f"USGS API request error: {e}")
        return []
    except ValueError as e:  # JSON decode error
        print(f"USGS API JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"USGS API unexpected error: {e}")
        return []


def gdacs_events(lat, lon, radius_km=50000):
    try:
        # Try the main GDACS API endpoint with geographic bounding box
        # Calculate bounding box based on radius (rough approximation: 1 degree ≈ 111 km)
        degree_radius = radius_km / 111.0
        min_lat = lat - degree_radius
        max_lat = lat + degree_radius
        min_lon = lon - degree_radius
        max_lon = lon + degree_radius
        
        # Try different GDACS API endpoints
        urls_to_try = [
            "https://www.gdacs.org/gdacsapi/api/events/geteventlist/MAP",
            "https://www.gdacs.org/gdacsapi/api/events",
            "https://www.gdacs.org/xml/gdacs.json"
        ]
        
        params = {
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "limit": 20,
            "alertlevel": "Red,Orange",
            "eventtype": "EQ,FL,TC,VO,WF"
        }
        
        # Try each URL until one works
        for url in urls_to_try:
            try:
                if "json" in url:
                    # For JSON endpoint, don't send bbox parameter
                    resp = requests.get(url, timeout=10)
                else:
                    resp = requests.get(url, params=params, timeout=10)
                
                if resp.status_code == 200:
                    break
            except:
                continue
        else:
            # If none of the URLs worked, use the last response for error reporting
            pass
        
        # Debug information
        print(f"GDACS API URL: {url}")
        if "json" not in url:
            print(f"GDACS API params: {params}")
        print(f"GDACS API response status: {resp.status_code}")
        
        # Check if response is successful
        if resp.status_code != 200:
            print(f"GDACS API returned status code: {resp.status_code}")
            print(f"Response text: {resp.text[:300]}...")
            # Only try RSS if we got a client error (not server error)
            if 400 <= resp.status_code < 500:
                return gdacs_events_from_rss(lat, lon, radius_km)
            return []
        
        # Check if response has content
        if not resp.text.strip():
            print("GDACS API returned empty response")
            return []
        
        print(f"GDACS API response length: {len(resp.text)}")
        print(f"GDACS API response preview: {resp.text[:200]}...")
        
        # Try to parse JSON
        data = resp.json()
        
        # Handle different response formats
        events = []
        if isinstance(data, dict):
            events = data.get("features", data.get("results", []))
        elif isinstance(data, list):
            events = data
        
        # Filter events by distance
        filtered_events = []
        for event in events[:5]:  # Limit to first 5 events
            try:
                # Try different possible field names for coordinates
                event_lat = None
                event_lon = None
                
                if 'geometry' in event and 'coordinates' in event['geometry']:
                    # GeoJSON format
                    coords = event['geometry']['coordinates']
                    event_lon, event_lat = float(coords[0]), float(coords[1])
                elif 'latitude' in event and 'longitude' in event:
                    # Direct lat/lon fields
                    event_lat = float(event['latitude'])
                    event_lon = float(event['longitude'])
                elif 'lat' in event and 'lon' in event:
                    # Alternative field names
                    event_lat = float(event['lat'])
                    event_lon = float(event['lon'])
                
                if event_lat is not None and event_lon is not None:
                    distance = _haversine_km(lat, lon, event_lat, event_lon)
                    if distance <= radius_km:
                        filtered_events.append(event)
                        
            except (ValueError, TypeError, KeyError):
                continue
                
        return filtered_events
        
    except requests.exceptions.RequestException as e:
        print(f"GDACS API request error: {e}")
        # Don't fall back to RSS if the API is down, just return empty
        return []
    except ValueError as e:  # JSON decode error
        print(f"GDACS API JSON decode error: {e}")
        print(f"Response content: {resp.text[:200]}...")
        # Try RSS only if we got a response but couldn't parse it
        return gdacs_events_from_rss(lat, lon, radius_km)
    except Exception as e:
        print(f"GDACS API unexpected error: {e}")
        return []


def gdacs_events_from_rss(lat, lon, radius_km=50):
    """Fallback method using GDACS RSS feed"""
    try:
        import xml.etree.ElementTree as ET
        
        url = "https://www.gdacs.org/xml/rss.xml"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            print(f"GDACS RSS feed returned status code: {resp.status_code}")
            return []
        
        # Remove BOM (Byte Order Mark) if present and clean the response
        response_text = resp.text
        if response_text.startswith('\ufeff'):
            response_text = response_text[1:]  # Remove BOM
        response_text = response_text.strip()
        
        # Check if response looks like XML
        if not response_text.startswith('<?xml') and not response_text.startswith('<'):
            print(f"GDACS RSS response doesn't look like XML: {response_text[:100]}...")
            return []
        
        # Parse RSS XML with error handling
        try:
            root = ET.fromstring(response_text)
        except ET.ParseError as e:
            print(f"GDACS RSS XML parse error: {e}")
            print(f"Response content: {response_text[:200]}...")
            return []
        
        events = []
        
        # Find all items in the RSS feed
        for item in root.findall(".//item")[:10]:  # Limit to first 10 items
            try:
                title = item.find("title")
                description = item.find("description")
                link = item.find("link")
                
                if title is not None:
                    title_text = title.text or ""
                    desc_text = description.text if description is not None else ""
                    link_text = link.text if link is not None else ""
                    
                    # Create basic event data
                    event_data = {
                        "title": title_text,
                        "description": desc_text,
                        "link": link_text,
                        "source": "gdacs_rss"
                    }
                    
                    # Try to extract coordinates from description or title
                    import re
                    
                    # Look for coordinates in various formats
                    coord_patterns = [
                        r'(\d+\.?\d*)[°\s]*[NS][,\s]*(\d+\.?\d*)[°\s]*[EW]',
                        r'lat[:\s]*(\d+\.?\d*)[,\s]*lon[:\s]*(\d+\.?\d*)',
                        r'(\d+\.?\d*)[,\s]+(\d+\.?\d*)'
                    ]
                    
                    event_lat = event_lon = None
                    text_to_search = f"{title_text} {desc_text}"
                    
                    for pattern in coord_patterns:
                        coord_match = re.search(pattern, text_to_search, re.IGNORECASE)
                        if coord_match:
                            try:
                                event_lat = float(coord_match.group(1))
                                event_lon = float(coord_match.group(2))
                                # Basic validation of coordinates
                                if -90 <= event_lat <= 90 and -180 <= event_lon <= 180:
                                    break
                                else:
                                    event_lat = event_lon = None
                            except ValueError:
                                continue
                    
                    if event_lat is not None and event_lon is not None:
                        distance = _haversine_km(lat, lon, event_lat, event_lon)
                        if distance <= radius_km:
                            event_data["latitude"] = event_lat
                            event_data["longitude"] = event_lon
                            event_data["distance_km"] = distance
                            events.append(event_data)
                    else:
                        # Include events without coordinates if they might be relevant
                        # This allows for manual review of potentially relevant events
                        if len(events) < 3:  # Only include a few without coordinates
                            events.append(event_data)
                            
            except Exception as e:
                print(f"Error parsing RSS item: {e}")
                continue
        
        return events
        
    except Exception as e:
        print(f"GDACS RSS fallback error: {e}")
        return []

