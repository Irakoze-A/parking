# Binary Image Converter API

This is a simple Flask API that converts uploaded images to binary (black and white) format.

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the Flask application:

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Usage

### Convert Image to Binary

**Endpoint:** `POST /convert`

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body parameter: `image` (file)

**Response:**

- A PNG image file containing the binary version of the input image

**Example using cURL:**

```bash
curl -X POST -F "image=@path/to/your/image.jpg" http://localhost:5000/convert --output binary_image.png
```

**Example using Python requests:**

```python
import requests

url = 'http://localhost:5000/convert'
files = {'image': open('path/to/your/image.jpg', 'rb')}
response = requests.post(url, files=files)

with open('binary_image.png', 'wb') as f:
    f.write(response.content)
```

## Error Handling

The API will return appropriate error messages if:

- No image is provided
- The provided file is not a valid image
- Any other error occurs during processing
