let selectedFiles = [];
let currentBatchId = null;

document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.addEventListener('dragover', function(event) {
        event.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', function(event) {
        event.preventDefault();
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', function(event) {
        event.preventDefault();
        uploadZone.classList.remove('dragover');
        handleFiles(Array.from(event.dataTransfer.files));
    });
    uploadZone.addEventListener('click', function(event) {
        if (event.target.id === 'selectBtn') {
            return;
        }
    });
    document.getElementById('selectBtn').addEventListener('click', function() {
        fileInput.click();
    });
    fileInput.addEventListener('change', function(event) {
        handleFiles(Array.from(event.target.files));
    });
    document.getElementById('processBtn').addEventListener('click', processFiles);
    document.getElementById('confirmBtn').addEventListener('click', confirmBatch);
    document.getElementById('downloadCsvBtn').addEventListener('click', function() {
        downloadExport('csv');
    });
    document.getElementById('downloadJsonBtn').addEventListener('click', function() {
        downloadExport('json');
    });
    document.getElementById('logoutBtn').addEventListener('click', logout);

    checkHealth();
    loadBatches();
});

function handleFiles(files) {
    const imageFiles = files.filter(function(file) { return file.type.startsWith('image/'); });
    if (imageFiles.length === 0) {
        showNotification('Selecciona archivos de imagen válidos.', 'error');
        return;
    }
    selectedFiles = imageFiles;
    const fileList = document.getElementById('fileList');
    const fileNames = document.getElementById('fileNames');
    fileList.classList.remove('hidden');
    fileNames.textContent = imageFiles.map(function(file) { return file.name; }).join(', ');
    document.getElementById('processBtn').disabled = false;
}

function processFiles() {
    if (selectedFiles.length === 0) {
        showNotification('Selecciona archivos primero.', 'error');
        return;
    }

    const formData = new FormData();
    selectedFiles.forEach(function(file) { formData.append('files', file); });

    document.getElementById('loadingSection').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('processBtn').disabled = true;
    setProgress(0, 'Subiendo imágenes...');

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.upload.onprogress = function(event) {
        if (!event.lengthComputable) {
            return;
        }
        const percent = Math.round((event.loaded / event.total) * 100);
        setProgress(percent, percent >= 100 ? 'Procesando imágenes...' : 'Subiendo imágenes...');
    };
    xhr.onload = function() {
        document.getElementById('loadingSection').classList.add('hidden');
        document.getElementById('processBtn').disabled = false;
        if (xhr.status === 401) {
            window.location.href = '/login';
            return;
        }
        if (xhr.status < 200 || xhr.status >= 300) {
            showNotification(readError(xhr) || 'Error en el procesamiento', 'error');
            return;
        }
        const data = JSON.parse(xhr.responseText);
        showBatch({
            id: data.batch_id,
            items: data.results,
            accepted_count: data.accepted_count,
            unreadable_count: data.unreadable_count,
            rejected_count: data.rejected_count,
            confirmed_count: 0
        });
        if (data.unreadable_count > 0 || data.rejected_count > 0) {
            showNotification('Hay imágenes sin lectura o rechazadas. Revísalas antes de confirmar.', 'warning');
        } else {
            showNotification('Imágenes listas para revisión.', 'success');
        }
        loadBatches();
    };
    xhr.onerror = function() {
        document.getElementById('loadingSection').classList.add('hidden');
        document.getElementById('processBtn').disabled = false;
        showNotification('Error de red al subir las imágenes.', 'error');
    };
    xhr.send(formData);
}

function setProgress(percent, label) {
    document.getElementById('progressBar').style.width = percent + '%';
    document.getElementById('progressLabel').textContent = label;
}

function showBatch(batch) {
    currentBatchId = batch.id;
    const container = document.getElementById('resultsContainer');
    container.innerHTML = '';
    (batch.items || []).forEach(function(item) {
        container.appendChild(createReviewRow(item));
    });
    document.getElementById('acceptedCount').textContent = batch.accepted_count || 0;
    document.getElementById('unreadableCount').textContent = batch.unreadable_count || 0;
    document.getElementById('rejectedCount').textContent = batch.rejected_count || 0;
    document.getElementById('resultsSection').classList.remove('hidden');
    document.getElementById('statsSection').classList.remove('hidden');
    const exportReady = (batch.confirmed_count || 0) > 0;
    document.getElementById('downloadCsvBtn').disabled = !exportReady;
    document.getElementById('downloadJsonBtn').disabled = !exportReady;
}

