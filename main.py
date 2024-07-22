import subprocess
import os
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from io import BytesIO
from PIL import Image
import tensorflow as tf
import uvicorn

# Define the FastAPI app
app = FastAPI()

# Allow CORS for frontend accessibility
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://mission-tomato.pages.dev"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your TensorFlow model
MODEL_PATH = "/home/ubuntu/mission-potato/saved_models/1"
model = tf.saved_model.load(MODEL_PATH)

# Define the class names
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

# Function to read and process the image
def read_file_as_image(data) -> np.ndarray:
    image = np.array(Image.open(BytesIO(data)))
    return image

# Define the prediction endpoint
@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0)
    img_batch = img_batch.astype(np.float32)
    predictions = model(img_batch)
    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])
    return {
        'class': predicted_class,
        'confidence': float(confidence)
    }

# Function to start the frontend
def start_frontend():
    frontend_dir = "/home/ubuntu/mission-potato/frontend"
    # Build the frontend
    subprocess.run(["npm", "install"], cwd=frontend_dir)
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir)
    # Serve the frontend build directory
    subprocess.Popen(["npx", "serve", "-s", "build"], cwd=os.path.join(frontend_dir, "build"))

# Start the frontend in a separate process
start_frontend()

# Run the FastAPI app
if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)
