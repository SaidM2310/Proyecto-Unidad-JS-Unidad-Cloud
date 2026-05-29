import redis
import json
import os
import time
from PIL import Image, ImageFilter, ImageOps

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/data/uploads")
PROCESSED_DIR = os.getenv("PROCESSED_DIR", "/app/data/processed")

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


def save_task(task):
    redis_client.set(f"task:{task['id']}", json.dumps(task))


def process_image(task):
    input_path = os.path.join(UPLOAD_DIR, task["input_filename"])
    operation = task["operation"]
    task_id = task["id"]

    with Image.open(input_path) as img:
        img = img.convert("RGB")

        if operation == "thumbnail":
            img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)
            output_filename = f"{task_id}_youtube_thumbnail.jpg"

        elif operation == "resize":
            width = int(task.get("width") or 800)
            height = int(task.get("height") or 600)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            output_filename = f"{task_id}_resize_{width}x{height}.jpg"

        elif operation == "grayscale":
            img = img.convert("L")
            output_filename = f"{task_id}_grayscale.jpg"

        elif operation == "blur":
            img = img.filter(ImageFilter.BLUR)
            output_filename = f"{task_id}_blur.jpg"

        elif operation == "convert_jpg":
            output_filename = f"{task_id}_converted.jpg"

        else:
            img.thumbnail((300, 300))
            output_filename = f"{task_id}_processed.jpg"

        output_path = os.path.join(PROCESSED_DIR, output_filename)
        img.save(output_path, "JPEG", quality=90)

    return output_filename


print("Worker de imágenes iniciado. Esperando tareas...")

while True:
    task_data = redis_client.brpop("image_tasks_queue", timeout=5)

    if not task_data:
        continue

    _, raw_task = task_data
    task = json.loads(raw_task)

    try:
        worker_name = os.getenv("HOSTNAME", "worker")
        print(f"{worker_name} procesando tarea {task['id']} con operación {task['operation']}")

        task["status"] = "en proceso"
        task["worker"] = worker_name
        save_task(task)

        time.sleep(3)

        output_filename = process_image(task)

        task["status"] = "completada"
        task["output_filename"] = output_filename
        task["result_url"] = f"/processed/{output_filename}"
        save_task(task)

        print(f"{worker_name} completó tarea {task['id']}")

    except Exception as e:
        task["status"] = "error"
        task["error"] = str(e)
        save_task(task)
        print(f"Error procesando tarea {task.get('id')}: {e}")
