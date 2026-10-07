const originalEl = document.getElementById('original');
const translatedEl = document.getElementById('translated');
const statusEl = document.getElementById('status');
const toggleBtn = document.getElementById('toggle-btn');
const settingsBtn = document.getElementById('settings-btn');
const subtitleContainer = document.getElementById('subtitle-container');
const controlsEl = document.getElementById('controls');

let subtitlesEnabled = true;
let ws = null;

// === УПРАВЛЕНИЕ КЛИКАМИ ===
// Включаем приём кликов при наведении на интерактивные элементы
function enableMouseEvents() {
    window.electronAPI.setIgnoreMouseEvents(false);
}

function disableMouseEvents() {
    window.electronAPI.setIgnoreMouseEvents(true, { forward: true });
}

// Панель управления (кнопки) — всегда интерактивна
controlsEl.addEventListener('mouseenter', enableMouseEvents);
controlsEl.addEventListener('mouseleave', disableMouseEvents);

// Контейнер субтитров — интерактивен только когда субтитры включены
subtitleContainer.addEventListener('mouseenter', () => {
    if (subtitlesEnabled) {
        enableMouseEvents();
    }
});
subtitleContainer.addEventListener('mouseleave', () => {
    if (subtitlesEnabled) {
        disableMouseEvents();
    }
});

// === ПЕРЕКЛЮЧЕНИЕ СУБТИТРОВ ===
toggleBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    subtitlesEnabled = !subtitlesEnabled;
    toggleBtn.textContent = `Субтитры: ${subtitlesEnabled ? 'ВКЛ' : 'ВЫКЛ'}`;
    toggleBtn.classList.toggle('active', subtitlesEnabled);
    
    if (subtitlesEnabled) {
        subtitleContainer.classList.remove('hidden');
        subtitleContainer.classList.add('visible');
    } else {
        subtitleContainer.classList.remove('visible');
        subtitleContainer.classList.add('hidden');
    }
});

// === ОТКРЫТИЕ НАСТРОЕК ===
settingsBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    console.log('[renderer] Открытие настроек');
    window.electronAPI.openSettings();
});

// === WEBSOCKET ===
function connect() {
    ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
        statusEl.textContent = '🟢 Подключено';
        if (subtitlesEnabled) {
            translatedEl.textContent = '🎧 Слушаю...';
            originalEl.textContent = '';
        }
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'subtitle' && subtitlesEnabled) {
                originalEl.textContent = data.original || '';
                translatedEl.textContent = data.translated || '';
            } else if (data.type === 'status' && subtitlesEnabled) {
                translatedEl.textContent = data.text;
                originalEl.textContent = '';
            }
        } catch (e) {
            console.error('Parse error:', e);
        }
    };

    ws.onclose = () => {
        statusEl.textContent = '🔴 Отключено';
        if (subtitlesEnabled) {
            translatedEl.textContent = 'Переподключение...';
            originalEl.textContent = '';
        }
        setTimeout(connect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}

connect();