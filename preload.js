const { contextBridge, ipcRenderer } = require('electron');

// 添加错误处理包装器
const safeIpcInvoke = async (channel, ...args) => {
  try {
    return await ipcRenderer.invoke(channel, ...args);
  } catch (error) {
    console.error(`IPC调用失败 (${channel}):`, error);
    throw error;
  }
};

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  getApps: () => safeIpcInvoke('get-apps'),
  saveApp: (app) => safeIpcInvoke('save-app', app),
  deleteApp: (id) => safeIpcInvoke('delete-app', id),
  launchApp: (app) => safeIpcInvoke('launch-app', app),
  openFileDialog: () => safeIpcInvoke('open-file-dialog'),
  getBasename: (filePath, ext) => safeIpcInvoke('get-basename', filePath, ext)
}); 