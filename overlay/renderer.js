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

// Перетаскивание окна
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
    
    // Получаем текущую позицию окна
    window.electronAPI.getWindowPosition().then(pos => {
        windowStartX = pos.x;
        windowStartY = pos.y;
    });
    
    e.preventDefault();
});

document.addEventListener('mousemove', (e) => {
    if (isDragging) {
        const deltaX = e.screenX - dragStartX;
        const deltaY = e.screenY - dragStartY;
        
        window.electronAPI.setWindowPosition(
            windowStartX + deltaX,
            windowStartY + deltaY
        );
    }
});

document.addEventListener('mouseup', () => {
    if (isDragging) {
        isDragging = false;
        disableMouseEvents();
    }
});

// Изменение размера окна
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
    
    window.electronAPI.getWindowSize().then(size => {
        windowStartWidth = size.width;
        windowStartHeight = size.height;
    });
    
    e.preventDefault();
});

document.addEventListener('mousemove', (e) => {
    if (isResizing) {
        const deltaX = e.screenX - resizeStartX;
        const deltaY = e.screenY - resizeStartY;
        
        const newWidth = Math.max(400, windowStartWidth + deltaX);
        const newHeight = Math.max(150, windowStartHeight + deltaY);
        
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
function connect() {
    ws = new WebSocket('ws://localhost:8765');

    ws.onopen = () => {
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
        translatedEl.textContent = 'Переподключение...';
        originalEl.textContent = '';
        setTimeout(connect, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}

connect();