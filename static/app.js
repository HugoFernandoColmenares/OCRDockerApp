// Variables globales
let selectedFiles = [];
let processingResults = [];
let processingStartTime = null;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    // Eventos de drag and drop
    uploadZone.addEventListener('dragover', handleDragOver);
    uploadZone.addEventListener('dragleave', handleDragLeave);
    uploadZone.addEventListener('drop', handleDrop);
    
    // Evento de selección de archivos
    fileInput.addEventListener('change', handleFileSelect);
    
    // Animaciones iniciales
    animateElements();
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    handleFiles(files);
}

function handleFiles(files) {
    // Filtrar solo archivos de imagen
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length === 0) {
        showNotification('Por favor selecciona archivos de imagen válidos.', 'error');
        return;
    }
    
    selectedFiles = imageFiles;
    displayFileList();
    
    // Habilitar botón de procesamiento
    document.getElementById('processBtn').disabled = false;
}

function displayFileList() {
    const fileList = document.getElementById('fileList');
    const fileNames = document.getElementById('fileNames');
    
    if (selectedFiles.length > 0) {
        fileList.classList.remove('hidden');
        fileNames.innerHTML = selectedFiles
            .map(file => `<span class="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-2 mb-1">${file.name}</span>`)
            .join('');
    } else {
        fileList.classList.add('hidden');
    }
}

async function processFiles() {
    if (selectedFiles.length === 0) {
        showNotification('Por favor selecciona archivos primero.', 'error');
        return;
    }
    
    // Mostrar sección de carga
    document.getElementById('loadingSection').classList.remove('hidden');
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('statsSection').classList.add('hidden');
    
    // Deshabilitar botón de procesamiento
    document.getElementById('processBtn').disabled = true;
    
    processingStartTime = Date.now();
    
    try {
        // Crear FormData para enviar archivos
        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        // Simular progreso de carga
        simulateProgress();
        
        // Enviar petición al servidor
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Error en el procesamiento');
        }
        
        const data = await response.json();
        
        if (data.success) {
            processingResults = data.results;
            displayResults();
            updateStatistics();
            showNotification('Procesamiento completado exitosamente!', 'success');
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
        
    } catch (error) {
        console.error('Error:', error);
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        // Ocultar sección de carga
        document.getElementById('loadingSection').classList.add('hidden');
        // Habilitar botón de procesamiento
        document.getElementById('processBtn').disabled = false;
    }
}

function simulateProgress() {
    const progressBar = document.getElementById('progressBar');
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 90) progress = 90;
        
        progressBar.style.width = `${progress}%`;
        
        if (progress >= 90) {
            clearInterval(interval);
        }
    }, 200);
}

function displayResults() {
    const container = document.getElementById('resultsContainer');
    const resultsSection = document.getElementById('resultsSection');
    
    container.innerHTML = '';
    
    processingResults.forEach((result, index) => {
        const resultCard = createResultCard(result, index);
        container.appendChild(resultCard);
    });
    
    resultsSection.classList.remove('hidden');
    
    // Animar las tarjetas de resultados
    anime({
        targets: '.result-card',
        translateY: [50, 0],
        opacity: [0, 1],
        delay: anime.stagger(100),
        duration: 600,
        easing: 'easeOutQuart'
    });
}

