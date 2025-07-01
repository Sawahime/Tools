import socket
import threading
import time
import json
from datetime import datetime
from tkinter import ttk, messagebox, scrolledtext
import tkinter as tk
from io import StringIO
import logging


class TCPServerTool:
    """TCP服务器测试工具"""

    def __init__(self, root):
        self.root = root
        self.root.title("TCP服务器测试工具")
        self.root.geometry("800x600")

        # 服务器状态
        self.servers = {}  # 存储多个服务器实例
        self.server_id_counter = 1

        # 设置日志
        self.log_stream = StringIO()
        self.setup_logging()

        # 创建UI
        self.create_widgets()

        # 初始化界面状态
        self.on_server_type_change()

        # 定时更新日志显示
        self.update_log_display()

    def on_server_type_change(self):
        """服务器类型改变时的处理"""
        # 隐藏所有配置框架
        self.delay_frame.pack_forget()
        self.data_frame.pack_forget()

        # 根据选择的类型显示对应配置
        if self.server_type.get() == "delay":
            self.delay_frame.pack(side=tk.LEFT)
        elif self.server_type.get() == "data":
            self.data_frame.pack(side=tk.LEFT)

    def setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(self.log_stream)]
        )
        self.logger = logging.getLogger(__name__)

    def create_widgets(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 服务器配置区域
        config_frame = ttk.LabelFrame(main_frame, text="服务器配置", padding="10")
        config_frame.pack(fill=tk.X, pady=5)

        # 第一行：基本配置
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="监听IP:").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(row1, width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "0.0.0.0")

        ttk.Label(row1, text="端口:").pack(side=tk.LEFT, padx=(20, 0))
        self.port_entry = ttk.Entry(row1, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "8888")

        # 第二行：服务器类型
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="服务器类型:").pack(side=tk.LEFT)
        self.server_type = tk.StringVar(value="delay")

        ttk.Radiobutton(row2, text="延迟测试", variable=self.server_type,
                        value="delay", command=self.on_server_type_change).pack(side=tk.LEFT, padx=(5, 15))
        ttk.Radiobutton(row2, text="数据传输", variable=self.server_type,
                        value="data", command=self.on_server_type_change).pack(side=tk.LEFT)

        # 第三行：特殊配置
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=2)

        # 延迟测试配置
        self.delay_frame = ttk.Frame(row3)
        ttk.Label(self.delay_frame, text="延迟(秒):").pack(side=tk.LEFT)
        self.delay_entry = ttk.Entry(self.delay_frame, width=8)
        self.delay_entry.pack(side=tk.LEFT, padx=5)
        self.delay_entry.insert(0, "1")

        # 数据传输配置
        self.data_frame = ttk.Frame(row3)
        ttk.Label(self.data_frame, text="数据大小(KB):").pack(side=tk.LEFT)
        self.data_size_entry = ttk.Entry(self.data_frame, width=8)
        self.data_size_entry.pack(side=tk.LEFT, padx=5)
        self.data_size_entry.insert(0, "1024")

        # TCP高级配置
        row4 = ttk.LabelFrame(config_frame, text="TCP高级配置", padding="5")
        row4.pack(fill=tk.X, pady=5)

        # 第一行高级配置
        tcp_row1 = ttk.Frame(row4)
        tcp_row1.pack(fill=tk.X, pady=2)

        ttk.Label(tcp_row1, text="并发连接数:").pack(side=tk.LEFT)
        self.max_connections_entry = ttk.Entry(tcp_row1, width=8)
        self.max_connections_entry.pack(side=tk.LEFT, padx=5)
        self.max_connections_entry.insert(0, "10")

        ttk.Label(tcp_row1, text="缓冲区大小(KB):").pack(side=tk.LEFT, padx=(20, 0))
        self.buffer_size_entry = ttk.Entry(tcp_row1, width=8)
        self.buffer_size_entry.pack(side=tk.LEFT, padx=5)
        self.buffer_size_entry.insert(0, "4")

        # 第二行高级配置
        tcp_row2 = ttk.Frame(row4)
        tcp_row2.pack(fill=tk.X, pady=2)

        ttk.Label(tcp_row2, text="发送间隔(ms):").pack(side=tk.LEFT)
        self.send_interval_entry = ttk.Entry(tcp_row2, width=8)
        self.send_interval_entry.pack(side=tk.LEFT, padx=5)
        self.send_interval_entry.insert(0, "0")

        self.keepalive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tcp_row2, text="启用TCP Keep-Alive",
                        variable=self.keepalive_var).pack(side=tk.LEFT, padx=(20, 0))

        # 操作按钮
        button_frame = ttk.Frame(config_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="启动服务器", command=self.start_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="停止所有服务器", command=self.stop_all_servers).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)

        # 服务器状态显示
        status_frame = ttk.LabelFrame(main_frame, text="运行中的服务器", padding="10")
        status_frame.pack(fill=tk.X, pady=5)

        # 服务器列表
        columns = ('ID', '类型', '地址', '状态', '连接数')
        self.server_tree = ttk.Treeview(status_frame, columns=columns, show='headings', height=6)

        for col in columns:
            self.server_tree.heading(col, text=col)
            self.server_tree.column(col, width=100, anchor='center')

        scrollbar_server = ttk.Scrollbar(status_frame, orient=tk.VERTICAL, command=self.server_tree.yview)
        self.server_tree.configure(yscrollcommand=scrollbar_server.set)

        self.server_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_server.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击停止服务器
        self.server_tree.bind('<Double-1>', self.stop_selected_server)

        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="服务器日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def start_server(self):
        """启动TCP服务器"""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            server_type = self.server_type.get()

            # 检查端口是否已被占用
            for server_info in self.servers.values():
                if server_info['port'] == port and server_info['running']:
                    messagebox.showerror("错误", f"端口 {port} 已被占用")
                    return

            # 创建服务器实例
            server_id = self.server_id_counter
            self.server_id_counter += 1

            server_info = {
                'id': server_id,
                'type': server_type,
                'ip': ip,
                'port': port,
                'socket': None,
                'thread': None,
                'running': False,
                'connections': 0
            }

            # 启动服务器线程
            thread = threading.Thread(target=self.run_server, args=(server_info,), daemon=True)
            server_info['thread'] = thread

            self.servers[server_id] = server_info
            thread.start()

        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
        except Exception as e:
            messagebox.showerror("错误", f"启动服务器失败: {str(e)}")

    def run_server(self, server_info):
        """运行TCP服务器"""
        try:
            # 获取并发连接数配置
            max_connections = int(self.max_connections_entry.get() or "10")

            # 创建socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((server_info['ip'], server_info['port']))
            server_socket.listen(max_connections)

            server_info['socket'] = server_socket
            server_info['running'] = True

            self.logger.info(
                f"服务器 {server_info['id']} ({server_info['type']}) 启动成功: {server_info['ip']}:{server_info['port']}")
            self.update_server_list()

            while server_info['running']:
                try:
                    server_socket.settimeout(1.0)  # 设置超时，便于检查停止信号
                    client_socket, client_address = server_socket.accept()

                    server_info['connections'] += 1
                    self.update_server_list()

                    # 处理客户端连接
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(server_info, client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except OSError:
                    break

        except Exception as e:
            self.logger.error(f"服务器 {server_info['id']} 运行错误: {str(e)}")
        finally:
            if server_info['socket']:
                server_info['socket'].close()
            server_info['running'] = False
            self.update_server_list()
            self.logger.info(f"服务器 {server_info['id']} 已停止")

    def handle_client(self, server_info, client_socket, client_address):
        """处理客户端连接"""
        try:
            self.logger.info(f"服务器 {server_info['id']} 接受连接: {client_address}")

            if server_info['type'] == 'delay':
                self.handle_delay_client(server_info, client_socket, client_address)
            elif server_info['type'] == 'data':
                self.handle_data_client(server_info, client_socket, client_address)

        except Exception as e:
            self.logger.error(f"处理客户端 {client_address} 时发生错误: {str(e)}")
        finally:
            try:
                client_socket.close()
            except:
                pass
            server_info['connections'] -= 1
            self.update_server_list()
            self.logger.info(f"客户端 {client_address} 断开连接")

    def handle_delay_client(self, server_info, client_socket, client_address):
        """处理延迟测试服务器客户端"""
        try:
            delay = float(self.delay_entry.get() or "1")

            # 接收数据
            data = client_socket.recv(1024)
            if data:
                self.logger.info(f"延迟服务器 {server_info['id']} 收到数据，将延迟 {delay} 秒后响应")

                # 延迟指定时间
                time.sleep(delay)

                # 发送响应
                response = f"Delayed response after {delay}s from server {server_info['id']}: {data.decode('utf-8', errors='ignore')}"
                client_socket.send(response.encode('utf-8'))

        except Exception as e:
            self.logger.error(f"延迟服务器处理数据时出错: {str(e)}")

    def handle_data_client(self, server_info, client_socket, client_address):
        """处理数据传输测试服务器客户端"""
        try:
            # 获取TCP配置参数
            buffer_size_kb = int(self.buffer_size_entry.get() or "4")
            send_interval_ms = int(self.send_interval_entry.get() or "0")
            keepalive = self.keepalive_var.get()

            # 设置TCP Keep-Alive
            if keepalive:
                client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            # 接收客户端请求
            request = client_socket.recv(1024).decode('utf-8', errors='ignore')

            if request.startswith("DATA_REQUEST:"):
                # 解析客户端请求的数据大小
                try:
                    requested_size_kb = int(request.split(":")[1])
                except:
                    requested_size_kb = int(self.data_size_entry.get() or "1024")
            else:
                # 使用默认配置的数据大小
                requested_size_kb = int(self.data_size_entry.get() or "1024")

            data_size = requested_size_kb * 1024
            self.logger.info(f"数据服务器 {server_info['id']} 准备发送 {requested_size_kb}KB 数据给 {client_address}")
            self.logger.info(f"TCP配置: 缓冲区={buffer_size_kb}KB, 发送间隔={send_interval_ms}ms, Keep-Alive={keepalive}")

            # 生成测试数据
            test_data = b'A' * data_size

            # 使用配置的缓冲区大小
            chunk_size = buffer_size_kb * 1024
            sent = 0

            while sent < data_size:
                chunk_end = min(sent + chunk_size, data_size)
                chunk = test_data[sent:chunk_end]

                try:
                    client_socket.send(chunk)
                    sent += len(chunk)

                    # 发送间隔控制
                    if send_interval_ms > 0:
                        time.sleep(send_interval_ms / 1000.0)

                    # 计算并显示进度
                    progress = (sent / data_size) * 100
                    current_chunk = sent // chunk_size + 1

                    if current_chunk % 5 == 0 or sent >= data_size:  # 每5个块或完成时显示进度
                        self.logger.info(
                            f"数据服务器 {server_info['id']} 传输进度: {progress:.1f}% ({sent/1024:.1f}KB/{requested_size_kb}KB)")

                except Exception as e:
                    self.logger.error(f"发送数据时出错: {str(e)}")
                    break

            if sent >= data_size:
                self.logger.info(f"数据服务器 {server_info['id']} 成功发送 {requested_size_kb}KB 数据给 {client_address}")
            else:
                self.logger.warning(f"数据服务器 {server_info['id']} 传输不完整: 发送 {sent/1024:.1f}KB/{requested_size_kb}KB")

        except Exception as e:
            self.logger.error(f"数据服务器处理请求时出错: {str(e)}")

    def update_server_list(self):
        """更新服务器列表显示"""
        def update_ui():
            # 清空现有项目
            for item in self.server_tree.get_children():
                self.server_tree.delete(item)

            # 添加当前服务器
            for server_info in self.servers.values():
                status = "运行中" if server_info['running'] else "已停止"
                address = f"{server_info['ip']}:{server_info['port']}"

                self.server_tree.insert('', 'end', values=(
                    server_info['id'],
                    server_info['type'],
                    address,
                    status,
                    server_info['connections']
                ))

        self.root.after(0, update_ui)

    def stop_selected_server(self, event):
        """停止选中的服务器"""
        selection = self.server_tree.selection()
        if selection:
            item = self.server_tree.item(selection[0])
            server_id = int(item['values'][0])
            self.stop_server(server_id)

    def stop_server(self, server_id):
        """停止指定服务器"""
        if server_id in self.servers:
            server_info = self.servers[server_id]
            server_info['running'] = False
            if server_info['socket']:
                server_info['socket'].close()
            self.logger.info(f"正在停止服务器 {server_id}")

    def stop_all_servers(self):
        """停止所有服务器"""
        for server_id in list(self.servers.keys()):
            self.stop_server(server_id)
        self.logger.info("正在停止所有服务器")

    def clear_log(self):
        """清除日志"""
        self.log_stream.truncate(0)
        self.log_stream.seek(0)
        self.log_text.delete(1.0, tk.END)

    def update_log_display(self):
        """更新日志显示"""
        log_content = self.log_stream.getvalue()
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, log_content)
        self.log_text.see(tk.END)
        self.root.after(500, self.update_log_display)


def main():
    root = tk.Tk()
    app = TCPServerTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
