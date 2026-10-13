# What Inventory OCR Scanner Still Needs to Be an MVP

This note describes the smallest product that a warehouse or retail operator could use in a real shift, and the gaps between that product and the current codebase. The app already has a working path: upload images, run Tesseract OCR, guess inventory-like tokens with regular expressions, show them in the browser, and download JSON. That path is a prototype. It is not yet a minimum viable product.

## What “done” means for this MVP

An operator should be able to:

1. Open the app on the machine where photos are taken.
2. Upload one or more inventory photos and know whether each file was accepted.
3. See the identifier the system believes it found (barcode, SKU, or serial), with a way to correct it before anything is kept.
4. Save the corrected result so it is still there after a refresh.
5. Export the saved batch as CSV (and keep the existing JSON export).
6. Tell a failed run from a successful one, including when Tesseract is missing or a photo has no readable code.

If those six things work on the documented Docker setup, with one smoke test that fails when they break, the product is an MVP. Everything else can wait.

## What already exists

| Area | Current behavior |
| --- | --- |
| Upload | Multi-file image upload, extension allow-list, 16 MB limit |
| OCR | OpenCV preprocess plus Tesseract (`spa` only in `extract_text_from_image`) |
| Parsing | Regex guesses for barcodes, product codes, serials, SKUs, and prices |
| UI | Single page: drag-and-drop, simulated progress, on-screen results, JSON download |
| Deploy | `Dockerfile` and Compose build; image `ocrdockerapp-ocr-app` starts and `/api/health` returns `healthy` |
| Config | `config.py` and `.env.example` for port, folders, CORS, and OCR language |

## Gaps that block the MVP

### 1. Identifiers are guessed, not read

Barcodes and SKUs are inferred from OCR text (`\d{8,13}`, loose alphanumerics, a very broad price pattern). There is no barcode or QR decoder. Printed digits that Tesseract misreads become inventory records. Confidence is the string `"high"` whenever any text comes back, `"low"` when the string is empty, or `"error"` on exception. It is not a recognition score.

For the MVP, decode barcodes and QR codes with a dedicated library first, and use OCR only as a fallback for labels that are text. Return a real confidence or “unreadable” state, and do not mark a price-like number as a product code.

### 2. Nobody can correct a bad read

OCR will be wrong often enough that uneditable output is not usable. The UI lists extracted codes and offers JSON download. It does not let the operator edit a code, drop a false match, or mark a row as reviewed.

The MVP needs a review step: one row per image, proposed code, editable field, and an explicit confirm action before the row is stored.

### 3. Results disappear

Uploads are written under `uploads/`. A JSON file is written under `results/` only when the client calls `POST /api/download-json`. There is no database, no list of past batches, and no reload of a previous session. `GET` history does not exist. Closing the tab drops the work.

The MVP needs a single store (SQLite is enough) with a batch, its images, the proposed code, the corrected code, and a timestamp. A “recent batches” view should load that store. Object storage, multi-tenant accounts, and a warehouse WMS can wait.

### 4. The export is not what inventory work uses

JSON is useful for developers. Spreadsheet and import tools expect CSV (filename, code type, raw value, corrected value, timestamp). The MVP should add CSV beside the current JSON download, generated from saved rows rather than from whatever the browser still has in memory.

### 5. Failures look like success

`/api/health` does not check that the Tesseract binary runs or that the `spa` language data is installed. `config.TESSERACT_CMD` is never applied in `app.py`; the process relies on `PATH`. Startup only logs a warning if Tesseract is missing, then keeps serving. The progress bar in `static/app.js` advances on a timer up to 90 percent and is not tied to the request. A photo with no code still returns `success: true`.

The MVP health check should fail when OCR cannot run. The UI should show per-file status: accepted, unreadable, or rejected. Progress should reflect the upload request, or be removed.

### 6. The documented runtime and the real runtime differ

`gunicorn.conf.py` exists, but the image command is `python app.py`. Compose sets `FLASK_ENV=production` while the dev server is what actually listens. Nginx is configured to alias `/uploads` and `/results` from `/app/...` inside the nginx container, and those paths are not mounted there. `OCR_LANGUAGE` in config defaults to `spa+eng`, while extraction hardcodes `-l spa`. Tests in `test_app.py` assume a server on port 8000 and write a sample image to `/tmp`, which is not a Windows path.

The MVP deploy should be one command that matches the README: the process that serves traffic should be the one the docs describe, health should pass inside that process, and one automated test should upload a fixture image and assert a known code. Pinning that test to Docker (Python 3.11, the version the image uses) matters because this workstation only has Python 3.13, which cannot install the pinned `numpy`, `opencv-python`, and `Pillow` versions.

### 7. The happy path is not safe enough to leave running

`SECRET_KEY` falls back to `dev-secret-key-change-in-production`. CORS defaults to `*`. Uploaded files are kept with no retention limit and no virus or content check beyond the extension. There is no authentication. For a single-operator MVP on a private network, full accounts are optional. A shared secret or a single local login, a non-default secret in production, and a cap or cleanup for `uploads/` are not.

## Explicitly out of scope for the MVP

These are real follow-ups. They are not required to prove the product:

- User accounts, roles, and audit logs beyond a single operator
- Mobile apps
- Cloud storage and multi-node queues
- A live analytics dashboard
- Replacing Tesseract with a custom model
- ERP or WMS connectors
- Internationalization beyond Spanish and English labels already implied by the OCR config

## Suggested order

1. Wire Tesseract from configuration and make `/api/health` report it.
2. Add barcode/QR decoding and stop treating regex hits as confirmed codes.
3. Add the review-and-correct screen.
4. Persist confirmed rows in SQLite and list recent batches.
5. Export CSV from stored rows.
6. Replace the simulated progress indicator and add one Docker-based smoke test with a fixture image.

That sequence turns the current demo into something an operator can finish a count with.