function createResultCard(result, index) {
    const card = document.createElement('div');
    card.className = 'result-card bg-gray-50 rounded-lg p-4 border border-gray-200';
    
    if (result.error) {
        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-medium text-red-600">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    ${result.original_filename}
                </h3>
                <span class="text-xs text-red-500">Error</span>
            </div>
            <p class="text-sm text-red-500">${result.error}</p>
        `;
    } else {
        const codes = result.ocr_result.extracted_codes;
        const hasCodes = Object.keys(codes).length > 0;
        
        card.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="font-medium text-gray-800">
                    <i class="fas fa-image mr-2 text-blue-600"></i>
                    ${result.original_filename}
                </h3>
                <div class="flex items-center space-x-2">
                    <span class="text-xs px-2 py-1 rounded ${getConfidenceColor(result.ocr_result.confidence)}">
                        ${result.ocr_result.confidence}
                    </span>
                    <span class="text-xs text-gray-500">
                        ${(result.file_size / 1024).toFixed(1)} KB
                    </span>
                </div>
            </div>
            
            ${hasCodes ? `
                <div class="mb-3">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Códigos Extraídos:</h4>
                    <div class="space-y-1">
                        ${Object.entries(codes).map(([type, values]) => `
                            <div class="flex items-center justify-between">
                                <span class="text-xs text-gray-600 capitalize">${type.replace('_', ' ')}:</span>
                                <div class="flex flex-wrap gap-1">
                                    ${values.map(code => `
                                        <span class="code-highlight text-xs px-2 py-1 bg-blue-100 rounded">${code}</span>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : `
                <div class="text-sm text-gray-500 mb-3">
                    <i class="fas fa-info-circle mr-1"></i>
                    No se encontraron códigos en esta imagen
                </div>
            `}
            
            <details class="text-xs">
                <summary class="cursor-pointer text-blue-600 hover:text-blue-800">
                    Ver texto completo extraído
                </summary>
                <div class="mt-2 p-2 bg-white rounded border text-gray-700 max-h-32 overflow-y-auto">
                    ${result.ocr_result.raw_text || 'Sin texto detectado'}
                </div>
            </details>
        `;
    }
    
    return card;
}

function getConfidenceColor(confidence) {
    switch (confidence) {
        case 'high': return 'bg-green-100 text-green-800';
        case 'medium': return 'bg-yellow-100 text-yellow-800';
        case 'low': return 'bg-red-100 text-red-800';
        default: return 'bg-gray-100 text-gray-800';
    }
}

function updateStatistics() {
    const statsSection = document.getElementById('statsSection');
    const totalImages = document.getElementById('totalImages');
    const totalCodes = document.getElementById('totalCodes');
    const processingTime = document.getElementById('processingTime');
    
    // Calcular estadísticas
    const successfulResults = processingResults.filter(r => !r.error);
    const totalCodesCount = successfulResults.reduce((count, result) => {
        const codes = result.ocr_result.extracted_codes;
        return count + Object.values(codes).reduce((sum, arr) => sum + arr.length, 0);
    }, 0);
    
    const timeElapsed = processingStartTime ? ((Date.now() - processingStartTime) / 1000).toFixed(1) : 0;
    
    // Actualizar UI
    totalImages.textContent = successfulResults.length;
    totalCodes.textContent = totalCodesCount;
    processingTime.textContent = `${timeElapsed}s`;
    
    statsSection.classList.remove('hidden');
    
    // Animar estadísticas
    anime({
        targets: '#statsSection .bg-white',
        scale: [0.8, 1],
        opacity: [0, 1],
        delay: anime.stagger(100),
        duration: 600,
        easing: 'easeOutBack'
    });
}

async function downloadResults() {
    if (processingResults.length === 0) {
        showNotification('No hay resultados para descargar.', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/download-json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ results: processingResults })
        });
        
        if (!response.ok) {
            throw new Error('Error al generar archivo');
        }
        
        // Descargar archivo
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ocr_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showNotification('Archivo descargado exitosamente!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al descargar archivo.', 'error');
    }
}

function showNotification(message, type = 'info') {
    // Crear notificación
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${getNotificationColor(type)}`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${getNotificationIcon(type)} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animar entrada
    anime({
        targets: notification,
        translateX: [300, 0],
        opacity: [0, 1],
        duration: 300,
        easing: 'easeOutQuart'
    });
    
    // Remover después de 3 segundos
    setTimeout(() => {
        anime({
            targets: notification,
            translateX: [0, 300],
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuart',
            complete: () => {
                document.body.removeChild(notification);
            }
        });
    }, 3000);
}

function getNotificationColor(type) {
    switch (type) {
        case 'success': return 'bg-green-500 text-white';
        case 'error': return 'bg-red-500 text-white';
        case 'warning': return 'bg-yellow-500 text-white';
        default: return 'bg-blue-500 text-white';
    }
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-circle';
        case 'warning': return 'fa-exclamation-triangle';
        default: return 'fa-info-circle';
    }
}

function animateElements() {
    // Animar header
    anime({
        targets: 'header',
        translateY: [-50, 0],
        opacity: [0, 1],
        duration: 800,
        easing: 'easeOutQuart'
    });
    
    // Animar secciones principales
    anime({
        targets: 'main section',
        translateY: [30, 0],
        opacity: [0, 1],
        delay: anime.stagger(200, {start: 300}),
        duration: 600,
        easing: 'easeOutQuart'
    });
    
    // Animar footer
    anime({
        targets: 'footer',
        translateY: [50, 0],
        opacity: [0, 1],
        delay: 1000,
        duration: 600,
        easing: 'easeOutQuart'
    });
}