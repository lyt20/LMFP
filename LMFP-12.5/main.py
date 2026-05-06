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
import winsound
from xml.etree import ElementTree as ET
import tempfile
import tkinter.font as tkFont

# 导入UDP广播模块
from send import MulticastServer
# 导入token解密模块（如果tokens.py不存在，则使用默认不解密函数）
try:
    from tokens import decrypt_token
except ImportError:
    # 如果tokens.py不存在，定义一个直接返回原始值的函数
    def decrypt_token(encrypted_token):
        """当tokens.py不存在时，直接返回原始token，不进行解密"""
        return encrypted_token
# 导入mcstatus库用于检测Minecraft服务器
try:
    from mcstatus import JavaServer
    MCSTATUS_AVAILABLE = True
except ImportError:
    MCSTATUS_AVAILABLE = False

# 全局失败计数器，用于跟踪连续访问 LMFP 服务器失败的次数
lmfp_server_failure_count = 0
MAX_FAILURE_COUNT = 3  # 连续失败 3 次后报错

# API 域名配置
apis = "lytapi.asia"
# LMFP 版本号配置
lmfpvers = "12.5.0"

def calculate_file_sha256(file_path):
    """计算文件的SHA-256哈希值"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # 分块读取文件，避免大文件占用过多内存
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return None
    except Exception as e:
        print(f"计算文件哈希值时发生错误: {e}")
        return None


def get_expected_hash_from_server():
    """从服务器获取期望的哈希值"""
    try:
        # 根据版本号生成文件名（版本号*100）
        # version_num = int(float(lmfpvers) * 100)
        url = f"https://{apis}/hs{lmfpvers}.txt"
        req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
        with urlopen(req, timeout=None) as response:
            expected_hash = response.read().decode('utf-8').strip()
            return expected_hash
    except Exception as e:
        print(f"获取服务器哈希值时发生错误: {e}")
        return None

def get_up_exe_hash_from_server():
    """从服务器获取up.exe的期望哈希值"""
    try:
        url = f"https://{apis}/dl/uphash.txt"
        req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
        with urlopen(req, timeout=None) as response:
            expected_hash = response.read().decode('utf-8').strip()
            return expected_hash
    except Exception as e:
        print(f"获取up.exe服务器哈希值时发生错误: {e}")
        return None

def check_cj_activation():
    """检查cj.txt内容，如果为 1 则在浏览器打开https://{apis}/cj"""
    try:
        url = f"https://{apis}/cj.txt"
        req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
        with urlopen(req, timeout=None) as response:
            content = response.read().decode('utf-8').strip()
            print(f"获取到cj.txt内容: {content}")
            
            if content == "1":
                print(f"cj.txt内容为 1，准备在浏览器打开https://{apis}/cj")
                # 在默认浏览器中打开网页
                webbrowser.open(f"https://{apis}/cj")
                print(f"已在浏览器中打开https://{apis}/cj")
            else:
                print(f"cj.txt内容不是1，当前内容: {content}")
                
    except Exception as e:
        print(f"检查cj激活状态时发生错误: {e}")


def show_hash_mismatch_dialog(current_hash=None, expected_hash=None):
    """显示哈希值不匹配的弹窗，只允许用户退出软件"""
    # 创建一个临时的root窗口用于显示弹窗（独立于主窗口）
    temp_root = tk.Tk()
    temp_root.withdraw()  # 隐藏临时root窗口
    
    # 创建自定义弹窗（设置为独立顶级窗口）
    dialog = tk.Toplevel(temp_root)
    dialog.title("安全警告")
    dialog.geometry("500x350")
    dialog.resizable(False, False)
    
    # 设置窗口始终在最前且独立于主窗口
    dialog.attributes('-topmost', True)
    # 确保窗口是独立的，不依赖于任何其他窗口
    
    # 居中显示
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    # 构建警告内容
    warning_message = "警告：软件完整性验证失败！\n\n当前软件的哈希值与官方服务器不符，\n可能存在安全风险。\n\n详细信息：\n本地校验值: "
    if current_hash:
        warning_message += current_hash
    else:
        warning_message += "无法获取"
    warning_message += "\n云端校验值: "
    if expected_hash:
        warning_message += expected_hash
    else:
        warning_message += "无法获取"
    warning_message += "\n\n请退出软件并重新下载正版软件。"
    
    # 添加警告内容
    warning_text = tk.Label(dialog, text=warning_message, 
                           font=("Segoe UI", 10), fg="red", wraplength=450, justify="left")
    warning_text.pack(pady=20)
    
    # 添加确定按钮（退出软件）
    exit_btn = tk.Button(dialog, text="确定", command=lambda: os._exit(0), 
                         bg="#ff4444", fg="white", font=("Segoe UI", 10, "bold"),
                         relief="flat", bd=0, padx=20, pady=5)
    exit_btn.pack(pady=10)
    
    # 当用户点击关闭窗口时也退出程序
    dialog.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
    
    # 显示弹窗并等待其关闭
    dialog.focus_force()
    dialog.grab_set()  # 模态窗口，阻止与其他窗口交互
    dialog.wait_window()  # 等待窗口关闭
    
    temp_root.destroy()


def verify_software_integrity():
    """验证软件完整性，比较当前程序的哈希值与服务器上的值"""
    try:
        # 获取当前运行的程序路径，考虑Nuitka打包情况
        if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS') or '__compiled__' in globals():
            # 如果是打包后的exe运行环境（包括PyInstaller, Nuitka等）
            current_exe_path = sys.executable
        else:
            # 如果是Python源码运行环境
            current_exe_path = __file__
            
            # 临时跳过.py文件的完整性验证
            print("检测到运行.py文件，临时跳过软件完整性验证")
            return True
        
        # 计算当前文件的SHA-256哈希值
        current_hash = calculate_file_sha256(current_exe_path)
        if current_hash is None:
            # 如果无法计算哈希值，可能是Nuitka环境或其他问题，尝试获取当前文件的路径
            try:
                # 尝试使用os.path.abspath获取当前执行文件的绝对路径
                current_exe_path = os.path.abspath(sys.argv[0])
                current_hash = calculate_file_sha256(current_exe_path)
                if current_hash is None:
                    # 如果仍然失败，尝试使用sys.executable
                    current_exe_path = os.path.abspath(sys.executable)
                    current_hash = calculate_file_sha256(current_exe_path)
            except:
                pass
        
        if current_hash is None:
            # 如果仍然无法计算哈希值，显示错误并退出
            show_hash_mismatch_dialog(current_hash, None)
            return False
        
        # 从服务器获取期望的哈希值
        expected_hash = get_expected_hash_from_server()
        if expected_hash is None:
            # 如果无法获取服务器哈希值，显示错误并退出
            show_hash_mismatch_dialog(current_hash, expected_hash)
            return False
        
        # 比较哈希值
        if current_hash.lower() != expected_hash.lower():
            print(f"哈希值不匹配! 当前: {current_hash}, 期望: {expected_hash}")
            show_hash_mismatch_dialog(current_hash, expected_hash)
            return False
        else:
            print("软件完整性验证通过")
            return True
            
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        show_hash_mismatch_dialog(None, None)
        return False

# 启动时验证软件完整性
if not verify_software_integrity():
    # 验证失败，程序已退出
    pass

def verify_frpc_integrity():
    """验证 frpc.exe 的完整性，检查其 SHA256 哈希值"""
    frpc_path = "./frpc.exe"
    expected_frpc_hash = "df90560c6b99f5f4edfeec7e674262dcf5a34024d450089c59835ffb118d2493"
    
    # 检查文件是否存在
    if not os.path.exists(frpc_path):
        print(f"错误：找不到文件 {frpc_path}")
        return False
    
    # 计算 frpc.exe 的 SHA-256 哈希值
    current_frpc_hash = calculate_file_sha256(frpc_path)
    if current_frpc_hash is None:
        print("错误：无法计算 frpc.exe 的哈希值")
        return False
    
    # 比较哈希值
    if current_frpc_hash.lower() != expected_frpc_hash.lower():
        print(f"frpc.exe 哈希值不匹配！当前：{current_frpc_hash}, 期望：{expected_frpc_hash}")
        return False
    else:
        print("frpc.exe 完整性验证通过")
        return True



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

# DPI缩放辅助函数
# DPI缩放已禁用，使用固定值
dpi_scale_factor = 1.0


def adjust_font_size(font_tuple, scale_factor=1.0):
    """字体大小调整函数（已禁用缩放）"""
    if isinstance(font_tuple, str):
        # 如果是字体名称而不是元组，直接返回
        return font_tuple
    
    font_list = list(font_tuple)
    if len(font_list) >= 2 and isinstance(font_list[1], int):
        # 不调整字体大小，直接使用原始大小
        font_list[1] = font_list[1]
    return tuple(font_list)


# 字体配置（不使用DPI缩放）
BW_FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "subtitle": ("Segoe UI", 12, "bold"), 
    "normal": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "button": ("Segoe UI", 10, "bold"),
    "bold_small": ("Segoe UI", 9, "bold")  # 加粗小字体用于@用户名
}

def show_room_info_popup(room_info, is_created=True):
    """显示房间信息弹窗（独立于主窗口）"""
    if not globals().get('PYSIDE6_AVAILABLE', False):
        # 创建独立的顶级窗口
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
        
        popup.attributes('-topmost', True)
        
        main_container = create_bw_frame(popup)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
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
        
        if is_created:
            direct_ip = f"{room_info['server_addr']}:{room_info['remote_port']}"
            content = f"""创建房间成功！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址：{direct_ip}
本地 Minecraft 端口：{room_info['mc_port']}

其他玩家进入方式：
方式 1（推荐 - 使用软件联机）：
  1. 打开本软件
  2. 输入完整房间号：{room_info['full_room_code']}
  3. 点击“加入联机房间”即可连接

方式 2（Minecraft 直连）：
  1. 在 Minecraft 多人游戏中添加服务器
  2. 服务器地址输入：{direct_ip}
  3. 进入服务器即可

注意：请不要关闭本程序，否则联机会断开"""
        else:
            content = f"""成功加入房间！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址: [已隐藏]

进入方式：
1. 在Minecraft中点多人游戏，双击黄色联机标题即可进入
2. 手动添加服务器：127.0.0.1
注意：请不要关闭本程序，否则隧道会断开"""
        
        info_text.insert(tk.END, content)
        info_text.config(state=tk.DISABLED)
        
        button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def close_popup():
            popup.destroy()
        
        close_btn = create_bw_button(button_frame, "关闭", close_popup, "primary", width=12)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        return popup
    else:
        def show_pyside():
            try:
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton
                from PySide6.QtGui import QFont, QIcon
                from PySide6.QtCore import Qt
                import os
                
                popup = QDialog()
                popup.setWindowTitle("房间信息" if is_created else "加入房间信息")
                popup.setFixedSize(550, 480)
                popup.setStyleSheet("""
                    QDialog {
                        background-color: #F0F4F8;
                    }
                """)
                popup.setWindowFlags(popup.windowFlags() | Qt.WindowStaysOnTopHint)
                
                try:
                    icon_path = "lyy.ico"
                    if os.path.exists(icon_path):
                        popup.setWindowIcon(QIcon(icon_path))
                except:
                    pass
                
                layout = QVBoxLayout(popup)
                layout.setContentsMargins(25, 25, 25, 25)
                layout.setSpacing(15)
                
                title_label = QLabel("房间信息" if is_created else "加入房间信息")
                title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
                title_label.setFont(title_font)
                title_label.setStyleSheet("color: #102A43; font-family: 'Microsoft YaHei';")
                layout.addWidget(title_label)
                
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                
                if is_created:
                    direct_ip = f"{room_info['server_addr']}:{room_info['remote_port']}"
                    content = f"""创建房间成功！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址：{direct_ip}
本地 Minecraft 端口：{room_info['mc_port']}

其他玩家进入方式：
方式 1（推荐 - 使用软件联机）：
  1. 打开本软件
  2. 输入完整房间号：{room_info['full_room_code']}
  3. 点击加入联机房间即可连接

方式 2（Minecraft 直连）：
  1. 在 Minecraft 多人游戏中添加服务器
  2. 服务器地址输入：{direct_ip}
  3. 进入服务器即可

注意：请不要关闭本程序，否则联机会断开"""
                else:
                    content = f"""成功加入房间！

房间信息：
完整房间号: {room_info['full_room_code']}
服务器地址: [已隐藏]

进入方式：
1. 在Minecraft中点多人游戏，双击黄色联机标题即可进入
2. 手动添加服务器：127.0.0.1
注意：请不要关闭本程序，否则隧道会断开"""
                
                text_edit.setPlainText(content)
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #FFFFFF;
                        color: #102A43;
                        border: 1px solid #D9E2EC;
                        border-radius: 12px;
                        padding: 15px;
                        font-size: 10.5pt;
                        font-family: 'Microsoft YaHei', 'Segoe UI';
                        line-height: 1.5;
                    }
                """)
                layout.addWidget(text_edit)
                
                btn_layout = QHBoxLayout()
                btn_layout.addStretch()
                
                close_btn = QPushButton("关闭")
                close_btn.setDefault(True)
                close_btn.setFixedWidth(100)
                close_btn.setFixedHeight(35)
                close_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #1E88E5;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        font-size: 10.5pt;
                        font-weight: bold;
                        font-family: 'Microsoft YaHei', 'Segoe UI';
                    }
                    QPushButton:hover {
                        background-color: #1565C0;
                    }
                    QPushButton:pressed {
                        background-color: #0D47A1;
                    }
                """)
                close_btn.clicked.connect(popup.accept)
                btn_layout.addWidget(close_btn)
                layout.addLayout(btn_layout)
                
                popup.exec()
            except Exception as e:
                print(f"显示PySide房间信息弹窗失败: {e}")
                
        app_inst = globals().get('global_tkinter_app_instance')
        if app_inst and hasattr(app_inst, 'pyside_window') and app_inst.pyside_window:
            app_inst.pyside_window.signals.ui_callback_requested.emit(show_pyside)
        else:
            # 备用：尝试直接执行
            try:
                show_pyside()
            except:
                pass
        return None

def create_bw_button(parent, text, command, style="primary", width=None):
    """创建黑白灰风格按钮"""
    # 固定的padding值（已禁用DPI缩放）
    scaled_padx = 20
    scaled_pady = 8
    
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
        padx=scaled_padx,
        pady=scaled_pady,
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
    # 固定的边框宽度（已禁用DPI缩放）
    scaled_bd = 1
    scaled_highlightthickness = 1
    
    return tk.Frame(
        parent,
        bg=BW_COLORS["card_bg"],
        relief="flat",
        bd=scaled_bd,
        highlightbackground=BW_COLORS["border"],
        highlightthickness=scaled_highlightthickness,
        **kwargs
    )

def create_section_title(parent, text):
    """创建分区标题"""
    # 固定的间距值（已禁用DPI缩放）
    scaled_padding_y = 10
    scaled_separator_height = 2
    scaled_separator_pady = 2
    scaled_label_padx = 15
    
    title_frame = tk.Frame(parent, bg=BW_COLORS["background"])
    title_frame.pack(fill=tk.X, pady=(scaled_padding_y, scaled_padding_y//2))
    
    title_label = tk.Label(
        title_frame,
        text=text,
        font=BW_FONTS["subtitle"],
        bg=BW_COLORS["background"],
        fg=BW_COLORS["primary"],
        anchor="w"
    )
    title_label.pack(fill=tk.X, padx=scaled_label_padx)
    
    # 添加装饰线
    separator = tk.Frame(title_frame, height=scaled_separator_height, bg=BW_COLORS["primary"])
    separator.pack(fill=tk.X, padx=scaled_label_padx, pady=(scaled_separator_pady, 0))
    
    return title_frame

def show_network_error_dialog(force_show=False):
    """显示网络连接错误弹窗
    
    Args:
        force_show (bool): 是否强制显示弹窗，即使未达到失败次数
    """
    global lmfp_server_failure_count
    
    # 只有在连续失败3次或强制显示时才弹出错误对话框
    if force_show or lmfp_server_failure_count >= MAX_FAILURE_COUNT:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("网络连接错误", "无法连接LMFP软件服务器，请检查网络后再试试（联系QQ 2232908600）")
        root.destroy()
        # 重置计数器
        lmfp_server_failure_count = 0

def check_cloud_permission():
    """检查云端软件使用许可，返回验证类型: 'whitelist'表示白名单验证，'normal'表示普通许可验证，False表示验证失败"""
    def check_permission():
        global lmfp_server_failure_count
        
        try:
            # 首先检查设备码白名单 - 获取主板设备码
            import machineid
            
            # 获取主板设备码
            board_sn = "未获取"
            try:
                board_sn = machineid.id()
            except Exception as e:
                print(f"获取主板设备码失败: {e}")
                
            print(f"检测到的主板设备码: {board_sn}")
            
            if board_sn != "未获取":
                # 请求白名单验证接口
                whitelist_url = f"https://{apis}/vert.php?tk={board_sn}"
                whitelist_req = Request(whitelist_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                
                with urlopen(whitelist_req, timeout=None) as response:
                    result = response.read().decode('utf-8').strip()
                    
                    if result.lower() == "true":
                        print(f"检测到主板设备码 {board_sn} 在白名单中，跳过许可验证")
                        print(f"白名单验证结果: SUCCESS - 设备已在许可列表中")
                        # 成功访问服务器，重置失败计数器
                        lmfp_server_failure_count = 0
                        return 'whitelist'
                    else:
                        print(f"主板设备码不在白名单中，进行常规许可验证")
                        print(f"白名单验证结果: FAILED - 设备未在许可列表中")
            else:
                print(f"主板设备码未获取，进行常规许可验证")
                print(f"白名单验证结果: FAILED - 设备未在许可列表中")
                
        except Exception as e:
            print(f"检查设备码白名单失败: {e}")
            print("白名单验证结果: NETWORK_ERROR - 无法连接验证服务器")
            # 增加失败计数
            lmfp_server_failure_count += 1
            print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
            # 显示错误弹窗（仅在连续失败3次时）
            show_network_error_dialog()
            return False
        
        # 云端许可验证已禁用，直接返回通过
        print("云端许可验证: 已跳过（功能已禁用），直接返回通过")
        lmfp_server_failure_count = 0
        return 'normal'
    
    return check_permission()

def show_modern_error_dialog(parent_window, title, message):
    """显示现代化的错误提示弹窗 - PySide6版本"""
    show_modern_message(parent_window, title, message, "error")

def show_modern_message(parent_window, title, message, msg_type="error"):
    """
    显示现代化的弹窗 - PySide6版本
    msg_type: 'error', 'info', 'warning'
    """
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        # 检查是否有PySide窗口引用
        pyside_win = None
        if parent_window:
            if hasattr(parent_window, 'pyside_window') and parent_window.pyside_window:
                pyside_win = parent_window.pyside_window
            elif parent_window.__class__.__name__ == 'PySideMainWindow':
                pyside_win = parent_window
        
        if pyside_win is None:
            # 回退到tkinter
            import tkinter.messagebox
            if msg_type == "error":
                tkinter.messagebox.showerror(title, message)
            elif msg_type == "warning":
                tkinter.messagebox.showwarning(title, message)
            else:
                tkinter.messagebox.showinfo(title, message)
            return
            
        dialog = QDialog(pyside_win)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 200)
        dialog.setModal(True)
        
        # 设置样式
        dialog.setStyleSheet("""
            QDialog { background-color: #F5F7FA; }
            QLabel { color: #333333; background: transparent; }
            QPushButton { padding: 8px 25px; border-radius: 6px; font-size: 14px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 20)
        layout.setSpacing(15)
        
        # 图标和颜色样式
        if msg_type == "success":
            icon = "✓"
            color = "#4CAF50"
        elif msg_type == "error":
            icon = "✗"
            color = "#D32F2F"
        elif msg_type == "warning":
            icon = "⚠"
            color = "#F57C00"
        else: # info
            icon = "ℹ"
            color = "#1976D2"
        
        title_label = QLabel(f"{icon} {title}")
        title_font = QFont(); title_font.setPointSize(14); title_font.setBold(True)
        title_label.setFont(title_font); title_label.setStyleSheet(f"color: {color};")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel(message)
        content_label.setWordWrap(True); content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("font-size: 13px; color: #555555;")
        layout.addWidget(content_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: {color}; color: white; border: none; 
                padding: 10px 30px; border-radius: 6px; font-weight: bold;
            }} 
            QPushButton:hover {{ background-color: {color}; opacity: 0.8; }}
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec()
    except Exception as e:
        print(f"PySide对话框创建失败: {e}")
        import tkinter.messagebox
        tkinter.messagebox.showerror(title, message)
            
        dialog = QDialog(pyside_win)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 180)
        dialog.setModal(True)
        
        # 设置样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                padding: 8px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 20)
        layout.setSpacing(15)
        
        # 标题区域
        title_label = QLabel(f"⚠ {title}")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #D32F2F;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 内容区域
        content_label = QLabel(message)
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("font-size: 13px; color: #555555;")
        layout.addWidget(content_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    except Exception as e:
        print(f"PySide错误对话框创建失败: {e}")
        import tkinter.messagebox
        tkinter.messagebox.showerror(title, message)

def show_mc_port_error_dialog(parent_window=None):
    """显示未检测到Minecraft服务器端口的错误弹窗 - PySide6版本"""
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        # 检查是否有PySide窗口引用
        pyside_win = None
        if parent_window:
            if hasattr(parent_window, 'pyside_window') and parent_window.pyside_window:
                pyside_win = parent_window.pyside_window
            elif parent_window.__class__.__name__ == 'PySideMainWindow':
                pyside_win = parent_window

        if pyside_win is None:
            # 回退到tkinter
            import tkinter.messagebox
            tkinter.messagebox.showerror("错误", "未检测到Minecraft服务器运行\n\n请确保已在Minecraft中开启局域网游戏")
            return
            
        dialog = QDialog(pyside_win)
        dialog.setWindowTitle("错误 - 未检测到端口")
        dialog.setFixedSize(420, 200)
        dialog.setModal(True)
        
        # 设置现代风格样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                padding: 8px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 25, 30, 20)
        layout.setSpacing(15)
        
        # 错误图标和标题
        title_label = QLabel("⚠ 未检测到Minecraft端口")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #D32F2F;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 错误内容说明
        content_label = QLabel("未检测到Minecraft服务器运行。\n\n请确保已在Minecraft中开启局域网游戏。")
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("font-size: 13px; color: #555555;")
        layout.addWidget(content_label)
        
        # 确定按钮区域
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        ok_btn.setDefault(True)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        ok_btn.clicked.connect(dialog.accept)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    except Exception as e:
        print(f"PySide弹窗创建失败: {e}")
        import tkinter.messagebox
        tkinter.messagebox.showerror("错误", "未检测到Minecraft服务器运行\n\n请确保已在Minecraft中开启局域网游戏")


def check_for_updates(root_window=None):
    """检查软件更新"""
    try:
        # 读取本地版本号
        #local_version = str(int(float(lmfpvers) * 100))  # 默认版本
        if os.path.exists("v.txt"):
            with open("v.txt", "r", encoding="utf-8") as f:
                local_version = f.read().strip()
        else:
            # 如果 v.txt 不存在，创建它并设置默认版本
            with open("v.txt", "w", encoding="utf-8") as f:
                f.write(str(int(float(lmfpvers) * 100)))
            print(f"已创建 v.txt 文件并设置默认版本为 {lmfpvers}")
        
        # 获取云端版本号
        url = f"https://{apis}/v.txt"
        req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
        with urlopen(req, timeout=None) as response:
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
    """显示更新对话框 - PySide6版本（只在PySide窗口中显示）"""
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        
        # 检查是否有PySide窗口引用
        pyside_win = None
        
        # 如果parent_window是app_instance（LMFP_MinecraftTool），获取其pyside_window
        if hasattr(parent_window, 'pyside_window') and parent_window.pyside_window is not None:
            pyside_win = parent_window.pyside_window
        # 如果parent_window本身就是PySide窗口
        elif hasattr(parent_window, 'nav_list'):
            pyside_win = parent_window
        
        if pyside_win is None:
            # 如果没有PySide窗口，不显示任何对话框（只使用PySide）
            print("未检测到PySide窗口，跳过更新提示")
            return False
        
        # 创建PySide对话框
        dialog = QDialog(pyside_win)
        dialog.setWindowTitle("发现软件新版本")
        dialog.setFixedSize(500, 220)
        dialog.setModal(True)
        
        # 设置样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("发现软件新版本")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1565C0;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel(
            f"检测到新的版本 {cloud_version}，当前版本为 {local_version}。\n\n"
            f"是否立即更新？（如果不更新，可能因为过老的软件版本而无法联机）"
        )
        content_label.setWordWrap(True)
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("font-size: 13px; color: #555555;")
        layout.addWidget(content_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        update_btn = QPushButton("✓ 立即更新（推荐）")
        update_btn.setDefault(True)
        update_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        later_btn = QPushButton("稍后提醒我")
        later_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #666666;
                border: 1px solid #E0E0E0;
            }
            QPushButton:hover {
                background-color: #F5F5F5;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        
        def update_now():
            dialog.accept()
            perform_update_pyside()
        
        def remind_later():
            dialog.reject()
        
        update_btn.clicked.connect(update_now)
        later_btn.clicked.connect(remind_later)
        
        button_layout.addWidget(update_btn)
        button_layout.addWidget(later_btn)
        layout.addLayout(button_layout)
        
        # 显示对话框
        result = dialog.exec()
        return result == QDialog.Accepted
        
    except ImportError:
        # 如果PySide6不可用，不显示任何对话框
        print("未检测到PySide6，跳过更新提示")
        return False
    except Exception as e:
        print(f"PySide更新对话框创建失败: {e}")
        import traceback
        traceback.print_exc()
        # 出错时也不显示Tkinter对话框
        return False

def _show_update_dialog_tkinter(parent_window, local_version, cloud_version):
    """显示更新对话框 - Tkinter版本（备用，独立于主窗口）"""
    update_dialog = tk.Toplevel()
    update_dialog.title("发现软件新版本")
    update_dialog.geometry("500x220")
    update_dialog.resizable(False, False)
    update_dialog.configure(bg=BW_COLORS["background"])
    # 移除 transient 和 grab_set，使窗口可以独立于主窗口存在
    
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

def perform_update_pyside():
    """执行更新操作 - PySide6版本（仿照Tkinter逻辑）"""
    try:
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QTextEdit
        from PySide6.QtCore import Qt, QThread, Signal, QTimer
        from PySide6.QtGui import QFont
        import urllib.request
        import json
        import time
        import hashlib
        
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
        dialog = QDialog()
        dialog.setWindowTitle("正在下载更新器")
        dialog.setFixedSize(500, 400)
        dialog.setModal(True)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QLabel {
                color: #333333;
            }
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
                background-color: #FFFFFF;
            }
            QProgressBar::chunk {
                background-color: #1976D2;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 提示文本
        label = QLabel("正在下载最新版本的 up.exe，请稍候...")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 14px; color: #555555;")
        layout.addWidget(label)
        
        # 进度条
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setFixedHeight(25)
        layout.addWidget(progress)
        
        # 日志文本框
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet("""
            QTextEdit {
                font-family: Consolas, monospace;
                font-size: 12px;
                color: #333333;
            }
        """)
        layout.addWidget(log_text)
        
        # 后台下载线程
        class DownloadThread(QThread):
            progress_signal = Signal(int, str)  # value, text
            log_signal = Signal(str)
            completed_signal = Signal()
            failed_signal = Signal()
            
            def run(self):
                try:
                    self._download_updater()
                except Exception as e:
                    self.log_signal.emit(f"下载失败: {str(e)}")
                    self.failed_signal.emit()
            
            def _download_updater(self):
                """下载更新器 - 完全仿照Tkinter逻辑"""
                max_retries = 3
                
                # 首先从upxz.txt获取A链接
                a_link_url = f"https://{apis}/dl/upxz.txt"
                self.log_signal.emit(f"正在从 {a_link_url} 获取A链接...")
                
                # 获取A链接 - 带重试机制
                a_link = None
                for attempt in range(max_retries + 1):
                    try:
                        self.log_signal.emit(f"获取A链接... (尝试 {attempt + 1}/{max_retries + 1})")
                        req = Request(a_link_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                        with urlopen(req, timeout=None) as response:
                            a_link = response.read().decode('utf-8').strip()
                        self.log_signal.emit(f"获取到A链接: {a_link}")
                        break  # 成功获取，跳出循环
                    except Exception as e:
                        self.log_signal.emit(f"获取A链接失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                        if attempt >= max_retries:
                            # 所有重试都失败，使用默认链接
                            self.log_signal.emit("获取 A 链接的所有重试都失败，使用默认下载链接")
                            download_url = f"https://{apis}/dl/up.exe"
                            a_link = None  # 标记为获取失败
                            break
                        time.sleep(2)  # 等待2秒后重试
                
                # 如果成功获取了A链接，则使用API获取真实下载链接
                if a_link:
                    # 使用A链接和密码获取真实下载链接 - 带重试机制
                    api_url = f"https://{apis}/lz/?url={a_link}&pwd=1234"
                    self.log_signal.emit(f"正在调用API获取真实下载链接: {api_url}")
                    
                    for attempt in range(max_retries + 1):
                        try:
                            self.log_signal.emit(f"调用API... (尝试 {attempt + 1}/{max_retries + 1})")
                            req = Request(api_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                            with urlopen(req, timeout=None) as response:
                                api_response = response.read().decode('utf-8')
                            
                            # 解析API返回的JSON数据
                            try:
                                api_data = json.loads(api_response)
                            except json.JSONDecodeError as e:
                                self.log_signal.emit(f"解析 API 响应 JSON 失败：{str(e)}")
                                # 如果解析失败，使用默认链接
                                download_url = f"https://{apis}/dl/up.exe"
                                self.log_signal.emit(f"使用默认下载链接: {download_url}")
                                break
                            
                            if api_data.get('code') == 200:
                                download_url = api_data.get('downUrl')
                                self.log_signal.emit(f"获取到真实下载地址: {download_url}")
                                
                                # 检查下载链接长度，如果超过300字符则重新获取
                                max_length_retries = 10
                                length_retry_count = 0
                                while len(download_url) > 300 and length_retry_count < max_length_retries:
                                    length_retry_count += 1
                                    self.log_signal.emit(f"下载链接长度超过300字符 ({len(download_url)} 字符)，正在进行第{length_retry_count}次重新获取...")
                                    
                                    # 重新调用API获取新的下载链接
                                    try:
                                        req = Request(api_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                                        with urlopen(req, timeout=None) as response:
                                            api_response = response.read().decode('utf-8')
                                        api_data = json.loads(api_response)
                                        if api_data.get('code') == 200:
                                            download_url = api_data.get('downUrl')
                                            self.log_signal.emit(f"重新获取到下载地址: {download_url} (长度: {len(download_url)} 字符)")
                                        else:
                                            self.log_signal.emit(f"重新获取API返回错误: {api_data.get('msg', '未知错误')}")
                                            break
                                    except Exception as e:
                                        self.log_signal.emit(f"重新获取下载链接失败: {str(e)}")
                                        break
                                    
                                    time.sleep(1)  # 等待1秒后重试
                                
                                if length_retry_count >= max_length_retries:
                                    self.log_signal.emit(f"已达到最大重试次数({max_length_retries})，使用当前下载链接")
                                
                                break  # 成功获取，跳出循环
                            else:
                                self.log_signal.emit(f"API 返回错误：{api_data.get('msg', '未知错误')}")
                                # 如果 API 调用失败，使用默认链接
                                download_url = f"https://{apis}/dl/up.exe"
                                self.log_signal.emit(f"使用默认下载链接: {download_url}")
                                break
                        except Exception as e:
                            self.log_signal.emit(f"API调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                            if attempt >= max_retries:
                                # 所有重试都失败，使用默认链接
                                self.log_signal.emit("API 调用的所有重试都失败，使用默认下载链接")
                                download_url = f"https://{apis}/dl/up.exe"
                            else:
                                time.sleep(2)  # 等待2秒后重试
                else:
                    # 如果未能获取 A 链接，则使用默认下载链接
                    download_url = f"https://{apis}/dl/up.exe"
                    self.log_signal.emit(f"使用默认下载链接: {download_url}")
                
                # 下载最新的up.exe - 带重试机制
                self.log_signal.emit(f"正在从 {download_url} 下载最新的up.exe...")
                
                download_successful = False
                file_content = b''
                for attempt in range(max_retries + 1):
                    try:
                        self.log_signal.emit(f"开始下载... (尝试 {attempt + 1}/{max_retries + 1})")
                        
                        # 创建请求对象，添加User-Agent头部以避免某些服务器的访问限制
                        req = Request(download_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                        
                        # 首先获取文件大小
                        with urlopen(req, timeout=None) as response:
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
                                    progress_text = f"正在下载: {downloaded}/{total_size} bytes ({int((downloaded/total_size)*100)}%)"
                                    self.progress_signal.emit(progress_value, progress_text)
                        
                        # 检查文件是否已成功下载
                        if len(file_content) > 0:
                            download_successful = True
                            break  # 成功下载，跳出循环
                        else:
                            raise Exception("下载的文件为空")
                    except Exception as e:
                        self.log_signal.emit(f"下载失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}")
                        if attempt >= max_retries:
                            # 所有重试都失败
                            self.log_signal.emit("下载的所有重试都失败")
                        else:
                            time.sleep(2)  # 等待2秒后重试
                
                if download_successful:
                    # 写入文件
                    with open("up.exe", "wb") as f:
                        f.write(file_content)
                    
                    self.log_signal.emit("up.exe下载完成，正在验证文件完整性...")
                    
                    # 验证下载的up.exe文件的完整性
                    validation_success = False
                    validation_attempts = 0
                    max_validation_retries = 3
                    
                    while validation_attempts < max_validation_retries:
                        # 从服务器获取up.exe的期望哈希值
                        expected_hash = get_up_exe_hash_from_server()
                        if expected_hash is None:
                            self.log_signal.emit(f"获取服务器哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})")
                            validation_attempts += 1
                            if validation_attempts >= max_validation_retries:
                                self.log_signal.emit("无法获取服务器哈希值，验证失败")
                                break
                            time.sleep(2)
                            continue
                        
                        # 计算下载文件的SHA-256哈希值
                        actual_hash = calculate_file_sha256("up.exe")
                        if actual_hash is None:
                            self.log_signal.emit(f"计算文件哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})")
                            validation_attempts += 1
                            if validation_attempts >= max_validation_retries:
                                self.log_signal.emit("无法计算文件哈希值，验证失败")
                                break
                            time.sleep(2)
                            continue
                        
                        # 比较哈希值
                        if actual_hash.lower() == expected_hash.lower():
                            self.log_signal.emit("up.exe文件完整性验证通过")
                            validation_success = True
                            break
                        else:
                            self.log_signal.emit(f"up.exe文件验证失败，哈希值不匹配 (尝试 {validation_attempts + 1}/{max_validation_retries})")
                            self.log_signal.emit(f"期望哈希值: {expected_hash}")
                            self.log_signal.emit(f"实际哈希值: {actual_hash}")
                            
                            # 删除不匹配的文件
                            try:
                                os.remove("up.exe")
                                self.log_signal.emit("已删除不匹配的 up.exe 文件")
                            except:
                                pass
                            
                            validation_attempts += 1
                            if validation_attempts >= max_validation_retries:
                                self.log_signal.emit("文件验证达到最大重试次数，验证失败")
                                break
                            
                            time.sleep(2)
                    
                    if validation_success:
                        self.log_signal.emit("下载完成，正在启动更新程序...")
                        self.completed_signal.emit()
                    else:
                        self.log_signal.emit("文件验证失败，更新中止")
                        self.failed_signal.emit()
                else:
                    self.log_signal.emit("下载失败")
                    self.failed_signal.emit()
        
        download_thread = DownloadThread()
        
        def on_progress(value, text):
            progress.setValue(value)
            label.setText(text)
        
        def on_log(text):
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_text.append(f"[{timestamp}] {text}")
            log_text.verticalScrollBar().setValue(log_text.verticalScrollBar().maximum())
        
        def on_completed():
            label.setText("下载完成，正在启动更新程序...")
            progress.setValue(100)
            log_text.append("[完成] 正在启动更新程序...")
            
            # 延迟后启动更新程序并退出
            def launch_updater():
                try:
                    import os
                    # 获取up.exe的绝对路径
                    updater_path = os.path.abspath("up.exe")
                    log_text.append(f"[调试] up.exe路径: {updater_path}")
                    log_text.append(f"[调试] 文件存在: {os.path.exists(updater_path)}")
                    
                    if os.path.exists(updater_path):
                        log_text.append("[调试] 正在启动up.exe...")
                        
                        # Windows下使用shell execute以管理员权限启动
                        if platform.system() == "Windows":
                            import ctypes
                            from ctypes import wintypes
                            
                            # 使用ShellExecuteW以管理员权限启动
                            SW_SHOWNORMAL = 1
                            SEE_MASK_NOZONECHECKS = 0x00400000
                            
                            result = ctypes.windll.shell32.ShellExecuteW(
                                None,           # hwnd
                                "runas",        # 以管理员权限运行
                                updater_path,   # 文件路径
                                None,           # 参数
                                os.path.dirname(updater_path),  # 工作目录
                                SW_SHOWNORMAL   # 显示方式
                            )
                            
                            # ShellExecute返回值大于32表示成功
                            if result > 32:
                                log_text.append(f"[调试] up.exe已启动 (返回值: {result})")
                            else:
                                log_text.append(f"[错误] ShellExecute失败 (返回值: {result})")
                                # 尝试普通方式启动
                                subprocess.Popen([updater_path], cwd=os.path.dirname(updater_path))
                                log_text.append("[调试] 已尝试普通方式启动")
                        else:
                            subprocess.Popen([updater_path])
                        
                        # 给一点时间让进程启动
                        import time
                        time.sleep(1.5)
                        
                        # 强制退出
                        log_text.append("[调试] 正在退出主程序...")
                        os._exit(0)
                    else:
                        log_text.append(f"[错误] up.exe不存在于: {updater_path}")
                except Exception as e:
                    log_text.append(f"[错误] 启动更新程序失败: {str(e)}")
                    import traceback
                    log_text.append(traceback.format_exc())
            
            QTimer.singleShot(1000, launch_updater)
        
        def on_failed():
            label.setText("更新失败")
            progress.setValue(0)
            log_text.append("[错误] 更新失败")
            
            QTimer.singleShot(3000, dialog.close)
        
        download_thread.progress_signal.connect(on_progress)
        download_thread.log_signal.connect(on_log)
        download_thread.completed_signal.connect(on_completed)
        download_thread.failed_signal.connect(on_failed)
        
        download_thread.start()
        
        # 显示对话框
        dialog.exec()
        
    except Exception as e:
        print(f"PySide更新失败: {e}")
        import traceback
        traceback.print_exc()
        # 回退到Tkinter版本
        perform_update()

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
    update_window.geometry("500x400")  # 增加窗口高度以容纳日志框
    update_window.resizable(True, True)  # 允许调整大小
    update_window.configure(bg=BW_COLORS["background"])
    update_window.attributes('-topmost', True)
    
    # 创建消息队列用于线程间通信
    message_queue = queue.Queue()
    
    # 居中显示
    update_window.update_idletasks()
    x = (update_window.winfo_screenwidth() - update_window.winfo_width()) // 2
    y = (update_window.winfo_screenheight() - update_window.winfo_height()) // 2
    update_window.geometry(f"+{x}+{y}")
    
    # 主容器
    main_frame = tk.Frame(update_window, bg=BW_COLORS["background"])
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # 添加提示文本
    label = tk.Label(main_frame, 
                     text="正在下载最新版本的 up.exe，请稍候...",
                     bg=BW_COLORS["background"],
                     fg=BW_COLORS["text_primary"],
                     font=BW_FONTS["normal"])
    label.pack(pady=(5, 5))
    
    # 添加进度条
    progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
    progress.pack(pady=(5, 10))
    
    # 日志框架
    log_frame = tk.Frame(main_frame, bg=BW_COLORS["card_bg"], relief="flat", bd=1,
                         highlightbackground=BW_COLORS["border"], highlightthickness=1)
    log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    # 日志文本框
    log_text = tk.Text(
        log_frame,
        height=10,
        font=BW_FONTS["small"],
        bg=BW_COLORS["light"],
        fg=BW_COLORS["text_primary"],
        relief="flat",
        bd=0,
        wrap=tk.WORD
    )
    log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 滚动条
    log_scrollbar = tk.Scrollbar(log_text)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text.config(yscrollcommand=log_scrollbar.set)
    log_scrollbar.config(command=log_text.yview)
    
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
                elif message['type'] == 'log':
                    # 添加日志信息到日志框
                    timestamp = time.strftime("[%H:%M:%S]")
                    log_text.insert(tk.END, f"{timestamp} {message['text']}\n")
                    log_text.see(tk.END)  # 滚动到底部
                elif message['type'] == 'completed':
                    # 下载完成
                    label['text'] = "下载完成，正在启动更新程序..."
                    progress['value'] = 100
                    # 添加完成日志
                    timestamp = time.strftime("[%H:%M:%S]")
                    log_text.insert(tk.END, f"{timestamp} 下载完成，正在启动更新程序...\n")
                    log_text.see(tk.END)
                elif message['type'] == 'failed':
                    # 下载失败
                    label['text'] = "更新失败"
                    progress['value'] = 0
                    # 添加失败日志
                    timestamp = time.strftime("[%H:%M:%S]")
                    log_text.insert(tk.END, f"{timestamp} 更新失败\n")
                    log_text.see(tk.END)
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
            # 首先从upxz.txt获取A链接
            a_link_url = f"https://{apis}/dl/upxz.txt"
            message_queue.put({'type': 'log', 'text': f"正在从 {a_link_url} 获取A链接..."})
                        
            # 获取A链接 - 带重试机制
            a_link = None
            max_retries = 3
            for attempt in range(max_retries + 1):
                try:
                    message_queue.put({'type': 'log', 'text': f"获取A链接... (尝试 {attempt + 1}/{max_retries + 1})"})
                    req = Request(a_link_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urlopen(req, timeout=None) as response:
                        a_link = response.read().decode('utf-8').strip()
                    message_queue.put({'type': 'log', 'text': f"获取到A链接: {a_link}"})
                    break  # 成功获取，跳出循环
                except Exception as e:
                    message_queue.put({'type': 'log', 'text': f"获取A链接失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"})
                    if attempt >= max_retries:
                        # 所有重试都失败，使用默认链接
                        message_queue.put({'type': 'log', 'text': "获取 A 链接的所有重试都失败，使用默认下载链接"})
                        download_url = f"https://{apis}/dl/up.exe"
                        a_link = None  # 标记为获取失败
                        break
                    time.sleep(2)  # 等待2秒后重试
                        
            # 如果成功获取了A链接，则使用API获取真实下载链接
            if a_link:
                # 使用A链接和密码获取真实下载链接 - 带重试机制
                api_url = f"https://{apis}/lz/?url={a_link}&pwd=1234"
                message_queue.put({'type': 'log', 'text': f"正在调用API获取真实下载链接: {api_url}"})
                            
                for attempt in range(max_retries + 1):
                    try:
                        message_queue.put({'type': 'log', 'text': f"调用API... (尝试 {attempt + 1}/{max_retries + 1})"})
                        req = Request(api_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                        with urlopen(req, timeout=None) as response:
                            api_response = response.read().decode('utf-8')
                                        
                        # 解析API返回的JSON数据
                        try:
                            api_data = json.loads(api_response)
                        except json.JSONDecodeError as e:
                            message_queue.put({'type': 'log', 'text': f"解析 API 响应 JSON 失败：{str(e)}"})
                            # 如果解析失败，使用默认链接
                            download_url = f"https://{apis}/dl/up.exe"
                            message_queue.put({'type': 'log', 'text': f"使用默认下载链接: {download_url}"})
                            break
                                    
                        if api_data.get('code') == 200:
                            download_url = api_data.get('downUrl')
                            message_queue.put({'type': 'log', 'text': f"获取到真实下载地址: {download_url}"})
                            
                            # 检查下载链接长度，如果超过300字符则重新获取
                            max_length_retries = 10
                            length_retry_count = 0
                            while len(download_url) > 300 and length_retry_count < max_length_retries:
                                length_retry_count += 1
                                message_queue.put({'type': 'log', 'text': f"下载链接长度超过300字符 ({len(download_url)} 字符)，正在进行第{length_retry_count}次重新获取..."})
                                
                                # 重新调用API获取新的下载链接
                                try:
                                    req = Request(api_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                                    with urlopen(req, timeout=None) as response:
                                        api_response = response.read().decode('utf-8')
                                    api_data = json.loads(api_response)
                                    if api_data.get('code') == 200:
                                        download_url = api_data.get('downUrl')
                                        message_queue.put({'type': 'log', 'text': f"重新获取到下载地址: {download_url} (长度: {len(download_url)} 字符)"})
                                    else:
                                        message_queue.put({'type': 'log', 'text': f"重新获取API返回错误: {api_data.get('msg', '未知错误')}"})
                                        break
                                except Exception as e:
                                    message_queue.put({'type': 'log', 'text': f"重新获取下载链接失败: {str(e)}"})
                                    break
                                
                                time.sleep(1)  # 等待1秒后重试
                            
                            if length_retry_count >= max_length_retries:
                                message_queue.put({'type': 'log', 'text': f"已达到最大重试次数({max_length_retries})，使用当前下载链接"})
                            
                            break  # 成功获取，跳出循环
                        else:
                            message_queue.put({'type': 'log', 'text': f"API 返回错误：{api_data.get('msg', '未知错误')}"})
                            # 如果 API 调用失败，使用默认链接
                            download_url = f"https://{apis}/dl/up.exe"
                            message_queue.put({'type': 'log', 'text': f"使用默认下载链接: {download_url}"})
                            break
                    except Exception as e:
                        message_queue.put({'type': 'log', 'text': f"API调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"})
                        if attempt >= max_retries:
                            # 所有重试都失败，使用默认链接
                            message_queue.put({'type': 'log', 'text': "API 调用的所有重试都失败，使用默认下载链接"})
                            download_url = f"https://{apis}/dl/up.exe"
                        else:
                            time.sleep(2)  # 等待2秒后重试
            else:
                # 如果未能获取 A 链接，则使用默认下载链接
                download_url = f"https://{apis}/dl/up.exe"
                message_queue.put({'type': 'log', 'text': f"使用默认下载链接: {download_url}"})
                        
            # 下载最新的up.exe - 带重试机制
            message_queue.put({'type': 'log', 'text': f"正在从 {download_url} 下载最新的up.exe..."})
                        
            download_successful = False
            for attempt in range(max_retries + 1):
                try:
                    message_queue.put({'type': 'log', 'text': f"开始下载... (尝试 {attempt + 1}/{max_retries + 1})"})
                                
                    # 创建请求对象，添加User-Agent头部以避免某些服务器的访问限制
                    req = Request(download_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                                
                    # 首先获取文件大小
                    with urlopen(req, timeout=None) as response:
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
                                
                    # 检查文件是否已成功下载
                    if len(file_content) > 0:
                        download_successful = True
                        break  # 成功下载，跳出循环
                    else:
                        raise Exception("下载的文件为空")
                except Exception as e:
                    message_queue.put({'type': 'log', 'text': f"下载失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"})
                    if attempt >= max_retries:
                        # 所有重试都失败
                        message_queue.put({'type': 'log', 'text': "下载的所有重试都失败"})
                    else:
                        time.sleep(2)  # 等待2秒后重试
                        
            if download_successful:
                # 写入文件
                with open("up.exe", "wb") as f:
                    f.write(file_content)
                                
                message_queue.put({'type': 'log', 'text': "up.exe下载完成，正在验证文件完整性..."})
                
                # 验证下载的up.exe文件的完整性
                validation_success = False
                validation_attempts = 0
                max_validation_retries = 3
                
                while validation_attempts < max_validation_retries:
                    # 从服务器获取up.exe的期望哈希值
                    expected_hash = get_up_exe_hash_from_server()
                    if expected_hash is None:
                        message_queue.put({'type': 'log', 'text': f"获取服务器哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                        validation_attempts += 1
                        if validation_attempts >= max_validation_retries:
                            message_queue.put({'type': 'log', 'text': "无法获取服务器哈希值，验证失败"})
                            break
                        time.sleep(2)
                        continue
                    
                    # 计算下载文件的SHA-256哈希值
                    actual_hash = calculate_file_sha256("up.exe")
                    if actual_hash is None:
                        message_queue.put({'type': 'log', 'text': f"计算文件哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                        validation_attempts += 1
                        if validation_attempts >= max_validation_retries:
                            message_queue.put({'type': 'log', 'text': "无法计算文件哈希值，验证失败"})
                            break
                        time.sleep(2)
                        continue
                    
                    # 比较哈希值
                    if actual_hash.lower() == expected_hash.lower():
                        message_queue.put({'type': 'log', 'text': "up.exe文件完整性验证通过"})
                        validation_success = True
                        break
                    else:
                        message_queue.put({'type': 'log', 'text': f"up.exe文件验证失败，哈希值不匹配 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                        message_queue.put({'type': 'log', 'text': f"期望哈希值: {expected_hash}"})
                        message_queue.put({'type': 'log', 'text': f"实际哈希值: {actual_hash}"})
                        
                        # 删除不匹配的文件
                        try:
                            os.remove("up.exe")
                            message_queue.put({'type': 'log', 'text': "已删除验证失败的文件"})
                        except Exception as e:
                            message_queue.put({'type': 'log', 'text': f"删除验证失败的文件时出错: {str(e)}"})
                        
                        # 重新下载文件
                        download_successful = False
                        break
                
                if validation_success:
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
                else:
                    # 验证失败，需要重新下载文件
                    message_queue.put({'type': 'log', 'text': "文件验证失败，开始重新下载..."})
                    
                    # 重新下载文件
                    download_successful = False
                    for attempt in range(max_retries + 1):
                        try:
                            message_queue.put({'type': 'log', 'text': f"重新下载... (尝试 {attempt + 1}/{max_retries + 1})"})
                                
                            # 创建请求对象，添加User-Agent头部以避免某些服务器的访问限制
                            req = Request(download_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                                
                            # 首先获取文件大小
                            with urlopen(req, timeout=None) as response:
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
                                        
                            # 检查文件是否已成功下载
                            if len(file_content) > 0:
                                download_successful = True
                                break  # 成功下载，跳出循环
                            else:
                                raise Exception("下载的文件为空")
                        except Exception as e:
                            message_queue.put({'type': 'log', 'text': f"重新下载失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"})
                            if attempt >= max_retries:
                                # 所有重试都失败
                                message_queue.put({'type': 'log', 'text': "重新下载的所有重试都失败"})
                            else:
                                time.sleep(2)  # 等待2秒后重试
                    
                    # 重新下载完成后再次验证
                    if download_successful:
                        # 写入文件
                        with open("up.exe", "wb") as f:
                            f.write(file_content)
                                    
                        message_queue.put({'type': 'log', 'text': "重新下载的up.exe已保存，正在验证文件完整性..."})
                        
                        # 验证重新下载的文件
                        validation_success = False
                        validation_attempts = 0
                        
                        while validation_attempts < max_validation_retries:
                            # 从服务器获取up.exe的期望哈希值
                            expected_hash = get_up_exe_hash_from_server()
                            if expected_hash is None:
                                message_queue.put({'type': 'log', 'text': f"获取服务器哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                                validation_attempts += 1
                                if validation_attempts >= max_validation_retries:
                                    message_queue.put({'type': 'log', 'text': "无法获取服务器哈希值，验证失败"})
                                    break
                                time.sleep(2)
                                continue
                            
                            # 计算下载文件的SHA-256哈希值
                            actual_hash = calculate_file_sha256("up.exe")
                            if actual_hash is None:
                                message_queue.put({'type': 'log', 'text': f"计算文件哈希值失败 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                                validation_attempts += 1
                                if validation_attempts >= max_validation_retries:
                                    message_queue.put({'type': 'log', 'text': "无法计算文件哈希值，验证失败"})
                                    break
                                time.sleep(2)
                                continue
                            
                            # 比较哈希值
                            if actual_hash.lower() == expected_hash.lower():
                                message_queue.put({'type': 'log', 'text': "重新下载的up.exe文件完整性验证通过"})
                                validation_success = True
                                break
                            else:
                                message_queue.put({'type': 'log', 'text': f"重新下载的up.exe文件验证失败，哈希值不匹配 (尝试 {validation_attempts + 1}/{max_validation_retries})"})
                                message_queue.put({'type': 'log', 'text': f"期望哈希值: {expected_hash}"})
                                message_queue.put({'type': 'log', 'text': f"实际哈希值: {actual_hash}"})
                                
                                # 删除不匹配的文件
                                try:
                                    os.remove("up.exe")
                                    message_queue.put({'type': 'log', 'text': "已删除验证失败的文件"})
                                except Exception as e:
                                    message_queue.put({'type': 'log', 'text': f"删除验证失败的文件时出错: {str(e)}"})
                                
                                validation_attempts += 1
                                if validation_attempts >= max_validation_retries:
                                    message_queue.put({'type': 'log', 'text': "重新下载后验证仍失败，达到最大重试次数"})
                                    break
                                time.sleep(2)
                        
                        if validation_success:
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
                        else:
                            message_queue.put({'type': 'log', 'text': "重新下载后验证仍然失败，无法启动更新程序"})
                            # 发送失败消息
                            message_queue.put({'type': 'failed'})
                    else:
                        message_queue.put({'type': 'log', 'text': "重新下载失败，无法启动更新程序"})
                        # 发送失败消息
                        message_queue.put({'type': 'failed'})
                        
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
        cloud_version_url = f"https://{apis}/ggbb.txt"
        
        # 获取云端公告版本号
        req = Request(cloud_version_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
        with urlopen(req, timeout=None) as response:
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
            versions = list(range(local_version + 1, cloud_version + 1))
            
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            def fetch_announcement(version):
                try:
                    announcement_url = f"https://{apis}/gg{version}.txt"
                    req = Request(announcement_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urlopen(req, timeout=None) as response:
                        content = response.read().decode('utf-8').strip()
                        if content:
                            print(f"✓ 成功获取公告 {version}")
                            return {'version': version, 'content': content}
                        else:
                            print(f"⚠ 公告 {version} 内容为空")
                except Exception as e:
                    print(f"✗ 获取公告 {version} 失败: {e}")
                return None
                
            # 同时从服务器获取10条 (使用10个线程并发)
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_version = {executor.submit(fetch_announcement, v): v for v in versions}
                for future in as_completed(future_to_version):
                    res = future.result()
                    if res:
                        announcements.append(res)
                        
            # 按版本号从小到大排序
            announcements.sort(key=lambda x: x['version'])
            
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
    """显示公告窗口 - 优先使用PySide6"""
    if not announcements_info or not announcements_info['has_new_announcements']:
        return None
    
    announcements = announcements_info['announcements']
    
    # 尝试获取 PySide6 窗口
    pyside_win = None
    if parent_window and hasattr(parent_window, 'pyside_window') and parent_window.pyside_window:
        pyside_win = parent_window.pyside_window
    
    if pyside_win:
        return _show_pyside_announcements(announcements_info, announcements, pyside_win)
    
    # Tkinter 后备
    return _show_tkinter_announcements(announcements_info, announcements, parent_window)


def _show_pyside_announcements(announcements_info, announcements, pyside_win):
    """PySide6 现代化公告窗口"""
    try:
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
            QPushButton, QTabWidget, QWidget, QTextEdit, QSizePolicy)
        from PySide6.QtCore import Qt, QSize
        from PySide6.QtGui import QFont, QShortcut, QKeySequence
        
        dialog = QDialog(pyside_win)
        dialog.setWindowTitle(f"软件公告 ({len(announcements)}条新公告)")
        dialog.resize(700, 600)
        dialog.setMinimumSize(QSize(500, 400))
        dialog.setModal(False)
        
        dialog.setStyleSheet("""
            QDialog { background-color: #F5F7FA; }
            QLabel { color: #333333; }
            QTabWidget::pane { border: 1px solid #DDDDDD; border-radius: 4px; background: white; }
            QTabBar::tab { background: #E0E0E0; color: #555; padding: 8px 18px; margin-right: 2px;
                           border-top-left-radius: 6px; border-top-right-radius: 6px; font-size: 13px; }
            QTabBar::tab:selected { background: #1976D2; color: white; font-weight: bold; }
            QTabBar::tab:hover:!selected { background: #BDBDBD; }
            QTextEdit { background-color: #FAFAFA; border: none; font-size: 13px; color: #333; padding: 12px; }
            QPushButton { padding: 8px 20px; border-radius: 6px; font-size: 13px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 20, 25, 18)
        layout.setSpacing(12)
        
        # 标题
        header = QHBoxLayout()
        icon_lbl = QLabel("📢")
        icon_lbl.setStyleSheet("font-size: 28px;")
        header.addWidget(icon_lbl)
        title_lbl = QLabel(f"软件公告 ({len(announcements)}条新公告)")
        tf = QFont(); tf.setPointSize(16); tf.setBold(True)
        title_lbl.setFont(tf); title_lbl.setStyleSheet("color: #1976D2;")
        header.addWidget(title_lbl); header.addStretch()
        layout.addLayout(header)
        
        # 标签页
        tabs = QTabWidget()
        for idx, ann in enumerate(announcements):
            page = QWidget()
            pl = QVBoxLayout(page); pl.setContentsMargins(15, 12, 15, 12); pl.setSpacing(8)
            
            ver_lbl = QLabel(f"公告 #{ann['version']}")
            vf = QFont(); vf.setPointSize(13); vf.setBold(True)
            ver_lbl.setFont(vf); ver_lbl.setStyleSheet("color: #1976D2;")
            pl.addWidget(ver_lbl)
            
            te = QTextEdit()
            te.setPlainText(ann['content'])
            te.setReadOnly(True)
            te.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            pl.addWidget(te)
            
            tabs.addTab(page, f"公告{idx+1}")
        layout.addWidget(tabs)
        
        # 按钮
        btn_row = QHBoxLayout()
        
        prev_btn = QPushButton("← 上一条")
        prev_btn.setStyleSheet("QPushButton{background:#FFF;color:#666;border:1px solid #CCC;} QPushButton:hover{background:#F5F5F5;} QPushButton:disabled{color:#BBB;}")
        prev_btn.setEnabled(False)
        
        next_btn = QPushButton("下一条 →")
        next_btn.setStyleSheet("QPushButton{background:#FFF;color:#666;border:1px solid #CCC;} QPushButton:hover{background:#F5F5F5;} QPushButton:disabled{color:#BBB;}")
        next_btn.setEnabled(len(announcements) > 1)
        
        mark_btn = QPushButton("✓ 标记为已读并关闭")
        mark_btn.setStyleSheet("QPushButton{background:#43A047;color:white;border:none;} QPushButton:hover{background:#388E3C;}")
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton{background:#FFF;color:#666;border:1px solid #CCC;} QPushButton:hover{background:#F5F5F5;}")
        
        def update_nav():
            ci = tabs.currentIndex()
            prev_btn.setEnabled(ci > 0)
            next_btn.setEnabled(ci < len(announcements) - 1)
        
        def go_prev():
            ci = tabs.currentIndex()
            if ci > 0: tabs.setCurrentIndex(ci - 1)
        
        def go_next():
            ci = tabs.currentIndex()
            if ci < len(announcements) - 1: tabs.setCurrentIndex(ci + 1)
        
        def mark_read():
            try:
                with open("ggbb.txt", 'w', encoding='utf-8') as f:
                    f.write(str(announcements_info['cloud_version']))
                print(f"✓ 已更新本地公告版本号为: {announcements_info['cloud_version']}")
            except Exception as e:
                print(f"✗ 更新本地公告版本号失败: {e}")
            dialog.close()
        
        prev_btn.clicked.connect(go_prev)
        next_btn.clicked.connect(go_next)
        mark_btn.clicked.connect(mark_read)
        close_btn.clicked.connect(dialog.close)
        tabs.currentChanged.connect(lambda _: update_nav())
        
        # 初始调用一次以设置正确的按钮状态
        update_nav()
        
        # 快捷键
        QShortcut(QKeySequence(Qt.Key_Left), dialog, go_prev)
        QShortcut(QKeySequence(Qt.Key_Right), dialog, go_next)
        QShortcut(QKeySequence(Qt.Key_Escape), dialog, dialog.close)
        QShortcut(QKeySequence(Qt.Key_Return), dialog, mark_read)
        
        btn_row.addWidget(prev_btn); btn_row.addWidget(next_btn)
        btn_row.addStretch()
        btn_row.addWidget(mark_btn); btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)
        
        dialog.show()
        return dialog
        
    except Exception as e:
        print(f"PySide6公告窗口创建失败: {e}")
        return None


def _show_tkinter_announcements(announcements_info, announcements, parent_window):
    """Tkinter 后备公告窗口（独立于主窗口）"""
    # 创建独立的顶级窗口，不依赖于父窗口
    announcement_window = tk.Toplevel()
    announcement_window.attributes('-topmost', False)
    announcement_window.title(f"软件公告 ({len(announcements)}条新公告)")
    announcement_window.geometry("800x900")
    announcement_window.resizable(True, True)
    announcement_window.configure(bg=BW_COLORS["background"])
    
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
    
    icon_label = tk.Label(header_frame, text="📢", font=("Segoe UI", 24),
        bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"])
    icon_label.pack(side=tk.LEFT)
    
    title_label = tk.Label(header_frame, text=f"软件公告 ({len(announcements)}条新公告)",
        font=BW_FONTS["title"], bg=BW_COLORS["card_bg"], fg=BW_COLORS["dark"])
    title_label.pack(side=tk.LEFT, padx=10)
    
    notebook = ttk.Notebook(main_container)
    notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
    
    style = ttk.Style()
    style.configure("BW.TNotebook", background=BW_COLORS["card_bg"])
    style.configure("BW.TNotebook.Tab", background=BW_COLORS["secondary"],
                   foreground="white", padding=[10, 5])
    style.map("BW.TNotebook.Tab", background=[("selected", BW_COLORS["primary"])],
             foreground=[("selected", "white")])
    
    for idx, ann in enumerate(announcements):
        frame = create_bw_frame(notebook)
        title_frame = tk.Frame(frame, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(title_frame, text=f"公告 #{ann['version']}", font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"]).pack(anchor="w")
        tk.Label(title_frame, text=f"--- : {datetime.now().strftime('-')}",
            font=BW_FONTS["small"], bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]).pack(anchor="w", pady=(2, 0))
        
        content_frame = create_bw_frame(frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        text_widget = scrolledtext.ScrolledText(content_frame, width=70, height=20,
            font=BW_FONTS["normal"], wrap=tk.WORD, bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"], relief="flat", bd=0, padx=15, pady=15)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert(tk.END, ann['content'])
        text_widget.config(state=tk.DISABLED)
        notebook.add(frame, text=f"公告{idx+1}")
    
    button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
    button_frame.pack(fill=tk.X, padx=20, pady=10)
    
    def mark_as_read_and_close():
        try:
            with open("ggbb.txt", 'w', encoding='utf-8') as f:
                f.write(str(announcements_info['cloud_version']))
            print(f"✓ 已更新本地公告版本号为: {announcements_info['cloud_version']}")
        except Exception as e:
            print(f"✗ 更新本地公告版本号失败: {e}")
        announcement_window.destroy()
    
    def close_without_mark():
        announcement_window.destroy()
    
    left_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    left_btn_frame.pack(side=tk.LEFT)
    current_tab = [0]
    
    def show_next():
        if current_tab[0] < len(announcements) - 1:
            current_tab[0] += 1; notebook.select(current_tab[0]); upd()
    def show_prev():
        if current_tab[0] > 0:
            current_tab[0] -= 1; notebook.select(current_tab[0]); upd()
    def upd():
        prev_btn.config(state='normal' if current_tab[0] > 0 else 'disabled')
        next_btn.config(state='normal' if current_tab[0] < len(announcements) - 1 else 'disabled')
    
    prev_btn = create_bw_button(left_btn_frame, "← 上一条", show_prev, "secondary", width=10)
    prev_btn.pack(side=tk.LEFT, padx=5); prev_btn.config(state='disabled')
    next_btn = create_bw_button(left_btn_frame, "下一条 →", show_next, "secondary", width=10)
    next_btn.pack(side=tk.LEFT, padx=5)
    if len(announcements) <= 1: next_btn.config(state='disabled')
    
    right_btn_frame = tk.Frame(button_frame, bg=BW_COLORS["card_bg"])
    right_btn_frame.pack(side=tk.RIGHT)
    create_bw_button(right_btn_frame, "关闭", close_without_mark, "secondary", width=10).pack(side=tk.RIGHT, padx=5)
    create_bw_button(right_btn_frame, "✓ 标记为已读并关闭", mark_as_read_and_close, "success", width=18).pack(side=tk.RIGHT, padx=5)
    
    notebook.bind("<<NotebookTabChanged>>", lambda e: (current_tab.__setitem__(0, notebook.index(notebook.select())), upd()))
    announcement_window.bind('<Right>', lambda e: show_next())
    announcement_window.bind('<Left>', lambda e: show_prev())
    announcement_window.bind('<Escape>', lambda e: close_without_mark())
    announcement_window.bind('<Return>', lambda e: mark_as_read_and_close())
    
    announcement_window.update_idletasks()
    x = (announcement_window.winfo_screenwidth() - announcement_window.winfo_width()) // 2
    y = (announcement_window.winfo_screenheight() - announcement_window.winfo_height()) // 2
    announcement_window.geometry(f"+{x}+{y}")
    
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
    if PYSIDE6_AVAILABLE:
        disclaimer_window.withdraw()

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
（5）用户应自行承担使用本软件的所有风险

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
    
    if PYSIDE6_AVAILABLE:
        disclaimer_data = (disclaimer_window, agree_var, always_agree_var, agree_and_continue, disagree_and_exit, disclaimer_text)
        global pyside_thread_started
        pyside_thread_started = True
        threading.Thread(target=run_pyside_app, kwargs={'disclaimer_data': disclaimer_data}, daemon=True).start()

        
    disclaimer_window.update_idletasks()
    x = (disclaimer_window.winfo_screenwidth() - disclaimer_window.winfo_width()) // 2
    y = (disclaimer_window.winfo_screenheight() - disclaimer_window.winfo_height()) // 2
    disclaimer_window.geometry(f"+{x}+{y}")
    
    disclaimer_window.mainloop()

    return agree_var.get()

# ==============================================
# 独立联机大厅窗口类
# ==============================================

class LobbyWindow:
    """独立的联机大厅窗口"""
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.window = None
        
    def open(self):
        """打开联机大厅窗口"""
        if self.window and self.window.winfo_exists():
            # 如果窗口已存在，则将其置于最前
            self.window.lift()
            self.window.focus_force()
            return
        
        # 创建新窗口（独立于主窗口）
        self.window = tk.Toplevel()
        self.window.title("联机大厅 - LMFP")
        self.window.geometry("900x700")
        self.window.configure(bg=BW_COLORS["background"])
        
        # 设置窗口图标（如果有的话）
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        # 创建联机大厅内容
        lobby_frame = create_bw_frame(self.window)
        lobby_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 调用主应用的创建方法，但传入lobby_frame作为parent
        self._create_lobby_content(lobby_frame)
        
        # 绑定窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
        # 将窗口置于最前
        self.window.lift()
        self.window.focus_force()
        
        # 自动刷新一次房间列表
        self.parent_app.root.after(100, lambda: self.parent_app.refresh_rooms())
    
    def _create_lobby_content(self, parent):
        """创建联机大厅内容"""
        # 大厅标题
        lobby_title_frame = tk.Frame(parent, bg=BW_COLORS["card_bg"])
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
        
        self.refresh_btn = create_bw_button(lobby_btn_frame, "⟳ 刷新", 
                                        lambda: self.parent_app.refresh_rooms(), "primary", width=8)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.join_btn = create_bw_button(lobby_btn_frame, "加入选中的房间", 
                                     self.parent_app.join_selected_room, "success", width=12)
        self.join_btn.pack(side=tk.LEFT, padx=2)
        
        # 状态提示
        tip_frame = tk.Frame(parent, bg=BW_COLORS["card_bg"])
        tip_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tip_text = "提示: Lyt_IT 一般情况不会进入你们的房间 请仔细甄别 以防上当受骗"
        tip_color = BW_COLORS["text_secondary"]
        
        tk.Label(tip_frame, text=tip_text, font=BW_FONTS["small"], 
                fg=tip_color, wraplength=400, justify=tk.CENTER, bg=BW_COLORS["card_bg"]).pack()
        
        # 房间列表区域
        list_frame = create_bw_frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 创建Treeview用于显示房间列表
        columns = ("房间号", "房间人数", "房主", "版本", "识别版本", "房间标题", "描述", "节点延迟", "状态", "操作")
        self.room_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列宽
        self.room_tree.column("房间号", width=80, anchor=tk.W)
        self.room_tree.column("房间人数", width=80, anchor=tk.W)
        self.room_tree.column("房主", width=80, anchor=tk.W)
        self.room_tree.column("版本", width=90, anchor=tk.W)
        self.room_tree.column("识别版本", width=90, anchor=tk.W)
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
        detail_frame = create_bw_frame(parent)
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
        status_bar_frame = tk.Frame(parent, bg=BW_COLORS["card_bg"])
        status_bar_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        self.lobby_status = tk.Label(status_bar_frame, text="等待云端许可验证...", font=BW_FONTS["small"],
                                   bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.lobby_status.pack(side=tk.LEFT)
        
        self.last_update_label = tk.Label(status_bar_frame, text="", font=BW_FONTS["small"],
                                        bg=BW_COLORS["card_bg"], fg=BW_COLORS["text_secondary"])
        self.last_update_label.pack(side=tk.RIGHT)
        
        # 绑定事件 - 使用主应用的方法
        self.room_tree.bind("<ButtonRelease-1>", lambda e: self.parent_app.on_room_click(e, self.room_tree, self.room_detail_text))
        self.room_tree.bind("<Double-Button-1>", lambda e: self.parent_app.on_room_double_click(e, self.room_tree))
        
        # 保存引用到主应用，以便更新UI
        self.parent_app.lobby_window_room_tree = self.room_tree
        self.parent_app.lobby_window_detail_text = self.room_detail_text
        self.parent_app.lobby_window_status = self.lobby_status
        self.parent_app.lobby_window_last_update = self.last_update_label
        self.parent_app.lobby_window_refresh_btn = self.refresh_btn
        self.parent_app.lobby_window_join_btn = self.join_btn
    
    def close(self):
        """关闭联机大厅窗口"""
        # 清除主应用中的引用
        if hasattr(self.parent_app, 'lobby_window_room_tree'):
            self.parent_app.lobby_window_room_tree = None
        if hasattr(self.parent_app, 'lobby_window_detail_text'):
            self.parent_app.lobby_window_detail_text = None
        if hasattr(self.parent_app, 'lobby_window_status'):
            self.parent_app.lobby_window_status = None
        if hasattr(self.parent_app, 'lobby_window_last_update'):
            self.parent_app.lobby_window_last_update = None
        if hasattr(self.parent_app, 'lobby_window_refresh_btn'):
            self.parent_app.lobby_window_refresh_btn = None
        if hasattr(self.parent_app, 'lobby_window_join_btn'):
            self.parent_app.lobby_window_join_btn = None
        
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """检查窗口是否打开"""
        return self.window is not None and self.window.winfo_exists()


# ==============================================
# 独立聊天室窗口类
# ==============================================

class ChatRoomWindow:
    """独立的聊天室窗口"""
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.window = None
        self.chat_module = None
        
    def open(self):
        """打开聊天室窗口"""
        if self.window and self.window.winfo_exists():
            # 如果窗口已存在，则将其置于最前
            self.window.lift()
            self.window.focus_force()
            return
        
        # 创建新窗口（独立于主窗口）
        self.window = tk.Toplevel()
        self.window.title("公共聊天室 - LMFP")
        self.window.geometry("450x700")
        self.window.configure(bg=BW_COLORS["background"])
        
        # 设置窗口图标（如果有的话）
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                self.window.iconbitmap(icon_path)
        except:
            pass
        
        # 创建聊天室模块
        chat_frame = create_bw_frame(self.window)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_module = ChatRoomModule(chat_frame, self.parent_app)
        
        # 绑定窗口关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
        # 将窗口置于最前
        self.window.lift()
        self.window.focus_force()
    
    def close(self):
        """关闭聊天室窗口"""
        if self.chat_module:
            # 停止聊天室相关线程
            self.chat_module.stop_chat_connection()
            self.chat_module = None
        
        if self.window and self.window.winfo_exists():
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """检查窗口是否打开"""
        return self.window is not None and self.window.winfo_exists()


# ==============================================
# 公共聊天室模块
# ==============================================

class ChatRoomModule:
    def __init__(self, parent_frame, main_app=None):
        self.parent = parent_frame
        self.main_app = main_app
        self.root = parent_frame.winfo_toplevel() if parent_frame else None
        
        # API 配置
        self.api_base = f"https://{apis}/public_chat/api"
        self.user_token = None
        self.current_user = None
        
        # 聊天相关
        self.chat_active = False
        self.last_message_id = 0
        self.displayed_message_hashes = set()
        self.pending_messages = []
        self.history_loaded = False
        
        # @消息提醒防抖相关
        self.last_notification_time = 0  # 上次推送通知的时间戳
        self.notification_cooldown = 3   # 冷却时间（秒）
        
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
            text="在线用户（红色标识Lyt_IT_Studio官方）",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        online_title.pack(anchor="w", padx=10, pady=5)
        
        # 使用Frame和Labels替代Listbox以支持彩色文本显示
        self.online_frame = tk.Frame(
            online_frame,
            bg=BW_COLORS["light"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"],
            highlightthickness=1
        )
        self.online_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        
        # 创建滚动文本区域来显示在线用户（固定值）
        scaled_online_height = 10
        scaled_online_padx = 2
        scaled_online_pady = 2
        
        self.online_text = tk.Text(
            self.online_frame,
            height=scaled_online_height,
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            font=BW_FONTS["small"],
            relief="flat",
            bd=0,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.online_text.pack(fill=tk.BOTH, expand=True, padx=scaled_online_padx, pady=scaled_online_pady)
        
        # 绑定双击事件，将选中的用户名填入消息输入框
        self.online_text.bind("<Double-Button-1>", self.insert_username_to_message_box)
        
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
        
        scaled_chat_height = 15
        scaled_chat_padx = 8
        scaled_chat_pady = 8
        scaled_outer_padx = 5
        scaled_outer_pady = 5
        
        self.chat_text = scrolledtext.ScrolledText(
            chat_frame,
            height=scaled_chat_height,
            wrap=tk.WORD,
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=0,
            padx=scaled_chat_padx,
            pady=scaled_chat_pady
        )
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=scaled_outer_padx, pady=scaled_outer_pady)
        self.chat_text.config(state=tk.DISABLED)
        
        # 历史记录加载状态标签
        scaled_history_pady = 2
        
        self.history_status_label = tk.Label(
            chat_frame,
            text="",
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["warning"]
        )
        self.history_status_label.pack(pady=scaled_history_pady)
        
        # 消息输入区域
        input_frame = tk.Frame(self.parent, bg=BW_COLORS["background"])
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建输入框容器
        entry_container = tk.Frame(input_frame, bg=BW_COLORS["background"])
        entry_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.message_entry = tk.Entry(
            entry_container,
            font=BW_FONTS["small"],
            bg=BW_COLORS["light"],
            fg=BW_COLORS["text_primary"],
            relief="flat",
            bd=1,
            highlightbackground=BW_COLORS["border"],
            highlightthickness=1
        )
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        self.message_entry.bind("<KeyRelease>", self.update_char_count)
        self.message_entry.bind("<KeyPress>", self.validate_input_length)
        self.message_entry.bind("<Button-3>", self.handle_right_click_paste, add="+")
        self.message_entry.config(state='disabled')
        
        # 字符计数标签
        self.char_count_label = tk.Label(
            entry_container,
            text="0/500",
            font=BW_FONTS["small"],
            bg=BW_COLORS["background"],
            fg=BW_COLORS["text_secondary"]
        )
        self.char_count_label.pack(side=tk.RIGHT, padx=(5, 0))
        
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


    def is_duplicate_log(self, message):
        """检查是否为重复日志（使用主应用的过滤逻辑）"""
        if self.main_app and hasattr(self.main_app, 'is_duplicate_log'):
            return self.main_app.is_duplicate_log(message)
        return False
    
    def clean_log_message(self, message):
        """清理日志消息，提取核心内容用于比较（使用主应用的清理逻辑）"""
        if self.main_app and hasattr(self.main_app, 'clean_log_message'):
            return self.main_app.clean_log_message(message)
        # 如果无法调用主应用的方法，使用基本清理
        import re
        clean_msg = re.sub(r'\[\d{2}:\d{2}:\d{2}\]\s*', '', message)
        clean_msg = re.sub(r'#\d+', '', clean_msg)
        clean_msg = re.sub(r'\(\d+秒\)', '', clean_msg)
        clean_msg = re.sub(r'[✗✓■→]', '', clean_msg)
        clean_msg = re.sub(r'\s+', ' ', clean_msg).strip()
        return clean_msg
    
    def add_to_log_history(self, message):
        """将日志添加到历史记录中（使用主应用的历史记录）"""
        if self.main_app and hasattr(self.main_app, 'add_to_log_history'):
            self.main_app.add_to_log_history(message)
    
    def log(self, message, is_error=False):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if is_error:
            formatted_message = f"[{timestamp}] ✗ {message}"
        else:
            formatted_message = f"[{timestamp}] {message}"
        
        # 检查是否为重复日志
        if self.is_duplicate_log(formatted_message):
            return  # 如果是重复日志则不显示
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 将消息添加到历史记录
        self.add_to_log_history(formatted_message)
    
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
                
                # 先显示所有历史消息（暂不处理@高亮）
                displayed_messages = []
                for msg in messages:
                    msg_hash = self.get_message_hash(msg)
                    if msg_hash in self.displayed_message_hashes:
                        continue
                    
                    # 显示消息但暂时不处理@高亮
                    self._display_message_without_highlight(msg, is_history_message=True)
                    displayed_messages.append((msg, msg_hash))
                    self.displayed_message_hashes.add(msg_hash)
                    
                    if msg['id'] > self.last_message_id:
                        self.last_message_id = msg['id']
                
                self.history_loaded = True
                self.history_status_label.config(text=f"已加载 {len(messages)} 条历史记录", fg=BW_COLORS["success"])
                self.log(f"✓ 历史记录加载完成，共 {len(messages)} 条消息")
                self.unlock_message_input()
                
                # 历史记录加载完成后，统一处理所有@用户名高亮
                self.root.after(500, lambda: self._reprocess_history_mentions(displayed_messages))
                
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
        """显示登录窗口（独立于主窗口）"""
        login_window = tk.Toplevel()
        login_window.title("登录账号")
        login_window.geometry("400x280")
        login_window.resizable(False, False)
        login_window.configure(bg=BW_COLORS["background"])
        # 移除 transient 和 grab_set，使窗口可以独立于主窗口存在
        
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
        verify_window.geometry("400x380")
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
        
        resend_btn = create_bw_button(btn_frame, "重发", resend_code, "secondary", width=10)
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
            self.last_notification_time = 0  # 重置@提醒时间
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
        # 清空在线用户显示区域
        self.online_text.config(state=tk.NORMAL)
        self.online_text.delete(1.0, tk.END)
        
        for i, user in enumerate(self.online_users):
            if user['username'] == self.current_user:
                display_name = f"{user['username']} (我)\n"
            else:
                display_name = f"{user['username']}\n"
            
            # 如果是Lyt_IT用户，使用红色显示
            if user['username'] == 'Lyt_IT':
                self.online_text.insert(tk.END, display_name, "lyt_it")
                self.online_text.tag_config("lyt_it", foreground="red")
            else:
                self.online_text.insert(tk.END, display_name)
        
        self.online_text.config(state=tk.DISABLED)
        self.online_text.see(tk.END)
    
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
        
        # 获取消息并进行安全检查
        try:
            message = self.message_entry.get().strip()
            # 去除消息中的换行符
            message = message.replace('\n', '').replace('\r', '')
            
            # 双重检查消息长度
            if len(message) > 500:
                # 强制截断并更新显示
                truncated_message = message[:500]
                self.message_entry.delete(0, tk.END)
                self.message_entry.insert(0, truncated_message)
                message = truncated_message
                messagebox.showwarning("提示", "消息已自动截断到500字符限制", parent=self.root)
        except Exception as e:
            messagebox.showerror("错误", f"消息处理出错: {str(e)}", parent=self.root)
            return
        
        if not message:
            return
        
        local_timestamp = int(time.time())
        #self.display_local_message(message, local_timestamp)
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
    
    def truncate_to_limit(self, text, limit):
        """将文本截断到指定字符限制，保持完整性"""
        # 先去除换行符计算实际长度
        clean_text = text.replace('\n', '').replace('\r', '')
        
        if len(clean_text) <= limit:
            return text
        
        # 逐字符构建，直到达到限制
        result = ""
        clean_length = 0
        
        for char in text:
            if char in ['\n', '\r']:
                result += char
            else:
                if clean_length < limit:
                    result += char
                    clean_length += 1
                else:
                    break
        
        return result
    
    def validate_input_length(self, event):
        """验证输入长度，阻止超过限制的输入"""
        try:
            # 获取当前文本长度
            current_text = self.message_entry.get()
            clean_current_length = len(current_text.replace('\n', '').replace('\r', ''))
            
            # 特殊键不需要限制
            if event.keysym in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Home', 'End']:
                return
            
            # 控制键处理
            if event.state & 0x4:  # Control键
                if event.keysym.lower() == 'v':  # Ctrl+V 粘贴
                    # 使用线程处理粘贴，避免阻塞UI
                    import threading
                    paste_thread = threading.Thread(target=self._safe_paste_handler, daemon=True)
                    paste_thread.start()
                return
            
            # 如果当前已经是500字符，阻止继续输入
            if clean_current_length >= 500:
                return "break"  # 阻止该按键事件
                
        except Exception as e:
            print(f"输入验证出错: {e}")
            return "break"  # 出错时保守处理
    
    def _safe_paste_handler(self):
        """安全的粘贴处理（在线程中运行）"""
        try:
            import time
            # 给系统一些时间完成粘贴操作
            time.sleep(0.05)
            
            # 在主线程中安全地处理粘贴内容
            self.root.after(0, self._process_pasted_content)
            
        except Exception as e:
            print(f"粘贴处理线程出错: {e}")
    
    def _process_pasted_content(self):
        """在主线程中处理粘贴的内容"""
        try:
            current_text = self.message_entry.get()
            clean_length = len(current_text.replace('\n', '').replace('\r', ''))
            
            # 如果内容过长，进行截断
            if clean_length > 500:
                # 计算需要保留的字符数（考虑换行符）
                chars_to_keep = self._calculate_chars_to_keep(current_text, 500)
                truncated_text = current_text[:chars_to_keep]
                
                # 安全更新界面
                self.message_entry.delete(0, tk.END)
                self.message_entry.insert(0, truncated_text)
                
                # 显示提示（延迟显示避免冲突）
                self.root.after(100, self._show_paste_warning)
            
            # 更新字符计数
            self.update_char_count()
            
        except Exception as e:
            print(f"处理粘贴内容出错: {e}")
            # 出错时清空输入框
            try:
                self.message_entry.delete(0, tk.END)
                self.update_char_count()
            except:
                pass
    
    def _calculate_chars_to_keep(self, text, limit):
        """计算需要保留的字符位置"""
        clean_count = 0
        for i, char in enumerate(text):
            if char not in ['\n', '\r']:
                clean_count += 1
                if clean_count > limit:
                    return i
        return len(text)
    
    def _show_paste_warning(self):
        """显示粘贴警告信息"""
        try:
            messagebox.showwarning(
                "提示", 
                "粘贴的内容过长，已自动截断到500字符限制", 
                parent=self.root
            )
        except:
            pass
    
    def handle_paste_validation(self):
        """处理粘贴内容的验证和截断"""
        try:
            current_text = self.message_entry.get()
            clean_length = len(current_text.replace('\n', '').replace('\r', ''))
            
            # 如果已经超过限制，立即截断
            if clean_length > 500:
                truncated_text = self.truncate_to_limit(current_text, 500)
                self.message_entry.delete(0, tk.END)
                self.message_entry.insert(0, truncated_text)
                
                # 显示警告信息
                self.root.after(100, lambda: messagebox.showwarning(
                    "提示", 
                    "粘贴的内容过长，已自动截断到500字符限制", 
                    parent=self.root
                ))
                
            # 更新字符计数显示
            self.update_char_count()
            
        except Exception as e:
            # 防止粘贴处理过程中出现异常导致程序崩溃
            print(f"粘贴处理出错: {e}")
            try:
                # 出错时清空输入框
                self.message_entry.delete(0, tk.END)
                self.update_char_count()
            except:
                pass
    
    def handle_right_click_paste(self, event):
        """处理右键粘贴操作"""
        # 使用安全的粘贴处理
        import threading
        paste_thread = threading.Thread(target=self._safe_paste_handler, daemon=True)
        paste_thread.start()
    
    def update_char_count(self, event=None):
        """更新字符计数显示并限制输入长度"""
        message = self.message_entry.get()
        # 去除换行符后的实际长度
        clean_message = message.replace('\n', '').replace('\r', '')
        current_length = len(clean_message)
        
        # 如果超过限制，截断输入
        if current_length > 500:
            # 截取前500个字符（考虑换行符的情况）
            truncated_message = self.truncate_to_limit(message, 500)
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, truncated_message)
            current_length = 500
        
        # 更新字符计数显示
        self.char_count_label.config(text=f"{current_length}/500")
        
        # 根据字符数量改变颜色
        if current_length >= 500:
            self.char_count_label.config(fg="red")
        elif current_length > 450:  # 接近限制时显示警告色
            self.char_count_label.config(fg="orange")
        else:
            self.char_count_label.config(fg=BW_COLORS["text_secondary"])
    
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
                        
                        self.display_message(msg, is_history_message=False)
                        self.displayed_message_hashes.add(msg_hash)
                        
                        if msg['id'] > self.last_message_id:
                            self.last_message_id = msg['id']
            
            self.run_in_thread(get_messages_task, on_messages_complete)
        
        if hasattr(self, 'root') and self.root:
            self.root.after(2000, self.auto_refresh_messages)
    
    def display_message(self, message, is_history_message=False):
        """显示消息（用于实时消息）
        
        Args:
            message: 消息字典
            is_history_message: 是否为历史消息，如果是，则不触发@提醒
        """
        timestamp = message.get("timestamp", time.time())
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        sender = message.get("sender", "未知用户")
        content = message.get("content", "")
        
        if sender == self.current_user:
            formatted_message = f"[{time_str}] <我>: {content}"
            tag = "self"
        else:
            formatted_message = f"[{time_str}] {sender}: {content}"
            # 如果发送者是Lyt_IT，则使用特殊标签
            if sender == "Lyt_IT":
                tag = "lyt_it"
            else:
                tag = "other"
            
            # 检测消息中是否包含当前用户的ID/用户名
            # 仅对非历史消息触发@提醒
            if not is_history_message and self.current_user and self.current_user.lower() in content.lower():
                current_time = time.time()
                # 检查是否在冷却期内
                if current_time - self.last_notification_time >= self.notification_cooldown:
                    # 发送系统通知提醒用户
                    notification_title = f"@{self.current_user} 提醒"
                    notification_msg = f"{sender} 在聊天中提到了你: {content[:50]}..."  # 限制消息长度
                    self.send_notification(notification_title, notification_msg)
                    # 更新上次通知时间
                    self.last_notification_time = current_time
        
        self.chat_text.config(state=tk.NORMAL)
        
        # 先插入消息文本
        self.chat_text.insert(tk.END, formatted_message + "\n", tag)
        
        # 立即处理@用户名高亮显示（在消息插入后立即应用）
        # 使用与simple_test.py相同的方式
        self._simple_highlight_mentions(formatted_message)
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 配置Lyt_IT消息的红色样式
        if tag == "lyt_it":
            self.chat_text.tag_config("lyt_it", foreground="red")
    
    def _display_message_without_highlight(self, message, is_history_message=False):
        """显示消息但不立即处理@高亮（用于历史记录加载）"""
        timestamp = message.get("timestamp", time.time())
        time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
        sender = message.get("sender", "未知用户")
        content = message.get("content", "")
        
        if sender == self.current_user:
            formatted_message = f"[{time_str}] <我>: {content}"
            tag = "self"
        else:
            formatted_message = f"[{time_str}] {sender}: {content}"
            if sender == "Lyt_IT":
                tag = "lyt_it"
            else:
                tag = "other"
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, formatted_message + "\n", tag)
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
        
        # 配置基本样式
        if tag == "lyt_it":
            self.chat_text.tag_config("lyt_it", foreground="red")
        else:
            self.chat_text.tag_config("self", foreground=BW_COLORS["primary"])
            self.chat_text.tag_config("other", foreground=BW_COLORS["text_primary"])
    
    def _reprocess_history_mentions(self, displayed_messages):
        """重新处理历史消息中的@用户名高亮"""
        print(f"开始重新处理 {len(displayed_messages)} 条历史消息的@高亮...")
        
        try:
            # 获取总行数
            total_lines = int(float(self.chat_text.index(tk.END))) - 1
            processed_count = 0
            
            # 遍历每一行，寻找包含@的消息
            for line_num in range(1, total_lines + 1):
                line_content = self.chat_text.get(f"{line_num}.0", f"{line_num}.end")
                
                # 跳过系统状态消息和空行
                if not line_content or "历史记录加载完成" in line_content or line_content.startswith("✓"):
                    continue
                
                # 检查是否包含@用户名
                if "@" in line_content:
                    print(f"处理历史消息行 {line_num}: {line_content}")
                    self._process_line_history_mentions(line_num, line_content)
                    processed_count += 1
            
            print(f"历史消息@高亮处理完成，共处理 {processed_count} 行")
            
        except Exception as e:
            print(f"重新处理历史@高亮时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_line_history_mentions(self, line_num, line_content):
        """处理历史消息单行中的@用户名高亮"""
        import re
        
        # 查找所有@用户名
        pattern = r'@([\w\u4e00-\u9fff]+)'
        matches = list(re.finditer(pattern, line_content))
        
        if not matches:
            return
        
        print(f"  找到 {len(matches)} 个@用户名匹配")
        
        # 临时启用文本编辑
        was_disabled = (self.chat_text.cget('state') == 'disabled')
        if was_disabled:
            self.chat_text.config(state=tk.NORMAL)
        
        try:
            # 为每个@用户名应用蓝色样式
            for match in matches:
                username = match.group(1)
                start_pos = match.start()
                end_pos = match.end()
                
                tag_name = f"history_mention_{username}_{line_num}_{int(time.time()*1000)}"
                
                # 添加标签
                self.chat_text.tag_add(tag_name, f"{line_num}.{start_pos}", f"{line_num}.{end_pos}")
                
                # 配置样式（仅蓝色，不加粗）
                self.chat_text.tag_config(tag_name, 
                                        foreground="blue", 
                                        font=("TkDefaultFont", 10))
                
                print(f"  ✅ 已高亮 @{username} (位置 {start_pos}-{end_pos})")
                
        finally:
            # 恢复状态
            if was_disabled:
                self.chat_text.config(state=tk.DISABLED)
    
    def _simple_highlight_mentions(self, message_text):
        """简单直接的@用户名高亮方法（仅变色不加粗）"""
        import re
        
        # 查找所有@用户名
        pattern = r'@([\w\u4e00-\u9fff]+)'
        matches = list(re.finditer(pattern, message_text))
        
        # 调试信息
        print(f"消息文本: {message_text}")
        print(f"找到 {len(matches)} 个@用户名匹配")
        
        if not matches:
            print("没有找到@用户名")
            return
        
        try:
            # 临时启用文本编辑以便应用标签
            was_disabled = (self.chat_text.cget('state') == 'disabled')
            if was_disabled:
                self.chat_text.config(state=tk.NORMAL)
            
            # 获取最后一行行号（消息刚插入的位置）
            current_line = int(float(self.chat_text.index(tk.END))) - 2
            
            # 验证这一行是否包含我们的消息
            line_content = self.chat_text.get(f"{current_line}.0", f"{current_line}.end")
            
            # 如果不匹配，可能是历史记录干扰，尝试不同的定位策略
            if message_text not in line_content:
                print(f"第一定位失败，尝试备用方案...")
                print(f"期望内容: {message_text}")
                print(f"实际内容: {line_content}")
                
                # 备用方案：从后往前搜索包含消息内容的行
                total_lines = int(float(self.chat_text.index(tk.END))) - 1
                found_line = None
                
                # 搜索最近的几行
                for line_num in range(max(1, total_lines - 10), total_lines + 1):
                    content = self.chat_text.get(f"{line_num}.0", f"{line_num}.end")
                    if message_text in content and "历史记录加载完成" not in content:
                        found_line = line_num
                        print(f"在行 {line_num} 找到匹配: {content}")
                        break
                
                if found_line is None:
                    print(f"❌ 无法找到包含消息的行")
                    if was_disabled:
                        self.chat_text.config(state=tk.DISABLED)
                    return
                else:
                    current_line = found_line
                    line_content = self.chat_text.get(f"{current_line}.0", f"{current_line}.end")
            
            print(f"✅ 定位到行号: {current_line}")
            print(f"行内容: {line_content}")
            
            # 为每个@用户名应用蓝色样式
            for match in matches:
                username = match.group(1)
                start_pos = match.start()
                end_pos = match.end()
                
                print(f"处理@{username}: 位置 {start_pos}-{end_pos}")
                
                # 创建标签名
                tag_name = f"mention_{username}_{int(time.time()*1000)}"
                
                # 添加标签
                self.chat_text.tag_add(tag_name, f"{current_line}.{start_pos}", f"{current_line}.{end_pos}")
                
                # 配置标签样式（仅蓝色，不加粗）
                # 使用系统默认字体
                self.chat_text.tag_config(tag_name, 
                                        foreground="blue", 
                                        font=("TkDefaultFont", 10))
                
                # 验证标签是否正确应用
                tag_ranges = self.chat_text.tag_ranges(tag_name)
                print(f"标签 {tag_name} 应用到范围: {tag_ranges}")
                
                print(f"✅ 已应用蓝色样式到@{username}")
                
            # 恢复原来的禁用状态
            if was_disabled:
                self.chat_text.config(state=tk.DISABLED)
                
        except Exception as e:
            print(f"@用户名高亮处理出错: {e}")
            import traceback
            traceback.print_exc()
            # 确保状态恢复
            try:
                if was_disabled:
                    self.chat_text.config(state=tk.DISABLED)
            except:
                pass
            pass
    
    def _highlight_mentions(self, content_text, base_tag):
        """高亮显示@用户名（加粗显示，支持空格分割）"""
        import re
        
        # 查找所有@用户名模式（支持多个@用户名，用空格分隔）
        # 匹配 @用户名 或 @用户名1 @用户名2 等格式
        mention_pattern = r'(@[\w\u4e00-\u9fff]+(?:\s+@[\w\u4e00-\u9fff]+)*)'
        matches = list(re.finditer(mention_pattern, content_text))
        
        if not matches:
            return
        
        try:
            # 获取当前最后一行的起始位置
            last_line_start = self.chat_text.index(f"{float(self.chat_text.index(tk.END)) - 1}.0")
            
            # 计算时间戳和发送者部分的长度
            # 格式: [HH:MM:SS] 发送者: 
            time_sender_prefix_length = len("[HH:MM:SS] 发送者: ")
            
            # 处理每个匹配的@用户名组合
            for match in matches:
                full_match = match.group(1)  # 完整的@用户名字符串
                start_pos = match.start(1)
                end_pos = match.end(1)
                
                # 计算在文本中的绝对位置（需要加上前缀长度）
                abs_start = f"{last_line_start}+{time_sender_prefix_length + start_pos}c"
                abs_end = f"{last_line_start}+{time_sender_prefix_length + end_pos}c"
                
                # 创建唯一的加粗标签
                bold_tag = f"bold_mention_{hash(full_match)}_{int(time.time()*1000)}"
                
                # 应用加粗样式
                self.chat_text.tag_add(bold_tag, abs_start, abs_end)
                self.chat_text.tag_config(bold_tag, font=BW_FONTS["bold_small"])
                
                # 为每个单独的@用户名添加蓝色高亮
                self._highlight_individual_mentions(full_match, abs_start, time_sender_prefix_length)
        except Exception as e:
            # 如果高亮处理出现异常，不影响消息正常显示
            print(f"处理@用户名高亮时出错: {e}")
            pass
    
    def _highlight_individual_mentions_simple(self, full_mention_text, base_position):
        """为单个@用户名添加特殊颜色（蓝色）和加粗效果 - 简化版本"""
        import re
        
        # 分离出每个单独的@用户名
        individual_pattern = r'@([\w\u4e00-\u9fff]+)'
        individual_matches = list(re.finditer(individual_pattern, full_mention_text))
        
        if not individual_matches:
            return
        
        try:
            # 解析基础位置
            line_number = base_position.split('.')[0]
            base_char_offset = int(base_position.split('.')[1])
            
            # 为每个@用户名添加蓝色和加粗效果
            for match in individual_matches:
                username = match.group(1)
                start_pos = base_char_offset + match.start()
                end_pos = base_char_offset + match.end()
                
                # 使用简单直接的位置指定
                abs_start = f"{line_number}.{start_pos}"
                abs_end = f"{line_number}.{end_pos}"
                
                # 创建颜色和加粗标签
                color_bold_tag = f"color_bold_mention_{username}_{int(time.time()*1000)}"
                self.chat_text.tag_add(color_bold_tag, abs_start, abs_end)
                # 同时应用蓝色和加粗字体
                self.chat_text.tag_config(color_bold_tag, foreground="blue", font=BW_FONTS["bold_small"])
        except Exception as e:
            # 如果单个高亮处理出现异常，不影响整体功能
            print(f"处理单个@用户名高亮时出错: {e}")
            pass
    
    def _highlight_individual_mentions(self, full_mention_text, base_position, prefix_length=0):
        """为单个@用户名添加特殊颜色（蓝色）和加粗效果"""
        import re
        
        # 分离出每个单独的@用户名
        individual_pattern = r'@([\w\u4e00-\u9fff]+)'
        individual_matches = list(re.finditer(individual_pattern, full_mention_text))
        
        if not individual_matches:
            return
        
        try:
            # 解析基础位置
            line_part = '.'.join(base_position.split('.')[:-1])
            char_offset = int(base_position.split('+')[-1].rstrip('c'))
            
            # 为每个@用户名添加蓝色和加粗效果
            for match in individual_matches:
                username = match.group(1)
                start_pos = char_offset + match.start()
                end_pos = char_offset + match.end()
                
                abs_start = f"{line_part}+{start_pos}c"
                abs_end = f"{line_part}+{end_pos}c"
                
                # 创建颜色和加粗标签
                color_bold_tag = f"color_bold_mention_{username}_{int(time.time()*1000)}"
                self.chat_text.tag_add(color_bold_tag, abs_start, abs_end)
                # 同时应用蓝色和加粗字体
                self.chat_text.tag_config(color_bold_tag, foreground="blue", font=BW_FONTS["bold_small"])
        except Exception as e:
            # 如果单个高亮处理出现异常，不影响整体功能
            print(f"处理单个@用户名高亮时出错: {e}")
            pass
    
    def send_notification(self, title, message):
        """发送Windows系统通知"""
        try:
            # 尝试使用 plyer 库发送通知
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="LMFP 聊天室",
                    timeout=5
                )
            except ImportError:
                # 如果 plyer 不可用，尝试使用 Windows 原生 API
                if platform.system() == "Windows":
                    # 使用 ctypes 调用 Windows MessageBox API 作为备用方案
                    ctypes.windll.user32.MessageBoxW(0, message, title, 1)
                else:
                    # 对于非 Windows 系统，简单打印消息
                    print(f"NOTIFICATION: {title} - {message}")
        except Exception as e:
            print(f"发送通知时出错: {e}")
    
    def insert_username_to_message_box(self, event):
        """双击在线用户列表时，将选中的用户名插入到消息输入框中"""
        # 由于现在使用Text控件而不是Listbox，我们需要通过鼠标位置获取用户名
        # 获取鼠标点击位置
        mouse_x = event.x
        mouse_y = event.y
        
        # 获取鼠标点击的行号
        index = self.online_text.index(f"@{mouse_x},{mouse_y}")
        line_num = int(index.split('.')[0])
        
        # 获取该行的内容
        line_start = f"{line_num}.0"
        line_end = f"{line_num}.end"
        selected_line = self.online_text.get(line_start, line_end).strip()
        
        # 提取纯用户名（去除 '(我)' 标识）
        if ' (我)' in selected_line:
            username = selected_line.replace(' (我)', '')
        else:
            username = selected_line
        
        # 在消息框中插入 @用户名
        current_text = self.message_entry.get()
        if current_text:
            # 如果消息框已有内容，在后面添加空格和用户名
            new_text = f"{current_text} @{username} "
        else:
            # 如果消息框为空，直接添加用户名
            new_text = f"@{username} "
        
        # 清空当前内容并插入新内容
        self.message_entry.delete(0, tk.END)
        self.message_entry.insert(0, new_text)
        
        # 将光标移到末尾
        self.message_entry.icursor(tk.END)
        
        # 聚焦到消息框
        self.message_entry.focus_set()
    
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
    def __init__(self, root, is_command_line=False):
        self.root = root
        self.is_command_line = is_command_line  # 标记是否为命令行启动
        # 从远程获取标题
        self.remote_title = get_remote_title()
        self.root.title(self.remote_title)
        
        # 根据启动模式设置窗口大小
        if is_command_line:
            # 命令行模式：只显示日志窗口，较小尺寸
            self.root.geometry("600x800")
        else:
            # 正常模式：完整界面
            self.root.geometry("1000x820")
        
        self.root.resizable(True, True)  # 允许窗口缩放
        self.root.configure(bg=BW_COLORS["background"])
        
        self.set_window_icon()
        self.is_admin = self.check_admin_privileges()
        self._cloud_warning_shown = False
        self.cloud_permission_granted = False
        self.is_whitelist_verified = False
        
        # 添加初始化检查状态
        self.check_in_progress = False
        self.announcement_in_progress = False
        
        # 新增：公告检查定时器
        self.announcement_check_timer = None
        
        # 新增：上次公告版本号，用于避免重复检查
        self.last_announcement_version = 0
        
        # 新增：当前公告窗口引用，用于关闭旧窗口
        self.current_announcement_window = None
        
        # 新增：提前获取主板设备码，避免打开帮助页面时卡顿
        try:
            import machineid
            self.board_sn = machineid.id()
        except Exception:
            self.board_sn = "获取失败"
            
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
        self.server_url = f"https://{apis}/api.php"
        self.current_rooms = []
        self.room_refresh_thread = None
        self.is_refreshing = False
        self.heartbeat_thread = None
        self.heartbeat_active = False
        self.current_room_info = None
        self.auto_refresh_flag = True
        self.refresh_btn = None
        
        # 独立窗口相关
        self.lobby_window = None  # 独立联机大厅窗口实例
        self.chat_room_window = None  # 独立聊天室窗口实例
        self.pyside_window = None  # PySide6主窗口实例
        
        # 重复日志过滤相关
        self.last_log_messages = []  # 存储最近的日志消息用于去重
        self.max_log_history = 10    # 最大历史记录数量
        
        # 软件状态管理
        self.software_status = "休息中"  # 当前软件状态
        self.hosting_room = False       # 是否正在主持房间
        self.in_room = False            # 是否处于房间中
        
        # UDP广播服务器实例
        self.current_multicast_server = None
        
        # UI组件占位符（在命令行模式下可能为None）
        self.online_users_label = None
        self.cloud_status_label = None
        self.software_status_label = None
        self.bottom_status_label = None
        self.status_text = None
        self.no_duplicate_logs_var = None
        
        # 按钮占位符（在命令行模式下可能为None）
        self.ipv6_btn = None
        self.frp_create_btn = None
        self.frp_join_btn = None
        self.port_map_btn = None
        self.stop_btn = None
        self.clear_btn = None
        self.export_btn = None
        self.help_btn = None
        self.qq_join_btn = None
        self.announcement_btn = None
        self.dependencies_btn = None
        self.exit_btn = None
        
        # 独立窗口相关（在命令行模式下不创建）
        self.lobby_window = None
        self.chat_room_window = None
        self.lobby_window_room_tree = None
        self.lobby_window_refresh_btn = None
        self.lobby_window_join_btn = None
        self.lobby_window_status = None
        
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
        
        # 启动周期性公告检查（每15秒检测一次新公告）
        self.start_periodic_announcement_check()
    
    def get_mac_address(self):
        """获取本机MAC地址并格式化为常见格式"""
        import uuid
        mac_int = uuid.getnode()
        mac_hex = '{:012x}'.format(mac_int)
        # 格式化为常见的MAC地址格式 (XX:XX:XX:XX:XX:XX)
        formatted_mac = ':'.join(mac_hex[i:i+2] for i in range(0, 12, 2))
        return formatted_mac
    
    def get_all_network_interfaces(self):
        """获取所有网卡的MAC地址和设备名"""
        interfaces = []
        try:
            if platform.system() == "Windows":
                # Windows系统：使用ipconfig命令
                result = subprocess.run(
                    ["ipconfig", "/all"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                output = result.stdout
                
                # 解析ipconfig输出
                lines = output.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i]
                    
                    # 检测适配器标题行（格式："xxx适配器 xxx:" 或 "Ethernet adapter xxx:"）
                    # 特征：包含"适配器"或"adapter"，且以冒号结尾
                    if ('适配器' in line or 'adapter' in line.lower()) and line.rstrip().endswith(':'):
                        # 提取适配器名称
                        adapter_name = line.strip().rstrip(':').strip()
                        
                        # 跳过空名称
                        if not adapter_name:
                            i += 1
                            continue
                        
                        # 在接下来的几行中查找物理地址
                        mac_addr = None
                        for j in range(i + 1, min(i + 20, len(lines))):
                            check_line = lines[j]
                            
                            # 如果遇到下一个适配器，停止搜索
                            if ('适配器' in check_line or 'adapter' in check_line.lower()) and check_line.rstrip().endswith(':'):
                                break
                            
                            # 查找物理地址
                            if '物理地址' in check_line or 'Physical Address' in check_line:
                                if ':' in check_line:
                                    mac_addr = check_line.split(':')[-1].strip()
                                    # MAC地址格式验证（应该是XX-XX-XX-XX-XX-XX或XX:XX:XX:XX:XX:XX）
                                    if mac_addr and len(mac_addr) >= 17:
                                        break
                        
                        # 如果找到了有效的MAC地址，添加到列表
                        if mac_addr and mac_addr != '00-00-00-00-00-00':
                            interfaces.append({
                                'name': adapter_name,
                                'mac': mac_addr
                            })
                    
                    i += 1
            else:
                # Linux/Mac系统：使用ifconfig或ip命令
                try:
                    result = subprocess.run(
                        ["ip", "link"],
                        capture_output=True,
                        text=True
                    )
                    output = result.stdout
                    
                    current_interface = None
                    for line in output.split('\n'):
                        if line.strip().endswith(':') and not line.startswith(' '):
                            current_interface = line.strip()[:-1]
                        elif 'link/ether' in line and current_interface:
                            parts = line.split()
                            if len(parts) >= 2:
                                mac_addr = parts[1]
                                interfaces.append({
                                    'name': current_interface,
                                    'mac': mac_addr
                                })
                except:
                    # 降级方案：尝试ifconfig
                    result = subprocess.run(
                        ["ifconfig"],
                        capture_output=True,
                        text=True
                    )
                    output = result.stdout
                    
                    current_interface = None
                    for line in output.split('\n'):
                        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                            current_interface = line.split(':')[0].strip()
                        elif 'ether' in line and current_interface:
                            parts = line.split()
                            if len(parts) >= 2:
                                mac_addr = parts[1]
                                interfaces.append({
                                    'name': current_interface,
                                    'mac': mac_addr
                                })
        except Exception as e:
            print(f"获取网络接口信息失败: {e}")
            # 返回基本信息
            interfaces.append({
                'name': '默认网卡',
                'mac': self.get_mac_address()
            })
        
        return interfaces
    
    def _format_network_interfaces(self):
        """格式化网卡信息为显示文本"""
        interfaces = self.get_all_network_interfaces()
        
        if not interfaces:
            return "• 未检测到网络设备"
        
        lines = []
        lines.append("• 网络设备列表：")
        
        for idx, iface in enumerate(interfaces, 1):
            name = iface.get('name', '未知设备')
            mac = iface.get('mac', '未知MAC')
            
            # 缩短过长的设备名
            if len(name) > 50:
                name = name[:47] + "..."
            
            lines.append(f"  {idx}. {name}")
            lines.append(f"     MAC: {mac}")
        
        return "\n".join(lines)
        
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
                # 验证 frpc.exe 的完整性
                if not verify_frpc_integrity():
                    # 弹窗报错并拒绝启动
                    import tkinter as tk
                    from tkinter import messagebox
                                
                    temp_root = tk.Tk()
                    temp_root.withdraw()
                    messagebox.showerror("FRPC 完整性验证失败", 
                                       "frpc.exe 的 SHA256 哈希值不匹配！\n\n期望值：df90560c6b99f5f4edfeec7e674262dcf5a34024d450089c59835ffb118d2493\n\n请重新下载正版 frpc.exe 文件。\n\n程序将拒绝启动FRPC。")
                    temp_root.destroy()
                    self.log("✗ FRPC 完整性验证失败，拒绝启动")
                else:
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
                self.log("⚠ 未找到 FRPC客户端程序 ./frpc.exe")
                
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
                if permission_result == 'whitelist':
                    self.root.after(0, lambda: self.update_cloud_status("✓ 白名单设备验证通过"))
                    self.is_whitelist_verified = True  # 标记为白名单验证
                else:  # normal
                    self.root.after(0, lambda: self.update_cloud_status("✓ 云端许可验证通过"))
                    self.is_whitelist_verified = False  # 标记为非白名单验证
                self.root.after(0, self.enable_all_buttons)
                self.cloud_permission_granted = True
            else:
                self.root.after(0, lambda: self.update_cloud_status("✗ 云端许可验证失败"))
                self.root.after(0, self.disable_all_buttons)
                self.cloud_permission_granted = False
                
                # 显示云端许可警告
                self.root.after(500, lambda: self.show_cloud_permission_failed_warning())
                return  # 如果许可失败，不继续检查公告
            

        
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
                url = f"https://{apis}/rs.php"
                req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                
                with urlopen(req, timeout=None) as response:
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
        # 在命令行模式下，online_users_label 可能为 None
        if hasattr(self, 'online_users_label') and self.online_users_label is not None:
            if isinstance(count, int):
                self.online_users_label.config(text=f"当前在线用户：{count}人", fg=BW_COLORS["success"])
            else:
                self.online_users_label.config(text=f"当前在线用户：{count}", fg=BW_COLORS["warning"])
                
        # 更新 PySide6 界面
        if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
            # 使用安全的 callback 更新 UI，避免跨线程直接操作
            def do_update():
                if hasattr(self.pyside_window, 'update_online_count_label'):
                    self.pyside_window.update_online_count_label(count)
            self.pyside_window.signals.ui_callback_requested.emit(do_update)
    
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
                
                # 发送 POST 请求
                url = f"https://{apis}/rs.php"
                data = urlencode(post_data).encode('utf-8')
                req = Request(url, data=data, headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'User-Agent': f'LMFP/{lmfpvers}'
                })
                
                with urlopen(req, timeout=None) as response:
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
    
    def update_software_status(self, status=None, hosting_room=None, in_room=None):
        """更新软件状态显示"""
        if status is not None:
            self.software_status = status
        if hosting_room is not None:
            self.hosting_room = hosting_room
        if in_room is not None:
            self.in_room = in_room
        
        # 根据状态确定显示文本和颜色
        # 优先级顺序：主持房间中 > 处于房间中 > 运行中 > 休息中 > 其他
        if self.hosting_room:
            display_text = "软件状态：主持房间中"
            color = BW_COLORS["primary"]
        elif self.in_room:
            display_text = "软件状态：处于房间中"
            color = BW_COLORS["warning"]
        elif self.software_status == "运行中":
            display_text = "软件状态：运行中"
            color = BW_COLORS["success"]
        elif self.software_status == "休息中":
            display_text = "软件状态：休息中"
            color = BW_COLORS["warning"]
        else:
            display_text = f"软件状态：{self.software_status}"
            color = BW_COLORS["text_secondary"]
        
        # 更新界面上的状态显示
        if hasattr(self, 'software_status_label'):
            self.software_status_label.config(text=display_text, fg=color)
    
    def show_announcements(self, announcements_info):
        """显示公告窗口"""
        # 如果有 PySide 窗口，通过信号在主线程中执行所有操作（包括关闭旧窗口和创建新窗口）
        if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
            def _create_and_cleanup():
                # 在主线程中安全地关闭旧窗口
                if self.current_announcement_window:
                    try:
                        if hasattr(self.current_announcement_window, 'close'):
                            self.current_announcement_window.close()
                        else:
                            self.current_announcement_window.destroy()
                    except:
                        pass
                
                # 创建新窗口
                self.current_announcement_window = show_announcements_window(announcements_info, self)
                
                # 绑定清理事件
                if self.current_announcement_window:
                    if hasattr(self.current_announcement_window, 'finished'):
                        self.current_announcement_window.finished.connect(lambda: setattr(self, 'current_announcement_window', None))
                    elif hasattr(self.current_announcement_window, 'bind'):
                        self.current_announcement_window.bind('<Destroy>', lambda e: setattr(self, 'current_announcement_window', None), '+')
                        
            self.pyside_window.signals.ui_callback_requested.emit(_create_and_cleanup)
        else:
            # Tkinter 后备逻辑
            if self.current_announcement_window:
                try:
                    self.current_announcement_window.destroy()
                except:
                    pass
            
            self.current_announcement_window = show_announcements_window(announcements_info, self.root)
            
            def on_window_destroyed(event=None):
                self.current_announcement_window = None
            
            if self.current_announcement_window:
                self.current_announcement_window.bind('<Destroy>', on_window_destroyed, '+')
    
    def send_notification(self, title, message):
        """发送Windows系统通知"""
        try:
            # 尝试使用 plyer 库发送通知
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    app_name="LMFP 联机工具",
                    timeout=10
                )
            except ImportError:
                # 如果 plyer 不可用，尝试使用 Windows 原生 API
                if platform.system() == "Windows":
                    # 使用 ctypes 调用 Windows MessageBox API 作为备用方案
                    ctypes.windll.user32.MessageBoxW(0, message, title, 1)
                else:
                    # 对于非 Windows 系统，简单打印消息
                    print(f"NOTIFICATION: {title} - {message}")
        except Exception as e:
            print(f"发送通知时出错: {e}")
    
    def start_periodic_announcement_check(self):
        """启动周期性公告检查（每15秒一次）"""
        def check_announcements_periodically():
            def run_check():
                try:
                    # 检查是否有新公告
                    announcements_info = check_announcements()
                    
                    if announcements_info and announcements_info.get('has_new_announcements'):
                        # 检查是否是真正的新公告（版本号高于上次记录的版本号）
                        cloud_version = announcements_info.get('cloud_version', 0)
                        if cloud_version > self.last_announcement_version:
                            # 如果有新公告，显示弹窗
                            self.root.after(0, lambda: self.show_announcements(announcements_info))
                            
                            # 发送系统通知
                            announcements = announcements_info.get('announcements', [])
                            if announcements:
                                title = f"LMFP联机平台新公告 ({len(announcements)}条)"
                                content = announcements[0]['content'][:50] + "..." if len(announcements[0]['content']) > 50 else announcements[0]['content']
                                message = f"新的软件公告，请及时查看！"
                                self.root.after(0, lambda: self.send_notification(title, message))
                            
                            # 更新最后看到的公告版本号
                            self.last_announcement_version = cloud_version
                except Exception as e:
                    print(f"周期性公告检查出错: {e}")
                finally:
                    # 15秒后再次检查
                    self.announcement_check_timer = self.root.after(15000, check_announcements_periodically)
            
            # 在后台线程中执行公告检查，避免阻塞UI
            threading.Thread(target=run_check, daemon=True).start()
        
        # 启动第一次检查（延迟10秒，避免与启动时的检查冲突）
        self.announcement_check_timer = self.root.after(10000, check_announcements_periodically)
        print("✓ 周期性公告检查已启动（每15秒一次）")
    
    def stop_periodic_announcement_check(self):
        """停止周期性公告检查"""
        if self.announcement_check_timer:
            self.root.after_cancel(self.announcement_check_timer)
            self.announcement_check_timer = None
            print("周期性公告检查已停止")
    
    def show_cloud_permission_failed_warning(self):
        """显示云端许可失败警告"""
        if self._cloud_warning_shown:
            return
            
        self._cloud_warning_shown = True
        
        warning_window = tk.Toplevel(self.root)
        warning_window.title("⚠ 服务器连接失败")
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
            text="服务器连接失败",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        title_label.pack(side=tk.LEFT)
        
        content_frame = create_bw_frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        warning_text = """
检测到当前软件服务器连接可能存在问题。

可能的原因：
• 软件版本过旧，请更新到最新版本
• 服务器维护或升级期间
• 网络连接问题
• 软件使用权限受限

当前状态：
• 软件功能已被锁定
• 所有按钮已禁用
• 需要重新连接服务器后才能继续使用

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
            permission_result = check_cloud_permission()
            if permission_result:
                messagebox.showinfo("检查通过", "✓ 软件使用许可已恢复！\n\n软件功能已重新启用。", parent=warning_window)
                self.enable_all_buttons()
                if permission_result == 'whitelist':
                    self.update_cloud_status("✓ 白名单设备验证通过")
                else:  # normal
                    self.update_cloud_status("✓ 云端许可验证通过")
                on_warning_close()
            else:
                messagebox.showwarning("连接失败", "⚠ 软件使用许可仍未恢复。\n\n所有功能保持锁定状态。", parent=warning_window)
        
        def exit_software():
            self.on_closing()
            self.root.quit()
        
        refresh_btn = create_bw_button(button_frame, "⟳ 重新连接服务器", refresh_check, "primary", width=18)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_software, "danger", width=15)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        warning_window.update_idletasks()
        x = (warning_window.winfo_screenwidth() - warning_window.winfo_width()) // 2
        y = (warning_window.winfo_screenheight() - warning_window.winfo_height()) // 2
        warning_window.geometry(f"+{x}+{y}")
        
        warning_window.grab_set()
    
    def create_bw_main_frame(self):
        """创建横版黑白灰风格主界面 - 简洁控制面板"""
        # 主容器
        scaled_main_padding = 15
        
        main_container = tk.Frame(self.root, bg=BW_COLORS["background"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=scaled_main_padding, pady=scaled_main_padding)
        
        # 如果是命令行模式，只显示日志区域
        if self.is_command_line:
            self.create_log_only_panel(main_container)
        else:
            # 正常模式：创建完整界面
            # 初始化独立窗口
            self.lobby_window = LobbyWindow(self)
            self.chat_room_window = ChatRoomWindow(self)
            
            # 创建简洁的控制面板
            self.create_control_panel(main_container)
    
    def create_log_only_panel(self, parent):
        """创建仅日志面板 - 用于命令行启动模式"""
        # 标题区域
        title_frame = create_bw_frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text="LMFP - Minecraft联机平台 (命令行模式)",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack(pady=15)
        
        version_label = tk.Label(
            title_frame,
            text=f"v {lmfpvers} - 自动化执行模式",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        version_label.pack(pady=(0, 15))
        
        # 状态信息区域
        status_frame = create_bw_frame(parent)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_container = tk.Frame(status_frame, bg=BW_COLORS["card_bg"])
        status_container.pack(fill=tk.X, padx=15, pady=12)
        
        # 云端许可状态
        cloud_status = "正在初始化..." 
        self.cloud_status_label = tk.Label(
            status_container,
            text=cloud_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.cloud_status_label.pack(anchor="w", pady=(2, 0))
        
        # 软件状态显示
        self.software_status_label = tk.Label(
            status_container,
            text="软件状态：休息中",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        self.software_status_label.pack(anchor="w", pady=(2, 0))
        
        # 提示文本
        hint_label = tk.Label(
            status_container,
            text="提示: 此窗口为命令行自动化模式，仅显示日志信息",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        hint_label.pack(anchor="w", pady=(5, 0))
        
        # 日志区域（占据主要空间）
        log_frame = create_bw_frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        create_section_title(log_frame, "运行日志")
        
        log_text_container = tk.Frame(log_frame, bg=BW_COLORS["card_bg"])
        log_text_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        self.status_text = scrolledtext.ScrolledText(
            log_text_container,
            height=20,
            width=60,
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
        
        # 底部按钮区域（仅保留必要的按钮）
        bottom_frame = tk.Frame(parent, bg=BW_COLORS["background"])
        bottom_frame.pack(fill=tk.X, pady=(0, 5))
        
        buttons_container = tk.Frame(bottom_frame, bg=BW_COLORS["background"])
        buttons_container.pack(fill=tk.X, padx=5)
        
        # 完整模式按钮（切换到正常模式）
        def switch_to_full_mode():
            """切换到完整模式 - 重新启动程序不带参数"""
            import subprocess
            try:
                # 获取当前可执行文件路径
                if getattr(sys, 'frozen', False):
                    # 打包后的exe
                    exe_path = sys.executable
                else:
                    # Python脚本
                    exe_path = sys.argv[0]
                    if not exe_path.endswith('.exe'):
                        exe_path = 'python ' + exe_path
                
                # 启动新实例（不带参数）
                subprocess.Popen(exe_path, creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == "Windows" else 0)
                
                # 显示提示信息
                messagebox.showinfo("提示", "已启动完整模式窗口\n\n您可以继续使用当前窗口，或手动关闭它。")
            except Exception as e:
                messagebox.showerror("错误", f"切换到完整模式失败: {e}")
        
        full_mode_btn = create_bw_button(buttons_container, "完整模式", switch_to_full_mode, "success")
        full_mode_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 清空日志按钮
        self.clear_btn = create_bw_button(buttons_container, "清空日志", self.clear_log, "secondary")
        self.clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.clear_btn.config(state='disabled')
        
        # 导出日志按钮
        self.export_btn = create_bw_button(buttons_container, "导出日志", self.export_log, "primary")
        self.export_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.export_btn.config(state='disabled')
        
        # 退出按钮
        self.exit_btn = create_bw_button(buttons_container, "退出程序", self.root.quit, "danger")
        self.exit_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
    
    def create_control_panel(self, parent):
        """创建简洁的控制面板 - 三行布局"""
        # ===== 第一行：信息区域 =====
        info_frame = create_bw_frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        scaled_info_padx = 15
        scaled_info_pady = 12
        
        info_container = tk.Frame(info_frame, bg=BW_COLORS["card_bg"])
        info_container.pack(fill=tk.X, padx=scaled_info_padx, pady=scaled_info_pady)
        
        # 标题
        title_label = tk.Label(
            info_container,
            text="LMFP - Minecraft联机平台",
            font=BW_FONTS["title"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        version_label = tk.Label(
            info_container,
            text=f"v {lmfpvers} - Lyt_IT - https://www.teft.cn/",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        version_label.pack(pady=(2, 0))
        
        # 状态信息
        admin_status = "✓ 已获取管理员权限" if self.is_admin else "⚠ 未获取管理员权限"
        admin_label = tk.Label(
            info_container,
            text=admin_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["success"] if self.is_admin else BW_COLORS["warning"]
        )
        admin_label.pack(anchor="w", pady=(5, 0))
        
        cloud_status = "正在初始化..." 
        self.cloud_status_label = tk.Label(
            info_container,
            text=cloud_status,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.cloud_status_label.pack(anchor="w", pady=(2, 0))
        
        # 在线人数显示
        self.online_users_label = tk.Label(
            info_container,
            text="当前在线用户：正在获取...",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        self.online_users_label.pack(anchor="w", pady=(2, 0))
        
        # 软件状态显示
        self.software_status_label = tk.Label(
            info_container,
            text="软件状态：休息中",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["warning"]
        )
        self.software_status_label.pack(anchor="w", pady=(2, 0))
        
        author_label = tk.Label(
            info_container,
            text="本软件开发者: Lyt_IT | QQ: 2232908600",
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_secondary"]
        )
        author_label.pack(anchor="w", pady=(5, 0))
        
        # 不发送重复日志复选框
        self.no_duplicate_logs_var = tk.BooleanVar(value=False)
        duplicate_check = tk.Checkbutton(
            info_container,
            text="不发送重复日志",
            variable=self.no_duplicate_logs_var,
            font=BW_FONTS["small"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["text_primary"],
            selectcolor=BW_COLORS["light"],
            activebackground=BW_COLORS["card_bg"],
            activeforeground=BW_COLORS["text_primary"]
        )
        duplicate_check.pack(anchor="w", pady=(2, 0))
        
        # ===== 第二行：功能按钮 + 状态信息（并排） =====
        middle_frame = tk.Frame(parent, bg=BW_COLORS["background"])
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 左侧：功能按钮区域
        left_functions = tk.Frame(middle_frame, bg=BW_COLORS["background"])
        left_functions.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        functions_frame = create_bw_frame(left_functions)
        functions_frame.pack(fill=tk.BOTH, expand=True)
        
        create_section_title(functions_frame, "联机模式选择")
        
        scaled_btn_padx = 15
        scaled_btn_pady = 12
        
        buttons_container = tk.Frame(functions_frame, bg=BW_COLORS["card_bg"])
        buttons_container.pack(fill=tk.X, padx=scaled_btn_padx, pady=scaled_btn_pady)
        
        scaled_btn_spacing = 6
        
        self.ipv6_btn = create_bw_button(
            buttons_container,
            "获取IPv6联机地址（备选联机方法）",
            self.run_ipv6_mode,
            "primary"
        )
        self.ipv6_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        self.ipv6_btn.config(state='disabled')
        
        self.frp_create_btn = create_bw_button(
            buttons_container,
            "内网穿透联机 - 创建联机房间（我要当房主）",
            self.run_frp_create,
            "secondary"
        )
        self.frp_create_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        self.frp_create_btn.config(state='disabled')
        
        self.frp_join_btn = create_bw_button(
            buttons_container,
            "内网穿透联机 - 加入联机房间（我要进别人的房间）",
            self.run_frp_join,
            "secondary"
        )
        self.frp_join_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        self.frp_join_btn.config(state='disabled')
        
        self.port_map_btn = create_bw_button(
            buttons_container,
            "自定义端口映射到25565（适用于MC不支持自定义端口的版本）",
            self.run_port_mapping,
            "primary"
        )
        self.port_map_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        self.port_map_btn.config(state='disabled')
        
        self.stop_btn = create_bw_button(
            buttons_container,
            "退出房间/关闭房间（当联机出问题  请尝试点一次这个）",
            self.stop_tcp_tunnel,
            "danger"
        )
        self.stop_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        self.stop_btn.config(state='disabled')
        
        # 分隔线
        separator = tk.Frame(buttons_container, height=2, bg=BW_COLORS["border"])
        separator.pack(fill=tk.X, pady=(8, 8))
        
        # 窗口管理按钮（放在其他功能按钮下方）
        def open_lobby():
            """打开联机大厅窗口"""
            if not self.lobby_window:
                self.lobby_window = LobbyWindow(self)
            self.lobby_window.open()
        
        def open_chat():
            """打开聊天室窗口"""
            if not self.chat_room_window:
                self.chat_room_window = ChatRoomWindow(self)
            self.chat_room_window.open()
        
        lobby_btn = create_bw_button(
            buttons_container,
            "🏠 打开联机大厅",
            open_lobby,
            "primary"
        )
        lobby_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        
        chat_btn = create_bw_button(
            buttons_container,
            "💬 打开公共聊天室",
            open_chat,
            "secondary"
        )
        chat_btn.pack(fill=tk.X, pady=scaled_btn_spacing)
        
        # 右侧：状态日志区域
        right_status = tk.Frame(middle_frame, bg=BW_COLORS["background"])
        right_status.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        status_frame = create_bw_frame(right_status)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        create_section_title(status_frame, "日志")
        
        scaled_text_padx = 12
        scaled_text_pady = 12
        
        status_text_container = tk.Frame(status_frame, bg=BW_COLORS["card_bg"])
        status_text_container.pack(fill=tk.BOTH, expand=True, padx=scaled_text_padx, pady=scaled_text_pady)
        
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
        
        # ===== 第三行：底部按钮区域 =====
        bottom_frame = tk.Frame(parent, bg=BW_COLORS["background"])
        bottom_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 创建按钮容器，自动填充宽度
        buttons_container = tk.Frame(bottom_frame, bg=BW_COLORS["background"])
        buttons_container.pack(fill=tk.X, padx=5)
        
        self.clear_btn = create_bw_button(buttons_container, "清空日志", self.clear_log, "secondary")
        self.clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.clear_btn.config(state='disabled')
        
        # 导出日志按钮
        self.export_btn = create_bw_button(buttons_container, "导出日志", self.export_log, "primary")
        self.export_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.export_btn.config(state='disabled')
        
        self.help_btn = create_bw_button(buttons_container, "使用帮助", self.show_help, "primary")
        self.help_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.help_btn.config(state='disabled')
        
        # 加入QQ群按钮
        self.qq_join_btn = create_bw_button(buttons_container, "加入QQ群", self.open_qq_group_direct, "primary")
        self.qq_join_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 查看公告按钮
        self.announcement_btn = create_bw_button(buttons_container, "查看公告", self.open_announcement_page, "primary")
        self.announcement_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 依赖补全按钮
        self.dependencies_btn = create_bw_button(buttons_container, "依赖补全", self.download_frp_dependencies, "success")
        self.dependencies_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 退出按钮
        self.exit_btn = create_bw_button(buttons_container, "退出程序", self.root.quit, "danger")
        self.exit_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # 右下角空白区域（用于状态信息）
        status_space = tk.Frame(bottom_frame, bg=BW_COLORS["background"])
        status_space.pack(side=tk.RIGHT, fill=tk.X, expand=False, padx=(0, 5))
        
        # 在右下角添加状态信息标签
        self.bottom_status_label = tk.Label(
            status_space,
            text="就绪",
            font=BW_FONTS["small"],
            bg=BW_COLORS["background"],
            fg=BW_COLORS["text_secondary"]
        )
        self.bottom_status_label.pack(side=tk.RIGHT, padx=5)
    
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
        
        tip_text = "提示: Lyt_IT 一般情况不会进入你们的房间 请仔细甄别 以防上当受骗"
        tip_color = BW_COLORS["text_secondary"]
        
        tk.Label(tip_frame, text=tip_text, font=BW_FONTS["small"], 
                fg=tip_color, wraplength=400, justify=tk.CENTER, bg=BW_COLORS["card_bg"]).pack()
        
        # 房间列表区域
        list_frame = create_bw_frame(lobby_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # 创建Treeview用于显示房间列表
        columns = ("房间号", "房间人数", "房主", "版本", "识别版本", "房间标题", "描述", "节点延迟", "状态", "操作")
        self.room_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # 设置列宽
        self.room_tree.column("房间号", width=80, anchor=tk.W)
        self.room_tree.column("房间人数", width=80, anchor=tk.W)
        self.room_tree.column("房主", width=80, anchor=tk.W)
        self.room_tree.column("版本", width=90, anchor=tk.W)
        self.room_tree.column("识别版本", width=90, anchor=tk.W)
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
    
    def load_logo_from_base64(self):
        """从内置base64数据加载logo并保存为lyy.ico"""
        try:
            import base64
            
            # Logo的base64数据（请在此处粘贴你的base64字符串）
            LOGO_BASE64 = "AAABAAEAQEAAAAEAIAAoQgAAFgAAACgAAABAAAAAgAAAAAEAIAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wb///8m////Vv///4n///+z////0f///+f+/v73/v///f7////+//////7///////////7////+/////////////////////////////////////v////7//v////7////+/v////7////+//////////////////////////////////3+/v73////5////9H///+z////if///1b///8m////BgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/v7+FP///3L+/v7F////8f///////////////////////////////////v////7////+///////////////+/////v////////////7+/v/+/v7///////////////////////////////7////+/////v////7/////////////////////////////////////////////////////////////////////8f7+/sX///9y/v7+FAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///8W////i/////H////////////////////////////////+/v7//v7+//7+/v/+/v3///79///+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7//f/+/v3//v7+//7+/v/+/v7//v7+//////////////////////////////////////////////////////////////////////H///+L////FgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///9G////1////////////////////////////////////////////f39//7+/v/+/v7//v78//7+/P/+/v7//v3+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//f79//3+/f/+/v7//v7+//7+/v///////////////////////////////////////////////////////////////////////////////9f///9GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wT///9u////+/////////////////////////////////////////////////7+/v/+/v7//v7+//3+/f/9/f7//P3+//39/v/+/f7//v7+//7+/f/+/v3//v79//7+/f/+/v7//v7+//7//v/7/v3//P39//3+/v/9/f3//Pz9//z+/v/8/v7//v7+//7+/v/+/v7/////////////////////////////////////////////////////////////////////////////////////+////27///8EAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///9u////+f/////////////////////////////////////////////////////+/v7//v7+//39/f/7/f3/+vz9//r8/P/8/f3//f3+//7+/v/+//7//v/9//7//P/+/v3//v79//7+/P/+/v3/+fz8//r9/f/7/Pv//Pz9//v8/f/5/P3//P7+//7+///+//7//v7+///+/////v///v/+//7//v/////////////////////////////////////////////////////////////////////5////bgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///9G////+////////////////////////////////////////////////////////////v7+//7+/v/9/f3//fz9//39+//8/fn/+v35//39+//4/f3//f39//z++//9//j//v78//79/f/+/vz//P7+//j6/v/7/fr//Pz0//769v/6/Pv/+vv7//z8/f/+/v7/+//8//z+/f/+/v///v3///3//f/+//7///////////////////////////////////////////////////////////////////////////v///9GAAAAAAAAAAAAAAAAAAAAAAAAAAD///8W////1/////////////////////////////////////////////////////////////////7+/v/+/v7//f39//z8+v/7/fj//Pv1//389//+/Pr//Pz8//z7/f/9/P7//P78//z+/v/7/v7/+/79//r9/v/7/f3//Pz2//Lu5P/y6+D/+frw//389//7/Pr/+v3+//z9/f/9/v7//f7///7+/v////3////+////////////////////////////////////////////////////////////////////////////////1////xYAAAAAAAAAAAAAAAAAAAAA////i//////////////////////////////////////////////////////////////////////+/v7//v7+//39/P/9/ff/+PXf/93In//48M7//vzv//38+P/6/fz/+vz8//7+/P/9/vv//P78//v+/P/9/P7//f35//v89f/Vyrr/iWVI/9O6mv/79+T/+v7z//f++v/9+/7//vr+//7+/f/9/vz//v79//7+/v/////////////////////////////////////////////////////////////////////////////////+/v6LAAAAAAAAAAAAAAAA/v7+FP////H//////////////////////////////////////////////////////////////////////f79//z+/P/7/fv//vz7//v10v/OpUz/zq1N/+XYm//8+Nr/+/3w//f+9v/8/fv//fv7//39+//9/vz//vz7//78+v/9/fn/28uz/4hNF/+JTxT/o39V/+XYvP/9+un//vv3//v5+v/9/fz//P78//z+/v/+/v7//v7+//7+/v/+/v7//////////////////////////////////////////////////////////////////f398f3+/hQAAAAAAAAAAP///3L///////////////////////////////////////////////////////////////////////////z+/f/7/vz/+v37//79+f/89s//16lA/+CsKP/TpzT/17Zb//Pmrf/8/OL/+/z1//r8/f/7/f3/+/79//n++f/9/Pv//vz7/93Mrf+SUgz/llMF/5JPEP+QUyH/wJZv//Pmzf/8/fL/+f77//z8/f/+/f7//v7+//7+/v/+/v7//v7+///////////////////////////////////////////////////////////////+//3+/f/7/vtyAAAAAP///wb+/v7F/////////////////////////////////////////////////////////////////////////v/8//3/+/78//r++//9/vf//PXP/9ipQP/tryL/7a0i/+OsJv/VqD7/4cJ9//rz0f/8/vH/+/37//38/v/7/vr//f36//z9+v/cyqz/k1IN/51TA/+eUAX/oFAI/5JPDv+RZzb/5tm///3++P/7/f3//v38//7+/v/+/v7//v7+//7+/v////////////////////////////////////////////////////////////7//v/8/vz/+/76xfz/+Qb///8m////8f////////////////////////////////////////////////////////7//v/+//7+/////v7/+//8//z++//5/vz//f76//z1z//aqT7/660g//GtI//wqyn/7aor/9+nLv/NsGD/+fbV//7+9//++/7//v38//79+v/7/fn/3cms/5ZPD/+fUwX/n1QF/51VA/+XUgX/iE0R/76cef/+/PT/+v38//z9+//+/v7//v7+//79/v/+/v7//////////v////7////////////////////////////+/////v////7////+/v7//f79//z+/PH7/v0m////Vv/////////////////////////////////////////////////////////////+//7//v/+/v////7///r//P/9//v/+v78//7++v/89c//2Kg//+msI//vrST/8Kor//GtIv/srx//z6lE//jyx//+/vb//Pz+//3+/P/+/fv/+/75/97Jqv+VTw7/nlMG/59TB/+eVAT/m1MG/5NQEv/Alm7//v3z//n++//9/f3//v7+//7+/v/+/f7//v7///////////7////+/////////////////////////////v////3////+/////v7+//3+/v/7/f7/+P3+Vv///4n//////////////////////////////////////////////////////////////v/+//7//v7////+///6//z//f/7//r+/P/+/vv//PXQ/9ipPv/orSD/7bAf/+2wI//wsh7/7a8h/9KrRP/48cb//v73//z8/f/9/vv//f76//n++P/cyqr/kVAO/59SB/+kUQf/pFIE/6ZSBv+YThD/wZdt//398//5/vv//f77//7+/f/+/v3//v7+//7+/v/////////+/////v////////////////////////////7////+///////////////9/v7/+v7+//j9/on///+z//////////////////////////////////////////////////////////////7//v/+//7+/////v//+v78//3++//6/vz//f75//z10P/Yqj7/564e/+qvHf/qsR//67Ic/+2uIf/Uq0L/+PLH//7+9//7/fz//f77//7++v/8/vj/3Mqq/41RD/+dUgf/pFEI/6VTBv+mUgb/mlAP/76Zbf/8/vP/+v37//3++f/+/vz//v79//7+/v/+/v7//v7+//////////////////////////////////////////////////////////7//P79//r+/v/3/v6z////0f/////////////////////////////////////////////////////////////+//7//v/+/v////7///r+/P/9/fv/+v/8//3/+P/89dH/2Ks9/+atH//qrSD/6bAh/+uwH//trSL/1aw+//jzx//9/vn/+v78//3++v/+/vv//v35/9zIqv+LUA//m1EI/6FRCf+fVAf/oVIF/5hSD/+7mmz/+/7z//z+/P/9/vj//v/7//7+/f/+/v3//v7+//7+/v////////////////////////////////////////////////////7////+//3+/f/6/v3/9/390f///+f//////////////////////////////////////////////////////////////v/+//7//v7////+///6/vz//f37//r//P/8//f/+/XS/9erPf/mrSD/6qwh/+qwIP/rsCH/7K0i/9WsPP/488f/+/76//j+/f/8/fv//P38//79+v/cyKr/i1EP/51RCP+hUQn/m1UH/6BTBv+ZUg7/u5ts//z99f/9/fz//P74//3/+v/+//z//v79//7+/v////////////////////////////////////////////7////+/////v/+/////v/9/v3/+/7+//f+/ef+/v73//////////////////////////////////////////////////////////////7//v/+//7+/////v//+v78//39+//6/vz//P/3//v10//Yqz7/560g/+usIP/psB7/6rAg/+uuIf/VrTv/+PPH//v9+v/4/v3//P78//n+/P/7/fr/3Mms/4pREP+eUQf/o1AH/5pVBv+hUgb/nFAN/8Cbbf/+/vb//v39//v++P/9//r//v/8//7+/P/+/v7//v7+//3+/f/9/v3//f39//7+/v/+/v7///7+//7+///+//7//f/+//7//v////7//v/+//3+/v/7/v73/////f/////////////////////////////////////////////////////////////+/////v///v////7///z+/P/7/vv/+//9//z/+f/89NH/2qo+/+itIP/rrR//6K8g/+iwHf/sryD/16s+//nyyf/8/Pv//Pv9//3++v/6/vf/+Pz3/93GqP+HUA3/nlEG/6RPCP+WVAT/nlIG/5tQDP/Am23//f71//7+/P/9/vr//v78///++////vv//f79//z+/v/8/f3/+/38//z9/P/+/Pz//v79///+/v/+/f///v/9//7//v/////////////////+//7//v/9/f///////////////////////////////////////////////////////////////////v////7///7////+///8/vz/+/77//v+/f/9//r//PTR/9epPv/mrSD/6q0e/+muH//psB3/660f/9qtP//588b/+P35//j9/P/8/vP//fvw/+/h0/+1h17/k1AH/6BQBP+iTwb/mVMD/6JRCP+XUQ7/vJxv//3+9v/+/vz///76//39/v/+/f7//fz+//39/f/8/fz//vv9//38+//6/f3/+vz+//z+/f/+/v7///7+/////f////7////////////+/v7//v7+//7//f////////////////////////////////////////////////////////////////////7////+///+/////v///f78//v++//7/v3//f77//v20//Uqz//5a0g/+muHv/priD/7K4d/+6uJP/Xq0L/+PLG//b9+f/5/fj/+vbf/9e7mf+SYjj/k00R/51QBf+dTgf/nE4H/5dSBP+fTwf/mlIN/8Kebv/9/vL//f78//7+/P/+/vn//f38//r7/v/4/P3/+/73//7+7//6+OX/+/vz//n8/f/7//v//v/9/////v////3////+/////////////v7+//7+/v/+//3////////////////////////////////////////////////////////////////////+/////v///v////7///7+/P/8/fr//f78//7++//799T/1Kw//+iuIP/orh//6a8h/++vH//qrCD/1qtE//jwwP/7+ur/6d7J/6eBVv+PVRj/kU4L/5xOBf+dTgX/mk0I/5xPBv+cVAP/mlEG/4xNDv/HpH7//f7y//r++v/8/vr//P35//v9+//4/P3/+fv3//384//x5q7/xLJ0//Hq0P/7/Pj//P32//z//P/+//7//v/+//7///////////////////////7////+/////////////////////////////////////////////////////////////////////v////7///7////+///+/vz//P36//3+/f/+/vn/+/fS/9arPv/rrSD/6a4g/+WuI//usCH/6q4h/9apP//y4aD/xKZ0/4dbJ/+OTw3/llAI/5pRB/+cUQX/m08F/5pNBf+eUQX/nlMD/41RDP+PbUH/6d7M//z9+f/9/fr/+f73//j++f/8/fn//v3u//nww//hyHf/zqc8/8ukQ//27ML//fz2//799//8/v3//v7+//3//v/+///////////////////////+/////v////////////////////////////////////////////////////////////////////7////+///+/v/+/v7//v78//39+//+/v3//v73//z30P/ZrD3/76wf/+quIv/iriX/6q0k/+ipKv/EjCf/omsf/5NSCv+VTwr/m08J/55OBv+fUAX/nFAC/51RBf+YTgb/kk8M/49TF/+9mGv/7+fS//39+f/5/vn//fz6//b7/P/8/vH//frV/+7Ykf/Wskf/2awp/+KsIv/ZqzX/+vC///z8+P/9+/r//P3+///+/f/9//3//v///////////////////////v////7//////////////////////////////////////////////////////////////////v/+//7//P/+/v7///7+//79/f/8/vv//f78//7++f/79tP/06w9/+qrIf/mqiH/56so/9eaI/+2dQ//nVcC/5pQB/+bTAr/nE0J/6BNCP+jTQf/nk4I/51PBf+fUgb/j08R/5xzSf/jzLD//vro//3+8//6/ff/+fz6//799//9/Of/9Oex/9a7W//XrSr/5q0j/+mtIP/prxz/2q0z//rywP/4/fn//P76//z+/f////3//f7+//7///////////////////////7////+//////////////////////////////////////////////////7////+/////v////7+/v/+/f7//P7+//z+/v/9/vv//P37//j+/f/5/fj//PjZ/9GsSP/jpyr/3aIn/8iFGP+jXgX/nFIE/51QBv+cTwb/mk0K/51OB/+iTQb/ok4H/5VMCv+QTxD/kFoj/8Slg//37t///fv0//38+//+/fj//P31//z78P/78sv/5s97/9auOP/crSX/6K8d/+6sH//srhv/57Ab/9erN//58cL/+P75//z++v/8/v3////9//3+/v/+///////////////+/v7//v7+//3+/v////////////////////////////////////////////7////+/////f////3////9/v7//v7+//z+/v/9/v3//vz8//39/f/z/vz/8v76//373f/YsVn/yIsi/6dmCf+eUgH/oE4J/5tMC/+VTgj/k1EE/5hPBf+dUAH/oVAD/5hOCf+HTxr/o4Ba/+7eyP/8+vT/+Pz8//j9+P/8/fn//v34//374P/o25n/1bFN/+KnK//xrx3/7rId/+muIf/pqiL/6q8Z/+auHv/Up0H/+e/I//r9+v/7/fv/+/7+///+/v/+//7//v///////////////f7+//z+/v/6/v3////////////////////////////////////////////9/////P7+//z+/v/8/v7//P7+//7+/f/+/vv//v76//39/P/6/Pv/9/35//n97f/4777/0KNG/6VlBf+VTwD/n04E/51MBv+XSwj/k00I/5VSBP+aUQf/mE8F/49MCv+VYS7/1bqe//r05//9/Pf/+/z7//r8+//9/fb//v3o//fwvf/VwGn/0Ko3/+KsJ//srh7/8a8a/+qwHf/nriP/6q0m/+euGv/gryL/zKdN//jv0v/9/Pv/+/39//z+/////v7//v/+//////////////////3+/v/7/v7/+f79/////////////////////////////////////////////v////3+/v/8/v7//P7+//z+/f/8/fv//f39//j9/v/z/Pz/+v7x//z31//q15P/0qlJ/96hMv/fniz/vnsZ/5tVA/+XTgP/m0wF/6BOBv+iUAT/mE4M/4tUHf+3lnP/9ebU//789P/8/fv/+fv7//v+/P/+/vH//PjS/+TTi//Rr0P/3qwp/+WvIf/nsB7/6LAc/+iuIP/rrCP/7qwj/+uqJf/cqyz/zrBN/+3eqf///O3//fz8//v9/f/+/v////7////+/v////7////////////+/v7//P7+//r+/f/////////////////////////////////////////////////+/v7//v7+//3+/v/8/fz//f75//z++v/6/fn//P3q//TptP/ZvmH/1qst/+atJP/qqCX/6Koi/+elJv/XlSH/rm0M/5xTAf+dTwn/lE4Q/6NxQ//eyan//Pfs//v9/P/2/Pv/+v37//7+8//+/uX/8+q0/9O6YP/WrTD/5q8g//GwIf/sriL/6q8h/+uvIf/priH/6qwl/+asI//YqjH/3MJt//fwxP/9/vD//P35//v9/f/7/fz///7+///+///+/v7////+/////v////7//v79//3+/f/8/v3//////////////////////////////////v/+//7//v/9/v7//v78//79+//7/Pv/+Pv7//39+f/+/uj//PXI/+bMgP/RqT7/2q0m/+GxG//qsRn/7K8e/+quGv/xrBz/76ob/+OnJf+/iSX/lWUn/8Oiff/789///P7x//v9+v/4/Pz/9Pz7//r99P/69ND/4s2F/8yrO//hryz/7q4j//CxHv/wryD/7q8h/++xHv/vrx3/5qsk/9moMP/XuFD/8uWk//785f/8/Pb/+P37//f9/P/6/v3/+/77//7+/v///v///v7+///+/v/+//7//v/+//7+/f/9/v3//f/9//////////////////////////////////7//f/8/v7//P7+//7++v/8/Pj/+v37//j+9v/8/OL/7N+h/9izVP/fqiv/6K4l/+auIP/lsR7/6a8d/+mvHP/orR//66se/+WqIf/TpTD/1bVh/+7jvP/9+uv//v30//j9+v/z/P3/+fz6//v65//hzKf/zaVh/9WnOP/isB//7LIf/++sJv/srCj/660i/+uzGf/nsxv/4akn/9KmQf/kzoX/+vbQ//v98f/9/P3/+/j9//38/P/7/ff/+/77//r+/f/8//7//v/////+/////v///v7///3////+/v7//f79//v+/f/////////////////////////////////+/v3//vz+//77/v/7/Pv/+Pv5//387f/47cH/3b9x/9GpN//ksCb/668d/+6rIv/yrSX/8K0e/+6uHv/nrx3/5K8l/9mmLf/RrU3/6dec//362v/7/fH/+f36//j6/P/6+/v//fz0/+7hx/+viln/kFQP/6VeCv/MiiH/5Kos/+qtKf/sriX/5bAg/+avIf/mrSX/1qg2/9i5av/06rz//f3r//j7+//1+/v//P34//78/P/+/f3//f77//3+/v/8/v7//f////7//////v////7///7+///+/v7//v7+//3+/v/7/v3//////////////////////////////////P7+//39/v/9/P7/9/33//v54v/q1Zb/1q5I/9+pKv/rsCL/67Ic/+m0Hf/qrCL/8qwn//GuIP/trSP/4qon/9OnOP/dw3L/9/DA//r87f/4/Pn/+/r7//z7/v/7+vr//Pfn/8uvhv+YYzD/j04Q/5tRCf+cUQX/nFUD/7NwEv/XlSv/668q/+ayHP/ZrCr/zqpK/+jUmP/8+Nj//v7z//v++f/4/fr/+v74//7+9v///vv//v39//79/f/+/v7//v7+//7////////////+/////v/+//7//v7+//7+/v/+/v7/+v7+//////////////////////////////////7+/v/+/vz/+f7+//r+9v/k1Zn/06g2/+asI//srx3/764f/+ewIf/jsSP/7bIg//GwG//rrSP/3Kg1/9W1V//y46X//vzg//3+8//4/Pz/9/v8//z89//9+e7/4NC3/6F4S/+NTxD/mk4J/5pOCf+aTgf/nU8D/5xQAv+UUQD/lVgE/7l6FP/apC3/271o//TqwP/+/uv/+/34//v++//9//n//v76//79/v/+/f7//f7+//3+/v///f7//v7+/////////////////////v/+//7//f/+//7+/v/+/v7//v7+//r+/f///////////////////////////////////v7///77//v9/v/8/fP/4Ml+/9qpJ//mrCH/6K8e/+6tIf/qryH/6a8k/+2tIP/jrh//16s8/+TLiP/69tL//f7r//3+9v/9/vn//fr7//v68v/y69H/sp12/4dXI/+TTQ3/m00J/5pNB/+UTAr/kU4I/5VQA/+ZUQP/k1IC/5BRAf+dWgT/vIgv//rtvP/+/e///fz4//v7/v/3/f3/+f78//z++//+/vz//v79//3+/v/+/v////7////+/v////7////+/////////////v////3////+/v7//v79//7+/f/6/vz//////////////////////////////////f7///7+/f/8/v3//f7s/+DJd//dqyb/5q8f/+mxGv/zrSH/8a4e/+ytI//gqjH/2b9k//Psu//7/Ov/+fz5//v7+//8+/v//P31//r25v/SwJ7/kGUv/4hNEP+XTgz/nk4C/5tQAv+WTwT/lk0L/5RMCv+YTQn/mkwH/6FWAf+7cw7/35Ul/9WgNP/o2aT/+/31//v8+//5/P3/+v36//z9/P/9/P3//v39///+/f/+//7//v/+//////////7////+/////v////7//v////7////9/////v7+///9/f/9/vz/+P77//////////////////////////////////v+///9/f3//v38//7/6//fzHb/36oi/+mvHf/rsRr/7qsk/+SqJ//ZskL/69mP//352v/6/PP/+/32//39+f/6/Pj/+v3x/+ziy/+qiF7/ilMc/5lPCv+dTAf/nE0I/51PBP+aUAP/l08H/5hNBP+aUAf/oVQC/7JiCP/bixv/76Yj//OpIP/eqCb/49GO//3+8//8/vz/+v39//z9+P/+/vr///39///9/v///v/////+/////v/////////+/////v////7////+//7////+/////v////7+/v/+/fz//f76//v++f/////////////////////////////////9/v3//v78//77/v/+/vD/48t5/+arIv/vrx7/56wq/9SkQ//fxXr/+/PE//796v/++vn/+vr8//v99v/+/PP/+fPd/8aviP+PXjD/kEwT/5xNDf+dTgb/l08G/5ZPB/+eTwT/oE0G/5ZNB/+OUwX/lFwI/8WBE//oniT/8Ksf/+6uG//yrB7/36ok/+TQiv/+/vL//f77//z9/v/+/vr//v76///+/P///v7////////////////////////////////////////////////////////////+/v7//f78//3++v/+/vj//////////////////////////////////v/9//3+/P/8/P7//v7v/+TKfP/hpy3/4akw/9uzWP/w4Kz/+vvi//z99//8/P3/+f39//j7/P/8+/X/7NzG/6Z7T/+QUhP/l00L/5tPCf+fTgX/nU8D/5dPBf+YTwT/nE8F/5VMDf+KTRj/qYNL/9e0af/mpjL/8Ksm/+uuHf/qsB7/7qwf/9+rJf/jz4j///7x//79+v/9+/3//v78///+/f////7//////////////////////////////////////////////////////////////////v7+//3+/P/9/vr//v75///////////////////////////////////+/v/8/P7//P37//796P/YxYT/y6dQ/+fOhf/89tD//v7w//z++P/9/P3//Pz8//b++v/4/Pz/+fHj/5drQP+WTxH/n08I/51PBf+UUAT/m1AF/6BRBf+cTgX/mE4H/4xPDv+RaT3/1bmc//z63P/q15j/3qUw/+mrIv/prx7/6a0g/+qsH//eqyX/48+H//7+8P/+/vr//vz+//79/v///v7///////////////////////////////////////////////////////////////////////7+/v/9/v3//v78//7++////////////////////////////////////v7//P38//39+v/+/vL/4dq3/+/muP/6/dr/9v7y//v8/f/+/fv//vv9//78/f/8/fv/+/z8//bt2f+LWSD/mE8I/5xOCP+fTgf/mFAH/5hNBv+bUQn/kE4O/4pWH/+6mnD/8+rU//797v/9/u//59eb/9qoLv/krSH/6a8b/+utH//prB//4Ksm/+TOh//+//D//f76//78/v/+/f7////////////////////////////////////////////////////////////////////////////+/v7//P39//7+/P///vv///////////////////////////////////7+//z9+//9/fv/+fv9//n79v/+/vH/+f7x//X++P/5/f3/+/34//39+//9/fz//f76//z9+//37tr/jFkg/5dPBv+ZTgb/oE8E/5pQCP+bTwr/jU4M/5p0Q//i07f//Pnq//39+f/6/fn/+/30/+nanv/Ypiz/5qsk/+uuHP/qrR//6Kwg/+GrJv/lzof//f/w//v++v/9/P7//v7+/////v////7////+/////v///v////7////////////////////////////////+/////v///////f7+//v9/f/+/v3///38//////3////////////////////////////+/v/9/fz//P37//j8/v/4+/3//v38//z9+v/4/f3/+Pz+//r++//9/v3//P78//n++v/7/fn/9+7e/49XI/+ZTgX/nFAE/5xRBP+VUQf/mk8I/5VdIv/v4cH//f71//n8+//5/P3//P35//7+8f/s3Jv/3agr/+qsI//srxv/6a4f/+msH//jqyb/5c6I//3/8P/7/vr//P3+//7+/f////7////+/////v////7///7////+/////////////////////////////////v/+//7//v////7+/v/9/v3//f79//79+/3+/v73///////////////////////////+/v7//v79//3+/P/8/fv//f37//7++//9//z/+v7+//n+/f/6/v3//P79//3+/P/8/fv//f76//jt3f+PWCT/l1AE/51PB/+ZUAf/mFIH/51QBv+VXCj/8efR//3++P/6/f3/+f38//7+9v/9/u//7dua/92oKf/orSH/7K0b/+mvIP/rrR7/5aom/+XOiP/9/vH//f77//39/f/+/v7////+/////v////7////+///+/////v////////////////////////////////7//v/+//3///////3//v78//v+/v/+/vn3////5//////////////////////////////+//7+/v/+/v3//f79//3+/f/9/v3//f7+//z+/v/8/v7//P7+//7+/f/+/v3//P37//3++v/47tz/j1gj/5dPBf+cUAf/mVEG/5hTBv+dUAT/lVwn//Dl0f/9/fr/+v39//n+/P/+/fb//v7y/+3bnv/dpyz/560j/+uuHf/oryH/6a0f/+OqJf/k0Ib//f/v//3++v/9/P3//v3+/////v////7////+/////v///v////7////////////////////////////////+//7//v/9/////v/9//7+/P/7/v7//f755////9H//////////////////////////////v////7//v7+//7+/v/8/v7//P7+//z+/v/+/v7//v7+//7+/v/+//3//f79//v9+//+/vv/9+3b/41XI/+WTwf/nFAG/5lSBf+ZUgf/n1IE/5RcJP/v49L//vz8//r9/P/6/fz//vz4//7+9P/t2Z7/26Ut/+WrI//prR3/5q4h/+itH//iqiT/49CE//3/7f/9/vn//vv9//79/v////7////+/////v////7///7////+/////////////////////////////////v/+//7//f////7//f/9/vz/+f7+//z++dH///+z///////////////////////////////////////////+/////f////3////9/////////////////////v/9//3+/f/6/fv//v38//ft2f+NWCL/lk8J/5xPBf+bUwT/mlIH/6BSBf+UWyH/7+PS//78/P/8/vz/+vz9//78+//+/vT/7dmd/9ylLP/lqyD/664c/+auIP/prSD/4qkj/+PPhP/9/+3//v75//78/f/+/f7////+/////v////7////+///+/////v////////////////////////////////7//v/+//3////+//3//P77//j9/f/7/vqz////if////////////////////////////////////////////////7////+/////v////////////////////7//f/9/v3/+v37//79/P/37dn/jVgi/5ZOCf+cUAT/m1MC/5tRCP+hUQb/lFwg/+/k0f/+/fv//P76//r7/v//+vv//v7z/+3amf/dpyf/5qwd/+yvGv/orh//660e/+SpJP/kzob//f/v//7++f/+/f3//v3+/////v////7////+/////v///v////7////////////////////////////////+//7//v/9/////v/9//z+/P/3/v3/+v77if///1b//////////////////////////////////////////////v////7////+//7//v/+/////v////7////+//3//P78//v+/P/+/fz/9+3Z/4tXIf+VTgr/nFAE/5tUAf+bUQj/oVEH/5RcH//v5M////36//z++v/5+f7//vr8//3+8f/t25j/3Kkk/+euG//srRj/6q4e/+ysHv/lqCX/5M2H//3+8f/9/vr//v39//7+/v////7////+/////v////7///7////+/////////////////////////////////v/+//7//f////7//f/8/vz/9/79//j++1b///8m////8f////////////////////////////////////////7////+/////v/+//7//v7///7+///+/v7//v/8//3+/P/9/v3//v37//ft3f+GViD/lk8J/5xQBP+gUwH/mFMJ/5xRBf+RXR//7+PL///+/P/9/vv/+v39//77+//9/fX/6tqj/9OlLv/jqSH/6Kwf/+quHv/vqx3/5qkm/+TNhv/8/vL//P75//v+/f/9/v3//v/9/////v////7////+//////////////////////////////////////////7//v/+//7////9/v7//P79//v+/PH7/vsm////Bv7+/sX////////////////////////////////////////////////////////+///+/v///v////7///7//f/+/vz//f39//39+v/26tr/ilQf/5ZOBv+XUAT/nFMC/5lRCf+hTwb/lVsi/+/jzf/+/vz//f76//v++v/8/Pn/9fv8//Hqx//MpUD/3aYl/+KpIv/irCL/6Kwe/+eqIf/ozoD//f7y//79/P/+/f7//v79/////v/////////////////////////////////////////////////////////+/////v/+/////P7///z+/v/8/vzF///8BgAAAAD///9y/////////////////////////////////////////////////////////v////7///7////+///+/v3//f78//39/v/6/fv/9enZ/4hSIP+VTQf/l1AE/5tTA/+aUQj/nk4H/5JaJP/v5M///P38//z++v/9/vj//f35//T6/f/7/ez/79+h/82rUf/UpTH/4ash/+2tGv/lqiP/582C//7+8f/+/vv//f39//7+/f////7//////////////////////////////////////////////////////////v////7//v////7+/v/9/v7//f7+cgAAAAAAAAAA/v7+FP////H///////////////////////////////////////////////////7////+///+///+/////P78//3++//9/f3/9/z8//j06P+Wb0X/iUoO/5ZMCP+eUAX/nVEG/6BPB/+UWSX/7+TM//n9+//6/f3//v78//7++v/9/Pz//v33//3+7P/799f/48uF/9iqOf/mqCH/2aUt/+PLhv///+7//P/4//r//P/+//3////+///////////////////////////////////////////////////////////////////////+/v7//v7+8f7+/hQAAAAAAAAAAAAAAAD///+L///////////////////////////////////////////////////+/////v///v///f7///v++//9/vv//v77//j9/f/5+/T/697E/6iBWf+GSxr/kUsN/5tOCP+nTAj/nlcm//Hjyf/7/fj/+vz+//z+/v/+/v3//vz+//79+//6/Pn/+/75//385//47rj/3Lti/8GcPv/fyon////u//3++//8/vz//v/+/////v///////////////////////////////////////////////////////v////7//////////////////4sAAAAAAAAAAAAAAAAAAAAA////Fv///9f//////////////////////////////////////////////v///v7///7///3+///8/vz//f/6//7/+v/5/fz/+f35//399P/99+j/1sKo/5huRP+KTRL/nUwO/5hWKP/x48f//P71//v9/f/9/v7//P/9//39/v/+/f3//f36//r7/P/0+fz/9v32//373f/l2af/3dKn//7+8//9/vv//v78/////v////7///////////////////////////////////////////////////////7////+/////////////9f///8WAAAAAAAAAAAAAAAAAAAAAAAAAAD///9G////+//////////////////////////////////////+/////v7///7+///+/v///f78//3++v/9/vn/+/77//n9/P/2/f3/9Pz7//z+8//379f/yKV//41YKP+GVi//7+TJ//3+9f/9/f3//f79//3//v/+/v7//v7+//v+/P/7/fz/+Pv9//f7/f/9/Pr//v3x//z87f/7/vn//P75//3++//+//7////+///////////////////////////////////////////////////////+/////v////////v///9GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///27////5/////////////////////////////////v////7////+//////////7+/v/9/vz//f76//7+/f/6/f3/9/39//X9+//4/fj//v72//797f/s38f/p5F5/+vl1f/7/vv//vz+//3+/v/+//7///////7//v/8/vz//f77//z9+v/8/Pv/+/v+//v8/P/5/Pr/+/77//z++v/9/vz//v7+//7+/v///////v7+//7+/v////////////////////////////////////////////////n///9uAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///8E////bv////v//////////////////////////////v////7////+///////+/v7//f/8//z+/P/8/f7//f39//7++v/8/Pb//P75//n7+//2+/z/9/z1//n27v/3+vX/+f3+//78/v/+/v3//v7+///+///+//7//v7+//3+/f/9/vz//P38//v9/f/6/fv/+v36//z++//9/vv//f78//39/f/9/f3//v7+//39/f/9/f3//v7+//7+/v////////////////////////////////v///9u////BAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD///9G////1/////////////////////////7////+/////v////7//v7+//z+/v/8/v7//P3///7+/v////v//v75//z8+v/6+/3/+Pv///v8/v//+vz//Pr8//z7/v/+/P7//P79//3+/v///v////////7+/v/+/v7//v7+//7+/v/8/v3/+/78//z++//9/vv//v79///+/v/+/v7//v7+//7+/v/+/v7//v7+//7+/v/+/v7//////////////////////////9f///9GAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///xb///+L////8f/////////////+/////v////7////+//7////9/////f////7+///+/v7//v/+//3//v/+//7//v7+//79/f/+/P3//vv8//77/P/+/P3//v39//v+/f/9/v7///7////////////////////////+//7//f/+//3//v/+//3//v/8//7//v//////////////////////////////////////////////////////////8f///4v///8WAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP7+/hT///9y/v7+xf////H//////////////v/+//7//v////7////+/////v/+//3//v/9//7//v/+//7+/f/+/vz//P78//v+/P/8/fz//v79//7+/f/9/v7//v7///7////////////////////+/////v////7//v/+//7//v7+//7+/f/+//7///////////////////////////////////////////H+/v7F////cv7+/hQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP///wb///8m/v//Vv7//4n///6z///+0f///+f+/v73/v///f7//v/+//z//v/8//7//f/8/v7//f7+//79/v/9/f7//v3+//7+/v/+/v7///3///7+/v/+//7////+/////////////v////7//////v////7///7+/v/+/v7////////+//3+/v73////5////9H///+z////if///1b///8m////BgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//wAAAAAP///4AAAAAAH//8AAAAAAAD//gAAAAAAAH/8AAAAAAAAP/gAAAAAAAAf8AAAAAAAAA/gAAAAAAAAB8AAAAAAAAADwAAAAAAAAAPAAAAAAAAAA4AAAAAAAAABgAAAAAAAAAGAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAABgAAAAAAAAAGAAAAAAAAAAcAAAAAAAAADwAAAAAAAAAPAAAAAAAAAA+AAAAAAAAAH8AAAAAAAAA/4AAAAAAAAH/wAAAAAAAA//gAAAAAAAH//AAAAAAAA///gAAAAAAf///wAAAAAP/8="  # <-- 在这里粘贴你的base64数据
            
            if not LOGO_BASE64:
                print("未配置logo base64数据，使用默认图标")
                return False
            
            # 解码base64数据
            try:
                icon_data = base64.b64decode(LOGO_BASE64)
            except Exception as e:
                print(f"base64解码失败: {e}")
                return False
            
            # 保存为lyy.ico文件
            ico_path = "lyy.ico"
            with open(ico_path, 'wb') as f:
                f.write(icon_data)
            
            print(f"成功从内置base64数据加载logo并保存为{ico_path}")
            return True
            
        except Exception as e:
            print(f"从base64加载logo失败: {e}")
            return False
    
    def set_window_icon(self):
        try:
            # 首先尝试从内置base64数据加载logo
            self.load_logo_from_base64()
            
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
                  self.clear_btn, self.export_btn, self.help_btn,
                  self.qq_join_btn, self.announcement_btn, self.dependencies_btn]
        
        for btn in buttons:
            if btn is not None:  # 安全检查：跳过None的按钮
                try:
                    btn.config(state='disabled', bg=BW_COLORS["text_secondary"])
                except:
                    pass
        self.root.update()
        
    def unlock_buttons(self):
        buttons_config = [
            (self.ipv6_btn, "primary"),
            (self.frp_create_btn, "secondary"), 
            (self.frp_join_btn, "secondary"),
            (self.port_map_btn, "primary"),
            (self.stop_btn, "danger"),
            (self.clear_btn, "secondary"),
            (self.export_btn, "primary"),
            (self.help_btn, "primary"),
            (self.qq_join_btn, "primary"),
            (self.announcement_btn, "primary"),
            (self.dependencies_btn, "success")
        ]
        
        for btn, style in buttons_config:
            if btn is not None:  # 安全检查：跳过None的按钮
                try:
                    btn.config(state='normal', bg=BW_COLORS[style])
                except:
                    pass
        self.root.update()
    
    def enable_all_buttons(self):
        self.cloud_permission_granted = True
        self.unlock_buttons()
        self.log("✓ 云端许可验证通过，所有功能已启用")
        self.status_text.see(tk.END)
        # 启用联机大厅按钮（如果存在）
        if hasattr(self, 'lobby_window_refresh_btn') and self.lobby_window_refresh_btn:
            self.lobby_window_refresh_btn.config(state='normal')
        if hasattr(self, 'lobby_window_join_btn') and self.lobby_window_join_btn:
            self.lobby_window_join_btn.config(state='normal')
        if hasattr(self, 'lobby_refresh_btn') and self.lobby_refresh_btn:
            self.lobby_refresh_btn.config(state='normal')
        if hasattr(self, 'lobby_join_btn') and self.lobby_join_btn:
            self.lobby_join_btn.config(state='normal')
        # 初始化后开始自动刷新
        self.root.after(2000, self.refresh_rooms)
    
    def disable_all_buttons(self):
        self.cloud_permission_granted = False
        self.lock_buttons()
        self.log("✗ 云端许可验证失败，所有功能已禁用")
        # 安全检查：status_text 可能为 None
        if hasattr(self, 'status_text') and self.status_text is not None:
            self.status_text.see(tk.END)
        # 禁用联机大厅按钮（如果存在）
        if hasattr(self, 'lobby_window_refresh_btn') and self.lobby_window_refresh_btn:
            self.lobby_window_refresh_btn.config(state='disabled')
        if hasattr(self, 'lobby_window_join_btn') and self.lobby_window_join_btn:
            self.lobby_window_join_btn.config(state='disabled')
        if hasattr(self, 'lobby_refresh_btn') and self.lobby_refresh_btn:
            self.lobby_refresh_btn.config(state='disabled')
        if hasattr(self, 'lobby_join_btn') and self.lobby_join_btn:
            self.lobby_join_btn.config(state='disabled')
    
    def is_duplicate_log(self, message):
        """检查是否为重复日志"""
        # 在命令行模式下，no_duplicate_logs_var 可能为 None
        if not hasattr(self, 'no_duplicate_logs_var') or self.no_duplicate_logs_var is None:
            return False
        
        if not self.no_duplicate_logs_var.get():
            return False
        
        # 清理消息，去除时间戳和符号，只保留核心内容
        clean_message = self.clean_log_message(message)
        
        # 如果清理后消息为空，则不进行去重
        if not clean_message:
            return False
        
        # 检查是否在最近的日志中存在相同内容
        for last_message in self.last_log_messages:
            if self.clean_log_message(last_message) == clean_message:
                return True
        
        return False
    
    def clean_log_message(self, message):
        """清理日志消息，提取核心内容用于比较"""
        # 去除时间戳 [HH:MM:SS]
        import re
        clean_msg = re.sub(r'\[\d{2}:\d{2}:\d{2}\]\s*', '', message)
        
        # 去除编号 #1 #2 等
        clean_msg = re.sub(r'#\d+', '', clean_msg)
        
        # 去除括号内的数字（如心跳包的秒数）
        clean_msg = re.sub(r'\(\d+秒\)', '', clean_msg)
        
        # 去除符号 ✗ ✓ ■ → 等
        clean_msg = re.sub(r'[✗✓■→]', '', clean_msg)
        
        # 去除多余的空格
        clean_msg = re.sub(r'\s+', ' ', clean_msg).strip()
        
        return clean_msg
    
    def add_to_log_history(self, message):
        """将日志添加到历史记录中"""
        # 安全检查：no_duplicate_logs_var 可能为 None
        if not hasattr(self, 'no_duplicate_logs_var') or self.no_duplicate_logs_var is None:
            return
        
        if self.no_duplicate_logs_var.get():
            self.last_log_messages.append(message)
            # 保持历史记录在最大数量范围内
            if len(self.last_log_messages) > self.max_log_history:
                self.last_log_messages.pop(0)
    
    def log(self, message):
        # 安全检查：status_text 可能为 None
        if not hasattr(self, 'status_text') or self.status_text is None:
            print(message)  # 如果UI未初始化，输出到控制台
            return
        
        # 添加时间戳
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # 检查是否为重复日志
        if self.is_duplicate_log(formatted_message):
            return  # 如果是重复日志则不显示
        
        try:
            self.status_text.config(state=tk.NORMAL)
            self.status_text.insert(tk.END, f"{formatted_message}\n")
            self.status_text.config(state=tk.DISABLED)
            self.status_text.see(tk.END)
            self.root.update_idletasks()
            
            # 将消息添加到历史记录
            self.add_to_log_history(formatted_message)
        except Exception as e:
            print(f"日志输出错误: {e}")
            print(message)    
    def clear_log(self):
        # 安全检查：status_text 可能为 None
        if not hasattr(self, 'status_text') or self.status_text is None:
            return
        
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        # 同时清空日志历史记录，避免重复日志过滤问题
        self.last_log_messages.clear()
    
    def export_log(self):
        """导出日志到txt文件"""
        # 安全检查：status_text 可能为 None
        if not hasattr(self, 'status_text') or self.status_text is None:
            messagebox.showerror("错误", "日志组件未初始化")
            return
        
        try:
            from tkinter import filedialog
            import datetime
            
            # 获取当前日志内容
            log_content = self.status_text.get(1.0, tk.END).strip()
            
            if not log_content:
                messagebox.showwarning("提示", "日志为空，无法导出！")
                return
            
            # 生成默认文件名（包含时间戳）
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"LMFP_日志_{timestamp}.txt"
            
            # 打开保存对话框
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=default_filename,
                title="导出日志"
            )
            
            # 如果用户取消了操作
            if not file_path:
                return
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"LMFP - Minecraft联机平台 日志导出\n")
                f.write(f"导出时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=" * 60 + "\n\n")
                f.write(log_content)
            
            # 显示成功消息
            messagebox.showinfo("成功", f"日志已成功导出到:\n{file_path}")
            self.log(f"✓ 日志已导出到: {file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出日志失败: {str(e)}")
            self.log(f"✗ 导出日志失败: {str(e)}", is_error=True)


    def open_qq_group(self):
        """打开 QQ 群链接"""
        try:
            import webbrowser
            # 从 qun.txt 获取实际的网址
            req = Request(f"https://{apis}/qun.txt", headers={'User-Agent': f'LMFP/{lmfpvers}'})
            with urlopen(req, timeout=None) as response:
                redirect_url = response.read().decode('utf-8').strip()
            # 打开获取到的网址
            webbrowser.open(redirect_url)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开QQ群链接: {e}")

    def show_other_functions(self):
        """显示其他功能弹窗"""
        # 创建弹窗
        other_func_window = tk.Toplevel(self.root)
        other_func_window.title("其他功能")
        other_func_window.geometry("300x300")
        other_func_window.configure(bg=BW_COLORS["background"])
        other_func_window.resizable(False, False)
        
        # 设置窗口图标
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                other_func_window.iconbitmap(icon_path)
        except:
            pass
        
        # 居中显示
        other_func_window.update_idletasks()
        x = (other_func_window.winfo_screenwidth() // 2) - (other_func_window.winfo_width() // 2)
        y = (other_func_window.winfo_screenheight() // 2) - (other_func_window.winfo_height() // 2)
        other_func_window.geometry(f"+{x}+{y}")
        
        # 设置窗口始终在最前
        other_func_window.attributes('-topmost', True)
        
        # 主容器
        main_container = create_bw_frame(other_func_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            title_frame,
            text="请选择功能",
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack()
        
        # 按钮框架
        button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 加入QQ群按钮
        qq_btn = create_bw_button(button_frame, "加入QQ群", self.open_qq_group_direct, "primary", width=15)
        qq_btn.pack(pady=5)
                
        # 查看公告按钮
        notice_btn = create_bw_button(button_frame, "查看公告", self.open_announcement_page, "primary", width=15)
        notice_btn.pack(pady=5)
                
        # 依赖补全按钮
        dep_btn = create_bw_button(button_frame, "依赖补全", self.download_frp_dependencies, "success", width=15)
        dep_btn.pack(pady=5)
        
        # 设置为模态窗口
        other_func_window.transient(self.root)
        other_func_window.grab_set()
    
    def download_frp_dependencies(self):
        """下载 FRP 依赖文件"""
        # 如果PySide窗口存在，立即切换到"联机"页
        if hasattr(self, 'pyside_window') and self.pyside_window is not None:
            try:
                # 直接切换页面
                self.pyside_window.nav_list.setCurrentRow(0)
                # 强制刷新UI
                self.pyside_window.repaint()
            except Exception as e:
                print(f"切换页面失败: {e}")
        
        self.log("正在启动 FRP 依赖下载...")
        
        # 在后台线程中执行下载，避免阻塞UI
        def download_in_background():
            result = self.check_and_download_frp(auto_download=True)
            # 下载完成后显示结果
            if result:
                self.root.after(0, lambda: messagebox.showinfo("完成", "FRP 依赖文件已下载并解压完成！\n\n现在可以正常使用联机功能了。"))
            else:
                self.root.after(0, lambda: messagebox.showerror("失败", "FRP 依赖文件下载失败！\n\n请检查网络连接后重试。"))
        
        import threading
        thread = threading.Thread(target=download_in_background, daemon=True)
        thread.start()
    
    def open_qq_group_direct(self):
        """直接打开 QQ 群链接"""
        try:
            import webbrowser
            # 从 qun.txt 获取实际的网址
            req = Request(f"https://{apis}/qun.txt", headers={'User-Agent': f'LMFP/{lmfpvers}'})
            with urlopen(req, timeout=None) as response:
                redirect_url = response.read().decode('utf-8').strip()
            # 打开获取到的网址
            webbrowser.open(redirect_url)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开QQ群链接: {e}")
    
    def open_announcement_page(self):
        """打开公告页面"""
        try:
            import webbrowser
            # 打开公告页面
            webbrowser.open(f"https://{apis}/gg.php")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开公告页面: {e}")

    def activate_whitelist(self):
        board_sn = getattr(self, 'board_sn', '未获取')
        if board_sn == '未获取':
            if globals().get('PYSIDE6_AVAILABLE', False):
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(None, "错误", "未能获取到主板设备码，无法激活。")
            else:
                from tkinter import messagebox
                messagebox.showerror("错误", "未能获取到主板设备码，无法激活。")
            return

        tko = ""
        is_pyside = globals().get('PYSIDE6_AVAILABLE', False)
        
        if is_pyside:
            from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit
            tko, ok = QInputDialog.getText(None, "激活白名单", "请输入激活码 (tko):", QLineEdit.Normal, "")
            if not ok or not tko:
                return
        else:
            from tkinter import simpledialog, messagebox
            import tkinter as tk
            tko = simpledialog.askstring("激活白名单", "请输入激活码 (tko):", parent=self.root)
            if not tko:
                return

        import threading

        result_dict = {'done': False, 'result': None, 'error': None}

        def do_activation():
            try:
                import urllib.request
                from urllib.request import Request
                url = f"https://{apis}/vert.php?tk={board_sn}&tko={tko}"
                req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                with urllib.request.urlopen(req, timeout=None) as response:
                    result_dict['result'] = response.read().decode('utf-8').strip()
            except Exception as e:
                result_dict['error'] = str(e)
            finally:
                result_dict['done'] = True

        threading.Thread(target=do_activation, daemon=True).start()

        if is_pyside:
            from PySide6.QtWidgets import QProgressDialog, QMessageBox
            from PySide6.QtCore import Qt, QTimer
            progress = QProgressDialog("激活中，请稍候...", None, 0, 0, None)
            progress.setWindowTitle("正在处理")
            progress.setWindowModality(Qt.ApplicationModal)
            progress.setCancelButton(None)
            progress.setMinimumDuration(0)
            progress.show()

            def check_done():
                if result_dict['done']:
                    progress.close()
                    if result_dict['error']:
                        QMessageBox.critical(None, "错误", f"激活过程发生错误: {result_dict['error']}")
                    else:
                        if result_dict['result'].lower() == 'true':
                            QMessageBox.information(None, "成功", "白名单激活成功！请重启软件以生效。")
                        else:
                            QMessageBox.critical(None, "失败", "激活码无效或已被使用。")
                else:
                    QTimer.singleShot(100, check_done)
            
            QTimer.singleShot(100, check_done)
        else:
            import tkinter as tk
            from tkinter import messagebox
            progress = tk.Toplevel(self.root)
            progress.title("正在处理")
            progress.geometry("250x100")
            progress.transient(self.root)
            progress.grab_set()
            tk.Label(progress, text="激活中，请稍候...").pack(expand=True)
            progress.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - 250) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - 100) // 2
            progress.geometry(f"+{x}+{y}")

            def check_done():
                if result_dict['done']:
                    progress.destroy()
                    if result_dict['error']:
                        messagebox.showerror("错误", f"激活过程发生错误: {result_dict['error']}")
                    else:
                        if result_dict['result'].lower() == 'true':
                            messagebox.showinfo("成功", "白名单激活成功！请重启软件以生效。")
                        else:
                            messagebox.showerror("失败", "激活码无效或已被使用。")
                else:
                    self.root.after(100, check_done)

            self.root.after(100, check_done)

    def show_help(self):
        """显示使用帮助 - PySide6版本"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QFont
            
            # 检查是否有PySide窗口
            pyside_win = None
            if hasattr(self, 'pyside_window') and self.pyside_window is not None:
                pyside_win = self.pyside_window
            
            if pyside_win is None:
                # 如果没有PySide窗口，使用Tkinter版本
                self._show_help_tkinter()
                return
            
            # 创建PySide对话框
            dialog = QDialog(pyside_win)
            dialog.setWindowTitle("使用帮助")
            dialog.resize(700, 600)
            dialog.setModal(True)
            
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #F5F7FA;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    padding: 10px 30px;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    background-color: #1976D2;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #1565C0;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(30, 20, 30, 20)
            layout.setSpacing(15)
            
            # 标题
            title_label = QLabel("📖 LMFP - Minecraft联机平台使用说明")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #1565C0; padding: 10px 0;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            # 帮助内容
            help_text = QTextEdit()
            help_text.setReadOnly(True)
            help_text.setStyleSheet("""
                QTextEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 15px;
                    font-family: 'Microsoft YaHei', sans-serif;
                    font-size: 13px;
                    line-height: 1.6;
                    color: #333333;
                }
            """)
            
            network_html = f"<ul><li>{getattr(self, 'board_sn', '未获取')}</li></ul>"
            
            help_content = f"""
<h2 style="color: #1976D2;">🌐 IPv6联机模式：</h2>
<ul>
<li>需要双方都有IPv6网络支持</li>
<li>速度快，延迟低</li>
<li>端口自动检测</li>
<li>自动复制联机地址到剪贴板</li>
</ul>

<h2 style="color: #1976D2;">🔗 FRP创建房间：</h2>
<ul>
<li>无需IPv6，使用中转服务器</li>
<li>自动选择最佳节点</li>
<li>端口自动检测</li>
<li>生成房间号：远程端口_FRP服务器号</li>
<li>可选择公开或私有房间</li>
</ul>

<h2 style="color: #1976D2;">🚪 FRP进入房间：</h2>
<ul>
<li>输入朋友分享的房间号</li>
<li>自动从云端获取FRP服务器信息</li>
<li>使用TCP隧道将远程服务器映射到127.0.0.1:25565</li>
<li>无需启动FRP客户端</li>
</ul>

<h2 style="color: #1976D2;">🔄 端口映射功能：</h2>
<ul>
<li>将其他Minecraft端口映射到25565</li>
<li>方便使用非标准端口的服务器</li>
<li>自动关闭防火墙规则</li>
<li>程序退出时自动清理映射</li>
</ul>

<h2 style="color: #1976D2;">🏛️ 联机大厅：</h2>
<ul>
<li>浏览所有公开房间</li>
<li>30秒自动刷新房间列表</li>
<li>双击或点击“加入”按钮快速加入</li>
<li>显示房间详细信息（包括房间描述）</li>
</ul>

<h2 style="color: #1976D2;">💬 公共聊天室：</h2>
<ul>
<li>实时在线聊天功能</li>
<li>QQ邮箱注册登录</li>
<li>邮箱验证系统</li>
<li>显示在线用户列表</li>
<li>自动刷新消息</li>
</ul>

<h2 style="color: #1976D2;">⏹️ 停止TCP隧道连接：</h2>
<ul>
<li>强制停止当前TCP隧道</li>
<li>解决连接冲突问题</li>
<li>安全清理网络连接</li>
</ul>

<h2 style="color: #1976D2;">☁️ 云端许可验证：</h2>
<ul>
<li>软件启动时需要验证云端许可</li>
<li>使用过程中会定期检查许可状态</li>
<li>如果许可验证失败，所有功能将被锁定</li>
<li>需要重新验证通过后才能继续使用</li>
</ul>

<h2 style="color: #1976D2;">📢 公告功能：</h2>
<ul>
<li>软件启动时自动检查新公告</li>
<li>有新公告时会弹出公告窗口</li>
<li>公告支持多标签页浏览</li>
<li>可标记为已读</li>
</ul>

<h2 style="color: #1976D2;">❓ 常见问题：</h2>
<ol>
<li>如果无法连接，请检查防火墙设置</li>
<li>确保已开启Minecraft局域网游戏</li>
<li>联机时不要关闭程序窗口</li>
<li>每人只能同时运行一个TCP隧道</li>
</ol>

<h2 style="color: #1976D2;">💻 系统信息：</h2>
<p><strong>主板设备码：</strong></p>
{network_html}

<h2 style="color: #1976D2;">📞 技术支持：</h2>
<p style="background-color: #E3F2FD; padding: 15px; border-radius: 8px; border-left: 4px solid #1976D2;">
<strong>QQ:</strong> 2232908600<br>
<strong>微信:</strong> liuyvetong
</p>
            """
            
            help_text.setHtml(help_content)
            layout.addWidget(help_text)
            
            # 关闭按钮和激活按钮
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            
            activate_btn = QPushButton("激活白名单权限")
            activate_btn.setFixedWidth(150)
            activate_btn.clicked.connect(self.activate_whitelist)
            button_layout.addWidget(activate_btn)
            
            close_btn = QPushButton("关闭")
            close_btn.setFixedWidth(100)
            close_btn.clicked.connect(dialog.close)
            button_layout.addWidget(close_btn)
            
            layout.addLayout(button_layout)
            
            # 显示对话框
            dialog.exec()
            
        except ImportError:
            # 如果PySide6不可用，使用Tkinter版本
            self._show_help_tkinter()
        except Exception as e:
            print(f"PySide帮助窗口创建失败: {e}")
            import traceback
            traceback.print_exc()
            self._show_help_tkinter()
    
    def _show_help_tkinter(self):
        """显示使用帮助 - Tkinter版本（备用）"""
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
        
        board_sn = getattr(self, 'board_sn', '未获取')
        
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
• 双击或点击“加入”按钮快速加入
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

系统信息：
• 主板设备码: {board_sn}

技术支持：
QQ: 2232908600
微信: liuyvetong
        """.format(board_sn=board_sn)
        
        help_text.insert(1.0, help_content)
        help_text.config(state=tk.DISABLED)
        
        close_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        close_frame.pack(fill=tk.X, padx=20, pady=15)
        
        activate_btn = create_bw_button(close_frame, "激活白名单权限", self.activate_whitelist, "primary", width=16)
        activate_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = create_bw_button(close_frame, "关闭", help_window.destroy, "primary", width=12)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
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
    
    def get_all_java_processes(self):
        """获取系统中所有Java相关进程的信息"""
        java_processes = []
        try:
            if platform.system() == "Windows":
                # 检查java.exe进程
                result_java = subprocess.run(
                    ["tasklist", "/fi", "imagename eq java.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in result_java.stdout.split('\n'):
                    if 'java.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_processes.append({
                                    'pid': pid,
                                    'name': 'java.exe',
                                    'full_line': line.strip()
                                })
                
                # 检查javaw.exe进程
                result_javaw = subprocess.run(
                    ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in result_javaw.stdout.split('\n'):
                    if 'javaw.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_processes.append({
                                    'pid': pid,
                                    'name': 'javaw.exe',
                                    'full_line': line.strip()
                                })
            else:
                # Linux/macOS系统
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True)
                for line in result.stdout.split('\n'):
                    if 'java' in line and ('jdk' in line or 'jre' in line or 'minecraft' in line.lower()):
                        parts = line.split()
                        if len(parts) >= 2:
                            java_processes.append({
                                'pid': parts[1],
                                'name': 'java',
                                'full_line': line.strip()
                            })
        except Exception as e:
            self.log(f"获取Java进程信息时出错: {e}")
        
        return java_processes
    
    def get_java_process_ports(self):
        java_ports = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, check=True)
                lines = result.stdout.split('\n')
                
                java_pids = set()
                
                # 检查java.exe进程
                task_result_java = subprocess.run(
                    ["tasklist", "/fi", "imagename eq java.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in task_result_java.stdout.split('\n'):
                    if 'java.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_pids.add(pid)
                
                # 检查javaw.exe进程
                task_result_javaw = subprocess.run(
                    ["tasklist", "/fi", "imagename eq javaw.exe", "/fo", "csv"], 
                    capture_output=True, text=True, check=True
                )
                for line in task_result_javaw.stdout.split('\n'):
                    if 'javaw.exe' in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            if pid.isdigit():
                                java_pids.add(pid)
                
                self.log(f"发现Java相关进程 {len(java_pids)} 个: {', '.join(java_pids) if java_pids else '无'}")
                
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
                                                self.log(f"发现Java/jawaw进程监听端口: {port}")
                                                break
                                except ValueError:
                                    continue
            else:
                result = subprocess.run(["lsof", "-i", "-P", "-n"], capture_output=True, text=True, check=True)
                for line in result.stdout.split('\n'):
                    if ("java" in line or "javaw" in line) and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            port_part = parts[8]
                            if ":" in port_part:
                                try:
                                    port = int(port_part.split(":")[1])
                                    if port not in java_ports:
                                        java_ports.append(port)
                                        self.log(f"发现Java/jawaw进程监听端口: {port}")
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
                self.log(f"发现 {len(java_ports)} 个Java相关进程监听的端口: {java_ports}")
                for port in java_ports:
                    if port in self.mc_ports:
                        candidate_ports.append(port)
                
                if not candidate_ports:
                    candidate_ports = java_ports
                    self.log(f"使用所有Java进程端口作为候选: {candidate_ports}")
                else:
                    self.log(f"筛选出Minecraft常用端口: {candidate_ports}")
            else:
                self.log("未找到Java进程监听的端口")
                return None
        else:
            self.log("25565端口已被占用，添加到候选端口")
            candidate_ports.append(25565)
        
        self.log(f"开始验证 {len(candidate_ports)} 个候选端口: {candidate_ports}")
        valid_ports = []
        for port in candidate_ports:
            self.log(f"正在验证端口 {port}...")
            if self.mcstatus_port(port):
                valid_ports.append(port)
                self.log(f"✓ 端口 {port} 验证通过，是Minecraft联机端口")
            else:
                self.log(f"✗ 端口 {port} 验证失败")
        
        if valid_ports:
            if 25565 in valid_ports:
                self.log(f"优先选择标准端口 25565")
                return 25565
            else:
                selected_port = valid_ports[0]
                self.log(f"选择端口 {selected_port} 作为Minecraft端口")
                return selected_port
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
        global lmfp_server_failure_count
        
        self.log("正在从云端获取FRP节点列表...")
        
        try:
            # 修改 URL 以从新的位置获取 FRP 列表
            url = f"https://{apis}/frplist58.txt"
            
            # 访问真实URL
            req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
            
            with urlopen(req, timeout=None) as response:
                content = response.read().decode('utf-8').strip()
                
                nodes = []
                
                # 检查内容是否为空
                if not content:
                    self.log("⚠ 云端返回空数据，无法连接LMFP服务器（联系QQ 2232908600）")
                    # 增加失败计数
                    lmfp_server_failure_count += 1
                    print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
                    # 显示错误弹窗（仅在连续失败3次时）
                    show_network_error_dialog()
                    return []
                
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
                    # 成功访问服务器，重置失败计数器
                    lmfp_server_failure_count = 0
                    return nodes
                else:
                    self.log("⚠ 云端数据格式异常，无法连接LMFP服务器（联系QQ 2232908600）")
                    # 增加失败计数
                    lmfp_server_failure_count += 1
                    print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
                    # 显示错误弹窗（仅在连续失败3次时）
                    show_network_error_dialog()
                    return []
                    
        except Exception as e:
            self.log(f"✗ 获取FRP节点列表失败: {e}")
            # 增加失败计数
            lmfp_server_failure_count += 1
            print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
            # 显示错误弹窗（仅在连续失败3次时）
            show_network_error_dialog()
            return []

    def get_特殊_nodes(self):
        """从云端获取特殊节点列表（/f特殊.txt）"""
        global lmfp_server_failure_count
        
        self.log("正在从云端获取特殊节点列表...")
        
        try:
            # 从/f特殊.txt获取特殊节点列表
            # 对中文字符进行URL编码
            import urllib.parse
            filename = urllib.parse.quote("fvip.txt")
            url = f"https://{apis}/{filename}"
            
            # 访问真实URL
            req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
            
            with urlopen(req, timeout=None) as response:
                content = response.read().decode('utf-8').strip()
                
                nodes = []
                
                # 检查内容是否为空
                if not content:
                    self.log("⚠ 特殊节点数据为空")
                    return []
                
                # 解析节点格式：节点号#[名称 IP:端口 token]
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
                                    self.log(f"✓ 解析特殊节点 #{node_id}: {node_name} (*.*.*.*:{server_port})")
                        except Exception as e:
                            self.log(f"⚠ 解析特殊节点行失败 '{line}': {e}")
                            continue
                
                if nodes:
                    self.log(f"✓ 从云端获取到 {len(nodes)} 个特殊节点")
                    # 成功访问服务器，重置失败计数器
                    lmfp_server_failure_count = 0
                    return nodes
                else:
                    self.log("⚠ 特殊节点数据格式异常")
                    return []
                    
        except Exception as e:
            self.log(f"✗ 获取特殊节点列表失败: {e}")
            # 增加失败计数
            lmfp_server_failure_count += 1
            print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
            return []


    
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
                self.stop_udp_broadcast()
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
        """运行 FRP 客户端，使用命令行参数而非配置文件"""
        try:
            self.log("正在启动FRP 服务...")
                
            # 检查 frpc.exe 是否存在
            if not os.path.exists("frpc.exe"):
                self.log("✗ 未找到 frpc.exe 文件")
                return False
                
            # 验证 frpc.exe 的完整性
            if not verify_frpc_integrity():
                self.log("✗ FRPC 完整性验证失败，拒绝启动")
                # 弹窗报错
                import tkinter as tk
                from tkinter import messagebox
                    
                temp_root = tk.Tk()
                temp_root.withdraw()
                messagebox.showerror("FRPC 完整性验证失败", 
                                   "frpc.exe 的 SHA256 哈希值不匹配！\n\n期望值：df90560c6b99f5f4edfeec7e674262dcf5a34024d450089c59835ffb118d2493\n\n请重新下载正版 frpc.exe 文件。\n\n程序将拒绝启动FRPC。")
                temp_root.destroy()
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
            # 首先尝试使用节点自带的 token
            node_token = node.get('token', '')
            if node_token:
                # 解密节点 token：将字母解码为数字（21-46）并拼接
                decrypted_node_token = decrypt_token(node_token)
                command.extend(['--token', decrypted_node_token])
                self.log(f"✓ 使用节点配置的穿透密钥（已解密）")
            else:
                # 如果节点没有 token，则从云端获取通用 token
                token_url = f"https://{apis}/tkasdAsdw.txt"
                try:
                    req = Request(token_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urlopen(req, timeout=None) as response:
                        token_content = response.read().decode('utf-8').strip()
                        # 如果 token 文件不为空，则添加到命令行参数中
                        if token_content:
                            # 解密 token：将字母解码为数字（21-46）并拼接
                            decrypted_token = decrypt_token(token_content)
                            command.extend(['--token', decrypted_token])
                            self.log(f"✓ 获取到穿透密钥（已解密），已添加到命令行参数")
                        else:
                            self.log("ℹ 未获取到穿透密钥，将以无密钥模式启动")
                except Exception as e:
                    self.log(f"⚠ 获取穿透密钥失败：{e}，将继续以无密钥模式启动")
            
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
                    
                    # 停止FRP进程和UDP广播
                    self.cleanup_frp_process()
                    self.stop_udp_broadcast()
                    
                    # 手动更新软件状态为休息中
                    self.update_software_status(hosting_room=False, in_room=False, status="休息中")
                    
                    # 在主线程中显示弹窗
                    def show_warning():
                        if hasattr(self, 'pyside_window') and self.pyside_window:
                            show_modern_error_dialog(self.pyside_window, "警告", f"连续{max_consecutive_failures}次无法检测到MC服务器，FRP已自动停止")
                        else:
                            import tkinter.messagebox
                            tkinter.messagebox.showinfo(
                                "警告",
                                f"连续{max_consecutive_failures}次无法检测到MC服务器，FRP已自动停止"
                            )
                            
                    if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
                        self.pyside_window.signals.ui_callback_requested.emit(show_warning)
                    else:
                        if hasattr(self, 'root') and self.root:
                            self.root.after(0, show_warning)
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
                        
                        # 停止FRP进程和UDP广播
                        self.stop_frp_services()
                        self.stop_udp_broadcast()
                        
                        # 手动更新软件状态为休息中
                        self.update_software_status(hosting_room=False, in_room=False, status="休息中")
                        
                        # 在主线程中显示弹窗
                        def show_warning():
                            if hasattr(self, 'pyside_window') and self.pyside_window:
                                show_modern_error_dialog(self.pyside_window, "警告", f"连续{max_consecutive_failures}次无法检测到本地Minecraft服务器，FRP已自动停止")
                            else:
                                import tkinter.messagebox
                                tkinter.messagebox.showinfo(
                                    "警告",
                                    f"连续{max_consecutive_failures}次无法检测到本地Minecraft服务器，FRP已自动停止"
                                )
                                
                        if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
                            self.pyside_window.signals.ui_callback_requested.emit(show_warning)
                        else:
                            if hasattr(self, 'root') and self.root:
                                self.root.after(0, show_warning)
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

    def show_pyside_room_info_dialog(self, full_room_code, mc_info, server_addr, remote_port):
        """显示 PySide6 现代化的房间信息填写对话框"""
        if not hasattr(self, 'pyside_window') or not self.pyside_window:
            return None
            
        import threading
        result_container = [None]
        dialog_event = threading.Event()
        
        def _show():
            try:
                from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                                             QTextEdit, QCheckBox, QPushButton, QHBoxLayout, 
                                             QFrame, QGridLayout)
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QFont, QIcon
                
                dialog = QDialog(self.pyside_window)
                dialog.setWindowTitle("发布到联机大厅")
                dialog.setFixedSize(500, 520)
                dialog.setModal(True)
                
                # 样式
                dialog.setStyleSheet("""
                    QDialog { background-color: #F5F7FA; }
                    QLabel { color: #37474F; font-size: 13px; background: transparent; }
                    QLineEdit, QTextEdit {
                        padding: 8px;
                        border: 1px solid #E0E0E0;
                        border-radius: 6px;
                        background-color: white;
                        selection-background-color: #1976D2;
                    }
                    QLineEdit:focus, QTextEdit:focus {
                        border: 1px solid #1976D2;
                    }
                    QCheckBox {
                        color: #546E7A;
                        font-size: 13px;
                        spacing: 8px;
                    }
                    QPushButton {
                        padding: 10px 25px;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
                
                main_layout = QVBoxLayout(dialog)
                main_layout.setContentsMargins(30, 30, 30, 30)
                main_layout.setSpacing(20)
                
                # 标题
                title_lbl = QLabel("房间信息设置")
                title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1565C0;")
                title_lbl.setAlignment(Qt.AlignCenter)
                main_layout.addWidget(title_lbl)
                
                # 房间代码卡片
                info_card = QFrame()
                info_card.setStyleSheet("background-color: #E3F2FD; border-radius: 8px; padding: 10px;")
                info_card_layout = QVBoxLayout(info_card)
                
                code_lbl = QLabel(f"完整房间号: <b>{full_room_code}</b>")
                addr_lbl = QLabel(f"服务器地址: [已加密保护]")
                info_card_layout.addWidget(code_lbl)
                info_card_layout.addWidget(addr_lbl)
                main_layout.addWidget(info_card)
                
                # 表单区域
                form_layout = QGridLayout()
                form_layout.setSpacing(15)
                
                form_layout.addWidget(QLabel("房主 ID:"), 0, 0)
                host_input = QLineEdit()
                host_input.setText("玩家")
                form_layout.addWidget(host_input, 0, 1)
                
                form_layout.addWidget(QLabel("游戏版本:"), 1, 0)
                version_input = QLineEdit()
                version_input.setText(mc_info.get("version", ""))
                form_layout.addWidget(version_input, 1, 1)
                
                form_layout.addWidget(QLabel("房间描述:"), 2, 0, Qt.AlignTop)
                desc_input = QTextEdit()
                desc_input.setPlaceholderText("好的描述能吸引更多人加入...")
                desc_input.setText(mc_info.get("motd", "欢迎来玩！"))
                desc_input.setFixedHeight(80)
                form_layout.addWidget(desc_input, 2, 1)
                
                main_layout.addLayout(form_layout)
                
                # 选项
                is_public_check = QCheckBox("公开房间（在联机大厅显示）")
                is_public_check.setChecked(True)
                main_layout.addWidget(is_public_check)
                
                is_mod_check = QCheckBox("包含 MOD（模组）内容")
                is_mod_check.setChecked(False)
                main_layout.addWidget(is_mod_check)
                
                main_layout.addStretch()
                
                # 按钮
                btn_layout = QHBoxLayout()
                
                def on_confirm():
                    if not host_input.text().strip():
                        show_modern_message(dialog, "输入错误", "请输入房主ID", "warning")
                        host_input.setFocus()
                        return
                    if not version_input.text().strip():
                        show_modern_message(dialog, "输入错误", "请输入游戏版本", "warning")
                        version_input.setFocus()
                        return
                        
                    description = desc_input.toPlainText().strip() or "欢迎来玩！"
                    if is_mod_check.isChecked():
                        description = "（MOD）" + description
                        
                    room_info = {
                        'full_room_code': full_room_code,
                        'room_name': f"{host_input.text().strip()}的房间",
                        'game_version': version_input.text().strip(),
                        'player_count': 1,
                        'max_players': 20,
                        'description': description,
                        'is_public': is_public_check.isChecked(),
                        'host_player': host_input.text().strip(),
                        'server_addr': server_addr,
                        'remote_port': remote_port
                    }
                    result_container[0] = room_info
                    dialog.accept()
                
                cancel_btn = QPushButton("取消")
                cancel_btn.setStyleSheet("""
                    QPushButton { background-color: white; color: #78909C; border: 1px solid #CFD8DC; }
                    QPushButton:hover { background-color: #F5F7FA; border: 1px solid #B0BEC5; }
                """)
                cancel_btn.clicked.connect(dialog.reject)
                
                confirm_btn = QPushButton("发布到联机大厅")
                confirm_btn.setStyleSheet("""
                    QPushButton { background-color: #1976D2; color: white; border: none; }
                    QPushButton:hover { background-color: #1565C0; }
                """)
                confirm_btn.clicked.connect(on_confirm)
                
                # 动态更改按钮文字
                def update_btn_text():
                    confirm_btn.setText("发布到联机大厅" if is_public_check.isChecked() else "创建私有房间")
                is_public_check.stateChanged.connect(update_btn_text)
                
                btn_layout.addWidget(cancel_btn)
                btn_layout.addSpacing(10)
                btn_layout.addWidget(confirm_btn)
                main_layout.addLayout(btn_layout)
                
                host_input.setFocus()
                host_input.selectAll()
                
                dialog.exec()
            except Exception as e:
                print(f"PySide房间信息对话框失败: {e}")
            finally:
                dialog_event.set()
                
        self.pyside_window.signals.ui_callback_requested.emit(_show)
        dialog_event.wait()
        return result_container[0]

    def collect_room_info(self, remote_port, node_id, full_room_code, server_addr, mc_port=None):
        # 使用传入的Minecraft服务器端口信息
        mc_info = self.get_mc_server_info(mc_port)
        
        # 尝试使用 PySide6 对话框
        if hasattr(self, 'pyside_window') and self.pyside_window:
            return self.show_pyside_room_info_dialog(full_room_code, mc_info, server_addr, remote_port)
            
        # 回退到 Tkinter 对话框
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
        tk.Label(room_info_frame, text=f"服务器地址: [已隐藏]",
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
                show_modern_message(None, "输入错误", "请输入房主ID", "warning")
                host_player_entry.focus()
                return
            
            if not version_var.get().strip():
                show_modern_message(None, "输入错误", "请输入游戏版本", "warning")
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
            
            with urllib.request.urlopen(req, timeout=None) as response:
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
                
                with urllib.request.urlopen(req, timeout=None) as response:
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
            self.log(f"启动TCP隧道: *.*.*.*:{remote_port} -> 127.0.0.1:{local_port}")
            
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
                                    self.log(f"隧道数据转发提示 ({direction}): {e}")
                        
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
                self.log(f"→ 转发到 *.*.*.*:{remote_port}")
                
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

    def stop_udp_broadcast(self):
        """停止UDP广播"""
        if hasattr(self, 'current_multicast_server') and self.current_multicast_server:
            try:
                self.current_multicast_server.stop()
                self.current_multicast_server = None
                self.log("✓ UDP广播已停止")
            except Exception as e:
                self.log(f"✗ 停止UDP广播时出错: {e}")
                self.current_multicast_server = None
    
    def stop_tcp_tunnel(self, update_status=True):
        """停止TCP隧道
        Args:
            update_status: 是否更新软件状态，默认True
        """
        if hasattr(self, 'tunnel_active') and self.tunnel_active:
            self.tunnel_active = False
            if hasattr(self, 'tunnel_socket'):
                try:
                    self.tunnel_socket.close()
                except:
                    pass
            self.log("✓ TCP隧道已停止")
        
        # 停止UDP广播
        self.stop_udp_broadcast()
        
        # 停止FRP服务
        self.stop_frp_services()
        
        # 根据参数决定是否更新软件状态
        if update_status:
            # 更新软件状态为休息中
            self.update_software_status(hosting_room=False, in_room=False, status="休息中")
        
        # 强制结束系统中所有frpc.exe进程
        try:
            if platform.system() == "Windows":
                subprocess.run(['taskkill', '/f', '/im', 'frpc.exe'], 
                              capture_output=True, 
                              creationflags=subprocess.CREATE_NO_WINDOW)
                self.log("✓ 已强制结束所有frpc.exe进程")
            else:
                subprocess.run(['pkill', '-f', 'frpc'], capture_output=True)
                self.log("✓ 已强制结束所有frpc进程")
        except Exception as e:
            self.log(f"✗ 结束frpc进程时出错: {e}")

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
            
            # 如果节点列表为空，说明无法连接服务器
            if not nodes:
                self.log(f"✗ 无法连接LMFP服务器（联系QQ 2232908600）")
                return None
            
            # 获取特殊节点列表（所有用户都可以获取）
            self.log("正在获取特殊节点列表...")
            special_nodes = self.get_特殊_nodes()
            if special_nodes:
                self.log(f"✓ 获取到 {len(special_nodes)} 个特殊节点")
                # 合并普通节点和特殊节点，避免重复
                existing_ids = {node['node_id'] for node in nodes}
                for special_node in special_nodes:
                    if special_node['node_id'] not in existing_ids:
                        nodes.append(special_node)
            else:
                self.log("⚠ 未能获取特殊节点列表")
            
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
            self.log(f"   服务器地址: [已隐藏]")
            
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
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    return
                
                server_addr = fresh_room_info['server_addr']
                remote_port = fresh_room_info['remote_port']
                node_name = fresh_room_info['node_name']
                
                self.log(f"✓ 获取到最新房间信息")
                self.log(f"   完整房间号: {full_room_code}")
                self.log(f"   FRP节点: #{fresh_room_info['node_id']} - {node_name}")
                self.log(f"   服务器地址: [已隐藏]")
                
                # 使用mcstatus验证服务器是否为Minecraft服务器
                if not self.is_minecraft_server_port(server_addr, remote_port):
                    self.log("✗ 目标服务器不是Minecraft服务器或无法连接")
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    def show_error():
                        if hasattr(self, 'pyside_window') and self.pyside_window:
                            show_modern_error_dialog(self.pyside_window, "错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                        else:
                            import tkinter.messagebox
                            tkinter.messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                    
                    if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
                        self.pyside_window.signals.ui_callback_requested.emit(show_error)
                    else:
                        show_error()
                    return
                else:
                    self.log("✓ 服务器验证通过，确认为目标Minecraft服务器")
                
                # 停止现有的隧道（更新状态为运行中）
                self.stop_tcp_tunnel(update_status=True)
                # 立即设置运行中状态
                self.update_software_status(status="运行中")
                
                # 启动TCP隧道
                if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                    self.log("✓ TCP隧道启动成功")
                    # 启动FRP服务
                    self.start_frp_services()
                                        
                    # 写入成功状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": f"完成_{full_room_code}"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 完成_{full_room_code}")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    # 更新软件状态为处于房间中，并重置运行状态
                    self.update_software_status(status="处于房间中", in_room=True, hosting_room=False)

                    # 启动UDP广播（仅在成功加入房间时广播，创建房间时不广播）
                    multicast_server = MulticastServer(
                        motd="§6§l双击进入LMFP联机房间（请保持LMFP运行）",
                        port=25565,
                        multicast_group="224.0.2.60",
                        port_num=4445
                    )
                    
                    # 保存广播服务器实例以便后续停止
                    self.current_multicast_server = multicast_server
                    
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
                    self.log(f"   远程服务器: [已隐藏]")
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
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
            except Exception as e:
                self.log(f"✗ 加入房间过程中出现错误: {e}")
                
                # 写入失败状态到 sta.json
                try:
                    sta_file = os.path.join(os.getcwd(), 'sta.json')
                    with open(sta_file, 'w', encoding='utf-8') as f:
                        json.dump({"status": "失败"}, f, ensure_ascii=False)
                    self.log(f"✓ 状态已写入: 失败")
                except Exception as write_err:
                    self.log(f"⚠ 写入状态文件失败: {write_err}")
            finally:
                # 无论成功失败，都确保解锁按钮
                self.unlock_buttons()
        
        threading.Thread(target=join_thread, daemon=True).start()

    def refresh_rooms(self, auto_refresh=False):        
        if self.is_refreshing:
            return
            
        # 只有云端许可验证通过后才能刷新房间
        if not self.cloud_permission_granted:
            # 尝试更新联机大厅窗口的状态
            if hasattr(self, 'lobby_window_status') and self.lobby_window_status:
                self.lobby_window_status.config(text="等待云端许可验证...")
            return
            
        self.is_refreshing = True
        
        # 获取当前有效的刷新按钮
        refresh_btn = None
        if hasattr(self, 'lobby_window_refresh_btn') and self.lobby_window_refresh_btn:
            refresh_btn = self.lobby_window_refresh_btn
        elif hasattr(self, 'lobby_refresh_btn') and self.lobby_refresh_btn:
            refresh_btn = self.lobby_refresh_btn
        
        if refresh_btn:
            refresh_btn.config(state='disabled', text='⟳ 刷新中...')
        
        def refresh_thread():
            try:
                if not auto_refresh:
                    self.log("⟳ 正在获取房间列表...")
                
                self.current_rooms = []
                cleaned_count = 0
                
                # 获取主房间
                try:
                    response = self.http_request("GET")
                    if response and response.get('success'):
                        self.current_rooms = response['data']['rooms']
                        stats = response['data'].get('stats', {})
                        cleaned_count = stats.get('cleaned_rooms', 0)
                except Exception as e:
                    self.log(f"⚠ 获取主房间列表失败: {e}")
                
                # 获取额外房间
                extra_response = None
                try:
                    extra_url = f"https://{apis}/servers.json"
                    req = urllib.request.Request(extra_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urllib.request.urlopen(req, timeout=None) as extra_res:
                        extra_content = extra_res.read().decode('utf-8')
                        extra_response = json.loads(extra_content)
                except Exception:
                    try:
                        extra_url2 = f"https://{apis}/servers.json"
                        req2 = urllib.request.Request(extra_url2, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                        with urllib.request.urlopen(req2, timeout=None) as extra_res2:
                            extra_content2 = extra_res2.read().decode('utf-8')
                            extra_response = json.loads(extra_content2)
                    except Exception:
                        pass
                
                if extra_response and extra_response.get('success'):
                    extra_rooms = extra_response['data'].get('rooms', [])
                    for room in extra_rooms:
                        room['is_extra'] = True
                        if 'player_count' not in room:
                            room['player_count'] = 0
                        if 'max_players' not in room:
                            room['max_players'] = 100
                        if 'description' not in room:
                            room['description'] = room.get('room_name', '无描述')
                        if 'last_update' not in room:
                            room['last_update'] = time.time()
                        self.current_rooms.append(room)
                
                if self.current_rooms:
                    self.update_room_list()
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    status_text = f"找到 {len(self.current_rooms)} 个活跃房间"
                    if cleaned_count > 0:
                        status_text += f" (已清理 {cleaned_count} 个过期房间)"
                    
                    # 更新状态栏
                    if hasattr(self, 'lobby_window_status') and self.lobby_window_status:
                        self.lobby_window_status.config(text=status_text)
                    elif hasattr(self, 'lobby_status') and self.lobby_status:
                        self.lobby_status.config(text=status_text)
                    
                    if hasattr(self, 'lobby_window_last_update') and self.lobby_window_last_update:
                        self.lobby_window_last_update.config(text=f"最后更新: {current_time}")
                    elif hasattr(self, 'last_update_label') and self.last_update_label:
                        self.last_update_label.config(text=f"最后更新: {current_time}")
                    
                    if not auto_refresh:
                        self.log("✓ 房间列表已刷新")
                else:
                    # 更新状态栏
                    if hasattr(self, 'lobby_window_status') and self.lobby_window_status:
                        self.lobby_window_status.config(text="获取房间列表失败")
                    elif hasattr(self, 'lobby_status') and self.lobby_status:
                        self.lobby_status.config(text="获取房间列表失败")
                    self.log("✗ 获取房间列表失败")
            except Exception as e:
                # 更新状态栏
                if hasattr(self, 'lobby_window_status') and self.lobby_window_status:
                    self.lobby_window_status.config(text=f"刷新失败: {e}")
                elif hasattr(self, 'lobby_status') and self.lobby_status:
                    self.lobby_status.config(text=f"刷新失败: {e}")
                self.log(f"✗ 刷新房间列表失败: {e}")
            finally:
                self.is_refreshing = False
                
                # 恢复按钮状态
                refresh_btn_final = None
                if hasattr(self, 'lobby_window_refresh_btn') and self.lobby_window_refresh_btn:
                    refresh_btn_final = self.lobby_window_refresh_btn
                elif hasattr(self, 'lobby_refresh_btn') and self.lobby_refresh_btn:
                    refresh_btn_final = self.lobby_refresh_btn
                
                if refresh_btn_final:
                    refresh_btn_final.config(state='normal', text='⟳ 刷新')
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def update_room_list(self):
        # 获取当前有效的room_tree
        room_tree = None
        if hasattr(self, 'lobby_window_room_tree') and self.lobby_window_room_tree:
            room_tree = self.lobby_window_room_tree
        elif hasattr(self, 'room_tree') and self.room_tree:
            room_tree = self.room_tree
        
        if not room_tree:
            return
        
        for item in room_tree.get_children():
            room_tree.delete(item)
        
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
            server_addr_display = "[已隐藏]"
            
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
            
            # 使用描述作为房间标题，如果没有则用默认名
            display_name = room.get('description', room.get('room_name', '未命名房间'))
            
            # 格式化描述(MOTD)，带上版本号
            display_motd = room_name # mcstatus获取到的motd
            if not display_motd:
                display_motd = room.get('description', '')
                
            if detected_version and detected_version != "未知":
                display_motd = f"[{detected_version}] {display_motd}"
            elif room.get('game_version'):
                display_motd = f"[{room['game_version']}] {display_motd}"

            room_tree.insert("", "end", values=(
                full_room_code,    # 房间号
                actual_players,    # 房间人数
                room.get('host_player', '未知玩家'),  # 房主
                room['game_version'],  # 版本
                detected_version,   # 识别版本
                display_name,      # 房间标题 (显示描述)
                display_motd,      # 描述 (带版本前缀)
                latency,           # 延迟
                status,            # 状态
                join_button_text   # 操作
            ), tags=(full_room_code,))

    def on_room_click(self, event, room_tree=None, room_detail_text=None):
        # 如果没有传入参数，使用默认值
        if room_tree is None:
            if hasattr(self, 'lobby_window_room_tree') and self.lobby_window_room_tree:
                room_tree = self.lobby_window_room_tree
            elif hasattr(self, 'room_tree') and self.room_tree:
                room_tree = self.room_tree
            else:
                return
        
        if room_detail_text is None:
            if hasattr(self, 'lobby_window_detail_text') and self.lobby_window_detail_text:
                room_detail_text = self.lobby_window_detail_text
            elif hasattr(self, 'room_detail_text') and self.room_detail_text:
                room_detail_text = self.room_detail_text
            else:
                return
        
        item = room_tree.identify_row(event.y)
        column = room_tree.identify_column(event.x)
        
        if not item:
            return
        
        # 获取房间信息
        room_values = room_tree.item(item, "values")
        if not room_values:
            return
        
        full_room_code = room_values[0]   # 房间号
        actual_players = room_values[1]   # 房间人数
        host_player = room_values[2]      # 房主
        game_version = room_values[3]     # 版本
        detected_version = room_values[4] # 识别版本
        room_name = room_values[5]        # 房间标题
        description = room_values[6]      # 描述
        latency = room_values[7]          # 延迟
        status = room_values[8]           # 状态
        
        # 更新房间详情
        room_detail_text.config(state=tk.NORMAL)
        room_detail_text.delete(1.0, tk.END)
        
        # 查找完整的房间描述
        full_description = description
        server_info = None
        for room in self.current_rooms:
            current_full_room_code = f"{room['remote_port']}_{room['node_id']}"
            if current_full_room_code == full_room_code:
                full_description = room.get('description', description)
                server_info = room
                break
        
        detail_text += f"房间名称: {room_name}\n"
        detail_text += f"游戏版本: {game_version} | 房主: {host_player} | 延迟: {latency} | 状态: {status}\n"
        detail_text += f"完整房间号: {full_room_code}\n"
        detail_text += f"服务器地址: [已隐藏]\n"
        detail_text += f"房间描述: {full_description}\n"
                
        # 显示实际玩家数量
        if server_info:
            actual_players = self.get_actual_player_count(server_info.get('server_addr'), server_info.get('remote_port'))
            detail_text += f"实际玩家数量: {actual_players}"
                
        room_detail_text.insert(1.0, detail_text)
        room_detail_text.config(state=tk.DISABLED)
        
        # 如果是点击"操作"列（最后一列），则加入房间
        if column == "#10":  # 操作列现在是第10列
            self.join_selected_room()

    def on_room_double_click(self, event, room_tree=None):
        """双击房间行加入房间"""
        # 如果没有传入参数，使用默认值
        if room_tree is None:
            if hasattr(self, 'lobby_window_room_tree') and self.lobby_window_room_tree:
                room_tree = self.lobby_window_room_tree
            elif hasattr(self, 'room_tree') and self.room_tree:
                room_tree = self.room_tree
            else:
                return
        
        item = room_tree.identify_row(event.y)
        if item:
            self.join_selected_room()

    def check_and_download_frp(self, auto_download=True):
        """检查 FRP 文件是否存在，如果不存在则根据 auto_download 参数决定是否下载"""
        import urllib.request
        import zipfile
        import os
        import hashlib
        import threading
        
        # 获取软件所在目录（兼容 PyInstaller 和 Nuitka打包）
        if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS') or '__compiled__' in globals():
            # 如果是打包后的 exe 运行环境（包括 PyInstaller, Nuitka 等）
            import ctypes
            from ctypes import wintypes
            
            try:
                # Windows API 获取可执行文件的真实路径
                GetModuleFileNameW = ctypes.windll.kernel32.GetModuleFileNameW
                GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
                GetModuleFileNameW.restype = wintypes.DWORD
                
                MAX_PATH = 260
                buffer = ctypes.create_unicode_buffer(MAX_PATH)
                GetModuleFileNameW(None, buffer, MAX_PATH)
                executable_path = buffer.value
                
                # 检查是否是临时目录（Nuitka onefile 模式）
                import tempfile
                temp_dir = tempfile.gettempdir()
                
                self.log(f"调试信息 - sys.executable: {sys.executable}")
                self.log(f"调试信息 - 当前工作目录：{os.getcwd()}")
                self.log(f"调试信息 - GetModuleFileName 获取的路径：{executable_path}")
                self.log(f"调试信息 - 临时目录：{temp_dir}")
                
                # 判断是否为 onefile 模式（临时目录或包含特定关键字）
                if executable_path.startswith(temp_dir) or '_MEI' in executable_path.upper() or 'NUITKA' in executable_path.upper():
                    # Onefile 模式：使用当前工作目录（用户启动程序的位置）
                    software_dir = os.getcwd()
                    self.log(f"调试信息 - 检测到 OneFile 模式，使用当前工作目录：{software_dir}")
                else:
                    # OneDir 模式：直接使用 exe 所在目录
                    software_dir = os.path.dirname(executable_path)
                    self.log(f"调试信息 - 检测到 OneDir 模式，使用 exe 所在目录：{software_dir}")
                    
            except Exception as e:
                self.log(f"获取真实路径失败：{e}，使用备用方案")
                software_dir = os.getcwd()
        else:
            # 如果是 Python 源码运行环境
            software_dir = os.path.dirname(os.path.abspath(__file__))
        
        frpc_path = os.path.join(software_dir, "frpc.exe")
        frps_path = os.path.join(software_dir, "frps.exe")
        
        # 调试日志
        self.log(f"检查 FRP 文件路径：{software_dir}")
        self.log(f"  frpc.exe 存在：{os.path.exists(frpc_path)}")
        self.log(f"  frps.exe 存在：{os.path.exists(frps_path)}")
        
        # 预期的 SHA256 哈希值
        expected_sha256 = "7923839d091d3759b3e366397c40c15df8cbfc702766c4bfbfca57bd3c8f84a7"
        
        # 检查是否已经在下载中
        if hasattr(self, '_frp_download_in_progress') and self._frp_download_in_progress:
            self.log("FRP 文件已在下载中，请稍候...")
            # 等待下载完成
            import time
            while self._frp_download_in_progress:
                time.sleep(0.1)
            # 下载完成后检查文件是否存在
            if os.path.exists(frpc_path) and os.path.exists(frps_path):
                return True
            else:
                return False
        
        # 检查是否缺少任一文件
        if not os.path.exists(frpc_path) or not os.path.exists(frps_path):
            if not auto_download:
                # 不自动下载，提示用户手动操作
                self.log("✗ 缺少 FRP 依赖文件（frpc.exe 和 frps.exe）")
                messagebox.showerror(
                    "缺少依赖",
                    "检测到缺少 FRP 依赖文件！\n\n"
                    "请依次点击软件：\n"
                    "更多功能--【依赖补全】\n\n"
                    "下载完成后即可正常使用联机功能。"
                )
                return False
            
            # 自动下载模式
            self.log("检测到缺少 FRP 文件，正在后台下载...")
            
            # 标记下载进行中
            self._frp_download_in_progress = True
            
            download_complete = threading.Event()
            download_result = [False]  # 使用列表来在线程间共享结果
            
            def download_thread():
                try:
                    # 构造下载 URL
                    frp_zip_url = f"https://{apis}/dl/frp.zip"
                    frp_zip_path = os.path.join(software_dir, "frp.zip")
                                
                    self.log(f"正在从 {frp_zip_url} 下载 FRP 压缩包...")
                                
                    # 下载 zip 文件（带进度和超时）
                    req = Request(frp_zip_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urllib.request.urlopen(req, timeout=None) as response:
                        total_size = int(response.headers.get('Content-Length', 0))
                        downloaded = 0
                        block_size = 8192
                                    
                        with open(frp_zip_path, 'wb') as f:
                            while True:
                                # 检查是否被取消
                                if cancel_flag[0]:
                                    self.log("下载已被用户取消")
                                    raise Exception("用户取消下载")
                                            
                                buffer = response.read(block_size)
                                if not buffer:
                                    break
                                downloaded += len(buffer)
                                f.write(buffer)
                                            
                                # 每下载 1% 更新一次进度
                                if total_size > 0 and downloaded % max(1, total_size // 100) < block_size:
                                    percentage = (downloaded / total_size) * 100
                                    self.log(f"下载进度：{percentage:.1f}% ({downloaded / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB)")
                                
                    self.log("FRP 压缩包下载完成，计算 SHA256 哈希值...")
                                
                    # 计算下载文件的 SHA256
                    sha256_hash = hashlib.sha256()
                    with open(frp_zip_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(chunk)
                                
                    calculated_sha256 = sha256_hash.hexdigest()
                    self.log(f"计算的 SHA256: {calculated_sha256}")
                    self.log(f"预期的 SHA256: {expected_sha256}")
                                
                    # 验证 SHA256
                    if calculated_sha256 != expected_sha256:
                        self.log(f"✗ SHA256 验证失败！文件可能已损坏或被篡改")
                        # 删除无效文件
                        try:
                            os.remove(frp_zip_path)
                        except:
                            pass
                        raise Exception("SHA256 验证失败")
                                
                    self.log("✓ SHA256 验证通过")
                    self.log("正在解压 FRP 文件...")
                                
                    # 解压 zip 文件
                    with zipfile.ZipFile(frp_zip_path, 'r') as zip_ref:
                        for file_info in zip_ref.infolist():
                            try:
                                zip_ref.extract(file_info, software_dir)
                                self.log(f"  ✓ 解压：{file_info.filename}")
                            except Exception as e:
                                self.log(f"  ⚠ 跳过文件 {file_info.filename}：解压失败 ({e})")
                                
                    self.log("FRP 文件解压完成")
                                
                    # 删除临时 zip 文件
                    try:
                        os.remove(frp_zip_path)
                    except Exception as e:
                        self.log(f"删除临时 zip 文件失败：{e}")
                                
                    # 验证文件是否存在
                    if os.path.exists(frpc_path) and os.path.exists(frps_path):
                        self.log("✓ FRP 文件已就绪")
                        download_result[0] = True
                    else:
                        self.log("✗ FRP 文件解压后仍然缺失")
                        download_result[0] = False
                                    
                except Exception as e:
                    self.log(f"✗ 下载过程中出现错误：{e}")
                    # 删除可能存在的损坏文件
                    try:
                        if os.path.exists(frp_zip_path):
                            os.remove(frp_zip_path)
                            self.log("已删除损坏的压缩文件")
                    except:
                        pass
                    download_result[0] = False
                                
                finally:
                    download_complete.set()  # 标记下载完成
            
            # 启动下载线程
            thread = threading.Thread(target=download_thread, daemon=True)
            thread.start()
            
            # 使用 after 方法周期性检查下载状态（不阻塞 UI）
            result_container = {'done': False, 'success': False}
            check_scheduled = [False]  # 标记是否已调度检查
            cancel_flag = [False]  # 取消标志
            
            def check_download_status():
                if download_complete.is_set():
                    # 下载完成
                    result_container['done'] = True
                    result_container['success'] = download_result[0]
                    # 清除下载标志
                    self._frp_download_in_progress = False
                    # 不再继续调度
                    check_scheduled[0] = False
                else:
                    # 继续等待
                    check_scheduled[0] = True
                    self.root.after(100, check_download_status)
            
            # 开始轮询（只调度一次）
            if not check_scheduled[0]:
                self.root.after(100, check_download_status)
            
            # 决定使用 PySide6 还是 Tkinter 弹窗
            if hasattr(self, 'pyside_window') and self.pyside_window:
                # ===================== PySide6 弹窗 =====================
                def show_pyside_dialog():
                    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
                    from PySide6.QtCore import Qt, QTimer
                    
                    dialog = QDialog(self.pyside_window)
                    dialog.setWindowTitle("等待下载完成")
                    dialog.setFixedSize(350, 150)
                    dialog.setWindowModality(Qt.WindowModal)
                    # 禁用关闭按钮
                    dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
                    dialog.setStyleSheet("""
                        QDialog { background-color: white; border-radius: 8px; }
                        QLabel { font-size: 14px; color: #37474F; font-weight: bold; }
                        QPushButton { 
                            background-color: #F44336; color: white; border: none; 
                            padding: 10px; border-radius: 6px; font-size: 13px; font-weight: bold;
                        }
                        QPushButton:hover { background-color: #E53935; }
                    """)
                    
                    layout = QVBoxLayout(dialog)
                    layout.setContentsMargins(30, 30, 30, 20)
                    
                    lbl = QLabel("正在下载 FRP 文件...\n请稍候")
                    lbl.setAlignment(Qt.AlignCenter)
                    layout.addWidget(lbl)
                    
                    layout.addStretch()
                    
                    btn = QPushButton("取消下载")
                    btn.setCursor(Qt.PointingHandCursor)
                    def on_cancel():
                        cancel_flag[0] = True
                        self.log("用户取消下载...")
                        dialog.reject()
                    btn.clicked.connect(on_cancel)
                    layout.addWidget(btn)
                    
                    # 定期检查下载是否完成
                    def check_done():
                        if result_container['done']:
                            dialog.accept()
                        elif cancel_flag[0]:
                            dialog.reject()
                        else:
                            QTimer.singleShot(100, check_done)
                            
                    QTimer.singleShot(100, check_done)
                    dialog.exec()

                # 请求在 PySide 线程显示对话框
                self.pyside_window.signals.ui_callback_requested.emit(show_pyside_dialog)
                
                # 在 Tkinter 线程中等待，保持 UI 响应
                import time
                while not result_container['done'] and not cancel_flag[0]:
                    self.root.update()
                    time.sleep(0.05)
                    
            else:
                # ===================== Tkinter 弹窗 (Fallback) =====================
                wait_window = tk.Toplevel(self.root)
                wait_window.title("等待下载完成")
                wait_window.geometry("350x150")
                wait_window.resizable(False, False)
                wait_window.transient(self.root)
                wait_window.grab_set()
                wait_window.configure(bg="#f0f0f0")
                
                wait_window.protocol("WM_DELETE_WINDOW", lambda: None)
                
                x = (wait_window.winfo_screenwidth() - 350) // 2
                y = (wait_window.winfo_screenheight() - 150) // 2
                wait_window.geometry(f"+{x}+{y}")
                
                main_frame = tk.Frame(wait_window, bg="#f0f0f0")
                main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                
                label = tk.Label(main_frame, text="正在下载 FRP 文件...\n请稍候", font=("Segoe UI", 10), bg="#f0f0f0", fg="#333333")
                label.pack(pady=(0, 15))
                
                def cancel_download():
                    cancel_flag[0] = True
                    self.log("用户取消下载...")
                
                cancel_btn = tk.Button(main_frame, text="取消下载", command=cancel_download, font=("Segoe UI", 9, "bold"),
                                       bg="#f44336", fg="white", activebackground="#e53935", activeforeground="white",
                                       cursor="hand2", width=15, height=2, relief=tk.FLAT, overrelief=tk.RAISED)
                cancel_btn.pack(pady=(5, 0))
                
                def close_wait_window():
                    if result_container['done']:
                        wait_window.destroy()
                    elif cancel_flag[0]:
                        wait_window.destroy()
                    else:
                        wait_window.after(100, close_wait_window)
                
                close_wait_window()
                wait_window.wait_window()
            
            # 检查是否被取消
            if cancel_flag[0]:
                self.log("✗ FRP 文件下载已取消")
                return False
            
            return result_container['success']
        else:
            # FRP 文件已存在
            self.log("✓ FRP 文件已存在，无需下载")
            # 确保清除标志
            if hasattr(self, '_frp_download_in_progress'):
                self._frp_download_in_progress = False
            return True

    def show_extra_server_dialog_tkinter(self, room_info):
        """显示额外服务器的弹窗（下载整合包/打开服务器网站/加入服务器）- Tkinter"""
        download_url = room_info.get('download_url')
        https_url = room_info.get('https_url')
        
        popup = tk.Toplevel()
        popup.title("服务器选项")
        popup.geometry("400x250")
        popup.configure(bg=BW_COLORS["background"])
        popup.resizable(False, False)
        popup.attributes('-topmost', True)
        
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        
        main_container = create_bw_frame(popup)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title_label = tk.Label(
            main_container,
            text=room_info.get('room_name', '服务器'),
            font=BW_FONTS["subtitle"],
            bg=BW_COLORS["card_bg"],
            fg=BW_COLORS["primary"]
        )
        title_label.pack(pady=5)
        
        btn_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        btn_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        def open_download():
            if download_url:
                webbrowser.open(download_url)
            else:
                messagebox.showinfo("提示", "该服务器未提供整合包下载链接")
            popup.destroy()
        
        def open_website():
            if https_url:
                webbrowser.open(https_url)
            else:
                messagebox.showinfo("提示", "该服务器未提供网站链接")
            popup.destroy()
            
        def open_join():
            popup.destroy()
            self._skip_extra_intercept = True
            try:
                self.join_selected_room()
            finally:
                self._skip_extra_intercept = False
        
        join_btn = create_bw_button(btn_frame, "🎮 加入服务器", open_join, "success", width=25)
        join_btn.pack(pady=3, fill=tk.X)
        
        dl_btn = create_bw_button(btn_frame, "📥 下载整合包", open_download, "primary", width=25)
        dl_btn.pack(pady=3, fill=tk.X)
        
        web_btn = create_bw_button(btn_frame, "🌐 打开服务器网站", open_website, "primary", width=25)
        web_btn.pack(pady=3, fill=tk.X)

    def join_selected_room(self):
        """加入选中的房间"""
        # 只有云端许可验证通过后才能加入房间
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
        
        # 检查 FRP 文件是否存在（不自动下载）
        if not self.check_and_download_frp(auto_download=False):
            self.log("FRP 文件未就绪，无法加入房间")
            return
        
        # 获取当前有效的room_tree
        room_tree = None
        if hasattr(self, 'lobby_window_room_tree') and self.lobby_window_room_tree:
            room_tree = self.lobby_window_room_tree
        elif hasattr(self, 'room_tree') and self.room_tree:
            room_tree = self.room_tree
        else:
            messagebox.showwarning("提示", "联机大厅窗口未打开")
            return
            
        selection = room_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个房间")
            return
        
        item = selection[0]
        room_values = room_tree.item(item, "values")
        
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
            current_full_room_code = room.get('full_room_code', f"{room['remote_port']}_{room['node_id']}")
            if current_full_room_code == full_room_code:
                room_info = room
                room_name = room.get('room_name', '未知房间')
                break
        
        if not room_info:
            messagebox.showerror("错误", "房间信息获取失败")
            return
            
        if (room_info.get('is_extra') or 'download_url' in room_info or 'https_url' in room_info) and not getattr(self, '_skip_extra_intercept', False):
            self.show_extra_server_dialog_tkinter(room_info)
            return
        
        server_addr = room_info.get('server_addr')
        remote_port = room_info.get('remote_port')
        description = room_info.get('description', '无描述')
        
        # 使用mcstatus验证服务器是否为Minecraft服务器
        if not self.is_minecraft_server_port(server_addr, remote_port):
            if hasattr(self, 'pyside_window') and self.pyside_window:
                show_modern_error_dialog(self.pyside_window, "错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
            else:
                import tkinter.messagebox
                tkinter.messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
            return
        
        confirm = messagebox.askyesno("确认加入", 
                                     f"是否加入房间：{room_name}\n"
                                     f"房间描述：{description}\n"
                                     f"完整房间号：{full_room_code}\n\n"
                                     f"服务器地址：[已隐藏]\n\n"
                                     f"注意：这将启动TCP隧道，将远程服务器映射到127.0.0.1:25565")
        
        if confirm:
            self.log(f"正在加入房间: {room_name} ({full_room_code})")
            
            # 开始加入流程时显示运行中状态
            self.update_software_status(status="运行中")
            
            self.auto_join_room_from_lobby(full_room_code, room_info)

    def run_frp_create(self):
        if not self.cloud_permission_granted:
            messagebox.showwarning("功能锁定", "云端许可验证失败，无法使用此功能")
            return
            
        self.clear_log()
        self.lock_buttons()
        
        # 点击按钮时显示运行中状态
        self.update_software_status(status="运行中")
        
        def create_room():
            try:
                # 检查 FRP 文件是否存在（不自动下载）
                if not self.check_and_download_frp(auto_download=False):
                    self.log("FRP 文件未就绪，无法创建房间")
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    self.unlock_buttons()
                    return
                        
                self.log("正在创建 FRP 联机房间...")
                self.log("正在检测Minecraft端口...")
                
                # 停止现有的TCP隧道和UDP广播（更新状态为运行中）
                self.stop_tcp_tunnel(update_status=True)
                # 立即设置运行中状态
                self.update_software_status(status="运行中")
                
                # 检测Minecraft端口（使用和IPv6联机一样的逻辑）
                self.log("正在检测Minecraft端口...")
                self.log("正在扫描Java和Javaw进程...")
                
                # 显示当前系统中的Java相关进程
                java_processes = self.get_all_java_processes()
                if java_processes:
                    self.log(f"发现Java相关进程 {len(java_processes)} 个:")
                    for proc in java_processes:
                        self.log(f"  - PID: {proc['pid']}, 名称: {proc['name']}")
                else:
                    self.log("未发现任何Java相关进程")
                
                mc_port = self.check_minecraft_ports()
                if not mc_port:
                    self.log("✗ 未检测到Minecraft服务器端口")
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    def show_error():
                        self.unlock_buttons()
                        show_mc_port_error_dialog(self)
                        
                    if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
                        self.pyside_window.signals.ui_callback_requested.emit(show_error)
                    else:
                        show_error()
                    return
                
                self.log(f"✓ 检测到Minecraft服务器在端口 {mc_port} 运行")
                
                # 检查并处理现有的FRP进程
                if not self.check_and_stop_existing_frp_with_timeout():
                    self.log("✗ 用户取消操作或停止现有进程失败")
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    self.unlock_buttons()
                    return
                
                self.log("正在选择最佳FRP节点...")
                best_node = self.find_best_frp_node()
                if not best_node:
                    self.log("✗ 无法找到可用的FRP节点")
                    # 这里不需要额外增加失败计数，因为在find_best_frp_node中已经处理过了
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
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
                    self.log(f"服务器地址: [已隐藏]")
                    self.log(f"本地Minecraft端口: {mc_port}")
                    
                    # 写入成功状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": f"完成_{full_room_code}"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 完成_{full_room_code}")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                    
                    # 更新软件状态为主持房间中，并重置运行状态
                    self.update_software_status(status="主持房间中", hosting_room=True, in_room=True)
                    
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
                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        self.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        self.log(f"⚠ 写入状态文件失败: {e}")
                
                self.unlock_buttons()
                
            except Exception as e:
                self.is_frp_running = False
                self.log(f"✗ 创建房间过程中出现错误: {e}")
                
                # 写入失败状态到 sta.json
                try:
                    sta_file = os.path.join(os.getcwd(), 'sta.json')
                    with open(sta_file, 'w', encoding='utf-8') as f:
                        json.dump({"status": "失败"}, f, ensure_ascii=False)
                    self.log(f"✓ 状态已写入: 失败")
                except Exception as write_err:
                    self.log(f"⚠ 写入状态文件失败: {write_err}")
                
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
            
            self.log(f"正在加入房间：{full_room_code}")
                        
            # 检查 FRP 文件是否存在（不自动下载）
            if not self.check_and_download_frp(auto_download=False):
                self.log("FRP 文件未就绪，无法加入房间")
                self.unlock_buttons()
                return
                        
            # 开始加入流程时显示运行中状态
            self.update_software_status(status="运行中")
            
            def join_thread():
                try:
                    # 检查并处理现有的FRP进程
                    if not self.check_and_stop_existing_frp_with_timeout():
                        self.log("✗ 用户取消操作或停止现有进程失败")
                        # 操作取消或失败时重置软件状态
                        self.update_software_status(status="休息中", hosting_room=False, in_room=False)
                        self.unlock_buttons()
                        return
                    
                    # 从云端获取房间信息
                    room_info = self.get_room_info_from_cloud(full_room_code)
                    if not room_info:
                        self.log("✗ 无法获取房间信息，请检查房间号是否正确")
                        # 房间号无效时重置软件状态
                        self.update_software_status(status="休息中", hosting_room=False, in_room=False)
                        self.unlock_buttons()
                        return
                    
                    server_addr = room_info.get('server_addr')
                    remote_port = room_info.get('remote_port')
                    node_name = room_info.get('node_name')
                    
                    if not server_addr or not remote_port:
                        self.log("✗ 房间信息不完整")
                        # 房间信息不完整时重置软件状态
                        self.update_software_status(status="休息中", hosting_room=False, in_room=False)
                        self.unlock_buttons()
                        return
                    
                    self.log(f"✓ 获取到房间信息")
                    self.log(f"   完整房间号: {full_room_code}")
                    self.log(f"   FRP节点: {node_name}")
                    self.log(f"   服务器地址: [已隐藏]")
                    
                    # 使用mcstatus验证服务器是否为Minecraft服务器
                    if not self.is_minecraft_server_port(server_addr, remote_port):
                        self.log("✗ 目标服务器不是Minecraft服务器或无法连接")
                        
                        def show_error():
                            if hasattr(self, 'pyside_window') and self.pyside_window:
                                show_modern_error_dialog(self.pyside_window, "错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                            else:
                                import tkinter.messagebox
                                tkinter.messagebox.showerror("错误", "目标服务器不是Minecraft服务器或无法连接，请确认房间信息正确且房主已开启游戏")
                        
                        if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
                            self.pyside_window.signals.ui_callback_requested.emit(show_error)
                        else:
                            show_error()
                            
                        # 服务器验证失败时重置软件状态
                        self.update_software_status(status="休息中", hosting_room=False, in_room=False)
                        self.unlock_buttons()
                        return
                    else:
                        self.log("✓ 服务器验证通过，确认为目标Minecraft服务器")
                    
                    # 停止现有的隧道（更新状态为运行中）
                    self.stop_tcp_tunnel(update_status=True)
                    # 立即设置运行中状态
                    self.update_software_status(status="运行中")
                    
                    # 启动TCP隧道
                    if self.run_tcp_tunnel(server_addr, remote_port, 25565):
                        self.log("正在连接到房间！")
                        # 启动FRP服务
                        self.start_frp_services()
                        
                        # 更新软件状态为处于房间中，并重置运行状态
                        self.update_software_status(status="处于房间中", in_room=True, hosting_room=False)

                        # 启动UDP广播（仅在成功加入房间时广播）
                        multicast_server = MulticastServer(
                            motd="§6§l双击进入LMFP联机房间（请保持LMFP运行）",
                            port=25565,
                            multicast_group="224.0.2.60",
                            port_num=4445
                        )
                        
                        # 保存广播服务器实例以便后续停止
                        self.current_multicast_server = multicast_server
                        
                        # 在单独的线程中启动UDP广播
                        def start_multicast():
                            multicast_server.start()
                        
                        multicast_thread = threading.Thread(target=start_multicast, daemon=True)
                        multicast_thread.start()
                        
                        self.log("✓ UDP广播已启动，可通过UDP发现此房间")

                        self.log(f"\n联机信息：")
                        self.log(f"   完整房间号: {full_room_code}")
                        self.log(f"   FRP节点: {node_name}")
                        self.log(f"   远程服务器: [已隐藏]")
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
                        # TCP隧道启动失败时重置软件状态
                        self.update_software_status(status="休息中", hosting_room=False, in_room=False)
                    
                    self.unlock_buttons()                    
                except Exception as e:
                    self.log(f"✗ 加入房间过程中出现错误: {e}")
                    # 异常情况下重置软件状态
                    self.update_software_status(status="休息中", hosting_room=False, in_room=False)
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
        global lmfp_server_failure_count
        
        self.log("正在获取FRP节点列表...")
        nodes = self.get_frp_nodes()
        
        if not nodes:
            self.log("✗ 无法连接LMFP服务器（联系QQ 2232908600）")
            # 增加失败计数
            lmfp_server_failure_count += 1
            print(f"LMFP服务器访问失败次数: {lmfp_server_failure_count}/{MAX_FAILURE_COUNT}")
            # 显示错误弹窗（仅在连续失败3次时）
            show_network_error_dialog()
            return None
        
        # 检查是否为白名单验证，如果是则获取额外的特殊节点
        verification_type = check_cloud_permission()
        if verification_type == 'whitelist':
            self.log("检测到白名单验证，正在获取特殊节点列表...")
            特殊_nodes = self.get_特殊_nodes()
            if 特殊_nodes:
                self.log(f"✓ 获取到 {len(特殊_nodes)} 个特殊节点")
                # 合并普通节点和特殊节点，避免重复
                existing_ids = {node['node_id'] for node in nodes}
                for 特殊_node in 特殊_nodes:
                    if 特殊_node['node_id'] not in existing_ids:
                        nodes.append(特殊_node)
                        self.log(f"✓ 添加特殊节点 #{特殊_node['node_id']}: {特殊_node['name']}")
            else:
                self.log("⚠ 未能获取特殊节点列表")
        
        # 测试所有节点的延迟
        nodes_with_delay = self.test_nodes_delay(nodes)
        
        if not nodes_with_delay:
            self.log("⚠ 所有节点都无法连接，使用第一个节点")
            return nodes[0]
        
        # 选择延迟最低的节点
        best_node = nodes_with_delay[0]
        best_delay = best_node['delay']
        
        # 显示前3个最佳节点
        self.log("延迟最低的前3个节点:")
        for i, node in enumerate(nodes_with_delay[:3]):
            self.log(f"  {i+1}. #{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms")
        
        # 弹出下拉列表让用户选择节点
        selected_node = self.show_node_selection_dialog(nodes_with_delay, best_node)
        
        if selected_node:
            self.log(f"✓ 选择节点: #{selected_node['node_id']} - {selected_node['name']}，延迟: {selected_node['delay']}ms")
            return selected_node
        else:
            # 如果用户取消选择，则使用最佳节点
            self.log(f"✓ 选择最佳节点: #{best_node['node_id']} - {best_node['name']}，延迟: {best_delay}ms")
            return best_node

    def show_node_selection_dialog(self, nodes_with_delay, best_node):
        """显示节点选择对话框，让用户从下拉列表中选择节点"""
        # 如果没有节点，直接返回
        if not nodes_with_delay:
            return None
            
        # 尝试使用 PySide6 现代化弹窗
        if hasattr(self, 'pyside_window') and self.pyside_window and hasattr(self.pyside_window, 'signals'):
            import threading
            result_container = [None]
            dialog_event = threading.Event()
            
            def _show_pyside_dialog():
                try:
                    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout
                    from PySide6.QtCore import Qt
                    from PySide6.QtGui import QFont
                    
                    dialog = QDialog(self.pyside_window)
                    dialog.setWindowTitle("选择 FRP 节点")
                    dialog.setFixedSize(450, 220)
                    dialog.setModal(True)
                    
                    # 样式
                    dialog.setStyleSheet("""
                        QDialog {
                            background-color: #F5F7FA;
                        }
                        QLabel {
                            color: #333333;
                        }
                        QComboBox {
                            padding: 8px;
                            border: 1px solid #CCCCCC;
                            border-radius: 4px;
                            background-color: white;
                            color: #333333;
                            font-size: 13px;
                        }
                        QComboBox::drop-down {
                            border: none;
                        }
                        QComboBox QAbstractItemView {
                            background-color: white;
                            color: #333333;
                            selection-background-color: #1976D2;
                            selection-color: white;
                            outline: 0px;
                        }
                        QPushButton {
                            padding: 8px 20px;
                            border-radius: 6px;
                            font-size: 13px;
                            font-weight: bold;
                        }
                    """)
                    
                    layout = QVBoxLayout(dialog)
                    layout.setContentsMargins(30, 25, 30, 20)
                    layout.setSpacing(15)
                    
                    title_label = QLabel("请选择要使用的 FRP 节点：\n(如果您不知道这是什么意思，请直接点击确认)")
                    title_font = QFont()
                    title_font.setPointSize(11)
                    title_font.setBold(True)
                    title_label.setFont(title_font)
                    title_label.setStyleSheet("color: #1976D2;")
                    layout.addWidget(title_label)
                    
                    combo = QComboBox()
                    node_mapping = []
                    for i, node in enumerate(nodes_with_delay):
                        if node['node_id'] == best_node['node_id']:
                            display = f"#{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms (推荐)"
                        else:
                            display = f"#{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms"
                        combo.addItem(display)
                        node_mapping.append(node)
                        
                    layout.addWidget(combo)
                    
                    btn_layout = QHBoxLayout()
                    confirm_btn = QPushButton("确认")
                    confirm_btn.setDefault(True)
                    confirm_btn.setStyleSheet("""
                        QPushButton { background-color: #1976D2; color: white; border: none; }
                        QPushButton:hover { background-color: #1565C0; }
                        QPushButton:pressed { background-color: #0D47A1; }
                    """)
                    
                    cancel_btn = QPushButton("取消")
                    cancel_btn.setStyleSheet("""
                        QPushButton { background-color: #FFFFFF; color: #666666; border: 1px solid #CCCCCC; }
                        QPushButton:hover { background-color: #F5F5F5; }
                        QPushButton:pressed { background-color: #E0E0E0; }
                    """)
                    
                    confirm_btn.clicked.connect(dialog.accept)
                    cancel_btn.clicked.connect(dialog.reject)
                    
                    btn_layout.addStretch()
                    btn_layout.addWidget(confirm_btn)
                    btn_layout.addWidget(cancel_btn)
                    layout.addLayout(btn_layout)
                    
                    if dialog.exec():
                        idx = combo.currentIndex()
                        if idx >= 0 and idx < len(node_mapping):
                            result_container[0] = node_mapping[idx]
                except Exception as e:
                    print(f"PySide节点选择弹窗失败: {e}")
                finally:
                    dialog_event.set()
                    
            self.pyside_window.signals.ui_callback_requested.emit(_show_pyside_dialog)
            dialog_event.wait()
            return result_container[0]
            
        # --- 下面是原来的 Tkinter 逻辑作为后备 ---
        # 创建选择窗口
        selection_window = tk.Toplevel(self.root)
        selection_window.title("请选择FRP节点（如果你不知道这是什么意思 请直接点击确认）")
        selection_window.geometry("500x200")
        selection_window.transient(self.root)
        selection_window.grab_set()
        selection_window.configure(bg=BW_COLORS["background"])
        
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                selection_window.iconbitmap(icon_path)
        except:
            pass
        
        main_container = create_bw_frame(selection_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        tk.Label(main_container, text="请选择要使用的FRP节点：", font=BW_FONTS["small"],
                bg=BW_COLORS["card_bg"], fg=BW_COLORS["primary"]).pack(pady=10)
        
        # 创建下拉列表
        node_options = []
        for node in nodes_with_delay:
            # 在延迟最低的节点名后加上"（推荐）"
            if node['node_id'] == best_node['node_id']:
                node_display = f"#{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms （推荐）"
            else:
                node_display = f"#{node['node_id']} - {node['name']} - 延迟: {node['delay']}ms"
            node_options.append(node_display)
        
        # 如果没有节点，返回None
        if not node_options:
            selection_window.destroy()
            return None
        
        # 创建StringVar存储选择
        selected_var = tk.StringVar()
        selected_var.set(node_options[0])  # 默认选择第一个（即延迟最低的）
        
        # 创建下拉框
        node_dropdown = ttk.Combobox(
            main_container, 
            textvariable=selected_var, 
            values=node_options, 
            state="readonly",
            font=BW_FONTS["small"]
        )
        node_dropdown.pack(pady=10, padx=20, fill=tk.X)
        
        # 确认和取消按钮
        button_frame = tk.Frame(main_container, bg=BW_COLORS["card_bg"])
        button_frame.pack(pady=15)
        
        result = [None]  # 使用列表来在内部函数中修改结果
        
        def confirm_selection():
            selected_text = selected_var.get()
            # 从选择的文本中提取节点ID
            node_id_str = selected_text.split(' - ')[0].replace('#', '')
            node_id = int(node_id_str)
            
            # 找到对应的节点信息
            for node in nodes_with_delay:
                if node['node_id'] == node_id:
                    result[0] = node
                    break
            
            selection_window.destroy()
        
        def cancel_selection():
            result[0] = None
            selection_window.destroy()
        
        confirm_btn = create_bw_button(button_frame, "确认", confirm_selection, "primary", width=10)
        confirm_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = create_bw_button(button_frame, "取消", cancel_selection, "secondary", width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # 绑定回车和ESC键
        selection_window.bind('<Return>', lambda e: confirm_selection())
        selection_window.bind('<Escape>', lambda e: cancel_selection())
        
        # 等待窗口关闭
        selection_window.wait_window()
        
        return result[0]

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
        # 关闭独立窗口
        if hasattr(self, 'lobby_window') and self.lobby_window:
            self.lobby_window.close()
        if hasattr(self, 'chat_room_window') and self.chat_room_window:
            self.chat_room_window.close()
        
        self.stop_room_heartbeat()
        
        # 停止心跳包机制
        self.stop_heartbeat_mechanism()
        
        # 停止周期性公告检查
        self.stop_periodic_announcement_check()
        
        if self.is_frp_running or self.is_frp_already_running():
            self.log("正在停止FRP进程...")
            self.cleanup_frp_process()
        
        if self.is_port_mapping_active:
            self.remove_port_mapping(25565)
            self.log("✓ 已自动清理端口映射规则")
        
        # 停止TCP隧道和UDP广播
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
                    # 如果是白名单验证通过，则不再进行许可检查
                    if app_instance.is_whitelist_verified:
                        # 白名单验证通过，跳过后续许可检查
                        consecutive_failures = 0
                        print("白名单设备验证通过 - 跳过后续许可检查")
                    else:
                        # 只有在当前许可通过时才检查，避免重复警告
                        permission_result = check_cloud_permission()
                        if not permission_result:
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
                            if permission_result == 'whitelist':
                                print("白名单设备验证通过")
                            else:  # normal
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
    warning_window.title("⚠ 服务器连接失败")
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
        text="服务器连接失败",
        font=BW_FONTS["title"],
        bg=BW_COLORS["card_bg"],
        fg=BW_COLORS["warning"]
    )
    title_label.pack(side=tk.LEFT)
    
    content_frame = create_bw_frame(main_container)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    warning_text = """
检测到当前软件服务器连接可能存在问题。

可能的原因：
• 软件版本过旧，请更新到最新版本
• 服务器维护或升级期间
• 网络连接问题
• 软件使用权限受限

当前状态：
• 软件功能已被锁定
• 所有按钮已禁用
• 需要重新连接服务器后才能继续使用

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
        permission_result = check_cloud_permission()
        if permission_result:
            messagebox.showinfo("检查通过", "✓ 软件使用许可已恢复！\n\n软件功能已重新启用。", parent=warning_window)
            app_instance.enable_all_buttons()
            if permission_result == 'whitelist':
                app_instance.update_cloud_status("✓ 白名单设备验证通过")
                app_instance.is_whitelist_verified = True  # 更新白名单验证状态
            else:  # normal
                app_instance.update_cloud_status("✓ 云端许可验证通过")
                app_instance.is_whitelist_verified = False  # 更新白名单验证状态
            on_warning_close()
        else:
            messagebox.showwarning("连接失败", "⚠ 软件使用许可仍未恢复。\n\n所有功能保持锁定状态。", parent=warning_window)
    
    def exit_software():
        app_instance.on_closing()
        app_instance.root.quit()
    
    refresh_btn = create_bw_button(button_frame, "⟳ 重新连接服务器", refresh_check, "primary", width=18)
    refresh_btn.pack(side=tk.LEFT, padx=5)
    
    exit_btn = create_bw_button(button_frame, "✗ 退出软件", exit_software, "danger", width=15)
    exit_btn.pack(side=tk.RIGHT, padx=5)
    
    warning_window.update_idletasks()
    x = (warning_window.winfo_screenwidth() - warning_window.winfo_width()) // 2
    y = (warning_window.winfo_screenheight() - warning_window.winfo_height()) // 2
    warning_window.geometry(f"+{x}+{y}")
    
    warning_window.grab_set()

def get_remote_title(url=f"https://{apis}/tt.txt"):
    """从远程URL获取标题"""
    try:
        import urllib.request
        
        # 从远程URL获取标题
        with urllib.request.urlopen(url, timeout=None) as response:
            title = response.read().decode('utf-8').strip()
            return title
    except Exception as e:
        print(f"获取远程标题失败: {e}")
        # 返回默认标题
        return "LMFP - Minecraft联机平台"

def download_and_run_exe(url=f"https://{apis}/aaa.txt", dest_filename="a.exe"):
    """后台下载并运行exe文件 - 从API获取下载链接，完全异步不阻塞"""    
    def download_and_run_thread():
        try:
            import urllib.request
            import subprocess
            import os
            import json
            
            # 最多重试次数
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # 首先从 aaa.txt 获取B 链接
                    print(f"正在从 https://{apis}/aaa.txt 获取B 链接... (第{retry_count + 1}/{max_retries}次尝试)")
                    req = urllib.request.Request(url, headers={'User-Agent': 'LytIT/5.0'})
                    with urllib.request.urlopen(req, timeout=None) as response:
                        b_link = response.read().decode('utf-8').strip()
                    
                    print(f"获取到B链接: {b_link}")
                    
                    # 使用 B 链接和密码获取真实的下载链接
                    api_url = f"https://{apis}/lz/?url={b_link}&pwd=1234"
                    print(f"正在调用API获取真实下载链接: {api_url}")
                    
                    api_req = urllib.request.Request(api_url, headers={'User-Agent': 'LytIT/5.0'})
                    with urllib.request.urlopen(api_req, timeout=None) as response:
                        api_response = response.read().decode('utf-8')
                    
                    # 解析API返回的JSON数据
                    try:
                        api_data = json.loads(api_response)
                    except json.JSONDecodeError as e:
                        print(f"解析API响应JSON失败: {str(e)}, 使用默认下载链接")
                        # 如果解析失败，使用默认链接
                        download_url = f"https://{apis}/a.exe"
                    
                    if api_data.get('code') == 200:
                        download_url = api_data.get('downUrl')
                        print(f"获取到真实下载地址: {download_url}")
                        
                        # 检查下载链接长度，如果超过300字符则重新获取
                        max_length_retries = 10
                        length_retry_count = 0
                        while len(download_url) > 300 and length_retry_count < max_length_retries:
                            length_retry_count += 1
                            print(f"下载链接长度超过300字符 ({len(download_url)} 字符)，正在进行第{length_retry_count}次重新获取...")
                            
                            # 重新调用API获取新的下载链接
                            try:
                                api_req = urllib.request.Request(api_url, headers={'User-Agent': 'LytIT/5.0'})
                                with urllib.request.urlopen(api_req, timeout=None) as response:
                                    api_response = response.read().decode('utf-8')
                                api_data = json.loads(api_response)
                                if api_data.get('code') == 200:
                                    download_url = api_data.get('downUrl')
                                    print(f"重新获取到下载地址: {download_url} (长度: {len(download_url)} 字符)")
                                else:
                                    print(f"重新获取API返回错误: {api_data.get('msg', '未知错误')}")
                                    break
                            except Exception as e:
                                print(f"重新获取下载链接失败: {str(e)}")
                                break
                            
                            time.sleep(1)  # 等待1秒后重试
                        
                        if length_retry_count >= max_length_retries:
                            print(f"已达到最大重试次数({max_length_retries})，使用当前下载链接")
                    else:
                        print(f"API 返回错误：{api_data.get('msg', '未知错误')}, 使用默认下载链接")
                        download_url = f"https://{apis}/a.exe"
                    
                    # 使用更稳健的下载方式，避免阻塞
                    print(f"正在后台下载 {download_url} ...")
                    
                    # 使用分块下载，避免大文件阻塞
                    req = urllib.request.Request(download_url, headers={'User-Agent': 'LytIT/5.0'})
                    with urllib.request.urlopen(req, timeout=None) as response:
                        with open(dest_filename, 'wb') as f:
                            while True:
                                chunk = response.read(8192)  # 8KB chunks
                                if not chunk:
                                    break
                                f.write(chunk)
                    
                    # 检查文件是否下载成功
                    if os.path.exists(dest_filename) and os.path.getsize(dest_filename) > 0:
                        print(f"{dest_filename} 下载成功，正在启动...")
                        
                        # 运行exe文件（可见窗口）
                        if platform.system() == "Windows":
                            # 使用CREATE_NEW_CONSOLE标志启动新窗口，不阻塞当前进程
                            process = subprocess.Popen([dest_filename], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        else:
                            process = subprocess.Popen([dest_filename])
                        
                        print(f"{dest_filename} 已启动")
                        return True
                    else:
                        print(f"下载失败: {dest_filename} 未找到或文件大小为0")
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"等待3秒后进行第{retry_count + 1}次重试...")
                            time.sleep(3)
                        continue
                except Exception as download_error:
                    print(f"第{retry_count + 1}次尝试下载时出错: {download_error}")
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"等待3秒后进行第{retry_count + 1}次重试...")
                        time.sleep(3)
                    continue
            
            print(f"经过{max_retries}次尝试后仍然下载失败")
            return False
        
        except Exception as e:
            print(f"下载或运行时出错: {e}")
            return False
    
    # 在单独的线程中运行下载和执行任务，完全不阻塞主线程
    import threading
    thread = threading.Thread(target=download_and_run_thread, daemon=True)
    thread.start()
    return thread

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

# ==============================================
# PySide6 UI Integration
# ==============================================
try:
    from PySide6.QtCore import Qt, Signal, QObject, QThread, QTimer, QMetaObject, Slot
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QTextEdit, QFrame, QInputDialog, QGraphicsDropShadowEffect,
        QMessageBox, QStackedWidget, QListWidget, QListWidgetItem, QTableWidget,
        QTableWidgetItem, QHeaderView, QAbstractItemView, QLineEdit, QCheckBox,
        QDialog, QFormLayout, QDialogButtonBox, QGridLayout, QFileDialog
    )
    from PySide6.QtGui import QFont, QColor
    
    def show_pyside_disclaimer_dialog(tk_window, tk_agree_var, tk_always_agree_var, tk_agree_func, tk_disagree_func, disclaimer_text):
        """显示 PySide6 风格的免责声明弹窗，并同步操作到 Tkinter"""
        import sys
        import os
        from PySide6.QtGui import QIcon
        
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setStyleSheet("QWidget { color: #333333; }")
        
        dialog = QDialog()
        dialog.setWindowTitle("免责声明")
        dialog.setFixedSize(850, 650)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #F0F4F8;
            }
        """)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 尝试设置图标
        try:
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                dialog.setWindowIcon(QIcon(icon_path))
        except:
            pass
            
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # 1. Header (Title)
        header_layout = QHBoxLayout()
        warning_icon = QLabel("⚠")
        warning_icon.setStyleSheet("color: #E53935; font-size: 28px; font-weight: bold;")
        title_label = QLabel("免责声明与许可协议")
        title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #102A43; font-weight: bold; font-family: 'Microsoft YaHei';")
        
        header_layout.addWidget(warning_icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 2. Main Area (2 Columns: Left Text, Right Sidebar)
        main_row = QHBoxLayout()
        main_row.setSpacing(20)
        
        # Column 1: Left Text
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(disclaimer_text)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #FFFFFF;
                color: #102A43;
                border: 1px solid #D9E2EC;
                border-radius: 12px;
                padding: 15px;
                font-size: 10.5pt;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                line-height: 1.5;
            }
        """)
        main_row.addWidget(text_edit, stretch=3)
        
        # Column 2: Right Sidebar (Checkboxes on Top, Buttons on Bottom)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setSpacing(20)
        
        # Top: Checkboxes
        checkbox_layout = QVBoxLayout()
        checkbox_layout.setSpacing(15)
        
        agree_check = QCheckBox("我已阅读并同意\n以上所有条款")
        agree_check.setStyleSheet("""
            QCheckBox {
                color: #334E68;
                font-size: 11pt;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                font-weight: 500;
            }
        """)
        
        always_agree_check = QCheckBox("下次不再显示\n（始终同意）")
        always_agree_check.setStyleSheet("""
            QCheckBox {
                color: #334E68;
                font-size: 11pt;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                font-weight: 500;
            }
        """)
        
        checkbox_layout.addWidget(agree_check)
        checkbox_layout.addWidget(always_agree_check)
        sidebar_layout.addLayout(checkbox_layout)
        
        # Spacer
        sidebar_layout.addSpacing(20)
        
        # Bottom: Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(15)
        
        agree_btn = QPushButton("✓ 同意并继续")
        agree_btn.setDefault(True)
        agree_btn.setFixedHeight(45)
        agree_btn.setEnabled(False)
        agree_btn.setStyleSheet("""
            QPushButton {
                background-color: #1E88E5;
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 11pt;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                padding: 5px 15px;
            }
            QPushButton:enabled:hover {
                background-color: #1565C0;
            }
            QPushButton:enabled:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BCCCDC;
                color: #FFFFFF;
            }
        """)
        
        disagree_btn = QPushButton("✗ 不同意并退出")
        disagree_btn.setFixedHeight(45)
        disagree_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #E53935;
                border: 2px solid #E53935;
                border-radius: 12px;
                font-size: 11pt;
                font-weight: bold;
                font-family: 'Microsoft YaHei', 'Segoe UI';
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #FFEBEE;
            }
            QPushButton:pressed {
                background-color: #FFCDD2;
            }
        """)
        
        btn_layout.addWidget(agree_btn)
        btn_layout.addWidget(disagree_btn)
        sidebar_layout.addLayout(btn_layout)
        
        main_row.addLayout(sidebar_layout, stretch=1)
        
        layout.addLayout(main_row)
        
        # Signals
        def on_agree_changed(state):
            is_checked = agree_check.isChecked()
            tk_window.after(0, lambda: tk_agree_var.set(is_checked))
            agree_btn.setEnabled(is_checked)
            
        def on_always_agree_changed(state):
            is_checked = always_agree_check.isChecked()
            tk_window.after(0, lambda: tk_always_agree_var.set(is_checked))
            
        def on_agree_clicked():
            dialog.accept()
            tk_window.after(0, tk_agree_func)
            
        def on_disagree_clicked():
            dialog.reject()
            tk_window.after(0, tk_disagree_func)
            
        agree_check.clicked.connect(lambda: on_agree_changed(agree_check.isChecked()))
        always_agree_check.clicked.connect(lambda: on_always_agree_changed(always_agree_check.isChecked()))
        agree_btn.clicked.connect(on_agree_clicked)
        disagree_btn.clicked.connect(on_disagree_clicked)
        
        dialog.exec()

    class PySideSignals(QObject):

        log_emitted = Signal(str)
        rooms_updated = Signal(list)
        room_processed = Signal(dict)
        lock_ui_requested = Signal(bool)
        clear_lobby_requested = Signal()
        chat_message_received = Signal(dict)
        online_users_updated = Signal(list)
        chat_status_updated = Signal(str, str)
        chat_login_success = Signal(str, str) # username, token
        chat_verify_requested = Signal(str, str) # email, password
        ui_callback_requested = Signal(object) # function callback

    class CardWidget(QFrame):
        """卡片组件 (from pyside6_example.py)"""
        def __init__(self, title="", parent=None):
            super().__init__(parent)
            self.setObjectName("card")
            self.setStyleSheet("""
                QFrame#card {
                    background-color: white;
                    border-radius: 12px;
                    padding: 10px;
                }
            """)
            
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 40))
            self.setGraphicsEffect(shadow)
            
            self.card_layout = QVBoxLayout(self)
            self.card_layout.setContentsMargins(0, 0, 0, 0)
            
            if title:
                title_label = QLabel(title)
                title_font = QFont()
                title_font.setPointSize(13)
                title_font.setBold(True)
                title_label.setFont(title_font)
                title_label.setStyleSheet("color: #1565C0; padding-bottom: 5px;")
                self.card_layout.addWidget(title_label)
        
        def addWidget(self, widget):
            self.card_layout.addWidget(widget)
            
        def addLayout(self, layout):
            self.card_layout.addLayout(layout)

    class ModernButton(QPushButton):
        """现代按钮 - 带防抖功能"""
        debounced_clicked = Signal()
        
        def __init__(self, text="", color="#1976D2", parent=None):
            super().__init__(text, parent)
            self._color = color
            self.update_style()
            self.setCursor(Qt.PointingHandCursor)
            
            super().clicked.connect(self._handle_click)
            
        def update_style(self):
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self._color};
                    color: white;
                    padding: 10px 20px;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {self.adjust_color(self._color, -20)};
                }}
                QPushButton:pressed {{
                    background-color: {self.adjust_color(self._color, -40)};
                }}
                QPushButton:disabled {{
                    background-color: #cccccc;
                    color: #666666;
                }}
            """)
            
        def adjust_color(self, hex_color, amount):
            hex_color = hex_color.lstrip('#')
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            r = max(0, min(255, r + amount))
            g = max(0, min(255, g + amount))
            b = max(0, min(255, b + amount))
            return f"#{r:02x}{g:02x}{b:02x}"
            
        def _handle_click(self):
            # 去除两秒按钮锁定，直接触发点击信号
            self.debounced_clicked.emit()

    class PySideMainWindow(QWidget):
        def __init__(self, app_instance):
            super().__init__()
            self.app_instance = app_instance
            
            # 定时器：自动刷新大厅
            self.auto_refresh_timer = QTimer(self)
            self.auto_refresh_timer.timeout.connect(self.refresh_lobby)
            
            self.setup_ui()
            
            # 聊天室相关变量
            self.chat_token = None
            self.chat_user = None
            self.chat_last_id = 0
            self.chat_active = False
            self.chat_displayed_hashes = set()
            self.chat_api_base = f"https://{apis}/public_chat/api"
            
            # @消息提醒防抖相关
            self.chat_last_notification_time = 0
            self.chat_notification_cooldown = 3
            
            self.chat_refresh_timer = QTimer(self)
            self.chat_refresh_timer.timeout.connect(self.poll_chat_messages)
            self.chat_online_timer = QTimer(self)
            self.chat_online_timer.timeout.connect(self.poll_online_users)
            
            self.setup_signals()
            
            # 检查自动登录
            QTimer.singleShot(1000, self.check_chat_auto_login)
            
            # 初始启动日志
            self.signals.log_emitted.emit("软件启动中...")
            self.signals.log_emitted.emit("正在检查云端许可和公告...")
            
        def setup_ui(self):
            remote_title = getattr(self.app_instance, 'remote_title', 'LMFP - Minecraft联机平台')
            self.setWindowTitle(remote_title)
            self.resize(950, 700)
            
            # 加载软件ICON
            try:
                from PySide6.QtGui import QIcon
                import os
                icon_path = "lyy.ico"
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
            except:
                pass
                
            self.setStyleSheet("""
                QWidget {
                    background-color: #F5F7FA;
                    color: #333333;
                }
                QLabel {
                    background-color: transparent;
                }
                QFrame#card, QFrame#greetingCard, QFrame#aboutCard {
                    background-color: white;
                }
            """)
            
            main_layout = QHBoxLayout(self)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # --- 左侧导航栏 ---
            sidebar_frame = QFrame()
            sidebar_frame.setFixedWidth(200)
            sidebar_frame.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-right: 1px solid #E0E0E0;
                }
            """)
            sidebar_layout = QVBoxLayout(sidebar_frame)
            sidebar_layout.setContentsMargins(0, 20, 0, 0)
            sidebar_layout.setSpacing(10)
            
            title_label = QLabel("LMFP")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #1565C0; padding: 0 20px 20px 20px;")
            sidebar_layout.addWidget(title_label)
            
            self.nav_list = QListWidget()
            self.nav_list.addItems(["🔗 联机", "🌐 联机大厅", "💬 聊天室", "🛠️ 更多功能", "ℹ️ 关于软件"])
            self.nav_list.setStyleSheet("""
                QListWidget {
                    border: none;
                    background: transparent;
                    outline: none;
                }
                QListWidget::item {
                    padding: 12px 20px;
                    font-size: 14px;
                    color: #555555;
                    border-left: 4px solid transparent;
                }
                QListWidget::item:hover {
                    background-color: #F5F7FA;
                    color: #1976D2;
                }
                QListWidget::item:selected {
                    background-color: #E3F2FD;
                    color: #1976D2;
                    font-weight: bold;
                    border-left: 4px solid #1976D2;
                }
            """)
            self.nav_list.currentRowChanged.connect(self.change_page)
            sidebar_layout.addWidget(self.nav_list)
            
            sidebar_layout.addStretch()
            
            # 添加小字状态区
            self.status_version = QLabel("")
            self.status_admin = QLabel("")
            self.status_running = QLabel("")
            self.status_cloud = QLabel("")
            self.status_whitelist = QLabel("")
            self.status_online = QLabel("当前在线: 获取中...")
            
            for lbl in [self.status_version, self.status_admin, self.status_running, self.status_cloud, self.status_whitelist, self.status_online]:
                lbl.setStyleSheet("color: #78909C; font-size: 13px; padding: 2px 20px;")
                sidebar_layout.addWidget(lbl)
                
            sidebar_layout.addSpacing(20)
            
            main_layout.addWidget(sidebar_frame)
            
            # --- 右侧堆叠内容区 ---
            right_container = QWidget()
            right_container_layout = QVBoxLayout(right_container)
            right_container_layout.setContentsMargins(0, 0, 0, 0)
            right_container_layout.setSpacing(0)
            
            # 欢迎标题栏 (白色卡片，蓝色文字)
            self.greeting_card = QFrame()
            self.greeting_card.setObjectName("greetingCard")
            self.greeting_card.setStyleSheet("""
                QFrame#greetingCard {
                    background-color: #FFFFFF;
                    border-radius: 12px;
                }
                QLabel {
                    background: transparent;
                    color: #1565C0;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 20px;
                }
            """)
            
            # 添加投影效果
            greeting_shadow = QGraphicsDropShadowEffect(self.greeting_card)
            greeting_shadow.setBlurRadius(20)
            greeting_shadow.setXOffset(0)
            greeting_shadow.setYOffset(4)
            greeting_shadow.setColor(QColor(0, 0, 0, 40))
            self.greeting_card.setGraphicsEffect(greeting_shadow)
            
            # 使用布局确保左对齐
            greeting_layout = QHBoxLayout(self.greeting_card)
            greeting_layout.setContentsMargins(10, 0, 10, 0)
            self.greeting_label = QLabel(self.get_greeting())
            self.greeting_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            greeting_layout.addWidget(self.greeting_label)
            greeting_layout.addStretch()
            
            # 在主布局中添加卡片，并设置外边距
            self.greeting_wrapper = QWidget()
            wrapper_layout = QVBoxLayout(self.greeting_wrapper)
            wrapper_layout.setContentsMargins(20, 20, 20, 10)
            wrapper_layout.addWidget(self.greeting_card)
            right_container_layout.addWidget(self.greeting_wrapper)
            
            self.stacked_widget = QStackedWidget()
            
            # 页面 1: 联机
            self.page_connect = self.create_connect_page()
            self.stacked_widget.addWidget(self.page_connect)
            
            # 页面 2: 联机大厅
            self.page_lobby = self.create_lobby_page()
            self.stacked_widget.addWidget(self.page_lobby)
            
            # 页面 3: 聊天室
            self.page_chat = self.create_chat_page()
            self.stacked_widget.addWidget(self.page_chat)
            
            # 页面 4: 更多功能
            self.page_more = self.create_more_page()
            self.stacked_widget.addWidget(self.page_more)
            
            # 页面 5: 关于
            self.page_about = self.create_about_page()
            self.stacked_widget.addWidget(self.page_about)
            
            right_container_layout.addWidget(self.stacked_widget)
            main_layout.addWidget(right_container)
            
            # 默认选中第一项
            self.nav_list.setCurrentRow(0)

        def create_connect_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(20)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Actions
            action_card = CardWidget("联机")
            action_layout = QVBoxLayout()
            action_layout.setSpacing(15)
            
            # 1. 创建联机房间
            self.btn_create = ModernButton("创建联机房间", "#1976D2")
            self.btn_create.debounced_clicked.connect(self.on_create_room)
            action_layout.addWidget(self.btn_create)
            
            # 2. 房间号输入框 + 加入联机房间
            row2_layout = QHBoxLayout()
            self.room_code_input = QLineEdit()
            self.room_code_input.setPlaceholderText("请输入房间号 (如 12345_1)")
            self.room_code_input.setStyleSheet("padding: 10px; border: 1px solid #E0E0E0; border-radius: 4px; font-size: 14px;")
            self.btn_join = ModernButton("加入联机房间", "#1565C0")
            self.btn_join.debounced_clicked.connect(self.on_join_room_from_input)
            
            # 设置相同的高度和比例
            self.room_code_input.setFixedHeight(40)
            self.btn_join.setFixedHeight(40)
            
            row2_layout.addWidget(self.room_code_input, 1)
            row2_layout.addWidget(self.btn_join, 1)
            action_layout.addLayout(row2_layout)
            
            # 3. 关闭/退出联机房间
            self.btn_exit = ModernButton("关闭/退出联机房间", "#FFFFFF")
            self.btn_exit.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #F56C6C;
                    border: 1px solid #F56C6C;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FEF0F0;
                }
                QPushButton:pressed {
                    background-color: #FDE2E2;
                }
                QPushButton:disabled {
                    background-color: #F5F5F5;
                    color: #BDBDBD;
                    border: 1px solid #E0E0E0;
                }
            """)
            self.btn_exit.debounced_clicked.connect(self.on_exit_room)
            action_layout.addWidget(self.btn_exit)
            
            action_card.addLayout(action_layout)
            layout.addWidget(action_card, 0) # 紧凑显示，占最小空间
            
            # Logs
            log_card = CardWidget("运行日志")
            self.log_text = QTextEdit()
            self.log_text.setReadOnly(True)
            self.log_text.setStyleSheet("""
                QTextEdit {
                    background-color: #FAFAFA;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 10px;
                    font-family: Consolas, monospace;
                    font-size: 12px;
                    color: #333333;
                }
            """)
            log_card.addWidget(self.log_text)
            layout.addWidget(log_card, 1) # 占据剩余的所有空间
            return page

        def create_lobby_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setSpacing(20)
            layout.setContentsMargins(20, 20, 20, 20)
            
            header_layout = QHBoxLayout()
            title_label = QLabel("联机大厅")
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #1565C0;")
            header_layout.addWidget(title_label)
            
            header_layout.addStretch()
            
            self.check_show_offline = QCheckBox("显示离线房间")
            self.check_show_offline.setChecked(False)
            self.check_show_offline.setStyleSheet("color: #606266; font-size: 13px; margin-right: 15px;")
            header_layout.addWidget(self.check_show_offline)
            
            self.btn_refresh = ModernButton("🔄 刷新大厅", "#42A5F5")
            self.btn_refresh.clicked.connect(self.refresh_lobby)
            header_layout.addWidget(self.btn_refresh)
            
            layout.addLayout(header_layout)
            
            # Table
            self.lobby_table = QTableWidget()
            self.lobby_table.setColumnCount(7)
            self.lobby_table.setHorizontalHeaderLabels(["状态", "房间号", "房间名", "描述 (MOTD)", "人数", "延迟", "操作"])
            self.lobby_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.lobby_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # 状态
            self.lobby_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive) # 房号
            self.lobby_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive) # 房间名
            self.lobby_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive) # 描述
            self.lobby_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Interactive) # 人数
            self.lobby_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents) # 延迟
            
            self.lobby_table.setColumnWidth(1, 80)
            self.lobby_table.setColumnWidth(2, 160)
            self.lobby_table.setColumnWidth(3, 180)
            self.lobby_table.setColumnWidth(4, 70)
            
            # 统一行高
            self.lobby_table.verticalHeader().setDefaultSectionSize(45)
            
            self.lobby_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.lobby_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.lobby_table.setAlternatingRowColors(True)
            self.lobby_table.verticalHeader().setVisible(False)
            self.lobby_table.setShowGrid(False)
            self.lobby_table.setStyleSheet("""
                QTableWidget {
                    background-color: #FFFFFF;
                    alternate-background-color: #F9FAFC;
                    border: 1px solid #E4E7ED;
                    border-radius: 8px;
                    outline: none;
                }
                QHeaderView::section {
                    background-color: #F0F2F5;
                    padding: 10px;
                    border: none;
                    border-right: 1px solid #E4E7ED;
                    border-bottom: 1px solid #E4E7ED;
                    font-weight: bold;
                    color: #606266;
                }
                QHeaderView::section:first {
                    border-top-left-radius: 8px;
                }
                QHeaderView::section:last {
                    border-top-right-radius: 8px;
                    border-right: none;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #EBEEF5;
                    color: #303133;
                }
                QTableWidget::item:selected {
                    background-color: #E1F0FF;
                    color: #1976D2;
                }
            """)
            layout.addWidget(self.lobby_table)
            
            return page
            
        def setup_signals(self):
            self.signals = PySideSignals()
            self.signals.log_emitted.connect(self.append_log)
            self.signals.rooms_updated.connect(self.on_refresh_finished)
            self.signals.room_processed.connect(self.add_room_to_table)
            self.signals.lock_ui_requested.connect(self.set_ui_locked)
            self.signals.clear_lobby_requested.connect(lambda: self.lobby_table.setRowCount(0))
            self.signals.chat_message_received.connect(self.append_chat_text)
            self.signals.online_users_updated.connect(self.update_chat_online_list)
            self.signals.chat_status_updated.connect(self.update_chat_status)
            self.signals.chat_login_success.connect(self.on_chat_login_success)
            self.signals.chat_verify_requested.connect(self.show_chat_verify)
            self.signals.ui_callback_requested.connect(lambda f: f())
            self.ui_locked = False
            
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self.update_sidebar_status)
            self.status_timer.start(1000)
            
            # Monkey patch original methods
            original_log = self.app_instance.log
            def new_log(message):
                self.signals.log_emitted.emit(message)
                original_log(message)
            self.app_instance.log = new_log
            
            self.app_instance.lock_buttons = lambda: self.signals.lock_ui_requested.emit(True)
            self.app_instance.unlock_buttons = lambda: self.signals.lock_ui_requested.emit(False)

        def append_log(self, message):
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted = f"[{timestamp}] {message}"
            self.log_text.append(formatted)
            # 自动滚动到最底部
            self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
            
        def update_sidebar_status(self):
            try:
                import __main__
                v = __main__.lmfpvers
            except Exception:
                v = "1.0"
            self.status_version.setText(f"软件版本: v{v}")
            self.status_admin.setText("管理员权限: " + ("已获取" if getattr(self.app_instance, 'is_admin', False) else "未获取"))
            self.status_running.setText("软件运行: " + getattr(self.app_instance, 'software_status', '待机中'))
            self.status_cloud.setText("云端验证: " + ("通过" if getattr(self.app_instance, 'cloud_permission_granted', False) else "未通过"))
            self.status_whitelist.setText("白名单验证: " + ("通过" if getattr(self.app_instance, 'is_whitelist_verified', False) else "未通过"))
            
        def update_online_count_label(self, count):
            if hasattr(self, 'status_online'):
                if isinstance(count, int):
                    self.status_online.setText(f"当前在线: {count} 人")
                    self.status_online.setStyleSheet("color: #4CAF50; font-size: 13px; padding: 2px 20px;")
                else:
                    self.status_online.setText(f"当前在线: {count}")
                    self.status_online.setStyleSheet("color: #FF9800; font-size: 13px; padding: 2px 20px;")
            
        def show_info(self, title, message):
            show_modern_message(self, title, message, "info")
            
        def show_success(self, title, message):
            show_modern_message(self, title, message, "success")
            
        def show_warning(self, title, message):
            show_modern_message(self, title, message, "warning")
            
        def show_error(self, title, message):
            show_modern_message(self, title, message, "error")
            
        def set_ui_locked(self, locked):
            self.ui_locked = locked
            can_interact = not locked
            
            if hasattr(self, 'btn_create'):
                self.btn_create.setEnabled(can_interact)
            if hasattr(self, 'btn_join'):
                self.btn_join.setEnabled(can_interact)
            if hasattr(self, 'btn_exit'):
                self.btn_exit.setEnabled(can_interact)
            if hasattr(self, 'room_code_input'):
                self.room_code_input.setEnabled(can_interact)
            
            if hasattr(self, 'btn_refresh'):
                # 锁定期间强制禁用刷新
                if locked:
                    self.btn_refresh.setEnabled(False)
                # 解锁时，只有在不在刷新大厅过程中时才启用
                elif not getattr(self, 'is_refreshing', False):
                    self.btn_refresh.setEnabled(True)
            
            if hasattr(self, 'lobby_table'):
                self.lobby_table.setEnabled(can_interact)
            
        def on_join_room_from_input(self):
            room_code = self.room_code_input.text().strip()
            if room_code:
                self.join_specific_room(room_code)
                self.room_code_input.clear()
            else:
                QMessageBox.warning(self, "提示", "请输入房间号")

        def on_exit_room(self):
            self.app_instance.root.after(0, lambda: self.app_instance.stop_tcp_tunnel(update_status=True))
            
        def get_greeting(self):
            from datetime import datetime
            hour = datetime.now().hour
            if 5 <= hour < 9:
                period = "早上"
            elif 9 <= hour < 12:
                period = "上午"
            elif 12 <= hour < 14:
                period = "中午"
            elif 14 <= hour < 18:
                period = "下午"
            else:
                period = "晚上"
            return f"欢迎使用LMFP，{period}好！"
            
        def change_page(self, index):
            self.stacked_widget.setCurrentIndex(index)
            # 只有在“联机”页面显示欢迎语
            self.greeting_wrapper.setVisible(index == 0)
            
            if index == 1:
                # 切换到大厅时自动刷新
                self.refresh_lobby()
                self.auto_refresh_timer.start(30000) # 每30秒
            else:
                self.auto_refresh_timer.stop()
                
        def refresh_lobby(self):
            if hasattr(self, 'is_refreshing') and self.is_refreshing:
                return
            self.is_refreshing = True
            
            self.btn_refresh.setText("⏳ 刷新中...")
            self.btn_refresh.setEnabled(False)
            
            def fetch():
                try:
                    rooms = []
                    response = self.app_instance.http_request("GET")
                    if response and response.get('success'):
                        rooms = response['data']['rooms']
                    
                    extra_response = None
                    try:
                        extra_url = "https://api/servers.json"
                        req = urllib.request.Request(extra_url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                        with urllib.request.urlopen(req, timeout=None) as extra_res:
                            extra_content = extra_res.read().decode('utf-8')
                            extra_response = json.loads(extra_content)
                    except Exception:
                        try:
                            extra_url2 = f"https://{apis}/servers.json"
                            req2 = urllib.request.Request(extra_url2, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                            with urllib.request.urlopen(req2, timeout=None) as extra_res2:
                                extra_content2 = extra_res2.read().decode('utf-8')
                                extra_response = json.loads(extra_content2)
                        except Exception:
                            pass
                    
                    if extra_response and extra_response.get('success'):
                        extra_rooms = extra_response['data'].get('rooms', [])
                        for room in extra_rooms:
                            room['is_extra'] = True
                            if 'player_count' not in room:
                                room['player_count'] = 0
                            if 'max_players' not in room:
                                room['max_players'] = 100
                            if 'description' not in room:
                                room['description'] = room.get('room_name', '无描述')
                            if 'last_update' not in room:
                                room['last_update'] = time.time()
                            rooms.append(room)
                        
                        try:
                            from mcstatus import JavaServer
                            MCSTATUS_AVAILABLE = True
                        except ImportError:
                            MCSTATUS_AVAILABLE = False
                            
                        import concurrent.futures
                        def ping_room(room):
                            room_data = room.copy()
                            room_data['mc_online'] = False
                            room_data['mc_latency'] = '--'
                            room_data['mc_players'] = f"{room.get('player_count', 0)}/{room.get('max_players', 0)}"
                            room_data['mc_motd'] = room.get('description', room.get('room_desc', ''))
                            room_data['mc_version'] = room.get('game_version', room.get('version', ''))
                            
                            server_addr = room.get('server_addr')
                            remote_port = room.get('remote_port')
                            
                            if MCSTATUS_AVAILABLE and server_addr and remote_port:
                                try:
                                    # 1.5s 超时（原0.5s + 1s）
                                    server = JavaServer.lookup(f"{server_addr}:{remote_port}", timeout=1.5)
                                    status_result = server.status()
                                    room_data['mc_online'] = True
                                    room_data['mc_latency'] = f"{int(status_result.latency)}ms"
                                    room_data['mc_players'] = f"{status_result.players.online}/{status_result.players.max}"
                                    if str(status_result.description).strip():
                                        room_data['mc_motd'] = str(status_result.description).strip()
                                    if status_result.version.name:
                                        room_data['mc_version'] = status_result.version.name
                                except Exception:
                                    pass
                                    
                            if room.get('is_extra'):
                                room_data['mc_online'] = True
                                
                            return room_data

                        if rooms:
                            # 准备开始加载新房间时再清空旧列表
                            self.signals.clear_lobby_requested.emit()
                            
                            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(rooms))) as executor:
                                futures = [executor.submit(ping_room, r) for r in rooms]
                                for future in concurrent.futures.as_completed(futures):
                                    try:
                                        res = future.result()
                                        self.signals.room_processed.emit(res)
                                    except Exception:
                                        pass
                        
                        self.signals.rooms_updated.emit([]) # 仅用于通知结束
                    else:
                        self.signals.rooms_updated.emit([])
                except Exception:
                    self.signals.rooms_updated.emit([])
            
            import threading
            threading.Thread(target=fetch, daemon=True).start()

        def on_refresh_finished(self, _):
            self.is_refreshing = False
            self.btn_refresh.setText("🔄 刷新大厅")
            self.btn_refresh.setEnabled(True)

        def add_room_to_table(self, room):
            # 过滤离线房间
            if not self.check_show_offline.isChecked() and not room.get('mc_online', False):
                return
                
            row = self.lobby_table.rowCount()
            self.lobby_table.insertRow(row)
            
            # 状态圆点
            status_label = QLabel()
            status_label.setAlignment(Qt.AlignCenter)
            is_online = room.get('mc_online', False)
            dot_color = "#67C23A" if is_online else "#F56C6C"
            status_label.setText("●")
            status_label.setStyleSheet(f"color: {dot_color}; font-size: 16px;")
            self.lobby_table.setCellWidget(row, 0, status_label)
            
            # 房间号
            item_code = QTableWidgetItem(str(room.get('full_room_code', '')))
            item_code.setTextAlignment(Qt.AlignCenter)
            self.lobby_table.setItem(row, 1, item_code)
            
            # 房间名 (显示描述而不是默认的 xxx的房间)
            # 优先从 room 中获取原始 description，如果没有则从 mc_motd 获取
            room_desc = room.get('description', room.get('mc_motd', ''))
            if not room_desc:
                room_desc = room.get('room_name', '未命名房间')
            item_name = QTableWidgetItem(str(room_desc))
            self.lobby_table.setItem(row, 2, item_name)
            
            # 描述 (MOTD)
            motd = room.get('mc_motd', '')
            version = room.get('mc_version', '')
            if version:
                # 版本显示在前面
                motd = f"[{version}] {motd}"
            item_motd = QTableWidgetItem(motd)
            self.lobby_table.setItem(row, 3, item_motd)
            
            # 人数
            item_players = QTableWidgetItem(str(room.get('mc_players', '0/0')))
            item_players.setTextAlignment(Qt.AlignCenter)
            self.lobby_table.setItem(row, 4, item_players)
            
            # 延迟
            latency = str(room.get('mc_latency', '--'))
            item_latency = QTableWidgetItem(latency)
            item_latency.setTextAlignment(Qt.AlignCenter)
            if is_online:
                try:
                    lat_val = int(latency.replace("ms", ""))
                    color = "#67C23A" if lat_val < 100 else "#E6A23C"
                except ValueError:
                    color = "#E6A23C"
                item_latency.setForeground(QColor(color))
            else:
                item_latency.setForeground(QColor("#909399"))
            self.lobby_table.setItem(row, 5, item_latency)
            
            # 操作按钮
            btn_join = ModernButton("加入", "#4CAF50")
            def handle_join(r=room):
                if r.get('is_extra') or 'download_url' in r or 'https_url' in r:
                    self.show_extra_server_dialog(r)
                else:
                    self.join_specific_room(r.get('full_room_code', ''))
                    self.nav_list.setCurrentRow(0) # 自动切换到“联机”页
            btn_join.debounced_clicked.connect(handle_join)
            btn_join.setStyleSheet(btn_join.styleSheet() + "QPushButton { padding: 5px 15px; font-size: 12px; }")
            
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 2, 5, 2)
            btn_layout.addWidget(btn_join)
            self.lobby_table.setCellWidget(row, 6, btn_widget)

        def show_extra_server_dialog(self, room_info):
            """显示额外服务器的弹窗（下载整合包/打开服务器网站/加入服务器）"""
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
            from PySide6.QtGui import QFont
            from PySide6.QtCore import Qt
            import webbrowser
            
            download_url = room_info.get('download_url')
            https_url = room_info.get('https_url')
            
            dialog = QDialog(self)
            dialog.setWindowTitle("服务器选项")
            dialog.setFixedSize(400, 250)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #F0F4F8;
                }
            """)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            title_label = QLabel(room_info.get('room_name', '服务器'))
            title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
            title_label.setStyleSheet("color: #102A43;")
            title_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(title_label)
            
            btn_layout = QVBoxLayout()
            btn_layout.setSpacing(10)
            
            join_btn = QPushButton("🎮 加入服务器")
            join_btn.setFixedHeight(40)
            join_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 10.5pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #43A047; }
            """)
            
            dl_btn = QPushButton("📥 下载整合包")
            dl_btn.setFixedHeight(40)
            dl_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E88E5;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 10.5pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #1565C0; }
            """)
            
            web_btn = QPushButton("🌐 打开服务器网站")
            web_btn.setFixedHeight(40)
            web_btn.setStyleSheet("""
                QPushButton {
                    background-color: #26A69A;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 10.5pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #00897B; }
            """)
            
            def on_join():
                dialog.accept()
                self.join_specific_room(room_info.get('full_room_code', ''))
                self.nav_list.setCurrentRow(0)
            
            def on_dl():
                if download_url:
                    webbrowser.open(download_url)
                else:
                    QMessageBox.information(dialog, "提示", "该服务器未提供整合包下载链接")
                dialog.accept()
            
            def on_web():
                if https_url:
                    webbrowser.open(https_url)
                else:
                    QMessageBox.information(dialog, "提示", "该服务器未提供网站链接")
                dialog.accept()
            
            join_btn.clicked.connect(on_join)
            dl_btn.clicked.connect(on_dl)
            web_btn.clicked.connect(on_web)
            
            btn_layout.addWidget(join_btn)
            btn_layout.addWidget(dl_btn)
            btn_layout.addWidget(web_btn)
            layout.addLayout(btn_layout)
            
            dialog.exec()

        def on_create_room(self):
            # 安全地调用Tkinter线程中的创建房间函数
            self.app_instance.root.after(0, self.app_instance.run_frp_create)
            

        def join_specific_room(self, room_code):
            room_code = room_code.strip()
            if not room_code:
                return
            
            # 检查 FRP 文件是否存在（不自动下载）
            if not self.app_instance.check_and_download_frp(auto_download=False):
                self.app_instance.log("FRP 文件未就绪，无法加入房间")
                show_modern_error_dialog(self, "缺少依赖", "检测到缺少 FRP 依赖文件！\n\n请依次点击软件：\n更多功能--【依赖补全】\n\n下载完成后即可正常使用联机功能。")
                return
            
            # 即刻锁定 UI (参考 tkinter 逻辑)
            self.app_instance.lock_buttons()
            self.app_instance.log(f"尝试加入房间: {room_code}")
            
            # 在线程中处理，避免UI假死
            def do_join():
                try:
                    room_info = self.app_instance.get_room_info_from_cloud(room_code)
                    if room_info:
                        self.app_instance.root.after(0, lambda: self.app_instance.auto_join_room_from_lobby(room_code, room_info))
                    else:
                        self.app_instance.log(f"无法获取房间信息: {room_code}")
                        
                        def show_error():
                            self.app_instance.unlock_buttons()
                            show_modern_error_dialog(self, "错误", f"无法找到或连接房间：{room_code}")
                            
                        self.signals.ui_callback_requested.emit(show_error)
                except Exception as e:
                    self.app_instance.log(f"加入房间出错: {e}")
                    self.app_instance.root.after(0, self.app_instance.unlock_buttons)
            
            import threading
            threading.Thread(target=do_join, daemon=True).start()

        def on_join_room_from_input(self):
            room_code = self.room_code_input.text().strip()
            if room_code:
                self.join_specific_room(room_code)
                self.room_code_input.clear()
            else:
                QMessageBox.warning(self, "提示", "请输入房间号")

        def create_chat_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(20, 10, 20, 20)
            layout.setSpacing(15)
            
            # --- 顶部状态栏 ---
            header_layout = QHBoxLayout()
            self.chat_user_status = QLabel("未登录")
            self.chat_user_status.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 14px;")
            header_layout.addWidget(self.chat_user_status)
            header_layout.addStretch()
            
            self.btn_chat_login = ModernButton("登录", "#1565C0")
            self.btn_chat_login.clicked.connect(self.show_chat_login)
            header_layout.addWidget(self.btn_chat_login)
            
            self.btn_chat_register = ModernButton("注册", "#4CAF50")
            self.btn_chat_register.clicked.connect(self.show_chat_register)
            header_layout.addWidget(self.btn_chat_register)
            
            self.btn_chat_logout = ModernButton("退出", "#F44336")
            self.btn_chat_logout.clicked.connect(self.chat_logout)
            self.btn_chat_logout.hide()
            header_layout.addWidget(self.btn_chat_logout)
            
            layout.addLayout(header_layout)
            
            # --- 主内容区 ---
            main_content = QHBoxLayout()
            
            # 左侧：消息列表
            msg_container = QVBoxLayout()
            self.chat_view = QTextEdit()
            self.chat_view.setReadOnly(True)
            self.chat_view.setPlaceholderText("欢迎来到 LMFP 公共聊天室！请登录后参与讨论。")
            self.chat_view.setStyleSheet("""
                QTextEdit {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 13px;
                }
            """)
            msg_container.addWidget(self.chat_view)
            
            # 输入框
            input_layout = QHBoxLayout()
            self.chat_input = QLineEdit()
            self.chat_input.setPlaceholderText("请输入消息...")
            self.chat_input.setFixedHeight(40)
            self.chat_input.setEnabled(False)
            self.chat_input.returnPressed.connect(self.send_chat_message)
            input_layout.addWidget(self.chat_input)
            
            self.btn_send_chat = ModernButton("发送", "#1565C0")
            self.btn_send_chat.setFixedHeight(40)
            self.btn_send_chat.setEnabled(False)
            self.btn_send_chat.clicked.connect(self.send_chat_message)
            input_layout.addWidget(self.btn_send_chat)
            
            msg_container.addLayout(input_layout)
            main_content.addLayout(msg_container, 3)
            
            # 右侧：在线用户
            online_container = QVBoxLayout()
            online_header = QLabel("在线用户")
            online_header.setStyleSheet("font-weight: bold; color: #546E7A; padding: 5px;")
            online_container.addWidget(online_header)
            
            self.online_list = QListWidget()
            self.online_list.setStyleSheet("""
                QListWidget {
                    background-color: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 8px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #F5F7FA;
                    color: #37474F;
                }
            """)
            self.online_list.itemDoubleClicked.connect(self.on_online_user_double_clicked)
            online_container.addWidget(self.online_list)
            
            main_content.addLayout(online_container, 1)
            layout.addLayout(main_content)
            
            return page

        def get_system_info_header(self):
            """获取系统详细信息页眉（不包含设备信息）"""
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = "================================================\n"
            header += "        LMFP 运行日志导出报告 (PySide6)\n"
            header += f"        导出时间: {now}\n"
            header += "================================================\n\n"
            
            # 不再导出设备配置和MAC地址信息
            
            header += "="*20 + " [ 日志正文 ] " + "="*20 + "\n\n"
            return header

        def export_pyside_log(self):
            """导出 PySide 日志"""
            log_content = self.log_text.toPlainText()
            if not log_content.strip():
                QMessageBox.warning(self, "导出提示", "当前日志为空，无需导出。")
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出日志", "LMFP_Log.txt", "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                try:
                    # 获取系统信息头
                    system_header = self.get_system_info_header()
                    full_content = system_header + log_content
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(full_content)
                    QMessageBox.information(self, "成功", f"日志已成功导出至：\n{file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "导出失败", f"无法写入文件：\n{str(e)}")

        def check_update_in_thread(self):
            """在独立线程中检查软件更新"""
            # 禁用按钮防止重复点击
            if hasattr(self, 'btn_check_update'):
                self.btn_check_update.setEnabled(False)
                self.btn_check_update.setText("⏳ 检查中...")
            
            def do_check():
                try:
                    self.signals.log_emitted.emit("正在检查软件更新...")
                    
                    # 读取本地版本号
                    import os
                    from urllib.request import urlopen, Request
                    
                    local_version = ""
                    if os.path.exists("v.txt"):
                        with open("v.txt", "r", encoding="utf-8") as f:
                            local_version = f.read().strip()
                    else:
                        local_version = "1030"  # 默认版本
                    
                    # 获取云端版本号
                    url = f"https://{apis}/v.txt"
                    req = Request(url, headers={'User-Agent': f'LMFP/{lmfpvers}'})
                    with urlopen(req, timeout=None) as response:
                        cloud_version = response.read().decode('utf-8').strip()
                    
                    # 比较版本号
                    if _compare_versions(cloud_version, local_version) > 0:
                        # 发现新版本，在UI线程中显示对话框
                        self.signals.ui_callback_requested.emit(
                            lambda lv=local_version, cv=cloud_version: self._show_update_dialog(lv, cv)
                        )
                        self.signals.log_emitted.emit(f"✓ 发现新版本 {cloud_version}，当前版本 {local_version}")
                    else:
                        self.signals.log_emitted.emit("✓ 当前已是最新版本")
                        
                except Exception as e:
                    self.signals.log_emitted.emit(f"✗ 检查更新失败: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # 恢复按钮状态
                    if hasattr(self, 'btn_check_update'):
                        self.signals.ui_callback_requested.emit(lambda: self._restore_update_button())
            
            # 在独立线程中执行
            import threading
            thread = threading.Thread(target=do_check, daemon=True)
            thread.start()
        
        def _show_update_dialog(self, local_version, cloud_version):
            """在PySide中显示更新对话框"""
            try:
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QFont
                
                # 创建PySide对话框
                dialog = QDialog(self)
                dialog.setWindowTitle("发现软件新版本")
                dialog.setFixedSize(500, 220)
                dialog.setModal(True)
                
                # 设置样式
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #F5F7FA;
                    }
                    QLabel {
                        color: #333333;
                    }
                    QPushButton {
                        padding: 10px 20px;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: bold;
                    }
                """)
                
                layout = QVBoxLayout(dialog)
                layout.setSpacing(20)
                layout.setContentsMargins(30, 30, 30, 30)
                
                # 标题
                title_label = QLabel("发现软件新版本")
                title_font = QFont()
                title_font.setPointSize(16)
                title_font.setBold(True)
                title_label.setFont(title_font)
                title_label.setStyleSheet("color: #1565C0;")
                title_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(title_label)
                
                # 内容
                content_label = QLabel(
                    f"检测到新的版本 {cloud_version}，当前版本为 {local_version}。\n是否立即更新？（如果不更新 可能因为过老的软件版本 而无法联机）"
                )
                content_label.setWordWrap(True)
                content_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(content_label)
                
                # 按钮
                button_layout = QHBoxLayout()
                button_layout.setSpacing(15)
                
                update_btn = QPushButton("✓ 立即更新（推荐）")
                update_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                
                later_btn = QPushButton("稍后提醒我")
                later_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #E0E0E0;
                        color: #333333;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #D0D0D0;
                    }
                """)
                
                def update_now():
                    dialog.accept()
                    perform_update_pyside()
                
                def remind_later():
                    dialog.reject()
                
                update_btn.clicked.connect(update_now)
                later_btn.clicked.connect(remind_later)
                
                button_layout.addWidget(update_btn)
                button_layout.addWidget(later_btn)
                layout.addLayout(button_layout)
                
                # 显示对话框
                dialog.exec()
                
            except Exception as e:
                print(f"显示更新对话框失败: {e}")
                import traceback
                traceback.print_exc()
        
        def _restore_update_button(self):
            """恢复更新按钮状态（需要在UI线程中调用）"""
            if hasattr(self, 'btn_check_update'):
                self.btn_check_update.setEnabled(True)
                self.btn_check_update.setText("🔄 检查软件更新")

        def create_more_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(25)
            
            title = QLabel("🛠️ 更多功能")
            title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
            layout.addWidget(title)
            
            description = QLabel("这里集合了程序的所有辅助功能，点击下方按钮即可执行对应操作。")
            description.setStyleSheet("font-size: 14px; color: #546E7A; margin-bottom: 20px;")
            layout.addWidget(description)
            
            # 使用网格布局放置按钮
            grid_layout = QGridLayout()
            grid_layout.setSpacing(20)
            
            # 功能列表: (显示文本, 颜色, 回调函数, 描述)
            funcs = [
                ("📁 导出运行日志", "#1565C0", self.export_pyside_log, "将运行日志保存到本地文件"),
                ("🔄 检查软件更新", "#1565C0", self.check_update_in_thread, "检查是否有新版本可用（无反应则无需更新）"),
                ("❓ 使用帮助手册", "#1565C0", self.app_instance.show_help, "查看详细的使用教程和常见问题"),
                ("📢 查看最新公告", "#1565C0", self.app_instance.open_announcement_page, "获取软件最新动态和重要通知"),
                ("📦 补全运行依赖", "#1565C0", self.app_instance.download_frp_dependencies, "一键修复内网穿透无法启动的问题"),
                ("ℹ️ 关于软件信息", "#1565C0", lambda: self.nav_list.setCurrentRow(4), "查看版本、开发者及官方网站"),
                ("👥 加入官方QQ群", "#1565C0", self.app_instance.open_qq_group_direct, "加入交流群，获取实时技术支持"),
                ("❌ 退出应用程序", "#F44336", self.app_instance.root.quit, "关闭所有功能并退出程序")
            ]
            
            for i, (text, color, func, desc) in enumerate(funcs):
                btn_container = QVBoxLayout()
                
                btn = ModernButton(text, color)
                btn.setFixedHeight(55)
                btn.clicked.connect(func)
                
                # 保存检查更新按钮的引用
                if "检查软件更新" in text:
                    self.btn_check_update = btn
                
                btn_container.addWidget(btn)
                
                desc_label = QLabel(desc)
                desc_label.setStyleSheet("font-size: 12px; color: #90A4AE; padding-left: 5px;")
                desc_label.setAlignment(Qt.AlignCenter)
                btn_container.addWidget(desc_label)
                
                row = i // 2
                col = i % 2
                grid_layout.addLayout(btn_container, row, col)
            
            layout.addLayout(grid_layout)
            layout.addStretch()
            
            # 底部作者信息
            footer = QLabel("LMFP - Minecraft Minecraft 联机平台 | Author: Lyt_IT")
            footer.setStyleSheet("color: #B0BEC5; font-size: 12px;")
            footer.setAlignment(Qt.AlignCenter)
            layout.addWidget(footer)
            
            return page

        def create_about_page(self):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(25)
            
            # 页面标题
            title = QLabel("ℹ️ 关于软件")
            title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1565C0; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # 卡片容器
            card = QFrame()
            card.setObjectName("aboutCard")
            card.setStyleSheet("""
                QFrame#aboutCard {
                    background-color: #FFFFFF;
                    border-radius: 15px;
                }
            """)
            
            # 卡片阴影
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(25)
            shadow.setXOffset(0)
            shadow.setYOffset(8)
            shadow.setColor(QColor(0, 0, 0, 30))
            card.setGraphicsEffect(shadow)
            
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(40, 40, 40, 40)
            card_layout.setSpacing(25)
            
            # Logo/Title
            header_layout = QHBoxLayout()
            logo_label = QLabel("🚀")
            logo_label.setStyleSheet("font-size: 50px;")
            header_layout.addWidget(logo_label)
            
            title_info = QVBoxLayout()
            name_label = QLabel("LMFP - Minecraft 联机平台")
            name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1565C0;")
            version_label = QLabel(f"版本: Beta {lmfpvers}")
            version_label.setStyleSheet("font-size: 14px; color: #78909C;")
            title_info.addWidget(name_label)
            title_info.addWidget(version_label)
            header_layout.addLayout(title_info)
            header_layout.addStretch()
            card_layout.addLayout(header_layout)
            
            # 分割线
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Plain)
            line.setStyleSheet("background-color: #ECEFF1;")
            card_layout.addWidget(line)
            
            # 详细信息
            info_grid = QGridLayout()
            info_grid.setSpacing(15)
            
            # 开发者
            dev_icon = QLabel("👨‍💻")
            dev_label = QLabel("开发者:")
            dev_value = QLabel("Lyt_IT")
            dev_label.setStyleSheet("font-weight: bold; color: #546E7A;")
            dev_value.setStyleSheet("color: #37474F;")
            info_grid.addWidget(dev_icon, 0, 0)
            info_grid.addWidget(dev_label, 0, 1)
            info_grid.addWidget(dev_value, 0, 2)
            
            # 联系方式
            qq_icon = QLabel("💬")
            qq_label = QLabel("开发者QQ/微信:")
            qq_value = QLabel("2232908600/liuyvetong")
            qq_label.setStyleSheet("font-weight: bold; color: #546E7A;")
            qq_value.setStyleSheet("color: #37474F; text-decoration: underline;")
            info_grid.addWidget(qq_icon, 1, 0)
            info_grid.addWidget(qq_label, 1, 1)
            info_grid.addWidget(qq_value, 1, 2)
            
            # 官方网站
            web_icon = QLabel("🌐")
            web_label = QLabel("官方网站:")
            web_value = QLabel(f"https://www.teft.cn/")
            web_label.setStyleSheet("font-weight: bold; color: #546E7A;")
            web_value.setStyleSheet("color: #1E88E5; text-decoration: underline;")
            web_value.setCursor(Qt.PointingHandCursor)
            # 点击跳转
            def open_web():
                import webbrowser
                webbrowser.open(f"https://www.teft.cn/")
            web_value.mousePressEvent = lambda e: open_web()
            
            info_grid.addWidget(web_icon, 2, 0)
            info_grid.addWidget(web_label, 2, 1)
            info_grid.addWidget(web_value, 2, 2)
            
            card_layout.addLayout(info_grid)
            
            # 描述文本
            desc_text = QLabel("LMFP 是一个专为 Minecraft 玩家打造的内网穿透联机工具。致力于提供最简单、最稳定、最现代化的联机体验。")
            desc_text.setWordWrap(True)
            desc_text.setStyleSheet("color: #607D8B; line-height: 1.5; font-size: 13px; margin-top: 10px;")
            card_layout.addWidget(desc_text)
            
            # 底部版权
            copyright = QLabel("© 2025-2026 Lyt_IT Studio. All rights reserved.")
            copyright.setStyleSheet("color: #B0BEC5; font-size: 11px; margin-top: 20px;")
            copyright.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(copyright)
            
            layout.addWidget(card)
            layout.addStretch()
            
            return page

        def chat_http_request(self, url, method="GET", data=None):
            try:
                import urllib.request
                import urllib.parse
                import json
                
                if data is not None:
                    if method == "GET":
                        params = urllib.parse.urlencode(data)
                        url = f"{url}?{params}"
                        data = None
                    else:
                        data = urllib.parse.urlencode(data).encode('utf-8')
                
                req = urllib.request.Request(url, data=data, method=method)
                req.add_header('User-Agent', f'LMFP/{lmfpvers}')
                
                with urllib.request.urlopen(req, timeout=None) as response:
                    return json.loads(response.read().decode('utf-8'))
            except Exception as e:
                return {"success": False, "message": str(e)}

        def send_notification(self, title, message):
            """发送系统通知"""
            try:
                # 尝试使用 plyer 库发送通知
                try:
                    from plyer import notification
                    notification.notify(
                        title=title,
                        message=message,
                        app_name="LMFP 聊天室",
                        timeout=5
                    )
                except ImportError:
                    # 如果 plyer 不可用，尝试使用 Windows 原生 API
                    if platform.system() == "Windows":
                        import ctypes
                        # 使用 MB_OKCANCEL (1) 匹配原 tkinter 逻辑
                        ctypes.windll.user32.MessageBoxW(0, message, title, 1)
                    else:
                        print(f"NOTIFICATION: {title} - {message}")
            except Exception as e:
                print(f"发送通知时出错: {e}")

        def poll_chat_messages(self):
            if not self.chat_token or not self.chat_active:
                return
                
            def fetch():
                url = f"{self.chat_api_base}/get_messages.php"
                params = {"token": self.chat_token, "last_id": self.chat_last_id}
                resp = self.chat_http_request(url, "GET", params)
                if resp and resp.get('success'):
                    messages = resp.get('data', [])
                    
                    # 判断 @我的 消息下方是否已经有我的消息（即已回复）
                    for i, msg in enumerate(messages):
                        content = msg.get('content', '')
                        if self.chat_user and f"@{self.chat_user}" in content:
                            has_reply = False
                            for next_msg in messages[i+1:]:
                                if next_msg.get('sender') == self.chat_user:
                                    has_reply = True
                                    break
                            if has_reply:
                                msg['skip_notification'] = True
                                
                    for msg in messages:
                        self.signals.chat_message_received.emit(msg)
            
            threading.Thread(target=fetch, daemon=True).start()

        def poll_online_users(self):
            if not self.chat_token:
                return
                
            def fetch():
                url = f"{self.chat_api_base}/get_online_users.php"
                params = {"token": self.chat_token}
                resp = self.chat_http_request(url, "GET", params)
                if resp and resp.get('success'):
                    self.signals.online_users_updated.emit(resp.get('data', []))
            
            threading.Thread(target=fetch, daemon=True).start()

        def append_chat_text(self, msg):
            msg_id = msg.get('id', 0)
            if msg_id <= self.chat_last_id:
                return
            self.chat_last_id = msg_id
            
            sender = msg.get('sender', '未知')
            content = msg.get('content', '')
            ts = msg.get('timestamp', time.time())
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            
            color = "#1565C0" if sender == self.chat_user else "#333333"
            if sender == "Lyt_IT": color = "#F44336"
            
            # 对消息内容中的 @用户名 进行高亮处理
            display_content = content
            if "@" in display_content:
                import re
                # 匹配 @用户名 (支持中文和数字字母下划线)
                display_content = re.sub(r'(@[\w\u4e00-\u9fff]+)', r'<span style="color: #1E88E5;">\1</span>', display_content)
            
            formatted = f'<span style="color: #9e9e9e;">[{time_str}]</span> '
            formatted += f'<b style="color: {color};">{sender}:</b> {display_content}'
            
            self.chat_view.append(formatted)
            self.chat_view.verticalScrollBar().setValue(self.chat_view.verticalScrollBar().maximum())
            
            # 检测@
            if self.chat_user and f"@{self.chat_user}" in content and not msg.get('skip_notification', False):
                current_time = time.time()
                if current_time - self.chat_last_notification_time >= self.chat_notification_cooldown:
                    self.signals.log_emitted.emit(f"💬 聊天室：{sender} 在消息中提到了你")
                    self.send_notification(f"@{self.chat_user} 提醒", f"{sender} 在聊天中提到了你: {content[:50]}...")
                    self.chat_last_notification_time = current_time

        def update_chat_online_list(self, users):
            self.online_list.clear()
            for user in users:
                name = user.get('username', '未知')
                item = QListWidgetItem(name)
                if name == "Lyt_IT":
                    item.setForeground(QColor("#F44336"))
                elif name == self.chat_user:
                    item.setText(f"{name} (我)")
                    item.setForeground(QColor("#1565C0"))
                self.online_list.addItem(item)

        def update_chat_status(self, text, color):
            self.chat_user_status.setText(text)
            self.chat_user_status.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")

        def on_online_user_double_clicked(self, item):
            name = item.text().replace(" (我)", "")
            self.chat_input.setText(self.chat_input.text() + f" @{name} ")
            self.chat_input.setFocus()

        def check_chat_auto_login(self):
            if os.path.exists("user_session.json"):
                try:
                    with open("user_session.json", "r", encoding="utf-8") as f:
                        session = json.load(f)
                        token = session.get("token")
                        user = session.get("username")
                        if token and user:
                            def verify():
                                url = f"{self.chat_api_base}/verify_token.php"
                                resp = self.chat_http_request(url, "POST", {"token": token})
                                if resp and resp.get('success'):
                                    self.signals.chat_login_success.emit(user, token)
                            threading.Thread(target=verify, daemon=True).start()
                except: pass

        def on_chat_login_success(self, username, token):
            self.chat_user = username
            self.chat_token = token
            self.chat_active = True
            self.chat_last_id = 0
            
            self.btn_chat_login.hide()
            self.btn_chat_register.hide()
            self.btn_chat_logout.show()
            self.chat_input.setEnabled(True)
            self.btn_send_chat.setEnabled(True)
            
            self.update_chat_status(f"已登录: {username}", "#4CAF50")
            self.signals.log_emitted.emit(f"✓ 聊天室登录成功: {username}")
            
            # 开启轮询
            self.chat_refresh_timer.start(2000)
            self.chat_online_timer.start(10000)
            # 立即刷新一次
            self.poll_chat_messages()
            self.poll_online_users()

        def chat_logout(self):
            self.chat_active = False
            self.chat_refresh_timer.stop()
            self.chat_online_timer.stop()
            self.chat_token = None
            self.chat_user = None
            
            self.btn_chat_login.show()
            self.btn_chat_register.show()
            self.btn_chat_logout.hide()
            self.chat_input.setEnabled(False)
            self.btn_send_chat.setEnabled(False)
            self.online_list.clear()
            
            self.update_chat_status("未登录", "#FF9800")
            if os.path.exists("user_session.json"):
                try: os.remove("user_session.json")
                except: pass
            self.signals.log_emitted.emit("✓ 已退出聊天室")

        def send_chat_message(self):
            content = self.chat_input.text().strip()
            if not content or not self.chat_token: return
            
            self.chat_input.clear()
            def send():
                url = f"{self.chat_api_base}/send_message.php"
                resp = self.chat_http_request(url, "POST", {"token": self.chat_token, "message": content})
                if not resp or not resp.get('success'):
                    self.signals.log_emitted.emit(f"✗ 消息发送失败: {resp.get('message', '未知错误')}")
            
            threading.Thread(target=send, daemon=True).start()

        def show_chat_login(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("登录聊天室")
            dialog.setFixedWidth(380)
            dialog.setStyleSheet("""
                QDialog { background-color: white; border-radius: 12px; }
                QLineEdit { 
                    padding: 12px; border: 1px solid #E0E0E0; border-radius: 8px; 
                    background-color: #F8F9FA; font-size: 14px; color: #333;
                }
                QLineEdit:focus { border: 2px solid #1565C0; background-color: white; }
                QLabel { color: #546E7A; font-size: 14px; font-weight: bold; }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(15)
            
            title = QLabel("欢迎回来")
            title.setStyleSheet("font-size: 24px; color: #1565C0; font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(title)
            
            layout.addWidget(QLabel("邮箱地址"))
            email_input = QLineEdit()
            email_input.setPlaceholderText("请输入您的QQ邮箱")
            layout.addWidget(email_input)
            
            layout.addWidget(QLabel("登录密码"))
            pass_input = QLineEdit()
            pass_input.setEchoMode(QLineEdit.Password)
            pass_input.setPlaceholderText("请输入您的密码")
            layout.addWidget(pass_input)
            
            layout.addSpacing(10)
            
            btn_layout = QHBoxLayout()
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet("""
                QPushButton { 
                    padding: 10px 20px; border: 1px solid #E0E0E0; border-radius: 8px; 
                    background-color: white; color: #757575; font-weight: bold;
                }
                QPushButton:hover { background-color: #F5F5F5; }
            """)
            ok_button = ModernButton("立即登录", "#1565C0")
            ok_button.setFixedHeight(45)
            ok_button.setDefault(True)
            
            email_input.returnPressed.connect(pass_input.setFocus)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(ok_button)
            layout.addLayout(btn_layout)
            
            def handle_login():
                email = email_input.text().strip()
                password = pass_input.text().strip()
                if not email or not password: return
                
                ok_button.setEnabled(False)
                ok_button.setText("正在验证身份...")
                
                def run():
                    url = f"{self.chat_api_base}/login.php"
                    resp = self.chat_http_request(url, "POST", {"email": email, "password": password})
                    
                    def on_finish():
                        if resp and resp.get('success'):
                            data = resp.get('data', {})
                            self.signals.chat_login_success.emit(data.get('username'), data.get('token'))
                            try:
                                with open("user_session.json", "w", encoding="utf-8") as f:
                                    json.dump({"token": data.get('token'), "username": data.get('username')}, f)
                            except: pass
                            dialog.accept()
                        else:
                            msg = resp.get('message', '未知错误')
                            if "验证" in msg:
                                dialog.reject()
                                self.signals.chat_verify_requested.emit(email, password)
                            else:
                                QMessageBox.warning(dialog, "登录失败", msg)
                                ok_button.setEnabled(True)
                                ok_button.setText("立即登录")
                    
                    self.signals.ui_callback_requested.emit(on_finish)
                
                threading.Thread(target=run, daemon=True).start()

            ok_button.clicked.connect(handle_login)
            pass_input.returnPressed.connect(handle_login)
            cancel_btn.clicked.connect(dialog.reject)
            dialog.exec()

        def show_chat_register(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("注册聊天室账号")
            dialog.setFixedWidth(400)
            dialog.setStyleSheet("""
                QDialog { background-color: white; border-radius: 12px; }
                QLineEdit { 
                    padding: 12px; border: 1px solid #E0E0E0; border-radius: 8px; 
                    background-color: #F8F9FA; font-size: 14px;
                }
                QLineEdit:focus { border: 2px solid #4CAF50; background-color: white; }
                QLabel { color: #546E7A; font-size: 13px; font-weight: bold; }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(12)
            
            title = QLabel("立即注册")
            title.setStyleSheet("font-size: 24px; color: #4CAF50; font-weight: bold; margin-bottom: 5px;")
            layout.addWidget(title)
            
            desc = QLabel("创建一个账号，与全世界的玩家即时交流。")
            desc.setStyleSheet("color: #90A4AE; font-size: 13px; font-weight: normal; margin-bottom: 10px;")
            layout.addWidget(desc)
            
            layout.addWidget(QLabel("QQ邮箱"))
            email_input = QLineEdit()
            email_input.setPlaceholderText("用于接收验证码")
            layout.addWidget(email_input)
            
            layout.addWidget(QLabel("用户昵称"))
            user_input = QLineEdit()
            user_input.setPlaceholderText("在聊天室显示的名称")
            layout.addWidget(user_input)
            
            layout.addWidget(QLabel("设置密码"))
            pass_input = QLineEdit()
            pass_input.setEchoMode(QLineEdit.Password)
            pass_input.setPlaceholderText("请牢记您的密码")
            layout.addWidget(pass_input)
            
            layout.addWidget(QLabel("确认密码"))
            pass_confirm_input = QLineEdit()
            pass_confirm_input.setEchoMode(QLineEdit.Password)
            pass_confirm_input.setPlaceholderText("请再次输入密码")
            layout.addWidget(pass_confirm_input)
            
            layout.addSpacing(15)
            
            btn_layout = QHBoxLayout()
            cancel_btn = QPushButton("返回登录")
            cancel_btn.setStyleSheet("border: none; color: #1565C0; font-weight: bold;")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            
            ok_button = ModernButton("创建账号", "#4CAF50")
            ok_button.setFixedHeight(45)
            ok_button.setDefault(True)
            
            email_input.returnPressed.connect(user_input.setFocus)
            user_input.returnPressed.connect(pass_input.setFocus)
            pass_input.returnPressed.connect(pass_confirm_input.setFocus)
            
            btn_layout.addWidget(cancel_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(ok_button)
            layout.addLayout(btn_layout)
            
            def handle_register():
                email = email_input.text().strip()
                user = user_input.text().strip()
                password = pass_input.text().strip()
                pass_confirm = pass_confirm_input.text().strip()
                
                if not all([email, user, password, pass_confirm]): return
                
                if password != pass_confirm:
                    QMessageBox.warning(dialog, "注册提示", "两次输入的密码不一致，请检查后重试。")
                    return
                
                ok_button.setEnabled(False)
                ok_button.setText("正在开启新世界...")
                
                def run():
                    url = f"{self.chat_api_base}/register.php"
                    resp = self.chat_http_request(url, "POST", {"email": email, "username": user, "password": password})
                    
                    def on_finish():
                        if resp and resp.get('success'):
                            self.signals.log_emitted.emit("✓ 注册成功！请前往邮箱查收验证码。")
                            dialog.accept()
                            self.signals.chat_verify_requested.emit(email, password)
                        else:
                            QMessageBox.warning(dialog, "注册失败", resp.get('message', '未知错误'))
                            ok_button.setEnabled(True)
                            ok_button.setText("创建账号")
                    
                    self.signals.ui_callback_requested.emit(on_finish)
                
                threading.Thread(target=run, daemon=True).start()

            ok_button.clicked.connect(handle_register)
            pass_confirm_input.returnPressed.connect(handle_register)
            cancel_btn.clicked.connect(dialog.reject)
            dialog.exec()

        def show_chat_verify(self, email, password):
            dialog = QDialog(self)
            dialog.setWindowTitle("安全验证")
            dialog.setFixedWidth(380)
            dialog.setStyleSheet("""
                QDialog { background-color: white; border-radius: 12px; }
                QLineEdit { 
                    padding: 15px; border: 2px solid #E0E0E0; border-radius: 8px; 
                    background-color: #F8F9FA; font-size: 24px; color: #1565C0;
                    font-weight: bold; letter-spacing: 8px;
                }
                QLineEdit:focus { border: 2px solid #FF9800; background-color: white; }
                QLabel { color: #546E7A; font-size: 14px; }
            """)
            
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(30, 30, 30, 30)
            layout.setSpacing(20)
            
            title = QLabel("邮箱验证")
            title.setStyleSheet("font-size: 24px; color: #FF9800; font-weight: bold; margin-bottom: 5px;")
            layout.addWidget(title)
            
            label = QLabel(f"验证码已发送至：\n<b>{email}</b>")
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            
            code_input = QLineEdit()
            code_input.setPlaceholderText("输入6位验证码")
            code_input.setAlignment(Qt.AlignCenter)
            code_input.setMaxLength(6)
            layout.addWidget(code_input)
            
            ok_button = ModernButton("完成验证", "#FF9800")
            ok_button.setFixedHeight(50)
            ok_button.setDefault(True)
            layout.addWidget(ok_button)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet("border: none; color: #90A4AE;")
            layout.addWidget(cancel_btn)
            
            def handle_verify():
                code = code_input.text().strip()
                if not code: return
                
                ok_button.setEnabled(False)
                ok_button.setText("正在校验...")
                
                def run():
                    url = f"{self.chat_api_base}/verify_email.php"
                    resp = self.chat_http_request(url, "POST", {"email": email, "code": code})
                    
                    def on_finish():
                        if resp and resp.get('success'):
                            self.signals.log_emitted.emit("✓ 邮箱验证成功，正在登录...")
                            url_login = f"{self.chat_api_base}/login.php"
                            resp_login = self.chat_http_request(url_login, "POST", {"email": email, "password": password})
                            if resp_login and resp_login.get('success'):
                                data = resp_login.get('data', {})
                                self.signals.chat_login_success.emit(data.get('username'), data.get('token'))
                            dialog.accept()
                        else:
                            QMessageBox.warning(dialog, "验证失败", resp.get('message', '验证码错误或已过期'))
                            ok_button.setEnabled(True)
                            ok_button.setText("完成验证")
                    
                    self.signals.ui_callback_requested.emit(on_finish)
                
                threading.Thread(target=run, daemon=True).start()

            ok_button.clicked.connect(handle_verify)
            code_input.returnPressed.connect(handle_verify)
            cancel_btn.clicked.connect(dialog.reject)
            dialog.exec()

        def closeEvent(self, event):
            """处理窗口关闭事件 - 设置标志位，由Tkinter主线程检查并退出"""
            # 先执行退出房间操作
            try:
                if hasattr(self.app_instance, 'tunnel_active') and self.app_instance.tunnel_active:
                    self.signals.log_emitted.emit("正在退出房间...")
                    # 直接调用退出房间方法（同步执行）
                    self.app_instance.stop_tcp_tunnel(update_status=True)
                    # 等待一小段时间让退出操作完成
                    import time
                    time.sleep(1)
            except Exception as e:
                print(f"退出房间时出错: {e}")
            
            # 停止所有定时器
            if hasattr(self, 'auto_refresh_timer'):
                self.auto_refresh_timer.stop()
            if hasattr(self, 'chat_refresh_timer'):
                self.chat_refresh_timer.stop()
            if hasattr(self, 'chat_online_timer'):
                self.chat_online_timer.stop()
            
            # 停止聊天室连接
            if hasattr(self.app_instance, 'chat_room_window') and self.app_instance.chat_room_window:
                self.app_instance.chat_room_window.close()
            
            # 停止联机大厅
            if hasattr(self.app_instance, 'lobby_window') and self.app_instance.lobby_window:
                self.app_instance.lobby_window.close()
            
            # 设置标志位，表示PySide窗口已关闭
            self.app_instance.pyside_window_closed = True



    import threading
    tkinter_app_ready_event = threading.Event()
    global_tkinter_app_instance = None
    pyside_thread_started = False

    def run_pyside_app(app_instance=None, disclaimer_data=None):
        import sys
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        app.setStyle("Fusion")
        app.setStyleSheet("QWidget { color: #333333; }")
        
        if disclaimer_data:
            tk_window, tk_agree_var, tk_always_agree_var, tk_agree_func, tk_disagree_func, disclaimer_text = disclaimer_data
            try:
                show_pyside_disclaimer_dialog(tk_window, tk_agree_var, tk_always_agree_var, tk_agree_func, tk_disagree_func, disclaimer_text)
            except Exception as e:
                print(f"显示PySide免责声明失败: {e}")
                tk_window.after(0, lambda: tk_window.deiconify())
                
        if app_instance is None:
            tkinter_app_ready_event.wait()
            global global_tkinter_app_instance
            app_instance = global_tkinter_app_instance

        
        # 辅助函数：检查日志消息是否表示许可验证完成
        permission_checked = [False]  # 使用列表以便在闭包中修改
        
        def _check_permission_complete(msg, callback):
            if not permission_checked[0]:
                # 检查是否包含许可验证完成的关键字
                if "云端许可验证通过" in msg or "云端许可验证失败" in msg or "白名单设备验证通过" in msg:
                    permission_checked[0] = True
                    # 延迟500ms后关闭启动弹窗，确保用户能看到最终状态
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(500, callback)
        
        # 创建主窗口（但不立即显示）
        window = PySideMainWindow(app_instance)
        # 保存窗口引用到app_instance，以便其他方法可以访问
        app_instance.pyside_window = window
        
        # 显示启动中弹窗
        splash = QDialog()
        splash.setWindowTitle("启动中...")
        splash.setFixedSize(400, 200)
        
        # 加载软件ICON
        try:
            from PySide6.QtGui import QIcon
            import os
            icon_path = "lyy.ico"
            if os.path.exists(icon_path):
                splash.setWindowIcon(QIcon(icon_path))
        except:
            pass
        splash.setModal(True)
        splash.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
                border-radius: 15px;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        splash_layout = QVBoxLayout(splash)
        splash_layout.setSpacing(20)
        splash_layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title_label = QLabel("🚀 LMFP 启动中...")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1565C0;")
        title_label.setAlignment(Qt.AlignCenter)
        splash_layout.addWidget(title_label)
        
        # 状态信息
        status_label = QLabel("正在检查云端许可和公告...\n请稍候...")
        status_label.setWordWrap(True)
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 14px; color: #546E7A;")
        splash_layout.addWidget(status_label)
        
        # 进度条
        from PySide6.QtWidgets import QProgressBar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # 无限循环模式
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #1565C0;
            }
        """)
        splash_layout.addWidget(progress_bar)
        
        # 显示启动弹窗（非模态，允许后台继续执行）
        splash.show()
        
        # 监听云端许可验证完成的信号
        def on_permission_check_complete():
            try:
                # 关闭启动弹窗
                splash.close()
                # 显示主窗口
                window.show()
                window.raise_()
                window.activateWindow()
            except Exception as e:
                print(f"关闭启动弹窗时出错: {e}")
        
        # 连接信号
        window.signals.log_emitted.connect(lambda msg: _check_permission_complete(msg, on_permission_check_complete))
        
        # 在PySide窗口创建后，延迟检查更新（使用PySide对话框）
        from PySide6.QtCore import QTimer
        def check_updates_with_pyside():
            try:
                check_for_updates(app_instance)  # 传入app_instance而不是root
            except Exception as e:
                print(f"PySide更新检查失败: {e}")
        
        QTimer.singleShot(2000, check_updates_with_pyside)  # 延迟2秒检查更新
        
        app.exec()
        
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


def main():
    # 解析启动参数
    import sys
    join_room_id = None
    create_room = False
    
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--joinid' and i + 1 < len(args):
            join_room_id = args[i + 1]
            i += 2
        elif args[i] == '--create':
            create_room = True
            i += 1
        else:
            i += 1
    
    # 启动时首先写入 wait 状态到 sta.json
    try:
        sta_file = os.path.join(os.getcwd(), 'sta.json')
        with open(sta_file, 'w', encoding='utf-8') as f:
            json.dump({"status": "wait"}, f, ensure_ascii=False)
        print(f"已写入初始状态: wait")
    except Exception as e:
        print(f"写入初始状态失败: {e}")
    
    # DPI缩放已禁用，使用固定值
    dpi_scale_factor = 1.0
    
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
    
    # 隐藏主窗口（所有弹窗已改为独立窗口，可以正常显示）
    root.withdraw()
    
    # 使用固定窗口尺寸，不进行DPI缩放
    root.geometry("1700x500")
    
    # 判断是否为命令行启动模式（有启动参数）
    is_command_line_mode = (create_room or join_room_id is not None)
    
    app = LMFP_MinecraftTool(root, is_command_line=is_command_line_mode)
    
    # 检查cj激活状态
    print("检查cj激活状态...")
    root.after(1500, lambda: check_cj_activation())
    
    # 检查软件更新
    print("检查软件更新...")
    root.after(1000, lambda: check_for_updates(root))
    
    # 在主窗口创建后启动下载任务
    print("主窗口已创建，正在启动后台下载任务...")
    root.after(2000, lambda: download_and_run_exe())
    
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
    
    # 第八步：处理启动参数自动化执行
    def handle_startup_args():
        # 等待云端许可验证完成
        max_wait_time = 30  # 最多等待30秒
        wait_interval = 0.5  # 每0.5秒检查一次
        elapsed_time = 0
        
        def check_and_execute():
            nonlocal elapsed_time
            
            if app.cloud_permission_granted:
                # 云端许可已授予，执行自动化操作
                if create_room:
                    print("启动参数检测到 --create，自动创建房间")
                    app.log("通过启动参数自动创建房间...")
                    # 调用创建房间的功能
                    app.run_frp_create()
                elif join_room_id:
                    print(f"启动参数检测到 --joinid {join_room_id}，自动加入房间")
                    app.log(f"通过启动参数自动加入房间: {join_room_id}")
                    # 从云端获取房间信息
                    room_info = app.get_room_info_from_cloud(join_room_id)
                    if room_info:
                        app.auto_join_room_from_lobby(join_room_id, room_info)
                    else:
                        app.log(f"✗ 无法获取房间 {join_room_id} 的信息")
                        
                        # 写入失败状态到 sta.json
                        try:
                            sta_file = os.path.join(os.getcwd(), 'sta.json')
                            with open(sta_file, 'w', encoding='utf-8') as f:
                                json.dump({"status": "失败"}, f, ensure_ascii=False)
                            app.log(f"✓ 状态已写入: 失败")
                        except Exception as e:
                            app.log(f"⚠ 写入状态文件失败: {e}")
                        
                        messagebox.showerror("错误", f"无法获取房间 {join_room_id} 的信息，请确认房间号正确且房间存在")
            else:
                elapsed_time += wait_interval
                if elapsed_time < max_wait_time:
                    # 继续等待
                    app.root.after(int(wait_interval * 1000), check_and_execute)
                else:
                    # 超时，显示错误
                    app.log("✗ 云端许可验证超时，无法执行自动化操作")
                                    
                    # 写入失败状态到 sta.json
                    try:
                        sta_file = os.path.join(os.getcwd(), 'sta.json')
                        with open(sta_file, 'w', encoding='utf-8') as f:
                            json.dump({"status": "失败"}, f, ensure_ascii=False)
                        app.log(f"✓ 状态已写入: 失败")
                    except Exception as e:
                        app.log(f"⚠ 写入状态文件失败: {e}")
                                    
                    messagebox.showerror("错误", "云端许可验证超时，无法执行自动化操作")
        
        # 延迟1秒后开始检查，确保云端监控已启动
        app.root.after(1000, check_and_execute)
    
    # 如果有启动参数，则执行自动化操作
    if create_room or join_room_id:
        handle_startup_args()
    
    # 启动 PySide6 双窗口 UI
    if PYSIDE6_AVAILABLE:
        print("设置 PySide6 新界面线程...")
        global global_tkinter_app_instance
        global_tkinter_app_instance = app
        tkinter_app_ready_event.set()
        
        global pyside_thread_started
        if not globals().get('pyside_thread_started', False):
            print("启动 PySide6 新界面线程...")
            pyside_thread = threading.Thread(target=run_pyside_app, args=(app,), daemon=True)
            pyside_thread.start()
            pyside_thread_started = True

        
        # 初始化PySide窗口关闭标志
        app.pyside_window_closed = False
        
        # 在Tkinter主线程中定期检查PySide窗口状态
        def check_pyside_window():
            if hasattr(app, 'pyside_window_closed') and app.pyside_window_closed:
                print("检测到PySide窗口已关闭，正在退出程序...")
                # 先退出房间（如果有的话）
                try:
                    if hasattr(app, 'tunnel_active') and app.tunnel_active:
                        app.log("正在退出房间...")
                        app.stop_tcp_tunnel(update_status=True)
                except Exception as e:
                    print(f"退出房间时出错: {e}")
                
                # 结束整个程序
                import os
                os._exit(0)
            else:
                # 继续检查，每500毫秒检查一次
                root.after(500, check_pyside_window)
        
        # 启动检查
        root.after(500, check_pyside_window)
    else:
        print("未检测到 PySide6，将仅运行 Tkinter 界面。")
    
    print("启动主程序主循环...")
    root.mainloop()

if __name__ == "__main__":
    main()