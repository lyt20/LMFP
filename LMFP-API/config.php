<?php
// config.php - 配置文件
return [
    // 基本设置
    'max_rooms' => 100,                    // 最大房间数量
    'room_timeout' => 60,                  // 房间超时时间（秒）
    'cleanup_interval' => 30,              // 清理间隔（秒）
    
    // 文件设置
    'data_file' => 'rooms.json',           // 数据文件
    'backup_file' => 'rooms_backup.json',  // 备份文件
    'log_file' => 'api_log.txt',           // 日志文件
    
    // 验证设置
    'max_node_id' => 1000,                 // 最大节点ID
    'room_code_length' => 6,               // 房间代码长度
    
    // 安全设置
    'enable_cors' => true,                 // 启用CORS
    'allowed_origins' => ['*'],            // 允许的域名
    'max_request_size' => 1024 * 1024,     // 最大请求大小（1MB）
];
?>