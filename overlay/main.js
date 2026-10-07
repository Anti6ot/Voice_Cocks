const { app, BrowserWindow, screen, ipcMain } = require('electron');
const path = require('path');

let settingsWindow;
let mainWindow;

function createSettingsWindow() {
    settingsWindow = new BrowserWindow({
        width: 500,
        height: 450,
        frame: true,
        resizable: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
    });

    settingsWindow.loadFile('settings.html');

    settingsWindow.on('closed', () => {
        settingsWindow = null;
    });
}

function createMainWindow() {
    if (mainWindow) {
        mainWindow.focus();
        return;
    }

    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    const winWidth = 900;
    const winHeight = 250;

    mainWindow = new BrowserWindow({
        width: winWidth,
        height: winHeight,
        x: Math.floor((width - winWidth) / 2),
        y: height - winHeight - 60,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        resizable: true,          // Разрешаем изменение размера
        hasShadow: false,
        minimizable: false,
        maximizable: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
    });

    mainWindow.loadFile('index.html');
    
    // Окно не блокирует клики в игре, но принимает события при наведении
    mainWindow.setIgnoreMouseEvents(true, { forward: true });
    mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);
    mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// IPC обработчики
ipcMain.on('open-settings', () => {
    if (!settingsWindow) {
        createSettingsWindow();
    } else {
        settingsWindow.focus();
    }
});

ipcMain.on('start-with-settings', (event, settings) => {
    console.log('[main] Запуск с настройками:', settings);
    
    if (settingsWindow) {
        settingsWindow.close();
        settingsWindow = null;
    }

    createMainWindow();
});

ipcMain.on('close-settings', () => {
    if (settingsWindow) {
        settingsWindow.close();
    }
});

// Переключение режима кликов
ipcMain.on('set-ignore-mouse-events', (event, ignore, options) => {
    if (mainWindow) {
        mainWindow.setIgnoreMouseEvents(ignore, options);
    }
});

// Изменение размера окна из renderer
ipcMain.on('resize-window', (event, { width, height }) => {
    if (mainWindow) {
        mainWindow.setSize(Math.round(width), Math.round(height));
    }
});

// Получение позиции окна
ipcMain.handle('get-window-position', () => {
    if (mainWindow) {
        const pos = mainWindow.getPosition();
        return { x: pos[0], y: pos[1] };
    }
    return { x: 0, y: 0 };
});

// Установка позиции окна
ipcMain.on('set-window-position', (event, x, y) => {
    if (mainWindow) {
        mainWindow.setPosition(Math.round(x), Math.round(y));
    }
});

// Получение размера окна
ipcMain.handle('get-window-size', () => {
    if (mainWindow) {
        const size = mainWindow.getSize();
        return { width: size[0], height: size[1] };
    }
    return { width: 900, height: 220 };
});

// Установка размера окна
ipcMain.on('set-window-size', (event, width, height) => {
    if (mainWindow) {
        mainWindow.setSize(Math.round(width), Math.round(height));
    }
});

app.whenReady().then(createSettingsWindow);

app.on('window-all-closed', () => {
    app.quit();
});