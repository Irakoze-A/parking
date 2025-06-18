import os
import json
import folium
from folium.plugins import Fullscreen
from shapely.geometry import LineString
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, asdict
import branca.colormap as cm
import overpy
from datetime import datetime

@dataclass
class StreetParking:
    name: str
    coordinates: List[Tuple[float, float]]
    street_type: str
    parking_data: Dict
    estimated_capacity: int

class ParkingMapViewer:
    def __init__(self, region_name: Optional[str] = None, bounds: Optional[Dict[str, float]] = None):
        self.osm_api = overpy.Overpass()
        self.bounds = bounds
        self.streets: List[StreetParking] = []
        self.map = None

    def collect_streets(self):
        """Collect street data from OpenStreetMap."""
        if not self.bounds:
            raise ValueError("Bounds must be set before collecting streets")

        try:
            query = f"""
                [out:json];
                (
                    way["highway"]
                        ({self.bounds['min_lat']},{self.bounds['min_lon']},
                         {self.bounds['max_lat']},{self.bounds['max_lon']});
                );
                out body;
                >;
                out skel qt;
            """

            result = self.osm_api.query(query)
            self.streets = []

            for way in result.ways:
                if 'highway' in way.tags:
                    street = self.process_street(way)
                    if street:
                        self.streets.append(street)

        except Exception as e:
            raise Exception(f"Error collecting streets: {str(e)}")

    def process_street(self, way) -> Optional[StreetParking]:
        """Process each street."""
        try:
            name = way.tags.get('name', 'Unknown Street')
            coords = [(float(node.lat), float(node.lon)) for node in way.nodes]

            # Basic parking data
            parking_data = {
                'street_type': way.tags.get('highway', 'unknown'),
                'parking_side': way.tags.get('parking:side', 'both'),
                'surface': way.tags.get('surface', 'unknown'),
                'restrictions': {
                    'fee': way.tags.get('parking:fee', 'no'),
                    'time': way.tags.get('parking:time', None),
                    'maxstay': way.tags.get('parking:maxstay', None)
                }
            }

            # Calculate parking capacity
            street_line = LineString([(lon, lat) for lat, lon in coords])
            length_meters = street_line.length * 111000  # Convert to meters
            spots = int(length_meters / 6)  # Assume 6 meters per car

            if parking_data['parking_side'] == 'both':
                spots *= 2

            return StreetParking(
                name=name,
                coordinates=coords,
                street_type=parking_data['street_type'],
                parking_data=parking_data,
                estimated_capacity=spots
            )

        except Exception as e:
            print(f"Error processing street: {e}")
            return None

    def create_map(self, zoom_start: int = 15, color_by_capacity: bool = True, satellite: bool = True):
        b = self.bounds
        center_lat = (b['min_lat'] + b['max_lat']) / 2
        center_lon = (b['min_lon'] + b['max_lon']) / 2
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}' if satellite else 'OpenStreetMap'
        attr = 'Esri, DigitalGlobe, GeoEye, i-cubed, USDA FSA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community' if satellite else None
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start, tiles=tiles, attr=attr)
        folium.TileLayer('OpenStreetMap').add_to(m)
        folium.TileLayer('CartoDB positron').add_to(m)
        folium.LayerControl().add_to(m)
        Fullscreen().add_to(m)
        
        color_palette = ['red', 'yellow', 'green']
        colormap = cm.LinearColormap(colors=color_palette, vmin=0, vmax=1)
        
        for street in self.streets:
            if not street.coordinates:
                continue
            popup_content = f"""
            <b>{street.name if street.name != 'Unknown Street' else 'Parking Area'}</b><br>
            Type: {street.street_type}<br>
            Estimated Capacity: {street.estimated_capacity} cars<br>
            Parking Side: {street.parking_data.get('parking_side', 'N/A')}<br>
            Fee: {'Yes' if street.parking_data.get('restrictions', {}).get('fee') == 'yes' else 'No'}<br>
            Time Restrictions: {street.parking_data.get('restrictions', {}).get('time', 'None')}<br>
            Max Stay: {street.parking_data.get('restrictions', {}).get('maxstay', 'None')}
            """
            color = colormap(min(1, street.estimated_capacity / 50.0)) if color_by_capacity else 'blue'
            locations = street.coordinates
            if locations and isinstance(locations[0], list):
                locations = [tuple(c) for c in locations]
            folium.PolyLine(
                locations=locations,
                popup=folium.Popup(popup_content, max_width=300),
                color=color,
                weight=4,
                opacity=0.7
            ).add_to(m)
        self.map = m
        return m

    def save_html(self, output_path: str = 'parking_map.html'):
        if self.map is None:
            raise RuntimeError("Map has not been created yet. Call create_map() first.")
        self.map.save(output_path)
        print(f"Map saved to {output_path}")

    def create_map_from_coordinates(self, lat: float, lng: float, delta: float, output_path: str):
        """Create and save a map from coordinates and delta."""
        # Calculate bounds
        bounds = {
            'min_lat': lat - delta,
            'max_lat': lat + delta,
            'min_lon': lng - delta,
            'max_lon': lng + delta
        }
        
        # Initialize with bounds
        self.bounds = bounds
        
        # Generate the map
        self.collect_streets()
        self.create_map()
        self.save_html(output_path)

if __name__ == "__main__":
    # Example usage with region name
    region = "Bahçelievler, Istanbul, Turkey"
    viewer = ParkingMapViewer(region_name=region)
    viewer.collect_streets()
    viewer.create_map()
    viewer.save_html("bahcelievler_parking_map.html")

    # Example usage with explicit bounds
    bounds = {
        'min_lat': 40.9916649,
        'max_lat': 41.027953,
        'min_lon': 28.8059569,
        'max_lon': 28.8857606
    }
    viewer2 = ParkingMapViewer(bounds=bounds)
    viewer2.collect_streets()
    viewer2.create_map()
    viewer2.save_html("bahcelievler_parking_map_bounds.html") 