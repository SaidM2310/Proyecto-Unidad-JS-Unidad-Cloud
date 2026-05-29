from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import redis
import uuid
import json
import os
import shutil
import time

app = FastAPI(title="Procesador de Imágenes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/data/uploads")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "/app/data/processed")
FRONTEND_DIR = "/app/frontend"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

@app.post("/api/tasks")
async def create_image_task(
    image: UploadFile = File(...),
    operation: str = Form("thumbnail"),
    width: int | None = Form(None),
    height: int | None = Form(None)
):
    allowed_operations = ["thumbnail", "resize", "grayscale", "blur", "convert_jpg"]
    if operation not in allowed_operations:
        operation = "thumbnail"

    if operation == "resize" and (not width or not height or width < 1 or height < 1):
        width = 800
        height = 600

    task_id = str(uuid.uuid4())
    original_extension = os.path.splitext(image.filename)[1].lower() or ".png"
    safe_filename = f"{task_id}{original_extension}"
    input_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    task = {
        "id": task_id,
        "status": "pendiente",
        "operation": operation,
        "width": width,
        "height": height,
        "original_filename": image.filename,
        "input_filename": safe_filename,
        "output_filename": None,
        "result_url": None,
        "error": None
    }

    redis_client.set(f"task:{task_id}", json.dumps(task))
    redis_client.lpush("image_tasks_queue", json.dumps(task))

    return {"task_id": task_id}

@app.get("/api/tasks/{task_id}")
def get_task(task_id: str):
    data = redis_client.get(f"task:{task_id}")
    if not data:
        return {"error": "Tarea no encontrada"}
    return json.loads(data)

@app.get("/api/events/{task_id}")
def task_events(task_id: str):
    def event_stream():
        last_payload = None

        while True:
            data = redis_client.get(f"task:{task_id}")

            if data and data != last_payload:
                yield f"data: {data}\n\n"
                last_payload = data

                task = json.loads(data)
                if task["status"] in ["completada", "error"]:
                    break

            time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/api/health")
def health():
    return {"status": "ok"}



app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
