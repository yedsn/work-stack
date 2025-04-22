const { exec } = require('child_process');
const path = require('path');

/**
 * 打开VSCode并加载指定项目
 * @param {string} projectPath 项目路径
 */
function openVSCode(projectPath) {
  // 确保路径是绝对路径
  const absolutePath = path.resolve(projectPath);
  console.log(`正在打开VSCode，项目路径: ${absolutePath}`);
  
  // 使用code命令打开VSCode
  // 注意：需要VSCode在PATH环境变量中
  exec(`Code "${absolutePath}"`, (error, stdout, stderr) => {
    if (error) {
      console.error(`执行出错: ${error.message}`);
      return;
    }
    if (stderr) {
      console.error(`stderr: ${stderr}`);
      return;
    }
    console.log(`VSCode已成功启动，加载项目: ${absolutePath}`);
  });
}

// 测试函数
// 替换为您想要打开的项目路径
const projectToOpen = 'E:\Workspaces\git\my\vue-easy-dict';
openVSCode(projectToOpen);

module.exports = { openVSCode }; 