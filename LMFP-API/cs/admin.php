<?php
// 配置
$token = 'token';
$status_file = 'st.txt';
$counter_file = 'ggbb.txt';
$announcement_prefix = 'gg';

// API配置
$room_api_url = 'https://lytapi.asia/api.php';

// 处理表单提交
$message = '';
$message_type = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input_token = $_POST['token'] ?? '';
    
    // 验证token
    if ($input_token !== $token) {
        $message = 'Token验证失败！';
        $message_type = 'error';
    } else {
        $action = $_POST['action'] ?? '';
        
        switch ($action) {
            case 'change_status':
                $new_status = $_POST['status'] ?? '';
                if (in_array($new_status, ['true', 'false'])) {
                    if (file_put_contents($status_file, $new_status)) {
                        $message = "状态已成功更改为: $new_status";
                        $message_type = 'success';
                    } else {
                        $message = '写入状态文件失败！';
                        $message_type = 'error';
                    }
                }
                break;
                
            case 'publish_announcement':
                $content = $_POST['content'] ?? '';
                if (!empty($content)) {
                    // 读取或创建计数器
                    if (!file_exists($counter_file)) {
                        file_put_contents($counter_file, '0');
                    }
                    
                    $current_number = trim(file_get_contents($counter_file));
                    if (is_numeric($current_number)) {
                        $current_number = intval($current_number);
                        $new_number = $current_number + 1;
                        
                        // 创建公告文件
                        $new_filename = $announcement_prefix . $new_number . '.txt';
                        if (file_put_contents($new_filename, $content)) {
                            // 更新计数器
                            file_put_contents($counter_file, strval($new_number));
                            $message = "公告发布成功！文件名: $new_filename";
                            $message_type = 'success';
                        } else {
                            $message = '创建公告文件失败！';
                            $message_type = 'error';
                        }
                    } else {
                        $message = '计数器文件内容无效！';
                        $message_type = 'error';
                    }
                } else {
                    $message = '公告内容不能为空！';
                    $message_type = 'error';
                }
                break;
        }
    }
}

// 读取当前状态
$current_status = '未知';
if (file_exists($status_file)) {
    $status_content = trim(file_get_contents($status_file));
    if (in_array($status_content, ['true', 'false'])) {
        $current_status = $status_content;
    }
}

// 读取公告计数
$announcement_count = 0;
if (file_exists($counter_file)) {
    $count_content = trim(file_get_contents($counter_file));
    if (is_numeric($count_content)) {
        $announcement_count = intval($count_content);
    }
}

// 获取房间列表数据
function fetchRoomData() {
    global $room_api_url;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $room_api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    if ($response) {
        $data = json_decode($response, true);
        if (isset($data['success']) && $data['success'] && isset($data['data']['rooms'])) {
            return $data['data'];
        }
    }
    
    return null;
}

