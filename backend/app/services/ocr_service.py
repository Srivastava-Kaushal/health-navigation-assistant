import os
import fitz
import cv2
import pytesseract

# Uncomment this if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return thresh


def extract_text_from_image(image_path: str) -> str:
    processed = preprocess_image(image_path)
    if processed is None:
        return ""

    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(processed, config=config)
    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    pdf = fitz.open(pdf_path)

    for i, page in enumerate(pdf):
        pix = page.get_pixmap()
        temp_img = f"temp_page_{i}.png"
        pix.save(temp_img)

        page_text = extract_text_from_image(temp_img)
        text += page_text + "\n"

        if os.path.exists(temp_img):
            os.remove(temp_img)

    return text.strip()


def detect_low_confidence(text: str) -> bool:
    if not text:
        return True

    clean_text = text.strip()
    if len(clean_text) < 8:
        return True

    weird_chars = sum(1 for ch in clean_text if not (ch.isalnum() or ch.isspace() or ch in ".,:/()-"))
    ratio = weird_chars / max(len(clean_text), 1)

    return ratio > 0.25


def extract_text(file_path: str, file_type: str):
    file_type = file_type.lower()

    if file_type in ["png", "jpg", "jpeg"]:
        text = extract_text_from_image(file_path)
    elif file_type == "pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = ""

    low_confidence = detect_low_confidence(text)

    return {
        "raw_text": text,
        "low_confidence": low_confidence,
        "message": "Handwritten or unclear text may be inaccurate. Please verify with doctor or pharmacist."
        if low_confidence
        else "Text extracted successfully."
    }