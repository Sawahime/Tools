import os
import threading
from io import StringIO
import logging
import requests
import socket
import time
from tkinter import ttk, messagebox, scrolledtext
import tkinter as tk


class HTTPTestModule:
    """HTTP测试模块"""

    def __init__(self, parent_frame, logger, log_callback=None):
        self.parent_frame = parent_frame
        self.logger = logger
        self.log_callback = log_callback
        self.create_widgets()

    def create_widgets(self):
        """创建HTTP测试模块的UI组件"""
        # IP输入部分
        ip_frame = ttk.LabelFrame(self.parent_frame, text="HTTP测试配置", padding="10")
        ip_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ip_frame, text="IP地址:").grid(row=0, column=0, sticky=tk.W)
        self.ip_entry = ttk.Entry(ip_frame, width=40)
        self.ip_entry.grid(row=0, column=1, padx=5)
        self.ip_entry.insert(0, "192.168.2.43")  # 默认IP

        # 协议选择
        self.protocol_var = tk.StringVar(value="http")
        ttk.Label(ip_frame, text="协议:").grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(ip_frame, text="HTTP", variable=self.protocol_var,
                        value="http").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(ip_frame, text="HTTPS", variable=self.protocol_var,
                        value="https").grid(row=1, column=2, sticky=tk.W)

        # 端口输入
        ttk.Label(ip_frame, text="端口:").grid(row=2, column=0, sticky=tk.W)
        self.port_entry = ttk.Entry(ip_frame, width=10)
        self.port_entry.grid(row=2, column=1, sticky=tk.W, padx=5)
        self.port_entry.insert(0, "80")

        # 操作按钮
        button_frame = ttk.Frame(self.parent_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.access_button = ttk.Button(button_frame, text="开始访问", command=self.start_access_thread)
        self.access_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="清除HTML", command=self.clear_html).pack(side=tk.LEFT, padx=5)

        # HTML内容显示区域
        html_frame = ttk.LabelFrame(self.parent_frame, text="HTML内容", padding="10")
        html_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建HTML内容显示区域（带行号）
        html_container = ttk.Frame(html_frame)
        html_container.pack(fill=tk.BOTH, expand=True)

        # 行号显示区域
        self.line_numbers = tk.Text(
            html_container,
            width=8,  # 行号区域宽度
            padx=3,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            font=('Consolas', 10),
            bg='#f0f0f0',
            fg='#666666',
            cursor='arrow'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # HTML内容显示区域
        self.html_text = scrolledtext.ScrolledText(
            html_container,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.html_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 绑定滚动事件
        self.setup_scroll_binding()

    def setup_scroll_binding(self):
        """设置滚动事件绑定"""
        # 绑定滚动条事件
        scrollbar = self.html_text.vbar
        scrollbar.config(command=self.on_scrollbar_move)

        # 绑定鼠标滚轮事件
        self.html_text.bind('<MouseWheel>', self.on_html_scroll)
        self.html_text.bind('<Button-4>', self.on_html_scroll)
        self.html_text.bind('<Button-5>', self.on_html_scroll)

        # 绑定键盘事件
        self.html_text.bind('<Up>', self.on_html_scroll)
        self.html_text.bind('<Down>', self.on_html_scroll)
        self.html_text.bind('<Prior>', self.on_html_scroll)
        self.html_text.bind('<Next>', self.on_html_scroll)
        self.html_text.bind('<Home>', self.on_html_scroll)
        self.html_text.bind('<End>', self.on_html_scroll)

        # 绑定文本变化事件
        self.html_text.bind('<Key>', self.on_html_change)
        self.html_text.bind('<Button-1>', self.on_html_change)

    def start_access_thread(self):
        """启动一个新线程来执行访问操作"""
        thread = threading.Thread(target=self.access_website, daemon=True)
        thread.start()

    def access_website(self):
        """模拟浏览器访问指定IP"""
        # 清空之前的HTML内容
        self.clear_html()

        ip = self.ip_entry.get().strip()
        protocol = self.protocol_var.get()
        port = self.port_entry.get().strip()

        if not ip:
            messagebox.showerror("错误", "请输入有效的IP地址")
            return

        try:
            # 构建URL
            url = f"{protocol}://{ip}"
            if port and port != "80":
                url += f":{port}"

            self.logger.info(f"开始访问: {url}")

            # 模拟浏览器请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            try:
                # 禁用详细日志以不显示传输过程
                logging.getLogger("urllib3").setLevel(logging.WARNING)

                response = requests.get(url, headers=headers, timeout=10)
                self.logger.info(f"访问成功: status_code={response.status_code}")

                # 获取实际接收的内容大小
                content_size = len(response.content)
                content_size_mb = content_size / (1024 * 1024)
                self.logger.info(f"文件大小: {content_size_mb:.2f} MB")

                # 显示HTML内容
                self.html_text.insert(tk.END, response.text)
                # 更新行号
                self.update_line_numbers()

            except requests.exceptions.RequestException as e:
                self.logger.error(f"访问失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}", exc_info=True)

    def clear_html(self):
        """清除HTML内容"""
        self.html_text.delete(1.0, tk.END)
        self.update_line_numbers()

    def update_line_numbers(self):
        """更新行号显示"""
        # 获取HTML文本的行数
        line_count = int(self.html_text.index('end-1c').split('.')[0])

        # 生成行号文本
        line_numbers_text = '\n'.join(str(i) for i in range(1, line_count))

        # 更新行号显示
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state='disabled')

    def on_scrollbar_move(self, *args):
        """处理滚动条移动事件"""
        # 先执行原始的滚动操作
        self.html_text.yview(*args)
        # 立即同步行号滚动
        self.sync_line_numbers()

    def on_html_scroll(self, event):
        """处理HTML文本滚动事件，同步行号滚动"""
        # 使用after方法确保在滚动完成后立即同步
        if self.log_callback:
            self.log_callback(1, self.sync_line_numbers)

    def on_html_change(self, event=None):
        """处理HTML文本变化事件，延迟更新行号"""
        # 延迟更新行号，避免频繁更新
        if self.log_callback:
            self.log_callback('idle', self.update_line_numbers)
            self.log_callback('idle', self.sync_line_numbers)

    def sync_line_numbers(self):
        """同步行号滚动位置"""
        try:
            # 获取HTML文本的当前滚动位置
            top, bottom = self.html_text.yview()
            # 同步行号滚动
            self.line_numbers.yview_moveto(top)
        except tk.TclError:
            # 忽略可能的Tcl错误
            pass


class TCPTestModule:
    """TCP测试模块"""

    def __init__(self, parent_frame, logger):
        self.parent_frame = parent_frame
        self.logger = logger
        self.is_scanning = False
        self.scan_thread = None
        self.create_widgets()

    def create_widgets(self):
        """创建TCP测试模块的UI组件"""
        # TCP测试配置
        config_frame = ttk.LabelFrame(self.parent_frame, text="TCP测试配置", padding="10")
        config_frame.pack(fill=tk.X, pady=5)

        # 第一行：IP地址
        row1 = ttk.Frame(config_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="目标IP:").pack(side=tk.LEFT)
        self.ip_entry = ttk.Entry(row1, width=20)
        self.ip_entry.pack(side=tk.LEFT, padx=(5, 20))
        self.ip_entry.insert(0, "192.168.2.43")  # 默认IP

        # 超时设置
        ttk.Label(row1, text="超时(秒):").pack(side=tk.LEFT)
        self.timeout_entry = ttk.Entry(row1, width=8)
        self.timeout_entry.pack(side=tk.LEFT, padx=5)
        self.timeout_entry.insert(0, "3")

        # 第二行：测试模式选择
        row2 = ttk.Frame(config_frame)
        row2.pack(fill=tk.X, pady=5)

        self.test_mode = tk.StringVar(value="single")
        ttk.Radiobutton(row2, text="单端口测试", variable=self.test_mode,
                        value="single", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(row2, text="端口扫描", variable=self.test_mode,
                        value="scan", command=self.on_mode_change).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(row2, text="数据传输测试", variable=self.test_mode,
                        value="data_test", command=self.on_mode_change).pack(side=tk.LEFT)

        # 第三行：端口配置
        row3 = ttk.Frame(config_frame)
        row3.pack(fill=tk.X, pady=2)

        # 单端口测试配置
        self.single_frame = ttk.Frame(row3)
        self.single_frame.pack(side=tk.LEFT)
        ttk.Label(self.single_frame, text="端口:").pack(side=tk.LEFT)
        self.port_entry = ttk.Entry(self.single_frame, width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "8888")

        # 端口扫描配置
        self.scan_frame = ttk.Frame(row3)
        ttk.Label(self.scan_frame, text="起始端口:").pack(side=tk.LEFT)
        self.start_port_entry = ttk.Entry(self.scan_frame, width=8)
        self.start_port_entry.pack(side=tk.LEFT, padx=5)
        self.start_port_entry.insert(0, "1")

        ttk.Label(self.scan_frame, text="结束端口:").pack(side=tk.LEFT, padx=(10, 0))
        self.end_port_entry = ttk.Entry(self.scan_frame, width=8)
        self.end_port_entry.pack(side=tk.LEFT, padx=5)
        self.end_port_entry.insert(0, "1000")

        # 数据传输测试配置
        self.data_test_frame = ttk.Frame(row3)
        ttk.Label(self.data_test_frame, text="请求数据大小(KB):").pack(side=tk.LEFT)
        self.request_size_entry = ttk.Entry(self.data_test_frame, width=8)
        self.request_size_entry.pack(side=tk.LEFT, padx=5)
        self.request_size_entry.insert(0, "100")

        # 操作按钮
        button_frame = ttk.Frame(self.parent_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.test_button = ttk.Button(button_frame, text="开始测试", command=self.start_test_thread)
        self.test_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止扫描", command=self.stop_scan, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="清除结果", command=self.clear_results).pack(side=tk.LEFT, padx=5)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.parent_frame, text="测试结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建结果显示表格
        columns = ('端口', '状态', '响应时间(ms)', '服务')
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=15)

        # 设置列标题和宽度
        self.result_tree.heading('端口', text='端口')
        self.result_tree.heading('状态', text='状态')
        self.result_tree.heading('响应时间(ms)', text='响应时间(ms)')
        self.result_tree.heading('服务', text='服务')

        self.result_tree.column('端口', width=80, anchor='center')
        self.result_tree.column('状态', width=80, anchor='center')
        self.result_tree.column('响应时间(ms)', width=120, anchor='center')
        self.result_tree.column('服务', width=150, anchor='w')

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)

        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置表格样式
        self.result_tree.tag_configure('open', background='#d4edda', foreground='#155724')  # 绿色
        self.result_tree.tag_configure('closed', background='#f8d7da', foreground='#721c24')  # 红色
        self.result_tree.tag_configure('timeout', background='#fff3cd', foreground='#856404')  # 黄色
        self.result_tree.tag_configure('error', background='#f5c6cb', foreground='#721c24')  # 粉红色

        # 数据传输进度显示区域
        self.progress_frame = ttk.LabelFrame(self.parent_frame, text="数据传输进度", padding="10")

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)

        # 进度信息
        self.progress_info = ttk.Label(self.progress_frame, text="等待开始传输...")
        self.progress_info.pack(pady=5)

        # 传输统计
        stats_frame = ttk.Frame(self.progress_frame)
        stats_frame.pack(fill=tk.X, pady=5)

        ttk.Label(stats_frame, text="已接收:").pack(side=tk.LEFT)
        self.received_label = ttk.Label(stats_frame, text="0 KB")
        self.received_label.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(stats_frame, text="传输速度:").pack(side=tk.LEFT)
        self.speed_label = ttk.Label(stats_frame, text="0 KB/s")
        self.speed_label.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(stats_frame, text="剩余时间:").pack(side=tk.LEFT)
        self.eta_label = ttk.Label(stats_frame, text="--")
        self.eta_label.pack(side=tk.LEFT, padx=5)

        # TCP客户端高级配置
        self.tcp_config_frame = ttk.LabelFrame(self.parent_frame, text="TCP客户端配置", padding="10")

        # 第一行配置
        tcp_row1 = ttk.Frame(self.tcp_config_frame)
        tcp_row1.pack(fill=tk.X, pady=2)

        ttk.Label(tcp_row1, text="并发连接数:").pack(side=tk.LEFT)
        self.client_connections_entry = ttk.Entry(tcp_row1, width=8)
        self.client_connections_entry.pack(side=tk.LEFT, padx=5)
        self.client_connections_entry.insert(0, "1")

        ttk.Label(tcp_row1, text="接收缓冲区(KB):").pack(side=tk.LEFT, padx=(20, 0))
        self.recv_buffer_entry = ttk.Entry(tcp_row1, width=8)
        self.recv_buffer_entry.pack(side=tk.LEFT, padx=5)
        self.recv_buffer_entry.insert(0, "4")

        # 第二行配置
        tcp_row2 = ttk.Frame(self.tcp_config_frame)
        tcp_row2.pack(fill=tk.X, pady=2)

        self.nodelay_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tcp_row2, text="禁用Nagle算法(TCP_NODELAY)",
                        variable=self.nodelay_var).pack(side=tk.LEFT)

        self.keepalive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(tcp_row2, text="启用Keep-Alive",
                        variable=self.keepalive_var).pack(side=tk.LEFT, padx=(20, 0))

        # 初始化界面状态
        self.on_mode_change()

    def on_mode_change(self):
        """测试模式改变时的处理"""
        # 隐藏所有配置框架
        self.single_frame.pack_forget()
        self.scan_frame.pack_forget()
        self.data_test_frame.pack_forget()
        self.progress_frame.pack_forget()
        self.tcp_config_frame.pack_forget()

        # 显示对应的配置框架
        if self.test_mode.get() == "single":
            self.single_frame.pack(side=tk.LEFT)
        elif self.test_mode.get() == "scan":
            self.scan_frame.pack(side=tk.LEFT)
        elif self.test_mode.get() == "data_test":
            self.data_test_frame.pack(side=tk.LEFT)
            self.progress_frame.pack(fill=tk.X, pady=5)
            self.tcp_config_frame.pack(fill=tk.X, pady=5)

    def start_test_thread(self):
        """启动测试线程"""
        if self.is_scanning:
            return

        self.scan_thread = threading.Thread(target=self.run_test, daemon=True)
        self.scan_thread.start()

    def run_test(self):
        """执行TCP测试"""
        try:
            ip = self.ip_entry.get().strip()
            if not ip:
                messagebox.showerror("错误", "请输入有效的IP地址")
                return

            timeout = float(self.timeout_entry.get().strip() or "3")

            if self.test_mode.get() == "single":
                self.run_single_port_test(ip, timeout)
            elif self.test_mode.get() == "scan":
                self.run_port_scan(ip, timeout)
            elif self.test_mode.get() == "data_test":
                self.run_data_transfer_test(ip, timeout)

        except ValueError:
            messagebox.showerror("错误", "超时时间必须是数字")
        except Exception as e:
            self.logger.error(f"TCP测试发生错误: {str(e)}")

    def run_single_port_test(self, ip, timeout):
        """单端口测试"""
        try:
            port = int(self.port_entry.get().strip())
            self.logger.info(f"开始TCP连接测试: {ip}:{port}")

            self.is_scanning = True
            self.update_button_state()

            result = self.test_tcp_connection(ip, port, timeout)
            self.add_result_to_tree(port, result['status'], result['response_time'], result['service'])

            self.logger.info(f"TCP测试完成: {ip}:{port} - {result['status']}")

        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
        finally:
            self.is_scanning = False
            self.update_button_state()

    def run_port_scan(self, ip, timeout):
        """端口扫描"""
        try:
            start_port = int(self.start_port_entry.get().strip())
            end_port = int(self.end_port_entry.get().strip())

            if start_port > end_port:
                messagebox.showerror("错误", "起始端口不能大于结束端口")
                return

            if end_port - start_port > 10000:
                if not messagebox.askyesno("确认", f"将扫描 {end_port - start_port + 1} 个端口，可能需要较长时间，是否继续？"):
                    return

            self.logger.info(f"开始端口扫描: {ip}:{start_port}-{end_port}")

            self.is_scanning = True
            self.update_button_state()

            open_ports = 0
            for port in range(start_port, end_port + 1):
                if not self.is_scanning:  # 检查是否被停止
                    break

                result = self.test_tcp_connection(ip, port, timeout)
                if result['status'] == '开放':
                    self.add_result_to_tree(port, result['status'], result['response_time'], result['service'])
                    open_ports += 1

                # 更新进度（每10个端口记录一次）
                if port % 10 == 0:
                    progress = ((port - start_port + 1) / (end_port - start_port + 1)) * 100
                    self.logger.info(f"扫描进度: {progress:.1f}% (当前端口: {port})")

            self.logger.info(f"端口扫描完成: 发现 {open_ports} 个开放端口")

        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
        finally:
            self.is_scanning = False
            self.update_button_state()

    def run_data_transfer_test(self, ip, timeout):
        """数据传输测试"""
        try:
            port = int(self.port_entry.get().strip())
            request_size = int(self.request_size_entry.get().strip())

            self.logger.info(f"开始数据传输测试: {ip}:{port}, 请求 {request_size}KB 数据")

            self.is_scanning = True
            self.update_button_state()

            # 重置进度显示
            self.reset_progress()

            # 执行数据传输测试
            self.perform_data_transfer(ip, port, timeout, request_size)

        except ValueError:
            messagebox.showerror("错误", "端口和数据大小必须是数字")
        finally:
            self.is_scanning = False
            self.update_button_state()

    def perform_data_transfer(self, ip, port, timeout, request_size_kb):
        """执行数据传输"""
        # 获取TCP配置
        client_connections = int(self.client_connections_entry.get() or "1")
        recv_buffer_kb = int(self.recv_buffer_entry.get() or "4")
        nodelay = self.nodelay_var.get()
        keepalive = self.keepalive_var.get()

        self.logger.info(
            f"TCP客户端配置: 并发连接={client_connections}, 接收缓冲区={recv_buffer_kb}KB, TCP_NODELAY={nodelay}, Keep-Alive={keepalive}")

        if client_connections == 1:
            # 单连接模式
            self._single_connection_transfer(ip, port, timeout, request_size_kb, recv_buffer_kb, nodelay, keepalive)
        else:
            # 多连接模式
            self._multi_connection_transfer(ip, port, timeout, request_size_kb,
                                            client_connections, recv_buffer_kb, nodelay, keepalive)

    def _single_connection_transfer(self, ip, port, timeout, request_size_kb, recv_buffer_kb, nodelay, keepalive):
        """单连接数据传输"""
        start_time = time.time()
        total_received = 0

        try:
            # 连接到服务器
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            # 设置TCP选项
            if nodelay:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if keepalive:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            sock.connect((ip, port))

            # 发送数据请求
            request = f"DATA_REQUEST:{request_size_kb}".encode('utf-8')
            sock.send(request)

            self.logger.info(f"已发送数据请求: {request_size_kb}KB")

            # 接收数据并更新进度
            expected_size = request_size_kb * 1024
            buffer_size = recv_buffer_kb * 1024

            while total_received < expected_size and self.is_scanning:
                try:
                    data = sock.recv(buffer_size)
                    if not data:
                        break

                    total_received += len(data)

                    # 更新进度
                    self.update_transfer_progress(total_received, expected_size, start_time)

                except socket.timeout:
                    break

            sock.close()

            # 传输完成
            elapsed_time = time.time() - start_time
            if total_received >= expected_size:
                self.logger.info(
                    f"数据传输完成: 接收 {total_received/1024:.1f}KB, 耗时 {elapsed_time:.2f}秒, 平均速度 {(total_received/1024)/elapsed_time:.1f}KB/s")
                self.update_progress_info("传输完成!", "green")
            else:
                self.logger.warning(f"数据传输不完整: 期望 {expected_size/1024:.1f}KB, 实际接收 {total_received/1024:.1f}KB")
                self.update_progress_info("传输不完整", "orange")

        except Exception as e:
            self.logger.error(f"数据传输测试失败: {str(e)}")
            self.update_progress_info(f"传输失败: {str(e)}", "red")

    def _multi_connection_transfer(self, ip, port, timeout, request_size_kb, connections, recv_buffer_kb, nodelay, keepalive):
        """多连接数据传输"""
        self.logger.info(f"启动 {connections} 个并发连接进行数据传输测试")

        # 每个连接请求的数据大小
        per_connection_kb = request_size_kb // connections

        # 使用线程池进行并发连接
        import threading
        threads = []
        results = []

        def connection_worker(conn_id):
            try:
                result = self._single_connection_worker(
                    ip, port, timeout, per_connection_kb, recv_buffer_kb, nodelay, keepalive, conn_id)
                results.append(result)
            except Exception as e:
                self.logger.error(f"连接 {conn_id} 失败: {str(e)}")
                results.append({'success': False, 'received': 0, 'time': 0})

        start_time = time.time()

        # 启动所有连接线程
        for i in range(connections):
            thread = threading.Thread(target=connection_worker, args=(i+1,), daemon=True)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 统计结果
        total_received = sum(r['received'] for r in results)
        successful_connections = sum(1 for r in results if r['success'])
        elapsed_time = time.time() - start_time

        self.logger.info(f"多连接传输完成: {successful_connections}/{connections} 个连接成功")
        self.logger.info(f"总接收数据: {total_received/1024:.1f}KB, 总耗时: {elapsed_time:.2f}秒")

        if successful_connections == connections:
            self.update_progress_info(f"多连接传输完成! ({successful_connections}/{connections})", "green")
        else:
            self.update_progress_info(f"部分连接失败 ({successful_connections}/{connections})", "orange")

    def _single_connection_worker(self, ip, port, timeout, request_size_kb, recv_buffer_kb, nodelay, keepalive, conn_id):
        """单个连接的工作线程"""
        total_received = 0
        start_time = time.time()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            if nodelay:
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            if keepalive:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            sock.connect((ip, port))

            request = f"DATA_REQUEST:{request_size_kb}".encode('utf-8')
            sock.send(request)

            expected_size = request_size_kb * 1024
            buffer_size = recv_buffer_kb * 1024

            while total_received < expected_size and self.is_scanning:
                try:
                    data = sock.recv(buffer_size)
                    if not data:
                        break
                    total_received += len(data)
                except socket.timeout:
                    break

            sock.close()
            elapsed_time = time.time() - start_time

            self.logger.info(f"连接 {conn_id}: 接收 {total_received/1024:.1f}KB, 耗时 {elapsed_time:.2f}秒")

            return {'success': True, 'received': total_received, 'time': elapsed_time}

        except Exception as e:
            self.logger.error(f"连接 {conn_id} 错误: {str(e)}")
            return {'success': False, 'received': total_received, 'time': time.time() - start_time}

    def reset_progress(self):
        """重置进度显示"""
        def update_ui():
            self.progress_var.set(0)
            self.progress_info.config(text="正在连接服务器...", foreground="blue")
            self.received_label.config(text="0 KB")
            self.speed_label.config(text="0 KB/s")
            self.eta_label.config(text="--")

        self.parent_frame.after(0, update_ui)

    def update_transfer_progress(self, received, total, start_time):
        """更新传输进度"""
        def update_ui():
            # 计算进度百分比
            progress = (received / total) * 100 if total > 0 else 0
            self.progress_var.set(progress)

            # 计算传输速度
            elapsed = time.time() - start_time
            speed = (received / elapsed) if elapsed > 0 else 0

            # 计算剩余时间
            if speed > 0:
                remaining_bytes = total - received
                eta_seconds = remaining_bytes / speed
                eta_text = f"{eta_seconds:.1f}s"
            else:
                eta_text = "--"

            # 更新显示
            self.progress_info.config(text=f"正在接收数据... {progress:.1f}%", foreground="blue")
            self.received_label.config(text=f"{received/1024:.1f} KB")
            self.speed_label.config(text=f"{speed/1024:.1f} KB/s")
            self.eta_label.config(text=eta_text)

        self.parent_frame.after(0, update_ui)

    def update_progress_info(self, message, color="black"):
        """更新进度信息"""
        def update_ui():
            self.progress_info.config(text=message, foreground=color)

        self.parent_frame.after(0, update_ui)

    def test_tcp_connection(self, ip, port, timeout):
        """测试TCP连接"""
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()

            response_time = (time.time() - start_time) * 1000  # 转换为毫秒

            if result == 0:
                service = self.get_service_name(port)
                return {
                    'status': '开放',
                    'response_time': f"{response_time:.1f}",
                    'service': service
                }
            else:
                return {
                    'status': '关闭',
                    'response_time': f"{response_time:.1f}",
                    'service': ''
                }
        except socket.timeout:
            response_time = timeout * 1000
            return {
                'status': '超时',
                'response_time': f"{response_time:.0f}",
                'service': ''
            }
        except Exception as e:
            return {
                'status': '错误',
                'response_time': '0',
                'service': str(e)
            }

    def get_service_name(self, port):
        """获取端口对应的服务名称"""
        common_ports = {
            21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
            80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 993: 'IMAPS',
            995: 'POP3S', 587: 'SMTP', 465: 'SMTPS', 3389: 'RDP', 3306: 'MySQL',
            5432: 'PostgreSQL', 1433: 'MSSQL', 6379: 'Redis', 27017: 'MongoDB',
            8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 9200: 'Elasticsearch'
        }
        return common_ports.get(port, '未知')

    def add_result_to_tree(self, port, status, response_time, service):
        """添加结果到表格"""
        # 在主线程中更新UI
        def update_ui():
            # 根据状态设置不同的标签
            if status == '开放':
                tags = ('open',)
            elif status == '关闭':
                tags = ('closed',)
            elif status == '超时':
                tags = ('timeout',)
            else:
                tags = ('error',)

            self.result_tree.insert('', 'end', values=(port, status, response_time, service), tags=tags)

            # 滚动到最新添加的项目
            children = self.result_tree.get_children()
            if children:
                self.result_tree.see(children[-1])

        # 使用after方法在主线程中执行UI更新
        self.parent_frame.after(0, update_ui)

    def update_button_state(self):
        """更新按钮状态"""
        def update_ui():
            if self.is_scanning:
                self.test_button.config(state='disabled')
                self.stop_button.config(state='normal')
            else:
                self.test_button.config(state='normal')
                self.stop_button.config(state='disabled')

        self.parent_frame.after(0, update_ui)

    def stop_scan(self):
        """停止扫描"""
        self.is_scanning = False
        self.logger.info("用户停止了端口扫描")

    def clear_results(self):
        """清除结果"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)


class NetworkTestTool:
    """网络测试工具主窗口"""

    def __init__(self, root):
        self.root = root
        self.root.title("网络测试工具")
        self.root.geometry("1200x800")

        # 设置日志
        self.log_stream = StringIO()
        self.setup_logging()

        # 当前测试模块
        self.current_module = None
        self.test_modules = {}

        # 创建UI
        self.create_widgets()

        # 初始化所有测试模块
        self.init_test_modules()

        # 默认显示HTTP测试模块
        self.switch_to_http()

    def setup_logging(self):
        """配置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(self.log_stream)]
        )
        self.logger = logging.getLogger(__name__)

    def create_widgets(self):
        """创建用户界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 顶部模块切换按钮
        module_frame = ttk.LabelFrame(main_frame, text="测试模块", padding="10")
        module_frame.pack(fill=tk.X, pady=5)

        ttk.Button(module_frame, text="HTTP测试", command=self.switch_to_http).pack(side=tk.LEFT, padx=5)
        ttk.Button(module_frame, text="TCP测试", command=self.switch_to_tcp).pack(side=tk.LEFT, padx=5)

        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 左侧测试模块区域
        self.test_frame = ttk.Frame(content_frame)
        self.test_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 右侧日志区域
        log_frame = ttk.LabelFrame(content_frame, text="日志", padding="10")
        log_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        log_frame.pack_propagate(False)  # 阻止子组件影响父容器大小
        log_frame.config(width=500)  # 设置固定宽度

        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 日志操作按钮
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(log_button_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_button_frame, text="清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=2)

        # 底部退出按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(bottom_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

        # 定时更新日志显示
        self.update_log_display()

    def init_test_modules(self):
        """初始化所有测试模块"""
        # 创建HTTP测试模块容器
        self.http_frame = ttk.Frame(self.test_frame)
        self.test_modules['http'] = HTTPTestModule(
            self.http_frame,
            self.logger,
            log_callback=self.schedule_callback
        )

        # 创建TCP测试模块容器
        self.tcp_frame = ttk.Frame(self.test_frame)
        self.test_modules['tcp'] = TCPTestModule(self.tcp_frame, self.logger)

    def switch_to_http(self):
        """切换到HTTP测试模块"""
        self.hide_all_modules()
        self.http_frame.pack(fill=tk.BOTH, expand=True)
        self.current_module = self.test_modules['http']

    def switch_to_tcp(self):
        """切换到TCP测试模块"""
        self.hide_all_modules()
        self.tcp_frame.pack(fill=tk.BOTH, expand=True)
        self.current_module = self.test_modules['tcp']

    def hide_all_modules(self):
        """隐藏所有测试模块"""
        self.http_frame.pack_forget()
        self.tcp_frame.pack_forget()

    def schedule_callback(self, delay, callback):
        """调度回调函数"""
        if delay == 'idle':
            self.root.after_idle(callback)
        else:
            self.root.after(delay, callback)

    def update_log_display(self):
        """更新日志显示区域"""
        log_content = self.log_stream.getvalue()
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, log_content)
        self.log_text.see(tk.END)
        self.root.after(500, self.update_log_display)  # 每500毫秒更新一次

    def save_log(self):
        """保存日志到文件"""
        try:
            log_content = self.log_stream.getvalue()
            if not log_content.strip():
                messagebox.showwarning("警告", "没有日志内容可保存")
                return

            # 获取桌面路径
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            log_file = os.path.join(desktop, "network_test_log.txt")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)

            self.logger.info(f"日志已保存到: {log_file}")
            messagebox.showinfo("成功", f"日志已保存到桌面: network_test_log.txt")
        except Exception as e:
            self.logger.error(f"保存日志失败: {str(e)}")
            messagebox.showerror("错误", f"保存日志失败: {str(e)}")

    def clear_log(self):
        """清除日志"""
        self.log_stream.truncate(0)
        self.log_stream.seek(0)
        self.log_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = NetworkTestTool(root)
    root.mainloop()


if __name__ == "__main__":
    main()
