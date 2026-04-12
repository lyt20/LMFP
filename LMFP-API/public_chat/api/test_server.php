<?php
// test_server.php - 放在api目录下
header('Content-Type: application/json; charset=utf-8');

// 测试JSON响应
$test_response = [
    'success' => true,
    'message' => '服务器正常',
    'timestamp' => time()
];

echo json_encode($test_response, JSON_UNESCAPED_UNICODE);
?>