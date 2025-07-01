import os
import threading
from io import StringIO
import logging
import requests
from tkinter import ttk, messagebox, scrolledtext
import tkinter as tk


class BrowserSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("浏览器模拟访问工具")
        self.root.geometry("1000x800")

        # 设置日志
        self.log_stream = StringIO()
        self.setup_logging()

        # 创建UI
        self.create_widgets()

        # 默认IP
        self.default_ip = "192.168.2.43"
        self.ip_entry.insert(0, self.default_ip)

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

        # IP输入部分
        ip_frame = ttk.LabelFrame(main_frame, text="目标IP地址", padding="10")
        ip_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ip_frame, text="IP地址:").grid(row=0, column=0, sticky=tk.W)
        self.ip_entry = ttk.Entry(ip_frame, width=40)
        self.ip_entry.grid(row=0, column=1, padx=5)

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
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.access_button = ttk.Button(button_frame, text="访问", command=self.start_access_thread)
        self.access_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="清除日志", command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="保存日志", command=self.save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除HTML", command=self.clear_html).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.RIGHT, padx=5)

        # 日志和HTML内容框架
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 日志显示
        log_frame = ttk.LabelFrame(content_frame, text="日志", padding="10")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # HTML内容显示
        html_frame = ttk.LabelFrame(content_frame, text="HTML内容", padding="10")
        html_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.html_text = scrolledtext.ScrolledText(
            html_frame,
            wrap=tk.WORD,
            font=('Consolas', 10)  # 使用等宽字体更好显示HTML
        )
        self.html_text.pack(fill=tk.BOTH, expand=True)

        # 定时更新日志显示
        self.update_log_display()

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

            except requests.exceptions.RequestException as e:
                self.logger.error(f"访问失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"发生错误: {str(e)}", exc_info=True)

    def update_log_display(self):
        """更新日志显示区域"""
        log_content = self.log_stream.getvalue()
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, log_content)
        self.log_text.see(tk.END)
        self.root.after(500, self.update_log_display)  # 每500毫秒更新一次

    def clear_log(self):
        """清除日志"""
        self.log_stream.truncate(0)
        self.log_stream.seek(0)
        self.log_text.delete(1.0, tk.END)

    def clear_html(self):
        """清除HTML内容"""
        self.html_text.delete(1.0, tk.END)

    def save_log(self):
        """保存日志到文件"""
        try:
            log_content = self.log_stream.getvalue()
            if not log_content.strip():
                messagebox.showwarning("警告", "没有日志内容可保存")
                return

            # 获取桌面路径
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            log_file = os.path.join(desktop, "browser_simulator_log.txt")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)

            self.logger.info(f"日志已保存到: {log_file}")
            messagebox.showinfo("成功", f"日志已保存到桌面: browser_simulator_log.txt")
        except Exception as e:
            self.logger.error(f"保存日志失败: {str(e)}")
            messagebox.showerror("错误", f"保存日志失败: {str(e)}")


def main():
    root = tk.Tk()
    app = BrowserSimulatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
