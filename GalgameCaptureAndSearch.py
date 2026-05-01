import os
import json
import re
import time
import psutil
import requests
import win32gui
import win32process
import subprocess
from datetime import datetime
import threading  # 【新增】：用于后台线程
import webview    # 【新增】：用于创建桌面 UI 窗口
import shutil  # 【新增】用于复制文件
import base64  # 【新增】用于图片编码
import winreg  # 【新增】：用于操作 Windows 注册表实现开机自启
import sys     # 【新增】：用于获取当前 Python 解释器或 EXE 的路径
import pystray            # 【新增】：用于系统托盘
from PIL import Image     # 【新增】：用于生成/加载托盘图标

# ================= 配置区 =================
# 自适应获取脚本所在的绝对路径作为项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 映射文件保存在根目录
MAPPING_FILE = os.path.join(BASE_DIR, "game_mappings.json") 
# 【修改点1】：数据文件保存在 public 文件夹下，完美适配 Vue 前端读取
DATA_FILE = os.path.join(BASE_DIR, "public", "data.json") 
CONFIG_FILE = os.path.join(BASE_DIR, "public", "user_config", "config.json")

CHECK_INTERVAL = 10  # 扫描间隔（秒）

# --- 内置忽略黑名单 ---
IGNORE_EXES = {
    "chrome.exe", "msedge.exe", "firefox.exe", "safari.exe", "opera.exe",
    "steam.exe", "steamwebhelper.exe", "epicgameslauncher.exe", "upc.exe",
    "explorer.exe", "taskmgr.exe", "systemsettings.exe", "cmd.exe", "conhost.exe", "powershell.exe",
    "notepad.exe", "code.exe", "idea64.exe", "pycharm64.exe", "nvidia overlay.exe", "ashotplugctrl.exe",
    "textinputhost.exe", "searchui.exe", "runtimebroker.exe", "applicationframehost.exe",
    "asmonitorcontrol.exe", "onenote.exe", "word.exe", "excel.exe", "powerpnt.exe", "outlook.exe",
    "wechat.exe", "qq.exe", "discord.exe", "telegram.exe"
}

# ================= 记录配置 =================
def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(filepath, data):
    # 【修改点2】：确保目标文件夹（如 public）存在，如果不存在则自动创建
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ================= 根据进程ID获取其主窗口的标题 =================
def get_window_title_by_pid(target_pid):
    def callback(hwnd, hwnds):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid == target_pid:
                hwnds.append(win32gui.GetWindowText(hwnd))
        return True
    
    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds[0] if hwnds else None

# ================= 清洗标题用于检索 =================
def clean_game_title(raw_title):
    title = re.sub(r'【.*?】|\[.*?\]|\(.*?\)|（.*?）', '', raw_title)
    title = re.sub(r'中文版|汉化版|体验版|试玩版|官方|正式版|L O G O|标题页面|主菜单|设置|存档|读档|回忆|CG模式', '', title)
    return title.strip(" -_~*")

