// ─────────────────────────────────────────────────────────────────────────────
// Meridian Web UI - JavaScript
// Handles file upload, form interaction, API calls, and progress tracking
// ─────────────────────────────────────────────────────────────────────────────

// ─── State Management ──────────────────────────────────────────────────────────
const state = {
    selectedFile: null,
    isProcessing: false,
    showApiKey: false
};

// ─── DOM Elements ──────────────────────────────────────────────────────────────
const elements = {
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    selectedFileInfo: document.getElementById('selectedFileInfo'),
    selectedFileName: document.getElementById('selectedFileName'),
    selectedFileSize: document.getElementById('selectedFileSize'),
    clearFileBtn: document.getElementById('clearFile'),
    
    minSlides: document.getElementById('minSlides'),
    maxSlides: document.getElementById('maxSlides'),
    minSlidesValue: document.getElementById('minSlidesValue'),
    maxSlidesValue: document.getElementById('maxSlidesValue'),
    model: document.getElementById('model'),
    apiKey: document.getElementById('apiKey'),
    toggleApiKeyBtn: document.getElementById('toggleApiKey'),
    
    convertBtn: document.getElementById('convertBtn'),
    btnSpinner: document.querySelector('.btn-spinner'),
    progressSection: document.getElementById('progressSection'),
    successSection: document.getElementById('successSection'),
    errorSection: document.getElementById('errorSection'),
    
    downloadBtn: document.getElementById('downloadBtn'),
    startNewBtn: document.getElementById('startNewBtn'),
    tryAgainBtn: document.getElementById('tryAgainBtn'),
    
    successMessage: document.getElementById('successMessage'),
    errorMessage: document.getElementById('errorMessage'),
    progressFill: document.getElementById('progressFill')
};

// ─── Initialize ───────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupDropZone();
    setupFileInput();
    setupFormInputs();
    setupButtons();
    updateConvertButtonState();
});

// ─── Drop Zone Setup ───────────────────────────────────────────────────────────
function setupDropZone() {
    const zone = elements.dropZone;
    
    zone.addEventListener('click', () => {
        elements.fileInput.click();
    });
    
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
    });
    
    zone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
    });
    
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
}

// ─── File Input Setup ──────────────────────────────────────────────────────────
function setupFileInput() {
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

// ─── File Selection Handler ───────────────────────────────────────────────────
function handleFileSelect(file) {
    // Validate file type
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    const allowedExt = ['.md', '.markdown', '.txt'];
    
    if (!allowedExt.includes(ext)) {
        showError(`Invalid file type: ${ext}`);
        return;
    }
    
    state.selectedFile = file;
    
    // Update UI
    elements.selectedFileName.textContent = file.name;
    elements.selectedFileSize.textContent = formatFileSize(file.size);
    elements.selectedFileInfo.classList.remove('d-none');
    elements.dropZone.classList.add('d-none');
    
    updateConvertButtonState();
}

// ─── Clear File Selection ──────────────────────────────────────────────────────
function clearFile() {
    state.selectedFile = null;
    elements.fileInput.value = '';
    elements.selectedFileInfo.classList.add('d-none');
    elements.dropZone.classList.remove('d-none');
    updateConvertButtonState();
}

// ─── Form Inputs Setup ────────────────────────────────────────────────────────
function setupFormInputs() {
    elements.minSlides.addEventListener('change', (e) => {
        elements.minSlidesValue.textContent = e.target.value;
        // Ensure min <= max
        if (parseInt(e.target.value) > parseInt(elements.maxSlides.value)) {
            elements.maxSlides.value = e.target.value;
            elements.maxSlidesValue.textContent = e.target.value;
        }
    });
    
    elements.maxSlides.addEventListener('change', (e) => {
        elements.maxSlidesValue.textContent = e.target.value;
        // Ensure max >= min
        if (parseInt(e.target.value) < parseInt(elements.minSlides.value)) {
            elements.minSlides.value = e.target.value;
            elements.minSlidesValue.textContent = e.target.value;
        }
    });
    
    elements.toggleApiKeyBtn.addEventListener('click', () => {
        state.showApiKey = !state.showApiKey;
        elements.apiKey.type = state.showApiKey ? 'text' : 'password';
        elements.toggleApiKeyBtn.textContent = state.showApiKey ? '🙈' : '👁️';
    });
}

// ─── Buttons Setup ────────────────────────────────────────────────────────────
function setupButtons() {
    elements.convertBtn.addEventListener('click', handleConvert);
    elements.clearFileBtn.addEventListener('click', clearFile);
    elements.downloadBtn.addEventListener('click', (e) => {
        if (elements.downloadBtn.href) {
            // Let the browser handle the download
        }
    });
    elements.startNewBtn.addEventListener('click', resetUI);
    elements.tryAgainBtn.addEventListener('click', resetUI);
}

// ─── Update Convert Button State ───────────────────────────────────────────────
function updateConvertButtonState() {
    const enabled = state.selectedFile !== null && !state.isProcessing;
    elements.convertBtn.disabled = !enabled;
    if (state.isProcessing) {
        elements.btnSpinner.classList.remove('d-none');
    } else {
        elements.btnSpinner.classList.add('d-none');
    }
}

// ─── Convert Handler ──────────────────────────────────────────────────────────
async function handleConvert(e) {
    e.preventDefault();
    
    if (state.isProcessing || !state.selectedFile) {
        return;
    }
    
    state.isProcessing = true;
    updateConvertButtonState();
    
    // Hide all sections and show progress
    document.getElementById('uploadSection').classList.add('d-none');
    document.getElementById('configSection').classList.add('d-none');
    elements.successSection.classList.add('d-none');
    elements.errorSection.classList.add('d-none');
    elements.progressSection.classList.remove('d-none');
    
    // Reset progress
    elements.progressFill.style.width = '0%';
    updateStage('validate', 'active');
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', state.selectedFile);
        formData.append('minSlides', elements.minSlides.value);
        formData.append('maxSlides', elements.maxSlides.value);
        formData.append('model', elements.model.value);
        
        const apiKey = elements.apiKey.value.trim();
        if (apiKey) {
            formData.append('apiKey', apiKey);
        }
        
        // Call API
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });
        
        // Update progress
        updateStage('validate', 'completed');
        updateStage('parse', 'active');
        elements.progressFill.style.width = '20%';
        
        await sleep(500);
        updateStage('parse', 'completed');
        updateStage('structure', 'active');
        elements.progressFill.style.width = '40%';
        
        await sleep(500);
        updateStage('structure', 'completed');
        updateStage('render', 'active');
        elements.progressFill.style.width = '60%';
        
        await sleep(500);
        updateStage('render', 'completed');
        updateStage('save', 'active');
        elements.progressFill.style.width = '80%';
        
        // Handle response
        const data = await response.json();
        
        await sleep(500);
        updateStage('save', 'completed');
        elements.progressFill.style.width = '100%';
        
        if (data.success) {
            // Show success
            await sleep(1000);
            showSuccess(data, formData);
        } else {
            showConversionError(data.error);
        }
        
    } catch (error) {
        showConversionError(error.message || 'Conversion failed');
    } finally {
        state.isProcessing = false;
        updateConvertButtonState();
    }
}

