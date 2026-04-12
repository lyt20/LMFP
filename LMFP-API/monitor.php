<?php
// monitor.php - 房间数据监控
header('Content-Type: text/plain; charset=utf-8');

$data_file = 'rooms.json';
$log_file = 'api_log.txt';

function read_rooms() {
    global $data_file;
    
    if (!file_exists($data_file)) {
        return ['rooms' => []];
    }
    
    $content = file_get_contents($data_file);
    $data = json_decode($content, true);
    return $data ?: ['rooms' => []];
}

function get_log_stats() {
    global $log_file;
    
    if (!file_exists($log_file)) {
        return '日志文件不存在';
    }
    
    $log_content = file_get_contents($log_file);
    $lines = explode("\n", $log_content);
    $total_lines = count($lines);
    $today_lines = 0;
    
    $today = date('Y-m-d');
    foreach ($lines as $line) {
        if (strpos($line, "[{$today}") === 0) {
            $today_lines++;
        }
    }
    
    return "总日志行数: {$total_lines}, 今日: {$today_lines}";
}

$data = read_rooms();
$current_time = time();

echo "=== LMFP Minecraft联机大厅监控 ===\n";
echo "服务器时间: " . date('Y-m-d H:i:s') . "\n";
echo "数据文件: rooms.json\n";
echo "日志文件: " . get_log_stats() . "\n\n";

echo "=== 房间统计 ===\n";
echo "总房间数: " . count($data['rooms']) . "\n";

// 统计公开和私有房间
$public_rooms = 0;
$private_rooms = 0;
$active_rooms = 0;
$expired_rooms = 0;

// 按节点统计
$node_stats = [];
$port_range = ['min' => 60000, 'max' => 10000]; // 初始化端口范围

foreach ($data['rooms'] as $room) {
    if ($room['is_public']) {
        $public_rooms++;
    } else {
        $private_rooms++;
    }
    
    $time_diff = $current_time - $room['last_update'];
    if ($time_diff <= 60) {
        $active_rooms++;
    } else {
        $expired_rooms++;
    }
    
    // 节点统计
    $node_id = $room['node_id'];
    if (!isset($node_stats[$node_id])) {
        $node_stats[$node_id] = 0;
    }
    $node_stats[$node_id]++;
    
    // 端口范围统计
    $remote_port = $room['remote_port'];
    if ($remote_port < $port_range['min']) {
        $port_range['min'] = $remote_port;
    }
    if ($remote_port > $port_range['max']) {
        $port_range['max'] = $remote_port;
    }
}

echo "公开房间: {$public_rooms}\n";
echo "私有房间: {$private_rooms}\n";
echo "活跃房间: {$active_rooms}\n";
echo "过期房间: {$expired_rooms}\n";
echo "端口范围: {$port_range['min']} - {$port_range['max']}\n\n";

// 节点统计
if (!empty($node_stats)) {
    echo "=== 节点分布 ===\n";
    ksort($node_stats);
    foreach ($node_stats as $node_id => $count) {
        echo "节点 #{$node_id}: {$count} 个房间\n";
    }
    echo "\n";
}

echo "=== 最近房间 (最多显示10个) ===\n";
$recent_rooms = array_slice($data['rooms'], 0, 10);
if (empty($recent_rooms)) {
    echo "暂无房间数据\n";
} else {
    foreach ($recent_rooms as $room) {
        $time_diff = $current_time - $room['last_update'];
        $status = $time_diff <= 60 ? '🟢活跃' : '🔴过期';
        $type = $room['is_public'] ? '公开' : '私有';
        $full_room_code = $room['remote_port'] . '_' . $room['node_id'];
        
        // 显示房间基本信息
        $room_info = "{$full_room_code} - {$room['room_name']}";
        
        // 显示游戏版本和玩家数量
        $game_info = "({$room['game_version']}, {$room['player_count']}/{$room['max_players']}人)";
        
        // 显示服务器信息
        $server_info = isset($room['server_addr']) ? "服务器: {$room['server_addr']}" : "服务器: 未知";
        
        echo "{$room_info} {$game_info} - {$type} - {$status} ({$time_diff}秒)\n";
        echo "  {$server_info}, 房主: {$room['host_player']}\n";
        
        // 显示房间描述（如果有）
        if (!empty($room['description']) && $room['description'] !== '欢迎来玩！') {
            $desc = mb_strlen($room['description']) > 50 ? mb_substr($room['description'], 0, 50) . '...' : $room['description'];
            echo "  描述: {$desc}\n";
        }
        echo "\n";
    }
}

echo "=== 系统信息 ===\n";
echo "内存使用: " . round(memory_get_usage() / 1024 / 1024, 2) . " MB\n";
echo "峰值内存: " . round(memory_get_peak_usage() / 1024 / 1024, 2) . " MB\n";
echo "磁盘空间: " . round(disk_free_space('.') / 1024 / 1024 / 1024, 2) . " GB 可用\n";

if (isset($data['created_at'])) {
    $created_time = date('Y-m-d H:i:s', $data['created_at']);
    $created_diff = $current_time - $data['created_at'];
    $created_days = floor($created_diff / 86400);
    echo "数据创建: {$created_time} ({$created_days}天前)\n";
}

if (isset($data['updated_at'])) {
    $updated_time = date('Y-m-d H:i:s', $data['updated_at']);
    $update_diff = $current_time - $data['updated_at'];
    echo "最后更新: {$updated_time} ({$update_diff}秒前)\n";
}

// 显示文件大小
if (file_exists($data_file)) {
    $file_size = filesize($data_file);
    echo "数据文件大小: " . round($file_size / 1024, 2) . " KB\n";
}

if (file_exists($log_file)) {
    $log_size = filesize($log_file);
    echo "日志文件大小: " . round($log_size / 1024, 2) . " KB\n";
}

// 显示PHP信息
echo "PHP版本: " . PHP_VERSION . "\n";
echo "运行用户: " . get_current_user() . "\n";

// 显示请求统计（从日志中分析）
echo "\n=== 请求统计 (今日) ===\n";
if (file_exists($log_file)) {
    $log_content = file_get_contents($log_file);
    $today = date('Y-m-d');
    
    $total_requests = substr_count($log_content, "收到请求:");
    $get_requests = substr_count($log_content, "处理GET请求");
    $post_requests = substr_count($log_content, "处理POST请求");
    $delete_requests = substr_count($log_content, "处理DELETE请求");
    
    // 今日请求
    $today_pattern = "/\\[{$today}.*收到请求:/";
    preg_match_all($today_pattern, $log_content, $today_matches);
    $today_requests = count($today_matches[0]);
    
    echo "总请求数: {$total_requests}\n";
    echo "今日请求: {$today_requests}\n";
    echo "GET请求: {$get_requests}\n";
    echo "POST请求: {$post_requests}\n";
    echo "DELETE请求: {$delete_requests}\n";
} else {
    echo "日志文件不存在，无法统计请求数据\n";
}

echo "\n" . str_repeat("=", 50) . "\n";
echo "监控脚本运行完成 - " . date('Y-m-d H:i:s') . "\n";
?>