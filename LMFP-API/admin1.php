<?php
// 配置
$token = 'xxxxxxxxxxx';
$status_file = 'st.txt';
$counter_file = 'ggbb.txt';
$announcement_prefix = 'gg';

// API配置
$room_api_url = 'https://lytapi.asia/api.php';
$chat_api_url = 'https://lytapi.asia/public_chat/data/messages.txt';
$ping_api_url = 'https://lytapi.asia/ping.php';

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
                
            case 'upload_update':
                // 处理软件更新包上传
                if (isset($_FILES['update_file']) && $_FILES['update_file']['error'] == 0) {
                    $target_dir = "dl/";
                    if (!is_dir($target_dir)) {
                        mkdir($target_dir, 0755, true);
                    }
                    
                    $target_file = $target_dir . "lmfp.zip";
                    $fileType = strtolower(pathinfo($target_file, PATHINFO_EXTENSION));
                    
                    // 检查文件是否为ZIP格式
                    if ($fileType == "zip") {
                        if (move_uploaded_file($_FILES["update_file"]["tmp_name"], $target_file)) {
                            $message = "更新包上传成功！";
                            $message_type = 'success';
                        } else {
                            $message = "更新包上传失败！";
                            $message_type = 'error';
                        }
                    } else {
                        $message = "只允许上传ZIP文件！";
                        $message_type = 'error';
                    }
                } else {
                    $message = "未选择文件或上传出错！";
                    $message_type = 'error';
                }
                break;
                
            case 'update_version':
                // 更新版本号
                $new_version = $_POST['version'] ?? '';
                if (!empty($new_version)) {
                    $version_file = 'v.txt';
                    if (file_put_contents($version_file, $new_version)) {
                        $message = "版本号已更新为: $new_version";
                        $message_type = 'success';
                    } else {
                        $message = '版本号更新失败！';
                        $message_type = 'error';
                    }
                } else {
                    $message = '版本号不能为空！';
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

// 获取聊天消息数据
function fetchChatData() {
    global $chat_api_url;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $chat_api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    if ($response) {
        $data = json_decode($response, true);
        if (is_array($data)) {
            // 按时间戳降序排序（最新的在前）
            usort($data, function($a, $b) {
                return $b['timestamp'] - $a['timestamp'];
            });
            return $data;
        }
    }
    
    return null;
}

// 获取FRP节点延迟数据
function fetchPingData() {
    global $ping_api_url;
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $ping_api_url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    $nodes = [];
    
    if ($response) {
        $lines = explode("\n", trim($response));
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            // 解析每行数据格式：1#Lyt_IT官方-山东青岛阿里云 - 超时（错误码：110，信息：Connection timed out）
            if (preg_match('/^(\d+)#(.+?) - (.+)$/', $line, $matches)) {
                $node = [
                    'id' => intval($matches[1]),
                    'name' => trim($matches[2]),
                    'status' => trim($matches[3])
                ];
                
                // 解析延迟或错误信息
                if (strpos($node['status'], 'ms') !== false) {
                    // 提取延迟数值
                    if (preg_match('/(\d+)ms/', $node['status'], $delay_matches)) {
                        $node['delay'] = intval($delay_matches[1]);
                        $node['is_online'] = true;
                    }
                } else {
                    // 超时或错误
                    $node['is_online'] = false;
                    if (preg_match('/错误码：(\d+)/', $node['status'], $error_matches)) {
                        $node['error_code'] = intval($error_matches[1]);
                    }
                }
                
                $nodes[] = $node;
            }
        }
    }
    
    return $nodes;
}

$room_data = fetchRoomData();
$chat_data = fetchChatData();
$ping_data = fetchPingData();

// 计算节点统计
$node_stats = [
    'total' => count($ping_data),
    'online' => 0,
    'offline' => 0,
    'avg_delay' => 0
];

