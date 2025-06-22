from flask import Flask, request, jsonify, render_template, send_from_directory
import logging
import os
from ParkingMapViewer import ParkingMapViewer

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/previous_maps/<path:filename>')
def serve_map(filename):
    return send_from_directory('previous_maps', filename)

@app.route("/submit-coordinates", methods=["POST"])
def submit_coordinates():
    try:
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        lat = data.get("lat")
        lng = data.get("lng")
        delta = data.get("delta", 0.01)  # Default to 1km if not specified
        
        if lat is None or lng is None:
            logger.error("Missing coordinates in request")
            return jsonify({"error": "Missing coordinates"}), 400
        
        try:
            # Create a unique filename based on coordinates and timestamp
            filename = f"parking_map_{lat}_{lng}_{delta}.html"
            filepath = os.path.join('previous_maps', filename)
            
            logger.info(f"Generating map for coordinates: lat={lat}, lng={lng}, delta={delta}")
            
            # Calculate bounds
            bounds = {
                'min_lat': lat - delta,
                'max_lat': lat + delta,
                'min_lon': lng - delta,
                'max_lon': lng + delta
            }
            
            # Generate the map
            viewer = ParkingMapViewer(bounds=bounds)
            viewer.create_map_from_coordinates(lat, lng, delta, filepath)
            
            # Return the URL to access the map
            map_url = f"/previous_maps/{filename}"
            return jsonify({
                "lat": lat,
                "lng": lng,
                "delta": delta,
                "map_url": map_url
            })
        except Exception as e:
            logger.error(f"Error generating map: {str(e)}", exc_info=True)
            return jsonify({"error": f"Error generating map: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in submit_coordinates: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    # Ensure the previous_maps directory exists
    os.makedirs('previous_maps', exist_ok=True)
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False) 