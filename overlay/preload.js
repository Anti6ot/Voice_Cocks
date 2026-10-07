const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    openSettings: () => ipcRenderer.send('open-settings'),
    startWithSettings: (settings) => ipcRenderer.send('start-with-settings', settings),
    closeSettings: () => ipcRenderer.send('close-settings'),
    
    // Переключение режима кликов
    setIgnoreMouseEvents: (ignore, options) => ipcRenderer.send('set-ignore-mouse-events', ignore, options),
    
    // Управление позицией окна
    getWindowPosition: () => ipcRenderer.invoke('get-window-position'),
    setWindowPosition: (x, y) => ipcRenderer.send('set-window-position', x, y),
    
    // Управление размером окна
    getWindowSize: () => ipcRenderer.invoke('get-window-size'),
    setWindowSize: (width, height) => ipcRenderer.send('set-window-size', width, height),
});