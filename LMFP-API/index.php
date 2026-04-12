<?php
$countFile = 'ccc.txt';
if (!file_exists($countFile)) {
    file_put_contents($countFile, '1');
    $totalVisits = 1;
} else {
    $currentCount = file_get_contents($countFile);
    $currentCount = intval($currentCount);
    $newCount = $currentCount + 1;
    file_put_contents($countFile, $newCount);
    $totalVisits = $newCount;
}
@chmod($countFile, 0644);

// 今日访问计数逻辑
$today = date('Y-m-d');
$todayCountFile = "{$today}_visits.txt";
if (!file_exists($todayCountFile)) {
    file_put_contents($todayCountFile, '1');
    $todayVisits = 1;
} else {
    $todayCurrent = file_get_contents($todayCountFile);
    $todayCurrent = intval($todayCurrent);
    $todayNew = $todayCurrent + 1;
    file_put_contents($todayCountFile, $todayNew);
    $todayVisits = $todayNew;
}
@chmod($todayCountFile, 0644);

?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LMFP联机平台 - Lyt_IT</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name='description' content='LMFP是一个开放性联机平台'>
    <link href="https://cdn.jsdelivr.net/npm/font-awesome@4.7.0/css/font-awesome.min.css" rel="stylesheet">
    <link rel="icon" href="yjtp.png" type="image/x-icon">

    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        primary: '#4CAF50',
                        secondary: '#2E7D32',
                        accent: '#8BC34A',
                        dark: '#1B5E20',
                        light: '#E8F5E9',
                        minecraft: '#52A552'
                    },
                    fontFamily: {
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    },
                }
            }
        }
    </script>
    <style type="text/tailwindcss">
        @layer utilities {
            .text-shadow {
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .text-shadow-lg {
                text-shadow: 0 4px 8px rgba(0,0,0,0.25);
            }
            .transition-transform {
                transition-property: transform;
                transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
                transition-duration: 300ms;
            }
            .hover-scale {
                @apply hover:scale-105 transition-all duration-300;
            }
            .card-effect {
                @apply shadow-lg hover:shadow-xl transition-all duration-300 rounded-lg overflow-hidden;
            }
        }
    </style>
</head>
<body class="bg-gray-50 font-sans text-gray-800">
    <!-- 导航栏 -->
    <header class="bg-white shadow-md fixed w-full z-50 transition-all duration-300" id="navbar">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex items-center space-x-2">
                <!--<i class="fa fa-cube text-minecraft text-3xl"></i>-->
                <img src="sdfghj.png" alt="示例图片" width="150" height="200">
                <!--<h1 class="text-xl md:text-2xl font-bold text-dark">LMFP</h1>-->
            </div>
            
            <nav class="hidden md:flex space-x-8">
                <a href="#features" class="text-gray-600 hover:text-primary transition-colors">功能介绍</a>
                <a href="#screenshots" class="text-gray-600 hover:text-primary transition-colors">软件截图</a>
                <a href="#download" class="text-gray-600 hover:text-primary transition-colors">立即下载</a>
                <a href="#faq" class="text-gray-600 hover:text-primary transition-colors">常见问题</a>
                <a href="LNW" class="text-gray-600 hover:text-primary transition-colors">了解Lyt_IT群组服务器</a>
                <a href="yl" class="text-gray-600 hover:text-primary transition-colors">友情链接</a>
            </nav>
            
            <button class="md:hidden text-gray-600 focus:outline-none" id="menuBtn">
                <i class="fa fa-bars text-xl"></i>
            </button>
        </div>
        
        <!-- 移动端菜单 -->
        <div class="md:hidden hidden bg-white w-full" id="mobileMenu">
            <div class="container mx-auto px-4 py-2 flex flex-col space-y-3">
                <a href="#features" class="py-2 text-gray-600 hover:text-primary transition-colors">功能介绍</a>
                <a href="#screenshots" class="py-2 text-gray-600 hover:text-primary transition-colors">软件截图</a>
                <a href="#download" class="py-2 text-gray-600 hover:text-primary transition-colors">立即下载</a>
                <a href="#faq" class="py-2 text-gray-600 hover:text-primary transition-colors">常见问题</a>
                <a href="LNW" class="py-2 text-gray-600 hover:text-primary transition-colors">了解Lyt_IT群组服务器</a>
                <a href="yl" class="py-2 text-gray-600 hover:text-primary transition-colors">友情链接</a>
            </div>
        </div>
    </header>

    <!-- 英雄区域 -->
    <section class="pt-28 pb-20 bg-gradient-to-br from-light to-white">
        <div class="container mx-auto px-4">
            <div class="flex flex-col md:flex-row items-center">
                <div class="md:w-1/2 mb-10 md:mb-0">
                    <h1 class="text-[clamp(2rem,5vw,3.5rem)] font-bold text-dark leading-tight text-shadow-lg mb-4">
                        LMFP<br>Minecraft联机平台
                    </h1>
                    <p class="text-gray-600 text-lg mb-8 max-w-lg">
                        无需复杂设置，一键创建或加入Minecraft房间，内置联机大厅，让你认识更多的玩家。
                    </p>
                    <div class="flex flex-col sm:flex-row gap-4">
                        <a href="#download" class="bg-primary hover:bg-secondary text-white font-bold py-3 px-8 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 text-center">
                            <i class="fa fa-download mr-2"></i>立即下载
                        </a>
                        <a href="https://qm.qq.com/cgi-bin/qm/qr?k=-LlckSeA5LtOHyuUETMDjd91xAOO7v-2&jump_from=webapi&authKey=9AuAKTEp9ED2bpd679Pb+5EhwkgJjsFX8UKDt1UM3CZ2AOUFVsYMO+XuPaiqkgHX" class="bg-white hover:bg-gray-100 text-primary border border-primary font-bold py-3 px-8 rounded-lg transition-all duration-300 text-center">
                            <i class="fa fa-info-circle mr-2"></i>进QQ群
                        </a>
                    </div>
                </div>
                <div class="md:w-1/2 flex justify-center">
                    <div class="relative">
                        <div class="absolute -inset-4 bg-accent/20 rounded-full blur-3xl"></div>
                        <img src="3.png" alt="Minecraft联机助手展示" class="relative z-10 rounded-lg shadow-2xl hover-scale">
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 功能介绍 -->
    <section id="features" class="py-20 bg-white">
        <div class="container mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold text-dark mb-4">强大功能，简单操作</h2>
                <p class="text-gray-600 max-w-2xl mx-auto text-lg">我们的联机助手提供了丰富的功能，让Minecraft联机变得前所未有的简单</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <!-- 功能卡片1 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-server text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">一键联机</h3>
                    <p class="text-gray-600">无需复杂配置，一键即可创建属于你的Minecraft联机房间。</p>
                </div>
                
                <!-- 功能卡片2 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-users text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">联机大厅</h3>
                    <p class="text-gray-600">浏览公共房间列表，一键加入好友的游戏，或分享你的服务器给他人。</p>
                </div>
                
                <!-- 功能卡片3 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-comments text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">内置聊天</h3>
                    <p class="text-gray-600">集成实时聊天室，方便玩家之间沟通交流，无需切换其他通讯工具。</p>
                </div>
                
                <!-- 功能卡片4 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-shield text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">安全连接</h3>
                    <p class="text-gray-600">采用加密连接技术，保障你的服务器安全，防止未授权访问。</p>
                </div>
                
                <!-- 功能卡片5 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-history text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">历史记录</h3>
                    <p class="text-gray-600">自动保存你的服务器连接历史，快速重新加入曾经玩过的服务器。</p>
                </div>
                
                <!-- 功能卡片6 -->
                <div class="bg-light rounded-xl p-8 card-effect">
                    <div class="w-14 h-14 bg-primary/20 rounded-full flex items-center justify-center mb-6">
                        <i class="fa fa-cog text-primary text-2xl"></i>
                    </div>
                    <h3 class="text-xl font-bold text-dark mb-3">灵活设置</h3>
                    <p class="text-gray-600">丰富的自定义选项，满足不同玩家的需求，打造个性化的联机体验。</p>
                </div>
            </div>
        </div>
    </section>

    <!-- 软件截图 -->
    <section id="screenshots" class="py-20 bg-gray-50">
        <div class="container mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold text-dark mb-4">软件截图</h2>
                <p class="text-gray-600 max-w-2xl mx-auto text-lg">直观了解我们的联机助手界面和功能</p>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                <!-- 截图1: 联机大厅 -->
                <div class="card-effect bg-white p-4">
                    <h3 class="text-xl font-bold text-dark mb-4 text-center">联机大厅</h3>
                    <div class="relative overflow-hidden rounded-lg">
                        <img src="1.jpg" alt="联机大厅界面" class="w-full h-auto hover-scale">
                        <div class="absolute inset-0 bg-primary/5 hover:bg-primary/10 transition-all duration-300"></div>
                    </div>
                    <p class="mt-4 text-gray-600 text-center">浏览和加入各种公共服务器，或创建自己的私人服务器（图片截取自4.3.0版本）</p>
                </div>
                
                <!-- 截图2: 聊天室 -->
                <div class="card-effect bg-white p-4">
                    <h3 class="text-xl font-bold text-dark mb-4 text-center">实时聊天室</h3>
                    <div class="relative overflow-hidden rounded-lg">
                        <img src="2.jpg" alt="聊天室界面" class="w-full h-auto hover-scale">
                        <div class="absolute inset-0 bg-primary/5 hover:bg-primary/10 transition-all duration-300"></div>
                    </div>
                    <p class="mt-4 text-gray-600 text-center">与其他玩家实时交流，分享游戏心得和体验（图片截取自1.3.1版本）</p>
                </div>
            </div>
        </div>
    </section>

    <!-- 下载区域 -->
    <section id="download" class="py-20 bg-gradient-to-br from-dark to-primary text-white">
        <div class="container mx-auto px-4 text-center">
            <h2 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold mb-6 text-shadow">立即开始你的联机之旅</h2>
            <p class="max-w-2xl mx-auto text-lg mb-10 text-light/90">
                下载我们的Minecraft联机助手，与好友一起探索方块世界的无限可能
            </p>
            <p class="max-w-2xl mx-auto text-lg mb-10 text-light/90">
                SHA 256 哈希校验值（ LMFP联机软件.zip ）fc7a6578729f39c12b5aadd4ff3363d3bb4b374287eb6bd4685fa934ce05aabd
            </p>
            
            <a href="https://liuyvetong.lanzoub.com/ihsh43hxjs3e" 
               class="inline-flex items-center justify-center bg-white text-primary hover:bg-gray-100 font-bold py-4 px-10 rounded-lg shadow-2xl hover:shadow-3xl transition-all duration-300 text-lg hover-scale">
                <i class="fa fa-download mr-3 text-xl"></i>
                立即下载
            </a>
            
            <div class="mt-12 flex flex-wrap justify-center gap-8">
                <div class="flex flex-col items-center">
                    <i class="fa fa-windows text-4xl mb-2"></i>
                    <span>支持Windows</span>
                </div>
                <div class="flex flex-col items-center">
                    <i class="fa fa-check-circle text-4xl mb-2"></i>
                    <span>免费使用</span>
                </div>
                <div class="flex flex-col items-center">
                    <i class="fa fa-shield text-4xl mb-2"></i>
                    <span>安全无毒</span>
                </div>
                <div class="flex flex-col items-center">
                    <i class="fa fa-refresh text-4xl mb-2"></i>
                    <span>自动更新</span>
                </div>
            </div>
        </div>
    </section>

    <!-- 常见问题 -->
    <section id="faq" class="py-20 bg-white">
        <div class="container mx-auto px-4">
            <div class="text-center mb-16">
                <h2 class="text-[clamp(1.8rem,4vw,2.5rem)] font-bold text-dark mb-4">常见问题</h2>
                <p class="text-gray-600 max-w-2xl mx-auto text-lg">解答你可能遇到的问题</p>
            </div>
            
            <div class="max-w-3xl mx-auto">
                <div class="space-y-6">
                    <!-- FAQ 项目 -->
                    <div class="border border-gray-200 rounded-lg overflow-hidden">
                        <button class="faq-toggle w-full flex justify-between items-center p-6 bg-gray-50 hover:bg-gray-100 transition-colors text-left font-medium" data-target="faq1">
                            <span>如何使用本软件创建Minecraft联机房间？</span>
                            <i class="fa fa-chevron-down text-gray-400 transition-transform duration-300"></i>
                        </button>
                        <div id="faq1" class="faq-content hidden p-6 bg-white border-t border-gray-200">
                            <p class="text-gray-600">
                                打开软件后，点击"创建房间"按钮即可。系统会自动完成内网穿透配置和启动过程，无需手动设置端口映射。
                            </p>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg overflow-hidden">
                        <button class="faq-toggle w-full flex justify-between items-center p-6 bg-gray-50 hover:bg-gray-100 transition-colors text-left font-medium" data-target="faq2">
                            <span>聊天室功能如何使用？</span>
                            <i class="fa fa-chevron-down text-gray-400 transition-transform duration-300"></i>
                        </button>
                        <div id="faq2" class="faq-content hidden p-6 bg-white border-t border-gray-200">
                            <p class="text-gray-600">
                                注册登录即可。
                            </p>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg overflow-hidden">
                        <button class="faq-toggle w-full flex justify-between items-center p-6 bg-gray-50 hover:bg-gray-100 transition-colors text-left font-medium" data-target="faq3">
                            <span>软件支持哪些Minecraft版本？</span>
                            <i class="fa fa-chevron-down text-gray-400 transition-transform duration-300"></i>
                        </button>
                        <div id="faq3" class="faq-content hidden p-6 bg-white border-t border-gray-200">
                            <p class="text-gray-600">
                                所有！！！（骄傲）
                            </p>
                        </div>
                    </div>
                    
                    <div class="border border-gray-200 rounded-lg overflow-hidden">
                        <button class="faq-toggle w-full flex justify-between items-center p-6 bg-gray-50 hover:bg-gray-100 transition-colors text-left font-medium" data-target="faq4">
                            <span>使用本软件需要付费吗？</span>
                            <i class="fa fa-chevron-down text-gray-400 transition-transform duration-300"></i>
                        </button>
                        <div id="faq4" class="faq-content hidden p-6 bg-white border-t border-gray-200">
                            <p class="text-gray-600">
                                本软件完全免费（即使未来有增值服务，也不会影响免费版使用），如果您是购买的本软件，说明你被骗了！！！
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- 页脚 -->
    <footer class="bg-dark text-white py-12">
        <div class="container mx-auto px-4">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div class="mb-6 md:mb-0">
                    <div class="flex items-center space-x-2 mb-4">
                        <i class="fa fa-cube text-accent text-2xl"></i>
                        <h2 class="text-xl font-bold">LMFP</h2>
                    </div>
                    <p class="text-gray-400 max-w-md">
                        本网站总访问次数：<?php echo $totalVisits; ?> 次       --- 今日访问次数：<?php echo $todayVisits; ?> 次
                    </p>
                </div>
                
                <div class="flex flex-col items-center md:items-end">
                    <div class="flex space-x-4 mb-4">
                        <!--<a href="#" class="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors">
                            <i class="fa fa-weixin"></i>
                        </a>-->
                        <a href="https://qm.qq.com/cgi-bin/qm/qr?k=-LlckSeA5LtOHyuUETMDjd91xAOO7v-2&jump_from=webapi&authKey=9AuAKTEp9ED2bpd679Pb+5EhwkgJjsFX8UKDt1UM3CZ2AOUFVsYMO+XuPaiqkgHX" class="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors">
                            <i class="fa fa-qq"></i>
                        </a>
                        <a href="https://github.com/lyt20" class="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center hover:bg-primary transition-colors">
                            <i class="fa fa-github"></i>
                        </a>
                    </div>
                    <p class="text-gray-400 text-sm">
                        &copy; 2025 Lyt_IT 版权所有
                    </p>
                </div>
            </div>
        </div>
    </footer>

    <script>
        // 导航栏滚动效果
        window.addEventListener('scroll', function() {
            const navbar = document.getElementById('navbar');
            if (window.scrollY > 50) {
                navbar.classList.add('py-2', 'shadow-lg');
                navbar.classList.remove('py-3', 'shadow-md');
            } else {
                navbar.classList.add('py-3', 'shadow-md');
                navbar.classList.remove('py-2', 'shadow-lg');
            }
        });
        
        // 移动端菜单切换
        document.getElementById('menuBtn').addEventListener('click', function() {
            const mobileMenu = document.getElementById('mobileMenu');
            mobileMenu.classList.toggle('hidden');
        });
        
        // FAQ 折叠功能
        document.querySelectorAll('.faq-toggle').forEach(toggle => {
            toggle.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const content = document.getElementById(targetId);
                const icon = this.querySelector('i');
                
                // 切换当前FAQ的显示状态
                content.classList.toggle('hidden');
                icon.classList.toggle('rotate-180');
                
                // 关闭其他打开的FAQ
                document.querySelectorAll('.faq-content').forEach(item => {
                    if (item.id !== targetId && !item.classList.contains('hidden')) {
                        item.classList.add('hidden');
                        document.querySelector(`[data-target="${item.id}"] i`).classList.remove('rotate-180');
                    }
                });
            });
        });
        
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    window.scrollTo({
                        top: targetElement.offsetTop - 80,
                        behavior: 'smooth'
                    });
                    
                    // 关闭移动端菜单
                    document.getElementById('mobileMenu').classList.add('hidden');
                }
            });
        });
    </script>
</body>
</html>