const deviceSelect = document.getElementById('device-select');
const modelSelect = document.getElementById('model-select');
const cancelBtn = document.getElementById('cancel-btn');
const saveBtn = document.getElementById('save-btn');

// Загрузка списка устройств
async function loadDevices() {
    try {
        const response = await fetch('http://localhost:8766/devices');
        const devices = await response.json();
        
        deviceSelect.innerHTML = '';
        devices.forEach((device, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `[${index}] ${device.name}`;
            deviceSelect.appendChild(option);
        });
        
        // Загружаем текущие настройки
        loadSettings();
    } catch (e) {
        deviceSelect.innerHTML = '<option value="0">Ошибка загрузки устройств</option>';
        console.error('Error loading devices:', e);
    }
}

// Загрузка текущих настроек
async function loadSettings() {
    try {
        const response = await fetch('http://localhost:8766/settings');
        const settings = await response.json();
        
        if (settings.device !== undefined) {
            deviceSelect.value = settings.device;
        }
        if (settings.model) {
            modelSelect.value = settings.model;
        }
    } catch (e) {
        console.error('Error loading settings:', e);
    }
}

// Сохранение настроек и запуск
saveBtn.addEventListener('click', async () => {
    const settings = {
        device: parseInt(deviceSelect.value),
        model: modelSelect.value
    };
    
    try {
        // Сохраняем настройки
        await fetch('http://localhost:8766/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });
        
        // Отправляем сигнал на запуск главного окна
        window.electronAPI.startWithSettings(settings);
    } catch (e) {
        alert('Ошибка сохранения настроек: ' + e.message);
    }
});

// Отмена
cancelBtn.addEventListener('click', () => {
    window.electronAPI.closeSettings();
});

// Инициализация
loadDevices();