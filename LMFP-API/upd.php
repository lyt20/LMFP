<?php
// 配置
$token = 'xxxxxxxxx';
$counter_file = 'ggbb.txt';
$announcement_prefix = 'gg';

// API配置
$version_api_url = 'https://lytapi.asia/vapi.php'; // 版本号API地址

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
                    // 使用cURL调用远程API更新版本号
                    $ch = curl_init();
                    curl_setopt($ch, CURLOPT_URL, $version_api_url);
                    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "POST");
                    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode(['version' => $new_version]));
                    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
                    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
                    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
                    
                    $response = curl_exec($ch);
                    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
                    curl_close($ch);
                    
                    if ($response === false || $http_code !== 200) {
                        $message = '版本号更新失败！无法连接到API服务器。';
                        $message_type = 'error';
                    } else {
                        $result = json_decode($response, true);
                        if (isset($result['success']) && $result['success']) {
                            $message = "版本号已成功更新为: $new_version";
                            $message_type = 'success';
                        } else {
                            $message = '版本号更新失败！' . (isset($result['message']) ? $result['message'] : '未知错误');
                            $message_type = 'error';
                        }
                    }
                } else {
                    $message = '版本号不能为空！';
                    $message_type = 'error';
                }
                break;
        }
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
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 8px;
        }
        
        .room-item {
            padding: 16px;
            border-bottom: 1px solid var(--border-color);
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
        
        hr {
            margin: 24px 0;
            border: 0;
            border-top: 1px solid var(--border-color);
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>LMFP-系统管理面板</h1>
            <p>软件更新和公告发布管理</p>
        </div>
        
        <?php if ($message): ?>
            <div class="message <?php echo $message_type; ?>">
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>
        
        <div class="grid">
            <!-- 软件更新 -->
            <div class="card">
                <h2 class="card-title">软件更新</h2>
                
                <!-- 上传更新包 -->
                <form method="POST" action="" enctype="multipart/form-data" style="margin-bottom: 30px;">
                    <input type="hidden" name="action" value="upload_update">
                    
                    <div class="form-group">
                        <label class="form-label">验证Token</label>
                        <input type="password" name="token" class="form-input" required placeholder="请输入验证token">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">选择更新包文件 (lmfp.zip)</label>
                        <input type="file" name="update_file" class="form-input" accept=".zip" required>
                    </div>
                    
                    <button type="submit" class="btn">上传更新包</button>
                </form>
                
                <hr>
                
                <!-- 更新版本号 -->
                <form method="POST" action="">
                    <input type="hidden" name="action" value="update_version">
                    
                    <div class="form-group">
                        <label class="form-label">验证Token</label>
                        <input type="password" name="token" class="form-input" required placeholder="请输入验证token">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">新版本号</label>
                        <input type="text" name="version" class="form-input" required placeholder="例如: 2.5">
                    </div>
                    
                    <button type="submit" class="btn">更新版本号</button>
                </form>
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
                        <div style="padding: 20px; text-align: center; color: var(--text-secondary);">
                            暂无公告
                        </div>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 表单提交确认
        document.addEventListener('DOMContentLoaded', function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const actionInput = this.querySelector('input[name="action"]');
                    if (!actionInput) return;
                    
                    const action = actionInput.value;
                    let message = '';
                    
                    if (action === 'publish_announcement') {
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
        });
    </script>
</body>
</html>