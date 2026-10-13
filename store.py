"""SQLite store for inventory batches and reviewed codes."""

import json
import os
import sqlite3
import uuid
from datetime import datetime


def utc_now():
    return datetime.utcnow().isoformat(timespec='seconds')


class Store:
    def __init__(self, path):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._init_db()

    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA journal_mode=WAL')
        connection.execute('PRAGMA foreign_keys=ON')
        return connection

    def _init_db(self):
        with self.connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS batches (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL
                )
                '''
            )
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    proposed_code TEXT,
                    code_type TEXT,
                    confidence TEXT,
                    raw_text TEXT,
                    candidates_json TEXT,
                    corrected_code TEXT,
                    confirmed INTEGER NOT NULL DEFAULT 0,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (batch_id) REFERENCES batches(id)
                )
                '''
            )

    def create_batch(self):
        batch_id = str(uuid.uuid4())
        with self.connect() as connection:
            connection.execute(
                'INSERT INTO batches (id, created_at) VALUES (?, ?)',
                (batch_id, utc_now()),
            )
        return batch_id

    def add_item(self, batch_id, **fields):
        item_id = str(uuid.uuid4())
        candidates = fields.get('candidates') or []
        with self.connect() as connection:
            connection.execute(
                '''
                INSERT INTO items (
                    id, batch_id, original_filename, status, proposed_code,
                    code_type, confidence, raw_text, candidates_json,
                    corrected_code, confirmed, file_size, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 0, ?, ?)
                ''',
                (
                    item_id,
                    batch_id,
                    fields.get('original_filename') or 'image',
                    fields.get('status') or 'rejected',
                    fields.get('proposed_code'),
                    fields.get('code_type'),
                    fields.get('confidence'),
                    (fields.get('raw_text') or '')[:8000],
                    json.dumps(candidates, ensure_ascii=False),
                    int(fields.get('file_size') or 0),
                    utc_now(),
                ),
            )
        return item_id

    def list_batches(self, limit=20):
        with self.connect() as connection:
            rows = connection.execute(
                '''
                SELECT
                    b.id,
                    b.created_at,
                    COUNT(i.id) AS total,
                    SUM(CASE WHEN i.status = 'accepted' THEN 1 ELSE 0 END) AS accepted,
                    SUM(CASE WHEN i.status = 'unreadable' THEN 1 ELSE 0 END) AS unreadable,
                    SUM(CASE WHEN i.status = 'rejected' THEN 1 ELSE 0 END) AS rejected,
                    SUM(CASE WHEN i.confirmed = 1 THEN 1 ELSE 0 END) AS confirmed
                FROM batches b
                LEFT JOIN items i ON i.batch_id = b.id
                GROUP BY b.id
                ORDER BY b.created_at DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_batch(self, batch_id):
        with self.connect() as connection:
            batch = connection.execute(
                'SELECT id, created_at FROM batches WHERE id = ?',
                (batch_id,),
            ).fetchone()
            if batch is None:
                return None
            items = connection.execute(
                '''
                SELECT id, batch_id, original_filename, status, proposed_code,
                       code_type, confidence, raw_text, candidates_json,
                       corrected_code, confirmed, file_size, created_at
                FROM items
                WHERE batch_id = ?
                ORDER BY created_at ASC
                ''',
                (batch_id,),
            ).fetchall()
        return {
            'id': batch['id'],
            'created_at': batch['created_at'],
            'items': [self._item_dict(row) for row in items],
        }

    def confirm_items(self, batch_id, updates):
        confirmed = []
        with self.connect() as connection:
            for update in updates:
                item_id = update.get('id')
                corrected = (update.get('corrected_code') or '').strip()
                if not item_id or not corrected:
                    continue
                cursor = connection.execute(
                    '''
                    UPDATE items
                    SET corrected_code = ?, confirmed = 1
                    WHERE id = ? AND batch_id = ?
                    ''',
                    (corrected, item_id, batch_id),
                )
                if cursor.rowcount:
                    confirmed.append(item_id)
        return confirmed

    def confirmed_rows(self, batch_id):
        with self.connect() as connection:
            rows = connection.execute(
                '''
                SELECT original_filename, code_type, proposed_code, corrected_code,
                       created_at, status
                FROM items
                WHERE batch_id = ? AND confirmed = 1
                ORDER BY created_at ASC
                ''',
                (batch_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def _item_dict(self, row):
        try:
            candidates = json.loads(row['candidates_json'] or '[]')
        except json.JSONDecodeError:
            candidates = []
        return {
            'id': row['id'],
            'batch_id': row['batch_id'],
            'original_filename': row['original_filename'],
            'status': row['status'],
            'proposed_code': row['proposed_code'],
            'code_type': row['code_type'],
            'confidence': row['confidence'],
            'raw_text': row['raw_text'] or '',
            'candidates': candidates,
            'corrected_code': row['corrected_code'],
            'confirmed': bool(row['confirmed']),
            'file_size': row['file_size'],
            'created_at': row['created_at'],
        }
