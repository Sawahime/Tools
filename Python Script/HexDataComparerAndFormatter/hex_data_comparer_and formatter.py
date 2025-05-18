import re
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QPushButton, QLabel, QGroupBox, QCheckBox,
                             QComboBox, QLineEdit, QSpinBox, QTabWidget, QColorDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCharFormat, QSyntaxHighlighter, QColor, QFont


class HexHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, highlight_color=QColor(Qt.yellow)):
        super().__init__(parent)
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(highlight_color)
        self.mismatch_positions = []  # 存储需要高亮的文本位置区间

    def update_mismatches(self, mismatches):
        """更新需要高亮的位置信息"""
        self.mismatch_positions = mismatches
        self.rehighlight()

    def highlightBlock(self, text):
        """根据存储的位置信息执行高亮"""
        for start, end in self.mismatch_positions:
            if start >= 0 and end <= len(text):
                self.setFormat(start, end - start, self.highlight_format)


class HexCompareWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._updating = False  # 添加更新标志
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.default_left_color = QColor(170, 255, 255)
        self.default_right_color = QColor(Qt.yellow)

        # Color selection
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Left Highlight Color:"))
        self.left_color_btn = QPushButton()
        self.left_color_btn.setStyleSheet(f"background-color: {self.default_left_color.name()}")
        self.left_color_btn.clicked.connect(lambda: self.choose_color('left'))
        color_layout.addWidget(self.left_color_btn)

        color_layout.addWidget(QLabel("Right Highlight Color:"))
        self.right_color_btn = QPushButton()
        self.right_color_btn.setStyleSheet(f"background-color: {self.default_right_color.name()}")
        self.right_color_btn.clicked.connect(lambda: self.choose_color('right'))
        color_layout.addWidget(self.right_color_btn)

        color_layout.addStretch()
        layout.addLayout(color_layout)

        # Text edit areas
        text_layout = QHBoxLayout()

        self.left_text = QTextEdit()
        self.left_text.setPlaceholderText("Enter first hex data here...")
        self.left_text.textChanged.connect(self.safe_compare_hex)
        text_layout.addWidget(self.left_text)

        self.right_text = QTextEdit()
        self.right_text.setPlaceholderText("Enter second hex data here...")
        self.right_text.textChanged.connect(self.safe_compare_hex)
        text_layout.addWidget(self.right_text)

        layout.addLayout(text_layout)

        self.setLayout(layout)

        # Initialize highlighters
        self.left_highlighter = HexHighlighter(self.left_text.document(), QColor(101, 165, 255))
        self.right_highlighter = HexHighlighter(self.right_text.document(), QColor(Qt.yellow))

    def safe_compare_hex(self):
        """防递归的对比触发"""
        if not hasattr(self, '_compare_lock'):
            self._compare_lock = False

        if self._compare_lock:
            return

        self._compare_lock = True
        try:
            left_text = self.left_text.toPlainText()
            right_text = self.right_text.toPlainText()

            # 保存光标位置
            left_cursor = self.left_text.textCursor()
            right_cursor = self.right_text.textCursor()

            # 执行比较
            left_mismatches, right_mismatches = self.find_mismatches(
                left_text, right_text)
            self.left_highlighter.update_mismatches(left_mismatches)
            self.right_highlighter.update_mismatches(right_mismatches)

            # 恢复光标
            self.left_text.setTextCursor(left_cursor)
            self.right_text.setTextCursor(right_cursor)
        except Exception as e:
            print(f"比较错误: {e}")
        finally:
            self._compare_lock = False

    def choose_color(self, side):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                if side == 'left':
                    self.left_highlighter.highlight_format.setBackground(color)
                    self.left_color_btn.setStyleSheet(f"background-color: {color.name()}")
                else:
                    self.right_highlighter.highlight_format.setBackground(color)
                    self.right_color_btn.setStyleSheet(f"background-color: {color.name()}")
                self.safe_compare_hex()
        except Exception as e:
            print(f"Error choosing color: {str(e)}")

    def compare_hex(self):
        try:
            # 提取标准化后的十六进制值及其位置
            left_data = self.extract_hex_data(self.left_text.toPlainText())
            right_data = self.extract_hex_data(self.right_text.toPlainText())

            # 找出差异
            left_only = {d['normalized'] for d in left_data} - \
                {d['normalized'] for d in right_data}
            right_only = {d['normalized'] for d in right_data} - \
                {d['normalized'] for d in left_data}

            # 更新高亮器
            self.left_highlighter.hex_values_to_highlight = left_only
            self.right_highlighter.hex_values_to_highlight = right_only

            # 重新高亮
            self.left_highlighter.rehighlight()
            self.right_highlighter.rehighlight()

        except Exception as e:
            print(f"Comparison error: {str(e)}")

    def extract_hex_positions(self, text):
        """提取文本中所有十六进制值及其位置"""
        pattern = r'(0x[0-9a-fA-F]{2}|[0-9a-fA-F]{2})'
        return [
            (match.start(), match.end(), match.group().lower().replace('0x', ''))
            for match in re.finditer(pattern, text)
            if len(match.group().replace('0x', '')) == 2
        ]

    def find_mismatches(self, left_text, right_text):
        """找出两侧文本中需要高亮的位置"""
        left_data = self.extract_hex_positions(left_text)
        right_data = self.extract_hex_positions(right_text)

        # 找出值不同的项
        left_mismatches = []
        right_mismatches = []

        for i in range(max(len(left_data), len(right_data))):
            left_val = left_data[i][2] if i < len(left_data) else None
            right_val = right_data[i][2] if i < len(right_data) else None

            if left_val != right_val:
                if left_val is not None:
                    left_mismatches.append((left_data[i][0], left_data[i][1]))
                if right_val is not None:
                    right_mismatches.append(
                        (right_data[i][0], right_data[i][1]))

        return left_mismatches, right_mismatches


class HexFormatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.create_widgets()
        self.setup_layout()

    def _create_labeled_checkbox(self, text, checked=False):
        """创建带标签的复选框"""
        label = QLabel(text)
        cb = QCheckBox()
        cb.setChecked(checked)

        container = QWidget()
        container.setObjectName("CheckboxContainer")  # 设置对象名用于样式表
        container.setStyleSheet("""
            QWidget#CheckboxContainer {
                background-color: #f0f8ff;
                border-radius: 8px;
                border: 1px solid #d3d3d3;
            }
        """)
        container.real_widget = cb  # 将实际控件保存在容器上

        layout = QHBoxLayout(container)  # 设置布局到容器
        layout.addWidget(label)
        layout.addWidget(cb)

        return container

    def _create_labeled_combobox(self, text, items=["Upper", "Lower"]):
        """创建带标签的下拉框"""
        label = QLabel(text)
        cb = QComboBox()
        cb.addItems(items)

        container = QWidget()
        container.setObjectName("ComboboxContainer")
        container.setStyleSheet("""
            QWidget#ComboboxContainer {
                background-color: #fff0f5;
                border-radius: 8px;
                border: 1px solid #d3d3d3;
            }
        """)
        container.real_widget = cb

        layout = QHBoxLayout(container)
        layout.addWidget(label)
        layout.addWidget(cb)

        return container

    def _create_labeled_spinbox(self, text, value=16, range_=(1, 100)):
        """创建带标签的数字框"""
        label = QLabel(text)
        sb = QSpinBox()
        sb.setValue(value)
        sb.setRange(*range_)

        container = QWidget()
        container.setObjectName("SpinboxContainer")
        container.setStyleSheet("""
            QWidget#SpinboxContainer {
                background-color: #fff8dc;
                border-radius: 8px;
                border: 1px solid #d3d3d3;
            }
        """)
        container.real_widget = sb

        layout = QHBoxLayout(container)
        layout.addWidget(label)
        layout.addWidget(sb)

        return container

    def _create_labeled_lineedit(self, text, value=" "):
        """创建带标签的输入框"""
        label = QLabel(text)
        le = QLineEdit(value)

        container = QWidget()  # 创建容器
        container.setObjectName("LineeditContainer")
        container.setStyleSheet("""
            QWidget#LineeditContainer {
                background-color: #f0fff0;
                border-radius: 8px;
                border: 1px solid #d3d3d3;
            }
        """)
        container.real_widget = le

        layout = QHBoxLayout(container)  # 布局附加到容器
        layout.addWidget(label)
        layout.addWidget(le)
        layout.addStretch()  # 添加一个弹性空间，让前面的控件左对齐

        return container

    def create_widgets(self):
        """创建所有控件"""
        self.include_prefix = self._create_labeled_checkbox("With 0x:", True)
        self.include_prefix.real_widget.stateChanged.connect(self.update_output)

        self.letter_case = self._create_labeled_combobox("Letter Case:", ["Upper", "Lower"])
        self.letter_case.real_widget.currentIndexChanged.connect(self.update_output)

        self.bytes_per_line = self._create_labeled_spinbox("LineFeed:", 16, (1, 100))
        self.bytes_per_line.real_widget.valueChanged.connect(self.update_output)

        self.separator = self._create_labeled_lineedit("Separator:", " ")
        self.separator.real_widget.textChanged.connect(self.update_output)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter hex data to convert...")
        self.input_text.textChanged.connect(self.update_output)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_output)

    def setup_layout(self):
        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.include_prefix)
        settings_layout.addWidget(self.letter_case)
        settings_layout.addWidget(self.bytes_per_line)
        settings_layout.addWidget(self.separator)
        settings_layout.addStretch()  # 添加一个弹性空间，让前面的控件左对齐

        settings_group = QGroupBox("Format Settings")
        font = settings_group.font()
        font.setBold(True)
        settings_group.setFont(font)
        settings_group.setLayout(settings_layout)

        input_col = QVBoxLayout()
        input_col.addWidget(QLabel("Input:"))
        input_col.addWidget(self.input_text)
        output_col = QVBoxLayout()
        output_col.addWidget(QLabel("Output:"))
        output_col.addWidget(self.output_text)
        output_col.addWidget(self.copy_btn)
        io_layout = QHBoxLayout()
        io_layout.addLayout(input_col)
        io_layout.addLayout(output_col)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(settings_group)
        main_layout.addLayout(io_layout)

    def update_output(self):
        """修正后的输出更新方法"""
        try:
            input_data = self.input_text.toPlainText()
            hex_values = self.extract_hex_values(input_data)

            formatted = []
            for i, hex_str in enumerate(hex_values):
                # 通过.real_widget访问实际控件值
                if self.letter_case.real_widget.currentText() == "Upper":
                    hex_str = hex_str.upper()
                else:
                    hex_str = hex_str.lower()

                if self.include_prefix.real_widget.isChecked():
                    hex_str = f"0x{hex_str}"

                formatted.append(hex_str)

                if (i + 1) % self.bytes_per_line.real_widget.value() == 0 and i != len(hex_values) - 1:
                    formatted.append("\n")
                elif i != len(hex_values) - 1:
                    formatted.append(self.separator.real_widget.text())

            self.output_text.setPlainText(''.join(formatted))
        except Exception as e:
            print(f"更新输出时出错: {e}")

    def extract_hex_values(self, text):
        hex_values = []
        pattern = r'(0x[0-9a-fA-F]{2}|[0-9a-fA-F]{2})'
        for match in re.finditer(pattern, text):
            hex_str = match.group().lower().replace('0x', '')
            if len(hex_str) == 2:
                hex_values.append(hex_str)
        return hex_values

    def copy_output(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())


class HexToolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Louis Hex Data Handle Tool v1.0")
        self.setGeometry(100, 100, 1000, 600)

        # Create tab widget
        self.tabs = QTabWidget()
        self.compare_tab = HexCompareWidget()
        self.format_tab = HexFormatWidget()

        self.tabs.addTab(self.compare_tab, "Hex Compare")
        self.tabs.addTab(self.format_tab, "Hex Format")

        self.setCentralWidget(self.tabs)

        # Set font
        font = QFont("Courier New", 10)
        self.compare_tab.left_text.setFont(font)
        self.compare_tab.right_text.setFont(font)
        self.format_tab.input_text.setFont(font)
        self.format_tab.output_text.setFont(font)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = HexToolApp()
    ex.show()
    sys.exit(app.exec_())
