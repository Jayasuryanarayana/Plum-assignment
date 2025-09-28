import io
import pytesseract
from PIL import Image
import cv2
import numpy as np

def set_tesseract_path(path):
    pytesseract.pytesseract.tesseract_cmd = path

def preprocess_image(image_bytes):
    try:
        image_np = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        processed_img = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(processed_img)
    except Exception as e:
        print(f"OpenCV Preprocessing Error: {e}")
        return Image.open(io.BytesIO(image_bytes))


def extract_text_from_image(image_file):

    try:
        image_bytes = image_file.read()

        processed_image = preprocess_image(image_bytes)

        # Perform OCR on the processed image
        text = pytesseract.image_to_string(processed_image)
        return text
    except Exception as e:
        print(f"Tesseract OCR Error: {e}")
        return None
