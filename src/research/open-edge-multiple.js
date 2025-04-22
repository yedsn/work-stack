const { exec } = require('child_process');
const os = require('os');

/**
 * 打开Edge浏览器并访问多个指定网站
 * @param {string[]} urls 要访问的网址数组
 */
function openEdgeWithMultipleUrls(urls) {
  if (!Array.isArray(urls) || urls.length === 0) {
    console.error('请提供有效的URL数组');
    return;
  }
  
  console.log(`正在打开Edge浏览器，访问${urls.length}个网站`);
  
  // 根据操作系统确定Edge的可执行文件路径
  let edgePath = '';
  let command = '';
  
  if (process.platform === 'win32') {
    // Windows系统
    // 在Windows上，可以使用多个URL参数一次性打开多个标签页
    edgePath = 'start microsoft-edge:';
    command = `${edgePath}"${urls.join('" "')}"`;
  } else if (process.platform === 'darwin') {
    // macOS系统
    edgePath = 'open -a "Microsoft Edge"';
    // 在macOS上，我们可以一次打开一个URL
    command = `${edgePath} "${urls[0]}"`;
    // 然后为其余URL创建新标签页
    for (let i = 1; i < urls.length; i++) {
      command += ` && ${edgePath} "${urls[i]}"`;
    }
  } else {
    // Linux系统
    edgePath = 'microsoft-edge';
    command = `${edgePath} "${urls.join('" "')}"`;
  }
  
  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`执行出错: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`stderr: ${stderr}`);
      return;
    }
    console.log(`Edge已成功启动，访问网址: ${urls.join(', ')}`);
  });
}

// 测试函数
const urlsToOpen = [
  'https://www.bing.com',
  'https://www.github.com',
  'https://www.stackoverflow.com'
];
openEdgeWithMultipleUrls(urlsToOpen);

module.exports = { openEdgeWithMultipleUrls }; 