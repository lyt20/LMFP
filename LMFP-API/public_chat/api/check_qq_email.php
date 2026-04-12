<?php
require_once 'config.php';

$data = get_request_data();
$email = trim($data['email'] ?? '');

if (empty($email)) {
    json_response(false, '邮箱不能为空');
}

$email = strtolower($email);

// 检查QQ邮箱格式
if (!validate_qq_email($email)) {
    json_response(false, '请使用QQ邮箱 (@qq.com)');
}

// 检查是否已注册
$users = load_data(USERS_FILE);
foreach ($users as $user) {
    if ($user['email'] === $email) {
        json_response(false, '该QQ邮箱已被注册');
    }
}

json_response(true, 'QQ邮箱可用');
?>