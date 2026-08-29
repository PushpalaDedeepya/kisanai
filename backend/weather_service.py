import requests
import re
from typing import Dict, Any, Optional, Tuple
from config import OPENWEATHER_API_KEY

# Open-Meteo Weather Codes Mapping (WMO Code -> Description)
WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    71: "Slight Snow Fall",
    73: "Moderate Snow Fall",
    75: "Heavy Snow Fall",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail"
}

# Well-known Indian city / district fallback coordinates
INDIAN_LOCATIONS = {
    "hyderabad": (17.3850, 78.4867, "Hyderabad, Telangana"),
    "guntur": (16.3067, 80.4365, "Guntur, Andhra Pradesh"),
    "vijayawada": (16.5062, 80.6480, "Vijayawada, Andhra Pradesh"),
    "warangal": (17.9689, 79.5941, "Warangal, Telangana"),
    "bengaluru": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "bangalore": (12.9716, 77.5946, "Bengaluru, Karnataka"),
    "chennai": (13.0827, 80.2707, "Chennai, Tamil Nadu"),
    "pune": (18.5204, 73.8567, "Pune, Maharashtra"),
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra"),
    "delhi": (28.6139, 77.2090, "New Delhi, Delhi"),
    "new delhi": (28.6139, 77.2090, "New Delhi, Delhi"),
    "ludhiana": (30.9010, 75.8573, "Ludhiana, Punjab"),
    "lucknow": (26.8467, 80.9462, "Lucknow, Uttar Pradesh"),
    "varanasi": (25.3176, 82.9739, "Varanasi, Uttar Pradesh"),
    "patna": (25.5941, 85.1376, "Patna, Bihar"),
    "kolkata": (22.5726, 88.3639, "Kolkata, West Bengal"),
    "nagpur": (21.1458, 79.0882, "Nagpur, Maharashtra"),
    "jaipur": (26.9124, 75.7873, "Jaipur, Rajasthan"),
    "ahmedabad": (23.0225, 72.5714, "Ahmedabad, Gujarat"),
    "coimbatore": (11.0168, 76.9558, "Coimbatore, Tamil Nadu")
}


def geocode_location(location_str: str) -> Optional[Tuple[float, float, str]]:
    """Resolve location string or coordinates into (lat, lon, display_name)."""
    if not location_str or not location_str.strip():
        return None

    loc = location_str.strip()

    # Check if input is "lat, lon" numbers
    coord_match = re.match(r"^(-?\d+(\.\d+)?),\s*(-?\d+(\.\d+)?)$", loc)
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(3))
        # Reverse geocode coordinates to get actual city / district name
        try:
            rev_url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10"
            rev_res = requests.get(rev_url, headers={"User-Agent": "KisanAI/2.0"}, timeout=3)
            if rev_res.status_code == 200:
                rev_data = rev_res.json()
                addr = rev_data.get("address", {})
                place = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or addr.get("district") or "Current Location"
                state = addr.get("state") or addr.get("country", "")
                full_name = f"{place}, {state}".strip(", ")
                return lat, lon, full_name
        except Exception as e:
            print(f"Reverse geocode lookup error: {e}")
        return lat, lon, f"{lat:.2f}, {lon:.2f}"

    # Check known cache
    loc_lower = loc.lower()
    for key, (lat, lon, name) in INDIAN_LOCATIONS.items():
        if key in loc_lower or loc_lower in key:
            return lat, lon, name

    # Try Open-Meteo Geocoding API (free, no API key needed)
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(loc)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", [])
            if results:
                top = results[0]
                lat = top.get("latitude")
                lon = top.get("longitude")
                name = f"{top.get('name')}, {top.get('admin1', '')} {top.get('country', '')}".strip(", ")
                return lat, lon, name
    except Exception as e:
        print(f"Geocoding lookup error: {e}")

    # Fallback to Hyderabad coordinates as safe default center
    return 17.3850, 78.4867, location_str


