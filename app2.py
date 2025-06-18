from flask import Flask, request, render_template, jsonify, url_for
import logging
import os
from ParkingMapViewer import ParkingMapViewer

app = Flask(__name__, static_folder='static')

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return app.send_static_file('index2.html')

@app.route('/submit-coordinates', methods=['POST'])
def submit_coordinates():
    data = request.get_json()
    lat = float(data.get('lat'))
    lng = float(data.get('lng'))
    delta = float(data.get('delta', 0.01))
    app.logger.info(f"Received coordinates: lat={lat}, lng={lng}, delta={delta}")
    # Calculate a bounding box around the point
    bounds = {
        'min_lat': lat - delta,
        'max_lat': lat + delta,
        'min_lon': lng - delta,
        'max_lon': lng + delta
    }
    # Generate the parking map
    output_filename = f"parking_map_{lat:.5f}_{lng:.5f}_d{delta:.3f}.html"
    output_path = os.path.join(app.static_folder, output_filename)
    viewer = ParkingMapViewer(bounds=bounds)
    viewer.collect_streets()
    viewer.create_map()
    viewer.save_html(output_path)
    map_url = url_for('static', filename=output_filename)
    return jsonify({'status': 'success', 'lat': lat, 'lng': lng, 'map_url': map_url})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 