// ─── Show Success ──────────────────────────────────────────────────────────────
function showSuccess(data, formData) {
    elements.progressSection.classList.add('d-none');
    elements.successSection.classList.remove('d-none');
    
    elements.successMessage.textContent = 
        `Your presentation is ready! (${data.size_mb} MB)`;
    
    elements.downloadBtn.href = data.download_url;
    elements.downloadBtn.download = data.filename;
}

// ─── Show Conversion Error ────────────────────────────────────────────────────
function showConversionError(errorMsg) {
    elements.progressSection.classList.add('d-none');
    elements.errorSection.classList.remove('d-none');
    
    elements.errorMessage.textContent = errorMsg;
}

// ─── Show Error Alert ─────────────────────────────────────────────────────────
function showError(message) {
    alert(`⚠️ ${message}`);
}

// ─── Reset UI ─────────────────────────────────────────────────────────────────
function resetUI() {
    clearFile();
    
    // Reset form
    elements.minSlides.value = '10';
    elements.maxSlides.value = '15';
    elements.minSlidesValue.textContent = '10';
    elements.maxSlidesValue.textContent = '15';
    elements.model.value = 'gemini-2.0-flash';
    elements.apiKey.value = '';
    
    // Show upload/config, hide others
    document.getElementById('uploadSection').classList.remove('d-none');
    document.getElementById('configSection').classList.remove('d-none');
    elements.progressSection.classList.add('d-none');
    elements.successSection.classList.add('d-none');
    elements.errorSection.classList.add('d-none');
    
    state.isProcessing = false;
    updateConvertButtonState();
}

// ─── Stage Update ────────────────────────────────────────────────────────────
function updateStage(stageName, status) {
    const stageEl = document.getElementById(`stage-${stageName}`);
    if (!stageEl) return;
    
    // Remove all status classes
    stageEl.classList.remove('active', 'completed');
    
    // Update icon
    const icon = stageEl.querySelector('.stage-icon');
    if (status === 'active') {
        stageEl.classList.add('active');
        icon.textContent = '⏳';
    } else if (status === 'completed') {
        stageEl.classList.add('completed');
        icon.textContent = '✓';
    } else {
        icon.textContent = '⏳';
    }
}

// ─── Utility Functions ────────────────────────────────────────────────────────

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
