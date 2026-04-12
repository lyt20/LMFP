<?php
// API配置
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// 数据库文件路径
define('DATA_DIR', __DIR__ . '/../data/');
define('USERS_FILE', DATA_DIR . 'users.txt');
define('SESSIONS_FILE', DATA_DIR . 'sessions.txt');
define('ONLINE_FILE', DATA_DIR . 'online_users.txt');
define('MESSAGES_FILE', DATA_DIR . 'messages.txt');

// 邮件配置
define('SMTP_HOST', 'smtp.163.com');        // SMTP服务器
define('SMTP_PORT', 465);                  // SMTP端口
define('SMTP_USER', 'liuyvetong_ai@163.com');   // 发件人邮箱
define('SMTP_PASS', 'xxxxxxxxxxxx');       // 邮箱授权码
define('SENDER_NAME', 'Lyt_IT_Studio');      // 发件人名称

// 创建必要目录
if (!file_exists(DATA_DIR)) mkdir(DATA_DIR, 0777, true);

// 初始化文件
function init_file($filename, $default_content = '[]') {
    if (!file_exists($filename)) {
        file_put_contents($filename, $default_content);
    }
}

init_file(USERS_FILE);
init_file(SESSIONS_FILE);
init_file(ONLINE_FILE);
init_file(MESSAGES_FILE);

// 返回JSON响应
function json_response($success, $message = '', $data = null) {
    $response = ['success' => $success];
    if ($message) $response['message'] = $message;
    if ($data !== null) $response['data'] = $data;
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    exit;
}

// 获取请求数据
function get_request_data() {
    $data = [];
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!empty($_POST)) {
            $data = $_POST;
        } else {
            // 处理JSON格式的POST数据
            $input = file_get_contents('php://input');
            if (!empty($input)) {
                $json_data = json_decode($input, true);
                if ($json_data !== null) {
                    $data = $json_data;
                }
            }
        }
    } else {
        $data = $_GET;
    }
    
    return $data;
}

// 验证QQ邮箱格式
function validate_qq_email($email) {
    $email = strtolower(trim($email));
    // 检查是否以@qq.com结尾
    if (!preg_match('/^[a-zA-Z0-9._%+-]+@qq\.com$/i', $email)) {
        return false;
    }
    return filter_var($email, FILTER_VALIDATE_EMAIL);
}

// 生成token
function generate_token($length = 32) {
    return bin2hex(random_bytes($length / 2));
}

// 保存数据到文件
function save_data($filename, $data) {
    file_put_contents($filename, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

// 加载数据从文件
function load_data($filename) {
    if (!file_exists($filename)) {
        return [];
    }
    $content = file_get_contents($filename);
    if (empty($content)) {
        return [];
    }
    return json_decode($content, true) ?: [];
}

// 验证token
function verify_token($token) {
    $sessions = load_data(SESSIONS_FILE);
    $current_time = time();
    
    foreach ($sessions as $session) {
        if ($session['token'] === $token && $session['expires'] > $current_time) {
            // 更新会话时间
            $session['last_activity'] = $current_time;
            return $session['user_id'];
        }
    }
    
    // 清理过期token
    $valid_sessions = array_filter($sessions, function($s) use ($current_time) {
        return $s['expires'] > $current_time;
    });
    save_data(SESSIONS_FILE, array_values($valid_sessions));
    
    return false;
}

// 获取用户信息
function get_user_info($user_id) {
    $users = load_data(USERS_FILE);
    
    foreach ($users as $user) {
        if ($user['id'] == $user_id) {
            return $user;
        }
    }
    
    return null;
}

// 更新用户在线状态
function update_online_status($user_id, $username) {
    $online_users = load_data(ONLINE_FILE);
    $current_time = time();
    
    // 清理10分钟无活动的用户
    $online_users = array_filter($online_users, function($user) use ($current_time) {
        return $user['last_activity'] > $current_time - 600; // 10分钟
    });
    
    // 更新或添加当前用户
    $found = false;
    foreach ($online_users as &$user) {
        if ($user['user_id'] == $user_id) {
            $user['last_activity'] = $current_time;
            $found = true;
            break;
        }
    }
    
    if (!$found) {
        $online_users[] = [
            'user_id' => $user_id,
            'username' => $username,
            'last_activity' => $current_time,
            'login_time' => $current_time
        ];
    }
    
    save_data(ONLINE_FILE, array_values($online_users));
    return $online_users;
}

// 清理过期会话
function cleanup_expired_sessions() {
    $sessions = load_data(SESSIONS_FILE);
    $current_time = time();
    
    $valid_sessions = array_filter($sessions, function($s) use ($current_time) {
        return $s['expires'] > $current_time;
    });
    
    if (count($sessions) != count($valid_sessions)) {
        save_data(SESSIONS_FILE, array_values($valid_sessions));
    }
}

// 每次请求时清理
cleanup_expired_sessions();
?>