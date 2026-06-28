# ============================================
# NyayaAI — Document/Image Processor
# Uploaded files (photo/PDF) ko AI ke samajhne
# layak format mein convert karta hai
# ============================================

import base64
import io
import os

import fitz  # PyMuPDF

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
ALLOWED_DOC_EXT = {"pdf"}

# Groq base64 image request limit ~4MB hai (docs ke mutabik)
MAX_IMAGE_BYTES = 4 * 1024 * 1024
# Overall upload limit (PDF ke liye thoda zyada chalega kyunki sirf text nikalna hai)
MAX_FILE_BYTES = 15 * 1024 * 1024


def get_extension(filename: str) -> str:
    """Filename se extension (lowercase, dot ke bina) nikalta hai."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_image(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_IMAGE_EXT


def is_pdf(filename: str) -> bool:
    return get_extension(filename) in ALLOWED_DOC_EXT


def validate_file(filename: str, file_bytes: bytes) -> str:
    """
    File type aur size validate karta hai.
    Returns: "image" ya "pdf"
    Raises: ValueError agar invalid ho
    """
    ext = get_extension(filename)

    if ext not in ALLOWED_IMAGE_EXT and ext not in ALLOWED_DOC_EXT:
        raise ValueError(
            f"Unsupported file type: .{ext}. "
            f"Allowed: PNG, JPG, JPEG, WEBP, PDF"
        )

    size = len(file_bytes)
    if size > MAX_FILE_BYTES:
        raise ValueError(
            f"File too large ({size / (1024*1024):.1f}MB). "
            f"Max allowed: {MAX_FILE_BYTES / (1024*1024):.0f}MB"
        )

    if ext in ALLOWED_IMAGE_EXT and size > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image too large ({size / (1024*1024):.1f}MB) for analysis. "
            f"Max allowed: {MAX_IMAGE_BYTES / (1024*1024):.0f}MB. "
            f"Please compress or crop the image."
        )

    return "image" if ext in ALLOWED_IMAGE_EXT else "pdf"


def encode_image_to_data_url(filename: str, file_bytes: bytes) -> str:
    """Image bytes ko Groq vision API ke liye base64 data URL mein convert karta hai."""
    ext = get_extension(filename)
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def extract_text_from_pdf(file_bytes: bytes, max_chars: int = 12000) -> str:
    """
    PyMuPDF se PDF ke saare pages ka text nikalta hai.
    max_chars se zyada hone par truncate karta hai (LLM context bachane ke liye).
    """
    text_parts = []
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
    except Exception as e:
        raise ValueError(f"PDF padhne mein error: {e}")

    full_text = "\n\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(
            "Is PDF se koi text nahi nikal paya — shayad ye scanned/image-based "
            "PDF hai. Kripya is document ka photo/screenshot upload karein."
        )

    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[...document truncated...]"

    return full_text
