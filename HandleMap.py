import overpy
import folium
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
from shapely.geometry import LineString
from datetime import datetime
from google.colab import files

@dataclass
class StreetParking:
    name: str
    coordinates: List[Tuple[float, float]]
    street_type: str
    parking_data: Dict
    estimated_capacity: int

class SimpleParkingMapper:
    def __init__(self):
        self.osm_api = overpy.Overpass()

        # Updated coordinates for the target area
        self.area_bounds = {
            'min_lat': 40.9916649,  # South
            'max_lat': 41.027953,   # North
            'min_lon': 28.8059569,  # West
            'max_lon': 28.8857606   # East
        }

    def collect_streets(self):
        """Collect street data from OpenStreetMap."""
        query = f"""
            [out:json];
            (
                way["highway"]
                    ({self.area_bounds['min_lat']},{self.area_bounds['min_lon']},
                     {self.area_bounds['max_lat']},{self.area_bounds['max_lon']});
            );
            out body;
            >;
            out skel qt;
        """

        try:
            result = self.osm_api.query(query)
            streets = []

            for way in result.ways:
                if 'highway' in way.tags:
                    street = self.process_street(way)
                    if street:
                        streets.append(street)

            return streets

        except Exception as e:
            print(f"Error: {e}")
            return []

    def process_street(self, way):
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
                    'fee': way.tags.get('parking:fee', 'no')
                }
            }

            # Calculate parking capacity
            street_line = LineString([(lon, lat) for lat, lon in coords])
            length_meters = street_line.length * 111000  # Convert to meters
            spots = int(length_meters / 6)  # Assume 5 meters per car

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

    def create_map(self, streets):
        """Create a simple map visualization."""
        # Center the map
        center_lat = (self.area_bounds['min_lat'] + self.area_bounds['max_lat']) / 2
        center_lon = (self.area_bounds['min_lon'] + self.area_bounds['max_lon']) / 2

        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

        # Add streets to map
        for street in streets:
            popup = f"""
                <b>{street.name}</b><br>
                Type: {street.street_type}<br>
                Estimated Parking: {street.estimated_capacity} cars<br>
                Parking Side: {street.parking_data['parking_side']}<br>
                {'Paid Parking' if street.parking_data['restrictions']['fee'] == 'yes' else 'Free Parking'}
            """

            folium.PolyLine(
                locations=street.coordinates,
                popup=folium.Popup(popup, max_width=300),
                color='blue',
                weight=3
            ).add_to(m)

        return m

    def export_to_json(self, streets, filename=None):
        """Export street and parking data to a JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Bahcelievler_parking_data.json"

        # Convert data to JSON-serializable format
        streets_data = {
            "metadata": {
                "total_streets": len(streets),
                "total_capacity": sum(street.estimated_capacity for street in streets),
                "area_bounds": self.area_bounds,
                "timestamp": datetime.now().isoformat()
            },
            "streets": [asdict(street) for street in streets]
        }

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(streets_data, f, indent=2, ensure_ascii=False)

        return filename