$room_data = fetchRoomData();
?>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统管理面板</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary-color: #64748b;
            --success-color: #10b981;
            --error-color: #ef4444;
            --warning-color: #f59e0b;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --border-color: #e2e8f0;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            background-color: var(--background-color);
            color: var(--text-primary);
            line-height: 1.5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: var(--card-background);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }
        
        .header h1 {
            font-size: 28px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 16px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }
        
        @media (min-width: 768px) {
            .grid {
                grid-template-columns: 1fr 1fr;
            }
        }
        
        .card {
            background: var(--card-background);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-color);
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .status-true {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .status-false {
            background-color: #fee2e2;
            color: #991b1b;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .stat-item {
            display: flex;
            flex-direction: column;
            padding: 12px;
            background: var(--background-color);
            border-radius: 8px;
        }
        
        .stat-label {
            font-size: 14px;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: var(--primary-color);
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            color: var(--text-primary);
            margin-bottom: 8px;
        }
        
        .form-input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .form-select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            background: var(--card-background);
            cursor: pointer;
        }
        
        .form-textarea {
            width: 100%;
            padding: 12px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            resize: vertical;
            min-height: 120px;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 20px;
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
            width: 100%;
        }
        
        .btn:hover {
            background-color: var(--primary-dark);
        }
        
        .message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 500;
        }
        
        .success {
            background-color: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        
        .error {
            background-color: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        
        .rooms-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }
        
        .room-item {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
            transition: background-color 0.2s;
        }
        
        .room-item:hover {
            background-color: var(--background-color);
        }
        
        .room-item:last-child {
            border-bottom: none;
        }
        
        .room-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }
        
        .room-name {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 16px;
        }
        
        .room-status {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .room-players {
            display: flex;
            align-items: center;
            font-size: 14px;
            color: var(--success-color);
            font-weight: 500;
        }
        
        .room-public {
            background-color: #dbeafe;
            color: var(--primary-color);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        
        .room-details {
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .room-detail-item {
            display: flex;
            align-items: center;
            margin-bottom: 4px;
        }
        
        .room-detail-label {
            min-width: 100px;
            color: var(--text-primary);
            font-weight: 500;
        }
        
        .room-code {
            background-color: var(--background-color);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }
        
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            color: var(--text-secondary);
        }
        
        .refresh-info {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        
        .refresh-time {
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 12px;
            }
            
            .header {
                padding: 16px;
            }
            
            .card {
                padding: 16px;
            }
            
            .room-header {
                flex-direction: column;
                gap: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LMFP-系统管理面板</h1>
            <p>系统状态管理、公告发布和房间监控</p>
        </div>
        
        <?php if ($message): ?>
            <div class="message <?php echo $message_type; ?>">
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>
        
        <div class="grid">
            <!-- 左侧：系统管理 -->
            <div class="card">
                <h2 class="card-title">系统状态管理</h2>
                
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">当前状态</span>
                        <span class="status-badge status-<?php echo $current_status; ?>">
                            <?php echo htmlspecialchars($current_status); ?>
                        </span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">公告数量</span>
                        <span class="stat-value"><?php echo $announcement_count; ?></span>
                    </div>
                </div>
                
                <!-- 修改状态表单 -->
                <form method="POST" action="" class="form-section">
                    <input type="hidden" name="action" value="change_status">
                    
                    <div class="form-group">
                        <label class="form-label">验证Token</label>
                        <input type="password" name="token" class="form-input" required placeholder="请输入验证token">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">系统状态</label>
                        <select name="status" class="form-select" required>
                            <option value="">请选择状态</option>
                            <option value="true">启用 (true)</option>
                            <option value="false">禁用 (false)</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">更新状态</button>
                </form>
            </div>
            
            <!-- 右侧：房间列表 -->
            <div class="card">
                <div class="refresh-info">
                    <h2 class="card-title">房间列表</h2>
                    <div class="refresh-time" id="refreshTime">最后更新: 刚刚</div>
                </div>
                
                <div class="rooms-container" id="roomsContainer">
                    <?php if ($room_data && isset($room_data['rooms'])): ?>
                        <?php foreach ($room_data['rooms'] as $room): ?>
                            <div class="room-item">
                                <div class="room-header">
                                    <div class="room-name"><?php echo htmlspecialchars($room['room_name']); ?></div>
                                    <div class="room-status">
                                        <span class="room-players">
                                            <?php echo "在线"; ?><!--<?php echo $room['max_players']; ?>-->
                                        </span>
                                        <span class="room-public"><?php echo $room['is_public'] ? '公开' : '私有'; ?></span>
                                    </div>
                                </div>
                                
                                <div class="room-details">
                                    <div class="room-detail-item">
                                        <span class="room-detail-label">房主:</span>
                                        <span><?php echo htmlspecialchars($room['host_player']); ?></span>
                                    </div>
                                    <div class="room-detail-item">
                                        <span class="room-detail-label">版本:</span>
                                        <span><?php echo htmlspecialchars($room['game_version']); ?></span>
                                    </div>
                                    <div class="room-detail-item">
                                        <span class="room-detail-label">描述:</span>
                                        <span><?php echo htmlspecialchars($room['description']); ?></span>
                                    </div>
                                    <div class="room-detail-item">
                                        <span class="room-detail-label">房间代码:</span>
                                        <span class="room-code"><?php echo htmlspecialchars($room['full_room_code']); ?></span>
                                    </div>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="loading">
                            正在加载房间列表...
                        </div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- 公告发布 -->
            <div class="card">
                <h2 class="card-title">发布公告</h2>
                <form method="POST" action="">
                    <input type="hidden" name="action" value="publish_announcement">
                    
                    <div class="form-group">
                        <label class="form-label">验证Token</label>
                        <input type="password" name="token" class="form-input" required placeholder="请输入验证token">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">公告内容</label>
                        <textarea name="content" class="form-textarea" required placeholder="请输入公告内容..."></textarea>
                    </div>
                    
                    <button type="submit" class="btn">发布公告</button>
                </form>
            </div>
            
            <!-- 公告列表 -->
            <div class="card">
                <h2 class="card-title">现有公告</h2>
                <div class="rooms-container">
                    <?php for ($i = 1; $i <= $announcement_count; $i++): ?>
                        <?php $filename = $announcement_prefix . $i . '.txt'; ?>
                        <?php if (file_exists($filename)): ?>
                            <div class="room-item">
                                <div class="room-header">
                                    <div class="room-name"><?php echo htmlspecialchars($filename); ?></div>
                                </div>
                                <div class="room-details">
                                    <div class="room-detail-item">
                                        <?php
                                        $content = file_get_contents($filename);
                                        $preview = mb_substr(trim($content), 0, 100, 'UTF-8');
                                        if (mb_strlen(trim($content), 'UTF-8') > 100) {
                                            $preview .= '...';
                                        }
                                        echo htmlspecialchars($preview);
                                        ?>
                                    </div>
                                </div>
                            </div>
                        <?php endif; ?>
                    <?php endfor; ?>
                    
                    <?php if ($announcement_count === 0): ?>
                        <div class="loading">
                            暂无公告
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 房间列表自动刷新
        let lastRefresh = new Date();
        
        function updateRefreshTime() {
            const now = new Date();
            const diff = Math.floor((now - lastRefresh) / 1000);
            
            let text = '最后更新: ';
            if (diff < 60) {
                text += '刚刚';
            } else if (diff < 3600) {
                text += Math.floor(diff / 60) + '分钟前';
            } else {
                text += Math.floor(diff / 3600) + '小时前';
            }
            
            document.getElementById('refreshTime').textContent = text;
        }
        
        function refreshRooms() {
            fetch(window.location.href)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newRooms = doc.getElementById('roomsContainer');
                    
                    if (newRooms) {
                        document.getElementById('roomsContainer').innerHTML = newRooms.innerHTML;
                        lastRefresh = new Date();
                        updateRefreshTime();
                    }
                })
                .catch(error => {
                    console.error('刷新失败:', error);
                });
        }
        
        // 初始设置
        updateRefreshTime();
        
        // 每3秒刷新一次房间列表
        setInterval(refreshRooms, 3000);
        
        // 每10秒更新一次时间显示
        setInterval(updateRefreshTime, 10000);
        
        // 表单提交确认
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const action = this.querySelector('input[name="action"]').value;
                    let message = '';
                    
                    if (action === 'change_status') {
                        const status = this.querySelector('select[name="status"]').value;
                        message = `确定要将系统状态更改为 "${status}" 吗？`;
                    } else if (action === 'publish_announcement') {
                        message = '确定要发布此公告吗？';
                    }
                    
                    if (message && !confirm(message)) {
                        e.preventDefault();
                    }
                });
            });
            
            // 自动清除消息
            setTimeout(() => {
                const messages = document.querySelectorAll('.message');
                messages.forEach(msg => {
                    msg.style.transition = 'opacity 0.5s';
                    msg.style.opacity = '0';
                    setTimeout(() => msg.remove(), 500);
                });
            }, 5000);
        });
    </script>
</body>
</html>