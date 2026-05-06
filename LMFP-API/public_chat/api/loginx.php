<?php
require_once 'config.php';

json_response(false, '因特殊原因，聊天室临时关闭，详情咨询QQ 2232908600');

$data = get_request_data();
$email = trim($data['email'] ?? '');
$password = trim($data['password'] ?? '');

if (empty($email) || empty($password)) {
    json_response(false, '请填写QQ邮箱和密码');
}

// 验证QQ邮箱格式
$email = strtolower($email);
if (!validate_qq_email($email)) {
    json_response(false, '请使用QQ邮箱登录 (@qq.com)');
}

$users = load_data(USERS_FILE);
$found_user = null;

foreach ($users as $user) {
    if ($user['email'] === $email) {
        $found_user = $user;
        break;
    }
}

if (!$found_user) {
    json_response(false, 'QQ邮箱或密码错误');
}

if (!$found_user['verified']) {
    json_response(false, '请先验证QQ邮箱');
}

if (!password_verify($password, $found_user['password'])) {
    json_response(false, 'QQ邮箱或密码错误');
}

// 生成token
$token = generate_token();
$expires = time() + 86400 * 7; // 7天有效期

// 保存会话
$sessions = load_data(SESSIONS_FILE);
$sessions[] = [
    'token' => $token,
    'user_id' => $found_user['id'],
    'created_at' => time(),
    'expires' => $expires,
    'last_activity' => time()
];
save_data(SESSIONS_FILE, $sessions);

// 更新在线状态
update_online_status($found_user['id'], $found_user['username']);

json_response(true, '登录成功', [
    'token' => $token,
    'username' => $found_user['username'],
    'expires' => $expires
]);
?>