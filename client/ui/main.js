const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 400,
    height: 600,
    transparent: true,
    frame: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    }
  });

  mainWindow.loadFile('index.html');
  mainWindow.setAlwaysOnTop(true, 'screen-saver');
}

app.whenReady().then(() => {
  createWindow();

  // Start Wake Word Listener
  const wakeWord = spawn('python', ['../wake_word.py']);
  wakeWord.stdout.on('data', (data) => {
    if (data.toString().includes('Wake word detected')) {
      mainWindow.show();
      mainWindow.webContents.send('task-status', 'LISTENING...');
    }
  });
});

ipcMain.on('run-task', (event, task) => {
  const executor = spawn('python', ['../executor.py', task]);

  executor.stdout.on('data', (data) => {
    mainWindow.webContents.send('task-status', data.toString());
  });

  executor.on('close', (code) => {
    mainWindow.webContents.send('task-finished', `Task finished with code ${code}`);
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
