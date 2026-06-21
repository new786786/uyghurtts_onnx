// ===================== DOM元素 =====================
const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const synthesizeBtn = document.getElementById('synthesize-btn');
const audioUpload = document.getElementById('audio-upload');
const fileName = document.getElementById('file-name');
const voiceChangeBtn = document.getElementById('voice-change-btn');
const pitchSlider = document.getElementById('pitch');
const pitchValue = document.getElementById('pitch-value');
const indexRateSlider = document.getElementById('index-rate');
const indexRateValue = document.getElementById('index-rate-value');
const protectSlider = document.getElementById('protect');
const protectValue = document.getElementById('protect-value');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loading-text');
const errorMessage = document.getElementById('error-message');
const resultSection = document.getElementById('result-section');
const audioPlayer = document.getElementById('audio-player');
const resultInfo = document.getElementById('result-info');
const downloadBtn = document.getElementById('download-btn');
const resetBtn = document.getElementById('reset-btn');

// ===================== 状态变量 =====================
let currentAudioUrl = null;
let currentFilename = null;
let selectedFile = null;

// ===================== 事件监听 =====================
textInput.addEventListener('input', () => {
    charCount.textContent = textInput.value.length;
    updateVoiceChangeBtnState();
});

synthesizeBtn.addEventListener('click', handleSynthesize);

audioUpload.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        selectedFile = e.target.files[0];
        fileName.textContent = selectedFile.name;
    }
    updateVoiceChangeBtnState();
});

pitchSlider.addEventListener('input', () => {
    pitchValue.textContent = pitchSlider.value;
});

indexRateSlider.addEventListener('input', () => {
    indexRateValue.textContent = indexRateSlider.value;
});

protectSlider.addEventListener('input', () => {
    protectValue.textContent = protectSlider.value;
});

voiceChangeBtn.addEventListener('click', handleVoiceChange);
downloadBtn.addEventListener('click', handleDownload);
resetBtn.addEventListener('click', handleReset);

// ===================== 辅助函数 =====================
function updateVoiceChangeBtnState() {
    // 变声按钮启用条件：有文本 或 有选择音频文件
    const hasText = textInput.value.trim().length > 0;
    const hasAudio = selectedFile !== null;
    voiceChangeBtn.disabled = !(hasText || hasAudio);
}

// ===================== 处理函数 =====================
async function handleSynthesize() {
    const text = textInput.value.trim();
    
    if (!text) {
        showError('تېكىسىت كىرگۈزۇڭ');
        return;
    }

    hideError();
    hideResult();
    showLoading('سەل ساقلاڭ...');
    synthesizeBtn.disabled = true;
    voiceChangeBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('text', text);

        const response = await fetch('/api/tts', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'مەغلۇپ بولدى');
        }

        currentAudioUrl = data.audio_url;
        currentFilename = data.filename;
        
        audioPlayer.src = currentAudioUrl;
        showResult('语音合成成功！');
    } catch (error) {
        showError(error.message || '网络错误，请重试');
    } finally {
        hideLoading();
        synthesizeBtn.disabled = false;
        updateVoiceChangeBtnState();
    }
}

async function handleVoiceChange() {
    const text = textInput.value.trim();
    const hasText = text.length > 0;
    const hasAudio = selectedFile !== null;

    if (!hasText && !hasAudio) {
        showError('تېكىسىت ياكى ئاۋاز ھەققىنى تاللاش كېرەك');
        return;
    }

    hideError();
    hideResult();
    showLoading('ئاۋاز بىرىكتۇرۈلىۋاتىدۇ...');
    synthesizeBtn.disabled = true;
    voiceChangeBtn.disabled = true;

    try {
        const formData = new FormData();
        
        if (hasAudio) {
            // 有选择音频：对音频进行变声
            formData.append('file', selectedFile);
        } else {
            // 无音频：对文本进行合成+变声
            formData.append('text', text);
        }
        
        formData.append('pitch', pitchSlider.value);
        formData.append('index_rate', indexRateSlider.value);
        formData.append('protect', protectSlider.value);
        formData.append('rms_mix_rate', '0.25');

        const response = await fetch('/api/tts-and-voice-change', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'مەغلۇپ بولدى');
        }

        currentAudioUrl = data.audio_url;
        currentFilename = data.filename;
        
        audioPlayer.src = currentAudioUrl;
        showResult('ئاۋاز بىرىكتۇرۇش مۇۋەپپەقىيەتلىك بولدى!');
    } catch (error) {
        showError(error.message || 'تور خاتالىقى، قايتا سىناڭ');
    } finally {
        hideLoading();
        synthesizeBtn.disabled = false;
        updateVoiceChangeBtnState();
    }
}

function handleDownload() {
    if (!currentAudioUrl) return;

    const link = document.createElement('a');
    link.href = currentAudioUrl;
    link.download = currentFilename || 'output.wav';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function handleReset() {
    textInput.value = '';
    charCount.textContent = '0';
    audioUpload.value = '';
    fileName.textContent = '选择音频文件 (WAV)';
    selectedFile = null;
    pitchSlider.value = 0;
    pitchValue.textContent = '0';
    indexRateSlider.value = 0.5;
    indexRateValue.textContent = '0.5';
    protectSlider.value = 0.1;
    protectValue.textContent = '0.1';
    hideResult();
    hideError();
    audioPlayer.src = '';
    currentAudioUrl = null;
    currentFilename = null;
    updateVoiceChangeBtnState();
}

// ===================== UI控制函数 =====================
function showLoading(text) {
    loadingText.textContent = text;
    loading.classList.remove('hidden');
}

function hideLoading() {
    loading.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

function hideError() {
    errorMessage.classList.add('hidden');
}

function showResult(info) {
    resultInfo.textContent = info;
    resultSection.classList.remove('hidden');
}

function hideResult() {
    resultSection.classList.add('hidden');
}
