import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QWidget,
                             QFileDialog, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class FileProcessor(QThread):
    """文件处理线程"""
    progress_updated = pyqtSignal(int)
    finished_processing = pyqtSignal(str, bool)

    def __init__(self, input_file, output_file, search_string):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.search_string = search_string
        self.processed_lines = 0
        self.total_lines = 0

    def run(self):
        try:
            # 统计总行数
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.total_lines = sum(1 for _ in f)

            if self.total_lines == 0:
                self.finished_processing.emit("文件为空！", False)
                return

            processed_count = 0
            removed_count = 0
            blank_removed_count = 0

            with open(self.input_file, 'r', encoding='utf-8') as infile, \
                    open(self.output_file, 'w', encoding='utf-8') as outfile:

                for line in infile:
                    processed_count += 1

                    # 更新进度
                    progress = int((processed_count / self.total_lines) * 100)
                    self.progress_updated.emit(progress)

                    # 跳过包含指定字符串的行
                    if self.search_string in line:
                        removed_count += 1
                        continue

                    # 跳过空白行（将在后续处理中删除）
                    stripped_line = line.rstrip('\r\n')
                    if not stripped_line:
                        blank_removed_count += 1
                        continue

                    # 写入非空白行
                    outfile.write(line)

            # 最终清理：重新读取并删除所有空白行
            with open(self.output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 过滤掉所有空白行
            non_blank_lines = [line for line in lines if line.strip()]

            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.writelines(non_blank_lines)

            result_message = (f"处理完成！\n"
                              f"总处理行数: {self.total_lines}\n"
                              f"删除包含指定字符串的行: {removed_count}\n"
                              f"删除空白行: {blank_removed_count}\n"
                              f"输出文件: {self.output_file}")

            self.finished_processing.emit(result_message, True)

        except Exception as e:
            self.finished_processing.emit(f"处理过程中出现错误: {str(e)}", False)


class TextFileCleaner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("TXT文件清理工具")
        self.setGeometry(100, 100, 800, 600)

        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout()

        # 输入文件选择
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("输入文件:"))
        self.input_file_edit = QLineEdit()
        self.input_file_edit.setPlaceholderText("选择或输入源文件路径...")
        input_layout.addWidget(self.input_file_edit)
        self.input_browse_btn = QPushButton("浏览")
        self.input_browse_btn.clicked.connect(self.browse_input_file)
        input_layout.addWidget(self.input_browse_btn)
        layout.addLayout(input_layout)

        # 输出文件选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件:"))
        self.output_file_edit = QLineEdit()
        self.output_file_edit.setPlaceholderText("选择或输入输出文件路径...")
        output_layout.addWidget(self.output_file_edit)
        self.output_browse_btn = QPushButton("浏览")
        self.output_browse_btn.clicked.connect(self.browse_output_file)
        output_layout.addWidget(self.output_browse_btn)
        layout.addLayout(output_layout)

        # 搜索字符串输入
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("要删除的字符串:"))
        self.search_string_edit = QLineEdit()
        self.search_string_edit.setPlaceholderText("输入要删除的字符串...")
        search_layout.addWidget(self.search_string_edit)
        layout.addLayout(search_layout)

        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.process_file)
        layout.addWidget(self.process_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 日志显示
        layout.addWidget(QLabel("处理日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # 设置默认路径
        self.set_default_paths()

        central_widget.setLayout(layout)

    def set_default_paths(self):
        """设置默认文件路径"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_input = os.path.join(current_dir, "input.txt")
        default_output = os.path.join(current_dir, "output.txt")

        self.input_file_edit.setText(default_input)
        self.output_file_edit.setText(default_output)

    def browse_input_file(self):
        """浏览输入文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if file_path:
            self.input_file_edit.setText(file_path)

    def browse_output_file(self):
        """浏览输出文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if file_path:
            self.output_file_edit.setText(file_path)

    def log_message(self, message):
        """添加日志消息"""
        self.log_text.append(message)

    def process_file(self):
        """处理文件"""
        input_file = self.input_file_edit.text().strip()
        output_file = self.output_file_edit.text().strip()
        # search_string = self.search_string_edit.text().strip()
        search_string = self.search_string_edit.text()

        # 验证输入
        if not input_file:
            QMessageBox.warning(self, "警告", "请输入输入文件路径！")
            return

        if not output_file:
            QMessageBox.warning(self, "警告", "请输入输出文件路径！")
            return

        if not search_string:
            QMessageBox.warning(self, "警告", "请输入要删除的字符串！")
            return

        if not os.path.exists(input_file):
            QMessageBox.warning(self, "警告", "输入文件不存在！")
            return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.process_btn.setEnabled(False)

        # 创建并启动处理线程
        self.processor = FileProcessor(input_file, output_file, search_string)
        self.processor.progress_updated.connect(self.progress_bar.setValue)
        self.processor.finished_processing.connect(self.on_processing_finished)
        self.processor.start()

        self.log_message(f"开始处理文件: {input_file}")
        self.log_message(f"搜索字符串: '{search_string}'")

    def on_processing_finished(self, message, success):
        """处理完成回调"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)

        if success:
            self.log_message(message)
            QMessageBox.information(self, "完成", "文件处理完成！")
        else:
            self.log_message(f"错误: {message}")
            QMessageBox.critical(self, "错误", message)


def main():
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle('Fusion')

    window = TextFileCleaner()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
