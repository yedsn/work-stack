const { spawn } = require('child_process');
const { createServer } = require('vite');
const electron = require('electron');
const path = require('path');

async function startApp() {
  // 启动 Vite 开发服务器
  const viteServer = await createServer({
    configFile: path.resolve(__dirname, '../vite.config.js')
  });
  
  await viteServer.listen();
  
  // 设置环境变量
  const env = Object.assign(process.env, {
    NODE_ENV: 'development',
    VITE_DEV_SERVER_URL: 'http://localhost:3000'
  });
  
  // 启动 Electron
  const electronProcess = spawn(electron, ['.'], { stdio: 'inherit', env });
  
  electronProcess.on('close', () => {
    viteServer.close();
    process.exit();
  });
}

startApp(); 