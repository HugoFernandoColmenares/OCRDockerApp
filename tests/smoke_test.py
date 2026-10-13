#!/usr/bin/env python3
"""Docker smoke test: login, barcode read, review, and CSV export."""

import io
import os
import sys
import tempfile

os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('SECRET_KEY', 'local-mvp-secret-change-me')
os.environ.setdefault('APP_PASSWORD', 'ocr-local')
os.environ['DATABASE_PATH'] = os.path.join(tempfile.mkdtemp(prefix='ocr-db-'), 'inventory.db')
os.environ['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='ocr-uploads-')
os.environ['RESULTS_FOLDER'] = tempfile.mkdtemp(prefix='ocr-results-')

import barcode
import pytesseract
from barcode.writer import ImageWriter
from PIL import Image

from app import app


PASSWORD = os.environ['APP_PASSWORD']
KNOWN_CODE = 'ABC123456'


def fail(message):
    print(f'FAIL: {message}')
    sys.exit(1)


def barcode_png(value):
    buffer = io.BytesIO()
    code = barcode.get_barcode_class('code128')(value, writer=ImageWriter())
    code.write(buffer, {
        'write_text': False,
        'quiet_zone': 6.5,
        'module_height': 20.0,
        'module_width': 0.4,
    })
    return buffer.getvalue()


def png_bytes(draw=None):
    image = Image.new('RGB', (480, 180), 'white')
    if draw:
        draw(image)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def post_file(client, name, payload):
    response = client.post(
        '/api/upload',
        data={'files': (io.BytesIO(payload), name)},
    )
    if response.status_code != 200:
        fail(f'upload {name} returned {response.status_code}: {response.get_data(as_text=True)}')
    body = response.get_json()
    return body['batch_id'], body['results'][0]


def main():
    client = app.test_client()

    health = client.get('/api/health')
    if health.status_code != 200:
        fail(f'health check failed: {health.get_data(as_text=True)}')
    health_body = health.get_json()
    if health_body.get('status') != 'healthy':
        fail(f'unexpected health payload: {health_body}')
    print('health: ok')

    denied = client.get('/api/batches')
    if denied.status_code != 401:
        fail('batches endpoint allowed an anonymous request')

    bad_login = client.post('/api/login', json={'password': 'wrong-password'})
    if bad_login.status_code != 401:
        fail('wrong password was accepted')

    login = client.post('/api/login', json={'password': PASSWORD})
    if login.status_code != 200:
        fail('operator login failed')
    print('login: ok')

    batch_id, item = post_file(client, 'fixture.png', barcode_png(KNOWN_CODE))
    print(f'barcode read: status={item["status"]} code={item["proposed_code"]} type={item["code_type"]}')
    if item['status'] != 'accepted' or item['proposed_code'] != KNOWN_CODE:
        fail(f'expected barcode {KNOWN_CODE}, got {item}')
    if item['confidence'] != 'high' or item['code_type'] != 'barcode':
        fail(f'barcode was not treated as a decoded symbol: {item}')

    _, blank = post_file(client, 'blank.png', png_bytes())
    if blank['status'] != 'unreadable':
        fail(f'blank image should be unreadable, got {blank}')
    print('blank image: unreadable')

    _, rejected = post_file(client, 'notes.txt', b'not an image')
    if rejected['status'] != 'rejected':
        fail(f'text file should be rejected, got {rejected}')
    print('text file: rejected')

    from PIL import ImageDraw
    def draw_price(image):
        drawing = ImageDraw.Draw(image)
        drawing.text((20, 70), 'PRECIO: $29.99', fill='black')

    _, priced = post_file(client, 'price.png', png_bytes(draw_price))
    proposed = priced.get('proposed_code') or ''
    if priced['code_type'] == 'barcode' or proposed in {'29.99', '$29.99'}:
        fail(f'price was stored as an inventory code: {priced}')
    print(f'price label: status={priced["status"]} proposed={proposed!r}')

    confirm = client.post(
        f'/api/batches/{batch_id}/confirm',
        json={'items': [{'id': item['id'], 'corrected_code': KNOWN_CODE}]},
    )
    if confirm.status_code != 200:
        fail(f'confirm failed: {confirm.get_data(as_text=True)}')
    print('confirm: ok')

    exported = client.get(f'/api/batches/{batch_id}/export.csv')
    if exported.status_code != 200 or KNOWN_CODE.encode() not in exported.data:
        fail(f'csv export missing the saved code: {exported.get_data(as_text=True)}')
    header = exported.get_data(as_text=True).splitlines()[0]
    if header != 'filename,code_type,raw_value,corrected_value,timestamp,status':
        fail(f'unexpected csv header: {header}')
    print('csv: ok')

    exported_json = client.get(f'/api/batches/{batch_id}/export.json')
    if exported_json.status_code != 200:
        fail('json export failed')
    rows = exported_json.get_json()
    if not rows or rows[0].get('corrected_value') != KNOWN_CODE:
        fail(f'json export did not come from the saved row: {rows}')
    print('json: ok')

    listing = client.get('/api/batches')
    batches = listing.get_json().get('batches') or []
    if not any(batch['id'] == batch_id and batch['confirmed'] >= 1 for batch in batches):
        fail('saved batch is missing from recent batches')
    print('recent batches: ok')

    original_cmd = pytesseract.pytesseract.tesseract_cmd
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract-missing'
    broken = client.get('/api/health')
    pytesseract.pytesseract.tesseract_cmd = original_cmd
    if broken.status_code != 503:
        fail('health stayed successful while Tesseract was missing')
    restored = client.get('/api/health')
    if restored.status_code != 200:
        fail('health did not recover after restoring Tesseract')
    print('health failure: ok')
    print('smoke test passed')


if __name__ == '__main__':
    main()
