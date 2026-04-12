<?php
// 版本号API接口
// 用于接收来自admin.php的请求并更新lytapi.asia服务器上的v.txt文件

header('Content-Type: application/json; charset=utf-8');

// 设置跨域请求头（如果需要）
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: POST, GET, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type");

// 处理预检请求
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

try {
    // 获取请求方法
    $method = $_SERVER['REQUEST_METHOD'];
    
    if ($method === 'POST') {
        // 获取POST数据
        $input = file_get_contents('php://input');
        $data = json_decode($input, true);
        
        // 如果JSON解析失败，尝试从POST变量获取
        if ($data === null) {
            $data = $_POST;
        }
        
        // 检查是否有版本号参数
        $version = isset($data['version']) ? trim($data['version']) : '';
        
        if (empty($version)) {
            throw new Exception('版本号不能为空');
        }
        
        // 验证版本号格式（可选）
        if (!preg_match('/^[0-9]+(\.[0-9]+)*$/', $version)) {
            throw new Exception('版本号格式不正确');
        }
        
        // 定义版本文件路径
        $version_file = 'v.txt';
        
        // 写入版本号到文件
        if (file_put_contents($version_file, $version) === false) {
            throw new Exception('无法写入版本文件');
        }
        
        // 返回成功响应
        echo json_encode([
            'success' => true,
            'message' => '版本号更新成功',
            'version' => $version,
            'timestamp' => date('Y-m-d H:i:s')
        ], JSON_UNESCAPED_UNICODE);
        
    } else if ($method === 'GET') {
        // 处理GET请求，返回当前版本号
        $version_file = 'v.txt';
        $current_version = 'unknown';
        
        if (file_exists($version_file)) {
            $current_version = trim(file_get_contents($version_file));
        }
        
        echo json_encode([
            'success' => true,
            'version' => $current_version,
            'timestamp' => date('Y-m-d H:i:s')
        ], JSON_UNESCAPED_UNICODE);
        
    } else {
        throw new Exception('不支持的请求方法');
    }
    
} catch (Exception $e) {
    // 错误处理
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => $e->getMessage(),
        'timestamp' => date('Y-m-d H:i:s')
    ], JSON_UNESCAPED_UNICODE);
}

?>