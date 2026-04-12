<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LMFP · 公告板 (仅显示有效)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: #f4f6fa;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 2rem 1rem;
        }

        /* 主卡片 — 极简干净 */
        .board {
            max-width: 800px;
            width: 100%;
            background: #ffffff;
            border-radius: 28px;
            box-shadow: 0 20px 35px -8px rgba(0, 10, 30, 0.15), 0 1px 3px rgba(0,0,0,0.02);
            padding: 2.5rem 2.2rem;
            transition: all 0.2s ease;
        }

        /* 标头 — LMFP 联机软件 */
        .header {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            border-bottom: 1px solid #e6ecf2;
            padding-bottom: 0.9rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .header h1 {
            font-size: 1.9rem;
            font-weight: 580;
            letter-spacing: -0.02em;
            color: #0c1f33;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .header h1 span {
            background: #eef3f9;
            color: #1f4975;
            font-size: 1rem;
            font-weight: 500;
            padding: 0.2rem 0.8rem;
            border-radius: 40px;
            margin-left: 0.5rem;
            letter-spacing: normal;
        }

        .badge-count {
            background: #d9e4f0;
            color: #1f3b5c;
            border-radius: 30px;
            padding: 0.3rem 1.1rem;
            font-size: 0.9rem;
            font-weight: 500;
            border: 1px solid #cddbe9;
        }

        /* 公告列表 */
        .announce-list {
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        /* 单个公告卡片 — 轻盈无边框 */
        .ann-item {
            background: #f9fbfe;
            border-radius: 20px;
            padding: 1.4rem 1.8rem;
            border: 1px solid #eef2f7;
            transition: background 0.15s;
        }

        .ann-item:hover {
            background: #f6f9ff;
            border-color: #dbe4f0;
        }

        /* 公告头部 (编号 + 装饰) */
        .ann-title {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
        }

        .ann-badge {
            background: #d6e3ff;
            color: #1d4d8c;
            font-weight: 600;
            font-size: 0.85rem;
            padding: 0.2rem 0.9rem;
            border-radius: 30px;
            letter-spacing: 0.3px;
            border: 1px solid #c1d4f0;
        }

        .ann-filename {
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 0.8rem;
            color: #687e9c;
            background: #eef2f8;
            padding: 0.2rem 0.7rem;
            border-radius: 30px;
            border: 1px solid #dfe6f0;
        }

        /* 正文内容 — 保留换行、空格，干净可读 */
        .ann-content {
            font-size: 1.05rem;
            line-height: 1.6;
            color: #1e2f41;
            white-space: pre-wrap;          /* 保留 \n 换行 */
            word-break: break-word;
            background: transparent;
            border-left: 3px solid transparent;
            padding-left: 0.2rem;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* 空状态 / 错误提示 */
        .info-box {
            background: #f1f5fb;
            border-radius: 18px;
            padding: 2.2rem 2rem;
            text-align: center;
            color: #4f658d;
            font-size: 1.1rem;
            border: 1px dashed #c7d8ec;
        }

        .info-box i {
            display: block;
            font-size: 2rem;
            margin-bottom: 0.8rem;
            opacity: 0.5;
        }

        .footnote {
            margin-top: 2.2rem;
            border-top: 1px solid #e3eaf2;
            padding-top: 1.2rem;
            display: flex;
            justify-content: space-between;
            color: #7d92b0;
            font-size: 0.9rem;
            flex-wrap: wrap;
        }

        .footnote a {
            color: #2b5a9e;
            text-decoration: none;
            border-bottom: 1px dotted #9bb5da;
        }

        .footnote a:hover {
            border-bottom: 1px solid #1f4975;
        }

        /* 加载中极简动画 */
        .loading-dots:after {
            content: '.';
            animation: dots 1.2s steps(1, end) infinite;
        }

        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60% { content: '...'; }
            80%, 100% { content: ''; }
        }

        /* 自适应 */
        @media (max-width: 480px) {
            .board { padding: 1.8rem 1.2rem; }
            .ann-item { padding: 1.2rem 1.2rem; }
            .header h1 { font-size: 1.6rem; }
        }
    </style>
</head>
<body>
    <div class="board">
        <div class="header">
            <h1>
                LMFP 联机软件
                <span>公告</span>
            </h1>
            <div class="badge-count" id="countDisplay">读取中…</div>
        </div>

        <div id="announcementContainer" class="announce-list">
            <!-- 动态插入公告 -->
            <div class="info-box" id="loadingIndicator">
                <i>📄</i> 正在加载公告列表…
            </div>
        </div>

        <div class="footnote">
            <span>⚡ 实时同步 · LMFP 官方频道 (仅显示有效公告)</span>
            <span><a href="ggbb.txt" target="_blank">ggbb.txt</a> 配置 · 公告 1..n</span>
        </div>
    </div>

    <script>
        (function() {
            // --- LMFP 公告页面逻辑 (修改版：无法读取的公告不显示) ---
            // 读取 ggbb.txt 得到数字 n，然后读取 gg1.txt ... gg<n>.txt 的内容并展示
            const CONFIG_FILE = 'ggbb.txt';            // 配置文件，仅包含一个数字 (1~n)
            const FILE_PREFIX = 'gg';                   // 公告文件名前缀 gg
            const FILE_SUFFIX = '.txt';                  // 后缀

            const container = document.getElementById('announcementContainer');
            const countDisplay = document.getElementById('countDisplay');

            // 显示加载失败或者无公告的统一方法
            function showError(message, details = '') {
                container.innerHTML = `
                    <div class="info-box">
                        <i>📭</i> ${message}
                        ${details ? `<br><span style="font-size:0.9rem; opacity:0.7;">${details}</span>` : ''}
                    </div>
                `;
                countDisplay.textContent = '暂无可读';
            }

            // 从 ggbb.txt 获取数字 n
            async function fetchConfigNumber() {
                try {
                    const response = await fetch(CONFIG_FILE, { cache: 'no-store' }); // 禁用缓存保证实时
                    if (!response.ok) {
                        throw new Error(`无法读取配置文件 (HTTP ${response.status})`);
                    }
                    let text = await response.text();
                    text = text.trim();                // 去除首尾空白
                    if (text.length === 0) {
                        throw new Error('配置文件为空');
                    }
                    // 提取第一个数字 (忽略其他字符，比如注释或换行)
                    const match = text.match(/\d+/);
                    if (!match) {
                        throw new Error('配置文件中未找到有效数字');
                    }
                    const num = parseInt(match[0], 10);
                    if (isNaN(num) || num < 1) {
                        throw new Error('数字必须 ≥1');
                    }
                    return num;
                } catch (e) {
                    console.warn('读取 ggbb.txt 失败:', e);
                    throw e; // 向上传递
                }
            }

            // 读取单个公告文件 gg{index}.txt
            async function fetchAnnouncementFile(index) {
                const fileName = `${FILE_PREFIX}${index}${FILE_SUFFIX}`;
                try {
                    const response = await fetch(fileName, { cache: 'no-store' });
                    if (!response.ok) {
                        // 文件不存在或无法访问 -> 返回 null（表示不显示）
                        return null;
                    }
                    let content = await response.text();
                    // 如果内容为空，可以选择不显示，或者显示占位符。这里决定：空内容也不显示（保持干净）
                    if (!content || content.trim().length === 0) {
                        return null; // 空文件也不显示
                    }
                    return {
                        index,
                        fileName,
                        content: content,   // 保留原始文本 (含换行)
                    };
                } catch (err) {
                    // 任何加载错误都不显示
                    return null;
                }
            }

            // 主流程: 获取n -> 并发读取所有公告 -> 渲染 (仅显示有效公告)
            async function loadAnnouncements() {
                // 显示初始加载状态
                container.innerHTML = `<div class="info-box"><i>⏳</i> 读取配置 <span class="loading-dots"></span></div>`;
                let totalAnnouncements = 0;

                try {
                    // 1. 获取公告数量 n
                    const n = await fetchConfigNumber();
                    totalAnnouncements = n;
                    countDisplay.textContent = `共 ${n} 条`;

                    if (n === 0) {
                        showError('配置文件 ggbb.txt 内容为 0，没有公告');
                        return;
                    }

                    // 更新提示为正在加载具体公告
                    container.innerHTML = `<div class="info-box"><i>📂</i> 正在加载 1 至 ${n} 号公告…</div>`;

                    // 2. 创建所有文件的读取任务 (index 从1到n)
                    const fetchTasks = [];
                    for (let i = 1; i <= n; i++) {
                        fetchTasks.push(fetchAnnouncementFile(i));
                    }

                    // 3. 并发执行
                    const results = await Promise.all(fetchTasks);

                    // 4. 过滤掉 null（无法读取的公告）和空内容的公告
                    const validAnnouncements = results.filter(item => item !== null);

                    // 5. 按 index 从大到小排序 (大到小显示)
                    validAnnouncements.sort((a, b) => b.index - a.index);

                    // 6. 渲染公告列表
                    if (validAnnouncements.length === 0) {
                        showError('没有可显示的公告', '所有公告文件可能缺失或为空');
                        countDisplay.textContent = `共 ${n} 条 (0 条有效)`;
                    } else {
                        // 更新计数显示：有效条数 / 总条数
                        countDisplay.textContent = `共 ${n} 条 (显示 ${validAnnouncements.length} 条)`;
                        renderAnnouncements(validAnnouncements);
                    }

                } catch (error) {
                    // 处理配置读取失败的情况
                    console.error('公告加载失败:', error);
                    showError('无法加载公告配置', error.message);
                    countDisplay.textContent = '配置错误';
                }
            }

            // 将公告数据渲染到页面
            function renderAnnouncements(announcements) {
                if (!announcements || announcements.length === 0) {
                    showError('没有可显示的公告');
                    return;
                }

                // 构建 HTML
                let htmlStr = '';
                for (const item of announcements) {
                    const idx = item.index;
                    const fileName = item.fileName;
                    const content = item.content;

                    // 正常显示内容 (保留原始换行)
                    htmlStr += `
                        <div class="ann-item">
                            <div class="ann-title">
                                <span class="ann-badge">公告 #${idx}</span>
                                <span class="ann-filename">${fileName}</span>
                            </div>
                            <div class="ann-content">${escapeHtml(content)}</div>
                        </div>
                    `;
                }

                container.innerHTML = htmlStr;
            }

            // 简单的转义函数 (防止XSS, 虽然大概率是文本文件)
            function escapeHtml(unsafe) {
                if (!unsafe) return '';
                return unsafe
                    .replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;")
                    .replace(/"/g, "&quot;")
                    .replace(/'/g, "&#039;")
                    .replace(/`/g, "&#96;");      // 反引号也可转义
            }

            // 启动一切
            loadAnnouncements();

            // 可选：每60秒自动刷新 (保持简洁，不加自动刷新，但可手动)
            // setInterval(() => {
            //     loadAnnouncements();
            // }, 60000);
        })();
    </script>
    <!-- 附加说明：符合需求——读取gg数字(1~n).txt，n来自ggbb.txt，页面简洁，编号从大到小显示，无法读取的公告不显示 -->
</body>
</html>