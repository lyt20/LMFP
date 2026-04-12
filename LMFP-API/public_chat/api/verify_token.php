<?php


//json_response(false, '因特殊原因，聊天室临时关闭，详情咨询QQ 2232908600');

require_once 'config.php';

$data = get_request_data();
$token = trim($data['token'] ?? '');

if (empty($token)) {
    json_response(false, 'token不能为空');
}

$user_id = verify_token($token);

if ($user_id) {
    $user = get_user_info($user_id);
    // 更新在线状态
    if ($user) {
        update_online_status($user_id, $user['username']);
    }
    json_response(true, 'token有效', [
        'user_id' => $user_id,
        'username' => $user['username']
    ]);
} else {
    json_response(false, 'token无效或已过期');
}
?>