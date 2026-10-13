import csv
import io
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta

from flask import Flask, jsonify, redirect, render_template, request, Response, session, url_for
from flask_cors import CORS
from PIL import Image
from werkzeug.utils import secure_filename

from config import get_config, validate_runtime
from recognition import analyze_image, barcode_report, configure_tesseract, tesseract_report
from store import Store

settings = get_config()
validate_runtime(settings)

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL), format=settings.LOG_FORMAT)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(settings)
app.permanent_session_lifetime = timedelta(hours=12)
CORS(app, origins=settings.CORS_ORIGINS)

UPLOAD_FOLDER = settings.UPLOAD_FOLDER
RESULTS_FOLDER = settings.RESULTS_FOLDER
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

configure_tesseract(settings)
store = Store(settings.DATABASE_PATH)

PUBLIC_ENDPOINTS = {'health_check', 'login', 'api_login', 'static'}


@app.before_request
def require_operator():
    if request.endpoint in PUBLIC_ENDPOINTS or request.endpoint is None:
        return None
    if not app.config.get('APP_PASSWORD'):
        return None
    if session.get('authenticated'):
        return None
    if request.path.startswith('/api/'):
        return jsonify({'error': 'No autorizado'}), 401
    return redirect(url_for('login'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_uploads():
    folder = app.config['UPLOAD_FOLDER']
    max_age = app.config['UPLOAD_MAX_AGE_DAYS'] * 86400
    max_files = app.config['MAX_STORED_UPLOADS']
    now = time.time()
    files = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        modified = os.path.getmtime(path)
        if now - modified > max_age:
            os.remove(path)
            continue
        files.append((modified, path))
    files.sort()
    overflow = len(files) - max_files
    for _, path in files[:max(0, overflow)]:
        os.remove(path)


def image_is_readable(path):
    try:
        with Image.open(path) as image:
            image.verify()
        return True
    except Exception:
        return False


def process_upload(file, batch_id):
    original_name = file.filename or 'image'
    if not allowed_file(original_name):
        return store_result(batch_id, original_name, status='rejected', error='Tipo de archivo no permitido')

    filename = secure_filename(original_name) or 'image'
    unique_filename = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)

    if not image_is_readable(filepath):
        os.remove(filepath)
        return store_result(batch_id, original_name, status='rejected', error='El archivo no es una imagen válida')

    file_size = os.path.getsize(filepath)
    try:
        analysis = analyze_image(filepath, settings)
    except Exception as exc:
        logger.exception('Error analizando %s', original_name)
        analysis = {
            'status': 'unreadable',
            'proposed_code': None,
            'code_type': None,
            'confidence': 'unreadable',
            'raw_text': '',
            'candidates': [],
            'error': str(exc),
        }

    return store_result(
        batch_id,
        original_name,
        status=analysis['status'],
        proposed_code=analysis.get('proposed_code'),
        code_type=analysis.get('code_type'),
        confidence=analysis.get('confidence'),
        raw_text=analysis.get('raw_text') or '',
        candidates=analysis.get('candidates') or [],
        file_size=file_size,
        error=analysis.get('error'),
    )


def store_result(batch_id, original_name, status, **extra):
    item_id = store.add_item(
        batch_id,
        original_filename=original_name,
        status=status,
        proposed_code=extra.get('proposed_code'),
        code_type=extra.get('code_type'),
        confidence=extra.get('confidence'),
        raw_text=extra.get('raw_text') or '',
        candidates=extra.get('candidates') or [],
        file_size=extra.get('file_size') or 0,
    )
    return {
        'id': item_id,
        'batch_id': batch_id,
        'original_filename': original_name,
        'status': status,
        'proposed_code': extra.get('proposed_code'),
        'code_type': extra.get('code_type'),
        'confidence': extra.get('confidence') or 'unreadable',
        'raw_text': extra.get('raw_text') or '',
        'candidates': extra.get('candidates') or [],
        'corrected_code': None,
        'confirmed': False,
        'file_size': extra.get('file_size') or 0,
        'error': extra.get('error'),
    }


def batch_payload(batch):
    items = batch['items']
    return {
        'id': batch['id'],
        'created_at': batch['created_at'],
        'items': items,
        'accepted_count': sum(1 for item in items if item['status'] == 'accepted'),
        'unreadable_count': sum(1 for item in items if item['status'] == 'unreadable'),
        'rejected_count': sum(1 for item in items if item['status'] == 'rejected'),
        'confirmed_count': sum(1 for item in items if item['confirmed']),
    }


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('authenticated'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '')
        if app.config.get('APP_PASSWORD') and password == app.config['APP_PASSWORD']:
            session['authenticated'] = True
            session.permanent = True
            return redirect(url_for('index'))
        if not app.config.get('APP_PASSWORD'):
            session['authenticated'] = True
            return redirect(url_for('index'))
        error = 'Clave incorrecta'
    return render_template('login.html', error=error)


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    expected = app.config.get('APP_PASSWORD') or ''
    if expected and password == expected:
        session['authenticated'] = True
        session.permanent = True
        return jsonify({'success': True})
    if not expected:
        session['authenticated'] = True
        return jsonify({'success': True})
    return jsonify({'error': 'Clave incorrecta'}), 401


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    tesseract = tesseract_report(settings)
    barcode = barcode_report()
    healthy = tesseract.get('available') and barcode.get('available')
    payload = {
        'status': 'healthy' if healthy else 'unhealthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.1.0',
        'tesseract': tesseract,
        'barcode': barcode,
    }
    return jsonify(payload), (200 if healthy else 503)


@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No se encontraron archivos'}), 400

    files = request.files.getlist('files')
    if not files or all(not item.filename for item in files):
        return jsonify({'error': 'No se seleccionaron archivos'}), 400

    batch_id = store.create_batch()
    results = [process_upload(item, batch_id) for item in files]
    cleanup_uploads()

    accepted = sum(1 for item in results if item['status'] == 'accepted')
    unreadable = sum(1 for item in results if item['status'] == 'unreadable')
    rejected = sum(1 for item in results if item['status'] == 'rejected')
    return jsonify({
        'success': True,
        'batch_id': batch_id,
        'processed_count': accepted + unreadable,
        'accepted_count': accepted,
        'unreadable_count': unreadable,
        'rejected_count': rejected,
        'results': results,
    })


@app.route('/api/batches', methods=['GET'])
def list_batches():
    return jsonify({'batches': store.list_batches()})


@app.route('/api/batches/<batch_id>', methods=['GET'])
def get_batch(batch_id):
    batch = store.get_batch(batch_id)
    if batch is None:
        return jsonify({'error': 'Lote no encontrado'}), 404
    return jsonify(batch_payload(batch))


@app.route('/api/batches/<batch_id>/confirm', methods=['POST'])
def confirm_batch(batch_id):
    if store.get_batch(batch_id) is None:
        return jsonify({'error': 'Lote no encontrado'}), 404

    data = request.get_json(silent=True) or {}
    updates = data.get('items') or []
    if not isinstance(updates, list):
        return jsonify({'error': 'Formato de confirmación inválido'}), 400

    store.confirm_items(batch_id, updates)
    batch = store.get_batch(batch_id)
    payload = batch_payload(batch)
    if payload['confirmed_count'] == 0:
        return jsonify({'error': 'No hay filas confirmadas. Escribe un código o descarta la fila.', **payload}), 400
    return jsonify({'success': True, **payload})


def export_rows(batch_id):
    if store.get_batch(batch_id) is None:
        return None, (jsonify({'error': 'Lote no encontrado'}), 404)
    rows = store.confirmed_rows(batch_id)
    if not rows:
        return None, (jsonify({'error': 'Confirma el lote antes de exportar'}), 400)
    return rows, None


@app.route('/api/batches/<batch_id>/export.csv', methods=['GET'])
def export_csv(batch_id):
    rows, error = export_rows(batch_id)
    if error:
        return error

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['filename', 'code_type', 'raw_value', 'corrected_value', 'timestamp', 'status'])
    for row in rows:
        writer.writerow([
            row['original_filename'],
            row['code_type'] or '',
            row['proposed_code'] or '',
            row['corrected_code'] or '',
            row['created_at'],
            row['status'],
        ])
    filename = f'ocr_results_{batch_id[:8]}.csv'
    return Response(
        buffer.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@app.route('/api/batches/<batch_id>/export.json', methods=['GET'])
def export_json(batch_id):
    rows, error = export_rows(batch_id)
    if error:
        return error

    payload = [
        {
            'filename': row['original_filename'],
            'code_type': row['code_type'],
            'raw_value': row['proposed_code'],
            'corrected_value': row['corrected_code'],
            'timestamp': row['created_at'],
            'status': row['status'],
        }
        for row in rows
    ]
    filename = f'ocr_results_{batch_id[:8]}.json'
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@app.errorhandler(413)
def too_large(_error):
    return jsonify({'error': 'El archivo es demasiado grande. Máximo 16MB permitido.'}), 413


@app.errorhandler(500)
def internal_error(error):
    logger.error('Error interno: %s', error)
    return jsonify({'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    report = tesseract_report(settings)
    if report.get('available'):
        logger.info('Tesseract OCR disponible')
    else:
        logger.error('Tesseract no está disponible: %s', report.get('error'))
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
