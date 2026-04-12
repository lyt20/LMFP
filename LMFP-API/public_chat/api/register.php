<?php
// register.php - 注册API
require_once 'config.php';

$data = get_request_data();
$email = trim($data['email'] ?? '');
$username = trim($data['username'] ?? '');
$password = trim($data['password'] ?? '');

// 验证输入
if (empty($email) || empty($username) || empty($password)) {
    json_response(false, '请填写所有字段');
}

// 强制验证纯数字QQ邮箱
$email = strtolower($email);
if (!validate_qq_email($email)) {
    json_response(false, '请使用QQ邮箱注册 (@qq.com)');
}

// 新增：验证是否为纯数字QQ邮箱
if (!preg_match('/^[0-9]+@qq\.com$/', $email)) {
    json_response(false, 'QQ邮箱格式错误，请使用纯数字QQ号+@qq.com格式');
}

if (strlen($password) < 6) {
    json_response(false, '密码长度至少6位');
}

if (strlen($username) < 2 || strlen($username) > 20) {
    json_response(false, '用户名长度2-20个字符');
}

// 检查用户名是否包含特殊字符
if (!preg_match('/^[a-zA-Z0-9_\x{4e00}-\x{9fa5}]+$/u', $username)) {
    json_response(false, '用户名只能包含中文、英文、数字和下划线');
}

// 检查邮箱是否已注册
$users = load_data(USERS_FILE);
foreach ($users as $user) {
    if ($user['email'] === $email) {
        json_response(false, '该QQ邮箱已被注册');
    }
    if ($user['username'] === $username) {
        json_response(false, '该用户名已被使用');
    }
}

// 生成验证码
$verify_code = mt_rand(100000, 999999);
$user_id = count($users) + 1;

// 创建用户数据（等待验证）
$new_user = [
    'id' => $user_id,
    'email' => $email,
    'username' => $username,
    'password' => password_hash($password, PASSWORD_DEFAULT),
    'verify_code' => $verify_code,
    'verified' => false,
    'created_at' => time(),
    'verify_expires' => time() + 3600 // 1小时有效
];

// 临时保存验证信息
$pending_file = DATA_DIR . 'pending_' . md5($email) . '.txt';
file_put_contents($pending_file, json_encode($new_user, JSON_UNESCAPED_UNICODE));

// 发送验证邮件 - 修改路径为当前目录下的phpmailer
try {
    require_once __DIR__ . '/phpmailer/src/PHPMailer.php';
    require_once __DIR__ . '/phpmailer/src/SMTP.php';
    require_once __DIR__ . '/phpmailer/src/Exception.php';
    
    $mail = new PHPMailer\PHPMailer\PHPMailer(true);
    
    $mail->isSMTP();
    $mail->Host = SMTP_HOST;
    $mail->SMTPAuth = true;
    $mail->Username = SMTP_USER;
    $mail->Password = SMTP_PASS;
    $mail->SMTPSecure = PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_SMTPS;
    $mail->Port = SMTP_PORT;
    
    $mail->setFrom(SMTP_USER, SENDER_NAME);
    $mail->addAddress($email, $username);
    
    $mail->isHTML(true);
    $mail->CharSet = 'UTF-8';
    $mail->Subject = '公共聊天室 - QQ邮箱验证';
    
    $mail->Body = "
    <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'>
        <h2 style='color: #333;'>欢迎注册公共聊天室！</h2>
        <p style='color: #666;'>尊敬的 {$username}，</p>
        <p style='color: #666;'>您的QQ邮箱验证码是：</p>
        <div style='background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; text-align: center;'>
            <h1 style='color: #d32f2f; margin: 0; letter-spacing: 5px;'>{$verify_code}</h1>
        </div>
        <p style='color: #666;'>请在1小时内完成验证。</p>
        <p style='color: #999; font-size: 12px;'>如果这不是您的操作，请忽略此邮件。</p>
        <hr style='border: none; border-top: 1px solid #eee; margin: 20px 0;'>
        <p style='color: #999; font-size: 12px;'>公共聊天室团队</p>
    </div>
    ";
    
    $mail->AltBody = "欢迎注册公共聊天室！\n验证码：{$verify_code}\n请在1小时内完成验证。\n\n如果这不是您的操作，请忽略此邮件。";
    
    if ($mail->send()) {
        json_response(true, '验证邮件已发送到您的QQ邮箱，请查收');
    } else {
        throw new Exception($mail->ErrorInfo);
    }
    
} catch (Exception $e) {
    // 删除临时文件
    if (file_exists($pending_file)) {
        unlink($pending_file);
    }
    json_response(false, '邮件发送失败，请稍后重试。错误信息：' . $e->getMessage());
}