<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// 处理预检请求
if ($_SERVER['REQUEST_METHOD'] == 'OPTIONS') {
    http_response_code(200);
    exit(0);
}

// 设置时区
date_default_timezone_set('Asia/Shanghai');

// 数据存储文件
$data_file = 'rooms.json';
$backup_file = 'rooms_backup.json';
$log_file = 'api_log.txt';

// 确保数据文件存在
if (!file_exists($data_file)) {
    file_put_contents($data_file, json_encode(['rooms' => [], 'created_at' => time()]));
}

/**
 * 记录日志
 */
function write_log($message) {
    global $log_file;
    $timestamp = date('Y-m-d H:i:s');
    $log_message = "[{$timestamp}] {$message}\n";
    file_put_contents($log_file, $log_message, FILE_APPEND | LOCK_EX);
}

/**
 * 读取房间数据
 */
function read_rooms() {
    global $data_file;
    write_log("读取房间数据");
    
    if (!file_exists($data_file)) {
        write_log("数据文件不存在，创建新文件");
        return ['rooms' => [], 'created_at' => time()];
    }
    
    $content = file_get_contents($data_file);
    if ($content === false) {
        write_log("读取数据文件失败");
        return ['rooms' => [], 'created_at' => time()];
    }
    
    $data = json_decode($content, true);
    if ($data === null) {
        write_log("JSON解析失败，使用默认数据");
        return ['rooms' => [], 'created_at' => time()];
    }
    
    // 确保数据结构正确
    if (!isset($data['rooms'])) {
        $data['rooms'] = [];
    }
    
    write_log("成功读取 " . count($data['rooms']) . " 个房间");
    return $data;
}

/**
 * 保存房间数据
 */
function save_rooms($data) {
    global $data_file, $backup_file;
    
    write_log("保存房间数据，当前房间数: " . count($data['rooms']));
    
    // 创建备份
    if (file_exists($data_file)) {
        if (!copy($data_file, $backup_file)) {
            write_log("警告：创建备份文件失败");
        }
    }
    
    // 添加更新时间
    $data['updated_at'] = time();
    
    $json_data = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    if ($json_data === false) {
        write_log("错误：JSON编码失败");
        return false;
    }
    
    $result = file_put_contents($data_file, $json_data, LOCK_EX);
    if ($result === false) {
        write_log("错误：写入数据文件失败");
        return false;
    }
    
    write_log("房间数据保存成功");
    return true;
}

/**
 * 清理过期房间（超过1分钟未更新）
 */
function cleanup_expired_rooms() {
    $data = read_rooms();
    $current_time = time();
    $cleaned_count = 0;
    $total_rooms = count($data['rooms']);
    
    write_log("开始清理过期房间，当前总数: {$total_rooms}");
    
    foreach ($data['rooms'] as $key => $room) {
        $last_update = $room['last_update'];
        $time_diff = $current_time - $last_update;
        
        if ($time_diff > 60) { // 1分钟
            $remote_port = $room['remote_port'];
            $node_id = $room['node_id'];
            write_log("清理过期房间: {$remote_port}_{$node_id}, 最后更新: {$time_diff}秒前");
            unset($data['rooms'][$key]);
            $cleaned_count++;
        }
    }
    
    if ($cleaned_count > 0) {
        $data['rooms'] = array_values($data['rooms']);
        if (save_rooms($data)) {
            write_log("成功清理 {$cleaned_count} 个过期房间，剩余: " . count($data['rooms']));
        } else {
            write_log("错误：清理后保存数据失败");
        }
    } else {
        write_log("没有需要清理的过期房间");
    }
    
    return $cleaned_count;
}

/**
 * 生成响应
 */
