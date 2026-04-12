<?php
require_once 'config.php';

$data = get_request_data();
$token = trim($data['token'] ?? '');
$message = trim($data['message'] ?? '');

if (empty($token)) {
    json_response(false, '请先登录');
}

$user_id = verify_token($token);
if (!$user_id) {
    json_response(false, '登录已过期，请重新登录');
}

if (empty($message)) {
    json_response(false, '消息不能为空');
}

if (strlen($message) > 1500) {
    json_response(false, '消息过长（最多1500字节）');
}

// 敏感词过滤
$banned_words = ['赌博', '毒品', '色情', '诈骗', '政治敏感词']; // 示例敏感词
foreach ($banned_words as $word) {
    if (strpos($message, $word) !== false) {
        json_response(false, '消息包含敏感内容');
    }
}

$user = get_user_info($user_id);
if (!$user) {
    json_response(false, '用户不存在');
}

// 更新在线状态
update_online_status($user_id, $user['username']);

// 保存消息
$messages = load_data(MESSAGES_FILE);
$message_id = count($messages) + 1;

$new_message = [
    'id' => $message_id,
    'sender' => $user['username'],
    'sender_id' => $user_id,
    'content' => $message,
    'timestamp' => time(),
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
];

$messages[] = $new_message;

// 限制消息数量（最多保留1000条）
if (count($messages) > 1000) {
    $messages = array_slice($messages, -1000);
}

save_data(MESSAGES_FILE, $messages);

json_response(true, '消息发送成功');
?>