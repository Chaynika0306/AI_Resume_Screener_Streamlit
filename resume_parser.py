# resume_parser.py
from pathlib import Path
from pdfminer.high_level import extract_text as pdf_extract_text
import docx

def extract_text_from_pdf(path):
    try:
        text = pdf_extract_text(path)
        return text or ""
    except Exception as e:
        print(f"[pdf parse error] {path}: {e}")
        return ""

def extract_text_from_docx(path):
    try:
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"[docx parse error] {path}: {e}")
        return ""

def extract_text_from_txt(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"[txt parse error] {path}: {e}")
        return ""

def extract_text_from_file(path):
    """
    path: str or Path to file (.pdf, .docx, .txt)
    returns: extracted text (string)
    """
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(str(p))
    elif suffix in [".docx", ".doc"]:
        return extract_text_from_docx(str(p))
    elif suffix in [".txt", ".md"]:
        return extract_text_from_txt(str(p))
    else:
        # fallback: try read as text
        return extract_text_from_txt(str(p))
