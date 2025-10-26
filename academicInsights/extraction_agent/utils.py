import pytesseract
from pytesseract import Output
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
from typing import Dict, Any
import re
import logging
from Models.Response import ExtractResponse

logger = logging.getLogger(__name__)

# Configure Tesseract path (Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path: Path, language: str = 'eng') -> tuple:
    """
    Extract text from image using Tesseract OCR
    
    Args:
        image_path: Path to image file
        language: Tesseract language code (default: 'eng')
    
    Returns:
        Extracted text
    """
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang=language)

        data = pytesseract.image_to_data(image, lang=language, output_type=Output.DICT)
        confs = []
        for c in data.get('conf', []):
            try:
                cv = float(c)
            except Exception:
                continue
            if cv >= 0:
                confs.append(cv)

        avg_conf = float(sum(confs) / len(confs)) if confs else None
        return text.strip(), avg_conf
    except Exception as e:
        logger.error(f"Error extracting text from image: {str(e)}")
        raise

def extract_text_from_pdf(pdf_path: Path, language: str = 'eng', dpi: int = 300) -> tuple:
    """
    Extract text from PDF using Tesseract OCR
    
    Args:
        pdf_path: Path to PDF file
        language: Tesseract language code (default: 'eng')
        dpi: DPI for PDF to image conversion
    
    Returns:
        Extracted text from all pages
    """
    try:

        images = convert_from_path(pdf_path, dpi=dpi)
        

        all_text = []
        all_confs = []

        for i, image in enumerate(images):
            logger.info(f"Processing page {i + 1}/{len(images)}")
            text = pytesseract.image_to_string(image, lang=language)
            all_text.append(text.strip())

            data = pytesseract.image_to_data(image, lang=language, output_type=Output.DICT)
            for c in data.get('conf', []):
                try:
                    cv = float(c)
                except Exception:
                    continue
                if cv >= 0:
                    all_confs.append(cv)

        joined = "\n\n".join(all_text)
        avg_conf = float(sum(all_confs) / len(all_confs)) if all_confs else None

        return joined, avg_conf
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_metadata(text: str) -> Dict[str, Any]:
    """
    Extract metadata from text (titles, dates, etc.)
    
    Args:
        text: Extracted text
    
    Returns:
        Dictionary with metadata
    """
    metadata = {
        "title": None,
        "dates": [],
        "emails": [],
        "urls": [],
        "word_count": 0,
        "line_count": 0
    }
    
    lines = text.split('\n')
    metadata["line_count"] = len(lines)
    metadata["word_count"] = len(text.split())
    

    for line in lines:
        if line.strip():
            metadata["title"] = line.strip()
            break
    

    date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b'
    metadata["dates"] = re.findall(date_pattern, text)
    

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    metadata["emails"] = re.findall(email_pattern, text)
    

    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    metadata["urls"] = re.findall(url_pattern, text)
    
    return metadata

def structure_text(text: str) -> Dict[str, Any]:
    """
    Structure extracted text into sections
    
    Args:
        text: Extracted text
    
    Returns:
        Structured dictionary
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    structure = {
        "paragraphs": [],
        "sections": []
    }
    
    current_paragraph = []
    
    for line in lines:
        if line.isupper() or line.endswith(':'):
            if current_paragraph:
                structure["paragraphs"].append(" ".join(current_paragraph))
                current_paragraph = []
            structure["sections"].append(line)
        else:
            current_paragraph.append(line)
    
    if current_paragraph:
        structure["paragraphs"].append(" ".join(current_paragraph))
    
    return structure

def clean_ocr_text(raw: str) -> Dict[str, str]:
    """
    Normalize OCR text:
      - convert escaped backslash sequences like '\\n' or '\\t' into actual whitespace
      - create 'struct_text' where multiple consecutive newlines are collapsed to one (keeps paragraph boundaries)
      - create 'raw_text' where all whitespace becomes single spaces (suitable for storage / display)
    Returns dict with keys: 'raw_text', 'struct_text', 'orig'
    """
    if raw is None:
        return {"raw_text": "", "struct_text": "", "orig": ""}

    text = raw.replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n').replace('\\t', ' ')
    
    struct_text = re.sub(r'\n{2,}', '\n\n', text)  # keep paragraph breaks (double newline) but normalize runs
    struct_text = re.sub(r'[ \t]+$', '', struct_text, flags=re.M)  # trim trailing spaces on lines

    raw_text = re.sub(r'\s+', ' ', text).strip()

    return {"raw_text": raw_text, "struct_text": struct_text, "orig": text}

async def process_document(file_path: Path, filename: str) -> ExtractResponse:
    """
    Process document and return structured JSON
    
    Args:
        file_path: Path to document
        filename: Original filename
    
    Returns:
        Dictionary with extracted data
    """
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.pdf':
        text, conf = extract_text_from_pdf(file_path)
    else:
        text, conf = extract_text_from_image(file_path)


    cleaned = clean_ocr_text(text)
    raw_text = cleaned["raw_text"]
    struct_input = cleaned["struct_text"]

    metadata = extract_metadata(struct_input)
    structure = structure_text(struct_input)
    
    conf_value = None
    if conf is not None:
        try:
            conf_value = f"{conf:.1f}"
        except Exception:
            conf_value = None

    result = {
        "status": "success",
        "filename": filename,
        "file_type": file_extension,
        "text": struct_input,
        "raw_text": raw_text,
        "metadata": metadata,
        "structure": structure,
        "confidence": conf_value if conf_value is not None else ("high" if len(raw_text) > 100 else "low")
    }

    return ExtractResponse(**result)