<?php
require_once 'config.php';

$data = get_request_data();
$token = trim($data['token'] ?? '');
$last_id = intval($data['last_id'] ?? 0);

if (!empty($token)) {
    $user_id = verify_token($token);
    if ($user_id) {
        $user = get_user_info($user_id);
        if ($user) {
            update_online_status($user_id, $user['username']);
        }
    }
}

$all_messages = load_data(MESSAGES_FILE);

// 如果未登录，只能看到最近50条消息
if (empty($token) || !$user_id) {
    $all_messages = array_slice($all_messages, -50);
    json_response(true, '获取成功', $all_messages);
}

// 获取新消息
$new_messages = [];
foreach ($all_messages as $msg) {
    if ($msg['id'] > $last_id) {
        $new_messages[] = $msg;
    }
}

// 限制返回数量（最多50条）
if (count($new_messages) > 50) {
    $new_messages = array_slice($new_messages, -50);
}

json_response(true, '获取成功', $new_messages);
?>