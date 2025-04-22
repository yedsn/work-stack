const { spawn } = require('child_process');
const electron = require('electron');
const path = require('path');

// 设置环境变量
process.env.NODE_ENV = 'development';

// 启动 Electron
const electronProcess = spawn(electron, ['.'], { 
  stdio: 'inherit',
  env: process.env
});

electronProcess.on('close', () => {
  process.exit();
}); 