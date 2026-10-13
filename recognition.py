"""Barcode decoding and OCR fallback for inventory labels."""

import os
import re
import subprocess

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Labeled tokens only. A bare number or a price is not an inventory code.
LABELED_PATTERNS = (
    ('sku', re.compile(r'\bSKU[:\s-]*([A-Z0-9][A-Z0-9-]{2,})', re.IGNORECASE)),
    ('serial', re.compile(r'\b(?:S/?N|SERIAL|SERIE)[:\s-]*([A-Z0-9-]{4,})', re.IGNORECASE)),
    ('product_code', re.compile(r'\b(?:COD(?:IGO)?|CODE|ITEM)[:\s-]*([A-Z0-9-]{4,})', re.IGNORECASE)),
)


def configure_tesseract(cfg):
    command = getattr(cfg, 'TESSERACT_CMD', '') or ''
    if command and os.path.isfile(command):
        pytesseract.pytesseract.tesseract_cmd = command


def _tesseract_command():
    return pytesseract.pytesseract.tesseract_cmd or 'tesseract'


def tesseract_report(cfg):
    """Check the binary on every call. pytesseract caches version lookups."""
    required = [lang for lang in cfg.OCR_LANGUAGE.split('+') if lang]
    command = _tesseract_command()
    try:
        version_output = subprocess.check_output(
            [command, '--version'],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
        language_output = subprocess.check_output(
            [command, '--list-langs'],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return {
            'available': False,
            'error': str(exc),
            'languages': [],
            'missing_languages': required,
        }

    version = version_output.strip().splitlines()[0] if version_output.strip() else ''
    languages = [
        line.strip()
        for line in language_output.splitlines()
        if re.fullmatch(r'[A-Za-z0-9_+]+', line.strip())
    ]
    missing = [lang for lang in required if lang not in languages]
    report = {
        'available': not missing,
        'version': version,
        'languages': languages,
        'missing_languages': missing,
    }
    if missing:
        report['error'] = 'Missing language data: ' + ', '.join(missing)
    return report


def barcode_report():
    try:
        from pyzbar.pyzbar import decode  # noqa: F401
        return {'available': True}
    except Exception as exc:
        return {'available': False, 'error': str(exc)}


def decode_symbols(image_path):
    from pyzbar.pyzbar import decode

    with Image.open(image_path) as image:
        symbols = decode(image.convert('RGB'))

    readings = []
    for symbol in symbols:
        value = symbol.data.decode('utf-8', errors='replace').strip()
        if not value:
            continue
        symbology = symbol.type or ''
        readings.append({
            'value': value,
            'type': 'qr' if symbology == 'QRCODE' else 'barcode',
            'symbology': symbology,
        })
    return readings


def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    kernel = np.ones((1, 1), np.uint8)
    return cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)


def extract_ocr_text(image_path, cfg):
    processed = preprocess_image(image_path)
    if processed is None:
        image = Image.open(image_path)
    else:
        image = Image.fromarray(processed)

    custom_config = f"{cfg.OCR_CONFIG} -l {cfg.OCR_LANGUAGE}"
    text = pytesseract.image_to_string(image, config=custom_config)
    return text.strip()


def labeled_codes(text):
    found = []
    seen = set()
    for code_type, pattern in LABELED_PATTERNS:
        for match in pattern.findall(text or ''):
            value = match.strip()
            key = (code_type, value.upper())
            if not value or key in seen:
                continue
            seen.add(key)
            found.append({'value': value, 'type': 'ocr', 'label': code_type})
    return found


def analyze_image(image_path, cfg):
    """Prefer a decoded barcode or QR. OCR is only a labeled-text fallback."""
    try:
        symbols = decode_symbols(image_path)
    except Exception as exc:
        symbols = []
        barcode_error = str(exc)
    else:
        barcode_error = None

    if symbols:
        primary = symbols[0]
        return {
            'status': 'accepted',
            'proposed_code': primary['value'],
            'code_type': primary['type'],
            'confidence': 'high',
            'raw_text': '',
            'candidates': symbols,
            'error': None,
        }

    try:
        raw_text = extract_ocr_text(image_path, cfg)
    except Exception as exc:
        return {
            'status': 'unreadable',
            'proposed_code': None,
            'code_type': None,
            'confidence': 'unreadable',
            'raw_text': '',
            'candidates': [],
            'error': barcode_error or str(exc),
        }

    labeled = labeled_codes(raw_text)
    if labeled:
        primary = labeled[0]
        return {
            'status': 'accepted',
            'proposed_code': primary['value'],
            'code_type': 'ocr',
            'confidence': 'low',
            'raw_text': raw_text,
            'candidates': labeled,
            'error': None,
        }

    return {
        'status': 'unreadable',
        'proposed_code': None,
        'code_type': None,
        'confidence': 'unreadable',
        'raw_text': raw_text,
        'candidates': [],
        'error': barcode_error,
    }