function send_response($success, $message = '', $data = null) {
    $response = [
        'success' => $success,
        'message' => $message,
        'timestamp' => time(),
        'server_time' => date('Y-m-d H:i:s')
    ];
    
    if ($data !== null) {
        $response['data'] = $data;
    }
    
    // 记录响应
    write_log("发送响应: " . ($success ? '成功' : '失败') . " - {$message}");
    
    echo json_encode($response, JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * 获取客户端IP
 */
function get_client_ip() {
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        return $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        return $_SERVER['HTTP_X_FORWARDED_FOR'];
    } else {
        return $_SERVER['REMOTE_ADDR'];
    }
}

/**
 * 验证房间数据 - 新版本适配远程端口格式
 */
function validate_room_data($input) {
    if (!$input) {
        return "无效的JSON数据";
    }
    
    // 新版本使用 remote_port 和 node_id
    if (!isset($input['remote_port']) || !is_numeric($input['remote_port'])) {
        return "缺少或无效的远程端口 (remote_port)";
    }
    
    if (!isset($input['node_id']) || !is_numeric($input['node_id'])) {
        return "缺少或无效的节点ID (node_id)";
    }
    
    $remote_port = intval($input['remote_port']);
    if ($remote_port < 10000 || $remote_port > 60000) {
        return "远程端口必须在10000-60000范围内";
    }
    
    $node_id = intval($input['node_id']);
    if ($node_id < 1 || $node_id > 1000) {
        return "节点ID必须在1-1000范围内";
    }
    
    return null; // 验证通过
}

/**
 * 根据远程端口和节点ID查找房间
 */
function find_room_by_port_and_node($rooms, $remote_port, $node_id) {
    foreach ($rooms as $index => $room) {
        if ($room['remote_port'] === $remote_port && $room['node_id'] === $node_id) {
            return $index;
        }
    }
    return -1;
}

// 主逻辑
try {
    $method = $_SERVER['REQUEST_METHOD'];
    $client_ip = get_client_ip();
    
    write_log("收到请求: {$method} from {$client_ip}");
    
    // 记录请求数据（POST和DELETE）
    if ($method == 'POST' || $method == 'DELETE') {
        $input_data = file_get_contents('php://input');
        write_log("请求数据: {$input_data}");
    }
    
    // 每次请求都清理过期房间
    $cleaned_count = cleanup_expired_rooms();
    
    switch ($method) {
        case 'GET':
            // 获取房间列表或查询特定房间
            $input = $_GET; // GET请求参数
            
            if (isset($input['remote_port']) && isset($input['node_id'])) {
                // 查询特定房间信息
                write_log("处理GET请求 - 查询特定房间");
                
                $remote_port = intval($input['remote_port']);
                $node_id = intval($input['node_id']);
                
                $data = read_rooms();
                $room_index = find_room_by_port_and_node($data['rooms'], $remote_port, $node_id);
                
                if ($room_index >= 0) {
                    $room = $data['rooms'][$room_index];
                    write_log("找到房间: {$remote_port}_{$node_id}");
                    send_response(true, '获取房间信息成功', $room);
                } else {
                    write_log("房间不存在: {$remote_port}_{$node_id}");
                    send_response(false, '房间不存在');
                }
            } else {
                // 获取所有房间列表
                write_log("处理GET请求 - 获取房间列表");
                
                $data = read_rooms();
                
                // 过滤只返回公开房间
                $public_rooms = [];
                foreach ($data['rooms'] as $room) {
                    if ($room['is_public']) {
                        $public_rooms[] = $room;
                    }
                }
                
                $public_rooms_count = count($public_rooms);
                
                $response_data = [
                    'rooms' => $public_rooms,
                    'stats' => [
                        'total_rooms' => count($data['rooms']),
                        'public_rooms' => $public_rooms_count,
                        'private_rooms' => count($data['rooms']) - $public_rooms_count,
                        'cleaned_rooms' => $cleaned_count,
                        'server_time' => time(),
                        'server_time_str' => date('Y-m-d H:i:s')
                    ]
                ];
                
                write_log("返回 {$public_rooms_count} 个公开房间");
                send_response(true, '获取房间列表成功', $response_data);
            }
            break;
            
        case 'POST':
            // 添加或更新房间（心跳机制）
            write_log("处理POST请求 - 添加/更新房间");
            
            $input = json_decode(file_get_contents('php://input'), true);
            
            // 验证数据
            $validation_error = validate_room_data($input);
            if ($validation_error) {
                write_log("数据验证失败: {$validation_error}");
                send_response(false, $validation_error);
            }
            
            $data = read_rooms();
            $remote_port = intval($input['remote_port']);
            $node_id = intval($input['node_id']);
            $current_time = time();
            
            // 查找是否已存在相同房间
            $room_index = find_room_by_port_and_node($data['rooms'], $remote_port, $node_id);
            
            if ($room_index >= 0) {
                // 更新现有房间（心跳更新）
                write_log("更新现有房间: {$remote_port}_{$node_id}");
                
                $data['rooms'][$room_index]['last_update'] = $current_time;
                
                // 更新可选字段
                if (isset($input['player_count'])) {
                    $data['rooms'][$room_index]['player_count'] = intval($input['player_count']);
                }
                if (isset($input['room_name'])) {
                    $data['rooms'][$room_index]['room_name'] = $input['room_name'];
                }
                if (isset($input['description'])) {
                    $data['rooms'][$room_index]['description'] = $input['description'];
                }
                if (isset($input['game_version'])) {
                    $data['rooms'][$room_index]['game_version'] = $input['game_version'];
                }
                if (isset($input['host_player'])) {
                    $data['rooms'][$room_index]['host_player'] = $input['host_player'];
                }
                if (isset($input['is_public'])) {
                    $data['rooms'][$room_index]['is_public'] = boolval($input['is_public']);
                }
                if (isset($input['server_addr'])) {
                    $data['rooms'][$room_index]['server_addr'] = $input['server_addr'];
                }
                
                $message = '房间心跳更新成功';
            } else {
                // 添加新房间
                write_log("创建新房间: {$remote_port}_{$node_id}");
                
                $new_room = [
                    'remote_port' => $remote_port,
                    'node_id' => $node_id,
                    'room_name' => $input['room_name'] ?? '未命名房间',
                    'game_version' => $input['game_version'] ?? '未知版本',
                    'player_count' => intval($input['player_count'] ?? 1),
                    'max_players' => intval($input['max_players'] ?? 20),
                    'description' => $input['description'] ?? '',
                    'is_public' => boolval($input['is_public'] ?? true),
                    'create_time' => $current_time,
                    'last_update' => $current_time,
                    'server_addr' => $input['server_addr'] ?? '47.104.23.23', // 默认FRP服务器地址
                    'host_player' => $input['host_player'] ?? '未知玩家',
                    'full_room_code' => $remote_port . '_' . $node_id // 完整的房间号
                ];
                
                array_unshift($data['rooms'], $new_room);
                $message = '房间创建成功';
            }
            
            // 限制房间数量，最多保存100个房间
            if (count($data['rooms']) > 100) {
                $removed_count = count($data['rooms']) - 100;
                $data['rooms'] = array_slice($data['rooms'], 0, 100);
                write_log("房间数量超过限制，移除 {$removed_count} 个最旧的房间");
            }
            
            if (save_rooms($data)) {
                $room_status = $room_index >= 0 ? '更新' : '创建';
                write_log("房间{$room_status}成功: {$remote_port}_{$node_id}");
                send_response(true, $message);
            } else {
                write_log("错误：保存房间数据失败");
                send_response(false, '保存房间信息失败');
            }
            break;
            
        case 'DELETE':
            // 删除房间（房主主动关闭房间）
            write_log("处理DELETE请求 - 删除房间");
            
            $input = json_decode(file_get_contents('php://input'), true);
            
            // 验证数据
            $validation_error = validate_room_data($input);
            if ($validation_error) {
                write_log("数据验证失败: {$validation_error}");
                send_response(false, $validation_error);
            }
            
            $data = read_rooms();
            $remote_port = intval($input['remote_port']);
            $node_id = intval($input['node_id']);
            $found = false;
            
            $room_index = find_room_by_port_and_node($data['rooms'], $remote_port, $node_id);
            
            if ($room_index >= 0) {
                write_log("删除房间: {$remote_port}_{$node_id}");
                unset($data['rooms'][$room_index]);
                $found = true;
            }
            
            if ($found) {
                $data['rooms'] = array_values($data['rooms']);
                if (save_rooms($data)) {
                    write_log("房间删除成功: {$remote_port}_{$node_id}");
                    send_response(true, '房间删除成功');
                } else {
                    write_log("错误：删除后保存数据失败");
                    send_response(false, '删除房间失败');
                }
            } else {
                write_log("删除失败：房间不存在 {$remote_port}_{$node_id}");
                send_response(false, '房间不存在');
            }
            break;
            
        default:
            write_log("不支持的请求方法: {$method}");
            send_response(false, '不支持的请求方法');
            break;
    }
    
} catch (Exception $e) {
    $error_message = '服务器错误: ' . $e->getMessage();
    write_log("异常: {$error_message}");
    send_response(false, $error_message);
}

// 记录请求完成
write_log("请求处理完成\n" . str_repeat("-", 50));
?>