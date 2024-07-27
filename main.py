import subprocess
import os
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import numpy as np
from io import BytesIO
from PIL import Image
import requests

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    'https://mission-tomato.pages.dev'
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TensorFlow Serving endpoint
TF_SERVING_ENDPOINT = 'http://localhost:5000/v1/models/tomato_model:predict'

# Class names for predictions
CLASS_NAMES = [
    'Tomato_Bacterial_spot',
    'Tomato_Early_blight',
    'Tomato_Late_blight',
    'Tomato_Leaf_Mold',
    'Tomato_Septoria_leaf_spot',
    'Tomato_Spider_mites_Two_spotted_spider_mite',
    'Tomato__Target_Spot',
    'Tomato__Tomato_YellowLeaf__Curl_Virus',
    'Tomato__Tomato_mosaic_virus',
    'Tomato_healthy'
]

def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        image = read_file_as_image(await file.read())
        img_batch = np.expand_dims(image, 0).astype(np.float32)

        # Prepare JSON data for TensorFlow Serving
        json_data = {'instances': img_batch.tolist()}

        # Send POST request to TensorFlow Serving endpoint
        response = requests.post(TF_SERVING_ENDPOINT, json=json_data)

        # Check if response is successful
        if response.status_code != 200:
            return {"error": f"Prediction failed with status code {response.status_code}"}

        # Parse predictions from response
        predictions = response.json().get('predictions')

        if not predictions:
            return {"error": "No predictions found in response"}

        # Extract predicted class and confidence
        prediction = np.array(predictions[0])
        predicted_class = CLASS_NAMES[np.argmax(prediction)]
        confidence = np.max(prediction)

        return {
            'class': predicted_class,
            'confidence': float(confidence)
        }

    except Exception as e:
        return {"error": str(e)}

# Serve the React app's static files
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("frontend/build/index.html")

if __name__ == "__main__":
    # Start the FastAPI app
    uvicorn.run(app, host='0.0.0.0', port=8000)
