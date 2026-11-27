const originalEl = document.getElementById('original');
const translatedEl = document.getElementById('translated');
const subtitleContainer = document.getElementById('subtitle-container');
const dragHandle = document.getElementById('drag-handle');
const resizeHandle = document.getElementById('resize-handle');

let ws = null;

// === УПРАВЛЕНИЕ КЛИКАМИ ===
function enableMouseEvents() {
    window.electronAPI.setIgnoreMouseEvents(false);
}

function disableMouseEvents() {
    window.electronAPI.setIgnoreMouseEvents(true, { forward: true });
}

// Текущие размеры и позиция окна. Обновляются на лету, чтобы не было гонок
// с асинхронным getWindowSize/getWindowPosition во время первого движения мыши.
let currentWidth = 900;
let currentHeight = 250;
let currentX = 0;
let currentY = 0;

window.electronAPI.getWindowSize().then(size => {
    currentWidth = size.width;
    currentHeight = size.height;
});
window.electronAPI.getWindowPosition().then(pos => {
    currentX = pos.x;
    currentY = pos.y;
});

// === ПЕРЕТАСКИВАНИЕ ===
let isDragging = false;
let dragStartX = 0;
let dragStartY = 0;
let windowStartX = 0;
let windowStartY = 0;

dragHandle.addEventListener('mouseenter', enableMouseEvents);
dragHandle.addEventListener('mouseleave', () => {
    if (!isDragging) disableMouseEvents();
});

dragHandle.addEventListener('mousedown', (e) => {
    isDragging = true;
    dragStartX = e.screenX;
    dragStartY = e.screenY;
    windowStartX = currentX;
    windowStartY = currentY;
    e.preventDefault();
});

document.addEventListener('mousemove', (e) => {
    if (isDragging) {
        currentX = windowStartX + (e.screenX - dragStartX);
        currentY = windowStartY + (e.screenY - dragStartY);
        window.electronAPI.setWindowPosition(currentX, currentY);
    }
});

document.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        disableMouseEvents();
    }
});

// === ИЗМЕНЕНИЕ РАЗМЕРА ===
let isResizing = false;
let resizeStartX = 0;
let resizeStartY = 0;
let windowStartWidth = 0;
let windowStartHeight = 0;

resizeHandle.addEventListener('mouseenter', enableMouseEvents);
resizeHandle.addEventListener('mouseleave', () => {
    if (!isResizing) disableMouseEvents();
});

resizeHandle.addEventListener('mousedown', (e) => {
    isResizing = true;
    resizeStartX = e.screenX;
    resizeStartY = e.screenY;
    windowStartWidth = currentWidth;
    windowStartHeight = currentHeight;
    e.preventDefault();
});

document.addEventListener('mousemove', (e) => {
    if (isResizing) {
        const newWidth = Math.max(400, windowStartWidth + (e.screenX - resizeStartX));
        const newHeight = Math.max(150, windowStartHeight + (e.screenY - resizeStartY));
        currentWidth = newWidth;
        currentHeight = newHeight;
        window.electronAPI.setWindowSize(newWidth, newHeight);
    }
});

document.addEventListener('mouseup', () => {
    if (isResizing) {
        isResizing = false;
        disableMouseEvents();
    }
});

// Контейнер субтитров — интерактивен для скролла
subtitleContainer.addEventListener('mouseenter', enableMouseEvents);
subtitleContainer.addEventListener('mouseleave', () => {
    if (!isDragging && !isResizing) {
        disableMouseEvents();
    }
});

// === WEBSOCKET ===
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5; // ~10 секунд без бэкенда — закрываем оверлей

function connect() {
    ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
        reconnectAttempts = 0;
        translatedEl.textContent = '🎧 Слушаю...';
        originalEl.textContent = '';
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'subtitle') {
                originalEl.textContent = data.original || '';
                translatedEl.textContent = data.translated || '';
            } else if (data.type === 'status') {
                translatedEl.textContent = data.text;
                originalEl.textContent = '';
            }
        } catch (e) {
            console.error('Parse error:', e);
        }
    };

    ws.onclose = () => {
        reconnectAttempts++;
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            translatedEl.textContent = 'Сервер отключён';
            originalEl.textContent = 'Закрываю...';
            setTimeout(() => window.electronAPI.quit(), 1200);
            return;
        }
        translatedEl.textContent = 'Переподключение...';
        originalEl.textContent = '';
        setTimeout(connect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}

connect();
