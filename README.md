# 初始化指南

欢迎使用本工具！为了让你的本地客户端能够顺利将数据同步到你专属的网页上，请按照以下步骤完成环境配置。

## 第一步：环境准备 (安装 Git)

本程序依赖 Git 进行数据同步，请确保你的电脑上已经安装了它：
1. 前往 [Git 官方网站](https://git-scm.com/downloads) 下载对应操作系统的安装包。
2. 按照默认提示一直点击“下一步”完成安装即可。

## 第二步：配置你的专属云端仓库

我们需要将纯净的网页模板复制到你自己的 GitHub 账号下：

1. 点击本页面右上角的 **Fork** 按钮。
2. **重要**：在弹出的页面中，**必须取消勾选** "Copy the main branch only"（仅复制 main 分支），然后点击 Create fork。
3. 进入你 Fork 后的个人仓库，点击顶部的  **Settings**（设置）。
4. 在左侧菜单点击 **General**，向下滚动找到 **Default branch** 区域。
5. 点击切换箭头 ，选择 **`pages-template`** 并确认更新 (Update)。
6. 回到仓库主页，点击左上角的 **branches** (分支列表)。
7. 找到原本的 `main` 分支，点击右侧的垃圾桶 🗑️ 将其删除。
8. 找到 `pages-template` 分支，点击右侧的铅笔 ✏️ 将其重命名为 **`main`**。

### 第三步：唤醒自动化部署机器人 (Actions)

出于安全机制，GitHub 默认禁用了 Fork 仓库的自动化脚本，我们需要手动开启它：

1. 点击仓库顶部导航栏的 **Actions** 标签页。
2. 你会看到一个醒目的绿色按钮，提示 "I understand my workflows, go ahead and enable them"（我了解我的工作流，继续并启用它们）。**点击这个绿色按钮**。


### 第四步：配置 GitHub Pages 部署模式

告诉 GitHub 服务器使用自动化脚本来构建你的 Vue 网页：

1. 点击顶部的 ⚙️ **Settings**（设置），在左侧菜单找到 **Pages**。
2. 找到 **Build and deployment** 下的 **Source**。
3. 点击下拉菜单，将其从默认的 "Deploy from a branch" 更改为 **"GitHub Actions"**。

*(此时，只要你的 `main` 分支有新的数据推送，GitHub Actions 就会在后台自动为你打包并上线网页！)*

至此，你已经拥有了一个全新的github pages页面！

## 第五步：本地同步与客户端整合

现在，我们将你的云端仓库同步到本地，并将客户端程序放入其中：

1. 在你的电脑上找一个你喜欢的**空白文件夹**。
2. 在该文件夹内，按住 `Shift` 键并右键点击空白处，选择“在此处打开 PowerShell 窗口”或“打开终端”或“Open git bash here”。
3. 输入以下命令，将你的仓库下载到本地（请将链接替换为你自己的仓库地址）：
   ```bash
   git clone [https://github.com/你的用户名/你的此项目仓库名.git](https://github.com/你的用户名/你的仓库名.git) .
此时，你可能被跳转至浏览器进行登陆操作。