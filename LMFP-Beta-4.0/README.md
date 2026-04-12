# LMFP Beta 4.0 - Minecraft联机软件

## 项目简介
LMFP是一款专为Minecraft玩家设计的内网穿透联机软件，内置FRP内网穿透功能，支持创建和加入网络房间，让玩家能够轻松实现跨网络联机游戏。

## 技术架构
本项目基于Python开发，采用图形用户界面设计，支持Windows平台运行。

## 依赖的Python标准库

### 核心系统库
- `os` - 操作系统接口
- `sys` - 系统特定参数和函数
- `platform` - 访问底层平台标识数据

### 网络通信库
- `socket` - 底层网络接口
- `urllib.parse` - URL解析工具
- `urllib.request` - URL打开工具
- `urllib.error` - URL异常处理

### 并发处理库
- `threading` - 线程处理
- `concurrent.futures` - 异步执行框架
- `queue` - 队列数据结构

### 图形界面库
- `tkinter` - Python标准GUI库
- `tkinter.ttk` - Tk主题部件
- `tkinter.messagebox` - 消息框组件
- `tkinter.scrolledtext` - 滚动文本组件

### 系统集成库
- `ctypes` - C语言兼容的数据类型
- `ctypes.wintypes` - Windows数据类型
- `subprocess` - 子进程管理

### 数据处理库
- `json` - JSON数据解析
- `hashlib` - 安全哈希和消息摘要
- `re` - 正则表达式操作

### 时间和随机数库
- `datetime` - 日期和时间处理
- `time` - 时间访问和转换
- `random` - 伪随机数生成器
- `string` - 常用字符串操作

### 实用工具库
- `atexit` - 退出处理器
- `signal` - 异步事件通知机制
- `webbrowser` - 方便的Web浏览器控制器

## 第三方依赖库

### 必需依赖
- `mcstatus` - Minecraft服务器状态查询库（可选，用于服务器检测功能）

## 项目特点

### 主要功能
1. **内网穿透联机** - 通过FRP技术实现跨网络联机
2. **房间系统** - 支持创建和加入网络房间
3. **自动更新** - 内置软件更新机制
4. **云端公告** - 实时获取软件公告信息
5. **心跳机制** - 维持连接活跃状态
6. **多播发现** - 局域网内的服务器发现

### 技术特性
- 黑白灰简约UI设计
- 多线程异步处理
- 异常安全的网络通信
- 自动化的进程管理
- 完善的错误处理机制

## 系统要求
- Windows操作系统
- Python 3.8+
- 网络连接


## 注意事项
- 本软件、代码仅供学习和技术研究使用
- 请遵守相关法律法规和Minecraft使用条款
- 建议在测试环境中使用内网穿透功能

---
*最后更新：2026年2月23日*