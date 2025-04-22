const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const Store = require('electron-store');

// 创建存储实例
const store = new Store();

// 保持对window对象的全局引用，如果不这样做，
// 当JavaScript对象被垃圾回收时，window对象将自动关闭
let mainWindow;

function createWindow() {
  // 创建浏览器窗口
  mainWindow = new BrowserWindow({
    width: 900,
    height: 700,
    webPreferences: {
      preload: path.resolve(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false // 禁用沙箱以解决某些模块加载问题
    }
  });

  // 在 createWindow 函数开始处添加
  console.log('应用路径:', app.getAppPath());
  console.log('__dirname:', __dirname);
  console.log('preload 路径:', path.resolve(__dirname, 'preload.js'));

  // 加载应用的index.html
  // 在开发环境中使用Vite服务器
  const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:3000');
    // 打开开发者工具
    mainWindow.webContents.openDevTools();
  } else {
    // 在生产环境中加载打包后的文件
    mainWindow.loadFile(path.join(__dirname, 'dist', 'index.html'));
  }

  // 当window被关闭时，发出事件
  mainWindow.on('closed', function () {
    mainWindow = null;
  });

  // 在 createWindow 函数中添加
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('页面加载失败:', errorCode, errorDescription);
  });
}

// 当Electron完成初始化并准备创建浏览器窗口时调用此方法
app.whenReady().then(() => {
  createWindow();

  app.on('activate', function () {
    // 在macOS上，当点击dock图标并且没有其他窗口打开时，
    // 通常在应用程序中重新创建一个窗口
    if (mainWindow === null) createWindow();
  });
});

// 当所有窗口关闭时退出应用
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// 处理IPC消息
ipcMain.handle('get-apps', async () => {
  return store.get('apps') || [];
});

ipcMain.handle('save-app', async (event, app) => {
  const apps = store.get('apps') || [];
  apps.push(app);
  store.set('apps', apps);
  return apps;
});

ipcMain.handle('delete-app', async (event, id) => {
  let apps = store.get('apps') || [];
  apps = apps.filter(app => app.id !== id);
  store.set('apps', apps);
  return apps;
});

ipcMain.handle('launch-app', async (event, app) => {
  try {
    console.log('正在启动应用:', app);
    
    if (app.type === 'software') {
      // 启动软件
      let command = `"${app.path}"`;
      if (app.args) {
        command += ` ${app.args}`;
      }
      
      console.log('执行命令:', command);
      
      exec(command, (error) => {
        if (error) {
          console.error(`执行出错: ${error.message}`);
          return false;
        }
      });
    } else if (app.type === 'browser') {
      // 导入浏览器启动模块
      try {
        const { openEdgeWithUrl } = require('./src/research/open-edge-single');
        
        if (app.browser === 'edge') {
          console.log('启动Edge浏览器:', app.url);
          openEdgeWithUrl(app.url);
        } else if (app.browser === 'chrome') {
          // 使用类似的方法启动Chrome
          console.log('启动Chrome浏览器:', app.url);
          let command = '';
          if (process.platform === 'win32') {
            command = `start chrome "${app.url}"`;
          } else if (process.platform === 'darwin') {
            command = `open -a "Google Chrome" "${app.url}"`;
          } else {
            command = `google-chrome "${app.url}"`;
          }
          
          console.log('执行命令:', command);
          
          exec(command, (error) => {
            if (error) {
              console.error(`执行出错: ${error.message}`);
              return false;
            }
          });
        }
      } catch (error) {
        console.error('导入浏览器启动模块失败:', error);
        return false;
      }
    }
    
    return true;
  } catch (error) {
    console.error('启动应用时出错:', error);
    return false;
  }
});

// 在现有的ipcMain处理程序后添加
ipcMain.handle('open-file-dialog', async () => {
  const { dialog } = require('electron');
  return dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [
      { name: '可执行文件', extensions: ['exe', 'bat', 'cmd', 'msi'] },
      { name: '所有文件', extensions: ['*'] }
    ]
  });
});

// 添加全局错误处理
process.on('uncaughtException', (error) => {
  console.error('未捕获的异常:', error);
});

// 添加到其他 ipcMain 处理程序后面
ipcMain.handle('get-basename', async (event, filePath, ext) => {
  return path.basename(filePath, ext);
}); 