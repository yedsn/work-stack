const { exec } = require('child_process');
const os = require('os');

/**
 * 使用Edge浏览器打开指定URL
 * @param {string} url 要打开的URL
 */
function openEdgeWithUrl(url) {
  let command = '';
  
  if (process.platform === 'win32') {
    // Windows
    command = `start microsoft-edge:${url}`;
  } else if (process.platform === 'darwin') {
    // macOS
    command = `open -a "Microsoft Edge" "${url}"`;
  } else {
    // Linux
    command = `microsoft-edge "${url}"`;
  }
  
  console.log('执行命令:', command);
  
  exec(command, (error) => {
    if (error) {
      console.error(`执行出错: ${error.message}`);
      return false;
    }
    return true;
  });
}

// 测试函数
const urlToOpen = 'https://www.bing.com';
openEdgeWithUrl(urlToOpen);

module.exports = {
  openEdgeWithUrl
}; 