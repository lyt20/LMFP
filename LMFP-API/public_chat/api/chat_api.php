<?php
/*
 * 公共聊天室 - 单文件API服务器
 * 版本: 1.0
 * 作者: AI Assistant
 * 使用方法: php -S localhost:8000 chat_api.php
 */

// ============================================
// 配置区 - 根据实际情况修改
// ============================================
define('API_KEY', 'public_chat_2024');  // API密钥，可修改
define('MAX_MESSAGES', 1000);           // 最大保存消息数
define('MAX_USERS', 10000);             // 最大用户数
define('SESSION_EXPIRE', 604800);       // 会话过期时间（7天）
define('ONLINE_TIMEOUT', 600);          // 在线超时时间（10分钟）

//邮箱配置（必需修改！）
define('SMTP_HOST', 'smtp.163.com');
define('SMTP_PORT', 465);
define('SMTP_USER', 'liuyvetong_ai@163.com');     // 改为您的邮箱
define('SMTP_PASS', 'xxxxxxxxxxx');        //邮箱授权码（不是密码）
define('SENDER_NAME', '公共聊天室系统');

// ============================================
// 初始化 - 不要修改以下代码
// ============================================

// 错误处理设置
error_reporting(0);  // 生产环境关闭错误显示
ini_set('display_errors', 0);

// 设置响应头
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// 处理预检请求
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

// 创建数据存储目录
$data_dir = __DIR__ . '/chat_data';
if (!file_exists($data_dir)) {
    mkdir($data_dir, 0777, true);
}

// 数据文件路径
define('DATA_DIR', $data_dir);
define('USERS_FILE', DATA_DIR . '/users.json');
define('SESSIONS_FILE', DATA_DIR . '/sessions.json');
define('ONLINE_FILE', DATA_DIR . '/online.json');
define('MESSAGES_FILE', DATA_DIR . '/messages.json');
define('PENDING_FILE', DATA_DIR . '/pending_%s.json');

// 初始化数据文件
init_data_files();

// ============================================
// 主路由处理
// ============================================

// 获取请求路径
$request_uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$api_path = trim($request_uri, '/');

// 如果是直接访问文件，显示信息
if (empty($api_path) || $api_path === basename(__FILE__)) {
    show_api_info();
    exit;
}

// 提取API动作
$parts = explode('/', $api_path);
$action = end($parts);

// 路由分发
switch ($action) {
    case 'register':
        handle_register();
        break;
    case 'login':
        handle_login();
        break;
    case 'verify_email':
        handle_verify_email();
        break;
    case 'verify_token':
        handle_verify_token();
        break;
    case 'get_online_users':
        handle_get_online_users();
        break;
    case 'send_message':
        handle_send_message();
        break;
    case 'get_messages':
        handle_get_messages();
        break;
    case 'update_online':
        handle_update_online();
        break;
    case 'logout':
        handle_logout();
        break;
    case 'get_user_info':
        handle_get_user_info();
        break;
    case 'check_email':
        handle_check_email();
        break;
    case 'test':
        handle_test();
        break;
    default:
        json_response(false, 'API不存在');
}

// ============================================
// 工具函数
// ============================================

/**
 * 初始化数据文件
 */
function init_data_files() {
    $files = [
        USERS_FILE => '[]',
        SESSIONS_FILE => '[]',
        ONLINE_FILE => '[]',
        MESSAGES_FILE => '[]'
    ];
    
    foreach ($files as $file => $default) {
        if (!file_exists($file)) {
            file_put_contents($file, $default);
        }
    }
}

/**
 * 返回JSON响应
 */
function json_response($success, $message = '', $data = null) {
    $response = [
        'success' => (bool)$success,
        'message' => $message,
        'timestamp' => time()
    ];
    
    if ($data !== null) {
        $response['data'] = $data;
    }
    
    // 确保没有其他输出
    if (ob_get_level() > 0) {
        ob_end_clean();
    }
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * 获取请求数据
 */
function get_request_data() {
    $data = [];
    
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        if (!empty($_POST)) {
            $data = $_POST;
        } else {
            $input = file_get_contents('php://input');
            if (!empty($input)) {
                $json_data = json_decode($input, true);
                if ($json_data !== null) {
                    $data = $json_data;
                } else {
                    parse_str($input, $data);
                }
            }
        }
    } else {
        $data = $_GET;
    }
    
    return $data;
}

