<?php
require_once 'config.php';

$data = get_request_data();
$token = trim($data['token'] ?? '');

if (!empty($token)) {
    $user_id = verify_token($token);
    if ($user_id) {
        $user = get_user_info($user_id);
        if ($user) {
            update_online_status($user_id, $user['username']);
        }
    }
}

$online_users = load_data(ONLINE_FILE);
$current_time = time();

// 清理10分钟无活动的用户
$active_users = array_filter($online_users, function($user) use ($current_time) {
    return $user['last_activity'] > $current_time - 5; // 10分钟
});

if (count($online_users) != count($active_users)) {
    save_data(ONLINE_FILE, array_values($active_users));
    $online_users = $active_users;
}

// 格式化用户信息
$formatted_users = [];
foreach ($online_users as $user) {
    $formatted_users[] = [
        'user_id' => $user['user_id'],
        'username' => $user['username'],
        'online_time' => $user['login_time'],
        'last_activity' => $user['last_activity']
    ];
}

json_response(true, '获取成功', $formatted_users);
?>