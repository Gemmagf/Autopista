import streamlit as st
import requests
import polyline
import math

# --------- CONFIG ---------
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# --------- FUNCTIONS ---------

def get_route(origin, destination):
    """Get the polyline route between origin and destination"""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if data['status'] == 'OK':
        return data['routes'][0]['overview_polyline']['points']
    else:
        st.error("Failed to fetch route.")
        return None

def find_gas_stations_along_route(encoded_polyline):
    """Find gas stations along the route"""
    points = polyline.decode(encoded_polyline)
    gas_stations = []

    # Sample points every 20th point to not exceed API limit
    sample_points = points[::20]

    for lat, lng in sample_points:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=2000&type=gas_station&key={GOOGLE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data['status'] == 'OK':
            for place in data['results']:
                gas_stations.append({
                    'name': place['name'],
                    'location': (place['geometry']['location']['lat'], place['geometry']['location']['lng']),
                    'rating': place.get('rating', 'N/A'),
                    'address': place.get('vicinity', 'No address available')
                })

    # Remove duplicates based on name
    unique_stations = {station['name']: station for station in gas_stations}
    return list(unique_stations.values())

def haversine(coord1, coord2):
    """Calculate the distance between two (lat, lon) coordinates"""
    R = 6371  # Earth radius in km
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# --------- STREAMLIT APP ---------

st.title("Gas Stations Along Your Route")

origin = st.text_input("Enter your starting point:")
destination = st.text_input("Enter your destination:")

if st.button("Find Gas Stations"):
    if not origin or not destination:
        st.warning("Please enter both origin and destination.")
    else:
        encoded_polyline = get_route(origin, destination)
        if encoded_polyline:
            gas_stations = find_gas_stations_along_route(encoded_polyline)

            if gas_stations:
                st.success(f"Found {len(gas_stations)} gas stations along your route.")
                last_location = None

                for idx, station in enumerate(gas_stations):
                    st.subheader(f"{idx+1}. {station['name']}")
                    st.write(f"Address: {station['address']}")
                    st.write(f"Rating: {station['rating']}")

                    if last_location:
                        distance = haversine(last_location, station['location'])
                        st.write(f"Distance from previous: {distance:.1f} km")
                    else:
                        st.write("First station on the route.")

                    # Placeholder for chargers, LPG, restaurant
                    st.write("Chargers: (info not available from Google)")
                    st.write("LPG Price: (info not available)")
                    st.write("Restaurant: (info inferred from nearby POIs if needed)")

                    last_location = station['location']
            else:
                st.warning("No gas stations found along the route.")
