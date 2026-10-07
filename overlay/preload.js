const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    openSettings: () => ipcRenderer.send('open-settings'),
    startWithSettings: (settings) => ipcRenderer.send('start-with-settings', settings),
    onSettingsReady: (callback) => ipcRenderer.on('settings-ready', (event, devices) => callback(devices)),
    closeSettings: () => ipcRenderer.send('close-settings'),
    
    // Переключение режима кликов
    setIgnoreMouseEvents: (ignore, options) => ipcRenderer.send('set-ignore-mouse-events', ignore, options),
});