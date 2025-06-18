from flask import Flask, request, send_file, send_from_directory
import cv2
import numpy as np
from PIL import Image
import io
import os
import socket

app = Flask(__name__, static_folder='static')

def get_local_ip():
    try:
        # Get the local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

@app.after_request
def add_security_headers(response):
    # Add basic security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/convert', methods=['POST'])
def convert_to_binary():
    try:
        # Get the image from the request
        if 'image' not in request.files:
            return {'error': 'No image provided'}, 400
        
        file = request.files['image']
        
        # Read the image using PIL
        img = Image.open(file.stream)
        
        # Convert PIL image to OpenCV format
        opencv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)
        
        # Convert to binary using threshold
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Convert back to PIL Image
        binary_pil = Image.fromarray(binary)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        binary_pil.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return send_file(
            img_byte_arr,
            mimetype='image/png'
        )
        
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    # Create static folder if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Get the local IP address
    local_ip = get_local_ip()
    port = 5000
    
    print(f"\n🌐 Server is running!")
    print(f"💻 Local access:     http://localhost:{port}")
    print(f"🔗 Network access:   http://{local_ip}:{port}")
    print("\nPress Ctrl+C to quit.\n")
    
    app.run(host='0.0.0.0', debug=True, port=port) 