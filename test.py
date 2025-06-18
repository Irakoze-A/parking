import requests
import folium
from folium import plugins
import os
from dotenv import load_dotenv
import json
import numpy as np
from PIL import Image
import io
import cv2

# Load environment variables
load_dotenv()

class ParkingSpotAnalyzer:
    def __init__(self):
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.google_api_key:
            raise ValueError("Google Maps API key not found in environment variables")

    def get_satellite_image(self, latitude, longitude, zoom=20):
        """Get satellite image from Google Maps API"""
        url = f"https://maps.googleapis.com/maps/api/staticmap"
        params = {
            'center': f"{latitude},{longitude}",
            'zoom': zoom,
            'size': '640x640',
            'maptype': 'satellite',
            'key': self.google_api_key
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            raise Exception(f"Failed to get satellite image: {response.text}")

    def get_street_data(self, latitude, longitude, radius=100):
        """Get street data from OpenStreetMap using Overpass API"""
        query = f"""
        [out:json][timeout:25];
        (
          way["highway"](around:{radius},{latitude},{longitude});
          relation["highway"](around:{radius},{latitude},{longitude});
        );
        out body;
        >;
        out skel qt;
        """
        
        response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get street data: {response.text}")

    def analyze_parking_spots(self, latitude, longitude):
        """Analyze parking spots in the given location"""
        try:
            # Get satellite image
            satellite_img = self.get_satellite_image(latitude, longitude)
            
            # Convert to OpenCV format
            opencv_img = cv2.cvtColor(np.array(satellite_img), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)
            
            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter potential parking spots based on area and shape
            parking_spots = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 100 < area < 1000:  # Adjust these thresholds based on your needs
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = float(w)/h
                    if 0.5 < aspect_ratio < 2.0:  # Typical parking spot aspect ratio
                        parking_spots.append((x, y, w, h))
            
            # Get street data
            street_data = self.get_street_data(latitude, longitude)
            
            # Create a map visualization
            m = folium.Map(location=[latitude, longitude], zoom_start=20)
            
            # Add satellite layer
            folium.TileLayer(
                tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr='Esri',
                name='Satellite'
            ).add_to(m)
            
            # Add parking spots to map
            for spot in parking_spots:
                x, y, w, h = spot
                # Convert pixel coordinates to lat/lon (approximate)
                lat_offset = (h/640) * 0.0001  # Adjust based on zoom level
                lon_offset = (w/640) * 0.0001
                folium.Rectangle(
                    bounds=[[latitude - lat_offset, longitude - lon_offset],
                           [latitude + lat_offset, longitude + lon_offset]],
                    color='red',
                    fill=True,
                    popup='Potential Parking Spot'
                ).add_to(m)
            
            # Save the map
            map_path = 'parking_analysis.html'
            m.save(map_path)
            
            return {
                'parking_spots_count': len(parking_spots),
                'map_path': map_path,
                'street_data': street_data
            }
            
        except Exception as e:
            raise Exception(f"Error analyzing parking spots: {str(e)}")

def main():
    # Example coordinates (New York City)
    latitude = 40.7128
    longitude = -74.0060
    
    try:
        analyzer = ParkingSpotAnalyzer()
        results = analyzer.analyze_parking_spots(latitude, longitude)
        print(f"Found {results['parking_spots_count']} potential parking spots")
        print(f"Map saved to {results['map_path']}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 