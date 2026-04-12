import os
import re
import subprocess
import sys
import platform
import socket
import time
import random
import string
import threading
import concurrent.futures
import json
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ctypes
from ctypes import wintypes
from datetime import datetime
import queue
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import atexit
import signal
import webbrowser

# API域名配置
api = "lytapi.asia"

# 导入UDP广播模块
from send import MulticastServer
# 导入mcstatus库用于检测Minecraft服务器
try:
    from mcstatus import JavaServer
    MCSTATUS_AVAILABLE = True
except ImportError:
    MCSTATUS_AVAILABLE = False

# Windows Job Object constants and structures
if platform.system() == "Windows":
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    JobObjectExtendedLimitInformation = 9
    
    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64)
        ]
    
    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_void_p),
            ("MaximumWorkingSetSize", ctypes.c_void_p),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_void_p),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32)
        ]
    
    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_void_p),
            ("JobMemoryLimit", ctypes.c_void_p),
            ("PeakProcessMemoryUsed", ctypes.c_void_p),
            ("PeakJobMemoryUsed", ctypes.c_void_p)
        ]
# 1导入mcstatus库用于检测Minecraft服务器
try:
    from mcstatus import JavaServer
    MCSTATUS_AVAILABLE = True
except ImportError:
    MCSTATUS_AVAILABLE = False


# 隐藏启动时的控制台窗口
if platform.system() == "Windows":
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
# 注册退出处理函数，确保FRP进程被清理
def cleanup_all_processes():
    try:
        # Windows下强制终止所有frpc.exe进程
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/f', '/im', 'frpc.exe'], 
                          capture_output=True, 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Unix/Linux/MacOS下终止frpc进程
            subprocess.run(['pkill', '-f', 'frpc'], capture_output=True)
    except Exception as e:
        pass  # 忽略错误，确保程序能正常退出

atexit.register(cleanup_all_processes)# 黑白灰主题颜色配置
BW_COLORS = {
    "primary": "#404040",
    "secondary": "#606060", 
    "accent": "#808080",
    "success": "#505050",
    "warning": "#707070",
    "danger": "#303030",
    "dark": "#202020",
    "light": "#f0f0f0",
    "background": "#e8e8e8",
    "card_bg": "#ffffff",
    "text_primary": "#000000",
    "text_secondary": "#404040",
    "border": "#c0c0c0"
}

# 字体配置
BW_FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"), 
    "normal": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "button": ("Segoe UI", 10, "bold")
}

def show_room_info_popup(room_info, is_created=True):
    """显示房间信息弹窗"""
    popup = tk.Toplevel()
    popup.title("房间信息" if is_created else "加入房间信息")
    popup.geometry("500x400")
    popup.configure(bg=BW_COLORS["background"])
    popup.resizable(True, True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
    except:
        pass
    
    # 设置窗口始终在最前面
    popup.attributes('-topmost', True)
    
    main_container = create_bw_frame(popup)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 标题
    title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    title_frame.pack(fill=tk.X, padx=10, pady=10)
    
    title_label = tk.Label(
        title_frame,
        text="房间信息" if is_created else "加入房间信息",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["primary"]
    )
    title_label.pack()
    
    # 房间信息显示
    info_frame = create_bw_frame(main_container)
    info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    info_text = tk.Text(
        info_frame,
        wrap=tk.WORD,
        font=BW_FONTS["normal"],
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=10,
        pady=10
    )
    info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 根据是创建还是加入房间显示不同内容
    if is_created:
        content = f"""创建房间成功！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址: {room_info['server_addr']}:{room_info['remote_port']}
本地Minecraft端口: {room_info['mc_port']}

其他玩家进入方式：
1. 打开本软件
2. 点击"内网穿透联机 - 加入网络房间（我要进别人的房间）"
3. 输入完整房间号: {room_info['full_room_code']}
4. 点击确认即可连接

注意：请不要关闭本程序，否则联机会断开"""
    else:
        content = f"""成功加入房间！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址: {room_info['server_addr']}:{room_info['remote_port']}

进入方式：
1. 在Minecraft中点多人游戏，添加服务器
2. 服务器地址输入: "127.0.0.1:25565"（已自动复制）
3. 进入服务器即可

注意：请不要关闭本程序，否则隧道会断开"""
    
    info_text.insert(tk.END, content)
    info_text.config(state=tk.DISABLED)
    
    # 按钮框架
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def close_popup():
        popup.destroy()
    
    # 关闭按钮
    close_btn = create_bw_button(button_frame, "关闭", close_popup, "primary", width=12)
    close_btn.pack(side=tk.RIGHT, padx=5)
    
    # 居中显示
    popup.update_idletasks()
    x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
    y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")
    
    # 设置为模态窗口
    popup.transient(popup.master)
    popup.grab_set()
    
    return popup

def create_bw_button(parent, text, command, style="primary", width=None):
    """创建黑白灰风格按钮"""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        font=BW_FONTS["button"],
        bg=BW_COLORS[style],
        fg="white",
        activebackground=BW_COLORS["accent"],
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=20,
        pady=8,
        cursor="hand2",
        width=width
    )
    
    # 添加悬停效果
    def on_enter(e):
        btn['bg'] = BW_COLORS["accent"]
        
    def on_leave(e):
        btn['bg'] = BW_COLORS[style]
    
    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn

def create_bw_frame(parent, **kwargs):
    """创建黑白灰风格框架"""
    return tk.Frame(
        parent,
        bg=BW_COLORS["card_bg"],
        relief="flat",
        bd=1,
        highlightbackground=BW_COLORS["border"],
        highlightthickness=1,
        **kwargs
    )

def create_section_title(parent, text):
    """创建分区标题"""
    title_frame = tk.Frame(parent, bg=BW_COLORS["background"])
    title_frame.pack(fill=tk.X, pady=(10, 5))
    
    title_label = tk.Label(
        title_frame,
        text=text,
        font=BW_FONTS["subtitle"],
        bg=BW_COLORS["background"],
        fg=BW_COLORS["primary"],
        anchor="w"
    )
    title_label.pack(fill=tk.X, padx=15)
    
    # 添加装饰线
    separator = tk.Frame(title_frame, height=2, bg=BW_COLORS["primary"])
    separator.pack(fill=tk.X, padx=15, pady=(2, 0))
    
    return title_frame

def check_cloud_permission():
    """检查云端软件使用许可"""
    def check_permission():
        try:
            url = f"https://{api}/st.txt"
            req = Request(url, headers={'User-Agent': 'LMFP/4.0.0'})
            
            with urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').strip().lower()
                return content == "true"
        except Exception as e:
            print(f"检查云端许可失败: {e}")
            return False
    
    return check_permission()

def check_for_updates(root_window=None):
    """检查软件更新"""
    try:
        # 读取本地版本号
        local_version = "400"  # 默认版本
        if os.path.exists("v.txt"):
            with open("v.txt", "r", encoding="utf-8") as f:
                local_version = f.read().strip()
        else:
            # 如果v.txt不存在，创建它并设置默认版本为1
            with open("v.txt", "w", encoding="utf-8") as f:
                f.write("400")
            print("已创建v.txt文件并设置默认版本为1")
        
        # 获取云端版本号
        url = f"https://{api}/v.txt"
        req = Request(url, headers={'User-Agent': 'LMFP/4.0.0'})
        with urlopen(req, timeout=10) as response:
            cloud_version = response.read().decode('utf-8').strip()
        
        # 比较版本号
        if _compare_versions(cloud_version, local_version) > 0:
            # 发现新版本，显示更新对话框
            return show_update_dialog(root_window, local_version, cloud_version)
        return False
    except Exception as e:
        print(f"检查更新失败: {e}")
        return False

def _compare_versions(version1, version2):
    """比较两个版本号"""
    def normalize(v):
        return [int(x) for x in v.split(".")]
    
    try:
        norm_v1 = normalize(version1)
        norm_v2 = normalize(version2)
        
        # 补齐版本号长度
        while len(norm_v1) < len(norm_v2):
            norm_v1.append(0)
        while len(norm_v2) < len(norm_v1):
            norm_v2.append(0)
        
        # 逐个比较版本号部分
        for i in range(len(norm_v1)):
            if norm_v1[i] > norm_v2[i]:
                return 1
            elif norm_v1[i] < norm_v2[i]:
                return -1
        return 0
    except:
        # 如果版本号解析失败，直接字符串比较
        if version1 > version2:
            return 1
        elif version1 < version2:
            return -1
        else:
            return 0

