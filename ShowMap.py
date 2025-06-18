import json
import folium
from folium.plugins import Fullscreen
from shapely.geometry import LineString
from typing import List, Tuple, Dict, Any
import branca.colormap as cm


# Define the data class (assuming it's the same as your previous code)
# You might want to load this from a separate utility file in a larger project
# For this script, we'll keep it inline for completeness
from dataclasses import dataclass

@dataclass
class StreetParking:
    name: str
    coordinates: List[Tuple[float, float]]
    street_type: str
    parking_data: Dict
    estimated_capacity: int

def load_parking_data(filepath='/content/Bahcelievler_parking_data.json') -> List[StreetParking]:
    """Loads street parking data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_data = json.load(f) # Load the entire top-level dictionary

        # --- FIX IS HERE: Access the 'streets' list ---
        data_to_process = full_data.get('streets', []) # Safely get the 'streets' list, default to empty list if not found
        if not data_to_process:
            print(f"Warning: No 'streets' array found in {filepath} or it's empty.")
            return []
        # --- END FIX ---

        streets = []
        for item in data_to_process: # Now 'item' will correctly be each street dictionary
            # Ensure coordinates are in (lat, lon) format for Folium
            # They should already be if processed correctly by your previous script
            if 'coordinates' not in item or not item['coordinates']:
                print(f"Warning: Skipping item with missing or empty coordinates: {item.get('name', 'Unnamed Item')}")
                continue # Skip items without coordinates

            # Handle cases where coordinates might be loaded as lists instead of tuples
            # This check is good practice, but they should ideally be tuples if already processed
            if isinstance(item['coordinates'][0], list):
                item['coordinates'] = [tuple(c) for c in item['coordinates']]

            # Defensive check for missing keys from your StreetParking dataclass
            # The .get() with a default value can help prevent KeyErrors if the source JSON is inconsistent
            streets.append(StreetParking(
                name=item.get('name', 'Unknown Street'),
                coordinates=item['coordinates'], # Coordinates are essential, handled by above check
                street_type=item.get('type', 'unknown'), # 'type' in JSON, 'street_type' in class
                parking_data=item.get('parking_data', {}),
                estimated_capacity=item.get('estimated_capacity', 0)
            ))
        print(f"Successfully loaded {len(streets)} street parking entries.")
        return streets
    except FileNotFoundError:
        print(f"Error: {filepath} not found. Please ensure you've run the data collection script.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Please check file content.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        return []


def create_verification_map(streets: List[StreetParking], center_lat: float, center_lon: float, zoom_start: int = 15):
    """
    Creates an interactive Folium map with satellite imagery for visual verification.
    Street segments are overlaid with popups containing parking details.
    """

    # Use Esri World Imagery for satellite view
    # You can also try 'OpenStreetMap' or 'CartoDB positron' as alternatives if needed
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri, DigitalGlobe, GeoEye, i-cubed, USDA FSA, USGS, AEX, Getmapping, Aerogrid, IGN, IGP, swisstopo, and the GIS User Community'
    )

    # Add a layer control to switch between map tiles if desired
    folium.TileLayer('OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB positron').add_to(m)
    folium.LayerControl().add_to(m)

    # Add Fullscreen button for easier viewing
    Fullscreen().add_to(m)

    for street in streets:
        if not street.coordinates:
            continue # Skip streets without coordinates

        popup_content = f"""
        <b>{street.name if street.name != 'Unknown Street' else 'Parking Area'}</b><br>
        Type: {street.street_type}<br>
        Estimated Capacity: {street.estimated_capacity} cars<br>
        Parking Side: {street.parking_data.get('parking_side', 'N/A')}<br>
        Fee: {'Yes' if street.parking_data.get('restrictions', {}).get('fee') == 'yes' else 'No'}<br>
        Time Restrictions: {street.parking_data.get('restrictions', {}).get('time', 'None')}<br>
        Max Stay: {street.parking_data.get('restrictions', {}).get('maxstay', 'None')}
        """

        color_intensity = min(1, street.estimated_capacity / 50.0) # Normalize for visual range
        # FIX: Explicitly create a LinearColormap with desired colors
        # For Red-Yellow-Green:
        color_palette = ['red', 'yellow', 'green']

        # If you prefer Yellow-Green-Blue (from previous option 1):
        # color_palette = ['yellow', 'lightgreen', 'blue']
        # (Note: 'lightgreen' and 'blue' for intermediate/high values, you can adjust these hex codes or names)

        color = cm.LinearColormap(colors=color_palette, vmin=0, vmax=1)
        # Apply the intensity to the colormap
        color = color(color_intensity)

        # Ensure coordinates are in (lat, lon) format for Folium PolyLine
        # They should already be if processed correctly by your previous script
        locations = street.coordinates
        if locations and isinstance(locations[0], list): # Defensive check
            locations = [tuple(c) for c in locations]

        folium.PolyLine(
            locations=locations,
            popup=folium.Popup(popup_content, max_width=300),
            color=color, # Using the color intensity
            weight=4,
            opacity=0.7
        ).add_to(m)

    return m

if __name__ == "__main__":
    json_filepath = '/content/Bahcelievler_parking_data.json'

    area_bounds = {
        'min_lat': 40.9916649,
        'max_lat': 41.027953,
        'min_lon': 28.8059569,
        'max_lon': 28.8857606
    }
    center_lat = (area_bounds['min_lat'] + area_bounds['max_lat']) / 2
    center_lon = (area_bounds['min_lon'] + area_bounds['max_lon']) / 2

    streets_data = load_parking_data(json_filepath)

    if streets_data:
        print("\nCreating verification map (this might take a moment)...")
        verification_map = create_verification_map(streets_data, center_lat, center_lon)

        # --- THIS IS THE KEY CHANGE FOR COLAB ---
        from IPython.display import display
        display(verification_map)
        # --- END OF KEY CHANGE ---

        print("\n--- Manual Verification Instructions ---")
        print("1. The interactive map is displayed above this text in the Colab output.")
        print("2. Zoom in on the blue/green/red lines representing street segments.")
        print("3. Use the satellite imagery background to visually inspect:")
        print("   - Are there clear curbs? Is parking physically possible here?")
        print("   - Are there painted parking lines or parked cars visible (indicating a parking area)?")
        print("   - Are there obvious 'No Parking' signs, bus stops, fire hydrants, or driveways that might not be captured by OSM tags, reducing actual capacity?")
        print("   - Does the estimated capacity make sense given the visible length and context?")
        print("4. Click on the lines for more details about the street segment.")
        print("5. Make notes on any segments that seem incorrect or suspicious.")
        print("---------------------------------------")

        # Optional: If you still want to save the HTML file and download it later
        # output_html_file = 'bahcelievler_parking_verification_map.html'
        # verification_map.save(output_html_file)
        # from google.colab import files
        # files.download(output_html_file)
        # print(f"Map also saved to {output_html_file} and offered for download.")

    else:
        print("No data loaded. Cannot create map for verification.")