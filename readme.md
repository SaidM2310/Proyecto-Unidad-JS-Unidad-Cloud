# Procesador de Imágenes

## Descripción del programa

Procesador de imágenes distribuido desarrollado bajo una arquitectura Cloud Native. El sistema permite cargar imágenes desde una interfaz web, enviarlas a una cola de mensajes y procesarlas mediante múltiples workers ejecutándose en contenedores Docker. El usuario puede modificar el tamaño de la imagen y visualizar el estado del procesamiento en tiempo real.

---

## Tecnologías utilizadas

* HTML
* CSS
* JavaScript
* Python
* FastAPI
* Redis
* Docker
* Docker Compose
* Pillow
* AWS EC2

---
## Características del sistema

- Subida de imágenes desde el navegador.
- Redimensionamiento manual de imágenes.
- Procesamiento distribuido mediante workers Docker.
- Cola de mensajes con Redis.
- Estado del procesamiento en tiempo real.
- Generación de miniaturas.
- Escalamiento de workers con Docker Compose.
---

## Arquitectura del programa

```text
Frontend (HTML, CSS, JavaScript)
                │
                │ Solicitud HTTP
                ▼
         Backend FastAPI
                │
                │ Cola de tareas
                ▼
             Redis Queue
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
     Worker   Worker   Worker
       #1       #2       #3
                │
                ▼
       Procesamiento de imagen
                │
                ▼
     Estado del procesamiento
      (pendiente / en proceso /
       completada / error)
```
---

## Flujo del sistema

1. El usuario selecciona una imagen desde el frontend.
2. El usuario define el tamaño manual de escalado.
3. La solicitud se envía al backend FastAPI.
4. La tarea se almacena en Redis.
5. Los workers Docker toman tareas desde la cola.
6. La imagen es procesada.
7. El estado del procesamiento se actualiza en tiempo real.
8. La imagen procesada queda disponible.

---

