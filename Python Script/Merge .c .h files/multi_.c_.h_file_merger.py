import os
import tkinter as tk
from tkinter import filedialog, messagebox

class FileCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件聚合工具")
        
        # 默认路径设置为脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.source_dir = self.script_dir
        self.output_dir = self.script_dir
        
        # 创建UI元素
        self.create_widgets()
        
    def create_widgets(self):
        # 源目录选择
        tk.Label(self.root, text="源目录:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.source_dir_entry = tk.Entry(self.root, width=50)
        self.source_dir_entry.grid(row=0, column=1, padx=5, pady=5)
        self.source_dir_entry.insert(0, self.source_dir)
        tk.Button(self.root, text="浏览...", command=self.select_source_dir).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出目录选择
        tk.Label(self.root, text="输出目录:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.output_dir_entry = tk.Entry(self.root, width=50)
        self.output_dir_entry.grid(row=1, column=1, padx=5, pady=5)
        self.output_dir_entry.insert(0, self.output_dir)
        tk.Button(self.root, text="浏览...", command=self.select_output_dir).grid(row=1, column=2, padx=5, pady=5)
        
        # 执行按钮
        tk.Button(self.root, text="聚合.h文件", command=lambda: self.collect_files('.h', '集合.h')).grid(row=2, column=0, padx=5, pady=10)
        tk.Button(self.root, text="聚合.c文件", command=lambda: self.collect_files('.c', '集合.c')).grid(row=2, column=1, padx=5, pady=10)
        tk.Button(self.root, text="全部聚合", command=self.collect_all).grid(row=2, column=2, padx=5, pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("准备就绪")
        tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W).grid(
            row=3, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5)
    
    def select_source_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.source_dir)
        if dir_path:
            self.source_dir = dir_path
            self.source_dir_entry.delete(0, tk.END)
            self.source_dir_entry.insert(0, dir_path)
    
    def select_output_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, dir_path)
    
    def collect_files(self, extension, output_filename):
        try:
            self.status_var.set("正在处理...")
            self.root.update()  # 更新UI
            
            # 获取当前设置的目录
            source_dir = self.source_dir_entry.get()
            output_dir = self.output_dir_entry.get()
            
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, 'w', encoding='utf-8') as outfile:
                # 遍历当前目录及所有子目录
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        if file.endswith(extension) and file != output_filename:  # 排除输出文件本身
                            filepath = os.path.join(root, file)
                            try:
                                # 写入文件名作为分隔标识
                                outfile.write(f"/***** File: {filepath} *****/\n\n")
                                # 写入文件内容
                                with open(filepath, 'r', encoding='utf-8') as infile:
                                    content = infile.read().rstrip()  # 移除原文件末尾的空白
                                    outfile.write(content)
                                outfile.write('\n\n')  # 添加两个换行作为分隔
                            except Exception as e:
                                print(f"Error processing {filepath}: {e}")
            
            self.status_var.set(f"已完成: {output_filename}")
            messagebox.showinfo("完成", f"文件聚合完成: {output_path}")
        except Exception as e:
            self.status_var.set("发生错误")
            messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
    
    def collect_all(self):
        self.collect_files('.h', '集合.h')
        self.collect_files('.c', '集合.c')

if __name__ == '__main__':
    root = tk.Tk()
    app = FileCollectorApp(root)
    root.mainloop()