<?php
header('Content-Type: text/plain; charset=utf-8');

echo "=== API服务诊断 ===\n\n";

// 检查文件权限
$files = [
    'rooms.json' => '数据文件',
    'api_log.txt' => '日志文件',
    'api.php' => '主程序'
];

foreach ($files as $file => $desc) {
    if (file_exists($file)) {
        $perms = substr(sprintf('%o', fileperms($file)), -4);
        $writable = is_writable($file) ? '可写' : '不可写';
        echo "{$desc} ({$file}): 权限{$perms}, {$writable}\n";
    } else {
        echo "{$desc} ({$file}): 文件不存在\n";
    }
}

echo "\n=== 数据文件内容 ===\n";
if (file_exists('rooms.json')) {
    $content = file_get_contents('rooms.json');
    $data = json_decode($content, true);
    if ($data) {
        echo "总房间数: " . count($data['rooms'] ?? []) . "\n";
        echo "文件创建: " . date('Y-m-d H:i:s', $data['created_at'] ?? 0) . "\n";
        echo "最后更新: " . date('Y-m-d H:i:s', $data['updated_at'] ?? 0) . "\n";
        
        if (!empty($data['rooms'])) {
            echo "\n房间列表:\n";
            foreach ($data['rooms'] as $room) {
                $status = (time() - $room['last_update'] <= 60) ? '活跃' : '过期';
                echo "- {$room['room_name']} ({$room['room_code']}_{$room['node_id']}) - {$status}\n";
            }
        }
    } else {
        echo "数据文件格式错误\n";
    }
} else {
    echo "数据文件不存在\n";
}

echo "\n=== 最近日志 ===\n";
if (file_exists('api_log.txt')) {
    $logs = file('api_log.txt');
    $recent_logs = array_slice($logs, -10); // 最后10行
    foreach ($recent_logs as $log) {
        echo $log;
    }
} else {
    echo "日志文件不存在\n";
}

echo "\n=== PHP信息 ===\n";
echo "内存限制: " . ini_get('memory_limit') . "\n";
echo "最大执行时间: " . ini_get('max_execution_time') . "\n";
echo "POST大小限制: " . ini_get('post_max_size') . "\n";
?>