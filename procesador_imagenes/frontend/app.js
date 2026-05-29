const imageInput = document.getElementById("imageInput");
const imageInfo = document.getElementById("imageInfo");
const operationSelect = document.getElementById("operation");
const resizeOptions = document.getElementById("resizeOptions");
const widthInput = document.getElementById("widthInput");
const heightInput = document.getElementById("heightInput");
const selectedSize = document.getElementById("selectedSize");
const sendBtn = document.getElementById("sendBtn");
const statusText = document.getElementById("status");
const workerInfo = document.getElementById("workerInfo");
const previewBox = document.getElementById("previewBox");

let originalWidth = null;
let originalHeight = null;

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  if (!file) {
    imageInfo.textContent = "Selecciona una imagen para ver sus medidas.";
    originalWidth = null;
    originalHeight = null;
    return;
  }

  const imageUrl = URL.createObjectURL(file);
  const img = new Image();

  img.onload = () => {
    originalWidth = img.naturalWidth;
    originalHeight = img.naturalHeight;
    imageInfo.textContent = `Medidas originales: ${originalWidth} × ${originalHeight} px`;
    URL.revokeObjectURL(imageUrl);
  };

  img.src = imageUrl;
});

operationSelect.addEventListener("change", toggleResizeOptions);
widthInput.addEventListener("input", updateSelectedSize);
heightInput.addEventListener("input", updateSelectedSize);

toggleResizeOptions();

function toggleResizeOptions() {
  if (operationSelect.value === "resize") {
    resizeOptions.classList.remove("hidden");
  } else {
    resizeOptions.classList.add("hidden");
  }
}

function updateSelectedSize() {
  const width = widthInput.value;
  const height = heightInput.value;

  if (width && height) {
    selectedSize.textContent = `Nuevo tamaño seleccionado: ${width} × ${height} px`;
  } else {
    selectedSize.textContent = "Nuevo tamaño: sin definir";
  }
}

sendBtn.addEventListener("click", async () => {
  if (!imageInput.files.length) {
    alert("Selecciona una imagen primero.");
    return;
  }

  const operation = operationSelect.value;
  const formData = new FormData();
  formData.append("image", imageInput.files[0]);
  formData.append("operation", operation);

  if (operation === "resize") {
    const width = parseInt(widthInput.value, 10);
    const height = parseInt(heightInput.value, 10);

    if (!width || !height || width < 1 || height < 1) {
      alert("Escribe un ancho y alto válidos para redimensionar.");
      return;
    }

    formData.append("width", width);
    formData.append("height", height);
  }

  statusText.textContent = "pendiente";
  statusText.className = "status processing";
  workerInfo.textContent = "Enviando tarea al backend...";
  previewBox.innerHTML = "<p>Esperando procesamiento...</p>";

  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      body: formData
    });

    if (!response.ok) {
      throw new Error("No se pudo crear la tarea en el backend.");
    }

    const data = await response.json();

    if (!data.task_id) {
      throw new Error("El backend no devolvió un task_id.");
    }

    localStorage.setItem("ultima_tarea_imagen", data.task_id);
    listenTask(data.task_id);
  } catch (error) {
    statusText.textContent = "error";
    statusText.className = "status error";
    workerInfo.textContent = error.message;
  }
});

function listenTask(taskId) {
  const eventSource = new EventSource(`/api/events/${taskId}`);

  eventSource.onmessage = (event) => {
    const task = JSON.parse(event.data);

    statusText.textContent = task.status;
    workerInfo.textContent = task.worker ? `Procesado por: ${task.worker}` : "Esperando worker disponible...";

    if (task.status === "en proceso") {
      statusText.className = "status processing";
    }

    if (task.status === "completada") {
      statusText.className = "status done";
      previewBox.innerHTML = `<img src="${task.result_url}" alt="Imagen procesada" />`;
      eventSource.close();
    }

    if (task.status === "error") {
      statusText.className = "status error";
      previewBox.innerHTML = `<p>Error: ${task.error}</p>`;
      eventSource.close();
    }
  };

  eventSource.onerror = () => {
    statusText.textContent = "error";
    statusText.className = "status error";
    workerInfo.textContent = "Se perdió la conexión SSE.";
    eventSource.close();
  };
}
