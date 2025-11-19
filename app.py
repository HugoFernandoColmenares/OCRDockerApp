import os
import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import pytesseract
from PIL import Image
import numpy as np
from config import get_config

# Load configuration
config = get_config()

# Configuración de logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = Flask(__name__)
app.config.from_object(config)
CORS(app, origins=config.CORS_ORIGINS)

# Configuración de directorios
UPLOAD_FOLDER = config.UPLOAD_FOLDER
RESULTS_FOLDER = config.RESULTS_FOLDER
ALLOWED_EXTENSIONS = config.ALLOWED_EXTENSIONS

# Crear directorios si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocesar imagen para mejorar el reconocimiento OCR"""
    try:
        # Leer imagen con OpenCV
        image = cv2.imread(image_path)
        
        if image is None:
            raise ValueError("No se pudo leer la imagen")
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Aplicar desenfoque gaussiano para reducir ruido
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Aplicar umbral adaptativo
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Aplicar morphological operations para mejorar la calidad
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    except Exception as e:
        logger.error(f"Error en preprocesamiento: {str(e)}")
        return None

def extract_text_from_image(image_path):
    """Extraer texto de una imagen usando OCR"""
    try:
        # Preprocesar imagen
        processed_image = preprocess_image(image_path)
        
        if processed_image is None:
            # Si falla el preprocesamiento, usar imagen original
            image = Image.open(image_path)
        else:
            # Convertir array de OpenCV a PIL Image
            image = Image.fromarray(processed_image)
        
        # Configurar pytesseract para español y mejorar precisión
        custom_config = r'--oem 3 --psm 6 -l spa'
        
        # Extraer texto
        text = pytesseract.image_to_string(image, config=custom_config)
        
        # Limpiar texto extraído
        cleaned_text = text.strip()
        
        # Buscar patrones de códigos comunes (números, letras, códigos de barras)
        import re
        
        # Patrones comunes de códigos de inventario
        patterns = {
            'codigo_barras': r'\b\d{8,13}\b',  # Códigos de barras (8-13 dígitos)
            'codigo_producto': r'\b[A-Z0-9]{4,12}\b',  # Códigos alfanuméricos
            'numero_serie': r'\b[A-Z]{2,4}\d{4,8}\b',  # Números de serie
            'sku': r'\bSKU[:\s]*([A-Z0-9-]+)\b',  # SKU
            'precio': r'\$?\d+\.?\d*'  # Precios
        }
        
        extracted_codes = {}
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
            if matches:
                extracted_codes[pattern_name] = matches
        
        return {
            'raw_text': cleaned_text,
            'extracted_codes': extracted_codes,
            'confidence': 'high' if cleaned_text else 'low'
        }
        
    except Exception as e:
        logger.error(f"Error en extracción OCR: {str(e)}")
        return {
            'raw_text': '',
            'extracted_codes': {},
            'confidence': 'error',
            'error': str(e)
        }

@app.route('/')
def index():
    """Página principal de la aplicación"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """Endpoint para cargar múltiples archivos"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No se encontraron archivos'}), 400
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({'error': 'No se seleccionaron archivos'}), 400
        
        results = []
        processed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                # Generar nombre único para el archivo
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Guardar archivo
                file.save(filepath)
                
                # Procesar con OCR
                logger.info(f"Procesando archivo: {filename}")
                ocr_result = extract_text_from_image(filepath)
                
                # Agregar metadatos
                result = {
                    'original_filename': filename,
                    'processed_filename': unique_filename,
                    'upload_time': datetime.now().isoformat(),
                    'file_size': os.path.getsize(filepath),
                    'ocr_result': ocr_result
                }
                
                results.append(result)
                processed_files.append(unique_filename)
                
                logger.info(f"Archivo procesado exitosamente: {filename}")
            else:
                results.append({
                    'original_filename': file.filename,
                    'error': 'Tipo de archivo no permitido'
                })
        
        return jsonify({
            'success': True,
            'processed_count': len([r for r in results if 'error' not in r]),
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error en carga de archivos: {str(e)}")
        return jsonify({'error': f'Error procesando archivos: {str(e)}'}), 500

@app.route('/api/download-json', methods=['POST'])
def download_json():
    """Endpoint para descargar resultados en formato JSON"""
    try:
        data = request.get_json()
        if not data or 'results' not in data:
            return jsonify({'error': 'No hay resultados para descargar'}), 400
        
        # Generar nombre de archivo único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'ocr_results_{timestamp}.json'
        filepath = os.path.join(RESULTS_FOLDER, filename)
        
        # Guardar resultados en archivo JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data['results'], f, ensure_ascii=False, indent=2)
        
        # Enviar archivo como descarga
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error generando JSON: {str(e)}")
        return jsonify({'error': f'Error generando archivo: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(413)
def too_large(e):
    """Manejar archivos demasiado grandes"""
    return jsonify({'error': 'El archivo es demasiado grande. Máximo 16MB permitido.'}), 413

@app.errorhandler(500)
def internal_error(e):
    """Manejar errores internos"""
    logger.error(f"Error interno: {str(e)}")
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    # Verificar que tesseract está instalado
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR disponible")
    except Exception as e:
        logger.error(f"Tesseract no está disponible: {str(e)}")
    
    # Iniciar aplicación
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)