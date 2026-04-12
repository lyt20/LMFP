<?php
require_once 'config.php';

$data = get_request_data();
$token = trim($data['token'] ?? '');

if (empty($token)) {
    json_response(false, '请先登录');
}

$user_id = verify_token($token);
if (!$user_id) {
    json_response(false, '登录已过期');
}

$user = get_user_info($user_id);
if (!$user) {
    json_response(false, '用户不存在');
}

// 更新在线状态
update_online_status($user_id, $user['username']);

json_response(true, '在线状态已更新');
?>