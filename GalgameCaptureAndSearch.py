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

# ================= 配置区 =================
# 自适应获取脚本所在的绝对路径作为项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 映射文件保存在根目录
MAPPING_FILE = os.path.join(BASE_DIR, "game_mappings.json") 
# 【修改点1】：数据文件保存在 public 文件夹下，完美适配 Vue 前端读取
DATA_FILE = os.path.join(BASE_DIR, "public", "data.json") 
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
        subprocess.run(["git", "add", "public/data.json"], check=True)
        
        # 2. 检查 git 状态，如果文件根本没发生变化，就直接退出，防止报错
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout:
            print("  -> 静默跳过: 游玩数据未发生实质变化。")
            return

        # 3. 提交更改，带上精确的时间戳
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"自动同步最新游玩记录: {now_str}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        
        # 4. 发射上云端
        subprocess.run(["git", "push"], check=True)
        print(f"GitHub 数据同步成功！你的网页即将在几分钟后更新。")

    except subprocess.CalledProcessError as e:
        print(f"Git 操作失败: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

# ================= 主程序 =================
def main():
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

if __name__ == "__main__":
    main()