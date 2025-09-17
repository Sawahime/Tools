import sys
import os
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QGroupBox,
    QComboBox,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QPixmap


class ImageConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.supported_formats = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "ICO": ".ico",
        }
        self.conversion_functions = {
            ("PNG", "ICO"): self.convert_png2ico,
            ("PNG", "JPEG"): self.convert_png2jpg,
        }
        self.initUI()
        self.input_file = ""

    def initUI(self):
        self.setWindowTitle("图片格式转换工具")
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
        self.target_format_combo.currentIndexChanged.connect(
            self.on_target_format_changed
        )

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
        self.convert_btn = QPushButton("请输入源文件")
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
        file_types += ";".join(
            [f"{fmt}文件 (*{ext})" for fmt, ext in self.supported_formats.items()]
        )

        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片文件", "", file_types)
        if file_path:
            self.set_input_file(file_path)

    def detect_format(self, file_path):
        """检测文件格式并返回格式名称"""
        ext = os.path.splitext(file_path)[1].lower()
        for fmt, fmt_ext in self.supported_formats.items():
            if ext == fmt_ext.lower():
                return fmt
        return None

    # 拖放支持
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.set_input_file(file_path)

    def set_input_file(self, file_path):
        source_format = self.detect_format(file_path)

        if source_format:
            self.input_file = file_path
            self.source_format_label.setText(source_format)
            self.input_label.setText(f"已选择: {os.path.basename(file_path)}")

            # 显示缩略图
            try:
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        QSize(100, 100), Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.input_label.setPixmap(scaled_pixmap)
            except:
                self.input_label.setText("无法显示预览")

            target_format = self.target_format_combo.currentText()
            if (source_format, target_format) in self.conversion_functions:
                self.convert_btn.setEnabled(True)
                self.convert_btn.setText("开始转换")
            else:
                self.convert_btn.setEnabled(False)
                self.convert_btn.setText("错误：暂不支持这样的格式转换")
        else:
            QMessageBox.warning(
                self,
                "错误",
                f"不支持的文件格式。支持的格式: {', '.join(self.supported_formats.keys())}",
            )

    def on_target_format_changed(self, index):
        """当目标格式改变时调用"""
        if index >= 0:  # 确保有有效的选择
            new_format = self.target_format_combo.currentText()

            if self.input_file:
                source_format = self.detect_format(self.input_file)
                if (source_format, new_format) not in self.conversion_functions:
                    self.convert_btn.setEnabled(False)
                    self.convert_btn.setText("暂不支持这样的格式转换")
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
                self,
                "文件已存在",
                f"文件 {base_name}{output_ext} 已存在，是否覆盖？",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        try:
            img = Image.open(self.input_file)
            if (source_format, target_format) in self.conversion_functions:
                self.conversion_functions[(source_format, target_format)](
                    img, output_file
                )
                QMessageBox.information(self, "成功", f"文件已保存到: {output_file}")
            else:
                self.convert_btn.setEnabled(False)
                self.convert_btn.setText("错误：暂不支持这样的格式转换")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"转换失败: {str(e)}")

        # 隐藏进度条
        self.progress_bar.setVisible(False)

    def convert_png2ico(self, img, output_file):
        self.progress_bar.setValue(0)

        # 创建不同尺寸
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
        images = []
        self.progress_bar.setValue(30)

        for size in sizes:
            # 保持宽高比调整大小
            img_resized = img.resize(size, Image.LANCZOS)
            images.append(img_resized)

        self.progress_bar.setValue(70)

        # 保存为ICO
        images[0].save(
            output_file,
            format="ICO",
            sizes=[img.size for img in images],
            append_images=images[1:] if len(images) > 1 else [],
        )

        self.progress_bar.setValue(100)

    def convert_png2jpg(self, img, output_file):
        self.progress_bar.setValue(0)

        if img.mode in ("RGBA", "LA"):
            # 创建一个白色背景
            background = Image.new("RGB", img.size, (255, 255, 255))
            self.progress_bar.setValue(30)
            # 如果图像有透明度，合并到白色背景上
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img, mask=img.getchannel("A"))
            self.progress_bar.setValue(60)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        self.progress_bar.setValue(80)

        # 保存为JPEG格式，可以设置质量参数（0-100，默认75）
        img.save(output_file, format="JPEG", quality=100)
        self.progress_bar.setValue(100)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    converter = ImageConverter()
    converter.show()
    sys.exit(app.exec_())