def get_weather_from_open_meteo(lat: float, lon: float, location_name: str) -> Dict[str, Any]:
    """Fetch live weather and 5-day forecast from Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m&"
        f"hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m&"
        f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&"
        f"timezone=auto&forecast_days=5"
    )

    res = requests.get(url, timeout=5)
    if res.status_code != 200:
        raise Exception(f"Open-Meteo returned status {res.status_code}")

    data = res.json()
    curr = data.get("current", {})
    daily = data.get("daily", {})
    hourly = data.get("hourly", {})

    weather_code = curr.get("weather_code", 0)
    condition_desc = WMO_WEATHER_CODES.get(weather_code, "Clear")

    temp_c = curr.get("temperature_2m", 28.0)
    feels_like_c = curr.get("apparent_temperature", temp_c)
    humidity_pct = curr.get("relative_humidity_2m", 60)
    wind_kmh = curr.get("wind_speed_10m", 8.0)
    wind_dir = curr.get("wind_direction_10m", 0)
    precip_mm = curr.get("precipitation", 0.0)

    # 24-hour max rain probability
    rain_prob_24h = 0
    if hourly.get("precipitation_probability"):
        rain_prob_24h = max(hourly["precipitation_probability"][:24]) if len(hourly["precipitation_probability"]) >= 24 else 0
    elif daily.get("precipitation_probability_max"):
        rain_prob_24h = daily["precipitation_probability_max"][0]

    # Daily forecast summary
    forecast_days = []
    times = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    daily_codes = daily.get("weather_code", [])
    daily_probs = daily.get("precipitation_probability_max", [])

    for i in range(min(5, len(times))):
        d_code = daily_codes[i] if i < len(daily_codes) else 0
        forecast_days.append({
            "date": times[i],
            "max_temp_c": max_temps[i] if i < len(max_temps) else temp_c,
            "min_temp_c": min_temps[i] if i < len(min_temps) else temp_c - 6,
            "condition": WMO_WEATHER_CODES.get(d_code, "Clear"),
            "rain_probability": daily_probs[i] if i < len(daily_probs) else 0
        })

    # Compute Agricultural Advisories
    advisory = compute_agricultural_advisories(
        temp_c=temp_c,
        humidity_pct=humidity_pct,
        rain_prob=rain_prob_24h,
        wind_kmh=wind_kmh,
        condition=condition_desc
    )

    return {
        "location": location_name,
        "latitude": lat,
        "longitude": lon,
        "temperature_c": round(temp_c, 1),
        "feels_like_c": round(feels_like_c, 1),
        "condition": condition_desc,
        "humidity_pct": int(humidity_pct),
        "wind_speed_kmh": round(wind_kmh, 1),
        "wind_direction_deg": int(wind_dir),
        "precipitation_mm": float(precip_mm),
        "rain_probability_pct": int(rain_prob_24h),
        "forecast": forecast_days,
        "agricultural_advisory": advisory,
        "source": "Open-Meteo (Live Global Meteorological Model)"
    }


def compute_agricultural_advisories(temp_c: float, humidity_pct: int, rain_prob: int, wind_kmh: float, condition: str) -> Dict[str, Any]:
    """Generates actionable agricultural guidance based on live atmospheric conditions."""
    # Spraying Feasibility
    if rain_prob >= 50:
        spraying_status = "NOT RECOMMENDED (High Rain Risk)"
        spraying_advice = f"🌧️ Rain probability is {rain_prob}%. Chemical sprays will likely be washed off. Postpone pesticide spraying until dry weather."
    elif wind_kmh >= 15.0:
        spraying_status = "NOT RECOMMENDED (High Wind Drift)"
        spraying_advice = f"💨 Wind speed is {wind_kmh} km/h. High winds cause significant chemical drift and wastage. Spray only when winds subside (<10 km/h)."
    else:
        spraying_status = "SUITABLE"
        spraying_advice = "✅ Wind and rainfall conditions are favorable for spraying. Prefer early morning or late evening."

    # Irrigation Feasibility
    if rain_prob >= 60:
        irrigation_advice = f"🌧️ High chance of rain ({rain_prob}%). Hold off on irrigation to avoid field waterlogging and save electricity."
    elif temp_c > 36.0:
        irrigation_advice = f"🌡️ High temperature ({temp_c}°C). Crops may experience heat stress. Maintain light, frequent irrigation during evening/early morning."
    else:
        irrigation_advice = "💧 Normal irrigation schedule based on soil moisture and crop growth stage."

    # Disease Vulnerability
    disease_warnings = []
    if humidity_pct >= 75 and 20.0 <= temp_c <= 32.0:
        disease_warnings.append("High humidity and warm temperatures elevate risk of fungal leaf spots, blights, and downy mildews. Inspect crop foliage regularly.")
    if "Rain" in condition or rain_prob >= 50:
        disease_warnings.append("Excess surface moisture promotes bacterial and damping-off infections in vegetable nurseries.")

    return {
        "spraying_status": spraying_status,
        "spraying_advice": spraying_advice,
        "irrigation_advice": irrigation_advice,
        "disease_risk_warnings": disease_warnings
    }


def get_weather(location_str: str = "") -> str:
    """
    Returns a clean formatted text summary of current weather and agricultural advisory
    suitable for prompt injection or display.
    """
    if not location_str:
        return "Location not provided. Weather context unavailable."

    try:
        geo = geocode_location(location_str)
        if not geo:
            return f"Weather data currently unavailable for '{location_str}'."

        lat, lon, name = geo
        w_data = get_weather_from_open_meteo(lat, lon, name)

        advisory = w_data["agricultural_advisory"]
        summary = (
            f"Location: {w_data['location']}\n"
            f"Current Conditions: {w_data['temperature_c']}°C, {w_data['condition']}, "
            f"Humidity: {w_data['humidity_pct']}%, Wind: {w_data['wind_speed_kmh']} km/h, "
            f"24h Rain Chance: {w_data['rain_probability_pct']}%\n"
            f"Agricultural Advisory:\n"
            f"• Spraying: {advisory['spraying_advice']}\n"
            f"• Irrigation: {advisory['irrigation_advice']}"
        )
        if advisory["disease_risk_warnings"]:
            summary += "\n• Disease Risk: " + " ".join(advisory["disease_risk_warnings"])

        return summary
    except Exception as e:
        print(f"Weather fetch failed: {e}")
        return f"Live weather temporarily unavailable for '{location_str}'."


def get_weather_json(location_str: str = "") -> Dict[str, Any]:
    """Returns structured JSON weather data for frontend widgets."""
    if not location_str:
        location_str = "Hyderabad"

    try:
        geo = geocode_location(location_str)
        if not geo:
            raise Exception("Location could not be resolved")

        lat, lon, name = geo
        return get_weather_from_open_meteo(lat, lon, name)
    except Exception as e:
        # Graceful fallback response
        return {
            "location": location_str,
            "temperature_c": 28.0,
            "feels_like_c": 29.0,
            "condition": "Partly Cloudy",
            "humidity_pct": 65,
            "wind_speed_kmh": 10.0,
            "wind_direction_deg": 180,
            "precipitation_mm": 0.0,
            "rain_probability_pct": 20,
            "forecast": [],
            "agricultural_advisory": {
                "spraying_status": "MODERATE",
                "spraying_advice": "Check local sky conditions before spraying.",
                "irrigation_advice": "Maintain normal irrigation based on soil moisture.",
                "disease_risk_warnings": []
            },
            "source": "Fallback Offline Weather Engine",
            "offline_notice": f"Live weather API connection failed ({str(e)}). Displaying standard seasonal guidance."
        }
