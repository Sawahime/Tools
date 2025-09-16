import sys
import os
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QProgressBar, QGroupBox, QComboBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap


class ImageConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.supported_formats = {
            'PNG': '.png',
            'JPEG': '.jpg',
            'ICO': '.ico',
            # 可以轻松添加更多格式
            # 'BMP': '.bmp',
            # 'GIF': '.gif',
            # 'TIFF': '.tiff',
        }
        self.initUI()
        self.input_file = ""

    def initUI(self):
        self.setWindowTitle('图片格式转换工具')
        self.setGeometry(300, 300, 550, 500)
        self.setAcceptDrops(True)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        layout = QVBoxLayout(central_widget)

        # 输入区域
        input_group = QGroupBox("输入文件")
        input_layout = QVBoxLayout()

        self.input_label = QLabel("拖放图片文件到这里或点击浏览")
        self.input_label.setAlignment(Qt.AlignCenter)
        self.input_label.setMinimumHeight(150)
        self.input_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")

        browse_btn = QPushButton("浏览文件")
        browse_btn.clicked.connect(self.browse_file)

        input_layout.addWidget(self.input_label)
        input_layout.addWidget(browse_btn)
        input_group.setLayout(input_layout)

        # 格式选择区域
        format_group = QGroupBox("转换设置")
        format_layout = QVBoxLayout()

        # 源格式显示
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("源文件格式:"))
        self.source_format_label = QLabel("未选择")
        source_layout.addWidget(self.source_format_label)
        source_layout.addStretch()
        format_layout.addLayout(source_layout)

        # 目标格式选择
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("转换为:"))

        # 把我们支持的类型添加到下拉菜单
        self.target_format_combo = QComboBox()
        for fmt in self.supported_formats.keys():
            self.target_format_combo.addItem(fmt)
        # 连接信号到槽函数
        self.target_format_combo.currentIndexChanged.connect(self.on_target_format_changed)

        target_layout.addWidget(self.target_format_combo)
        target_layout.addStretch()
        format_layout.addLayout(target_layout)

        format_group.setLayout(format_layout)

        # 输出区域
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()

        self.output_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.output_label = QLabel(f"输出到: {self.output_path}")
        self.output_label.setWordWrap(True)

        output_btn = QPushButton("选择输出位置")
        output_btn.clicked.connect(self.select_output)

        output_layout.addWidget(self.output_label)
        output_layout.addWidget(output_btn)
        output_group.setLayout(output_layout)

        # 转换按钮
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.clicked.connect(self.convert_image)
        self.convert_btn.setEnabled(False)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # 添加到主布局
        layout.addWidget(input_group)
        layout.addWidget(format_group)
        layout.addWidget(output_group)
        layout.addWidget(self.convert_btn)
        layout.addWidget(self.progress_bar)

    def browse_file(self):
        # 构建文件过滤器
        file_types = "所有支持的格式 ("
        file_types += " ".join([f"*{ext}" for ext in self.supported_formats.values()])
        file_types += ");;"
        file_types += ";".join([f"{fmt}文件 (*{ext})" for fmt, ext in self.supported_formats.items()])

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", "", file_types
        )
        if file_path:
            self.set_input_file(file_path)

    def detect_format(self, file_path):
        """检测文件格式并返回格式名称"""
        ext = os.path.splitext(file_path)[1].lower()
        for fmt, fmt_ext in self.supported_formats.items():
            if ext == fmt_ext.lower():
                return fmt
        return None

    def set_input_file(self, file_path):
        detected_format = self.detect_format(file_path)

        if detected_format:
            self.input_file = file_path
            self.source_format_label.setText(detected_format)
            self.input_label.setText(f"已选择: {os.path.basename(file_path)}")

            # 显示缩略图
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(QSize(100, 100), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.input_label.setPixmap(scaled_pixmap)
            except:
                self.input_label.setText("无法显示预览")

            # 启用转换按钮
            self.convert_btn.setEnabled(True)
            self.convert_btn.setText("开始转换")

            # 如果源格式和目标格式相同，禁用转换按钮
            target_format = self.target_format_combo.currentText()
            if detected_format == target_format:
                self.convert_btn.setEnabled(False)
                self.convert_btn.setText("错误：源文件格式与目标格式相同")
        else:
            QMessageBox.warning(
                self,
                "错误",
                f"不支持的文件格式。支持的格式: {', '.join(self.supported_formats.keys())}"
            )

    def on_target_format_changed(self, index):
        """当目标格式改变时调用"""
        if index >= 0:  # 确保有有效的选择
            new_format = self.target_format_combo.currentText()

            if self.input_file:
                source_format = self.detect_format(self.input_file)
                if source_format == new_format:
                    self.convert_btn.setEnabled(False)
                    self.convert_btn.setText("错误：源文件格式与目标格式相同")
                else:
                    self.convert_btn.setEnabled(True)
                    self.convert_btn.setText("开始转换")

    def select_output(self):
        directory = QFileDialog.getExistingDirectory(
            self, "选择输出文件夹", self.output_path
        )
        if directory:
            self.output_path = directory
            self.output_label.setText(f"输出到: {directory}")

    def convert_image(self):
        if not self.input_file:
            QMessageBox.warning(self, "错误", "请先选择图片文件")
            return

        source_format = self.detect_format(self.input_file)
        target_format = self.target_format_combo.currentText()

        if source_format == target_format:
            QMessageBox.warning(self, "错误", "源格式和目标格式相同，无需转换")
            return

        # 准备输出文件名
        base_name = os.path.splitext(os.path.basename(self.input_file))[0]
        output_ext = self.supported_formats[target_format]
        output_file = os.path.join(self.output_path, f"{base_name}{output_ext}")

        # 检查文件是否已存在
        if os.path.exists(output_file):
            reply = QMessageBox.question(
                self, "文件已存在",
                f"文件 {base_name}{output_ext} 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            # 转换图像
            img = Image.open(self.input_file)

            # 对于ICO格式的特殊处理
            if target_format == 'ICO':
                # ICO文件通常需要多个尺寸，这里创建一个包含常用尺寸的ICO
                self.progress_bar.setValue(30)

                # 创建不同尺寸
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
                images = []

                for size in sizes:
                    # 保持宽高比调整大小
                    img_resized = img.resize(size, Image.LANCZOS)
                    images.append(img_resized)

                self.progress_bar.setValue(70)

                # 保存为ICO
                images[0].save(
                    output_file,
                    format='ICO',
                    sizes=[img.size for img in images],
                    append_images=images[1:] if len(images) > 1 else []
                )
            else:
                self.progress_bar.setValue(50)

                # 转换为RGB模式（JPEG不支持透明通道）
                if target_format == 'JPEG' and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img, mask=img.getchannel('A'))
                    img = background

                # 保存图像
                img.save(output_file, format=target_format)

            self.progress_bar.setValue(100)

            QMessageBox.information(self, "成功", f"文件已保存到: {output_file}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")

        # 隐藏进度条
        self.progress_bar.setVisible(False)

    # 拖放支持
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.set_input_file(file_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = ImageConverter()
    converter.show()
    sys.exit(app.exec_())
