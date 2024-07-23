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
import tensorflow as tf

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

# Path to the model directory
MODEL_PATH = "saved_models/1"

# Load the model
model = tf.saved_model.load(MODEL_PATH)

# Class names for the predictions
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
    image = read_file_as_image(await file.read())
    img_batch = np.expand_dims(image, 0)

    # Convert the image batch to float32 (if required by the model)
    img_batch = img_batch.astype(np.float32)

    # Perform inference using the loaded model
    predictions = model(img_batch)

    predicted_class = CLASS_NAMES[np.argmax(predictions[0])]
    confidence = np.max(predictions[0])
    return {
        'class': predicted_class,
        'confidence': float(confidence)
    }

def build_frontend():
    frontend_dir = "/home/ubuntu/mission-tomato/frontend"
    npm_path = "/usr/bin/npm"
    
    print(f"Building frontend in directory: {frontend_dir}")
    
    # Set NODE_OPTIONS environment variable
    os.environ["NODE_OPTIONS"] = "--openssl-legacy-provider"
    
    # Run the npm build command
    build_process = subprocess.run([npm_path, "run", "build"], cwd=frontend_dir, capture_output=True, text=True, env=os.environ)
    
    if build_process.returncode == 0:
        print("Frontend build succeeded")
        print(build_process.stdout)
    else:
        print("Frontend build failed")
        print(build_process.stderr)

# Serve the React app's static files
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("frontend/build/index.html")

if __name__ == "__main__":
    # Build the frontend
    build_frontend()
    
    # Start the FastAPI app
    uvicorn.run(app, host='0.0.0.0', port=8000)
