"""Geography, climate and venue data for the prediction model.

All climate figures are real-world long-term averages (not from any video game):
- temp_jun: average June daytime high (deg C) in the country's main footballing city
- humidity: typical summer relative humidity class (0=dry, 1=moderate, 2=humid)
- alt: altitude (m) of the main national-team home venue
- lat/lon: capital / main city, used for travel-distance fatigue features

Used to model weather adaptation: a team from a cool, dry country playing a June
afternoon match in humid 35C Houston faces a measurable disadvantage; Mexico at
2,200 m Estadio Azteca punishes sea-level visitors, etc.
"""
import math

# team -> (lat, lon, temp_jun, humidity, alt)
COUNTRY = {
    "Algeria": (36.75, 3.06, 29, 0, 50), "Argentina": (-34.60, -58.38, 15, 1, 25),
    "Australia": (-33.87, 151.21, 18, 1, 20), "Austria": (48.21, 16.37, 24, 1, 170),
    "Belgium": (50.85, 4.35, 20, 1, 30), "Bosnia and Herzegovina": (43.86, 18.41, 25, 1, 550),
    "Brazil": (-23.55, -46.63, 23, 1, 760), "Canada": (43.65, -79.38, 24, 1, 80),
    "Cape Verde": (14.93, -23.51, 27, 2, 30), "Colombia": (4.71, -74.07, 19, 1, 2640),
    "Croatia": (45.81, 15.98, 25, 1, 120), "Curaçao": (12.11, -68.93, 31, 2, 5),
    "Czech Republic": (50.08, 14.44, 22, 1, 200), "DR Congo": (-4.44, 15.27, 29, 2, 280),
    "Ecuador": (-0.18, -78.47, 19, 1, 2850), "Egypt": (30.04, 31.24, 35, 0, 20),
    "England": (51.51, -0.13, 21, 1, 15), "France": (48.86, 2.35, 23, 1, 35),
    "Germany": (52.52, 13.41, 22, 1, 35), "Ghana": (5.60, -0.19, 29, 2, 40),
    "Haiti": (18.54, -72.34, 33, 2, 40), "Iran": (35.69, 51.39, 34, 0, 1190),
    "Iraq": (33.31, 44.36, 41, 0, 35), "Ivory Coast": (5.36, -4.01, 29, 2, 20),
    "Japan": (35.68, 139.69, 26, 2, 15), "Jordan": (31.95, 35.93, 31, 0, 800),
    "Mexico": (19.43, -99.13, 24, 1, 2240), "Morocco": (33.57, -7.59, 24, 1, 60),
    "Netherlands": (52.37, 4.90, 19, 1, 0), "New Zealand": (-36.85, 174.76, 15, 1, 25),
    "Norway": (59.91, 10.75, 19, 1, 25), "Panama": (8.98, -79.52, 31, 2, 10),
    "Paraguay": (-25.26, -57.58, 24, 1, 90), "Portugal": (38.72, -9.14, 26, 0, 100),
    "Qatar": (25.29, 51.53, 41, 2, 10), "Saudi Arabia": (24.71, 46.68, 42, 0, 610),
    "Scotland": (55.95, -3.19, 17, 1, 45), "Senegal": (14.72, -17.47, 29, 2, 20),
    "South Africa": (-26.20, 28.05, 17, 0, 1750), "South Korea": (37.57, 126.98, 27, 2, 40),
    "Spain": (40.42, -3.70, 30, 0, 660), "Sweden": (59.33, 18.07, 20, 1, 15),
    "Switzerland": (46.95, 7.45, 22, 1, 550), "Tunisia": (36.81, 10.18, 31, 0, 10),
    "Turkey": (41.01, 28.98, 27, 1, 40), "United States": (38.91, -77.04, 30, 2, 20),
    "Uruguay": (-34.90, -56.16, 15, 1, 40), "Uzbekistan": (41.30, 69.24, 33, 0, 450),
}

# 2026 World Cup venues: name -> (city, lat, lon, alt_m, roof, temp_jun_high, humidity)
VENUES = {
    "Estadio Azteca (Mexico City)": ("Mexico City", 19.30, -99.15, 2240, False, 24, 1),
    "Estadio Akron (Guadalajara)": ("Guadalajara", 20.68, -103.46, 1640, False, 30, 1),
    "Estadio BBVA (Monterrey)": ("Monterrey", 25.67, -100.24, 540, False, 34, 2),
    "Mercedes-Benz Stadium (Atlanta)": ("Atlanta", 33.76, -84.40, 300, True, 31, 2),
    "AT&T Stadium (Dallas)": ("Dallas", 32.75, -97.09, 180, True, 34, 1),
    "NRG Stadium (Houston)": ("Houston", 29.68, -95.41, 15, True, 33, 2),
    "SoFi Stadium (Los Angeles)": ("Los Angeles", 33.95, -118.34, 25, True, 26, 1),
    "Levi's Stadium (San Francisco)": ("Santa Clara", 37.40, -121.97, 5, False, 27, 0),
    "Lumen Field (Seattle)": ("Seattle", 47.60, -122.33, 5, False, 22, 1),
    "Arrowhead Stadium (Kansas City)": ("Kansas City", 39.05, -94.48, 265, False, 31, 2),
    "Gillette Stadium (Boston)": ("Foxborough", 42.09, -71.26, 90, False, 26, 1),
    "MetLife Stadium (New York/NJ)": ("East Rutherford", 40.81, -74.07, 2, False, 28, 2),
    "Lincoln Financial Field (Philadelphia)": ("Philadelphia", 39.90, -75.17, 10, False, 29, 2),
    "Hard Rock Stadium (Miami)": ("Miami Gardens", 25.96, -80.24, 3, False, 32, 2),
    "BC Place (Vancouver)": ("Vancouver", 49.28, -123.11, 5, True, 21, 1),
    "BMO Field (Toronto)": ("Toronto", 43.63, -79.42, 80, False, 25, 1),
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def climate_features(team, venue_lat, venue_lon, venue_temp, venue_hum, venue_alt, roof=False):
    """Mismatch between a team's home climate and the match conditions."""
    lat, lon, t_home, h_home, alt_home = COUNTRY.get(team, (45.0, 10.0, 24, 1, 100))
    eff_temp = venue_temp - (6 if roof else 0)  # roofed/air-conditioned venues blunt heat
    return {
        "heat_mismatch": max(0.0, eff_temp - t_home),       # only suffering in hotter-than-home
        "humidity_mismatch": max(0, venue_hum - h_home),
        "altitude_gap": max(0.0, (venue_alt - alt_home)) / 1000.0,
        "travel_km": haversine_km(lat, lon, venue_lat, venue_lon) / 1000.0,
    }
