import fitz
import os


def extract_text_from_pdf(workspace_id: str, filename: str) -> str:
    """Extract raw text from an uploaded PDF using PyMuPDF."""
    file_path = os.path.join("uploads", workspace_id, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF not found: {file_path}")

    doc = fitz.open(file_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n".join(text_parts).strip()
