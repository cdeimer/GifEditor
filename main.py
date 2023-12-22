import base64
from io import BytesIO
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# A class to easily store and retrive image data between API calls
class ImageStore:
    def __init__(self):
        self.uploaded_image: bytes = None

image_store = ImageStore()

def save_image_to_store(image: bytes):
    image_store.uploaded_image = image

def get_image_from_store():
    return image_store.uploaded_image

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "id": "test"})

@app.post("/upload", response_class=HTMLResponse)
async def upload_and_process_file(file: UploadFile, request: Request):

    # get uploaded file from request
    filename = file.filename

    print(filename)
    print(file.file, file.content_type)

    # Read the file content and encode it as base64
    file_content = await file.read()
    resized_image = resize_image(file_content)
    base64_image = base64.b64encode(resized_image).decode("utf-8")

    save_image_to_store(resized_image)

    return templates.TemplateResponse("image_component.html", {"request": request, "content_type": file.content_type, "base64_image": base64_image})

@app.post("/edit", response_class=HTMLResponse)
async def edit(request: Request) -> bytes:
    stored_image_bytes = get_image_from_store()

    edited_image = create_intensifies_gif(stored_image_bytes)
    print("edited image: ", edited_image)

    base64_image = base64.b64encode(edited_image).decode("utf-8")
    print("base64 image: ", base64_image)

    return templates.TemplateResponse("image_component.html", {"request": request, "content_type": "image/gif", "base64_image": base64_image})

def resize_image(file_content: bytes, target_size=(256, 256)):
    # Open the image using Pillow
    print("resize file content type: ", type(file_content))
    image = Image.open(BytesIO(file_content))

    # Resize the image
    resized_image = image.resize(target_size)

    # Convert the resized image to bytes
    resized_content = BytesIO()
    resized_image.save(resized_content, format="PNG")

    return resized_content.getvalue()

def create_intensifies_gif(image_bytes, num_frames=30, amplitude=5) -> bytes:
    original_image = Image.open(BytesIO(image_bytes))

    width, height = original_image.size

    shaking_frames = []

    for frame in range(num_frames):
        shaking_frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))

        displacement_x = amplitude * (frame / num_frames)
        displacement_y = amplitude * (frame / num_frames)

        shaking_frame.paste(original_image, (int(displacement_x), int(displacement_y)))

        shaking_frames.append(shaking_frame)
    
    gif_bytesio = BytesIO()

    shaking_frames[0].save(
        gif_bytesio,
        format='GIF',
        save_all = True,
        append_images=shaking_frames[1:],
        duration=10,
        loop=0
    )

    gif_bytesio.seek(0)

    return gif_bytesio.read()