if (!empty($ping_data)) {
    $total_delay = 0;
    $online_count = 0;
    
    foreach ($ping_data as $node) {
        if (isset($node['is_online']) && $node['is_online']) {
            $node_stats['online']++;
            $online_count++;
            if (isset($node['delay'])) {
                $total_delay += $node['delay'];
            }
        } else {
            $node_stats['offline']++;
        }
    }
    
    if ($online_count > 0) {
        $node_stats['avg_delay'] = round($total_delay / $online_count, 1);
    }
}
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
            --chat-sender-color: #3b82f6;
            --chat-time-color: #94a3b8;
            --chat-bg-odd: #f8fafc;
            --chat-bg-even: #ffffff;
            --node-online: #10b981;
            --node-offline: #ef4444;
            --node-warning: #f59e0b;
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
            max-width: 1600px;
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
        
        @media (min-width: 1024px) {
            .grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        .card {
            background: var(--card-background);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }
        
        .card-full {
            grid-column: 1 / -1;
            margin-bottom: 32px;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--border-color);
        }
        
        /* 节点卡片网格布局 - 每行显示4个节点 */
        .nodes-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        
        /* 响应式调整 - 在不同屏幕尺寸下的适配 */
        @media (max-width: 1400px) {
            .nodes-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        @media (max-width: 1100px) {
            .nodes-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .nodes-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* 节点卡片样式 */
        .node-card {
            background: var(--card-background);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .node-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            border-color: var(--primary-color);
        }
        
        /* 节点状态指示条 */
        .node-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                <?php echo isset($node['is_online']) && $node['is_online'] ? 'var(--success-color)' : 'var(--error-color)'; ?> 0%, 
                <?php echo isset($node['is_online']) && $node['is_online'] ? 'var(--success-color)' : 'var(--error-color)'; ?> 100%);
        }
        
        .node-card.online::before {
            background: linear-gradient(90deg, var(--success-color), #34d399);
        }
        
        .node-card.offline::before {
            background: linear-gradient(90deg, var(--error-color), #f87171);
        }
        
        .node-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        
        .node-title {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
        }
        
        .node-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: var(--background-color);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            font-weight: 600;
            color: var(--primary-color);
            flex-shrink: 0;
        }
        
        .node-name {
            font-weight: 600;
            font-size: 14px;
            color: var(--text-primary);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .node-id {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 2px;
        }
        
        .node-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
            flex-shrink: 0;
        }
        
        .badge-online {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .badge-offline {
            background-color: #fee2e2;
            color: #991b1b;
        }
        
        .node-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin: 12px 0;
            padding: 8px;
            background: var(--background-color);
            border-radius: 8px;
        }
        
        .node-stat {
            text-align: center;
        }
        
        .node-stat-label {
            font-size: 11px;
            color: var(--text-secondary);
            margin-bottom: 2px;
        }
        
        .node-stat-value {
            font-size: 16px;
            font-weight: 600;
        }
        
        .delay-excellent {
            color: #059669;
        }
        
        .delay-good {
            color: #2563eb;
        }
        
        .delay-medium {
            color: #d97706;
        }
        
        .delay-poor {
            color: #dc2626;
        }
        
        .node-info {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        
        .node-info-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
        }
        
        .node-info-label {
            min-width: 40px;
            color: var(--text-secondary);
        }
        
        .node-info-value {
            color: var(--text-primary);
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .node-error-message {
            background: #fee2e2;
            color: #991b1b;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            margin-top: 8px;
            border: 1px solid #fecaca;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .node-footer {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px dashed var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .node-timestamp {
            font-size: 10px;
            color: var(--text-secondary);
        }
        
        .node-status-indicator {
            display: flex;
            align-items: center;
            gap: 4px;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.online {
            background-color: var(--success-color);
        }
        
        .status-dot.offline {
            background-color: var(--error-color);
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        /* 加载动画 */
        .loading-spinner {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 200px;
            grid-column: 1/-1;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border-color);
            border-top-color: var(--primary-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
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
        
        .stats-grid-3 {
            grid-template-columns: repeat(3, 1fr);
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
        
        .node-delay {
            color: var(--success-color);
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
        
        /* 聊天消息样式 */
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: var(--background-color);
        }
        
        .chat-message {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .chat-message:nth-child(odd) {
            background-color: var(--chat-bg-odd);
        }
        
        .chat-message:nth-child(even) {
            background-color: var(--chat-bg-even);
        }
        
        .chat-message:last-child {
            border-bottom: none;
        }
        
        .chat-message:hover {
            background-color: rgba(59, 130, 246, 0.05);
        }
        
        .chat-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        
        .chat-sender {
            font-weight: 600;
            color: var(--chat-sender-color);
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .sender-id {
            background-color: var(--border-color);
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 11px;
            color: var(--text-secondary);
        }
        
        .chat-time {
            font-size: 12px;
            color: var(--chat-time-color);
        }
        
        .chat-content {
            font-size: 14px;
            color: var(--text-primary);
            line-height: 1.5;
            word-break: break-word;
        }
        
        .chat-ip {
            font-size: 11px;
            color: var(--text-secondary);
            font-family: monospace;
            margin-top: 4px;
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
        
        .chat-stats {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            font-size: 14px;
        }
        
        .chat-stat-item {
            background: var(--background-color);
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
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
            
            .node-header {
                flex-direction: column;
                gap: 8px;
            }
            
            .chat-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 4px;
            }
            
            .chat-stats {
                flex-direction: column;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid-3 {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LMFP-系统管理面板</h1>
            <p>系统状态管理、公告发布、房间监控和聊天管理</p>
        </div>
        
        <?php if ($message): ?>
            <div class="message <?php echo $message_type; ?>">
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>
        
        <!-- FRP节点监控 - 每行4个节点 -->
        <div class="card card-full">
            <div class="refresh-info">
                <h2 class="card-title">FRP节点延迟监测 (每行4节点)</h2>
                <div class="refresh-time" id="nodeRefreshTime">最后更新: 刚刚</div>
            </div>
            
            <div class="stats-grid stats-grid-3">
                <div class="stat-item">
                    <span class="stat-label">总节点数</span>
                    <span class="stat-value"><?php echo $node_stats['total']; ?></span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">在线节点</span>
                    <span class="stat-value node-delay"><?php echo $node_stats['online']; ?></span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">离线节点</span>
                    <span class="stat-value node-delay"><?php echo $node_stats['offline']; ?></span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">平均延迟</span>
                    <span class="stat-value node-delay"><?php echo $node_stats['avg_delay']; ?>ms</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">在线率</span>
                    <span class="stat-value node-delay">
                        <?php 
                        if ($node_stats['total'] > 0) {
                            echo round(($node_stats['online'] / $node_stats['total']) * 100, 1) . '%';
                        } else {
                            echo '0%';
                        }
                        ?>
                    </span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">当前时间</span>
                    <span class="stat-value" id="currentTime"><?php echo date('H:i:s'); ?></span>
                </div>
            </div>
            
            <!-- 节点卡片网格 - 每行4个 -->
            <div class="nodes-grid" id="nodesGrid">
                <?php if (!empty($ping_data)): ?>
                    <?php foreach ($ping_data as $node): ?>
                        <div class="node-card <?php echo $node['is_online'] ? 'online' : 'offline'; ?>">
                            <div class="node-header">
                                <div class="node-title">
                                    <div class="node-icon">
                                        <?php echo $node['id']; ?>
                                    </div>
                                    <div>
                                        <div class="node-name" title="<?php echo htmlspecialchars($node['name']); ?>">
                                            <?php echo htmlspecialchars(mb_substr($node['name'], 0, 20)); ?>
                                            <?php if(mb_strlen($node['name']) > 20) echo '...'; ?>
                                        </div>
                                        <div class="node-id">节点ID: #<?php echo $node['id']; ?></div>
                                    </div>
                                </div>
                                <div class="node-badge <?php echo $node['is_online'] ? 'badge-online' : 'badge-offline'; ?>">
                                    <?php echo $node['is_online'] ? '在线' : '离线'; ?>
                                </div>
                            </div>
                            
                            <div class="node-stats">
                                <?php if ($node['is_online'] && isset($node['delay'])): ?>
                                    <?php 
                                    $delay_class = 'delay-medium';
                                    if ($node['delay'] < 50) {
                                        $delay_class = 'delay-excellent';
                                    } elseif ($node['delay'] < 100) {
                                        $delay_class = 'delay-good';
                                    } elseif ($node['delay'] < 200) {
                                        $delay_class = 'delay-medium';
                                    } else {
                                        $delay_class = 'delay-poor';
                                    }
                                    ?>
                                    <div class="node-stat">
                                        <div class="node-stat-label">当前延迟</div>
                                        <div class="node-stat-value <?php echo $delay_class; ?>">
                                            <?php echo $node['delay']; ?>ms
                                        </div>
                                    </div>
                                    <div class="node-stat">
                                        <div class="node-stat-label">状态</div>
                                        <div class="node-stat-value" style="color: var(--success-color);">
                                            🛜 正常
                                        </div>
                                    </div>
                                <?php else: ?>
                                    <div class="node-stat">
                                        <div class="node-stat-label">状态</div>
                                        <div class="node-stat-value" style="color: var(--error-color);">
                                            ⚠️ 离线
                                        </div>
                                    </div>
                                    <div class="node-stat">
                                        <div class="node-stat-label">错误码</div>
                                        <div class="node-stat-value" style="color: var(--error-color);">
                                            <?php echo $node['error_code'] ?? '未知'; ?>
                                        </div>
                                    </div>
                                <?php endif; ?>
                            </div>
                            
                            <div class="node-info">
                                <div class="node-info-item">
                                    <span class="node-info-label">延迟:</span>
                                    <span class="node-info-value">
                                        <?php if ($node['is_online'] && isset($node['delay'])): ?>
                                            <span class="<?php echo $delay_class; ?>">
                                                <?php echo $node['delay']; ?>ms
                                                <?php
                                                if ($node['delay'] < 50) {
                                                    echo '(优秀)';
                                                } elseif ($node['delay'] < 100) {
                                                    echo '(良好)';
                                                } elseif ($node['delay'] < 200) {
                                                    echo '(一般)';
                                                } else {
                                                    echo '(较差)';
                                                }
                                                ?>
                                            </span>
                                        <?php else: ?>
                                            <span style="color: var(--error-color);">超时</span>
                                        <?php endif; ?>
                                    </span>
                                </div>
                                
                                <?php if (!$node['is_online']): ?>
                                    <div class="node-error-message" title="<?php echo htmlspecialchars($node['status']); ?>">
                                        <?php echo htmlspecialchars(mb_substr($node['status'], 0, 30)); ?>
                                        <?php if(mb_strlen($node['status']) > 30) echo '...'; ?>
                                    </div>
                                <?php endif; ?>
                            </div>
                            
                            <div class="node-footer">
                                <div class="node-timestamp">
                                    <?php echo date('H:i:s'); ?> 更新
                                </div>
                                <div class="node-status-indicator">
                                    <span class="status-dot <?php echo $node['is_online'] ? 'online' : 'offline'; ?>"></span>
                                    <span style="font-size: 11px; color: var(--text-secondary);">
                                        <?php echo $node['is_online'] ? '正常' : '断开'; ?>
                                    </span>
                                </div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <div style="margin-top: 16px; color: var(--text-secondary);">正在加载节点数据...</div>
                    </div>
                <?php endif; ?>
            </div>
        </div>
        
        <div class="grid">
            <!-- 第一行：系统管理和房间列表 -->
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
            
            <!-- 房间列表 -->
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
                                            <?php echo "在线"; ?>
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
            
            <!-- 聊天区 -->
            <div class="card">
                <div class="refresh-info">
                    <h2 class="card-title">公共聊天区</h2>
                    <div class="refresh-time" id="chatRefreshTime">最后更新: 刚刚</div>
                </div>
                
                <div class="chat-stats">
                    <div class="chat-stat-item">
                        总消息数: <strong><?php echo $chat_data ? count($chat_data) : 0; ?></strong>
                    </div>
                    <div class="chat-stat-item">
                        最近1小时: <strong>
                            <?php
                            if ($chat_data) {
                                $one_hour_ago = time() - 3600;
                                $recent_count = 0;
                                foreach ($chat_data as $msg) {
                                    if ($msg['timestamp'] > $one_hour_ago) {
                                        $recent_count++;
                                    }
                                }
                                echo $recent_count;
                            } else {
                                echo '0';
                            }
                            ?>
                        </strong>
                    </div>
                </div>
                
                <div class="chat-container" id="chatContainer">
                    <?php if ($chat_data): ?>
                        <?php foreach ($chat_data as $index => $msg): ?>
                            <div class="chat-message" data-id="<?php echo $msg['id']; ?>">
                                <div class="chat-header">
                                    <div class="chat-sender">
                                        <span><?php echo htmlspecialchars($msg['sender']); ?></span>
                                        <span class="sender-id">#<?php echo $msg['sender_id']; ?></span>
                                    </div>
                                    <div class="chat-time" data-timestamp="<?php echo $msg['timestamp']; ?>">
                                        <?php 
                                        $time_diff = time() - $msg['timestamp'];
                                        if ($time_diff < 60) {
                                            echo '刚刚';
                                        } elseif ($time_diff < 3600) {
                                            echo floor($time_diff / 60) . '分钟前';
                                        } elseif ($time_diff < 86400) {
                                            echo floor($time_diff / 3600) . '小时前';
                                        } else {
                                            echo date('Y-m-d H:i', $msg['timestamp']);
                                        }
                                        ?>
                                    </div>
                                </div>
                                <div class="chat-content">
                                    <?php echo htmlspecialchars($msg['content']); ?>
                                </div>
                                <div class="chat-ip">
                                    <!--IP: <?php echo htmlspecialchars($msg['ip']); ?>-->
                                </div>
                            </div>
                        <?php endforeach; ?>
                    <?php else: ?>
                        <div class="loading">
                            正在加载聊天消息...
                        </div>
                    <?php endif; ?>
                </div>
            </div>
            
            <!-- 软件更新 -->
            <div class="card">
                <h2 class="card-title">软件更新</h2>
                
                <!-- 上传更新包 -->
                <form method="POST" action="" enctype="multipart/form-data" style="margin-bottom: 30px;">
                    <a href="upd.php" class="btn">重定向</a>
                </form>
                
                <hr>
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
            
            <!-- 现有公告 -->
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
        // 节点监控自动刷新
        let lastNodeRefresh = new Date();
        
        function updateNodeRefreshTime() {
            const now = new Date();
            const diff = Math.floor((now - lastNodeRefresh) / 1000);
            
            let text = '最后更新: ';
            if (diff < 10) {
                text += '刚刚';
            } else if (diff < 60) {
                text += diff + '秒前';
            } else if (diff < 3600) {
                text += Math.floor(diff / 60) + '分钟前';
            } else {
                text += Math.floor(diff / 3600) + '小时前';
            }
            
            document.getElementById('nodeRefreshTime').textContent = text;
        }
        
        function refreshNodes() {
            // 添加一个随机参数防止缓存
            const url = window.location.href + (window.location.href.includes('?') ? '&' : '?') + '_t=' + Date.now();
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    
                    // 获取新的节点数据
                    const newNodesGrid = doc.querySelector('.nodes-grid');
                    const newStatsGrid = doc.querySelector('.stats-grid.stats-grid-3');
                    
                    if (newNodesGrid && newStatsGrid) {
                        // 更新节点网格
                        document.getElementById('nodesGrid').innerHTML = newNodesGrid.innerHTML;
                        
                        // 更新统计数据
                        const statsContainer = document.querySelector('.card-full .stats-grid.stats-grid-3');
                        if (statsContainer) {
                            statsContainer.innerHTML = newStatsGrid.innerHTML;
                        }
                        
                        // 更新最后刷新时间
                        lastNodeRefresh = new Date();
                        updateNodeRefreshTime();
                        
                        // 更新页面上的总更新时间
                        const timeElement = document.getElementById('currentTime');
                        if (timeElement) {
                            const now = new Date();
                            const timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                                         now.getMinutes().toString().padStart(2, '0') + ':' + 
                                         now.getSeconds().toString().padStart(2, '0');
                            timeElement.textContent = timeStr;
                        }
                    }
                })
                .catch(error => {
                    console.error('刷新节点数据失败:', error);
                    // 即使失败也更新时间，显示尝试刷新
                    lastNodeRefresh = new Date();
                    updateNodeRefreshTime();
                });
        }
        
        // 房间列表自动刷新
        let lastRoomRefresh = new Date();
        
        function updateRoomRefreshTime() {
            const now = new Date();
            const diff = Math.floor((now - lastRoomRefresh) / 1000);
            
            let text = '最后更新: ';
            if (diff < 10) {
                text += '刚刚';
            } else if (diff < 60) {
                text += diff + '秒前';
            } else if (diff < 3600) {
                text += Math.floor(diff / 60) + '分钟前';
            } else {
                text += Math.floor(diff / 3600) + '小时前';
            }
            
            document.getElementById('refreshTime').textContent = text;
        }
        
        function refreshRooms() {
            const url = window.location.href + (window.location.href.includes('?') ? '&' : '?') + '_t=' + Date.now();
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newRooms = doc.getElementById('roomsContainer');
                    
                    if (newRooms) {
                        document.getElementById('roomsContainer').innerHTML = newRooms.innerHTML;
                        lastRoomRefresh = new Date();
                        updateRoomRefreshTime();
                    }
                })
                .catch(error => {
                    console.error('刷新房间列表失败:', error);
                    lastRoomRefresh = new Date();
                    updateRoomRefreshTime();
                });
        }
        
        // 聊天消息自动刷新
        let lastChatRefresh = new Date();
        
        function updateChatRefreshTime() {
            const now = new Date();
            const diff = Math.floor((now - lastChatRefresh) / 1000);
            
            let text = '最后更新: ';
            if (diff < 10) {
                text += '刚刚';
            } else if (diff < 60) {
                text += diff + '秒前';
            } else if (diff < 3600) {
                text += Math.floor(diff / 60) + '分钟前';
            } else {
                text += Math.floor(diff / 3600) + '小时前';
            }
            
            document.getElementById('chatRefreshTime').textContent = text;
        }
        
        function refreshChat() {
            const url = window.location.href + (window.location.href.includes('?') ? '&' : '?') + '_t=' + Date.now();
            
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newChat = doc.getElementById('chatContainer');
                    const newChatStats = doc.querySelector('.chat-stats');
                    
                    if (newChat) {
                        document.getElementById('chatContainer').innerHTML = newChat.innerHTML;
                        if (newChatStats) {
                            document.querySelector('.chat-stats').innerHTML = newChatStats.innerHTML;
                        }
                        lastChatRefresh = new Date();
                        updateChatRefreshTime();
                        updateRelativeTimes();
                    }
                })
                .catch(error => {
                    console.error('刷新聊天消息失败:', error);
                    lastChatRefresh = new Date();
                    updateChatRefreshTime();
                });
        }
        
        // 更新时间显示为相对时间
        function updateRelativeTimes() {
            const timeElements = document.querySelectorAll('.chat-time[data-timestamp]');
            const now = Math.floor(Date.now() / 1000);
            
            timeElements.forEach(element => {
                const timestamp = parseInt(element.getAttribute('data-timestamp'));
                const diff = now - timestamp;
                
                let timeText;
                if (diff < 60) {
                    timeText = '刚刚';
                } else if (diff < 3600) {
                    timeText = Math.floor(diff / 60) + '分钟前';
                } else if (diff < 86400) {
                    timeText = Math.floor(diff / 3600) + '小时前';
                } else {
                    const date = new Date(timestamp * 1000);
                    timeText = date.getFullYear() + '-' + 
                               (date.getMonth() + 1).toString().padStart(2, '0') + '-' + 
                               date.getDate().toString().padStart(2, '0') + ' ' + 
                               date.getHours().toString().padStart(2, '0') + ':' + 
                               date.getMinutes().toString().padStart(2, '0');
                }
                
                element.textContent = timeText;
            });
        }
        
        // 更新当前时间
        function updateCurrentTime() {
            const timeElement = document.getElementById('currentTime');
            if (timeElement) {
                const now = new Date();
                const timeStr = now.getHours().toString().padStart(2, '0') + ':' + 
                             now.getMinutes().toString().padStart(2, '0') + ':' + 
                             now.getSeconds().toString().padStart(2, '0');
                timeElement.textContent = timeStr;
            }
        }
        
        // 初始设置
        updateNodeRefreshTime();
        updateRoomRefreshTime();
        updateChatRefreshTime();
        updateRelativeTimes();
        updateCurrentTime();
        
        // 每60秒刷新一次节点监控
        setInterval(refreshNodes, 60000);
        
        // 每3秒刷新一次房间列表
        setInterval(refreshRooms, 3000);
        
        // 每5秒刷新一次聊天消息
        setInterval(refreshChat, 5000);
        
        // 每1秒更新一次时间显示（更精确）
        setInterval(() => {
            updateNodeRefreshTime();
            updateRoomRefreshTime();
            updateChatRefreshTime();
            updateRelativeTimes();
            updateCurrentTime();
        }, 1000);
        
        // 表单提交确认
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const actionInput = this.querySelector('input[name="action"]');
                    if (!actionInput) return;
                    
                    const action = actionInput.value;
                    let message = '';
                    
                    if (action === 'change_status') {
                        const statusSelect = this.querySelector('select[name="status"]');
                        if (statusSelect) {
                            const status = statusSelect.value;
                            message = `确定要将系统状态更改为 "${status}" 吗？`;
                        }
                    } else if (action === 'publish_announcement') {
                        message = '确定要发布此公告吗？';
                    } else if (action === 'upload_update') {
                        const fileInput = this.querySelector('input[type="file"]');
                        if (fileInput && fileInput.files.length > 0) {
                            message = `确定要上传文件 "${fileInput.files[0].name}" 作为更新包吗？`;
                        } else {
                            message = '未选择文件，确定要继续吗？';
                        }
                    } else if (action === 'update_version') {
                        const versionInput = this.querySelector('input[name="version"]');
                        if (versionInput) {
                            const version = versionInput.value;
                            message = `确定要将版本号更新为 "${version}" 吗？`;
                        }
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
            
            // 自动滚动聊天到底部
            const chatContainer = document.getElementById('chatContainer');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            // 自动滚动节点网格到顶部（如果有新数据）
            const nodesGrid = document.getElementById('nodesGrid');
            if (nodesGrid) {
                nodesGrid.scrollTop = 0;
            }
        });
    </script>
</body>
</html>