import socket
import time
import struct

class MulticastServer:
    def __init__(self, motd="§6§l双击进入LMFP联机房间（请保持LMFP运行）", port=25565, 
                 multicast_group="224.0.2.60", port_num=4445):
        """
        初始化多播服务器
        :param motd: 服务器描述信息
        :param port: 服务器端口
        :param multicast_group: 多播组地址
        :param port_num: 多播端口
        """
        self.motd = motd
        self.port = port
        self.multicast_group = multicast_group
        self.port_num = port_num
        self.sock = None
        
    def create_message(self):
        """创建符合格式的服务端信息字符串"""
        return f"[MOTD]{self.motd}[/MOTD][AD]{self.port}[/AD]"
    
    def start(self):
        """启动多播服务器"""
        try:
            # 创建UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            
            # 设置TTL（生存时间），让数据包可以跨越路由器
            ttl = struct.pack('b', 1)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            
            print(f"启动多播服务器...")
            print(f"多播组: {self.multicast_group}:{self.port_num}")
            print(f"服务器信息: MOTD='{self.motd}', 端口={self.port}")
            print("按 Ctrl+C 停止服务器\n")
            
            while True:
                # 创建消息
                message = self.create_message()
                
                # 发送多播消息
                self.sock.sendto(message.encode('utf-8'), 
                                (self.multicast_group, self.port_num))
                
                print(f"发送: {message}")
                
                # 等待1.5秒
                time.sleep(1.5)
                
        except KeyboardInterrupt:
            print("\n服务器已停止")
        except Exception as e:
            print(f"发生错误: {e}")
        finally:
            if self.sock:
                self.sock.close()

if __name__ == "__main__":
    # 配置服务器参数
    server = MulticastServer(
        motd="§6§l双击进入LMFP联机房间（请保持LMFP运行）",  # 服务器描述
        port=25565,  # 服务器端口
        multicast_group="224.0.2.60",  # 多播组地址
        port_num=4445  # 多播端口
    )
    
    # 启动服务器
    server.start()