# ================= VNDB API =================
def search_vndb(title):
    if len(title) < 1:
        return None, None
    
    print(f"🔍 正在向 VNDB 搜索: [{title}] ...")
    url = "https://api.vndb.org/kana/vn"
    headers = {"Content-Type": "application/json"}
    payload = {
        "filters": ["search", "=", title],
        "fields": "id, title"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                first_result = data["results"][0]
                return first_result["id"], first_result["title"]
    except Exception as e:
        print(f"⚠️ VNDB 请求失败: {e}")
    return None, None

# ================= 游玩时长记录 =================
def log_playtime(vndb_id, duration_minutes):    
    play_data = load_json(DATA_FILE)
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if today_str not in play_data:
        play_data[today_str] = {}
        
    if vndb_id not in play_data[today_str]:
        play_data[today_str][vndb_id] = 0
        
    play_data[today_str][vndb_id] += duration_minutes
    save_json(DATA_FILE, play_data)

# ================= [新增模块]：自动化推送到 GitHub =================
def auto_push_to_github():
    print("正在 GitHub 自动同步...")
    
    # 切换到项目根目录，确保 git 命令在正确的位置执行
    os.chdir(BASE_DIR)

    try:
        # 1. 将 data.json 添加到暂存区
        subprocess.run(["git", "add", "public/"], check=True)
        
        # 2. 检查 git 状态，如果文件根本没发生变化，就直接退出，防止报错
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout:
            print("  -> 静默跳过: 游玩数据未发生实质变化。")
            return

        # 3. 提交更改，带上精确的时间戳
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"自动同步修改: {now_str}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # 4. 发射上云端
        subprocess.run(["git", "push"], check=True)
        print(f"GitHub 数据同步成功！你的网页即将在几分钟后更新。")

    except subprocess.CalledProcessError as e:
        print(f"Git 操作失败: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

# ================= 【新增模块】：暴露给 Vue 前端的 API =================
class TrackerAPI:
    def __init__(self):
        self._window = None # 将在 main 中被赋值
    
    def _trigger_background_sync(self):
        sync_thread = threading.Thread(target=auto_push_to_github, daemon=True)
        sync_thread.start()

    def get_image(self, img_type):
        """
        前端请求获取图片资源 (img_type: 'avatar' 或 'background')
        将图片转为 Base64 字符串返回，绕过浏览器的跨域路径限制
        """
        filename = f"{img_type}.jpg"
        filepath = os.path.join(BASE_DIR, "public", "user_config", filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, "rb") as f:
                    # 读取二进制并编码为 base64
                    encoded_string = base64.b64encode(f.read()).decode('utf-8')
                    # 拼接为前端 <img> 标签可直接使用的 data URI 格式
                    return f"data:image/jpeg;base64,{encoded_string}"
            except Exception as e:
                print(f"❌ 读取图片失败: {e}")
        
        # 如果文件不存在，返回空字符串，前端将使用默认图
        return ""
    def get_data(self):
        """Dashboard.vue 请求获取游玩数据"""
        return load_json(DATA_FILE)
    
    def get_config(self):
        """前端请求获取用户配置信息"""
        return load_json(CONFIG_FILE)
        
    def get_mappings(self):
        """Mapping.vue 请求获取路径映射数据"""
        return load_json(MAPPING_FILE)
    
    def delete_record(self, date_str, vnid):
        """Dashboard.vue 请求删除某条记录"""
        play_data = load_json(DATA_FILE)
        if date_str in play_data and vnid in play_data[date_str]:
            del play_data[date_str][vnid]
            # 如果这一天没有任何游戏了，把这一天的节点也删掉
            if not play_data[date_str]:
                del play_data[date_str]
            save_json(DATA_FILE, play_data)
            # 数据删除成功，触发同步
            self._trigger_background_sync()
            return True
        return False

    def update_mapping(self, exe_path, vnid):
        """Mapping.vue 请求更新游戏绑定关系"""
        mappings = load_json(MAPPING_FILE)
        if exe_path in mappings:
            # 如果 vnid 是空字符串，则存入 None 供脚本忽略
            mappings[exe_path]["vndb_id"] = vnid if vnid else None
            save_json(MAPPING_FILE, mappings)
            # 映射更新成功，触发同步
            self._trigger_background_sync()
        return True

    def save_config(self, username, signature, auto_start):
        """Settings.vue 请求保存系统配置"""
        config = load_json(CONFIG_FILE)
        config["username"] = username
        config["signature"] = signature
        config["autoStart"] = auto_start
        save_json(CONFIG_FILE, config)
        # 2. 【新增】：同步修改系统开机自启项！
        self._set_autostart(auto_start)
        
        # （可选扩展）：如果 auto_start 为 True，可以编写注册表写入逻辑，将其加入开机自启项
        print(f"配置已更新: 用户名={username}, 开机自启={auto_start}")
        # 配置更新成功，触发同步
        self._trigger_background_sync()
        return True
    
    # 【新增】：弹出原生对话框选择图片并复制
    def select_and_save_image(self, img_type):
        """前端请求弹出对话框选择图片 (img_type: 'avatar' 或 'background')"""
        if not self._window:
            return {"success": False, "msg": "Window object not bound."}

        # 1. 弹出原生文件选择对话框
        file_types = ('Image Files (*.bmp;*.jpg;*.gif;*.png)', 'All files (*.*)')
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, 
            allow_multiple=False, 
            file_types=file_types
        )

        # 2. 如果用户没有选择文件（点击了取消）
        if not result:
            return {"success": False, "msg": "用户取消了选择。"}

        # 获取选中的源文件绝对路径
        source_path = result[0]
        
        # 3. 构建目标保存路径
        filename = f"{img_type}.jpg" # 强制存为 jpg 方便前端统一读取
        target_path = os.path.join(BASE_DIR, "public", "user_config", filename)
        
        try:
            # 确保目标文件夹存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 4. 执行复制并覆盖
            shutil.copy2(source_path, target_path)
            
            print(f"✅ 图片已成功复制至: {target_path}")

            # 图片覆写成功，触发同步
            self._trigger_background_sync()

            # 返回成功状态和源文件的名字，供前端显示
            return {"success": True, "filename": os.path.basename(source_path)}
        
        except Exception as e:
            print(f"❌ 复制图片失败: {e}")
            return {"success": False, "msg": str(e)}
        
    def _set_autostart(self, enable=True):
        """修改注册表，设置或取消开机自启"""
        app_name = "R U Winning Son?"  # 注册表中的键名，可以自定义
        
        # 智能判断运行环境获取路径：
        # 如果是未来用 PyInstaller 打包好的 exe 运行
        if getattr(sys, 'frozen', False):
            exe_path = f'"{sys.executable}"'
        # 如果是当前的 python main.py 脚本运行
        else:
            exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

        # 指定开机启动的注册表路径
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            # 打开注册表（获取修改权限）
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            if enable:
                # 勾选：写入注册表
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                print(f"成功添加开机自启: {exe_path}")
            else:
                # 取消：从注册表中删除
                try:
                    winreg.DeleteValue(key, app_name)
                    print("成功移除开机自启")
                except FileNotFoundError:
                    # 如果本来就不存在，忽略报错
                    pass 
                    
            winreg.CloseKey(key)
        except Exception as e:
            print(f"❌ 设置开机自启失败，可能需要管理员权限或被安全软件拦截: {e}")

# ================= 监控程序后台线程 =================
def monitor_loop():
    mappings = load_json(MAPPING_FILE)
    active_sessions = {}
    
    print(" Galgame 后台监控程序已启动... (按 Ctrl+C 退出)")
    print(f"监控根目录: {BASE_DIR}")
    
    while True:
        current_running_paths = set()    

        for proc in psutil.process_iter(['name','exe','pid']):
            try:
                exe_path = proc.info['exe']
                exe_name = proc.info['name']
                if not exe_path or not exe_name:
                    continue
                
                if exe_name.lower() in IGNORE_EXES:
                    continue

                if exe_path not in mappings:
                    raw_title = get_window_title_by_pid(proc.info['pid'])
                    if raw_title:
                        print(f"发现新窗口: [{raw_title}]")
                        cleaned_title = clean_game_title(raw_title)
                        vndb_id, std_title = search_vndb(cleaned_title)
                        
                        if vndb_id:
                            print(f"匹配成功！VNDB ID: {vndb_id} ({std_title})")
                            mappings[exe_path] = {"vndb_id": vndb_id, "title": std_title}
                        else:
                            print("未找到匹配项，自动拉黑，后续忽略。")
                            mappings[exe_path] = {"vndb_id": None, "title": raw_title}
                        save_json(MAPPING_FILE, mappings)

                # ------ 计时抓取模块 ------
                if exe_path in mappings and mappings[exe_path].get("vndb_id") is not None:
                    current_running_paths.add(exe_path)
                    
                    if exe_path not in active_sessions:
                        active_sessions[exe_path] = time.time()
                        game_name = mappings[exe_path]["title"]
                        print(f"\n🟢 [{datetime.now().strftime('%H:%M:%S')}] 开始游玩: {game_name}")

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # ------ 结算模块 ------
        closed_games = []
        for path, start_time in active_sessions.items():
            if path not in current_running_paths:
                end_time = time.time()
                duration = int((end_time - start_time) / 60)
                
                game_info = mappings[path]
                print(f"\n🔴 [{datetime.now().strftime('%H:%M:%S')}] 结束游玩: {game_info['title']} | 本次时长: {duration} 分钟")
                
                log_playtime(game_info["vndb_id"], duration)
                print(f"  -> 数据已成功写入: {DATA_FILE}")
                
                closed_games.append(path)
                
        # 从活跃列表中清理掉已经关闭的游戏
        for path in closed_games:
            del active_sessions[path]
            
        # 【修改点3】：如果有游戏刚刚结束并写入了数据，立刻触发云端同步！
        if closed_games:
            auto_push_to_github()

        # 休息 10 秒后再次扫描
        time.sleep(CHECK_INTERVAL)

def setup_tray(window):
    """配置系统托盘图标和右键菜单"""
    
    # 1. 定义托盘菜单的功能
    def on_show(icon, item):
        window.show() # 显示被隐藏的窗口

    def on_quit(icon, item):
        icon.stop()          # 停止托盘图标运行
        window.destroy()     # 彻底销毁 webview 窗口
        os._exit(0)          # 强制退出所有 Python 线程，干净利落

    # 2. 创建一个简单的纯色带字图标 (你也可以后续换成读取本地 .ico 文件)
    # 这里我们动态生成一个蓝底白字的 "GT" (Galgame Tracker) 图标
    icon_image = Image.new('RGB', (64, 64), color=(24, 144, 255))
    
    # 3. 配置右键菜单 (设置 default=True 即可支持鼠标左键双击触发)
    menu = pystray.Menu(
        pystray.MenuItem('显示主界面', on_show, default=True),
        pystray.MenuItem('完全退出', on_quit)
    )

    # 4. 实例化托盘对象
    tray_icon = pystray.Icon("GalgameTracker", icon_image, "Galgame 记录器运行中", menu)
    
    # 5. 在独立的守护线程中启动托盘，防止阻塞 UI
    threading.Thread(target=tray_icon.run, daemon=True).start()

# ================= 主程序入口 =================
if __name__ == "__main__":
    # 1. 以守护线程 (daemon=True) 的方式启动原有的游戏监控代码
    # daemon=True 意味着当 UI 窗口关闭时，后台监控也会自动结束
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()

    # 2. 定位到前端 Vue 打包好的 index.html 路径
    html_path = os.path.join(BASE_DIR, "frontend_local", "dist", "index.html")

    # 3. 实例化 API 桥梁
    api = TrackerAPI()

    # 4. 创建并启动桌面应用程序窗口
    print("正在启动图形用户界面...")
    window = webview.create_window(
        title='R U Winning, Son?', 
        url=html_path,     # 加载前端页面
        js_api=api,        # 把 Python API 注入到 window.pywebview.api 供 Vue 使用
        width=1600, 
        height=900,
        frameless=False,   # 如果设为 True 可以隐藏 Windows 原生标题栏，做纯沉浸式界面
    )

    # 【关键】：将 window 实例绑定给 API，这样 API 内部才能调用 create_file_dialog
    api._window = window

    def on_closing():
        """当用户点击窗口 X 按钮时触发"""
        window.hide()  # 隐藏窗口而不是关闭它
        return False   # 返回 False 代表取消关闭操作，保持程序后台存活
        
    window.events.closing += on_closing
    # ==============================================================

    # 初始化并启动托盘图标
    setup_tray(window)
    # 启动 pywebview 引擎 (debug=True 可以让你在窗口内按 F12 打开开发者工具排错)
    webview.start(debug=False)