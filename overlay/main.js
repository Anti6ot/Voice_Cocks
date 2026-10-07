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

    const winWidth = 1100;
    const winHeight = 300;

    mainWindow = new BrowserWindow({
        width: winWidth,
        height: winHeight,
        x: Math.floor((width - winWidth) / 2),
        y: height - winHeight - 50,
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        resizable: false,
        hasShadow: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
    });

    mainWindow.loadFile('index.html');
    mainWindow.setIgnoreMouseEvents(false, { forward: true });
    mainWindow.setAlwaysOnTop(true, 'screen-saver', 1);
    mainWindow.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// Открытие окна настроек из главного окна
ipcMain.on('open-settings', () => {
    if (!settingsWindow) {
        createSettingsWindow();
    } else {
        settingsWindow.focus();
    }
});

// Запуск главного окна с настройками
ipcMain.on('start-with-settings', (event, settings) => {
    console.log('[main] Запуск с настройками:', settings);
    
    // Закрываем окно настроек
    if (settingsWindow) {
        settingsWindow.close();
        settingsWindow = null;
    }

    // Создаём главное окно
    createMainWindow();
});

// Закрытие окна настроек
ipcMain.on('close-settings', () => {
    if (settingsWindow) {
        settingsWindow.close();
    }
});

app.whenReady().then(createSettingsWindow);

app.on('window-all-closed', () => {
    app.quit();
});