/**
 * 验证QQ邮箱格式
 */
function validate_qq_email($email) {
    $email = strtolower(trim($email));
    return filter_var($email, FILTER_VALIDATE_EMAIL) && 
           preg_match('/@qq\.com$/', $email);
}

/**
 * 生成随机token
 */
function generate_token($length = 32) {
    return bin2hex(random_bytes($length / 2));
}

/**
 * 生成验证码
 */
function generate_verify_code($length = 6) {
    return str_pad(mt_rand(0, pow(10, $length) - 1), $length, '0', STR_PAD_LEFT);
}

/**
 * 保存数据到文件
 */
function save_data($filename, $data) {
    return file_put_contents($filename, json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
}

/**
 * 加载数据从文件
 */
function load_data($filename) {
    if (!file_exists($filename)) {
        return [];
    }
    
    $content = file_get_contents($filename);
    if (empty($content)) {
        return [];
    }
    
    $data = json_decode($content, true);
    return $data ?: [];
}

/**
 * 验证token
 */
function verify_token($token) {
    $sessions = load_data(SESSIONS_FILE);
    $current_time = time();
    
    foreach ($sessions as $session) {
        if ($session['token'] === $token && $session['expires'] > $current_time) {
            // 更新最后活动时间
            $session['last_activity'] = $current_time;
            return $session['user_id'];
        }
    }
    
    return false;
}

/**
 * 获取用户信息
 */
function get_user_info($user_id) {
    $users = load_data(USERS_FILE);
    
    foreach ($users as $user) {
        if ($user['id'] == $user_id) {
            return $user;
        }
    }
    
    return null;
}

/**
 * 更新在线状态
 */
function update_online_status($user_id, $username) {
    $online_users = load_data(ONLINE_FILE);
    $current_time = time();
    
    // 清理超时用户
    $online_users = array_filter($online_users, function($user) use ($current_time) {
        return $user['last_activity'] > $current_time - ONLINE_TIMEOUT;
    });
    
    // 更新或添加用户
    $found = false;
    foreach ($online_users as &$user) {
        if ($user['user_id'] == $user_id) {
            $user['last_activity'] = $current_time;
            $user['username'] = $username;
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

/**
 * 清理过期数据
 */
function cleanup_expired_data() {
    $current_time = time();
    
    // 清理过期会话
    $sessions = load_data(SESSIONS_FILE);
    $valid_sessions = array_filter($sessions, function($s) use ($current_time) {
        return $s['expires'] > $current_time;
    });
    save_data(SESSIONS_FILE, array_values($valid_sessions));
    
    // 清理过期待验证用户
    $files = glob(sprintf(PENDING_FILE, '*'));
    foreach ($files as $file) {
        if (file_exists($file)) {
            $user_data = json_decode(file_get_contents($file), true);
            if ($user_data && $user_data['verify_expires'] < $current_time) {
                unlink($file);
            }
        }
    }
}

// 每次请求都清理过期数据
cleanup_expired_data();

/**
 * 发送邮件（使用内置mail函数，兼容性最好）
 */
function send_email($to, $subject, $body_html, $body_text = '') {
    // 方法1：使用内置mail函数（最简单）
    $headers = [
        'From: ' . SENDER_NAME . ' <' . SMTP_USER . '>',
        'Reply-To: ' . SMTP_USER,
        'MIME-Version: 1.0',
        'Content-Type: text/html; charset=UTF-8',
        'X-Mailer: PHP/' . phpversion()
    ];
    
    return mail($to, $subject, $body_html, implode("\r\n", $headers));
    
    /*
    // 方法2：使用PHPMailer（需要额外文件）
    // 如果需要使用PHPMailer，请取消注释以下代码
    // 并确保phpmailer目录存在
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
        $mail->addAddress($to);
        
        $mail->isHTML(true);
        $mail->CharSet = 'UTF-8';
        $mail->Subject = $subject;
        $mail->Body = $body_html;
        $mail->AltBody = $body_text;
        
        return $mail->send();
    } catch (Exception $e) {
        return false;
    }
    */
}

// ============================================
// API处理函数
// ============================================

/**
 * 显示API信息
 */
function show_api_info() {
    echo '<!DOCTYPE html>
    <html>
    <head>
        <title>公共聊天室API服务器</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
            .api-list { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .api-item { margin: 10px 0; padding: 10px; border-left: 4px solid #4CAF50; background: white; }
            .method { display: inline-block; padding: 4px 8px; background: #4CAF50; color: white; border-radius: 3px; font-size: 12px; }
            .url { color: #2196F3; font-family: monospace; }
            .status { float: right; color: #4CAF50; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 公共聊天室API服务器</h1>
            <p>服务器正在运行！所有API端点：</p>
            
            <div class="api-list">
                <div class="api-item">
                    <span class="method">POST</span>
                    <span class="url">/register</span>
                    <span class="status">✓ 注册账号</span>
                </div>
                <div class="api-item">
                    <span class="method">POST</span>
                    <span class="url">/verify_email</span>
                    <span class="status">✓ 验证邮箱</span>
                </div>
                <div class="api-item">
                    <span class="method">POST</span>
                    <span class="url">/login</span>
                    <span class="status">✓ 用户登录</span>
                </div>
                <div class="api-item">
                    <span class="method">GET</span>
                    <span class="url">/get_online_users</span>
                    <span class="status">✓ 获取在线用户</span>
                </div>
                <div class="api-item">
                    <span class="method">POST</span>
                    <span class="url">/send_message</span>
                    <span class="status">✓ 发送消息</span>
                </div>
                <div class="api-item">
                    <span class="method">GET</span>
                    <span class="url">/get_messages</span>
                    <span class="status">✓ 获取消息</span>
                </div>
                <div class="api-item">
                    <span class="method">GET</span>
                    <span class="url">/test</span>
                    <span class="status">✓ 测试连接</span>
                </div>
            </div>
            
            <p><strong>数据目录：</strong> ' . DATA_DIR . '</p>
            <p><strong>API数量：</strong> 10个可用端点</p>
            <p><strong>状态：</strong> <span style="color: #4CAF50;">● 正常运行</span></p>
        </div>
    </body>
    </html>';
}

/**
 * 处理注册请求
 */
function handle_register() {
    $data = get_request_data();
    $email = trim($data['email'] ?? '');
    $username = trim($data['username'] ?? '');
    $password = trim($data['password'] ?? '');
    
    // 验证输入
    if (empty($email) || empty($username) || empty($password)) {
        json_response(false, '请填写所有字段');
    }
    
    // 验证QQ邮箱
    if (!validate_qq_email($email)) {
        json_response(false, '请使用QQ邮箱注册 (@qq.com)');
    }
    
    if (strlen($password) < 6) {
        json_response(false, '密码长度至少6位');
    }
    
    if (strlen($username) < 2 || strlen($username) > 20) {
        json_response(false, '用户名长度2-20个字符');
    }
    
    // 检查重复
    $users = load_data(USERS_FILE);
    foreach ($users as $user) {
        if ($user['email'] === $email) {
            json_response(false, '该QQ邮箱已被注册');
        }
        if ($user['username'] === $username) {
            json_response(false, '该用户名已被使用');
        }
    }
    
    // 生成验证码
    $verify_code = generate_verify_code();
    $user_id = count($users) + 1;
    
    // 创建待验证用户
    $pending_user = [
        'id' => $user_id,
        'email' => $email,
        'username' => $username,
        'password' => password_hash($password, PASSWORD_DEFAULT),
        'verify_code' => $verify_code,
        'verified' => false,
        'created_at' => time(),
        'verify_expires' => time() + 3600 // 1小时有效
    ];
    
    // 保存待验证用户
    $pending_file = sprintf(PENDING_FILE, md5($email));
    save_data($pending_file, $pending_user);
    
    // 发送验证邮件
    $subject = '公共聊天室 - 邮箱验证码';
    $body = '
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">欢迎注册公共聊天室！</h2>
        <p style="color: #666;">尊敬的 ' . htmlspecialchars($username) . '，</p>
        <p style="color: #666;">您的验证码是：</p>
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px dashed #4CAF50;">
            <h1 style="color: #d32f2f; margin: 0; font-size: 36px; letter-spacing: 8px;">' . $verify_code . '</h1>
        </div>
        <p style="color: #666;">请在1小时内完成验证。</p>
        <p style="color: #999; font-size: 14px;">如果这不是您的操作，请忽略此邮件。</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">公共聊天室团队</p>
    </div>
    ';
    
    if (send_email($email, $subject, $body)) {
        json_response(true, '验证邮件已发送到您的QQ邮箱，请查收验证码');
    } else {
        // 邮件发送失败，删除临时文件
        if (file_exists($pending_file)) {
            unlink($pending_file);
        }
        json_response(false, '邮件发送失败，请检查邮箱配置或稍后重试');
    }
}

/**
 * 处理邮箱验证
 */
function handle_verify_email() {
    $data = get_request_data();
    $email = trim($data['email'] ?? '');
    $code = trim($data['code'] ?? '');
    
    if (empty($email) || empty($code)) {
        json_response(false, '参数不完整');
    }
    
    // 验证QQ邮箱
    if (!validate_qq_email($email)) {
        json_response(false, '请使用QQ邮箱验证 (@qq.com)');
    }
    
    $pending_file = sprintf(PENDING_FILE, md5($email));
    
    if (!file_exists($pending_file)) {
        json_response(false, '验证请求已过期或不存在');
    }
    
    $user_data = load_data($pending_file);
    
    if ($user_data['verify_code'] != $code) {
        json_response(false, '验证码错误');
    }
    
    if ($user_data['verify_expires'] < time()) {
        unlink($pending_file);
        json_response(false, '验证码已过期');
    }
    
    // 验证成功，保存正式用户
    unset($user_data['verify_code']);
    unset($user_data['verify_expires']);
    $user_data['verified'] = true;
    
    $users = load_data(USERS_FILE);
    $users[] = $user_data;
    save_data(USERS_FILE, $users);
    
    // 删除临时文件
    unlink($pending_file);
    
    // 发送欢迎邮件
    $subject = '公共聊天室 - 注册成功';
    $body = '
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #4CAF50;">🎉 恭喜您注册成功！</h2>
        <p style="color: #666;">尊敬的 ' . htmlspecialchars($user_data['username']) . '，</p>
        <p style="color: #666;">您的QQ邮箱验证已完成，现在可以登录公共聊天室了。</p>
        <div style="background: #f0f8ff; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #4CAF50;">
            <p style="margin: 0 0 10px 0; color: #333; font-weight: bold;">账号信息：</p>
            <p style="margin: 5px 0; color: #666;">用户名：' . htmlspecialchars($user_data['username']) . '</p>
            <p style="margin: 5px 0; color: #666;">注册时间：' . date('Y-m-d H:i:s') . '</p>
            <p style="margin: 5px 0; color: #666;">用户ID：' . $user_data['id'] . '</p>
        </div>
        <p style="color: #666;">立即登录公共聊天室，与大家实时交流吧！</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #999; font-size: 12px;">公共聊天室 - 让沟通更简单</p>
    </div>
    ';
    
    send_email($email, $subject, $body);
    
    json_response(true, 'QQ邮箱验证成功，现在可以登录了');
}

/**
 * 处理登录请求
 */
function handle_login() {
    $data = get_request_data();
    $email = trim($data['email'] ?? '');
    $password = trim($data['password'] ?? '');
    
    if (empty($email) || empty($password)) {
        json_response(false, '请填写QQ邮箱和密码');
    }
    
    // 验证QQ邮箱
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
    $expires = time() + SESSION_EXPIRE;
    
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
        'user_id' => $found_user['id'],
        'expires' => $expires
    ]);
}

/**
 * 处理token验证
 */
function handle_verify_token() {
    $data = get_request_data();
    $token = trim($data['token'] ?? '');
    
    if (empty($token)) {
        json_response(false, 'token不能为空');
    }
    
    $user_id = verify_token($token);
    
    if ($user_id) {
        $user = get_user_info($user_id);
        if ($user) {
            update_online_status($user_id, $user['username']);
        }
        json_response(true, 'token有效', [
            'user_id' => $user_id,
            'username' => $user['username'] ?? ''
        ]);
    } else {
        json_response(false, 'token无效或已过期');
    }
}

/**
 * 处理获取在线用户
 */
function handle_get_online_users() {
    $data = get_request_data();
    $token = trim($data['token'] ?? '');
    
    // 如果提供了token，更新在线状态
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
    
    // 清理超时用户
    $active_users = array_filter($online_users, function($user) use ($current_time) {
        return $user['last_activity'] > $current_time - ONLINE_TIMEOUT;
    });
    
    if (count($online_users) != count($active_users)) {
        save_data(ONLINE_FILE, array_values($active_users));
        $online_users = $active_users;
    }
    
    // 格式化响应
    $formatted_users = [];
    foreach ($online_users as $user) {
        $formatted_users[] = [
            'user_id' => $user['user_id'],
            'username' => $user['username'],
            'online_time' => $user['login_time'],
            'last_activity' => $user['last_activity'],
            'status' => ($user['last_activity'] > $current_time - 60) ? '在线' : '离开'
        ];
    }
    
    json_response(true, '获取成功', $formatted_users);
}

/**
 * 处理发送消息
 */
function handle_send_message() {
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
    
    if (strlen($message) > 500) {
        json_response(false, '消息过长（最多500字）');
    }
    
    // 敏感词过滤
    $banned_words = ['赌博', '毒品', '色情', '诈骗', '政治敏感词'];
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
    
    // 限制消息数量
    if (count($messages) > MAX_MESSAGES) {
        $messages = array_slice($messages, -MAX_MESSAGES);
    }
    
    save_data(MESSAGES_FILE, $messages);
    
    json_response(true, '消息发送成功');
}

/**
 * 处理获取消息
 */
function handle_get_messages() {
    $data = get_request_data();
    $token = trim($data['token'] ?? '');
    $last_id = intval($data['last_id'] ?? 0);
    
    // 更新在线状态（如果已登录）
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
    
    // 如果未登录或token无效，只返回最近50条
    if (empty($token) || !verify_token($token)) {
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
    
    // 限制返回数量
    if (count($new_messages) > 50) {
        $new_messages = array_slice($new_messages, -50);
    }
    
    json_response(true, '获取成功', $new_messages);
}

/**
 * 处理更新在线状态
 */
function handle_update_online() {
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
}

/**
 * 处理退出登录
 */
function handle_logout() {
    $data = get_request_data();
    $token = trim($data['token'] ?? '');
    
    if (empty($token)) {
        json_response(true, '已退出');
    }
    
    // 从在线用户中移除
    $online_users = load_data(ONLINE_FILE);
    $online_users = array_filter($online_users, function($user) use ($token) {
        $user_id = verify_token($token);
        return $user['user_id'] != $user_id;
    });
    
    save_data(ONLINE_FILE, array_values($online_users));
    
    json_response(true, '已成功退出登录');
}

/**
 * 处理获取用户信息
 */
function handle_get_user_info() {
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
    
    // 安全过滤，不返回密码
    unset($user['password']);
    
    json_response(true, '获取成功', $user);
}

/**
 * 处理检查邮箱
 */
function handle_check_email() {
    $data = get_request_data();
    $email = trim($data['email'] ?? '');
    
    if (empty($email)) {
        json_response(false, '邮箱不能为空');
    }
    
    if (!validate_qq_email($email)) {
        json_response(false, '请使用QQ邮箱 (@qq.com)');
    }
    
    $users = load_data(USERS_FILE);
    foreach ($users as $user) {
        if ($user['email'] === $email) {
            json_response(false, '该QQ邮箱已被注册');
        }
    }
    
    json_response(true, 'QQ邮箱可用');
}

/**
 * 处理测试连接
 */
function handle_test() {
    json_response(true, 'API服务器正常运行', [
        'version' => '1.0',
        'server_time' => date('Y-m-d H:i:s'),
        'timestamp' => time(),
        'data_dir' => DATA_DIR,
        'file_status' => [
            'users' => file_exists(USERS_FILE) ? '正常' : '异常',
            'messages' => file_exists(MESSAGES_FILE) ? '正常' : '异常',
            'sessions' => file_exists(SESSIONS_FILE) ? '正常' : '异常',
            'online' => file_exists(ONLINE_FILE) ? '正常' : '异常'
        ],
        'statistics' => [
            'users' => count(load_data(USERS_FILE)),
            'messages' => count(load_data(MESSAGES_FILE)),
            'online' => count(load_data(ONLINE_FILE))
        ]
    ]);
}
?>