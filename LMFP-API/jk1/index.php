<?php
// 手动引入PHPMailer
require 'phpmailer/src/Exception.php';
require 'phpmailer/src/PHPMailer.php';
require 'phpmailer/src/SMTP.php';

// 引入PHPMailer
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

//require 'vendor/autoload.php'; // 如果使用Composer
// 或者手动引入：
// require 'PHPMailer/src/Exception.php';
// require 'PHPMailer/src/PHPMailer.php';
// require 'PHPMailer/src/SMTP.php';

// 配置文件
$remoteUrl = 'https://lytapi.asia/st.txt';
$localFile = 'zt.txt';
$emailTo = '2232908600@qq.com';
$emailSubject = 'LMFP许可状态变更通知';
$checkInterval = 5; // 检查间隔（秒）

// 初始化本地状态文件（如果不存在）
if (!file_exists($localFile)) {
    file_put_contents($localFile, 'unknown');
}

// 获取远程状态
function getRemoteStatus($url) {
    try {
        $content = @file_get_contents($url, false, stream_context_create([
            'http' => [
                'timeout' => 10, // 10秒超时
                'ignore_errors' => true
            ],
            'ssl' => [
                'verify_peer' => false,
                'verify_peer_name' => false,
            ]
        ]));
        
        if ($content === false) {
            return 'offline'; // 无法获取内容
        }
        
        $content = trim($content);
        if ($content === 'true') {
            return 'true';
        } elseif ($content === 'false') {
            return 'false';
        } else {
            return 'offline'; // 内容无效
        }
    } catch (Exception $e) {
        return 'offline';
    }
}

// 获取本地状态
function getLocalStatus($file) {
    if (!file_exists($file)) {
        return 'unknown';
    }
    return trim(file_get_contents($file));
}

// 发送邮件
function sendEmail($status, $to) {
    $mail = new PHPMailer(true);
    
    try {
        // SMTP配置（使用QQ邮箱示例）
        $mail->isSMTP();
        $mail->Host = 'smtp.163.com'; // QQ邮箱SMTP服务器
        $mail->SMTPAuth = true;
        $mail->Username = 'liuyvetong_ai@163.com'; // 发件人邮箱
        $mail->Password = 'xxxxxxxxxxxxx'; // 邮箱授权码（不是密码）
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_SMTPS;
        $mail->Port = 465;
        
        // 发件人和收件人
        $mail->setFrom('liuyvetong_ai@163.com', 'LMFP监控系统');
        $mail->addAddress($to);
        
        // 邮件内容
        if ($status === 'false') {
            $mail->Subject = 'LMFP许可关闭通知';
            $mail->Body = 'LMFP许可已关闭，请注意检查。';
        } elseif ($status === 'true') {
            $mail->Subject = 'LMFP许可开启通知';
            $mail->Body = 'LMFP许可已开启，系统恢复正常。';
        } elseif ($status === 'offline') {
            $mail->Subject = 'LMFP服务器离线通知';
            $mail->Body = 'LMFP服务器已离线，请立即检查。';
        }
        
        $mail->send();
        return true;
    } catch (Exception $e) {
        error_log("邮件发送失败: " . $mail->ErrorInfo);
        return false;
    }
}

// 主逻辑
$remoteStatus = getRemoteStatus($remoteUrl);
$localStatus = getLocalStatus($localFile);

// 检查状态是否变化
if ($remoteStatus !== $localStatus) {
    // 状态发生变化，更新本地文件并发送邮件
    file_put_contents($localFile, $remoteStatus);
    sendEmail($remoteStatus, $emailTo);
    
    $statusMessage = "状态已变化：$localStatus → $remoteStatus";
    $emailMessage = "已发送邮件通知";
} else {
    $statusMessage = "状态未变化，无需操作";
    $emailMessage = "状态相同，已忽略";
}

// 准备显示的状态文本
$displayText = '';
switch ($remoteStatus) {
    case 'true':
        $displayText = 'true (开启)';
        $statusColor = 'green';
        break;
    case 'false':
        $displayText = 'false (关闭)';
        $statusColor = 'red';
        break;
    case 'offline':
        $displayText = 'offline (离线)';
        $statusColor = 'orange';
        break;
    default:
        $displayText = 'unknown (未知)';
        $statusColor = 'gray';
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LMFP许可状态监控</title>
    <meta http-equiv="refresh" content="<?php echo $checkInterval; ?>">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .status-box {
            text-align: center;
            padding: 30px;
            margin: 20px 0;
            border-radius: 8px;
            border: 2px solid #ddd;
        }
        .status-true {
            background-color: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        .status-false {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        .status-offline {
            background-color: #fff3cd;
            border-color: #ffeeba;
            color: #856404;
        }
        .info-box {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-size: 14px;
        }
        .last-check {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            background-color: <?php echo $statusColor; ?>;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LMFP许可状态监控系统</h1>
        
        <div class="info-box">
            <strong>监控信息：</strong><br>
            远程URL: <?php echo htmlspecialchars($remoteUrl); ?><br>
            检查间隔: <?php echo $checkInterval; ?>秒<br>
            上次检查: <?php echo date('Y-m-d H:i:s'); ?><br>
            本地状态: <?php echo htmlspecialchars($localStatus); ?>
        </div>
        
        <div class="status-box <?php echo 'status-' . $remoteStatus; ?>">
            <h2>当前状态</h2>
            <div class="status-badge"><?php echo $displayText; ?></div>
            <p style="margin-top: 20px; font-size: 18px;">
                <?php echo $statusMessage; ?>
            </p>
        </div>
        
        <div class="info-box">
            <strong>操作日志：</strong><br>
            <?php echo $emailMessage; ?><br>
            远程状态: <?php echo htmlspecialchars($remoteStatus); ?><br>
            本地状态: <?php echo htmlspecialchars($localStatus); ?>
        </div>
        
        <div class="last-check">
            页面每<?php echo $checkInterval; ?>秒自动刷新一次<br>
            下次刷新: <?php echo date('H:i:s', time() + $checkInterval); ?>
        </div>
    </div>
    
    <script>
        // 额外的JavaScript刷新（作为备用）
        setTimeout(function() {
            window.location.reload();
        }, <?php echo $checkInterval * 1000; ?>);
        
        // 显示刷新倒计时
        let countdown = <?php echo $checkInterval; ?>;
        const countdownElement = document.createElement('div');
        countdownElement.className = 'last-check';
        countdownElement.innerHTML = `页面将在 <span id="countdown">${countdown}</span> 秒后刷新`;
        document.querySelector('.last-check').appendChild(countdownElement);
        
        setInterval(function() {
            countdown--;
            document.getElementById('countdown').textContent = countdown;
            if (countdown <= 0) {
                countdown = <?php echo $checkInterval; ?>;
            }
        }, 1000);
    </script>
</body>
</html>