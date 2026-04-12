<?php
// verify_email.php - 验证邮箱API
require_once 'config.php';

$data = get_request_data();
$email = trim($data['email'] ?? '');
$code = trim($data['code'] ?? '');

if (empty($email) || empty($code)) {
    json_response(false, '参数不完整');
}

// 验证QQ邮箱格式
$email = strtolower($email);
if (!validate_qq_email($email)) {
    json_response(false, '请使用QQ邮箱验证 (@qq.com)');
}

$pending_file = DATA_DIR . 'pending_' . md5($email) . '.txt';

if (!file_exists($pending_file)) {
    json_response(false, '验证请求已过期或不存在');
}

$user_data = json_decode(file_get_contents($pending_file), true);

if ($user_data['verify_code'] != $code) {
    json_response(false, '验证码错误');
}

if ($user_data['verify_expires'] < time()) {
    unlink($pending_file);
    json_response(false, '验证码已过期');
}

// 移除验证码信息
unset($user_data['verify_code']);
unset($user_data['verify_expires']);
$user_data['verified'] = true;

// 保存到正式用户文件
$users = load_data(USERS_FILE);
$users[] = $user_data;
save_data(USERS_FILE, $users);

// 删除临时文件
unlink($pending_file);

// 发送欢迎邮件 - 修改路径
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
    $mail->addAddress($email, $user_data['username']);
    
    $mail->isHTML(true);
    $mail->CharSet = 'UTF-8';
    $mail->Subject = '公共聊天室 - 注册成功';
    
    $mail->Body = "
    <div style='font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;'>
        <h2 style='color: #4CAF50;'>🎉 恭喜您注册成功！</h2>
        <p style='color: #666;'>尊敬的 {$user_data['username']}，</p>
        <p style='color: #666;'>您的QQ邮箱验证已完成，现在可以登录公共聊天室了。</p>
        <div style='background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4CAF50;'>
            <p style='margin: 0; color: #333;'><strong>账号信息：</strong></p>
            <p style='margin: 10px 0 0 0; color: #666;'>用户名：{$user_data['username']}</p>
            <p style='margin: 5px 0 0 0; color: #666;'>注册时间：" . date('Y-m-d H:i:s') . "</p>
        </div>
        <p style='color: #666;'>立即登录公共聊天室，与大家实时交流吧！</p>
        <hr style='border: none; border-top: 1px solid #eee; margin: 20px 0;'>
        <p style='color: #999; font-size: 12px;'>公共聊天室 - 让沟通更简单</p>
    </div>
    ";
    
    $mail->AltBody = "恭喜您注册成功！\n\n用户名：{$user_data['username']}\n注册时间：" . date('Y-m-d H:i:s') . "\n\n立即登录公共聊天室，与大家实时交流吧！";
    
    $mail->send();
    
} catch (Exception $e) {
    // 邮件发送失败不影响注册成功
}

json_response(true, 'QQ邮箱验证成功，现在可以登录了');
?>