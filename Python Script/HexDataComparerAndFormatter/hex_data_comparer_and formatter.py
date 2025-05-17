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

        self.default_left_color = QColor(101, 165, 255)
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
            left_mismatches, right_mismatches = self.find_mismatches(left_text, right_text)
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
            left_only = {d['normalized'] for d in left_data} - {d['normalized'] for d in right_data}
            right_only = {d['normalized'] for d in right_data} - {d['normalized'] for d in left_data}
            
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
                    right_mismatches.append((right_data[i][0], right_data[i][1]))
        
        return left_mismatches, right_mismatches

class HexFormatWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Settings group
        settings_group = QGroupBox("Format Settings")
        settings_layout = QHBoxLayout()
        
        self.include_prefix = QCheckBox("Include 0x prefix")
        self.include_prefix.setChecked(True)
        self.include_prefix.stateChanged.connect(self.update_output)
        settings_layout.addWidget(self.include_prefix)
        
        self.letter_case = QComboBox()
        self.letter_case.addItems(["Uppercase", "Lowercase"])
        self.letter_case.currentIndexChanged.connect(self.update_output)
        settings_layout.addWidget(self.letter_case)
        
        settings_layout.addWidget(QLabel("Separator:"))
        self.separator = QLineEdit(" ")
        self.separator.setMaximumWidth(30)
        self.separator.textChanged.connect(self.update_output)
        settings_layout.addWidget(self.separator)
        
        settings_layout.addWidget(QLabel("Bytes per line:"))
        self.bytes_per_line = QSpinBox()
        self.bytes_per_line.setRange(1, 100)
        self.bytes_per_line.setValue(16)
        self.bytes_per_line.valueChanged.connect(self.update_output)
        settings_layout.addWidget(self.bytes_per_line)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Text areas
        text_layout = QHBoxLayout()
        
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Input:"))
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter hex data to convert...")
        self.input_text.textChanged.connect(self.update_output)
        input_layout.addWidget(self.input_text)
        
        output_layout = QVBoxLayout()
        output_layout.addWidget(QLabel("Output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_output)
        output_layout.addWidget(self.copy_btn)
        
        text_layout.addLayout(input_layout)
        text_layout.addLayout(output_layout)
        layout.addLayout(text_layout)
        
        self.setLayout(layout)
        
    def update_output(self):
        input_data = self.input_text.toPlainText()
        hex_values = self.extract_hex_values(input_data)
        
        # Apply formatting
        formatted = []
        for i, hex_str in enumerate(hex_values):
            # Apply case
            if self.letter_case.currentText() == "Uppercase":
                hex_str = hex_str.upper()
            else:
                hex_str = hex_str.lower()
                
            # Add prefix
            if self.include_prefix.isChecked():
                hex_str = f"0x{hex_str}"
                
            formatted.append(hex_str)
            
            # Add line breaks
            if (i + 1) % self.bytes_per_line.value() == 0 and i != len(hex_values) - 1:
                formatted.append("\n")
            elif i != len(hex_values) - 1:
                formatted.append(self.separator.text())
        
        self.output_text.setPlainText(''.join(formatted))
        
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
        self.setWindowTitle("Hex Data Tool")
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

def excepthook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
    QApplication.quit()



if __name__ == '__main__':
    sys.excepthook = excepthook
    app = QApplication(sys.argv)
    ex = HexToolApp()
    ex.show()
    sys.exit(app.exec_())