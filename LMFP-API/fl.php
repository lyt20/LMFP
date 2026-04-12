<?php
// 方法2: 逐行读取文件
$filename = 'frplist58.txt';

if (file_exists($filename)) {
    $file = fopen($filename, 'r');
    
    if ($file) {
        echo "<pre>"; // 使用 pre 标签保留格式
        
        while (($line = fgets($file)) !== false) {
            echo htmlspecialchars($line); // 输出每行内容
        }
        
        echo "</pre>";
        fclose($file);
    } else {
        echo "无法打开文件！";
    }
} else {
    echo "文件 {$filename} 不存在！";
}
?>