<?php
// vert.php 示例

header('Content-Type: text/plain; charset=utf-8');

// 获取所有可能的参数
$tk  = isset($_GET['tk'])  ? trim($_GET['tk'])  : '';
$tko = isset($_GET['tko']) ? trim($_GET['tko']) : '';
$tkn = isset($_GET['tkn']) ? trim($_GET['tkn']) : '';

$file_path     = __DIR__ . '/tk/tk.txt';
$tko_file_path = __DIR__ . '/tk/tko.txt';

// 确保存放目录存在
if (!is_dir(__DIR__ . '/tk')) {
    mkdir(__DIR__ . '/tk', 0755, true);
}

// ========== 1. 优先处理 tko 一次性注册码 ==========
if (!empty($tko)) {
    if (!file_exists($tko_file_path)) {
        echo "false";
        exit;
    }

    $tko_lines = file($tko_file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $tko_exists = false;
    $new_tko_lines = [];

    foreach ($tko_lines as $line) {
        $line = trim($line);
        if (strcasecmp($line, $tko) === 0) {
            $tko_exists = true;
        } else {
            $new_tko_lines[] = $line;
        }
    }

    if ($tko_exists) {
        // 将 tk 加入白名单（如果尚未存在）
        $tk_already = false;
        if (file_exists($file_path)) {
            $tk_lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            foreach ($tk_lines as $tline) {
                if (strcasecmp(trim($tline), $tk) === 0) {
                    $tk_already = true;
                    break;
                }
            }
        }
        if (!$tk_already && !empty($tk)) {
            file_put_contents($file_path, $tk . PHP_EOL, FILE_APPEND | LOCK_EX);
        }

        // 移除已使用的 tko
        $new_content = empty($new_tko_lines) ? "" : implode(PHP_EOL, $new_tko_lines) . PHP_EOL;
        file_put_contents($tko_file_path, $new_content, LOCK_EX);

        echo "true";
    } else {
        echo "false";
    }
    exit;
}

// ========== 2. 处理 tkn 相关逻辑 ==========
if (!empty($tkn)) {
    // 情况 A：同时存在 tk 和 tkn → 将 tkn 添加到白名单（需要验证 tk 有效）
    if (!empty($tk)) {
        // 检查 tk 是否在白名单中
        $tk_valid = false;
        if (file_exists($file_path)) {
            $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
            foreach ($lines as $line) {
                if (strcasecmp(trim($line), $tk) === 0) {
                    $tk_valid = true;
                    break;
                }
            }
        }

        if ($tk_valid) {
            // 检查 tkn 是否已存在，避免重复
            $tkn_exists = false;
            if (file_exists($file_path)) {
                $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
                foreach ($lines as $line) {
                    if (strcasecmp(trim($line), $tkn) === 0) {
                        $tkn_exists = true;
                        break;
                    }
                }
            }
            if (!$tkn_exists) {
                file_put_contents($file_path, $tkn . PHP_EOL, FILE_APPEND | LOCK_EX);
            }
            echo "true";
        } else {
            echo "false";
        }
        exit;
    }

    // 情况 B：只有 tkn（没有 tk，也没有 tko）→ 模仿 tk 验证，检查 tkn 是否在白名单中
    if (file_exists($file_path)) {
        $lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strcasecmp(trim($line), $tkn) === 0) {
                echo "true";
                exit;
            }
        }
    }
    echo "false";
    exit;
}

// ========== 3. 常规 tk 验证（只有 tk 参数） ==========
if (empty($tk)) {
    echo "false";
    exit;
}

if (!file_exists($file_path)) {
    echo "false";
    exit;
}

$lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
$valid = false;
foreach ($lines as $line) {
    if (strcasecmp(trim($line), $tk) === 0) {
        $valid = true;
        break;
    }
}

echo $valid ? "true" : "false";