<?php
header("Content-Type: text/plain; charset=utf-8");

/**
 * 从远程URL获取服务器列表（带调试）
 * @param string $url 数据源URL
 * @return array 解析后的服务器数组
 */
function getFrpServers($url) {
    $servers = [];
    // 设置超时时间（秒）
    $context = stream_context_create([
        'http' => [
            'timeout' => 10,
            'user_agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        ]
    ]);

    // 获取远程内容
    $content = @file_get_contents($url, false, $context);
    if (!$content) {
        echo "[调试] 无法获取远程文件内容\n";
        return $servers;
    }

    // 输出原始内容（调试用）
    //echo "[调试] 远程文件原始内容：\n{$content}\n\n";

    // 按行解析内容（兼容不同换行符）
    $lines = preg_split('/\r\n|\r|\n/', $content);
    $lineNum = 0;
    foreach ($lines as $line) {
        $lineNum++;
        $line = trim($line);
        //echo "[调试] 第{$lineNum}行：原始内容=[{$line}] ";

        if (empty($line)) {
            //echo "→ 空行，跳过\n";
            continue;
        }

        // 宽松正则：兼容名称含数字/特殊字符、端口任意位数
        // 匹配规则：数字#[]包裹的内容，内部包含名称、IP、端口
        //preg_match('/^(\d+)#\[(.+?)\s+([0-9\.]{7,15}):(\d+)\]$/', $line, $matches);
        preg_match('/^(\d+)#\[(.+?)\s+([0-9\.]{7,15}):(\d+)(\s+.+?)?\]$/', $line, $matches); 
        
        if (count($matches) >= 5) {
            $server = [
                'id' => $matches[1],
                'name' => trim($matches[2]),
                'ip' => $matches[3],
                'port' => $matches[4]
            ];
            $servers[] = $server;
            //echo "→ 解析成功：ID={$server['id']} 名称={$server['name']} IP={$server['ip']} 端口={$server['port']}\n";
        } else {
            //echo "→ 解析失败（格式不匹配）\n";
        }
    }
    
    //echo "\n[调试] 最终解析到 ".count($servers)." 个服务器\n\n";
    return $servers;
}

/**
 * 纯PHP实现TCP端口延迟检测（替代ping）
 * @param string $ip IP地址
 * @param int $port 端口号
 * @param int $timeout 超时时间（秒）
 * @return string 延迟值（ms）或超时提示
 */
function tcpPing($ip, $port, $timeout = 2) {
    // 记录开始时间（微秒）
    $startTime = microtime(true);
    
    // 创建套接字（增加错误抑制，避免警告）
    $socket = @fsockopen($ip, $port, $errno, $errstr, $timeout);
    
    // 记录结束时间
    $endTime = microtime(true);
    
    // 计算延迟（毫秒）
    $delay = round(($endTime - $startTime) * 1000);
    
    if ($socket) {
        fclose($socket);
        return $delay . "ms";
    } else {
        return "超时（错误码：{$errno}，信息：{$errstr}）";
    }
}

// 主程序
//$url = "https://lytapi.asia/fplt.txt";
$url = "https://lytapi.asia/frplistlytapiit.txt";
$servers = getFrpServers($url);

if (empty($servers)) {
    echo "无法获取服务器列表或列表为空\n";
    exit;
}

// 遍历检测并输出
//echo "===== 服务器延迟检测结果 =====\n";
foreach ($servers as $server) {
    $delay = tcpPing($server['ip'], $server['port']);
    echo "{$server['id']}#{$server['name']} - {$delay}\n";
}
?>