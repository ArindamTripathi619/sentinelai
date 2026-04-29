# SentinelAI — IP Geolocation Wrapper
# Owner: Parthiv
# Uses ip-api.com (free, no API key required for HTTP)
# Called by Atul's login endpoint for geo drift detection

import httpx
import os
from dataclasses import dataclass
from typing import Optional

GEO_API_URL = os.getenv("GEO_API_URL", "http://ip-api.com/json")
LOCAL_MOCK_COUNTRY = os.getenv("GEO_LOCAL_MOCK_COUNTRY", "India")

# IPs that are local/private — can't be geolocated
PRIVATE_IP_PREFIXES = ("127.", "192.168.", "10.", "172.16.", "::1", "localhost")


@dataclass
class GeoLocation:
    ip: str
    country: str
    city: str
    lat: float
    lon: float
    isp: str
    is_mock: bool = False


def is_private_ip(ip: str) -> bool:
    return any(ip.startswith(prefix) for prefix in PRIVATE_IP_PREFIXES)


def get_location(ip: str) -> Optional[GeoLocation]:
    """
    Get geographic location for an IP address.
    Returns a mock location for private/local IPs (for dev/demo use).
    Returns None if the API call fails.
    """
    # During local development, IPs will be 127.0.0.1 — mock them
    if is_private_ip(ip):
        return GeoLocation(
            ip=ip,
            country=LOCAL_MOCK_COUNTRY,
            city="Local",
            lat=20.5937,
            lon=78.9629,
            isp="Local Network",
            is_mock=True,
        )

    try:
        response = httpx.get(f"{GEO_API_URL}/{ip}", timeout=3.0)
        data = response.json()

        if data.get("status") != "success":
            return None

        return GeoLocation(
            ip=ip,
            country=data.get("country", "Unknown"),
            city=data.get("city", "Unknown"),
            lat=data.get("lat", 0.0),
            lon=data.get("lon", 0.0),
            isp=data.get("isp", "Unknown"),
        )

    except Exception as e:
        print(f"[geo.py] Failed to geolocate {ip}: {e}")
        return None


def get_country(ip: str) -> str:
    """
    Convenience method — returns just the country name string.
    Returns "Unknown" on failure.
    """
    loc = get_location(ip)
    return loc.country if loc else "Unknown"


if __name__ == "__main__":
    # Quick test — run: python geo.py
    test_ips = [
        "8.8.8.8",        # Google DNS — should be USA
        "85.208.96.1",    # Should be Germany (used in demo attack script)
        "127.0.0.1",      # Local — should return mock
    ]
    for ip in test_ips:
        loc = get_location(ip)
        if loc:
            print(f"{ip:20} → {loc.country}, {loc.city} {'[MOCK]' if loc.is_mock else ''}")
        else:
            print(f"{ip:20} → Failed to geolocate")