function createReviewRow(item) {
    const card = document.createElement('div');
    card.className = 'result-card review-row bg-gray-50 rounded-lg p-4 border border-gray-200';
    card.dataset.id = item.id;

    const meta = statusMeta(item.status);
    const proposed = item.corrected_code || item.proposed_code || '';
    const others = (item.candidates || [])
        .map(function(candidate) { return candidate.value; })
        .filter(function(value) { return value && value !== item.proposed_code; });

    const title = document.createElement('div');
    title.className = 'flex items-center justify-between mb-3 gap-3';
    const name = document.createElement('h3');
    name.className = 'font-medium text-gray-800';
    name.textContent = item.original_filename;
    const badge = document.createElement('span');
    badge.className = 'text-xs px-2 py-1 rounded ' + meta.className;
    badge.textContent = meta.label;
    title.appendChild(name);
    title.appendChild(badge);

    const fields = document.createElement('div');
    fields.className = 'grid grid-cols-1 md:grid-cols-2 gap-3';
    const proposal = document.createElement('p');
    proposal.className = 'text-sm text-gray-600';
    proposal.textContent = 'Propuesto (' + (item.code_type || 'sin tipo') + ', ' + (item.confidence || 'unreadable') + '): ' + (item.proposed_code || '—');

    const label = document.createElement('label');
    label.className = 'block text-sm text-gray-700';
    label.textContent = 'Código corregido';
    const input = document.createElement('input');
    input.type = 'text';
    input.value = proposed;
    input.className = 'corrected mt-1 w-full border border-gray-300 rounded px-2 py-1';
    label.appendChild(input);

    const discardLabel = document.createElement('label');
    discardLabel.className = 'flex items-center gap-2 text-sm text-gray-600 mt-3';
    const discard = document.createElement('input');
    discard.type = 'checkbox';
    discard.className = 'discard';
    discardLabel.appendChild(discard);
    discardLabel.appendChild(document.createTextNode('Descartar esta fila'));

    fields.appendChild(proposal);
    const editor = document.createElement('div');
    editor.appendChild(label);
    editor.appendChild(discardLabel);
    fields.appendChild(editor);

    card.appendChild(title);
    card.appendChild(fields);

    if (others.length > 0) {
        const extra = document.createElement('p');
        extra.className = 'text-xs text-gray-500 mt-2';
        extra.textContent = 'Otras lecturas: ' + others.join(', ');
        card.appendChild(extra);
    }
    if (item.error) {
        const error = document.createElement('p');
        error.className = 'text-xs text-red-600 mt-2';
        error.textContent = item.error;
        card.appendChild(error);
    }
    if (item.raw_text) {
        const details = document.createElement('details');
        details.className = 'text-xs mt-2';
        const summary = document.createElement('summary');
        summary.className = 'cursor-pointer text-blue-600';
        summary.textContent = 'Ver texto OCR';
        const pre = document.createElement('pre');
        pre.className = 'mt-2 p-2 bg-white rounded border whitespace-pre-wrap';
        pre.textContent = item.raw_text;
        details.appendChild(summary);
        details.appendChild(pre);
        card.appendChild(details);
    }
    return card;
}

function statusMeta(status) {
    if (status === 'accepted') {
        return { label: 'Aceptada', className: 'bg-green-100 text-green-800' };
    }
    if (status === 'unreadable') {
        return { label: 'Sin lectura', className: 'bg-yellow-100 text-yellow-800' };
    }
    return { label: 'Rechazada', className: 'bg-red-100 text-red-800' };
}

async function confirmBatch() {
    if (!currentBatchId) {
        return;
    }
    const items = [];
    const rows = document.querySelectorAll('.review-row');
    for (const row of rows) {
        if (row.querySelector('.discard').checked) {
            continue;
        }
        const corrected = row.querySelector('.corrected').value.trim();
        if (!corrected) {
            showNotification('Escribe un código o marca la fila como descartada.', 'warning');
            return;
        }
        items.push({ id: row.dataset.id, corrected_code: corrected });
    }
    if (items.length === 0) {
        showNotification('No hay filas para confirmar.', 'warning');
        return;
    }

    const response = await fetch('/api/batches/' + currentBatchId + '/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: items })
    });
    if (response.status === 401) {
        window.location.href = '/login';
        return;
    }
    const data = await response.json();
    if (!response.ok) {
        showNotification(data.error || 'No se pudo confirmar el lote', 'error');
        return;
    }
    showBatch(data);
    showNotification('Lote guardado. Ya puedes exportarlo.', 'success');
    loadBatches();
}

async function downloadExport(kind) {
    if (!currentBatchId) {
        return;
    }
    const response = await fetch('/api/batches/' + currentBatchId + '/export.' + kind);
    if (response.status === 401) {
        window.location.href = '/login';
        return;
    }
    if (!response.ok) {
        const data = await response.json();
        showNotification(data.error || 'No se pudo exportar', 'error');
        return;
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ocr_results_' + currentBatchId.slice(0, 8) + '.' + kind;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
}

async function loadBatches() {
    const response = await fetch('/api/batches');
    if (response.status === 401) {
        window.location.href = '/login';
        return;
    }
    const data = await response.json();
    const list = document.getElementById('batchList');
    list.innerHTML = '';
    if (!data.batches || data.batches.length === 0) {
        list.textContent = 'Todavía no hay lotes guardados.';
        return;
    }
    data.batches.forEach(function(batch) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'block w-full text-left border border-gray-200 rounded-lg px-3 py-2 mb-2 hover:bg-gray-50';
        button.textContent = batch.created_at + ' · ' + batch.total + ' imágenes · ' + batch.confirmed + ' confirmadas';
        button.addEventListener('click', function() { openBatch(batch.id); });
        list.appendChild(button);
    });
}

async function openBatch(batchId) {
    const response = await fetch('/api/batches/' + batchId);
    if (!response.ok) {
        showNotification('No se pudo abrir el lote', 'error');
        return;
    }
    showBatch(await response.json());
}

async function checkHealth() {
    const response = await fetch('/api/health');
    const banner = document.getElementById('healthBanner');
    if (response.ok) {
        banner.classList.add('hidden');
        return;
    }
    let detail = 'OCR no disponible.';
    try {
        const data = await response.json();
        detail = (data.tesseract && data.tesseract.error) || data.status || detail;
    } catch (error) {
        detail = 'OCR no disponible.';
    }
    banner.textContent = 'El servicio de lectura no está listo: ' + detail;
    banner.classList.remove('hidden');
}

async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    window.location.href = '/login';
}

function readError(xhr) {
    try {
        return JSON.parse(xhr.responseText).error;
    } catch (error) {
        return '';
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    const colors = {
        success: 'bg-green-600',
        error: 'bg-red-600',
        warning: 'bg-yellow-600',
        info: 'bg-blue-600'
    };
    notification.className = 'fixed top-4 right-4 z-50 text-white px-4 py-3 rounded-lg shadow-lg ' + (colors[type] || colors.info);
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(function() { notification.remove(); }, 3500);
}