def show_update_dialog(parent_window, local_version, cloud_version):
    """显示更新对话框"""
    update_dialog = tk.Toplevel(parent_window)
    update_dialog.title("发现软件新版本")
    update_dialog.geometry("500x220")
    update_dialog.resizable(False, False)
    update_dialog.configure(bg=BW_COLORS["background"])
    update_dialog.transient(parent_window)
    update_dialog.grab_set()
    
    # 居中显示
    update_dialog.update_idletasks()
    x = (update_dialog.winfo_screenwidth() - update_dialog.winfo_width()) // 2
    y = (update_dialog.winfo_screenheight() - update_dialog.winfo_height()) // 2
    update_dialog.geometry(f"+{x}+{y}")
    
    main_container = create_bw_frame(update_dialog)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 标题
    title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    title_frame.pack(fill=tk.X, pady=(0, 15))
    
    title_label = tk.Label(
        title_frame,
        text="发现软件新版本",
        font=BW_FONTS["subtitle"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["primary"]
    )
    title_label.pack()
    
    # 内容
    content_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    content_frame.pack(fill=tk.X, pady=5)
    
    content_label = tk.Label(
        content_frame,
        text=f"检测到新的版本 {cloud_version}，当前版本为 {local_version}。是否立即更新？（如果不更新 可能因为过老的软件版本 而无法联机）",
        font=BW_FONTS["normal"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_primary"],
        wraplength=500,
        justify=tk.LEFT
    )
    content_label.pack(pady=10)
    
    # 按钮
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, pady=(15, 0))
    
    def update_now():
        update_dialog.destroy()
        perform_update()
    
    def remind_later():
        update_dialog.destroy()
    
    update_btn = create_bw_button(button_frame, "✓ 立即更新（推荐）", update_now, "success", width=12)
    update_btn.pack(side=tk.LEFT, padx=5)
    
    later_btn = create_bw_button(button_frame, "稍后提醒我", remind_later, "secondary", width=12)
    later_btn.pack(side=tk.RIGHT, padx=5)
    
    update_dialog.bind('<Return>', lambda e: update_now())
    update_dialog.bind('<Escape>', lambda e: remind_later())
    
    return True

def perform_update():
    """执行更新操作"""
    # 关闭所有可能的子窗口和进程
    cleanup_all_processes()
    
    # 结束up.exe进程
    try:
        if platform.system() == "Windows":
            subprocess.run(['taskkill', '/f', '/im', 'up.exe'], 
                          capture_output=True, 
                          creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run(['pkill', '-f', 'up.exe'], capture_output=True)
    except Exception as e:
        pass  # 忽略错误
    
    # 创建更新进度窗口
    update_window = tk.Tk()
    update_window.title("正在下载更新器")
    update_window.geometry("400x100")
    update_window.resizable(False, False)
    update_window.configure(bg=BW_COLORS["background"])
    update_window.attributes('-topmost', True)
    
    # 创建消息队列用于线程间通信
    message_queue = queue.Queue()
    
    # 居中显示
    update_window.update_idletasks()
    x = (update_window.winfo_screenwidth() - update_window.winfo_width()) // 2
    y = (update_window.winfo_screenheight() - update_window.winfo_height()) // 2
    update_window.geometry(f"+{x}+{y}")
    
    # 添加提示文本
    label = tk.Label(update_window, 
                     text="正在下载最新版本的 up.exe，请稍候...",
                     bg=BW_COLORS["background"],
                     fg=BW_COLORS["text_primary"],
                     font=BW_FONTS["normal"])
    label.pack(pady=(10, 5))
    
    # 添加进度条
    progress = ttk.Progressbar(update_window, length=300, mode='determinate')
    progress.pack(pady=(5, 10))
    
    # 更新窗口显示
    update_window.update()
    
    def update_ui():
        """在主线程中更新UI"""
        try:
            while True:
                # 检查消息队列
                message = message_queue.get_nowait()
                
                if message['type'] == 'progress':
                    # 更新进度条和标签
                    progress['value'] = message['value']
                    label['text'] = message['text']
                elif message['type'] == 'completed':
                    # 下载完成
                    label['text'] = "下载完成，正在启动更新程序..."
                    progress['value'] = 100
                elif message['type'] == 'failed':
                    # 下载失败
                    label['text'] = "更新失败"
                    progress['value'] = 0
                    # 3秒后关闭窗口
                    update_window.after(3000, update_window.destroy)
                    return
                elif message['type'] == 'exit':
                    # 关闭窗口并退出
                    update_window.destroy()
                    os._exit(0)
        except queue.Empty:
            pass
        
        # 每100毫秒检查一次消息队列
        update_window.after(100, update_ui)
    
    # 开始UI更新循环
    update_window.after(100, update_ui)
    
    def download_and_update():
        try:
            # 首先从up.txt获取最新的up.exe下载地址
            up_txt_url = f"https://{api}/up.txt"
            print(f"正在从 {up_txt_url} 获取下载地址...")
            
            # 创建请求对象，添加User-Agent头部以避免某些服务器的访问限制
            req = Request(up_txt_url, headers={'User-Agent': 'LMF4.0.0'})
            
            # 获取下载地址
            with urlopen(req, timeout=30) as response:
                download_url = response.read().decode('utf-8').strip()
            
            print(f"获取到实际下载地址: {download_url}")
            
            # 下载最新的up.exe
            print(f"正在从 {download_url} 下载最新的up.exe...")
            
            # 创建请求对象，添加User-Agent头部以避免某些服务器的访问限制
            req = Request(download_url, headers={'User-Agent': 'LMFP/4.0.0'})
            
            # 首先获取文件大小
            with urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                file_content = b''
                
                # 分块读取文件并更新进度
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    file_content += chunk
                    downloaded += len(chunk)
                    
                    # 更新进度条
                    if total_size > 0:
                        progress_value = int((downloaded / total_size) * 100)
                        message = {
                            'type': 'progress',
                            'value': progress_value,
                            'text': f"正在下载: {downloaded}/{total_size} bytes ({int((downloaded/total_size)*100)}%)"
                        }
                        message_queue.put(message)
            
            # 写入文件
            with open("up.exe", "wb") as f:
                f.write(file_content)
                
            print("up.exe下载完成，正在启动更新程序...")
            
            # 发送下载完成消息
            message_queue.put({'type': 'completed'})
            
            # 启动更新程序
            if os.path.exists("up.exe"):
                subprocess.Popen(["up.exe"])
                # 启动up.exe后立即退出当前程序
                os._exit(0)
            else:
                # 如果没有up.exe，尝试运行up.py
                if os.path.exists("up.py"):
                    subprocess.Popen([sys.executable, "up.py"])
                    # 启动up.py后立即退出当前程序
                    os._exit(0)
            
            # 发送退出消息
            message_queue.put({'type': 'exit'})
        except Exception as e:
            # 发送失败消息
            message_queue.put({'type': 'failed'})
            print(f"启动更新程序失败: {e}")
    
    # 在单独的线程中执行下载和更新操作
    threading.Thread(target=download_and_update, daemon=True).start()
# 公告检查功能
# ==============================================

def check_announcements():
    """检查云端公告"""
    try:
        # 云端公告版本号文件
        cloud_version_url = f"https://{api}/ggbb.txt"
        
        # 获取云端公告版本号
        req = Request(cloud_version_url, headers={'User-Agent': 'LMFP/4.0.0'})
        with urlopen(req, timeout=10) as response:
            cloud_version_str = response.read().decode('utf-8').strip()
            
            # 验证版本号是否为数字
            if not cloud_version_str.isdigit():
                print("云端公告版本号格式错误")
                return {'has_new_announcements': False}
            
            cloud_version = int(cloud_version_str)
            print(f"云端公告版本号: {cloud_version}")
        
        # 本地公告版本号文件
        local_version_file = "ggbb.txt"
        local_version = 0
        
        # 尝试读取本地版本号
        if os.path.exists(local_version_file):
            try:
                with open(local_version_file, 'r', encoding='utf-8') as f:
                    local_version_str = f.read().strip()
                    if local_version_str.isdigit():
                        local_version = int(local_version_str)
                        print(f"本地公告版本号: {local_version}")
                    else:
                        print("本地公告版本号格式错误，重置为0")
                        local_version = 0
            except Exception as e:
                print(f"读取本地公告版本号失败: {e}")
                local_version = 0
        
        # 比较版本号
        if cloud_version > local_version:
            print(f"发现新公告，云端版本: {cloud_version}, 本地版本: {local_version}")
            
            # 获取所有未读的公告
            announcements = []
            for version in range(local_version + 1, cloud_version + 1):
                try:
                    announcement_url = f"https://{api}/gg{version}.txt"
                    print(f"获取公告: {announcement_url}")
                    
                    req = Request(announcement_url, headers={'User-Agent': 'LMFP/4.0.0'})
                    with urlopen(req, timeout=10) as response:
                        content = response.read().decode('utf-8').strip()
                        if content:
                            announcements.append({
                                'version': version,
                                'content': content
                            })
                            print(f"✓ 成功获取公告 {version}")
                        else:
                            print(f"⚠ 公告 {version} 内容为空")
                except Exception as e:
                    print(f"✗ 获取公告 {version} 失败: {e}")
            
            # 如果有新公告，展示给用户
            if announcements:
                return {
                    'has_new_announcements': True,
                    'cloud_version': cloud_version,
                    'local_version': local_version,
                    'announcements': announcements
                }
            else:
                print("未获取到有效的公告内容")
                return {'has_new_announcements': False}
        
        print("没有新公告")
        return {'has_new_announcements': False}
        
    except Exception as e:
        print(f"公告检查过程中出错: {e}")
        return {'has_new_announcements': False}

def show_announcements_window(announcements_info, parent_window=None):
    """显示黑白灰风格公告窗口"""
    if not announcements_info or not announcements_info['has_new_announcements']:
        return None
    
    announcements = announcements_info['announcements']
    
    announcement_window = tk.Toplevel(parent_window) if parent_window else tk.Tk()
    announcement_window.title(f"软件公告 ({len(announcements)}条新公告)")
    announcement_window.geometry("800x900")
    announcement_window.resizable(True, True)
    announcement_window.configure(bg=BW_COLORS["background"])
    announcement_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            announcement_window.iconbitmap(icon_path)
    except:
        pass
    
    main_container = create_bw_frame(announcement_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=15)
    
    icon_label = tk.Label(
        header_frame,
        text="📢",
        font=("Arial", 24),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["primary"]
    )
    icon_label.pack(side=tk.LEFT)
    
    title_label = tk.Label(
        header_frame,
        text=f"软件公告 ({len(announcements)}条新公告)",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["dark"]
    )
    title_label.pack(side=tk.LEFT, padx=10)
    
    # 创建笔记本控件，用于多公告切换
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
    
    style = ttk.Style()
    style.configure("BW.TNotebook", background=BW_COLORS["card_bg"])
    style.configure("BW.TNotebook.Tab", 
                   background=BW_COLORS["secondary"],
                   foreground="white",
                   padding=[10, 5])
    style.map("BW.TNotebook.Tab", 
             background=[("selected", BW_COLORS["primary"])],
             foreground=[("selected", "white")])
    
    frames = []
    text_widgets = []
    
    for idx, ann in enumerate(announcements):
        # 创建每个公告的标签页
        frame = create_bw_frame(notebook)
        frames.append(frame)
        
        # 公告标题
        title_frame = tk.Frame(frame, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ann_title = tk.Label(
            title_frame,
            text=f"公告 #{ann['version']}",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        ann_title.pack(anchor="w")
        
        date_label = tk.Label(
            title_frame,
            text=f"--- : {datetime.now().strftime('-')}",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        date_label.pack(anchor="w", pady=(2, 0))
        
        # 公告内容
        content_frame = create_bw_frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            width=70,
            height=20,
            font=BW_FONTS["normal"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=15,
            pady=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert(tk.END, ann['content'])
        text_widget.config(state=tk.DISABLED)
        text_widgets.append(text_widget)
        
        # 添加到笔记本
        notebook.add(frame, text=f"公告{idx+1}")
    
    # 底部按钮
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=10)
    
    def mark_as_read_and_close():
        try:
            # 更新本地版本号
            with open("ggbb.txt", 'w', encoding='utf-8') as f:
                f.write(str(announcements_info['cloud_version']))
            print(f"✓ 已更新本地公告版本号为: {announcements_info['cloud_version']}")
        except Exception as e:
            print(f"✗ 更新本地公告版本号失败: {e}")
        
        announcement_window.destroy()
    
    def close_without_mark():
        announcement_window.destroy()
    
    # 左对齐按钮组
    left_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    left_btn_frame.pack(side=tk.LEFT)
    
    prev_btn = create_bw_button(left_btn_frame, "← 上一条", lambda: show_prev_announcement(), "secondary", width=10)
    prev_btn.pack(side=tk.LEFT, padx=5)
    prev_btn.config(state='disabled')  # 第一条公告时禁用
    
    next_btn = create_bw_button(left_btn_frame, "下一条 →", lambda: show_next_announcement(), "secondary", width=10)
    next_btn.pack(side=tk.LEFT, padx=5)
    if len(announcements) <= 1:
        next_btn.config(state='disabled')  # 只有一条公告时禁用
    
    # 右对齐按钮组
    right_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    right_btn_frame.pack(side=tk.RIGHT)
    
    close_btn = create_bw_button(right_btn_frame, "关闭", close_without_mark, "secondary", width=10)
    close_btn.pack(side=tk.RIGHT, padx=5)
    
    mark_read_btn = create_bw_button(right_btn_frame, "✓ 标记为已读并关闭", mark_as_read_and_close, "success", width=18)
    mark_read_btn.pack(side=tk.RIGHT, padx=5)
    
    # 标签页切换函数
    current_tab = [0]  # 使用列表以便在闭包中修改
    
    def show_next_announcement():
        if current_tab[0] < len(announcements) - 1:
            current_tab[0] += 1
            notebook.select(current_tab[0])
            update_nav_buttons()
    
    def show_prev_announcement():
        if current_tab[0] > 0:
            current_tab[0] -= 1
            notebook.select(current_tab[0])
            update_nav_buttons()
    
    def update_nav_buttons():
        # 更新导航按钮状态
        prev_btn.config(state='normal' if current_tab[0] > 0 else 'disabled')
        next_btn.config(state='normal' if current_tab[0] < len(announcements) - 1 else 'disabled')
    
    def on_tab_changed(event):
        selected_index = notebook.index(notebook.select())
        current_tab[0] = selected_index
        update_nav_buttons()
    
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # 添加键盘快捷键
    announcement_window.bind('<Right>', lambda e: show_next_announcement())
    announcement_window.bind('<Left>', lambda e: show_prev_announcement())
    announcement_window.bind('<Escape>', lambda e: close_without_mark())
    announcement_window.bind('<Return>', lambda e: mark_as_read_and_close())
    
    # 窗口居中
    announcement_window.update_idletasks()
    x = (announcement_window.winfo_screenwidth() - announcement_window.winfo_width()) // 2
    y = (announcement_window.winfo_screenheight() - announcement_window.winfo_height()) // 2
    announcement_window.geometry(f"+{x}+{y}")
    
    # 置于顶层
    announcement_window.attributes('-topmost', True)
    announcement_window.after(100, lambda: announcement_window.attributes('-topmost', False))
    
    return announcement_window

def show_disclaimer():
    """显示黑白灰风格免责声明窗口"""
    # 首先检查是否已设置始终同意
    try:
        if os.path.exists("Always-agree-to-the-terms.txt"):
            with open("Always-agree-to-the-terms.txt", "r", encoding="utf-8") as f:
                content = f.read().strip().lower()
                if content == "true":
                    # 如果已设置始终同意，则直接返回True
                    return True
    except Exception as e:
        print(f"读取Always-agree-to-the-terms.txt文件时出错: {e}")
    
    disclaimer_window = tk.Tk()
    disclaimer_window.title("免责声明")
    disclaimer_window.geometry("650x700")
    disclaimer_window.resizable(False, False)
    disclaimer_window.configure(bg=BW_COLORS["background"])
    disclaimer_window.attributes('-topmost', True)    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            disclaimer_window.iconbitmap(icon_path)
        else:
            # 尝试其他可能的路径
            possible_paths = [
                "./lyy.ico", "lyy.ico",
                os.path.join(os.path.dirname(__file__), "lyy.ico"),
                os.path.join(os.path.dirname(sys.executable), "lyy.ico")
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    disclaimer_window.iconbitmap(path)
                    break
    except:
        pass
    
    main_container = create_bw_frame(disclaimer_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=20)
    
    warning_icon = tk.Label(
        header_frame,
        text="⚠",
        font=("Arial", 28),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    warning_icon.pack(side=tk.LEFT, padx=(0, 15))
    
    title_label = tk.Label(
        header_frame,
        text="免责声明",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["dark"]
    )
    title_label.pack(side=tk.LEFT)
    
    content_frame = create_bw_frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    disclaimer_text = """重要提示：本协议是具有法律约束力的文件。在下载、安装或使用本软件前，请务必仔细阅读、理解并同意所有条款。如您不同意本协议的任何条款，请立即停止使用本软件并将其从您的设备中完全删除。

第一章 总则与基本定义
第1条 协议性质与效力
1.1 本《免责声明与用户协议》（下称“本协议”）是由软件开发者（下称“开发者”或“我们”）与软件使用者（下称“用户”或“您”）之间就“MC联机软件（内置FRP内网穿透功能）”（下称“本软件”）的使用所订立的具有法律约束力的协议。

1.2 本协议包含但不限于：软件许可条款、使用限制条款、免责声明条款、隐私政策条款、知识产权条款、责任限制条款、法律适用与争议解决条款等。所有条款构成完整、单一的法律文件。

1.3 开发者保留随时修改、更新本协议的权利，修改后的协议将在软件发布平台或官方网站公示。您继续使用本软件即视为接受修改后的协议。如您不同意修改内容，应立即停止使用本软件。

第2条 软件性质与定位
2.1 本软件被明确界定为“教育工具”和“技术研究平台”，其主要设计目的是：
（1）为计算机科学、网络工程、软件工程等相关专业学生提供网络通信技术的学习材料；
（2）为网络技术研究人员提供内网穿透技术的研究和测试环境；
（3）为软件开发者提供P2P连接技术的参考实现；
（4）为信息技术爱好者提供合法的技术实验工具。

2.2 本软件内置的FRP（Fast Reverse Proxy）内网穿透功能仅为技术演示和教育目的而存在，旨在帮助用户理解：
（1）NAT穿透的基本原理；
（2）反向代理的工作机制；
（3）网络安全中的隧道技术；
（4）分布式网络通信的实现方法。

2.3 本软件不允许用于任何实际的、持续的生产环境或商业服务。所有连接会话应仅限于测试、演示和学习目的。

第3条 关键术语定义
3.1 “本软件”：指“MC联机软件（内置FRP内网穿透功能）”及其所有相关组件、文档、更新和补丁。

3.2 “内网穿透”：指通过本软件演示的网络技术原理，该技术允许在特定网络配置下建立临时连接，仅供技术学习使用。

3.3 “学习交流”：指在个人或教育机构内部，以非商业、非盈利为目的的技术研究、教学和知识分享活动。

3.4 “非法目的”：包括但不限于：
（1）未经授权访问计算机系统或网络；
（2）干扰、破坏网络服务；
（3）侵犯他人知识产权；
（4）传播违法信息；
（5）进行任何违反适用法律法规的行为。

3.5 “商业用途”：包括但不限于：
（1）直接或间接收取费用；
（2）作为商业产品的一部分；
（3）用于提高商业竞争力；
（4）任何以盈利为目的的使用。

第二章 许可授权与使用限制
第4条 有限许可授予
4.1 开发者授予用户一项有限的、非独占的、不可转让的、可撤销的许可，允许用户在遵守本协议所有条款的前提下：
（1）在个人设备上下载和安装本软件；
（2）为学习网络技术目的运行本软件；
（3）在教育机构监督下用于教学演示；
（4）在技术研究项目中作为参考实现。

4.2 本许可明确禁止以下行为：
（1）将本软件用于任何商业运营；
（2）修改、逆向工程、反编译或反汇编本软件；
（3）移除、规避或修改本软件中的任何技术保护措施；
（4）将本软件集成到其他产品或服务中；
（5）出租、出借、转让、分发或再许可本软件。

第5条 使用场景限制
5.1 本软件仅限在以下场景中使用：
（1）个人学习环境：用户在自己的本地网络环境中，为学习网络编程和分布式系统概念而使用；
（2）实验室环境：在教育机构或研究机构的受控实验环境中，在教师或研究导师的监督下使用；
（3）技术演示：在技术会议或研讨会上，为展示特定网络技术原理而进行的临时演示；
（4）合规测试：在获得明确书面授权的网络环境中进行安全测试。

5.2 严格禁止的使用场景包括但不限于：
（1）公共网络服务：不得将本软件部署为向公众提供的服务；
（2）生产环境：不得用于任何商业或非商业的生产系统；
（3）关键基础设施：不得在任何关键基础设施相关的网络中使用；
（4）规避安全措施：不得用于规避任何网络安全管理措施；
（5）侵犯隐私：不得用于监控、收集或传输他人隐私信息。

第6条 技术功能限制
6.1 虽然本软件展示了内网穿透的技术可能性，但用户理解并同意：
（1）本软件不提供任何服务质量保证；
（2）所有连接均为临时性、实验性连接；
（3）数据传输不包含任何加密或安全保证；
（4）连接可能在任何时间无故中断；
（5）不支持高并发或高负载场景。

6.2 用户确认理解以下技术事实：
（1）内网穿透可能涉及网络地址转换；
（2）某些网络环境可能阻止此类连接；
（3）使用本软件可能导致网络配置变化；
（4）不当使用可能影响网络稳定性；
（5）本软件不提供任何形式的专业技术支持。

第三章 用户义务与行为规范
第7条 合法使用义务
7.1 用户保证并承诺：
（1）仅在完全遵守所有适用法律法规的前提下使用本软件；
（2）在使用前已获得所有必要的授权和许可；
（3）不利用本软件从事任何违法或侵权活动；
（4）对使用本软件所产生的所有后果承担全部责任。

7.2 用户特别承诺不进行以下行为：
（1）未经授权访问任何计算机系统或网络；
（2）干扰、破坏或未经授权使用网络服务；
（3）传播病毒、蠕虫、特洛伊木马或其他恶意代码；
（4）进行端口扫描、网络探测或其他安全测试（除非获得明确授权）；
（5）发起拒绝服务攻击或分布式拒绝服务攻击。

第8条 网络安全责任
8.1 用户理解并承认：
（1）网络穿透技术可能被滥用于非法目的；
（2）用户有责任确保其使用方式符合网络安全要求；
（3）用户应确保其网络环境的安全配置；
（4）用户应对通过本软件传输的内容负全部责任。

8.2 用户应采取合理措施确保：
（1）仅在自己拥有完全控制权的网络中使用本软件；
（2）不在企业网络、政府网络或敏感网络环境中使用；
（3）使用防火墙和其他安全措施保护本地系统；
（4）定期更新和修补系统漏洞；
（5）监控网络活动，防止未经授权的访问。

第9条 内容责任
9.1 用户应对通过本软件创建、上传、传输、存储或分享的所有内容承担全部法律责任，包括但不限于：
（1）确保内容不侵犯任何第三方知识产权；
（2）确保内容不包含违法或不良信息；
（3）确保内容不危害国家安全或社会公共利益；
（4）确保内容不侵犯他人隐私或人格权利。

9.2 开发者不监控、审查或控制用户通过本软件传输的任何内容，也不对任何用户内容承担责任。

第10条 年龄与能力要求
10.1 用户声明并保证：
（1）如为自然人，已年满18周岁并具有完全民事行为能力；
（2）如未满18周岁，应在监护人指导下使用，并由监护人同意本协议；
（3）具备理解本协议条款和软件功能的技术知识；
（4）有能力判断和承担使用本软件可能带来的风险。

10.2 如用户不具备完全民事行为能力，其监护人应承担所有使用责任。

第四章 知识产权保护
第11条 软件知识产权
11.1 本软件及其所有相关权利，包括但不限于：
（1）源代码、目标代码；
（2）用户界面、设计、图标；
（3）文档、手册、说明材料；
（4）算法、数据结构、技术方案；
均归开发者所有，受著作权法、专利法、商标法和其他知识产权法律保护。

11.2 本协议不授予用户任何知识产权许可，除非明确在本协议中说明。

第12条 禁止逆向工程
12.1 用户同意不对本软件进行以下行为：
（1）反编译、反汇编或逆向工程；
（2）修改、改编、翻译或创建衍生作品；
（3）去除、修改或隐藏任何版权声明、商标或其他专有标记；
（4）分析软件的内部结构、算法或实现细节（纯粹为学习目的的有限分析除外，但不得复制或重用代码）。

12.2 如用户所在司法管辖区的法律允许出于互操作性目的的逆向工程，用户必须在进行此类活动前：
（1）书面通知开发者并说明具体目的；
（2）证明已尝试通过其他方式获得必要信息；
（3）确保不侵犯开发者的知识产权；
（4）仅将获得的信息用于法律允许的目的。

第13条 开源组件声明
13.1 本软件可能包含第三方开源软件组件，这些组件的使用遵守其各自的许可证条款。

13.2 用户同意遵守所有适用的开源许可证条款，特别是：
（1）不违反开源组件的许可证要求；
（2）保留所有版权声明和许可声明；
（3）如开源许可证要求，在分发时提供源代码。

13.3 开源组件的使用不代表开发者对其功能、安全性或适用性作出任何保证。

第五章 免责声明与责任限制
第14条 软件“按现状”提供
14.1 本软件以“按现状”和“按可用”的基础提供，开发者不提供任何形式的明示或暗示保证，包括但不限于：
（1）对适销性、特定用途适用性的保证；
（2）对不侵权的保证；
（3）对功能完整性和无错误的保证；
（4）对连续可用性和可靠性的保证；
（5）对安全性和无病毒性的保证。

14.2 用户理解并接受：
（1）本软件可能存在缺陷、错误或漏洞；
（2）本软件可能与其他软件或硬件不兼容；
（3）使用本软件可能导致数据丢失或系统不稳定；
（4）本软件不提供任何形式的技术支持；
（5）用户应自行承担使用本软件的所有风险。

第15条 技术风险免责
15.1 开发者不对以下情况承担责任：
（1）因使用本软件导致的任何直接、间接、偶然、特殊或 consequential 损害；
（2）数据丢失、损坏或泄露；
（3）系统崩溃、服务中断或性能下降；
（4）任何第三方行为造成的损害；
（5）因用户违反本协议造成的任何后果。

15.2 即使用开发者已被告知可能发生此类损害，本免责条款仍然适用。

第16条 法律风险免责
16.1 用户独立承担因使用本软件而产生的所有法律风险，包括但不限于：
（1）违反当地法律法规的风险；
（2）侵犯第三方权利的风险；
（3）违反网络服务条款的风险；
（4）承担行政处罚或刑事处罚的风险；
（5）面临民事诉讼或索赔的风险。

16.2 开发者不对用户的任何违法行为承担责任，也不为用户提供任何法律保护或辩护支持。

第17条 最大责任限制
17.1 在任何情况下，开发者的总责任（无论是基于合同、侵权还是其他法律理论）均不超过用户为获得本软件使用权而实际支付的金额，或者如用户免费获得，则开发者的责任上限为10美元或等值本地货币。

17.2 某些司法管辖区不允许排除或限制附带损害或间接损害的责任，因此上述限制可能不适用于您。

第六章 隐私与数据保护
第18条 数据收集声明
18.1 为改进软件质量和提供基本功能，本软件可能收集以下非个人身份信息：
（1）软件版本和更新信息；
（2）功能使用频率和模式（匿名统计）；
（3）系统配置和环境信息（硬件类型、操作系统版本等）；
（4）错误报告和崩溃日志（仅包含技术信息，不含个人数据）。

18.2 本软件不会收集、存储或传输：
（1）个人身份信息（姓名、地址、电话、邮箱等）；
（2）网络通信内容；
（3）文件或数据传输内容；
（4）密码、密钥或其他认证凭证。

第19条 用户数据责任
19.1 用户完全负责：
（1）通过本软件传输的任何数据的安全性；
（2）确保数据不包含敏感或个人身份信息；
（3）遵守所有适用的数据保护法律（如GDPR、CCPA等）；
（4）获得数据主体（如涉及他人数据）的必要同意。

19.2 开发者不存储、处理或控制用户通过本软件传输的任何数据，也不对数据的丢失、泄露或滥用承担责任。

第20条 网络安全警告
20.1 用户理解并确认：
（1）网络通信本质上存在安全风险；
（2）内网穿透可能增加安全暴露面；
（3）应假设所有传输的数据可能被第三方截获；
（4）不应通过本软件传输敏感或机密信息。

20.2 用户应采取适当的加密和安全措施保护自己的数据和系统。

第七章 合规与监管要求
第21条 法律法规遵守
21.1 用户必须遵守所有适用的国家、地区和当地法律法规，包括但不限于：
（1）网络安全法、数据保护法；
（2）计算机犯罪相关法律；
（3）知识产权法律；
（4）出口管制法规；
（5）行业特定监管要求。

21.2 用户特别承诺遵守以下规定：
（1）不将本软件用于任何军事或国防目的；
（2）不将本软件出口到受制裁的国家或地区；
（3）不将本软件用于受管制行业（金融、医疗、能源等）；
（4）不违反任何网络服务提供商的使用条款。

第22条 监管配合义务
22.1 如因用户使用本软件而引发监管调查或法律程序，用户应：
（1）独立承担所有责任和后果；
（2）配合监管机构的调查要求；
（3）保护开发者免受任何牵连或损害；
（4）赔偿开发者因此产生的所有费用和损失。

22.2 开发者保留在以下情况下配合执法机构的权利：
（1）收到有效的法院命令或传票；
（2）确信存在迫在眉睫的人身伤害风险；
（3）为保护开发者或他人的合法权利所必需。

第23条 出口管制
23.1 用户确认本软件可能受出口管制法律法规的约束，用户承诺：
（1）不将本软件下载或出口到受限制的国家或地区；
（2）不向受限制的个人或实体提供本软件；
（3）遵守所有适用的贸易制裁和禁运规定；
（4）承担违反出口管制法规的全部责任。

第八章 协议终止与后果
第24条 协议终止
24.1 本协议在以下情况下终止：
（1）用户主动删除本软件并停止使用；
（2）开发者终止软件服务（如有）；
（3）用户违反本协议任何条款；
（4）法律要求终止。

24.2 开发者保留在不事先通知的情况下终止用户使用权的权利，特别是当用户涉嫌违反本协议时。

第25条 终止后果
25.1 协议终止后：
（1）用户必须立即停止使用本软件；
（2）用户必须从所有设备上删除本软件及所有副本；
（3）本协议中按性质应继续有效的条款（如免责声明、责任限制、知识产权保护等）继续有效；
（4）用户仍应对协议终止前的行为承担责任。

25.2 开发者不因协议终止而对用户承担任何责任，包括不退还任何已支付费用（如有）。

第九章 其他条款
第26条 完整协议
26.1 本协议构成用户与开发者之间关于本软件使用的完整协议，取代所有先前的口头或书面协议、谅解或沟通。

26.2 如本协议任何条款被有管辖权的法院认定为无效或不可执行，该条款应在最小必要范围内修改以使其可执行，其余条款继续保持完全效力。

第27条 不可抗力
27.1 开发者不对因超出合理控制范围的情况（包括但不限于自然灾害、战争、恐怖主义行为、政府行为、网络攻击、电力故障等）造成的延误或未能履行义务承担责任。

第28条 通知
28.1 开发者可通过以下方式向用户发出通知：
（1）在软件内显示通知；
（2）在软件发布平台发布公告；
（3）通过电子邮件发送（如用户提供）；
（4）在官方网站上发布。

28.2 通知自发布之时起视为已送达。

第29条 可分割性
29.1 如本协议的任何条款被认定为无效、非法或不可执行，该条款应与本协议分离，不影响其余条款的有效性和可执行性。

第30条 弃权
30.1 开发者未执行本协议任何条款不构成对该条款或任何其他条款的弃权。任何弃权必须以书面形式作出并由开发者明确确认。

第31条 转让
31.1 用户不得转让本协议或本协议下的任何权利或义务。开发者可将本协议转让给关联公司或收购方，转让后原开发者在本协议下的义务终止。

第十章 法律适用与争议解决
第32条 法律适用
32.1 本协议的解释、效力及争议解决应适用开发者所在地法律，但不包括其冲突法规则。

32.2 联合国国际货物销售合同公约不适用于本协议。

第33条 争议解决
33.1 因本协议引起的或与本协议相关的任何争议，双方应首先尝试通过友好协商解决。

33.2 如协商不成，争议应提交开发者所在地有管辖权的人民法院诉讼解决。

33.3 即使用户所在地法律要求不同的争议解决方式，用户仍同意按本条规定解决争议。

33.4 用户同意，任何诉讼必须以个人身份提起，不得作为集体诉讼或代表诉讼的成员。

最终确认条款
第34条 用户确认
34.1 在下载、安装或使用本软件前，用户确认：
（1）已完整阅读、理解并同意接受本协议所有条款的约束；
（2）理解本软件的技术原理和潜在风险；
（3）具备使用本软件所需的技术知识和能力；
（4）已咨询法律顾问（如必要）并了解本协议的法律含义；
（5）使用本软件完全出于个人自愿，未受任何欺骗或胁迫。

34.2 用户进一步确认：
（1）本软件仅为学习工具，不提供任何实际服务保证；
（2）开发者不对用户的使用行为承担任何责任；
（3）用户应对自己的所有行为承担全部法律责任；
（4）如不同意本协议任何条款，应立即退出并删除本软件。

第35条 协议生效
35.1 本协议自以下时间较早者起生效：
（1）用户首次下载、安装或运行本软件；
（2）用户勾选“我同意”或类似确认选项；
（3）用户以其他方式表示接受本协议。

35.2 用户的继续使用构成对本协议的持续接受和确认。

本协议最终解释权归我们（开发者）所有。

请慎重考虑后做出选择：
"""
    
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        width=70,
        height=15,
        font=BW_FONTS["normal"],
        wrap=tk.WORD,
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=15,
        pady=15
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_widget.insert(tk.END, disclaimer_text)
    text_widget.config(state=tk.DISABLED)
    
    action_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    action_frame.pack(fill=tk.X, padx=20, pady=20)
    
    agree_var = tk.BooleanVar(value=False)
    always_agree_var = tk.BooleanVar(value=False)
    
    def on_agree_changed():
        if agree_var.get():
            agree_btn.config(state='normal', bg=BW_COLORS["success"])
        else:
            agree_btn.config(state='disabled', bg=BW_COLORS["secondary"])
    
    agree_check = tk.Checkbutton(
        action_frame,
        text="我已阅读并同意以上所有条款",
        variable=agree_var,
        command=on_agree_changed,
        font=BW_FONTS["normal"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_primary"],
        selectcolor=BW_COLORS["light"],
        activebackground=BW_COLORS["card_bg"],
        activeforeground=BW_COLORS["text_primary"]
    )
    agree_check.pack(pady=(0, 5))
    
    always_agree_check = tk.Checkbutton(
        action_frame,
        text="下次不再显示本免责声明（始终同意）",
        variable=always_agree_var,
        font=BW_FONTS["normal"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["text_primary"],
        selectcolor=BW_COLORS["light"],
        activebackground=BW_COLORS["card_bg"],
        activeforeground=BW_COLORS["text_primary"]
    )
    always_agree_check.pack(pady=(0, 15))    
    btn_container = tk.Frame(action_frame, bg=BW_COLORS["card_bg"])
    btn_container.pack(fill=tk.X)
    
    def agree_and_continue():
        # 如果用户选择了"始终同意"，则创建或修改文件
        if always_agree_var.get():
            try:
                with open("Always-agree-to-the-terms.txt", "w", encoding="utf-8") as f:
                    f.write("true")
            except Exception as e:
                print(f"写入Always-agree-to-the-terms.txt文件时出错: {e}")
        
        disclaimer_window.quit()
        disclaimer_window.destroy()    
    def disagree_and_exit():
        disclaimer_window.quit()
        disclaimer_window.destroy()
        os._exit(0)
    
    agree_btn = create_bw_button(btn_container, "✓ 同意并继续", agree_and_continue, "success", width=15)
    agree_btn.pack(side=tk.LEFT, padx=10)
    agree_btn.config(state='disabled', bg=BW_COLORS["secondary"])
    
    disagree_btn = create_bw_button(btn_container, "✗ 不同意并退出", disagree_and_exit, "danger", width=15)
    disagree_btn.pack(side=tk.RIGHT, padx=10)
    
    disclaimer_window.bind('<Return>', lambda e: agree_and_continue() if agree_var.get() else None)
    disclaimer_window.bind('<Escape>', lambda e: disagree_and_exit())
    
    disclaimer_window.update_idletasks()
    x = (disclaimer_window.winfo_screenwidth() - disclaimer_window.winfo_width()) // 2
    y = (disclaimer_window.winfo_screenheight() - disclaimer_window.winfo_height()) // 2
    disclaimer_window.geometry(f"+{x}+{y}")
    
    disclaimer_window.mainloop()
    return agree_var.get()

# ==============================================
# 公共聊天室模块
# ==============================================

class ChatRoomModule:
    def __init__(self, parent_frame, main_app=None):
        self.parent = parent_frame
        self.main_app = main_app
        self.root = parent_frame.winfo_toplevel() if parent_frame else None
        
        # API配置
        self.api_base = f"https://{api}/public_chat/api"
        self.user_token = None
        self.current_user = None
        
        # 聊天相关
        self.chat_active = False
        self.last_message_id = 0
        self.displayed_message_hashes = set()
        self.pending_messages = []
        self.history_loaded = False
        
        # 在线用户列表
        self.online_users = []
        
        # 注册时的临时信息
        self.pending_email = None
        self.pending_password = None
        
        # 线程管理
        self.thread_queue = queue.Queue()
        
        # 重试机制
        self.retry_count = {}
        self.max_retries = 3
        
        # 创建聊天室UI
        self.create_chat_ui()
        
        # 处理线程队列
        self.process_thread_queue()
        
        # 自动检查登录状态
        self.check_auto_login()
        
        # 启动自动刷新
        self.auto_refresh_messages()
        self.auto_refresh_online_users()
    
    def get_message_hash(self, message):
        """生成消息的唯一哈希"""
        if isinstance(message, dict):
            content = f"{message.get('id', 0)}_{message.get('sender', '')}_{message.get('content', '')}_{message.get('timestamp', 0)}"
        else:
            content = str(message)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def process_thread_queue(self):
        """处理线程队列中的结果"""
        try:
            while True:
                item = self.thread_queue.get_nowait()
                if callable(item):
                    self.root.after(0, item)
                elif isinstance(item, tuple) and len(item) == 2:
                    callback, args = item
                    if callable(callback):
                        if args:
                            self.root.after(0, callback, *args)
                        else:
                            self.root.after(0, callback)
        except queue.Empty:
            pass
        finally:
            if hasattr(self, 'root') and self.root:
                self.root.after(100, self.process_thread_queue)
    
    def run_in_thread(self, func, callback=None, *callback_args):
        """在后台线程中运行函数"""
        def thread_worker():
            try:
                result = func()
                if callback:
                    if callback_args:
                        self.thread_queue.put((callback, (result,) + callback_args))
                    else:
                        self.thread_queue.put((callback, (result,)))
            except Exception as e:
                if callback:
                    self.thread_queue.put((callback, (None, str(e))))
        
        thread = threading.Thread(target=thread_worker, daemon=True)
        thread.start()
    
    def create_chat_ui(self):
        """创建聊天室界面"""
        # 聊天室标题
        chat_header = create_bw_frame(self.parent)
        chat_header.pack(fill=tk.X, padx=10, pady=5)
        
        title_container = tk.Frame(chat_header, bg=BW_COLORS["card_bg"])
        title_container.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(
            title_container,
            text="公共聊天室",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack(side=tk.LEFT)
        
        self.user_status_label = tk.Label(
            title_container,
            text="未登录",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        self.user_status_label.pack(side=tk.RIGHT, padx=5)
        
        # 在线用户区域
        online_frame = create_bw_frame(self.parent)
        online_frame.pack(fill=tk.X, padx=10, pady=5)
        
        online_title = tk.Label(
            online_frame,
            text="在线用户",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        online_title.pack(anchor="w", padx=10, pady=5)
        
        self.online_listbox = tk.Listbox(
            online_frame,
            height=6,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            font=BW_FONTS["small"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"]
        )
        self.online_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        # 用户管理按钮组
        user_btn_frame = tk.Frame(online_frame, bg=BW_COLORS["card_bg"])
        user_btn_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        # 第一行按钮
        btn_row1 = tk.Frame(user_btn_frame, bg=BW_COLORS["card_bg"])
        btn_row1.pack(fill=tk.X, pady=(0, 5))
        
        self.login_btn = create_bw_button(
            btn_row1,
            "登录",
            self.show_login,
            "primary",
            width=8
        )
        self.login_btn.pack(side=tk.LEFT, padx=2)
        
        self.register_btn = create_bw_button(
            btn_row1,
            "注册",
            self.show_register,
            "secondary",
            width=8
        )
        self.register_btn.pack(side=tk.LEFT, padx=2)
        
        # 第二行按钮
        btn_row2 = tk.Frame(user_btn_frame, bg=BW_COLORS["card_bg"])
        btn_row2.pack(fill=tk.X)
        
        self.refresh_online_btn = create_bw_button(
            btn_row2,
            "刷新在线",
            self.refresh_online_users,
            "primary",
            width=8
        )
        self.refresh_online_btn.pack(side=tk.LEFT, padx=2)
        self.refresh_online_btn.config(state='disabled')
        
        self.logout_btn = create_bw_button(
            btn_row2,
            "退出登录",
            self.logout,
            "danger",
            width=8
        )
        self.logout_btn.pack(side=tk.LEFT, padx=2)
        self.logout_btn.config(state='disabled')
        
        # 聊天消息区域
        chat_frame = create_bw_frame(self.parent)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            height=15,
            wrap=tk.WORD,
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=8,
            pady=8
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)
        
        # 历史记录加载状态标签
        self.history_status_label = tk.Label(
            chat_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["warning"]
        )
        self.history_status_label.pack(pady=2)
        
        # 消息输入区域
        input_frame = tk.Frame(self.parent, bg=BW_COLORS["background"])
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.message_entry = tk.Entry(
            input_frame,
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"],
            highlightthickness=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.config(state='disabled')
        
        self.send_btn = create_bw_button(
            input_frame,
            "发送",
            self.send_message,
            "primary",
            width=6
        )
        self.send_btn.pack(side=tk.RIGHT)
        self.send_btn.config(state='disabled')
        
        # 状态栏
        status_frame = tk.Frame(self.parent, bg=BW_COLORS["background"])
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.status_label = tk.Label(
            status_frame,
            text="就绪",
            font=BW_FONTS["small"],
            bg=BW_COLORS["background"],
            fg=BW_COLORS["text_secondary"]
        )
        self.status_label.pack(side=tk.LEFT)
        
        self.online_count_label = tk.Label(
            status_frame,
            text="在线: 0",
            font=BW_FONTS["small"],
            bg=BW_COLORS["background"],
            fg=BW_COLORS["success"]
        )
        self.online_count_label.pack(side=tk.RIGHT)
        
        # 初始日志
        self.log("聊天室已加载，查看消息请登录或注册", is_error=False)
    
    def update_login_state(self):
        """更新登录状态"""
        if self.current_user:
            self.user_status_label.config(text=f"已登录: {self.current_user}", fg=BW_COLORS["success"])
            self.login_btn.config(state='disabled')
            self.register_btn.config(state='disabled')
            self.logout_btn.config(state='normal')
            self.refresh_online_btn.config(state='normal')
            
            if self.history_loaded:
                self.message_entry.config(state='normal')
                self.send_btn.config(state='normal')
            else:
                self.message_entry.config(state='disabled')
                self.send_btn.config(state='disabled')
                self.history_status_label.config(text="正在加载历史记录...", fg=BW_COLORS["warning"])
        else:
            self.user_status_label.config(text="未登录", fg=BW_COLORS["warning"])
            self.login_btn.config(state='normal')
            self.register_btn.config(state='normal')
            self.logout_btn.config(state='disabled')
            self.message_entry.config(state='disabled')
            self.send_btn.config(state='disabled')
            self.refresh_online_btn.config(state='disabled')
            self.history_loaded = False
            self.history_status_label.config(text="")


    def log(self, message, is_error=False):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_error:
            formatted_message = f"[{timestamp}] ✗ {message}"
        else:
            formatted_message = f"[{timestamp}] {message}"
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)
    
    def update_login_state(self):
        """更新登录状态"""
        if self.current_user:
            self.user_status_label.config(text=f"已登录: {self.current_user}", fg=BW_COLORS["success"])
            self.login_btn.config(state='disabled')
            self.logout_btn.config(state='normal')
            self.refresh_online_btn.config(state='normal')
            
            if self.history_loaded:
                self.message_entry.config(state='normal')
                self.send_btn.config(state='normal')
            else:
                self.message_entry.config(state='disabled')
                self.send_btn.config(state='disabled')
                self.history_status_label.config(text="正在加载历史记录...", fg=BW_COLORS["warning"])
        else:
            self.user_status_label.config(text="未登录", fg=BW_COLORS["warning"])
            self.login_btn.config(state='normal')
            self.logout_btn.config(state='disabled')
            self.message_entry.config(state='disabled')
            self.send_btn.config(state='disabled')
            self.refresh_online_btn.config(state='disabled')
            self.history_loaded = False
            self.history_status_label.config(text="")
    

    def check_auto_login(self):
        """检查自动登录"""
        try:
            if os.path.exists("user_session.json"):
                with open("user_session.json", "r", encoding="utf-8") as f:
                    session = json.load(f)
                    
                    def verify_task():
                        return self.verify_token(session.get("token"))
                    
                    self.run_in_thread(
                        verify_task,
                        self.on_auto_login_checked,
                        session
                    )
        except Exception as e:
            self.log(f"自动登录失败: {e}", is_error=True)
    
    def on_auto_login_checked(self, token_valid, session):
        """自动登录检查完成后的回调"""
        if token_valid:
            self.user_token = session["token"]
            self.current_user = session["username"]
            self.update_login_state()
            self.log("✓ 自动登录成功")
            self.refresh_online_users()
            self.start_chat_connection()
            self.load_chat_history()
        else:
            self.log("自动登录失败: Token无效", is_error=True)
    
    def load_chat_history(self):
        """加载历史聊天记录"""
        if not self.current_user:
            return
        
        self.log("正在加载历史聊天记录...")
        self.lock_message_input()
        
        def load_history_task():
            return self.api_get_messages(0)
        
        def on_history_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                messages = result[1] if success else []
            else:
                success = False
                messages = []
            
            if success and messages:
                messages.sort(key=lambda x: x.get('id', 0))
                
                for msg in messages:
                    msg_hash = self.get_message_hash(msg)
                    if msg_hash in self.displayed_message_hashes:
                        continue
                    
                    self.display_message(msg)
                    self.displayed_message_hashes.add(msg_hash)
                    
                    if msg['id'] > self.last_message_id:
                        self.last_message_id = msg['id']
                
                self.history_loaded = True
                self.history_status_label.config(text=f"已加载 {len(messages)} 条历史记录", fg=BW_COLORS["success"])
                self.log(f"✓ 历史记录加载完成，共 {len(messages)} 条消息")
                self.unlock_message_input()
            else:
                self.history_status_label.config(text="历史记录加载失败", fg=BW_COLORS["danger"])
                self.log("✗ 历史记录加载失败", is_error=True)
                self.unlock_message_input()
                self.history_status_label.after(3000, lambda: self.history_status_label.config(text=""))
        
        self.run_in_thread(load_history_task, on_history_complete)
    
    def lock_message_input(self):
        """锁定消息输入和发送功能"""
        self.message_entry.config(state='disabled')
        self.send_btn.config(state='disabled')
        self.history_status_label.config(text="正在加载历史聊天记录...", fg=BW_COLORS["warning"])
        self.update_status("正在加载历史记录...")
    
    def unlock_message_input(self):
        """解锁消息输入和发送功能"""
        if self.current_user and self.history_loaded:
            self.message_entry.config(state='normal')
            self.send_btn.config(state='normal')
            self.update_status("就绪")
            self.root.after(3000, lambda: self.history_status_label.config(text=""))
    
    def save_session(self):
        """保存会话信息"""
        if self.user_token and self.current_user:
            session = {
                "token": self.user_token,
                "username": self.current_user,
                "timestamp": int(time.time())
            }
            try:
                with open("user_session.json", "w", encoding="utf-8") as f:
                    json.dump(session, f, ensure_ascii=False)
            except:
                pass
    
    def clear_session(self):
        """清除会话信息"""
        try:
            if os.path.exists("user_session.json"):
                os.remove("user_session.json")
        except:
            pass
    
    def show_login(self):
        """显示登录窗口"""
        login_window = tk.Toplevel(self.root)
        login_window.title("登录账号")
        login_window.geometry("400x280")
        login_window.resizable(False, False)
        login_window.configure(bg=BW_COLORS["background"])
        login_window.transient(self.root)
        login_window.grab_set()
        
        main_container = create_bw_frame(login_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="登录账号",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            form_frame,
            text="QQ邮箱:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=0, column=0, sticky=tk.W, pady=10, padx=5)
        
        email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=25, font=BW_FONTS["normal"])
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=10)
        
        tk.Label(
            form_frame,
            text="密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=1, column=0, sticky=tk.W, pady=10, padx=5)
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=password_var, width=25, font=BW_FONTS["normal"], show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W, pady=10)
        
        result_label = tk.Label(
            form_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"]
        )
        result_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        def disable_form():
            email_entry.config(state='disabled')
            password_entry.config(state='disabled')
            login_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
            result_label.config(text="正在登录...")
        
        def enable_form():
            email_entry.config(state='normal')
            password_entry.config(state='normal')
            login_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_login_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                data = result[1] if success else result[1]
            else:
                success = False
                data = "未知错误"
            
            enable_form()
            
            if success and data and isinstance(data, dict):
                self.user_token = data.get("token")
                self.current_user = data.get("username")
                if self.user_token and self.current_user:
                    self.save_session()
                    self.update_login_state()
                    login_window.destroy()
                    self.log("✓ 登录成功")
                    self.refresh_online_users()
                    self.start_chat_connection()
                    self.load_chat_history()
                else:
                    result_label.config(text="登录失败: 服务器返回数据不完整")
            else:
                result_label.config(text=f"登录失败: {data}")
        
        def do_login():
            email = email_var.get().strip().lower()
            password = password_var.get().strip()
            
            if not email or not password:
                result_label.config(text="请输入QQ邮箱和密码")
                return
            
            if not email.endswith('@qq.com'):
                result_label.config(text="请使用QQ邮箱登录 (@qq.com)")
                return
            
            disable_form()
            
            def login_task():
                return self.api_login(email, password)
            
            self.run_in_thread(login_task, on_login_complete)
        
        login_btn = create_bw_button(btn_frame, "登录", do_login, "primary", width=10)
        login_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", login_window.destroy, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(
            main_container,
            text="没有账号？请先注册",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        ).pack(pady=(5, 0))
        
        register_btn = create_bw_button(main_container, "注册账号", self.show_register, "secondary", width=15)
        register_btn.pack(pady=5)
        
        email_entry.focus()
        login_window.bind('<Return>', lambda e: do_login())
    
    def show_register(self):
        """显示注册窗口"""
        register_window = tk.Toplevel(self.root)
        register_window.title("注册账号")
        register_window.geometry("400x350")
        register_window.resizable(False, False)
        register_window.configure(bg=BW_COLORS["background"])
        register_window.transient(self.root)
        register_window.grab_set()
        
        main_container = create_bw_frame(register_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="注册账号 (仅限QQ邮箱)",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            form_frame,
            text="QQ邮箱:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=0, column=0, sticky=tk.W, pady=8, padx=5)
        
        email_var = tk.StringVar()
        email_entry = tk.Entry(form_frame, textvariable=email_var, width=25, font=BW_FONTS["normal"])
        email_entry.grid(row=0, column=1, sticky=tk.W, pady=8)
        
        tk.Label(
            form_frame,
            text="用户名:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=1, column=0, sticky=tk.W, pady=8, padx=5)
        
        username_var = tk.StringVar()
        username_entry = tk.Entry(form_frame, textvariable=username_var, width=25, font=BW_FONTS["normal"])
        username_entry.grid(row=1, column=1, sticky=tk.W, pady=8)
        
        tk.Label(
            form_frame,
            text="密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=2, column=0, sticky=tk.W, pady=8, padx=5)
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(form_frame, textvariable=password_var, width=25, font=BW_FONTS["normal"], show="*")
        password_entry.grid(row=2, column=1, sticky=tk.W, pady=8)
        
        tk.Label(
            form_frame,
            text="确认密码:",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).grid(row=3, column=0, sticky=tk.W, pady=8, padx=5)
        
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(form_frame, textvariable=confirm_var, width=25, font=BW_FONTS["normal"], show="*")
        confirm_entry.grid(row=3, column=1, sticky=tk.W, pady=8)
        
        result_label = tk.Label(
            form_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"]
        )
        result_label.grid(row=4, column=0, columnspan=2, pady=10)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        def disable_form():
            email_entry.config(state='disabled')
            username_entry.config(state='disabled')
            password_entry.config(state='disabled')
            confirm_entry.config(state='disabled')
            register_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
            result_label.config(text="正在注册...")
        
        def enable_form():
            email_entry.config(state='normal')
            username_entry.config(state='normal')
            password_entry.config(state='normal')
            confirm_entry.config(state='normal')
            register_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_register_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                data = result[1] if not success else "注册成功"
            else:
                success = False
                data = "未知错误"
            
            enable_form()
            
            if success:
                result_label.config(text="注册成功！请查看QQ邮箱验证", fg=BW_COLORS["success"])
                register_window.after(1000, register_window.destroy)
                self.log("✓ 注册成功，请查收验证邮件")
                self.show_email_verification(email_var.get(), username_var.get())
            else:
                result_label.config(text=f"注册失败: {data}")
        
        def do_register():
            email = email_var.get().strip().lower()
            username = username_var.get().strip()
            password = password_var.get().strip()
            confirm = confirm_var.get().strip()
            
            if not all([email, username, password, confirm]):
                result_label.config(text="请填写所有字段")
                return
            
            if not email.endswith('@qq.com'):
                result_label.config(text="请使用QQ邮箱注册 (@qq.com)")
                return
            
            if password != confirm:
                result_label.config(text="两次输入的密码不一致")
                return
            
            if len(password) < 6:
                result_label.config(text="密码长度至少6位")
                return
            
            if len(username) < 2 or len(username) > 20:
                result_label.config(text="用户名长度2-20个字符")
                return
            
            disable_form()
            
            self.pending_email = email
            self.pending_password = password
            
            def register_task():
                return self.api_register(email, username, password)
            
            self.run_in_thread(register_task, on_register_complete)
        
        register_btn = create_bw_button(btn_frame, "注册", do_register, "primary", width=10)
        register_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", register_window.destroy, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        email_entry.focus()
        register_window.bind('<Return>', lambda e: do_register())
    
    def show_email_verification(self, email, username):
        """显示邮箱验证窗口"""
        verify_window = tk.Toplevel(self.root)
        verify_window.title("邮箱验证")
        verify_window.geometry("400x300")
        verify_window.resizable(False, False)
        verify_window.configure(bg=BW_COLORS["background"])
        verify_window.transient(self.root)
        verify_window.grab_set()
        
        main_container = create_bw_frame(verify_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            main_container,
            text="邮箱验证",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=10)
        
        info_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            info_frame,
            text=f"验证码已发送到您的QQ邮箱：",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"]
        ).pack()
        
        tk.Label(
            info_frame,
            text=email,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        ).pack(pady=(2, 0))
        
        tk.Label(
            info_frame,
            text="请在1小时内完成验证",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        ).pack(pady=(5, 0))
        
        form_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        form_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(
            form_frame,
            text="6位验证码：",
            font=BW_FONTS["normal"],
            bg=BW_COLORS["card_bg"]
        ).pack(pady=(0, 5))
        
        code_var = tk.StringVar()
        code_entry = tk.Entry(
            form_frame,
            textvariable=code_var,
            width=12,
            font=("Consolas", 16, "bold"),
            justify="center",
            bg=BW_COLORS["light"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"]
        )
        code_entry.pack()
        
        result_label = tk.Label(
            main_container,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["danger"]
        )
        result_label.pack(pady=10)
        
        def disable_form():
            code_entry.config(state='disabled')
            verify_btn.config(state='disabled')
            resend_btn.config(state='disabled')
            cancel_btn.config(state='disabled')
        
        def enable_form():
            code_entry.config(state='normal')
            verify_btn.config(state='normal')
            resend_btn.config(state='normal')
            cancel_btn.config(state='normal')
        
        def on_verify_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                message = result[1]
            else:
                success = False
                message = "未知错误"
            
            enable_form()
            
            if success:
                result_label.config(text="✓ 验证成功！正在自动登录...", fg=BW_COLORS["success"])
                verify_window.update()
                verify_window.after(1000, lambda: self.perform_auto_login(verify_window, email))
            else:
                result_label.config(text=f"验证失败: {message}")
        
        def on_resend_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                message = result[1]
            else:
                success = False
                message = "未知错误"
            
            enable_form()
            
            if success:
                messagebox.showinfo("成功", "验证码已重新发送到您的邮箱", parent=verify_window)
            else:
                messagebox.showerror("失败", f"发送失败: {message}", parent=verify_window)
        
        def do_verify():
            code = code_var.get().strip()
            if len(code) != 6 or not code.isdigit():
                result_label.config(text="请输入6位数字验证码")
                return
            
            result_label.config(text="正在验证...")
            disable_form()
            
            def verify_task():
                return self.api_verify_email(email, code)
            
            self.run_in_thread(verify_task, on_verify_complete)
        
        def resend_code():
            disable_form()
            
            def resend_task():
                return self.api_resend_code(email)
            
            self.run_in_thread(resend_task, on_resend_complete)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        verify_btn = create_bw_button(btn_frame, "验证", do_verify, "primary", width=8)
        verify_btn.pack(side=tk.LEFT, padx=5)
        
        resend_btn = create_bw_button(btn_frame, "重新发送", resend_code, "secondary", width=10)
        resend_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", verify_window.destroy, "danger", width=8)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        verify_window.bind('<Return>', lambda e: do_verify())
        code_entry.focus()
    
    def perform_auto_login(self, verify_window, email):
        """执行自动登录"""
        def on_login_complete(result):
            verify_window.destroy()
            
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                login_data = result[1] if success else None
            else:
                success = False
                login_data = None
            
            if success and login_data:
                self.user_token = login_data.get("token")
                self.current_user = login_data.get("username")
                if self.user_token and self.current_user:
                    self.save_session()
                    self.update_login_state()
                    self.log("✓ 自动登录成功")
                    self.refresh_online_users()
                    self.start_chat_connection()
                    self.load_chat_history()
                else:
                    self.log("✗ 自动登录失败：服务器返回数据不完整", is_error=True)
                    messagebox.showinfo("验证成功", "邮箱验证成功！请手动登录。", parent=self.root)
            else:
                self.log("✗ 自动登录失败，请手动登录", is_error=True)
                messagebox.showinfo("验证成功", "邮箱验证成功！请手动登录。", parent=self.root)
        
        def login_task():
            return self.api_login(email, self.pending_password)
        
        self.run_in_thread(login_task, on_login_complete)
    
    def logout(self):
        """退出登录"""
        if messagebox.askyesno("确认退出", "确定要退出登录吗？", parent=self.root):
            self.stop_chat_connection()
            self.user_token = None
            self.current_user = None
            self.history_loaded = False
            self.clear_session()
            self.update_login_state()
            self.clear_online_list()
            self.log("✓ 已退出登录")
            self.displayed_message_hashes.clear()
            self.last_message_id = 0
    
    def refresh_online_users(self):
        """刷新在线用户列表"""
        if not self.current_user:
            return
        
        self.refresh_online_btn.config(state='disabled')
        self.update_status("正在刷新在线用户...")
        
        def on_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                users = result[1] if success else []
            else:
                success = False
                users = []
            
            if self.current_user:
                self.refresh_online_btn.config(state='normal')
            
            if success and users is not None:
                self.online_users = users
                self.update_online_list()
                self.online_count_label.config(text=f"在线: {len(users)}")
                self.update_status("就绪")
            else:
                self.update_status("刷新失败")
        
        def get_online_task():
            return self.api_get_online_users()
        
        self.run_in_thread(get_online_task, on_complete)
    
    def clear_online_list(self):
        """清空在线用户列表"""
        self.online_listbox.delete(0, tk.END)
        self.online_users = []
        self.online_count_label.config(text="在线: 0")
    
    def update_online_list(self):
        """更新在线用户列表显示"""
        self.online_listbox.delete(0, tk.END)
        
        for user in self.online_users:
            if user['username'] == self.current_user:
                display_name = f"{user['username']} (我)"
            else:
                display_name = user['username']
            
            self.online_listbox.insert(tk.END, display_name)
    
    def auto_refresh_online_users(self):
        """自动刷新在线用户列表"""
        if self.current_user:
            def refresh_task():
                return self.api_get_online_users()
            
            def on_refresh_complete(result):
                if isinstance(result, tuple) and len(result) >= 2:
                    success = result[0]
                    users = result[1] if success else []
                else:
                    success = False
                    users = []
                
                if success and users is not None:
                    self.online_users = users
                    self.update_online_list()
                    self.online_count_label.config(text=f"在线: {len(users)}")
            
            self.run_in_thread(refresh_task, on_refresh_complete)
        
        if hasattr(self, 'root') and self.root:
            self.root.after(10000, self.auto_refresh_online_users)
    
    def send_message(self):
        """发送消息"""
        if not self.current_user:
            messagebox.showwarning("提示", "请先登录", parent=self.root)
            return
        
        if not self.history_loaded:
            messagebox.showwarning("提示", "历史记录加载中，请稍后再发送消息", parent=self.root)
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        local_timestamp = int(time.time())
        self.display_local_message(message, local_timestamp)
        self.message_entry.delete(0, tk.END)
        
        pending_msg = {
            "content": message,
            "timestamp": local_timestamp,
            "hash": self.get_message_hash(f"local_{local_timestamp}_{message}")
        }
        self.pending_messages.append(pending_msg)
        
        def send_task():
            return self.api_send_message(message)
        
        def on_send_complete(result):
            if isinstance(result, tuple) and len(result) >= 2:
                success = result[0]
                result_msg = result[1]
            else:
                success = False
                result_msg = "未知错误"
            
            if success:
                self.pending_messages = [msg for msg in self.pending_messages 
                                       if msg["hash"] != pending_msg["hash"]]
                #self.log(f"----------------------------------------- ✓ 消息发送成功")
            else:
                error_msg = f"消息发送失败: {result_msg}"
                self.log(error_msg, is_error=True)
                
                if pending_msg["hash"] not in self.retry_count:
                    self.retry_count[pending_msg["hash"]] = 0
                
                if self.retry_count[pending_msg["hash"]] < self.max_retries:
                    self.retry_count[pending_msg["hash"]] += 1
                    self.log(f"第{self.retry_count[pending_msg['hash']]}次重试发送...")
                else:
                    self.log("消息发送失败，已放弃重试", is_error=True)
        
        self.run_in_thread(send_task, on_send_complete)
    
    def display_local_message(self, message, timestamp=None):
        """本地显示发送的消息（即时反馈）"""
        if timestamp is None:
            timestamp = time.time()
        
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        formatted_message = f"[{time_str}] -"
        msg_hash = self.get_message_hash(f"local_{timestamp}_{message}")
        
        if msg_hash in self.displayed_message_hashes:
            return
        
        self.displayed_message_hashes.add(msg_hash)
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n", "self")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        self.chat_text.tag_config("self", foreground=BW_COLORS["primary"])
        self.chat_text.tag_config("other", foreground=BW_COLORS["text_primary"])
    
    def start_chat_connection(self):
        """启动聊天连接"""
        self.chat_active = True
        self.log("已连接到公共聊天室")
    
    def stop_chat_connection(self):
        """停止聊天连接"""
        self.chat_active = False
        self.log("已断开聊天室连接")
    
    def auto_refresh_messages(self):
        """自动刷新消息"""
        if self.current_user and self.chat_active:
            def get_messages_task():
                return self.api_get_messages(self.last_message_id)
            
            def on_messages_complete(result):
                if isinstance(result, tuple) and len(result) >= 2:
                    success = result[0]
                    messages = result[1] if success else []
                else:
                    success = False
                    messages = []
                
                if success and messages:
                    for msg in messages:
                        msg_hash = self.get_message_hash(msg)
                        if msg_hash in self.displayed_message_hashes:
                            continue
                        
                        self.display_message(msg)
                        self.displayed_message_hashes.add(msg_hash)
                        
                        if msg['id'] > self.last_message_id:
                            self.last_message_id = msg['id']
            
            self.run_in_thread(get_messages_task, on_messages_complete)
        
        if hasattr(self, 'root') and self.root:
            self.root.after(2000, self.auto_refresh_messages)
    
    def display_message(self, message):
        """显示消息"""
        timestamp = message.get("timestamp", time.time())
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        sender = message.get("sender", "未知用户")
        content = message.get("content", "")
        
        if sender == self.current_user:
            formatted_message = f"[{time_str}] <我>: {content}"
            tag = "self"
        else:
            formatted_message = f"[{time_str}] {sender}: {content}"
            tag = "other"
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n", tag)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    # ========== HTTP 请求方法 ==========
    
    def http_request(self, url, method="GET", data=None, headers=None, timeout=10):
        """发送HTTP请求"""
        try:
            if data is not None:
                if method == "GET":
                    if isinstance(data, dict):
                        params = urllib.parse.urlencode(data)
                        url = f"{url}?{params}"
                    data = None
                else:
                    if isinstance(data, dict):
                        data = urllib.parse.urlencode(data).encode('utf-8')
                    else:
                        data = str(data).encode('utf-8')
            
            request_headers = {'User-Agent': 'PublicChat/1.0'}
            if headers:
                request_headers.update(headers)
            
            req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
                
        except urllib.error.URLError as e:
            return {"success": False, "message": f"网络错误: {e.reason}"}
        except urllib.error.HTTPError as e:
            return {"success": False, "message": f"HTTP错误 {e.code}"}
        except json.JSONDecodeError as e:
            return {"success": False, "message": "服务器响应格式错误"}
        except Exception as e:
            return {"success": False, "message": f"请求失败: {str(e)}"}
    
    def verify_token(self, token):
        """验证token"""
        try:
            response = self.http_request(
                f"{self.api_base}/verify_token.php",
                method="POST",
                data={"token": token}
            )
            return response.get("success", False)
        except Exception as e:
            return False
    
    def api_login(self, email, password):
        """API登录"""
        response = self.http_request(
            f"{self.api_base}/login.php",
            method="POST",
            data={
                "email": email,
                "password": password
            }
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data")
        else:
            return False, response.get("message", "未知错误")
    
    def api_register(self, email, username, password):
        """API注册"""
        response = self.http_request(
            f"{self.api_base}/register.php",
            method="POST",
            data={
                "email": email,
                "username": username,
                "password": password
            }
        )
        
        success = response.get("success", False)
        message = response.get("message", "未知错误")
        return success, message
    
    def api_verify_email(self, email, code):
        """验证邮箱"""
        response = self.http_request(
            f"{self.api_base}/verify_email.php",
            method="POST",
            data={
                "email": email,
                "code": code
            }
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_resend_code(self, email):
        """重新发送验证码"""
        response = self.http_request(
            f"{self.api_base}/resend_code.php",
            method="POST",
            data={"email": email}
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_get_online_users(self):
        """获取在线用户列表"""
        params = {"token": self.user_token} if self.user_token else {}
        
        response = self.http_request(
            f"{self.api_base}/get_online_users.php",
            method="GET",
            data=params
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data", [])
        else:
            return False, []
    
    def api_send_message(self, message):
        """发送消息"""
        response = self.http_request(
            f"{self.api_base}/send_message.php",
            method="POST",
            data={
                "token": self.user_token,
                "message": message
            }
        )
        
        success = response.get("success", False)
        return success, response.get("message", "未知错误")
    
    def api_get_messages(self, last_id=0):
        """获取消息"""
        params = {
            "token": self.user_token,
            "last_id": last_id
        }
        
        response = self.http_request(
            f"{self.api_base}/get_messages.php",
            method="GET",
            data=params
        )
        
        success = response.get("success", False)
        if success:
            return True, response.get("data", [])
        else:
            return False, []

# ==============================================
# 主应用程序类
# ==============================================

class LMFP_MinecraftTool:
    def __init__(self, root):
        self.root = root
        self.root.title("LMFP - 4.0 - Lyt_IT - https://www.teft.cn/")
        self.root.state('zoomed')  # 强制最大化窗口
        self.root.configure(bg=BW_COLORS["background"])
        
        self.set_window_icon()
        self.is_admin = self.check_admin_privileges()
        self._cloud_warning_shown = False
        self.cloud_permission_granted = False
        
        # 添加初始化检查状态
        self.check_in_progress = False
        self.announcement_in_progress = False
        
        self.ipv6 = ""
        self.mc_port = None
        self.mc_ports = [25565, 25566, 25567, 19132, 19133]
        self.frp_nodes = []
        self.best_node = None
        
        self.port_mapping_process = None
        self.is_port_mapping_active = False
        self.mapped_port = None
        
        self.frp_process = None
        self.is_frp_running = False
        self.current_room_code = None
        self.current_node_id = None
        self.current_remote_port = None
        self.mc_monitor_thread = None
        
        # TCP隧道相关属性
        self.tunnel_active = False
        self.tunnel_socket = None
        self.tunnel_thread = None
        
        # Windows Job Object for process management
        self.job_object = None
        if platform.system() == "Windows":
            self.create_job_object()        
        self.server_url = f"https://{api}/api.php"
        self.current_rooms = []
        self.room_refresh_thread = None
        self.is_refreshing = False
        self.heartbeat_thread = None
        self.heartbeat_active = False
        self.current_room_info = None
        self.auto_refresh_flag = True
        self.refresh_btn = None
        
        # 聊天室相关
        self.chat_room_var = tk.BooleanVar(value=False)
        self.chat_room_frame = None
        self.chat_room_module = None
        
        self.create_bw_main_frame()
        self.is_scanning = False
        self.is_connecting = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 注册全局退出处理函数，确保在各种终止情况下都能清理FRP进程
        if platform.system() != "Windows":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)        
        # 注册信号处理函数，确保在各种终止情况下都能清理FRP进程
        if platform.system() != "Windows":
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)        
        # 启动后台检查
        self.start_background_checks()
        
        # 启动在线人数获取
        self.start_online_users_check()
        
        # 启动心跳包机制
        self.start_heartbeat_mechanism()
        
    def start_frp_services(self):
        """启动FRP服务端和客户端"""
        try:
            # 停止现有的FRP服务
            self.stop_frp_services()
            
            # 启动FRPS服务端
            if os.path.exists("./frps.exe"):
                if platform.system() == "Windows":
                    self.frps_process = subprocess.Popen(["./frps.exe"], 
                                                       stdout=subprocess.DEVNULL, 
                                                       stderr=subprocess.DEVNULL,
                                                       creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.frps_process = subprocess.Popen(["./frps.exe"], 
                                                       stdout=subprocess.DEVNULL, 
                                                       stderr=subprocess.DEVNULL)
                self.log("✓ FRPS服务端已启动")
            else:
                self.log("⚠ 未找到FRPS服务端程序 ./frps.exe")
                return
            
            # 稍微等待FRPS启动
            time.sleep(1)
            
            # 启动FRPC客户端
            if os.path.exists("./frpc.exe"):
                frpc_cmd = ["./frpc.exe", "tcp", 
                           "--server_addr", "127.0.0.1:7000", 
                           "--proxy_name", "123", 
                           "--local_port", "25565", 
                           "--remote_port", "25565"]
                if platform.system() == "Windows":
                    self.frpc_process = subprocess.Popen(frpc_cmd, 
                                                       stdout=subprocess.DEVNULL, 
                                                       stderr=subprocess.DEVNULL,
                                                       creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    self.frpc_process = subprocess.Popen(frpc_cmd, 
                                                       stdout=subprocess.DEVNULL, 
                                                       stderr=subprocess.DEVNULL)
                self.log("✓ FRPC客户端已启动")
            else:
                self.log("⚠ 未找到FRPC客户端程序 ./frpc.exe")
                
            # 启动Minecraft服务器监控
            self.start_mc_server_monitoring()
                
        except Exception as e:
            self.log(f"✗ 启动FRP服务失败: {e}")
    
    def stop_frp_services(self):
        """停止FRP服务"""
        try:
            # 停止FRPC客户端
            if self.frpc_process and self.frpc_process.poll() is None:
                self.frpc_process.terminate()
                self.frpc_process.wait(timeout=3)
            self.frpc_process = None
            
            # 停止FRPS服务端
            if self.frps_process and self.frps_process.poll() is None:
                self.frps_process.terminate()
                self.frps_process.wait(timeout=3)
            self.frps_process = None
            
        except Exception as e:
            print(f"停止FRP服务时出错: {e}")
            # 强制杀死进程
            try:
                if self.frpc_process:
                    self.frpc_process.kill()
                if self.frps_process:
                    self.frps_process.kill()
            except:
                pass

        
    def create_job_object(self):
        """Create a Windows Job Object to ensure child processes are killed when parent is terminated"""
        try:
            if platform.system() != "Windows":
                return
                
            # Create a job object
            self.job_object = ctypes.windll.kernel32.CreateJobObjectW(None, None)
            
            # Set job object limits
            job_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
            job_info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            
            # Apply the limits to the job object
            ctypes.windll.kernel32.SetInformationJobObject(
                self.job_object,
                JobObjectExtendedLimitInformation,
                ctypes.byref(job_info),
                ctypes.sizeof(job_info)
            )
        except Exception as e:
            print(f"Failed to create job object: {e}")
            self.job_object = None

    def assign_process_to_job(self, process_handle):
        """Assign a process to the job object"""
        try:
            if self.job_object and process_handle:
                ctypes.windll.kernel32.AssignProcessToJobObject(self.job_object, process_handle)
        except Exception as e:
            print(f"Failed to assign process to job object: {e}")

    def start_background_checks(self):
        """启动后台检查和公告显示"""
        def perform_checks():
            # 等待主窗口完全显示
            time.sleep(0.5)
            
            # 在Windows系统上重置端口代理
            if platform.system() == "Windows":
                try:
                    subprocess.run(["netsh", "interface", "portproxy", "reset"], 
                                 capture_output=True, 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
                    print("端口代理已重置")
                except Exception as e:
                    print(f"重置端口代理时出错: {e}")
            
            # 1. 首先检查云端许可
            self.root.after(0, lambda: self.update_cloud_status("正在检查云端许可..."))
            permission_result = check_cloud_permission()
            
            if permission_result:
                self.root.after(0, lambda: self.update_cloud_status("✓ 云端许可验证通过"))
                self.root.after(0, self.enable_all_buttons)
                self.cloud_permission_granted = True
            else:
                self.root.after(0, lambda: self.update_cloud_status("✗ 云端许可验证失败"))
                self.root.after(0, self.disable_all_buttons)
                self.cloud_permission_granted = False
                
                # 显示云端许可警告
                self.root.after(500, lambda: self.show_cloud_permission_failed_warning())
                return  # 如果许可失败，不继续检查公告
            
            # 2. 检查公告
            self.root.after(0, lambda: self.update_cloud_status("正在检查公告..."))
            announcements_info = check_announcements()
            
            if announcements_info and announcements_info.get('has_new_announcements'):
                self.root.after(0, lambda: self.update_cloud_status(f"-----------------------------------"))
                # 延迟显示公告窗口，让用户先看到主界面
                self.root.after(1000, lambda: self.show_announcements(announcements_info))
            else:
                self.root.after(0, lambda: self.update_cloud_status("-----------------------------------"))
        
        threading.Thread(target=perform_checks, daemon=True).start()
    
    def start_online_users_check(self):
        """启动在线人数检查"""
        # 立即获取一次在线人数
        self.get_online_users_count()
        # 每5秒自动刷新一次
        self.root.after(5000, self.start_online_users_check)
    
    def get_online_users_count(self):
        """获取在线用户数量"""
        def fetch_online_count():
            try:
                # 从远程接口获取在线人数
                url = f"https://{api}/rs.php"
                req = Request(url, headers={'User-Agent': 'LMFP/4.0.0'})
                
                with urlopen(req, timeout=10) as response:
                    content = response.read().decode('utf-8').strip()
                    
                    # 尝试解析返回的数字
                    try:
                        online_count = int(content)
                        self.root.after(0, lambda: self.update_online_users_display(online_count))
                    except ValueError:
                        # 如果无法解析为整数，显示原始内容
                        self.root.after(0, lambda: self.update_online_users_display(content))
            except Exception as e:
                print(f"获取在线人数失败: {e}")
                self.root.after(0, lambda: self.update_online_users_display("获取失败"))
        
        # 在后台线程中执行，避免阻塞UI
        threading.Thread(target=fetch_online_count, daemon=True).start()
    
    def update_online_users_display(self, count):
        """更新在线人数显示"""
        if isinstance(count, int):
            self.online_users_label.config(text=f"当前在线用户：{count}人", fg=BW_COLORS["success"])
        else:
            self.online_users_label.config(text=f"当前在线用户：{count}", fg=BW_COLORS["warning"])
    
    def start_heartbeat_mechanism(self):
        """启动心跳包机制"""
        # 启动主界面后开始发送心跳包
        self.send_heartbeat()
        # 设置定时器，每5秒发送一次心跳包
        self.heartbeat_timer = self.root.after(5000, self.start_heartbeat_mechanism)
    
    def send_heartbeat(self):
        """发送心跳包"""
        def send_heartbeat_request():
            try:
                import uuid
                from urllib.parse import urlencode
                
                # 获取本机MAC地址作为用户标识
                # 使用uuid.getnode()获取MAC地址
                mac_int = uuid.getnode()
                # 格式化为12位十六进制字符串（无分隔符）
                user_id = '{:012x}'.format(mac_int)
                
                # 构造POST数据
                post_data = {
                    'user_id': user_id,
                    'action': 'heartbeat'
                }
                
                # 发送POST请求
                url = f"https://{api}/rs.php"
                data = urlencode(post_data).encode('utf-8')
                req = Request(url, data=data, headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': 'LMFP/4.0.0'
                })
                
                with urlopen(req, timeout=5) as response:
                    result = response.read().decode('utf-8')
                    print(f"心跳包发送成功: {result}")
            except Exception as e:
                print(f"心跳包发送失败: {e}")
        
        # 在后台线程中执行，避免阻塞UI
        threading.Thread(target=send_heartbeat_request, daemon=True).start()
    
    def stop_heartbeat_mechanism(self):
        """停止心跳包机制"""
        if hasattr(self, 'heartbeat_timer'):
            self.root.after_cancel(self.heartbeat_timer)
            print("心跳包机制已停止")
    
    def update_cloud_status(self, message):
        """更新云端许可状态显示"""
        if hasattr(self, 'cloud_status_label'):
            self.cloud_status_label.config(text=message)
            
            # 根据消息内容设置颜色
            if "✓" in message or "通过" in message:
                self.cloud_status_label.config(fg=BW_COLORS["success"])
            elif "✗" in message or "失败" in message:
                self.cloud_status_label.config(fg=BW_COLORS["danger"])
            elif "正在" in message:
                self.cloud_status_label.config(fg=BW_COLORS["primary"])
            else:
                self.cloud_status_label.config(fg=BW_COLORS["text_secondary"])
    
    def show_announcements(self, announcements_info):
        """显示公告窗口"""
        if not self.announcement_in_progress:
            self.announcement_in_progress = True
            show_announcements_window(announcements_info, self.root)
            self.announcement_in_progress = False
    
    def show_cloud_permission_failed_warning(self):
        """显示云端许可失败警告"""
        if self._cloud_warning_shown:
            return
            
        self._cloud_warning_shown = True
        
        warning_window = tk.Toplevel(self.root)
        warning_window.title("⚠ 软件许可警告")
        warning_window.geometry("500x560")
        warning_window.resizable(False, False)
        warning_window.configure(bg=BW_COLORS["background"])
        warning_window.transient(self.root)
        warning_window.attributes('-topmost', True)
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                warning_window.iconbitmap(icon_path)
        except:
            pass
        
        def on_warning_close():
            self._cloud_warning_shown = False
            warning_window.destroy()
        
        warning_window.protocol("WM_DELETE_WINDOW", on_warning_close)
        
        main_container = create_bw_frame(warning_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        warning_icon = tk.Label(
            header_frame,
            text="⚠",
            font=("Arial", 24),
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        warning_icon.pack(side=tk.LEFT, padx=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="软件许可警告",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        title_label.pack(side=tk.LEFT)
        
        content_frame = create_bw_frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        warning_text = """
检测到当前软件使用许可可能存在问题。

可能的原因：
• 软件版本过旧，请更新到最新版本
• 服务器维护或升级期间
• 网络连接问题
• 软件使用权限受限

当前状态：
• 软件功能已被锁定
• 所有按钮已禁用
• 需要重新验证许可后才能继续使用

请选择以下操作：
"""
        
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            width=50,
            height=15,
            font=BW_FONTS["normal"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=10,
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert(tk.END, warning_text)
        text_widget.config(state=tk.DISABLED)
        
        button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        button_frame.pack(fill=tk.X, padx=20, pady=15)
        
        def refresh_check():
            if check_cloud_permission():
                messagebox.showinfo("检查通过", "✓ 软件使用许可已恢复！\n\n软件功能已重新启用。", parent=warning_window)
                self.enable_all_buttons()
                self.update_cloud_status("✓ 云端许可验证通过")
                on_warning_close()
            else:
                messagebox.showwarning("检查失败", "⚠ 软件使用许可仍未恢复。\n\n所有功能保持锁定状态。", parent=warning_window)
        
        def exit_software():
            self.on_closing()
            self.root.quit()
        
        refresh_btn = create_bw_button(button_frame, "⟳ 重新验证许可", refresh_check, "primary", width=18)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_software, "danger", width=15)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        warning_window.update_idletasks()
        x = (warning_window.winfo_screenwidth() - warning_window.winfo_width()) // 2
        y = (warning_window.winfo_screenheight() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")
        
        warning_window.grab_set()
    
    def create_bw_main_frame(self):
        """创建横版黑白灰风格主界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=BW_COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 左侧功能区域
        left_frame = tk.Frame(main_container, bg=BW_COLORS["background"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # 中间联机大厅区域
        center_frame = tk.Frame(main_container, bg=BW_COLORS["background"])
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 右侧聊天室区域（初始隐藏）
        self.right_frame = tk.Frame(main_container, bg=BW_COLORS["background"])
        
        # 左侧功能区域内容
        self.create_left_function_area(left_frame)
        
        # 中间联机大厅区域内容
        self.create_center_lobby_area(center_frame)
        
        # 监听聊天室复选框变化
        self.chat_room_var.trace('w', self.toggle_chat_room)
    
    def create_left_function_area(self, parent):
        """创建左侧功能区域"""
        # 标题区域
        header_frame = create_bw_frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        title_container.pack(fill=tk.X, padx=15, pady=12)
        
        title_label = tk.Label(
            title_container,
            text="LMFP - Minecraft联机平台",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        version_label = tk.Label(
            title_container,
            text="v.4.0 - Lyt_IT - https://www.teft.cn/",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        version_label.pack(pady=(2, 0))
        
        # 状态信息
        status_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        status_container.pack(fill=tk.X, padx=15, pady=(0, 12))
        
        admin_status = "✓ 已获取管理员权限" if self.is_admin else "⚠ 未获取管理员权限"
        admin_label = tk.Label(
            status_container,
            text=admin_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["success"] if self.is_admin else BW_COLORS["warning"]
        )
        admin_label.pack(anchor="w")
        
        cloud_status = "正在初始化..." 
        self.cloud_status_label = tk.Label(
            status_container,
            text=cloud_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.cloud_status_label.pack(anchor="w", pady=(2, 0))
        
        # 在线人数显示
        self.online_users_label = tk.Label(
            status_container,
            text="当前在线用户：正在获取...",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.online_users_label.pack(anchor="w", pady=(2, 0))
        
        author_label = tk.Label(
            status_container,
            text="本软件开发者: Lyt_IT | QQ: 2232908600",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        author_label.pack(anchor="w", pady=(5, 0))
        
        # 聊天室复选框
        chat_container = tk.Frame(header_frame, bg=BW_COLORS["card_bg"])
        chat_container.pack(fill=tk.X, padx=15, pady=(5, 0))
        
        chat_check = tk.Checkbutton(
            chat_container,
            text="显示公共聊天室",
            variable=self.chat_room_var,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_primary"],
            selectcolor=BW_COLORS["light"],
            activebackground=BW_COLORS["card_bg"],
            activeforeground=BW_COLORS["text_primary"]
        )
        chat_check.pack(anchor="w")
        
        # 功能按钮区域
        functions_frame = create_bw_frame(parent)
        functions_frame.pack(fill=tk.X, pady=(0, 15))
        
        create_section_title(functions_frame, "联机模式选择")
        
        buttons_container = tk.Frame(functions_frame, bg=BW_COLORS["card_bg"])
        buttons_container.pack(fill=tk.X, padx=15, pady=12)
        
        # 调整按钮宽度以适应左侧区域
        self.ipv6_btn = create_bw_button(
            buttons_container,
            "获取IPv6联机地址（备选联机方法）",
            self.run_ipv6_mode,
            "primary"
        )
        self.ipv6_btn.pack(fill=tk.X, pady=6)
        self.ipv6_btn.config(state='disabled')
        
        self.frp_create_btn = create_bw_button(
            buttons_container,
            "内网穿透联机 - 创建联机房间（我要当房主）",
            self.run_frp_create,
            "secondary"
        )
        self.frp_create_btn.pack(fill=tk.X, pady=6)
        self.frp_create_btn.config(state='disabled')
        
        self.frp_join_btn = create_bw_button(
            buttons_container,
            "内网穿透联机 - 加入联机房间（我要进别人的房间）",
            self.run_frp_join,
            "secondary"
        )
        self.frp_join_btn.pack(fill=tk.X, pady=6)
        self.frp_join_btn.config(state='disabled')
        
        self.port_map_btn = create_bw_button(
            buttons_container,
            "自定义端口映射到25565（适用于MC不支持自定义端口的版本）",
            self.run_port_mapping,
            "primary"
        )
        self.port_map_btn.pack(fill=tk.X, pady=6)
        self.port_map_btn.config(state='disabled')
        
        self.stop_btn = create_bw_button(
            buttons_container,
            "关闭本回25565隧道（当联机出问题  请尝试点一次这个）",
            self.stop_tcp_tunnel,
            "danger"
        )
        self.stop_btn.pack(fill=tk.X, pady=6)
        self.stop_btn.config(state='disabled')
        
        # 状态日志区域
        status_frame = create_bw_frame(parent)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        create_section_title(status_frame, "状态信息")
        
        status_text_container = tk.Frame(status_frame, bg=BW_COLORS["card_bg"])
        status_text_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        self.status_text = scrolledtext.ScrolledText(
            status_text_container,
            height=8,
            width=40,
            font=BW_FONTS["normal"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=8,
            pady=8
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)
        self.status_text.insert(tk.END, "软件启动中...\n正在检查云端许可和公告...\n")
        self.status_text.config(state=tk.DISABLED)        
        # 底部按钮区域
        bottom_frame = tk.Frame(parent, bg=BW_COLORS["background"])
        bottom_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.clear_btn = create_bw_button(bottom_frame, "清空日志", self.clear_log, "secondary", width=10)
        self.clear_btn.pack(side=tk.LEFT, padx=2)
        self.clear_btn.config(state='disabled')
        
        self.help_btn = create_bw_button(bottom_frame, "使用帮助", self.show_help, "primary", width=10)
        self.help_btn.pack(side=tk.LEFT, padx=2)
        self.help_btn.config(state='disabled')
        
        self.qq_group_btn = create_bw_button(bottom_frame, "加入QQ群", self.open_qq_group, "primary", width=10)
        self.qq_group_btn.pack(side=tk.LEFT, padx=2)
        
        self.exit_btn = create_bw_button(bottom_frame, "退出程序", self.root.quit, "danger", width=10)
        self.exit_btn.pack(side=tk.RIGHT, padx=2)
    
    def create_center_lobby_area(self, parent):
        """创建中间联机大厅区域"""
        # 联机大厅框架
        lobby_frame = create_bw_frame(parent)
        lobby_frame.pack(fill=tk.BOTH, expand=True)
        
        # 大厅标题
        lobby_title_frame = tk.Frame(lobby_frame, bg=BW_COLORS["card_bg"])
        lobby_title_frame.pack(fill=tk.X, padx=15, pady=10)
        
        lobby_title = tk.Label(
            lobby_title_frame,
            text="联机大厅 - 公开房间列表",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        lobby_title.pack(side=tk.LEFT)
        
        # 刷新按钮区域
        lobby_btn_frame = tk.Frame(lobby_title_frame, bg=BW_COLORS["card_bg"])
        lobby_btn_frame.pack(side=tk.RIGHT)
        
        self.lobby_refresh_btn = create_bw_button(lobby_btn_frame, "⟳ 刷新", 
                                                lambda: self.refresh_rooms(), "primary", width=8)
        self.lobby_refresh_btn.pack(side=tk.LEFT, padx=2)
        self.lobby_refresh_btn.config(state='disabled')
        
        self.lobby_join_btn = create_bw_button(lobby_btn_frame, "加入选中的房间", 
                                             self.join_selected_room, "success", width=12)
        self.lobby_join_btn.pack(side=tk.LEFT, padx=2)
        self.lobby_join_btn.config(state='disabled')
        
        # 状态提示
        tip_frame = tk.Frame(lobby_frame, bg=BW_COLORS["card_bg"])
        tip_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tip_text = "提示: 点击房间行查看详情，点击右侧'加入'按钮加入房间"
        tip_color = BW_COLORS["text_secondary"]
        
        tk.Label(tip_frame, text=tip_text, font=BW_FONTS["small"], 
                fg=tip_color, wraplength=400, justify=tk.CENTER, bg=BW_COLORS["card_bg"]).pack()
        
        # 房间列表区域
        list_frame = create_bw_frame(lobby_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 创建Treeview用于显示房间列表
        columns = ("房间号", "房间人数", "房主", "版本", "识别版本", "服务器地址", "房间标题", "描述", "节点延迟", "状态", "操作")
        self.room_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # 设置列宽
        self.room_tree.column("房间号", width=80, anchor=tk.W)
        self.room_tree.column("房间人数", width=80, anchor=tk.W)
        self.room_tree.column("房主", width=80, anchor=tk.W)
        self.room_tree.column("版本", width=90, anchor=tk.W)
        self.room_tree.column("识别版本", width=90, anchor=tk.W)
        self.room_tree.column("服务器地址", width=150, anchor=tk.W)
        self.room_tree.column("房间标题", width=110, anchor=tk.W)
        self.room_tree.column("描述", width=130, anchor=tk.W)
        self.room_tree.column("节点延迟", width=60, anchor=tk.W)
        self.room_tree.column("状态", width=60, anchor=tk.W)
        self.room_tree.column("操作", width=40, anchor=tk.W)
        
        # 设置列标题
        for col in columns:
            self.room_tree.heading(col, text=col, anchor=tk.W)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.room_tree.yview)
        self.room_tree.configure(yscrollcommand=scrollbar.set)
        
        self.room_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 房间详情区域
        detail_frame = create_bw_frame(lobby_frame)
        detail_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        detail_label = tk.Label(detail_frame, text="房间详情:", font=BW_FONTS["small"], 
                               bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"])
        detail_label.pack(anchor=tk.W, padx=10, pady=5)
        
        self.room_detail_text = tk.Text(
            detail_frame,
            height=4,
            width=60,
            font=BW_FONTS["small"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=10,
            pady=5
        )
        self.room_detail_text.pack(fill=tk.X, padx=10, pady=(0, 5))
        self.room_detail_text.config(state=tk.DISABLED)
        self.room_detail_text.insert(tk.END, "等待云端许可验证通过后加载房间列表...")
        
        # 底部状态栏
        status_bar_frame = tk.Frame(lobby_frame, bg=BW_COLORS["card_bg"])
        status_bar_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.lobby_status = tk.Label(status_bar_frame, text="等待云端许可验证...", font=BW_FONTS["small"],
                                   bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.lobby_status.pack(side=tk.LEFT)
        
        self.last_update_label = tk.Label(status_bar_frame, text="", font=BW_FONTS["small"],
                                        bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.last_update_label.pack(side=tk.RIGHT)
        
        # 绑定事件
        self.room_tree.bind("<ButtonRelease-1>", self.on_room_click)
        self.room_tree.bind("<Double-Button-1>", self.on_room_double_click)
    
    def toggle_chat_room(self, *args):
        """切换聊天室显示"""
        if self.chat_room_var.get():
            # 显示聊天室
            self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0))
            self.right_frame.config(width=300)  # 设置宽度为300
            
            # 创建聊天室框架
            self.chat_room_frame = create_bw_frame(self.right_frame)
            self.chat_room_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 初始化聊天室模块
            self.chat_room_module = ChatRoomModule(self.chat_room_frame, self)
            
            # 更新窗口大小
            # 窗口已强制最大化，无需调整尺寸
        else:
            # 隐藏聊天室
            if self.chat_room_module:
                # 停止聊天室相关线程
                self.chat_room_module.stop_chat_connection()
                self.chat_room_module = None
            
            if self.chat_room_frame:
                self.chat_room_frame.destroy()
                self.chat_room_frame = None
            
            self.right_frame.pack_forget()
            
            # 窗口已强制最大化，无需调整尺寸
        
        self.root.update_idletasks()
    
    def set_window_icon(self):
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                possible_paths = [
                    "./lyy.ico", "lyy.ico",
                    os.path.join(os.path.dirname(__file__), "lyy.ico"),
                    os.path.join(os.path.dirname(sys.executable), "lyy.ico")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        self.root.iconbitmap(path)
                        break
                else:
                    print("未找到 lyy.ico 图标文件，使用默认图标")
        except Exception as e:
            print(f"设置图标失败: {e}")
    
    def check_admin_privileges(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def lock_buttons(self):
        buttons = [self.ipv6_btn, self.frp_create_btn, self.frp_join_btn, 
                  self.port_map_btn, self.stop_btn,
                  self.clear_btn, self.help_btn]
        
        for btn in buttons:
            btn.config(state='disabled', bg=BW_COLORS["text_secondary"])
        self.root.update()
        
    def unlock_buttons(self):
        buttons_config = [
            (self.ipv6_btn, "primary"),
            (self.frp_create_btn, "secondary"), 
            (self.frp_join_btn, "secondary"),
            (self.port_map_btn, "primary"),
            (self.stop_btn, "danger"),
            (self.clear_btn, "secondary"),
            (self.help_btn, "primary")
        ]
        
        for btn, style in buttons_config:
            btn.config(state='normal', bg=BW_COLORS[style])
        self.root.update()
    
    def enable_all_buttons(self):
        self.cloud_permission_granted = True
        self.unlock_buttons()
        self.log("✓ 云端许可验证通过，所有功能已启用")
        self.status_text.see(tk.END)
        # 启用联机大厅按钮
        self.lobby_refresh_btn.config(state='normal')
        self.lobby_join_btn.config(state='normal')
        # 初始化后开始自动刷新
        self.root.after(2000, self.refresh_rooms)
    
    def disable_all_buttons(self):
        self.cloud_permission_granted = False
        self.lock_buttons()
        self.log("✗ 云端许可验证失败，所有功能已禁用")
        self.status_text.see(tk.END)
        # 禁用联机大厅按钮
        self.lobby_refresh_btn.config(state='disabled')
        self.lobby_join_btn.config(state='disabled')
    
    def log(self, message):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.config(state=tk.DISABLED)
        self.status_text.see(tk.END)
        self.root.update_idletasks()    
    def clear_log(self):
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)


    def open_qq_group(self):
        """打开QQ群链接"""
        try:
            import webbrowser
            # 从qun.txt获取实际的网址
            req = Request(f"https://{api}/qun.txt", headers={'User-Agent': 'LMFP/4.0.0'})
            with urlopen(req, timeout=10) as response:
                redirect_url = response.read().decode('utf-8').strip()
            # 打开获取到的网址
            webbrowser.open(redirect_url)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开QQ群链接: {e}")

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                help_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(help_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="使用帮助",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        content_frame = create_bw_frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        help_text = scrolledtext.ScrolledText(
            content_frame,
            width=80,
            height=20,
            font=BW_FONTS["normal"],
            wrap=tk.WORD,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=15,
            pady=15
        )
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        help_content = """
LMFP - Minecraft联机平台使用说明

IPv6联机模式：
• 需要双方都有IPv6网络支持
• 速度快，延迟低  
• 端口自动检测
• 自动复制联机地址到剪贴板

FRP创建房间：
• 无需IPv6，使用中转服务器
• 自动选择最佳节点
• 端口自动检测
• 生成房间号：远程端口_FRP服务器号
• 可选择公开或私有房间

FRP进入房间：
• 输入朋友分享的房间号
• 自动从云端获取FRP服务器信息
• 使用TCP隧道将远程服务器映射到127.0.0.1:25565
• 无需启动FRP客户端

端口映射功能：
• 将其他Minecraft端口映射到25565
• 方便使用非标准端口的服务器
• 自动关闭防火墙规则
• 程序退出时自动清理映射

联机大厅（右侧）：
• 浏览所有公开房间
• 30秒自动刷新房间列表
• 双击或点击"加入"按钮快速加入
• 显示房间详细信息（包括房间描述）

公共聊天室：
• 实时在线聊天功能
• QQ邮箱注册登录
• 邮箱验证系统
• 显示在线用户列表
• 自动刷新消息

停止TCP隧道连接：
• 强制停止当前TCP隧道
• 解决连接冲突问题
• 安全清理网络连接

云端许可验证：
• 软件启动时需要验证云端许可
• 使用过程中会定期检查许可状态
• 如果许可验证失败，所有功能将被锁定
• 需要重新验证通过后才能继续使用

公告功能：
• 软件启动时自动检查新公告
• 有新公告时会弹出公告窗口
• 公告支持多标签页浏览
• 可标记为已读

常见问题：
1. 如果无法连接，请检查防火墙设置
2. 确保已开启Minecraft局域网游戏
3. 联机时不要关闭程序窗口
4. 每人只能同时运行一个TCP隧道

技术支持：
QQ: 2232908600
微信: liuyvetong
        """
        
        help_text.insert(1.0, help_content)
        help_text.config(state=tk.DISABLED)
        
        close_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        close_frame.pack(fill=tk.X, padx=20, pady=15)
        
        close_btn = create_bw_button(close_frame, "关闭", help_window.destroy, "primary", width=12)
        close_btn.pack()
    
    def validate_ipv6(self, ipv6):
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^([0-9a-fA-F]{1,4}:){1,7}:|^:(:[0-9a-fA-F]{1,4}){1,7}$'
        return re.match(ipv6_pattern, ipv6) is not None
    
    def get_ipv6_powershell(self):
        try:
            ps_command = """
            Get-NetIPAddress -AddressFamily IPv6 | 
            Where-Object {
                $_.PrefixOrigin -eq 'RouterAdvertisement' -and 
                $_.SuffixOrigin -ne 'Link' -and 
                $_.IPAddress -notlike 'fe80*' -and 
                $_.IPAddress -notlike 'fc*' -and 
                $_.IPAddress -notlike 'fd*' -and 
                $_.IPAddress -ne '::1'
            } | 
            Select-Object -First 1 -ExpandProperty IPAddress
            """
            
            result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, check=True)
            ipv6 = result.stdout.strip()
            if ipv6 and self.validate_ipv6(ipv6):
                return ipv6
        except Exception:
            pass
        return None
    
    def get_ipv6_ipconfig(self):
        try:
            result = subprocess.run(["ipconfig"], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if "IPv6" in line and ":" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        ipv6 = parts[1].strip()
                        self.log(f"检查地址: {ipv6}")
                        if re.match(r"^2[0-9a-f][0-9a-f][0-9a-f]:", ipv6) and self.validate_ipv6(ipv6):
                            return ipv6
        except Exception:
            pass
        return None
    
    def copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            return True
        except Exception:
            return False
    
    def is_port_occupied(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except Exception:
            return False

    def is_port_occupied_by_java_original(self, port):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                
                for line in lines:
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        for part in parts:
                            if part.isdigit() and len(part) > 3:
                                pid = part
                                task_result = subprocess.run(
                                    ["tasklist", "/fi", f"pid eq {pid}", "/fo", "csv"], 
                                    capture_output=True, text=True, check=True
                                )
                                if "java.exe" in task_result.stdout:
                                    self.log(f"端口 {port} 被Java进程占用 (PID: {pid})")
                                    return True
                return False
            else:
                result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True, check=True)
                return "java" in result.stdout
        except Exception as e:
            self.log(f"检查端口占用时出错: {e}")
            return False

    def is_port_occupied_by_java(self, port):
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"端口映射激活中，检查映射源端口 {self.mapped_port}")
            return self.is_port_occupied_by_java_original(self.mapped_port)
        return self.is_port_occupied_by_java_original(port)
    
    def get_java_process_ports(self):
        java_ports = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                
                java_pids = set()
                task_result = subprocess.run(
                    ["tasklist", "/fi", "imagename eq java.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in task_result.stdout.split('\n'):
                    if 'java.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_pids.add(pid)
                
                for line in lines:
                    if "LISTENING" in line:
                        parts = line.split()
                        for part in parts:
                            if ":" in part and "[" not in part:
                                try:
                                    port_str = part.split(":")[-1]
                                    port = int(port_str)
                                    for p in parts:
                                        if p.isdigit() and len(p) > 3:
                                            if p in java_pids and port not in java_ports:
                                                java_ports.append(port)
                                                self.log(f"发现Java进程监听端口: {port}")
                                                break
                                except ValueError:
                                    continue
            else:
                result = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True, check=True)
                for line in result.stdout.split('\n'):
                    if "java" in line and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            port_part = parts[8]
                            if ":" in port_part:
                                try:
                                    port = int(port_part.split(":")[1])
                                    if port not in java_ports:
                                        java_ports.append(port)
                                        self.log(f"发现Java进程监听端口: {port}")
                                except ValueError:
                                    continue
        except Exception as e:
            self.log(f"获取Java进程端口时出错: {e}")
        return java_ports
    
    def tcping_port(self, port):
        actual_port = port
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"端口映射激活中，实际检查端口 {self.mapped_port}")
            actual_port = self.mapped_port
        
        self.log(f"正在验证端口 {actual_port} 是否为Minecraft联机端口...")
        
        try:
            with socket.socket(socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                target_host = self.ipv6 if self.ipv6 else '127.0.0.1'
                s.connect((target_host, actual_port))
                self.log(f"端口 {actual_port} TCP连接成功")
                
                try:
                    s.settimeout(1)
                    data = s.recv(1024)
                    if data:
                        self.log(f"端口 {actual_port} 有数据响应，可能是Minecraft服务")
                        return True
                    else:
                        self.log(f"端口 {actual_port} 连接成功但无数据响应")
                        return False
                except socket.timeout:
                    self.log(f"端口 {actual_port} 连接成功但读取超时，可能是Minecraft服务")
                    return True
                except Exception as e:
                    self.log(f"端口 {actual_port} 读取数据时出错: {e}")
                    return False
        except socket.timeout:
            self.log(f"端口 {actual_port} 连接超时")
            return False
        except ConnectionRefusedError:
            self.log(f"端口 {actual_port} 连接被拒绝")
            return False
        except Exception as e:
            self.log(f"端口 {actual_port} 连接失败: {e}")
            return False
    
    def mcstatus_port(self, port):
        """
        使用mcstatus库检测端口是否为Minecraft服务器端口
        """
        actual_port = port
        if self.is_port_mapping_active and port == 25565 and self.mapped_port:
            self.log(f"端口映射激活中，实际检查端口 {self.mapped_port}")
            actual_port = self.mapped_port
            
        self.log(f"正在使用mcstatus验证端口 {actual_port} 是否为Minecraft联机端口...")
        
        if not MCSTATUS_AVAILABLE:
            self.log("✗ mcstatus库不可用，回退到tcping方法")
            return self.tcping_port(port)
            
        try:
            server = JavaServer.lookup(f"127.0.0.1:{actual_port}")
            status = server.status()
            self.log(f"✓ 端口 {actual_port} 是Minecraft服务器，玩家数: {status.players.online}/{status.players.max}")
            return True
        except Exception as e:
            self.log(f"✗ 端口 {actual_port} 不是Minecraft服务器或无法连接: {e}")
            return False    
    def check_minecraft_ports(self):
        self.log("正在检测Minecraft端口...")
        
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"端口映射激活中，直接使用映射端口 {self.mapped_port}")
            if self.mcstatus_port(self.mapped_port):
                self.log(f"✓ 映射源端口 {self.mapped_port} 验证通过")
                return 25565
            else:
                self.log(f"✗ 映射源端口 {self.mapped_port} 验证失败")
                return None
        
        candidate_ports = []
        
        if not self.is_port_occupied(25565):
            self.log("25565端口未被占用，开始检测Java进程监听的端口...")
            java_ports = self.get_java_process_ports()
            
            if java_ports:
                for port in java_ports:
                    if port in self.mc_ports:
                        candidate_ports.append(port)
                
                if not candidate_ports:
                    candidate_ports = java_ports
            else:
                self.log("未找到Java进程监听的端口")
                return None
        else:
            self.log("25565端口已被占用，添加到候选端口")
            candidate_ports.append(25565)
        
        valid_ports = []
        for port in candidate_ports:
            if self.mcstatus_port(port):
                valid_ports.append(port)
                self.log(f"✓ 端口 {port} 验证通过，是Minecraft联机端口")
            else:
                self.log(f"✗ 端口 {port} 验证失败")
        
        if valid_ports:
            if 25565 in valid_ports:
                return 25565
            else:
                return valid_ports[0]
        else:
            self.log("所有候选端口验证失败")
            return None    
    def check_java_minecraft_server(self):
        self.log("正在检查25565端口状态...")
        
        if self.is_port_mapping_active and self.mapped_port:
            self.log(f"端口映射激活中，检查映射源端口 {self.mapped_port}")
            if self.is_port_occupied_by_java_original(self.mapped_port):
                self.log(f"✓ 映射源端口 {self.mapped_port} 被Java进程占用")
                return True
            else:
                self.log(f"✗ 映射源端口 {self.mapped_port} 未被Java进程占用")
                return False
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', 25565))
                if result == 0:
                    self.log("✓ 25565端口被占用，可能是Minecraft服务器")
                    return True
                else:
                    self.log("25565端口未被占用")
                    return False
        except Exception:
            self.log("25565端口检查失败")
            return False
    
    def manual_port_selection(self):
        self.log("\n无法确定Minecraft使用的端口，请手动确认：")
        self.log("1. 我已在Minecraft中开启局域网游戏")
        self.log("2. 我还没有开启局域网游戏")
        return None
    
    def generate_random_remote_port(self):
        return random.randint(10000, 60000)
    
    def get_frp_nodes(self):
        """从云端获取FRP节点列表"""
        self.log("正在从云端获取FRP节点列表...")
        
        try:
            # 修改URL以从新的位置获取FRP列表
            url = f"https://{api}/frplistlytapiit.txt"
            req = Request(url, headers={'User-Agent': 'LMFP/4.0.0'})
            
            with urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8').strip()
                nodes = []
                
                # 检查内容是否为空
                if not content:
                    self.log("⚠ 云端返回空数据，使用备用节点")
                    return self.get_fallback_nodes()
                
                # 解析新的节点格式：节点号#[名称 IP:端口 token]
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # 解析格式：节点号#[名称 IP:端口 token]
                    if '#[' in line and line.endswith(']'):
                        try:
                            node_id_str, rest = line.split('#', 1)
                            node_id = int(node_id_str.strip())
                            
                            # 提取括号内的内容
                            inner_content = rest[1:-1]  # 去掉方括号
                            
                            # 分离token（如果有）
                            token = ""
                            if ' ' in inner_content:
                                # 检查最后一个空格后面是否是token
                                parts = inner_content.split(' ')
                                last_part = parts[-1]
                                # 如果最后一部分看起来像token（没有冒号），则认为它是token
                                if ':' not in last_part:
                                    token = last_part
                                    inner_content = ' '.join(parts[:-1])
                            
                            # 分离名称和地址
                            if ' ' in inner_content:
                                name_part, addr_part = inner_content.rsplit(' ', 1)
                                node_name = name_part.strip()
                                
                                if ':' in addr_part:
                                    server_addr, server_port = addr_part.split(':')
                                    server_port = int(server_port.strip())
                                    
                                    node_info = {
                                        'node_id': node_id,
                                        'name': node_name,
                                        'server_addr': server_addr.strip(),
                                        'server_port': server_port,
                                        'token': token  # 添加token字段
                                    }
                                    nodes.append(node_info)
                                    self.log(f"✓ 解析节点 #{node_id}: {node_name} (*.*.*.*:{server_port})")
                        except Exception as e:
                            self.log(f"⚠ 解析节点行失败 '{line}': {e}")
                            continue
                
                if nodes:
                    self.log(f"✓ 从云端获取到 {len(nodes)} 个FRP节点")
                    return nodes
                else:
                    self.log("⚠ 云端数据格式异常，使用备用节点")
                    return self.get_fallback_nodes()
                    
        except Exception as e:
            self.log(f"✗ 获取FRP节点列表失败: {e}")
            self.log("✓ 使用备用FRP节点")
            return self.get_fallback_nodes()

    def get_fallback_nodes(self):
        """获取备用FRP节点列表"""
        self.log("正在加载备用FRP节点...")
        
        # 备用节点列表
        fallback_nodes = [
            {
                'node_id': 1,
                'name': 'Lyt_IT官方-青岛阿里云',
                'server_addr': '0.0.0.0',
                'server_port': 15443
            },
            {
                'node_id': 2,
                'name': 'Lyt_IT官方-青岛阿里云备用',
                'server_addr': '0.0.0.0', 
                'server_port': 15444
            },
            {
                'node_id': 3,
                'name': 'Lyt_IT官方-青岛阿里云备用2',
                'server_addr': '0.0.0.0',
                'server_port': 15445
            }
        ]
        
        self.log(f"✓ 加载 {len(fallback_nodes)} 个备用节点")
        for node in fallback_nodes:
            self.log(f"  节点 #{node['node_id']}: {node['name']} - {node['server_addr']}:{node['server_port']}")
        
        return fallback_nodes
    
    def create_frpc_config(self, node, proxy_name, local_port, remote_port):
        """创建frpc.toml配置文件"""
        config_content = f'''serverAddr = "{node['server_addr']}"
serverPort = {node['server_port']}

[[proxies]]
name = "{proxy_name}"
type = "tcp"
localIP = "127.0.0.1"
localPort = {local_port}
remotePort = {remote_port}
'''
        
        try:
            with open('frpc.toml', 'w', encoding='utf-8') as f:
                f.write(config_content)
            self.log("✓ frpc.toml配置文件创建成功")
            return True
        except Exception as e:
            self.log(f"✗ 创建frpc.toml配置文件失败: {e}")
            return False
    
    def is_frp_already_running(self):
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['tasklist', '/fi', 'imagename eq frpc.exe', '/fo', 'csv'],
                    capture_output=True, text=True, check=True
                )
                return 'frpc.exe' in result.stdout
            else:
                result = subprocess.run(['pgrep', '-f', 'frpc'], capture_output=True, text=True)
                return result.returncode == 0
        except Exception:
            return False

    def cleanup_frp_process(self):
        try:
            if self.frp_process and self.frp_process.poll() is None:
                self.frp_process.terminate()
                self.frp_process.wait(timeout=5)
            
            if platform.system() == "Windows":
                subprocess.run(['taskkill', '/f', '/im', 'frpc.exe'], capture_output=True, 
                              creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.run(['pkill', '-f', 'frpc'], capture_output=True)
            
            self.is_frp_running = False
            self.frp_process = None
            return True
        except Exception as e:
            self.log(f"✗ 清理FRP进程失败: {e}")
            return False
    def check_and_stop_existing_frp(self):
        if self.is_frp_already_running():
            self.log("⚠ 检测到已有FRP进程在运行")
            response = messagebox.askyesno(
                "FRP进程冲突", 
                "检测到已有FRP进程正在运行。\n\n是否停止现有进程并启动新的连接？\n\n注意：停止现有进程会导致当前联机中断。"
            )
            if response:
                if self.cleanup_frp_process():
                    self.log("✓ 已停止现有FRP进程")
                    return True
                else:
                    self.log("✗ 停止现有进程失败")
                    return False
            else:
                self.log("✗ 用户取消操作")
                return False
        return True

    def check_and_stop_existing_frp_with_timeout(self):
        """
        检查是否有正在运行的FRP进程，如果有则显示带倒计时的对话框
        倒计时10秒后默认关闭第一个FRP并启动第二个
        """
        if self.is_frp_already_running():
            self.log("⚠ 检测到已有FRP进程在运行")
            
            # 创建对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("FRP进程冲突")
            dialog.geometry("500x500")
            dialog.resizable(False, False)
            dialog.configure(bg=BW_COLORS["background"])
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # 创建界面元素
            main_container = create_bw_frame(dialog)
            main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
            
            message_label = tk.Label(
                main_container,
                text="检测到已有FRP进程正在运行。",
                font=BW_FONTS["normal"],
                bg=BW_COLORS["card_bg"],
                fg=BW_COLORS["text_primary"]
            )
            message_label.pack(pady=10)
            
            detail_label = tk.Label(
                main_container,
                text="是否停止现有进程并启动新的连接？\n注意：停止现有进程会导致当前联机中断。",
                font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"],
                fg=BW_COLORS["text_secondary"]
            )
            detail_label.pack(pady=5)
            
            # 倒计时变量
            countdown = 10
            result = [None]  # 使用列表来存储结果，因为在内部函数中需要修改
            
            countdown_label = tk.Label(
                main_container,
                text=f"将在 {countdown} 秒后默认关闭第一个FRP并启动第二个",
                font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"],
                fg=BW_COLORS["warning"]
            )
            countdown_label.pack(pady=10)
            
            # 按钮框架
            button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
            button_frame.pack(pady=15)
            
            def on_confirm():
                result[0] = True
                dialog.destroy()
            
            def on_cancel():
                result[0] = False
                dialog.destroy()
            
            confirm_btn = create_bw_button(button_frame, "确定：关闭第一个FRP", on_confirm, "primary", width=20)
            confirm_btn.pack(side=tk.LEFT, padx=5)
            
            cancel_btn = create_bw_button(button_frame, "取消：保留第一个", on_cancel, "secondary", width=15)
            cancel_btn.pack(side=tk.LEFT, padx=5)
            
            # 倒计时函数
            def update_countdown():
                nonlocal countdown
                if dialog.winfo_exists():  # 检查对话框是否仍然存在
                    countdown -= 1
                    if countdown >= 0:
                        countdown_label.config(text=f"将在 {countdown} 秒后默认关闭第一个FRP并启动第二个")
                        dialog.after(1000, update_countdown)
                    else:
                        # 时间到了，默认选择关闭第一个FRP
                        result[0] = True
                        dialog.destroy()
            
            # 启动倒计时
            dialog.after(1000, update_countdown)
            
            # 等待对话框关闭
            dialog.wait_window()
            
            # 处理结果
            if result[0] is True:
                if self.cleanup_frp_process():
                    self.log("✓ 已停止现有FRP进程")
                    return True
                else:
                    self.log("✗ 停止现有进程失败")
                    return False
            else:
                self.log("✗ 用户取消操作")
                return False
                
        return True
    def stop_frp(self):
        if not self.is_frp_running and not self.is_frp_already_running():
            self.log("ℹ 没有正在运行的FRP进程")
            return
        
        if messagebox.askyesno("确认停止", "确定要停止当前FRP连接吗？\n这将中断当前的联机会话。"):
            if self.cleanup_frp_process():
                self.log("✓ FRP进程已停止")
                self.stop_room_heartbeat()
            else:
                self.log("✗ 停止FRP进程失败")

    def check_frp_installation(self):
        try:
            if os.path.exists("frpc.exe"):
                return True
            
            result = subprocess.run(['where', 'frpc.exe'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
                
            self.log("✗ 未找到 frpc.exe")
            self.log("请确保 FRP 已正确安装并在系统PATH中")
            return False
        except Exception as e:
            self.log(f"✗ 检查FRP安装时出错: {e}")
            return False

    def run_frp_command(self, node, local_port, remote_port):
        """运行FRP客户端，使用命令行参数而非配置文件"""
        try:
            self.log("正在启动FRP服务...")
            
            # 检查frpc.exe是否存在
            if not os.path.exists("frpc.exe"):
                self.log("✗ 未找到 frpc.exe 文件")
                return False
            
            # 构造命令行参数
            command = [
                'frpc.exe', 
                'tcp',
                '--server_addr', f"{node['server_addr']}:{node['server_port']}",
                '--proxy_name', f"mc_{remote_port}",
                '--local_port', str(local_port),
                '--remote_port', str(remote_port)
            ]
            
            # 获取token
            # 首先尝试使用节点自带的token
            node_token = node.get('token', '')
            if node_token:
                command.extend(['--token', node_token])
                self.log(f"✓ 使用节点配置的穿透密钥")
            else:
                # 如果节点没有token，则从云端获取通用token
                token_url = f"https://{api}/tkasdAsdw.txt"
                try:
                    req = Request(token_url, headers={'User-Agent': 'LMF4.0.0'})
                    with urlopen(req, timeout=10) as response:
                        token_content = response.read().decode('utf-8').strip()
                        # 如果token文件不为空，则添加到命令行参数中
                        if token_content:
                            command.extend(['--token', token_content])
                            self.log(f"✓ 获取到穿透密钥，已添加到命令行参数")
                        else:
                            self.log("ℹ 未获取到穿透密钥，将以无密钥模式启动")
                except Exception as e:
                    self.log(f"⚠ 获取穿透密钥失败: {e}，将继续以无密钥模式启动")
            
            if platform.system() == "Windows":
                self.frp_process = subprocess.Popen(command, creationflags=subprocess.CREATE_NO_WINDOW)
                # Assign the FRP process to our job object so it terminates with the parent
                self.assign_process_to_job(self.frp_process._handle)
                threading.Thread(target=self.monitor_frp_process, daemon=True).start()
                
                # 启动MC服务器检测线程
                self.log("✓ 已启动FRP服务(窗口已隐藏)，正在启动MC服务器检测...")
                threading.Thread(target=self.monitor_mc_server, args=(node['server_addr'], remote_port), daemon=True).start()                    
                self.log("提示: FRP窗口已隐藏运行")
                return True
            else:
                self.frp_process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                threading.Thread(target=self.monitor_frp_process, daemon=True).start()
                
                # 启动MC服务器检测线程
                if MCSTATUS_AVAILABLE:
                    self.log("✓ 已启动FRP服务，正在启动MC服务器检测...")
                    threading.Thread(target=self.monitor_mc_server, args=(node['server_addr'], remote_port), daemon=True).start()
                else:
                    self.log("✓ 已启动FRP服务")
                    
                return True
        except Exception as e:
            self.is_frp_running = False
            self.log(f"✗ 启动FRP失败: {e}")
            return False
    def monitor_frp_process(self):
        try:
            if self.frp_process:
                self.frp_process.wait()
                self.is_frp_running = False
                self.frp_process = None
                
                self.log("■ FRP进程已停止，自动停止心跳包发送")
                self.stop_room_heartbeat()
        except Exception:
            pass
    
    def monitor_mc_server(self, server_addr, remote_port):
        """
        每10秒检测一次Minecraft服务器状态
        如果不是Minecraft服务器，则停止FRP并弹窗提示
        连续3次检测失败则停止FRP
        """
        # 等待一段时间让FRP建立连接
        time.sleep(5)
        
        # 连续失败计数器
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while self.is_frp_running and self.frp_process and self.frp_process.poll() is None:
            try:
                # 使用mcstatus检测服务器
                server = JavaServer.lookup(f"{server_addr}:{remote_port}")
                status = server.status()
                
                # 如果能成功获取状态，说明是Minecraft服务器
                self.log(f"✓ 检测到MC服务器运行中，玩家数: {status.players.online}/{status.players.max}")

                # 重置失败计数器
                consecutive_failures = 0
            except Exception as e:
                # 增加失败计数器
                consecutive_failures += 1
                self.log(f"✗ 检测MC服务器失败 ({consecutive_failures}/{max_consecutive_failures}): {str(e)}")
                
                # 如果连续失败达到3次，则停止FRP
                if consecutive_failures >= max_consecutive_failures:
                    self.log(f"✗ 连续{max_consecutive_failures}次无法检测到MC服务器，正在停止FRP...")
                    
                    # 停止FRP进程
                    self.cleanup_frp_process()
                    
                    # 在主线程中显示弹窗
                    self.root.after(0, lambda: messagebox.showinfo(
                        "警告",
                        f"连续{max_consecutive_failures}次无法检测到MC服务器，FRP已自动停止",
                        parent=self.root
                    ))
                    break
            
            # 每10秒检测一次
            time.sleep(10)    
    def get_actual_player_count(self, server_addr, remote_port):
        """
        使用mcstatus库获取服务器实际玩家数量，使用tcping获取延迟
        """
        if not server_addr or not remote_port:
            return "未知", "--"
        
        # 使用tcping测试连接延迟
        is_connected, ping_time = self.tcping(server_addr, remote_port)
        latency = f"{ping_time}ms" if is_connected and ping_time != -1 else "--"
        
        # 如果mcstatus不可用，只返回延迟信息
        if not MCSTATUS_AVAILABLE:
            return "未知", latency
        
        try:
            server = JavaServer.lookup(f"{server_addr}:{remote_port}")
            status = server.status()
            return f"{status.players.online}/{status.players.max}", latency
        except Exception as e:
            return "未知", latency
    
    def tcping(self, host, port, timeout=3):
        """
        TCP ping指定主机和端口，测量连接延迟
        """
        try:
            start_time = time.time()
            with socket.create_connection((host, port), timeout=timeout) as sock:
                # 计算连接建立时间
                latency = (time.time() - start_time) * 1000
                return True, int(latency)
        except Exception:
            return False, -1

    def is_minecraft_server_port(self, host, port):
        """
        使用mcstatus验证指定端口是否为Minecraft服务器
        """
        try:
            server = JavaServer.lookup(f"{host}:{port}", timeout=2)
            # 尝试获取服务器状态
            status = server.status()
            # 如果能成功获取状态，则确认是Minecraft服务器
            return True
        except Exception:
            # 如果出现异常，则不是Minecraft服务器或无法连接
            return False
    
    def get_server_status(self, host, port):
        """
        获取指定主机和端口的Minecraft服务器状态
        """
        try:
            server = JavaServer.lookup(f"{host}:{port}")
            status = server.status()
            
            return {
                "motd": str(status.description),
                "version": status.version.name,
                "protocol": status.version.protocol,
                "players_online": status.players.online,
                "players_max": status.players.max,
                "ping": status.latency
            }
        except Exception as e:
            return {"error": str(e)}
    
    def scan_local_mc_server_info(self):
        """
        扫描本地运行的Minecraft服务器并获取MOTD和版本信息
        """
        try:
            # 获取Java进程监听的端口
            java_ports = self.get_java_process_ports()
            
            # 检查这些端口是否为Minecraft服务器
            for port in java_ports:
                if self.is_minecraft_server_port('127.0.0.1', port):
                    # 获取服务器状态信息
                    status = self.get_server_status('127.0.0.1', port)
                    if 'error' not in status:
                        return {
                            'motd': status['motd'],
                            'version': status['version']
                        }
            
            # 如果没找到，尝试常用端口
            common_ports = [25565, 25575, 25577]
            for port in common_ports:
                if self.is_minecraft_server_port('127.0.0.1', port):
                    status = self.get_server_status('127.0.0.1', port)
                    if 'error' not in status:
                        return {
                            'motd': status['motd'],
                            'version': status['version']
                        }
        except Exception as e:
            self.log(f"扫描本地Minecraft服务器时出错: {e}")
        
        # 默认返回值
        return {
            'motd': '欢迎来玩！',
            'version': ''
        }
    
    def start_mc_server_monitoring(self):
        """启动Minecraft服务器监控线程"""
        monitoring_thread = threading.Thread(target=self.monitor_local_mc_server, daemon=True)
        monitoring_thread.start()
        self.log("✓ Minecraft服务器监控已启动")
    
    def monitor_local_mc_server(self):
        """监控本地Minecraft服务器状态"""
        # 等待一段时间让FRP建立连接
        time.sleep(5)
        
        # 连续失败计数器
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while True:
            try:
                # 检查FRP进程是否仍在运行
                frp_running = False
                if hasattr(self, 'frps_process') and self.frps_process and self.frps_process.poll() is None:
                    frp_running = True
                if hasattr(self, 'frpc_process') and self.frpc_process and self.frpc_process.poll() is None:
                    frp_running = True
                
                if not frp_running:
                    break
                
                # 使用mcstatus验证127.0.0.1是否为Minecraft服务器
                if self.is_minecraft_server_port('127.0.0.1', 25565):
                    # 如果能成功验证，说明是Minecraft服务器
                    self.log(f"✓ 本地Minecraft服务器运行正常")
                    # 重置失败计数器
                    consecutive_failures = 0
                else:
                    # 增加失败计数器
                    consecutive_failures += 1
                    self.log(f"✗ 检测本地Minecraft服务器失败 ({consecutive_failures}/{max_consecutive_failures})")
                    
                    # 如果连续失败达到3次，则停止FRP
                    if consecutive_failures >= max_consecutive_failures:
                        self.log(f"✗ 连续{max_consecutive_failures}次无法检测到本地Minecraft服务器，正在停止FRP...")
                        
                        # 停止FRP进程
                        self.stop_frp_services()
                        
                        # 在主线程中显示弹窗
                        self.root.after(0, lambda: messagebox.showinfo(
                            "警告",
                            f"连续{max_consecutive_failures}次无法检测到本地Minecraft服务器，FRP已自动停止",
                            parent=self.root
                        ))
                        break
                
                # 每10秒检测一次
                time.sleep(10)
            except Exception as e:
                self.log(f"✗ 监控Minecraft服务器时出错: {e}")
                time.sleep(10)

    def get_mc_server_info(self, mc_port):
        """
        获取指定端口的Minecraft服务器信息
        """
        if mc_port is None:
            # 如果没有提供端口信息，则扫描本地服务器
            return self.scan_local_mc_server_info()
        
        try:
            # 获取指定端口的服务器状态信息
            status = self.get_server_status('127.0.0.1', mc_port)
            if 'error' not in status:
                return {
                    'motd': status['motd'],
                    'version': status['version']
                }
        except Exception as e:
            self.log(f"获取Minecraft服务器信息时出错: {e}")
        
        # 默认返回值
        return {
            'motd': '欢迎来玩！',
            'version': ''
        }

    def collect_room_info(self, remote_port, node_id, full_room_code, server_addr, mc_port=None):
        # 使用传入的Minecraft服务器端口信息
        mc_info = self.get_mc_server_info(mc_port)
        
        info_window = tk.Toplevel(self.root)
        info_window.title("发布到联机大厅")
        info_window.geometry("500x500")
        info_window.transient(self.root)
        info_window.grab_set()
        info_window.resizable(False, False)
        info_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                info_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(info_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(title_frame, text="房间信息设置", font=BW_FONTS["subtitle"], 
                bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"]).pack()
        
        room_info_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        room_info_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(room_info_frame, text=f"完整房间号: {full_room_code}", 
                font=BW_FONTS["small"], fg=BW_COLORS["primary"]).pack(anchor="w")
        tk.Label(room_info_frame, text=f"服务器地址: {server_addr}:{remote_port}", 
                font=BW_FONTS["small"], fg=BW_COLORS["primary"]).pack(anchor="w")
        
        form_frame = create_bw_frame(main_container)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        tk.Label(form_frame, text="房主ID:", font=BW_FONTS["small"], 
                bg=BW_COLORS["card_bg"]).grid(row=0, column=0, sticky=tk.W, pady=8, padx=10)
        host_player_var = tk.StringVar()
        host_player_entry = tk.Entry(form_frame, textvariable=host_player_var, width=25, font=BW_FONTS["small"])
        host_player_entry.grid(row=0, column=1, sticky=tk.W, pady=8)
        host_player_entry.insert(0, "玩家")
        
        tk.Label(form_frame, text="游戏版本:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).grid(row=1, column=0, sticky=tk.W, pady=8, padx=10)
        version_var = tk.StringVar()
        version_entry = tk.Entry(form_frame, textvariable=version_var, width=25, font=BW_FONTS["small"])
        version_entry.grid(row=1, column=1, sticky=tk.W, pady=8)
        version_entry.insert(0, mc_info.get("version", ""))
        
        tk.Label(form_frame, text="房间描述:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).grid(row=2, column=0, sticky=tk.NW, pady=8, padx=10)
        description_frame = tk.Frame(form_frame, bg=BW_COLORS["card_bg"])
        description_frame.grid(row=2, column=1, sticky=tk.W+tk.E, pady=8)
        
        description_text = tk.Text(description_frame, width=25, height=3, font=BW_FONTS["small"])
        description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        description_text.insert("1.0", mc_info.get("motd", "欢迎来玩！"))
        
        is_public_var = tk.BooleanVar(value=True)
        public_frame = tk.Frame(form_frame, bg=BW_COLORS["card_bg"])
        public_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        public_check = tk.Checkbutton(public_frame, text="公开房间（在联机大厅显示）",
                                     variable=is_public_var, bg=BW_COLORS["card_bg"])
        public_check.pack(side=tk.LEFT)
        
        # 添加MOD复选框
        is_mod_var = tk.BooleanVar(value=False)
        mod_frame = tk.Frame(form_frame, bg=BW_COLORS["card_bg"])
        mod_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        mod_check = tk.Checkbutton(mod_frame, text="包含MOD",
                                  variable=is_mod_var, bg=BW_COLORS["card_bg"])
        mod_check.pack(side=tk.LEFT)
        
        result = [None]
        
        def confirm_info():
            if not host_player_var.get().strip():
                messagebox.showwarning("输入错误", "请输入房主ID")
                host_player_entry.focus()
                return
            
            if not version_var.get().strip():
                messagebox.showwarning("输入错误", "请输入游戏版本")
                version_entry.focus()
                return
            
            description = description_text.get("1.0", tk.END).strip()
            if not description:
                description = "欢迎来玩！"
            
            # 如果选择了MOD选项，在描述前添加(MOD)标识
            if is_mod_var.get():
                description = "（MOD）" + description
            
            room_info = {
                'full_room_code': full_room_code,
                'room_name': f"{host_player_var.get().strip()}的房间",
                'game_version': version_var.get().strip(),
                'player_count': 1,
                'max_players': 20,
                'description': description,
                'is_public': is_public_var.get(),
                'host_player': host_player_var.get().strip(),
                'server_addr': server_addr,
                'remote_port': remote_port
            }
            result[0] = room_info
            info_window.destroy()
        
        def skip_info():
            result[0] = None
            info_window.destroy()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=15)
        
        if is_public_var.get():
            btn_text = "发布到联机大厅"
        else:
            btn_text = "创建私有房间"
        
        confirm_btn = create_bw_button(btn_frame, btn_text, confirm_info, "primary", width=18)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", skip_info, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        def update_btn_text():
            if is_public_var.get():
                confirm_btn.config(text="发布到联机大厅")
            else:
                confirm_btn.config(text="创建私有房间")
        
        is_public_var.trace('w', lambda *args: update_btn_text())
        host_player_entry.focus()
        host_player_entry.select_range(0, tk.END)
        
        info_window.bind('<Return>', lambda e: confirm_info())
        info_window.bind('<Escape>', lambda e: skip_info())
        
        info_window.wait_window()
        return result[0]

    def http_request(self, method, data=None):
        try:
            import urllib.request
            import urllib.parse
            
            if method == "GET":
                req = urllib.request.Request(self.server_url)
            else:
                headers = {'Content-Type': 'application/json'}
                json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                req = urllib.request.Request(self.server_url, data=json_data, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                return json.loads(content)
        except urllib.error.URLError as e:
            self.log(f"✗ 网络连接失败: {e.reason}")
            return None
        except urllib.error.HTTPError as e:
            self.log(f"✗ HTTP错误 {e.code}: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            self.log(f"✗ JSON解析失败: {e}")
            return None
        except UnicodeDecodeError as e:
            self.log(f"✗ 字符编码错误: {e}")
            try:
                if method == "GET":
                    req = urllib.request.Request(self.server_url)
                else:
                    headers = {'Content-Type': 'application/json'}
                    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
                    req = urllib.request.Request(self.server_url, data=json_data, headers=headers, method=method)
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read().decode('gbk')
                    return json.loads(content)
            except:
                self.log("✗ 所有编码方式都失败了")
                return None
        except Exception as e:
            self.log(f"✗ HTTP请求失败: {str(e)}")
            return None

    def submit_room_info(self, room_info, start_heartbeat=True):
        def submit_thread():
            try:
                full_room_code = room_info['full_room_code']
                room_parts = full_room_code.split('_')
                if len(room_parts) != 2:
                    self.log("✗ 房间号格式错误")
                    return
                    
                remote_port = int(room_parts[0])
                node_id = int(room_parts[1])
                
                submit_data = {
                    'remote_port': remote_port,
                    'node_id': node_id,
                    'room_name': room_info['room_name'],
                    'game_version': room_info['game_version'],
                    'player_count': room_info.get('player_count', 1),
                    'max_players': room_info.get('max_players', 20),
                    'description': room_info['description'],
                    'is_public': room_info['is_public'],
                    'host_player': room_info['host_player'],
                    'server_addr': room_info['server_addr']
                }
                
                self.log(f"提交房间数据完成")
                response = self.http_request("POST", submit_data)
                if response and response.get('success'):
                    if room_info['is_public']:
                        self.log("✓ 房间已发布到联机大厅")
                    else:
                        self.log("✓ 私有房间创建成功")
                    
                    if start_heartbeat:
                        self.start_room_heartbeat(room_info)
                else:
                    error_msg = response.get('message', '未知错误') if response else '请求失败'
                    self.log(f"⚠ 房间信息发布失败: {error_msg}")
            except Exception as e:
                self.log(f"✗ 发布房间信息时出错: {e}")
        
        threading.Thread(target=submit_thread, daemon=True).start()

    def start_room_heartbeat(self, room_info):
        if self.heartbeat_active:
            self.stop_room_heartbeat()
        
        self.current_room_info = room_info
        self.heartbeat_active = True
        
        def heartbeat_loop():
            heartbeat_count = 0
            while self.heartbeat_active:
                try:
                    if not self.is_frp_running and not self.is_frp_already_running():
                        self.log("■ FRP进程未运行，停止发送心跳包")
                        self.stop_room_heartbeat()
                        break
                    
                    full_room_code = room_info['full_room_code']
                    room_parts = full_room_code.split('_')
                    if len(room_parts) != 2:
                        self.log("✗ 心跳发送失败：房间号格式错误")
                        continue
                        
                    remote_port = int(room_parts[0])
                    node_id = int(room_parts[1])
                    
                    heartbeat_data = {
                        'remote_port': remote_port,
                        'node_id': node_id,
                        'room_name': room_info['room_name'],
                        'game_version': room_info['game_version'],
                        'player_count': room_info.get('player_count', 1),
                        'max_players': room_info.get('max_players', 20),
                        'description': room_info['description'],
                        'is_public': room_info['is_public'],
                        'host_player': room_info['host_player'],
                        'server_addr': room_info['server_addr']
                    }
                    
                    response = self.http_request("POST", heartbeat_data)
                    heartbeat_count += 1
                    if response and response.get('success'):
                        self.log(f"心跳发送成功 #{heartbeat_count}（30秒）")
                    else:
                        error_msg = response.get('message', '未知错误') if response else '请求失败'
                        self.log(f"⚠ 房间心跳发送失败 #{heartbeat_count}: {error_msg}")
                except Exception as e:
                    self.log(f"✗ 心跳发送错误 #{heartbeat_count}: {e}")
                
                for i in range(30):
                    if not self.heartbeat_active:
                        break
                    if not self.is_frp_running and not self.is_frp_already_running():
                        self.log("■ 检测到FRP进程已停止，停止心跳包")
                        self.stop_room_heartbeat()
                        return
                    time.sleep(1)
        
        self.heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        self.log("✓ 房间心跳监控已启动（每30秒一次，自动检测FRP状态）")

    def stop_room_heartbeat(self):
        if self.heartbeat_active:
            self.heartbeat_active = False
            if self.heartbeat_thread and self.heartbeat_thread.is_alive():
                self.heartbeat_thread.join(timeout=2)
            
            if self.current_room_info:
                self.log("正在从联机大厅移除房间信息")
                self.delete_room_info(self.current_room_info)
                self.current_room_info = None
            
            self.log("■ 房间心跳监控已停止")

    def delete_room_info(self, room_info):
        def delete_thread():
            try:
                full_room_code = room_info['full_room_code']
                room_parts = full_room_code.split('_')
                if len(room_parts) != 2:
                    self.log("✗ 房间号格式错误，无法删除房间信息")
                    return
                    
                remote_port = int(room_parts[0])
                node_id = int(room_parts[1])
                
                delete_data = {'remote_port': remote_port, 'node_id': node_id}
                self.log(f"正在发送删除请求")
                
                response = self.http_request("DELETE", delete_data)
                if response:
                    if response.get('success'):
                        self.log("✓ 房间信息已从大厅移除")
                    else:
                        error_msg = response.get('message', '未知错误')
                        self.log(f"⚠ 房间信息移除失败: {error_msg}")
                else:
                    self.log("✗ 删除请求无响应")
            except Exception as e:
                self.log(f"✗ 移除房间信息时出错: {e}")
        
        threading.Thread(target=delete_thread, daemon=True).start()

    def run_tcp_tunnel(self, server_addr, remote_port, local_port=25565):
        
        try:
            self.log(f"启动TCP隧道: {server_addr}:{remote_port} -> 127.0.0.1:{local_port}")
            
            # 使用Python的socket来实现简单的端口转发
            def start_tunnel():
                import socket
                import threading
                
                def handle_client(client_socket, target_host, target_port):
                    try:
                        # 连接到目标服务器
                        target_socket = socket.create_connection((target_host, target_port), timeout=10)
                        
                        # 双向数据传输
                        def forward(source, destination, direction):
                            try:
                                while self.tunnel_active:
                                    data = source.recv(4096)
                                    if not data:
                                        break
                                    destination.send(data)
                            except Exception as e:
                                if self.tunnel_active:
                                    self.log(f"隧道数据转发错误 ({direction}): {e}")
                        
                        # 启动两个方向的转发线程
                        client_to_target = threading.Thread(
                            target=forward, 
                            args=(client_socket, target_socket, "客户端→服务器")
                        )
                        target_to_client = threading.Thread(
                            target=forward, 
                            args=(target_socket, client_socket, "服务器→客户端")
                        )
                        
                        client_to_target.daemon = True
                        target_to_client.daemon = True
                        
                        client_to_target.start()
                        target_to_client.start()
                        
                        # 等待任一线程结束
                        client_to_target.join()
                        target_to_client.join()
                        
                    except Exception as e:
                        if self.tunnel_active:
                            self.log(f"隧道连接错误: {e}")
                    finally:
                        try:
                            client_socket.close()
                        except:
                            pass
                        try:
                            target_socket.close()
                        except:
                            pass
                
                # 创建本地监听socket
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(('127.0.0.1', local_port))
                server_socket.listen(5)
                server_socket.settimeout(1)  # 设置超时以便检查隧道状态
                
                self.log(f"✓ TCP隧道已启动，监听 127.0.0.1:{local_port}")
                self.log(f"→ 转发到 {server_addr}:{remote_port}")
                
                self.tunnel_active = True
                self.tunnel_socket = server_socket
                
                try:
                    while self.tunnel_active:
                        try:
                            client_socket, addr = server_socket.accept()
                            self.log(f"新的连接来自: {addr[0]}:{addr[1]}")
                            
                            # 为每个客户端创建新的处理线程
                            client_thread = threading.Thread(
                                target=handle_client, 
                                args=(client_socket, server_addr, remote_port)
                            )
                            client_thread.daemon = True
                            client_thread.start()
                            
                        except socket.timeout:
                            continue  # 超时是正常的，用于检查隧道状态
                        except Exception as e:
                            if self.tunnel_active:  # 如果不是主动关闭
                                self.log(f"接受连接错误: {e}")
                            break
                            
                except Exception as e:
                    if self.tunnel_active:  # 如果不是主动关闭
                        self.log(f"隧道错误: {e}")
                finally:
                    server_socket.close()
                    self.tunnel_active = False
                    self.log("TCP隧道已停止")
        
            # 启动隧道线程
            self.tunnel_thread = threading.Thread(target=start_tunnel)
            self.tunnel_thread.daemon = True
            self.tunnel_thread.start()
            
            # 等待隧道启动
            time.sleep(1)
            return self.tunnel_active
            
        except Exception as e:
            self.log(f"✗ 启动TCP隧道失败: {e}")
            return False

    def stop_tcp_tunnel(self):
        """停止TCP隧道"""
        if hasattr(self, 'tunnel_active') and self.tunnel_active:
            self.tunnel_active = False
            if hasattr(self, 'tunnel_socket'):
                try:
                    self.tunnel_socket.close()
                except:
                    pass
            self.log("✓ TCP隧道已停止")
        
        # 停止FRP服务
        self.stop_frp_services()

    def get_room_info_from_cloud(self, full_room_code):
        """从云端获取指定房间号的FRP服务器信息"""
        try:
            self.log(f"正在从云端获取房间 {full_room_code} 的信息...")
            
            # 解析房间号
            room_parts = full_room_code.split('_')
            if len(room_parts) != 2:
                self.log("✗ 房间号格式错误")
                return None
            
            remote_port = int(room_parts[0])
            node_id = int(room_parts[1])
            
            # 从云端获取FRP节点列表
            self.log(f"正在获取FRP节点 #{node_id} 的服务器信息...")
            nodes = self.get_frp_nodes()
            
            # 查找指定节点ID的服务器信息
            target_node = None
            for node in nodes:
                if node['node_id'] == node_id:
                    target_node = node
                    break
            
            if not target_node:
                self.log(f"✗ 未找到FRP节点 #{node_id} 的信息")
                return None
            
            self.log(f"✓ 找到FRP节点 #{node_id}: {target_node['name']}")
            self.log(f"   服务器地址: {target_node['server_addr']}:{target_node['server_port']}")
            
            # 使用房间号的前6位作为真正的远程端口
            actual_remote_port = int(str(remote_port)[:6]) if len(str(remote_port)) >= 6 else remote_port
            self.log(f"✓ 使用真正的远程端口: {actual_remote_port}")
            
            # 构建房间信息
            room_info = {
                'full_room_code': full_room_code,
                'server_addr': target_node['server_addr'],
                'server_port': target_node['server_port'],
                'remote_port': actual_remote_port,
                'node_id': node_id,
                'node_name': target_node['name'],
                'room_name': f"FRP节点#{node_id}的房间",
                'game_version': '未知',
                'host_player': '未知玩家',
                'description': f"通过FRP节点 #{node_id} 连接"
            }
            
            self.log(f"✓ 房间信息获取成功")
            return room_info
            
        except Exception as e:
            self.log(f"✗ 获取房间信息失败: {e}")
            return None

    def auto_join_room_from_lobby(self, full_room_code, room_info):
        """从联机大厅直接加入房间 - 使用TCP隧道"""
        def join_thread():
            try:
                # 重新从云端获取最新的节点信息
                fresh_room_info = self.get_room_info_from_cloud(full_room_code)
                if not fresh_room_info:
                    self.log("✗ 无法获取最新的房间信息")
                    return
                
                server_addr = fresh_room_info['server_addr']
                remote_port = fresh_room_info['remote_port']
                node_name = fresh_room_info['node_name']
                
                self.log(f"✓ 获取到最新房间信息")
                self.log(f"   完整房间号: {full_room_code}")
                self.log(f"   FRP节点: #{fresh_room_info['node_id']} - {node_name}")
                self.log(f"   服务器地址: {server_addr}:{remote_port}")
                
                # 使用mcstatus验证服务器是否为Minecraft服务器
                if not self.is_minecraft_server_port(server_addr, remote_port):
                    self.log("✗ 目标服务器不是Minecraft服务器或无法连接")
                    messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                    return
                else:
                    self.log("✓ 服务器验证通过，确认为目标Minecraft服务器")
                
                # 停止现有的隧道
                self.stop_tcp_tunnel()
                
                # 启动TCP隧道
                if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                    self.log("✓ TCP隧道启动成功")
                    # 启动FRP服务
                    self.start_frp_services()

                    # 启动UDP广播（仅在成功加入房间时广播，创建房间时不广播）
                    multicast_server = MulticastServer(
                        motd="§6§l双击进入LMFP联机房间（请保持LMFP运行）",
                        port=25565,
                        multicast_group="224.0.2.60",
                        port_num=4445
                    )
                    
                    # 在单独的线程中启动UDP广播
                    def start_multicast():
                        multicast_server.start()
                    
                    multicast_thread = threading.Thread(target=start_multicast, daemon=True)
                    multicast_thread.start()
                    
                    self.log("使用说明：")
                    self.log("  1. TCP隧道已就绪")
                    self.log("  2. 在Minecraft中添加服务器")
                    self.log("  3. 服务器地址输入: 127.0.0.1:25565")
                    self.log("  4. 等待房主开启游戏")
                    
                    if self.copy_to_clipboard("127.0.0.1:25565"):
                        self.log("服务器地址已自动复制到剪贴板")
                    
                    self.log(f"\n隧道信息：")
                    self.log(f"   完整房间号: {full_room_code}")
                    self.log(f"   FRP节点: {node_name}")
                    self.log(f"   远程服务器: {server_addr}:{remote_port}")
                    self.log(f"   本地地址: 127.0.0.1:25565")
                    self.log(f"   连接方式: TCP隧道直连")
                    
                    self.log(" ")
                    self.log("使用方法：")
                    self.log("  1. 在Minecraft中点多人游戏，添加服务器")
                    self.log("  2. 服务器地址输入: “127.0.0.1:25565”（已自动复制）")
                    self.log("  3. 进入服务器即可")
                    self.log(" ")
                    self.log("\n注意：请不要关闭本程序，否则隧道会断开")

                    # 显示房间信息弹窗
                    room_info_for_popup = {
                        'full_room_code': full_room_code,
                        'server_addr': server_addr,
                        'remote_port': remote_port
                    }
                    show_room_info_popup(room_info_for_popup, is_created=False)
                else:
                    self.log("✗ TCP隧道启动失败")
                    
            except Exception as e:
                self.log(f"✗ 加入房间过程中出现错误: {e}")
        
        threading.Thread(target=join_thread, daemon=True).start()

    def refresh_rooms(self, auto_refresh=False):        
        if self.is_refreshing:
            return
            
        # 只有云端许可验证通过后才能刷新房间
        if not self.cloud_permission_granted:
            self.lobby_status.config(text="等待云端许可验证...")
            return
            
        self.is_refreshing = True
        if self.lobby_refresh_btn:
            self.lobby_refresh_btn.config(state='disabled', text='⟳ 刷新中...')
        
        def refresh_thread():
            try:
                if not auto_refresh:
                    self.log("⟳ 正在获取房间列表...")
                
                response = self.http_request("GET")
                if response:
                    if response.get('success'):
                        self.current_rooms = response['data']['rooms']
                        self.update_room_list()
                        current_time = datetime.now().strftime("%H:%M:%S")
                        stats = response['data'].get('stats', {})
                        cleaned_count = stats.get('cleaned_rooms', 0)
                        
                        status_text = f"找到 {len(self.current_rooms)} 个活跃房间"
                        if cleaned_count > 0:
                            status_text += f" (已清理 {cleaned_count} 个过期房间)"
                        
                        self.lobby_status.config(text=status_text)
                        self.last_update_label.config(text=f"最后更新: {current_time}")
                        
                        if auto_refresh and len(self.current_rooms) > 0:
                            # 自动刷新时不显示日志，避免干扰
                            pass
                        else:
                            self.log("✓ 房间列表已刷新")
                    else:
                        self.lobby_status.config(text="获取房间列表失败")
                        self.log("✗ 获取房间列表失败")
                else:
                    self.lobby_status.config(text="获取房间列表失败：无响应")
                    self.log("✗ 获取房间列表失败：无响应")
            except Exception as e:
                self.lobby_status.config(text=f"刷新失败: {e}")
                self.log(f"✗ 刷新房间列表失败: {e}")
            finally:
                self.is_refreshing = False
                if self.lobby_refresh_btn:
                    self.lobby_refresh_btn.config(state='normal', text='⟳ 刷新')
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def update_room_list(self):
        for item in self.room_tree.get_children():
            self.room_tree.delete(item)
        
        for room in self.current_rooms:
            player_text = f"{room['player_count']}/{room['max_players']}"
            # 使用mcstatus判断房间在线状态，tcping测量延迟
            status = "○ 离线"  # 默认离线
            latency = "--"
            
            # 使用tcping测量延迟
            server_addr = room.get('server_addr')
            remote_port = room.get('remote_port')
            
            if server_addr and remote_port:
                # 使用tcping测试连接延迟
                is_connected, ping_time = self.tcping(server_addr, remote_port)
                latency = f"{ping_time}ms" if is_connected and ping_time != -1 else "--"
                
                # 使用mcstatus判断在线状态
                if MCSTATUS_AVAILABLE:
                    try:
                        server = JavaServer.lookup(f"{server_addr}:{remote_port}")
                        status_result = server.status()
                        # 如果能成功获取服务器状态，则认为房间在线
                        status = "● 在线"
                    except Exception:
                        # 如果出现异常，则认为房间离线
                        status = "○ 离线"
                else:
                    # 如果mcstatus不可用，回退到原来的时间判断方式
                    current_time = time.time()
                    time_diff = current_time - room['last_update']
                    if time_diff <= 60:
                        status = "● 在线"
                    else:
                        status = "○ 离线"
            else:
                status = "○ 离线"
            
            full_room_code = f"{room['remote_port']}_{room['node_id']}"
            server_addr_display = f"{room.get('server_addr', '未知')}:{room.get('remote_port', '未知')}"
            
            join_button_text = "加入"
            
            # 截断过长的描述
            description = room.get('description', '无描述')
            if len(description) > 20:
                description = description[:20] + "..."
            
            # 使用mcstatus获取实际玩家数量和MOTD作为房间名
            actual_players = "未知"
            room_name = room['room_name']
            detected_version = "未知"
            if MCSTATUS_AVAILABLE:
                try:
                    server = JavaServer.lookup(f"{room.get('server_addr')}:{room.get('remote_port')}")
                    status_result = server.status()
                    actual_players = f"{status_result.players.online}/{status_result.players.max}"
                    # 使用从mcstatus获取的MOTD作为房间名
                    if str(status_result.description).strip():
                        room_name = str(status_result.description).strip()
                    # 获取通过mcstatus检测到的版本
                    if status_result.version.name:
                        detected_version = status_result.version.name
                except Exception as e:
                    print(f"获取服务器状态失败: {e}")
            
            self.room_tree.insert("", "end", values=(
                full_room_code,    # 房间号
                actual_players,    # 房间人数
                room.get('host_player', '未知玩家'),  # 房主
                room['game_version'],  # 版本
                detected_version,   # 识别版本
                server_addr_display,       # 服务器地址
                room_name,         # 房间标题
                description,       # 描述
                latency,           # 延迟
                status,            # 状态
                join_button_text   # 操作
            ), tags=(full_room_code,))

    def on_room_click(self, event):
        item = self.room_tree.identify_row(event.y)
        column = self.room_tree.identify_column(event.x)
        
        if not item:
            return
        
        # 获取房间信息
        room_values = self.room_tree.item(item, "values")
        if not room_values:
            return
        
        full_room_code = room_values[0]   # 房间号
        actual_players = room_values[1]   # 房间人数
        host_player = room_values[2]      # 房主
        game_version = room_values[3]     # 版本
        detected_version = room_values[4] # 识别版本
        server_addr = room_values[5]      # 服务器地址
        room_name = room_values[6]        # 房间标题
        description = room_values[7]      # 描述
        latency = room_values[8]          # 延迟
        status = room_values[9]           # 状态
        
        # 更新房间详情
        self.room_detail_text.config(state=tk.NORMAL)
        self.room_detail_text.delete(1.0, tk.END)
        
        # 查找完整的房间描述
        full_description = description
        server_info = None
        for room in self.current_rooms:
            current_full_room_code = f"{room['remote_port']}_{room['node_id']}"
            if current_full_room_code == full_room_code:
                full_description = room.get('description', description)
                server_info = room
                break
        
        detail_text = f"房间名称: {room_name}\n"
        detail_text += f"游戏版本: {game_version} | 房主: {host_player} | 延迟: {latency} | 状态: {status}\n"
        detail_text += f"完整房间号: {full_room_code}\n"
        detail_text += f"服务器地址: {server_addr}\n"
        detail_text += f"房间描述: {full_description}\n"
        
        # 显示实际玩家数量
        if server_info:
            actual_players = self.get_actual_player_count(server_info.get('server_addr'), server_info.get('remote_port'))
            detail_text += f"实际玩家数量: {actual_players}"
        
        self.room_detail_text.insert(1.0, detail_text)
        self.room_detail_text.config(state=tk.DISABLED)
        
        # 如果是点击"操作"列（最后一列），则加入房间
        if column == "#11":  # 操作列现在是第11列
            self.join_selected_room()

    def on_room_double_click(self, event):
        """双击房间行加入房间"""
        item = self.room_tree.identify_row(event.y)
        if item:
            self.join_selected_room()

    def join_selected_room(self):
        """加入选中的房间"""
        # 只有云端许可验证通过后才能加入房间
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        selection = self.room_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个房间")
            return
        
        item = selection[0]
        room_values = self.room_tree.item(item, "values")
        
        if not room_values or len(room_values) < 3:
            messagebox.showerror("错误", "房间信息不完整")
            return
        
        full_room_code = room_values[0]   # 房间号
        actual_players = room_values[1]   # 房间人数
        host_player = room_values[2]      # 房主
        game_version = room_values[3]     # 版本
        detected_version = room_values[4] # 识别版本
        
        # 直接从当前房间列表中获取房间信息
        room_info = None
        for room in self.current_rooms:
            current_full_room_code = f"{room['remote_port']}_{room['node_id']}"
            if current_full_room_code == full_room_code:
                room_info = room
                room_name = room.get('room_name', '未知房间')
                break
        
        if not room_info:
            messagebox.showerror("错误", "房间信息获取失败")
            return
        
        server_addr = room_info.get('server_addr')
        remote_port = room_info.get('remote_port')
        description = room_info.get('description', '无描述')
        
        # 使用mcstatus验证服务器是否为Minecraft服务器
        if not self.is_minecraft_server_port(server_addr, remote_port):
            messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
            return
        
        confirm = messagebox.askyesno("确认加入", 
                                     f"是否加入房间：{room_name}\n"
                                     f"房间描述：{description}\n"
                                     f"完整房间号：{full_room_code}\n\n"
                                     f"服务器地址：{server_addr}:{remote_port}\n\n"
                                     f"注意：这将启动TCP隧道，将远程服务器映射到127.0.0.1:25565")
        
        if confirm:
            self.log(f"正在加入房间: {room_name} ({full_room_code})")
            self.auto_join_room_from_lobby(full_room_code, room_info)

    def run_frp_create(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()        
        def create_room():
            try:
                self.log("正在创建FRP联机房间...")
                self.log("正在检测Minecraft端口...")
                
                # 检测Minecraft端口（使用和IPv6联机一样的逻辑）
                mc_port = self.check_minecraft_ports()
                if not mc_port:
                    self.log("✗ 未检测到Minecraft服务器端口")
                    messagebox.showerror("错误", "未检测到Minecraft服务器运行\n\n请确保已在Minecraft中开启局域网游戏")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 检测到Minecraft服务器在端口 {mc_port} 运行")
                
                # 检查并处理现有的FRP进程
                if not self.check_and_stop_existing_frp_with_timeout():
                    self.log("✗ 用户取消操作或停止现有进程失败")
                    self.unlock_buttons()
                    return
                
                self.log("正在选择最佳FRP节点...")
                best_node = self.find_best_frp_node()
                if not best_node:
                    self.log("✗ 无法找到可用的FRP节点")
                    messagebox.showerror("错误", "无法找到可用的FRP节点，请检查网络连接")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 已选择节点: #{best_node['node_id']} - {best_node['name']}")
                
                # 生成房间信息 - 房间号格式：远程端口_FRP服务器号
                remote_port = self.generate_random_remote_port()
                full_room_code = f"{remote_port}_{best_node['node_id']}"
                proxy_name = f"mc_{remote_port}"
                
                self.log(f"✓ 生成完整房间号: {full_room_code}")
                self.log(f"✓ 本地Minecraft端口: {mc_port}")
                self.log(f"✓ 远程映射端口: {remote_port}")
                
                # 注意：FRP配置文件不再需要创建，因为我们现在使用命令行参数
                
                # 收集房间信息（包含房间描述）
                room_info = self.collect_room_info(remote_port, best_node['node_id'], full_room_code, 
                                                 best_node['server_addr'], mc_port)
                
                self.is_frp_running = True
                
                if self.run_frp_command(best_node, mc_port, remote_port):
                    self.log("\n房间创建成功！")
                    self.log(f"完整房间号: {full_room_code}")
                    self.log(f"服务器地址: {best_node['server_addr']}:{remote_port}")
                    self.log(f"本地Minecraft端口: {mc_port}")
                    
                    if room_info:
                        room_info['full_room_code'] = full_room_code
                        
                        if room_info['is_public']:
                            self.log("✓ 房间已发布到联机大厅")
                            self.log("其他玩家可以在联机大厅看到并加入")
                            self.submit_room_info(room_info)
                            # 刷新大厅列表
                            self.refresh_rooms()
                        else:
                            self.log("私有房间创建成功")
                            self.log("只有知道房间号的玩家才能加入")
                            self.log("请将房间号分享给朋友: " + full_room_code)
                    else:
                        self.log("房间未发布到联机大厅")
                    
                    if self.copy_to_clipboard(full_room_code):
                        self.log("完整房间号已自动复制到剪贴板")
                    
                    self.log("\n注意：请不要关闭FRP进程，否则联机会断开")
                    self.log(f" ")
                    self.log(f"------------------------------------------")
                    self.log(f"完整房间号: {full_room_code}")
                    self.log(f"------------------------------------------")
                    self.log(f" ")

                    # 保存当前房间信息
                    self.current_room_code = full_room_code
                    self.current_node_id = best_node['node_id']
                    self.current_remote_port = remote_port

                    # 显示房间信息弹窗
                    room_info_for_popup = {
                        'full_room_code': full_room_code,
                        'server_addr': best_node['server_addr'],
                        'remote_port': remote_port,
                        'mc_port': mc_port
                    }
                    show_room_info_popup(room_info_for_popup, is_created=True)
                else:
                    self.is_frp_running = False
                    self.log("✗ 房间创建失败")
                
                self.unlock_buttons()
                
            except Exception as e:
                self.is_frp_running = False
                self.log(f"✗ 创建房间过程中出现错误: {e}")
                self.unlock_buttons()

        threading.Thread(target=create_room, daemon=True).start()
    def run_frp_join(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        
        input_window = tk.Toplevel(self.root)
        input_window.title("输入完整房间号")
        input_window.geometry("400x150")
        input_window.transient(self.root)
        input_window.grab_set()
        input_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(input_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="请输入完整房间号:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=10)
        
        room_entry = tk.Entry(main_container, width=30, font=BW_FONTS["small"])
        room_entry.pack(pady=5)
        
        def confirm_join():
            full_room_code = room_entry.get().strip()
            input_window.destroy()
            
            if not full_room_code:
                messagebox.showerror("错误", "房间号不能为空")
                self.unlock_buttons()
                return
            
            if '_' not in full_room_code:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（远程端口_FRP服务器号）")
                self.unlock_buttons()
                return
            
            room_parts = full_room_code.split('_')
            if len(room_parts) != 2:
                messagebox.showerror("错误", "房间号格式错误，请使用完整房间号（远程端口_FRP服务器号）")
                self.unlock_buttons()
                return
            
            remote_port_str = room_parts[0]
            node_id_str = room_parts[1]
            
            if not remote_port_str.isdigit() or not (10000 <= int(remote_port_str) <= 60000):
                messagebox.showerror("错误", "远程端口格式错误，必须是10000-60000的数字")
                self.unlock_buttons()
                return
            
            if not node_id_str.isdigit() or not (1 <= int(node_id_str) <= 1000):
                messagebox.showerror("错误", "FRP服务器号格式错误，必须是1-1000的数字")
                self.unlock_buttons()
                return
            
            self.log(f"正在加入房间: {full_room_code}")
            
            def join_thread():
                try:
                    # 检查并处理现有的FRP进程
                    if not self.check_and_stop_existing_frp_with_timeout():
                        self.log("✗ 用户取消操作或停止现有进程失败")
                        self.unlock_buttons()
                        return
                    
                    # 从云端获取房间信息
                    room_info = self.get_room_info_from_cloud(full_room_code)
                    if not room_info:
                        self.log("✗ 无法获取房间信息，请检查房间号是否正确")
                        self.unlock_buttons()
                        return
                    
                    server_addr = room_info.get('server_addr')
                    remote_port = room_info.get('remote_port')
                    node_name = room_info.get('node_name')
                    
                    if not server_addr or not remote_port:
                        self.log("✗ 房间信息不完整")
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✓ 获取到房间信息")
                    self.log(f"   完整房间号: {full_room_code}")
                    self.log(f"   FRP节点: {node_name}")
                    self.log(f"   服务器地址: {server_addr}:{remote_port}")
                    
                    # 使用mcstatus验证服务器是否为Minecraft服务器
                    if not self.is_minecraft_server_port(server_addr, remote_port):
                        self.log("✗ 目标服务器不是Minecraft服务器或无法连接")
                        messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                        self.unlock_buttons()
                        return
                    else:
                        self.log("✓ 服务器验证通过，确认为目标Minecraft服务器")
                    
                    # 停止现有的隧道
                    self.stop_tcp_tunnel()
                    
                    # 启动TCP隧道
                    if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                        self.log("正在连接到房间！")
                        # 启动FRP服务
                        self.start_frp_services()

                        self.log(f"\n联机信息：")
                        self.log(f"   完整房间号: {full_room_code}")
                        self.log(f"   FRP节点: {node_name}")
                        self.log(f"   远程服务器: {server_addr}:{remote_port}")
                        self.log(f"   本地地址: 127.0.0.1:25565")
                        self.log(f"   连接方式: TCP隧道直连")                        
                        if self.copy_to_clipboard("127.0.0.1:25565"):
                            self.log("服务器地址已自动复制到剪贴板")
                        
                        self.log(" ")
                        self.log("使用方法：")
                        self.log("  1. 在Minecraft中点多人游戏，添加服务器")
                        self.log("  2. 服务器地址输入: “127.0.0.1:25565”（已自动复制）")
                        self.log("  3. 进入服务器即可")
                        self.log(" ")
                        self.log("\n注意：请不要关闭本程序，否则隧道会断开")

                        # 显示房间信息弹窗
                        room_info_for_popup = {
                            'full_room_code': full_room_code,
                            'server_addr': server_addr,
                            'remote_port': remote_port
                        }
                        show_room_info_popup(room_info_for_popup, is_created=False)
                    else:
                        self.log("✗ 连接房间失败")
                    
                    self.unlock_buttons()                    
                except Exception as e:
                    self.log(f"✗ 加入房间过程中出现错误: {e}")
                    self.unlock_buttons()
            
            threading.Thread(target=join_thread, daemon=True).start()
        
        def cancel_join():
            input_window.destroy()
            self.unlock_buttons()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=10)
        
        confirm_btn = create_bw_button(btn_frame, "确认", confirm_join, "primary", width=10)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", cancel_join, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        input_window.bind('<Return>', lambda e: confirm_join())
        room_entry.focus()

    def find_best_frp_node(self):
        """根据延迟选择最佳FRP节点"""
        self.log("正在获取FRP节点列表...")
        nodes = self.get_frp_nodes()
        
        if not nodes:
            self.log("✗ 无法获取FRP节点列表")
            return None
        
        # 测试所有节点的延迟
        nodes_with_delay = self.test_nodes_delay(nodes)
        
        if not nodes_with_delay:
            self.log("⚠ 所有节点都无法连接，使用第一个节点")
            return nodes[0]
        
        # 选择延迟最低的节点
        best_node = nodes_with_delay[0]
        best_delay = best_node['delay']
        
        self.log(f"✓ 选择最佳节点: #{best_node['node_id']} - {best_node['name']}，延迟: {best_delay}ms")
        
        # 显示前3个最佳节点
        self.log("延迟最低的前3个节点:")
        for i, node in enumerate(nodes_with_delay[:3]):
            self.log(f"  {i+1}. #{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms")
        
        return best_node

    def ping_node(self, server_addr, server_port):
        """测试节点延迟"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server_addr, server_port))
            end_time = time.time()
            sock.close()
            
            if result == 0:
                delay = int((end_time - start_time) * 1000)
                return delay
            else:
                return None
        except:
            return None

    def test_nodes_delay(self, nodes):
        """测试多个节点的延迟"""
        self.log(f"正在测试 {len(nodes)} 个节点的延迟...")
        
        nodes_with_delay = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_node = {
                executor.submit(self.ping_node, node['server_addr'], node['server_port']): node 
                for node in nodes
            }
            
            for future in concurrent.futures.as_completed(future_to_node):
                node = future_to_node[future]
                try:
                    delay = future.result()
                    if delay is not None:
                        node['delay'] = delay
                        nodes_with_delay.append(node)
                        self.log(f"节点 #{node['node_id']} - {node['name']} 延迟: {delay}ms")
                    else:
                        self.log(f"节点 #{node['node_id']} - {node['name']} 无法连接")
                except Exception as e:
                    self.log(f"节点 #{node['node_id']} - {node['name']} 测试失败: {e}")
        
        # 按延迟排序
        nodes_with_delay.sort(key=lambda x: x.get('delay', float('inf')))
        return nodes_with_delay

    def run_ipv6_mode(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        self.log("正在检测IPv6网络配置...")
        self.log("正在获取IPv6地址，请稍等...")
        
        def detect_ipv6():
            try:
                self.ipv6 = self.get_ipv6_powershell()
                
                if not self.ipv6:
                    self.ipv6 = self.get_ipv6_ipconfig()
                
                if not self.ipv6:
                    self.log("✗ 未检测到公网IPv6地址")
                    messagebox.showerror("错误", "未检测到公网IPv6地址，请联系QQ2232908600获取帮助")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 获取到IPv6地址: {self.ipv6}")
                
                self.log("正在检测Minecraft联机端口...")
                self.mc_port = self.check_minecraft_ports()
                
                if not self.mc_port:
                    self.mc_port = self.manual_port_selection()
                
                if not self.mc_port:
                    self.log("✗ 未检测到有效的Minecraft联机端口")
                    self.log("")
                    self.log("可能的原因：")
                    self.log("1. 未开启Minecraft局域网游戏")
                    self.log("2. 防火墙阻止了端口访问")
                    self.log("3. Minecraft服务未正常启动")
                    self.log("")
                    self.log("请先进入Minecraft单人游戏，开启局域网游戏：")
                    self.log("1. 进入单人游戏世界")
                    self.log("2. 按ESC键打开游戏菜单")
                    self.log("3. 点击'对局域网开放'")
                    self.log("4. 设置游戏模式（可选）")
                    self.log("5. 点击'创建局域网世界'")
                    self.log("6. 记下显示的端口号")
                    messagebox.showerror("错误", "未检测到Minecraft联机端口，请确保已在Minecraft中开启局域网游戏")
                    self.unlock_buttons()
                    return
                
                self.log(f"✓ 验证通过！将使用端口 {self.mc_port} 进行联机")
                
                mc_address = f"[{self.ipv6}]:{self.mc_port}"
                
                self.log("=" * 50)
                self.log("Minecraft联机地址已生成！")
                self.log(mc_address)
                self.log("=" * 50)
                
                if self.copy_to_clipboard(mc_address):
                    self.log("地址已自动复制到剪贴板！")
                self.log("")
                
                self.log("使用说明：")
                self.log("1. 确保您已在Minecraft中开启局域网游戏")
                self.log("2. 您的朋友需要在Minecraft多人游戏中输入此地址")
                self.log("3. 双方都需要支持IPv6网络")
                self.log("")
                
                self.log(f"游戏联机地址： [{self.ipv6}]:{self.mc_port}")
                self.log("")
                self.log("常见问题：")
                self.log("- 如果无法连接，请检查防火墙设置")
                self.log("- 确保端口号与Minecraft中显示的一致")
                self.log("- '登入失败:无效会话'：安装联机模组关闭正版验证")
                self.log("")
                
                self.log("如果使用本脚本联机时遇到问题，请联系：")
                self.log("QQ：2232908600")
                self.log("微信：liuyvetong")
                self.log("")
                self.log(f"游戏联机地址： [{self.ipv6}]:{self.mc_port}")
                if self.copy_to_clipboard(mc_address):
                    self.log("地址已自动复制到剪贴板！")
                
                self.unlock_buttons()
                
            except Exception as e:
                self.log(f"✗ IPv6检测过程中出现错误: {e}")
                self.unlock_buttons()
        
        threading.Thread(target=detect_ipv6, daemon=True).start()

    def create_port_mapping(self, source_port, target_port=25565):
        try:
            command = f'netsh interface portproxy add v4tov4 listenport={target_port} listenaddress=0.0.0.0 connectport={source_port} connectaddress=127.0.0.1'
            
            self.log(f"创建端口映射: {source_port} -> {target_port}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✓ 端口映射创建成功")
                
                firewall_command = f'netsh advfirewall firewall add rule name="Minecraft Port {target_port}" dir=in action=allow protocol=TCP localport={target_port}'
                subprocess.run(firewall_command, shell=True, capture_output=True)
                self.log("✓ 防火墙规则添加成功")
                
                return True
            else:
                self.log(f"✗ 端口映射创建失败: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"✗ 创建端口映射时出错: {e}")
            return False

    def remove_port_mapping(self, target_port=25565):
        try:
            command = f'netsh interface portproxy delete v4tov4 listenport={target_port} listenaddress=0.0.0.0'
            subprocess.run(command, shell=True, capture_output=True)
            
            firewall_command = f'netsh advfirewall firewall delete rule name="Minecraft Port {target_port}"'
            subprocess.run(firewall_command, shell=True, capture_output=True)
            
            self.log(f"✓ 已移除端口 {target_port} 的映射规则")
            return True
        except Exception as e:
            self.log(f"✗ 移除端口映射时出错: {e}")
            return False

    def run_port_mapping(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
        
        self.clear_log()
        self.lock_buttons()
        
        input_window = tk.Toplevel(self.root)
        input_window.title("端口映射设置")
        input_window.geometry("400x200")
        input_window.transient(self.root)
        input_window.grab_set()
        input_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                input_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(input_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(main_container, text="请输入要映射的源端口:", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=10)
        
        port_entry = tk.Entry(main_container, width=20, font=BW_FONTS["small"])
        port_entry.pack(pady=5)
        
        tk.Label(main_container, text="目标端口将固定为25565", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"]).pack(pady=5)
        
        def confirm_mapping():
            port_str = port_entry.get().strip()
            input_window.destroy()
            
            if not port_str:
                messagebox.showerror("错误", "端口号不能为空")
                self.unlock_buttons()
                return
            
            try:
                source_port = int(port_str)
                if not (1 <= source_port <= 65535):
                    messagebox.showerror("错误", "端口号必须在1-65535范围内")
                    self.unlock_buttons()
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的端口号")
                self.unlock_buttons()
                return
            
            def mapping_thread():
                try:
                    self.log(f"正在设置端口映射: {source_port} -> 25565")
                    
                    if not self.is_port_occupied(source_port):
                        self.log(f"✗ 源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        messagebox.showerror("错误", f"源端口 {source_port} 未被占用，请确保Minecraft服务正在运行")
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✓ 检测到源端口 {source_port} 正在运行")
                    
                    if self.is_port_occupied(25565):
                        self.log("⚠ 目标端口25565已被占用，正在清理...")
                        self.remove_port_mapping(25565)
                    
                    if self.create_port_mapping(source_port, 25565):
                        self.mapped_port = source_port
                        self.is_port_mapping_active = True
                        
                        self.log("\n端口映射设置成功！")
                        self.log(f"映射规则: {source_port} -> 25565")
                        self.log("现在可以使用25565端口连接Minecraft服务器")
                        self.log("注意：程序退出时将自动移除映射规则")
                        
                        self.port_map_btn.config(text="端口映射已激活 (点击关闭)", 
                                               command=self.stop_port_mapping)
                    else:
                        self.log("✗ 端口映射设置失败")
                    
                    self.unlock_buttons()
                    
                except Exception as e:
                    self.log(f"✗ 端口映射过程中出现错误: {e}")
                    self.unlock_buttons()
            
            threading.Thread(target=mapping_thread, daemon=True).start()
        
        def cancel_mapping():
            input_window.destroy()
            self.unlock_buttons()
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(pady=20)
        
        confirm_btn = create_bw_button(btn_frame, "确认", confirm_mapping, "primary", width=10)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(btn_frame, "取消", cancel_mapping, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        input_window.bind('<Return>', lambda e: confirm_mapping())
        port_entry.focus()

    def stop_port_mapping(self):
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.is_port_mapping_active = False
            self.mapped_port = None
            
            self.log("✓ 端口映射已停止")
            self.port_map_btn.config(text="将其他端口映射至25565", 
                                   command=self.run_port_mapping)
        else:
            self.log("⚠ 没有激活的端口映射")

    def on_closing(self):
        # 停止聊天室连接
        if hasattr(self, 'chat_room_module') and self.chat_room_module:
            self.chat_room_module.stop_chat_connection()
        
        self.stop_room_heartbeat()
        
        # 停止心跳包机制
        self.stop_heartbeat_mechanism()
        
        if self.is_frp_running or self.is_frp_already_running():
            self.log("正在停止FRP进程...")
            self.cleanup_frp_process()
        
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.log("✓ 已自动清理端口映射规则")
        
        # 停止TCP隧道
        self.stop_tcp_tunnel()
        
        # 确保所有FRP进程都被清理
        cleanup_all_processes()
        
        # Close job object on Windows
        if platform.system() == "Windows" and self.job_object:
            try:
                ctypes.windll.kernel32.CloseHandle(self.job_object)
            except:
                pass
        
        self.root.quit()

def start_cloud_monitor(app_instance):    # 连续失败计数器
    consecutive_failures = 0
    max_consecutive_failures = 3
    
    def monitor_loop():
        nonlocal consecutive_failures
        while True:
            try:
                time.sleep(30)
                if app_instance.cloud_permission_granted:
                    # 只有在当前许可通过时才检查，避免重复警告
                    if not check_cloud_permission():
                        # 增加失败计数器
                        consecutive_failures += 1
                        print(f"云端许可检查失败 ({consecutive_failures}/{max_consecutive_failures})")
                        
                        # 只有连续失败3次才锁定软件
                        if consecutive_failures >= max_consecutive_failures:
                            app_instance.root.after(0, lambda: show_cloud_warning_and_lock(app_instance))
                            # 重置计数器
                            consecutive_failures = 0
                    else:
                        # 检查成功，重置失败计数器
                        consecutive_failures = 0
                        print("云端许可检查通过")
            except Exception as e:
                print(f"云端监控检查失败: {e}")
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    print("云端许可监控已启动")

def show_cloud_warning_and_lock(app_instance):
    if hasattr(app_instance, '_cloud_warning_shown') and app_instance._cloud_warning_shown:
        return        
    app_instance._cloud_warning_shown = True
    app_instance.disable_all_buttons()
    
    warning_window = tk.Toplevel(app_instance.root)
    warning_window.title("⚠ 软件许可警告")
    warning_window.geometry("500x560")
    warning_window.resizable(False, False)
    warning_window.configure(bg=BW_COLORS["background"])
    warning_window.transient(app_instance.root)
    warning_window.attributes('-topmost', True)
    
    try:
        icon_path = "lyy.ico"
        if os.path.exists(icon_path):
            warning_window.iconbitmap(icon_path)
    except:
        pass
    
    def on_warning_close():
        app_instance._cloud_warning_shown = False
        warning_window.destroy()
    
    warning_window.protocol("WM_DELETE_WINDOW", on_warning_close)
    
    main_container = create_bw_frame(warning_window)
    main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    header_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    header_frame.pack(fill=tk.X, padx=20, pady=15)
    
    warning_icon = tk.Label(
        header_frame,
        text="⚠",
        font=("Arial", 24),
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    warning_icon.pack(side=tk.LEFT, padx=(0, 10))
    
    title_label = tk.Label(
        header_frame,
        text="软件许可警告",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    title_label.pack(side=tk.LEFT)
    
    content_frame = create_bw_frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    warning_text = """
检测到当前软件使用许可可能存在问题。

可能的原因：
• 软件版本过旧，请更新到最新版本
• 服务器维护或升级期间
• 网络连接问题
• 软件使用权限受限

当前状态：
• 软件功能已被锁定
• 所有按钮已禁用
• 需要重新验证许可后才能继续使用

请选择以下操作：
"""
    
    text_widget = scrolledtext.ScrolledText(
        content_frame,
        width=50,
        height=15,
        font=BW_FONTS["normal"],
        wrap=tk.WORD,
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        padx=10,
        pady=10
    )
    text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    text_widget.insert(tk.END, warning_text)
    text_widget.config(state=tk.DISABLED)
    
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=15)
    
    def refresh_check():
        if check_cloud_permission():
            messagebox.showinfo("检查通过", "✓ 软件使用许可已恢复！\n\n软件功能已重新启用。", parent=warning_window)
            app_instance.enable_all_buttons()
            app_instance.update_cloud_status("✓ 云端许可验证通过")
            on_warning_close()
        else:
            messagebox.showwarning("检查失败", "⚠ 软件使用许可仍未恢复。\n\n所有功能保持锁定状态。", parent=warning_window)
    
    def exit_software():
        app_instance.on_closing()
        app_instance.root.quit()
    
    refresh_btn = create_bw_button(button_frame, "⟳ 重新验证许可", refresh_check, "primary", width=18)
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_software, "danger", width=15)
    exit_btn.pack(side=tk.RIGHT, padx=5)
    
    warning_window.update_idletasks()
    x = (warning_window.winfo_screenwidth() - warning_window.winfo_width()) // 2
    y = (warning_window.winfo_screenheight() - warning_window.winfo_height()) // 2
    warning_window.geometry(f"+{x}+{y}")
    
    warning_window.grab_set()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_uac():
    if is_admin():
        return True
        
    try:
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = sys.argv[0]
        
        result = ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            current_file, 
            " ".join(sys.argv[1:]), 
            None, 
            1
        )
        
        if result > 32:
            return True
        else:
            print("请求管理员权限失败")
            return False
    except Exception as e:
        print(f"请求管理员权限失败: {e}")
        return False

def main():
    if platform.system() != "Windows":
        messagebox.showerror("错误", "此程序目前仅支持Windows系统")
        return
    
    # 第一步：显示免责声明
    print("显示免责声明...")
    if not show_disclaimer():
        print("用户不同意免责声明，程序退出")
        return
    
    # 第二步：创建主程序窗口
    print("创建主程序窗口...")
    root = tk.Tk()
    app = LMFP_MinecraftTool(root)
    
    # 检查软件更新
    print("检查软件更新...")
    root.after(1000, lambda: check_for_updates(root))
    
    # 第六步：启动云端许可监控
    print("启动云端许可监控...")
    start_cloud_monitor(app)
    
    # 第七步：启动联机大厅自动刷新
    def start_auto_refresh():
        def auto_refresh_loop():
            while True:
                time.sleep(30)  # 30秒刷新一次
                if app.cloud_permission_granted and hasattr(app, 'root') and app.root.winfo_exists():
                    app.root.after(0, lambda: app.refresh_rooms(auto_refresh=True))
        
        threading.Thread(target=auto_refresh_loop, daemon=True).start()
    
    start_auto_refresh()
    
    print("启动主程序主循环...")
    root.mainloop()

if __name__ == "__main__":
    main()