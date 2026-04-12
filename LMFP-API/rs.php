<?php
// rs.php - 服务器端在线人数统计和心跳包处理脚本

// 设置响应头
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

// 数据库配置
define('DB_HOST', 'localhost');
define('DB_USER', '123');
define('DB_PASS', '123');
define('DB_NAME', '123');

// 数据文件路径
define('DATA_FILE', 'online_users.json');

// 最大在线用户数量（用于返回给客户端）
define('MAX_ONLINE_USERS', 5000); // 可根据实际情况调整

/**
 * 获取当前时间戳
 */
function getCurrentTimestamp() {
    return time();
}

/**
 * 读取在线用户数据
 */
function readOnlineUsers() {
    if (file_exists(DATA_FILE)) {
        $content = file_get_contents(DATA_FILE);
        $data = json_decode($content, true);
        return $data ?: array('users' => array(), 'timestamp' => 0);
    }
    return array('users' => array(), 'timestamp' => 0);
}

/**
 * 保存在线用户数据
 */
function saveOnlineUsers($data) {
    return file_put_contents(DATA_FILE, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
}

/**
 * 清理过期用户（超过3分钟未发送心跳的用户）
 */
function cleanExpiredUsers(&$users) {
    $now = getCurrentTimestamp();
    $timeout = 30; // 3分钟 = 180秒
    
    foreach ($users as $user_id => $user_data) {
        if (($now - $user_data['last_heartbeat']) > $timeout) {
            unset($users[$user_id]);
        }
    }
}

/**
 * 处理心跳包
 */
function handleHeartbeat($user_id) {
    if (empty($user_id)) {
        return array('success' => false, 'message' => '用户ID不能为空');
    }
    
    // 读取现有数据
    $data = readOnlineUsers();
    
    // 清理过期用户
    cleanExpiredUsers($data['users']);
    
    // 更新或添加用户
    $now = getCurrentTimestamp();
    $data['users'][$user_id] = array(
        'last_heartbeat' => $now,
        'join_time' => isset($data['users'][$user_id]['join_time']) ? $data['users'][$user_id]['join_time'] : $now
    );
    
    // 保存数据
    $result = saveOnlineUsers($data);
    
    if ($result !== false) {
        return array('success' => true, 'message' => '心跳包接收成功', 'online_count' => count($data['users']));
    } else {
        return array('success' => false, 'message' => '保存数据失败');
    }
}

/**
 * 获取在线用户数量
 */
function getOnlineCount() {
    // 读取现有数据
    $data = readOnlineUsers();
    
    // 清理过期用户
    cleanExpiredUsers($data['users']);
    
    // 保存清理后的数据
    saveOnlineUsers($data);
    
    return count($data['users']);
}

/**
 * 获取所有在线用户列表（可选功能）
 */
function getOnlineUsersList() {
    // 读取现有数据
    $data = readOnlineUsers();
    
    // 清理过期用户
    cleanExpiredUsers($data['users']);
    
    // 保存清理后的数据
    saveOnlineUsers($data);
    
    return array_values($data['users']);
}

// 主逻辑
try {
    $method = $_SERVER['REQUEST_METHOD'];
    
    if ($method === 'GET') {
        // GET请求：返回在线用户数量
        $online_count = getOnlineCount();
        echo $online_count; // 直接输出数字，兼容客户端解析
    } elseif ($method === 'POST') {
        // POST请求：处理心跳包或其他操作
        $input = file_get_contents('php://input');
        $post_data = array();
        
        // 解析POST数据
        if (!empty($input)) {
            parse_str($input, $post_data);
        } else {
            // 也尝试从$_POST获取数据
            $post_data = $_POST;
        }
        
        $action = isset($post_data['action']) ? $post_data['action'] : '';
        $user_id = isset($post_data['user_id']) ? $post_data['user_id'] : '';
        
        if ($action === 'heartbeat') {
            // 处理心跳包
            $result = handleHeartbeat($user_id);
            echo json_encode($result, JSON_UNESCAPED_UNICODE);
        } else {
            // 未知操作
            http_response_code(400);
            echo json_encode(array('success' => false, 'message' => '未知操作'), JSON_UNESCAPED_UNICODE);
        }
    } else {
        // 不支持的请求方法
        http_response_code(405);
        echo json_encode(array('success' => false, 'message' => '不支持的请求方法'), JSON_UNESCAPED_UNICODE);
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(array('success' => false, 'message' => '服务器内部错误: ' . $e->getMessage()), JSON_UNESCAPED_UNICODE);
}
?>