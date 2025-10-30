import sys
import os
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
                             QFileDialog, QSpinBox, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QGroupBox, QSplitter, QProgressBar)
from PyQt5.QtCore import Qt, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
import fitz  # PyMuPDF


class DraggableFileWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 文件拖放区域
        self.drop_label = QLabel("拖放PDF文件到这里\n或点击浏览选择文件")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 20px;
                background-color: #f9f9f9;
                font-size: 14px;
            }
            QLabel:hover {
                border: 2px dashed #0078d4;
                background-color: #f0f8ff;
            }
        """)
        self.drop_label.setMinimumHeight(100)

        # 文件路径输入
        path_layout = QHBoxLayout()
        self.path_label = QLabel("文件路径:")
        self.path_input = QLineEdit()
        self.browse_btn = QPushButton("浏览")

        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)

        layout.addWidget(self.drop_label)
        layout.addLayout(path_layout)

        self.setLayout(layout)

        # 连接信号
        self.browse_btn.clicked.connect(self.browse_file)
        self.path_input.textChanged.connect(self.on_path_changed)

        # 启用拖放
        self.setAcceptDrops(True)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)"
        )
        if file_path:
            self.path_input.setText(file_path)

    def on_path_changed(self, text):
        if hasattr(self.parent, 'update_file_info'):
            self.parent.update_file_info(text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.path_input.setText(file_path)
                event.acceptProposedAction()
            else:
                QMessageBox.warning(self, "错误", "请选择PDF文件")


class BookmarkGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_file = None

    def initUI(self):
        self.setWindowTitle("PDF书签生成器")
        self.setGeometry(100, 100, 1000, 700)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout()

        # 文件选择模块
        file_group = QGroupBox("1. 选择PDF文件")
        file_layout = QVBoxLayout()
        self.file_widget = DraggableFileWidget(self)
        file_layout.addWidget(self.file_widget)
        file_group.setLayout(file_layout)

        # 目录输入模块
        toc_group = QGroupBox("2. 输入目录和设置")
        toc_layout = QVBoxLayout()

        # 页码偏移设置
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("页码偏移量:"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(-1000, 1000)
        self.offset_spin.setValue(0)
        self.offset_spin.setToolTip("PDF页码 = 目录页码 + 偏移量")
        offset_layout.addWidget(self.offset_spin)
        offset_layout.addStretch()

        # 目录输入框
        self.toc_input = QTextEdit()
        self.toc_input.setPlaceholderText(
            "请输入目录，格式如下：\n"
            "第1章 Hello World驱动 1\n"
            "1.1从Hello World开始 2\n"
            "1.1.1 HelloDRIVER 4\n"
            "1.1.2代码解释 8\n"
            "..."
        )
        self.toc_input.setMinimumHeight(150)

        toc_layout.addLayout(offset_layout)
        toc_layout.addWidget(QLabel("目录内容:"))
        toc_layout.addWidget(self.toc_input)
        toc_group.setLayout(toc_layout)

        # 目录预览模块
        preview_group = QGroupBox("3. 目录预览")
        preview_layout = QVBoxLayout()

        # 预览树形控件
        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderLabels(["标题", "页码"])
        self.toc_tree.setColumnWidth(0, 400)

        # 按钮
        btn_layout = QHBoxLayout()
        self.parse_btn = QPushButton("解析目录")
        self.generate_btn = QPushButton("生成书签")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        btn_layout.addWidget(self.parse_btn)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.progress_bar)

        preview_layout.addWidget(self.toc_tree)
        preview_layout.addLayout(btn_layout)
        preview_group.setLayout(preview_layout)

        # 添加到主布局
        main_layout.addWidget(file_group)
        main_layout.addWidget(toc_group)
        main_layout.addWidget(preview_group)

        central_widget.setLayout(main_layout)

        # 连接信号
        self.parse_btn.clicked.connect(self.parse_toc)
        self.generate_btn.clicked.connect(self.generate_bookmarks)

    def update_file_info(self, file_path):
        if os.path.exists(file_path) and file_path.lower().endswith('.pdf'):
            self.current_file = file_path
        else:
            self.current_file = None

    def parse_toc(self):
        """解析目录文本"""
        toc_text = self.toc_input.toPlainText().strip()
        if not toc_text:
            QMessageBox.warning(self, "错误", "请输入目录内容")
            return

        # 清空之前的预览
        self.toc_tree.clear()

        try:
            # 解析目录
            bookmarks = self._parse_toc_text(toc_text)

            # 构建树形结构
            self._build_toc_tree(bookmarks)

            QMessageBox.information(self, "成功", f"成功解析 {len(bookmarks)} 个目录项")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"解析目录时出错: {str(e)}")

    def _parse_toc_text(self, toc_text):
        """解析目录文本为结构化数据"""
        lines = toc_text.split('\n')
        bookmarks = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 匹配标题和页码
            # 使用正则表达式匹配：标题 + 空格 + 数字（页码）
            match = re.match(r'^(.*?)\s+(\d+)$', line)
            if match:
                title = match.group(1).strip()
                page_num = int(match.group(2))
                bookmarks.append((title, page_num))
            else:
                # 如果没有找到页码，尝试其他匹配模式
                match = re.match(r'^(.*?)(\d+)$', line)
                if match:
                    title = match.group(1).strip()
                    page_num = int(match.group(2))
                    bookmarks.append((title, page_num))
                else:
                    # 如果还是无法匹配，将整行作为标题，页码设为0
                    bookmarks.append((line, 0))

        return bookmarks

    def _build_toc_tree(self, bookmarks):
        """构建树形预览"""
        root_items = []
        stack = []  # 用于跟踪层级关系

        for title, page_num in bookmarks:
            # 计算层级（通过标题的格式判断）
            level = self._get_toc_level(title)

            # 创建树节点
            item = QTreeWidgetItem([title, str(page_num)])

            # 根据层级关系添加到树中
            if level == 0:
                root_items.append(item)
                stack = [(item, 0)]  # 重置栈，存储(item, level)
            else:
                # 找到合适的父节点
                while stack and stack[-1][1] >= level:
                    stack.pop()

                if stack:
                    parent = stack[-1][0]
                    parent.addChild(item)

                # 更新栈
                stack.append((item, level))

        # 添加到树控件
        self.toc_tree.insertTopLevelItems(0, root_items)
        self.toc_tree.expandAll()

    def _get_toc_level(self, title):
        """根据标题判断层级"""
        # 匹配常见的层级格式
        title_clean = title.strip()

        # 章级别 - 第X章
        if re.match(r'^第[零一二三四五六七八九十百千]+章', title_clean):
            return 0
        # 附录、参考文献等
        elif re.match(r'^(附录|参考文献|索引|致谢|前言|目录)', title_clean):
            return 0
        # 三级标题 - X.X.X
        elif re.match(r'^\d+\.\d+\.\d+', title_clean):
            return 2
        # 二级标题 - X.X
        elif re.match(r'^\d+\.\d+', title_clean):
            return 1
        # 一级标题 - X
        elif re.match(r'^\d+$', title_clean.split()[0] if title_clean.split() else ''):
            return 0
        else:
            # 默认根据缩进判断（如果有空格缩进）
            leading_spaces = len(title) - len(title.lstrip())
            if leading_spaces >= 4:
                return 2
            elif leading_spaces >= 2:
                return 1
            else:
                return 0

    def generate_bookmarks(self):
        """生成PDF书签"""
        if not self.current_file:
            QMessageBox.warning(self, "错误", "请先选择PDF文件")
            return

        if self.toc_tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "错误", "请先解析目录")
            return

        try:
            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # 打开PDF文件
            pdf_document = fitz.open(self.current_file)

            # 获取偏移量
            offset = self.offset_spin.value()

            # 准备书签数据 - 修复层级问题
            toc_data = []
            self._collect_toc_data(self.toc_tree.invisibleRootItem(), toc_data, offset, 1)  # 从层级1开始

            # 验证并修复书签数据
            toc_data = self._validate_toc_data(toc_data)

            # 设置书签
            pdf_document.set_toc(toc_data)

            # 保存文件
            output_file = self._get_output_filename()
            pdf_document.save(output_file)
            pdf_document.close()

            self.progress_bar.setValue(100)
            QMessageBox.information(self, "成功", f"书签生成完成！\n输出文件: {output_file}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成书签时出错: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def _collect_toc_data(self, parent_item, toc_data, offset, level):
        """从树控件收集书签数据"""
        for i in range(parent_item.childCount()):
            item = parent_item.child(i)
            title = item.text(0)
            page_num = int(item.text(1)) + offset

            # 确保页码在有效范围内
            page_num = max(0, page_num)

            # 创建书签条目
            bookmark = [level, title, page_num]
            toc_data.append(bookmark)

            # 递归处理子项
            if item.childCount() > 0:
                self._collect_toc_data(item, toc_data, offset, level + 1)

    def _validate_toc_data(self, toc_data):
        """验证和修复书签数据"""
        if not toc_data:
            return toc_data

        # 确保第一个项目的层级是1
        if toc_data[0][0] != 1:
            # 调整所有层级的基准
            base_level = toc_data[0][0]
            for i in range(len(toc_data)):
                toc_data[i][0] = toc_data[i][0] - base_level + 1

        # 确保层级是连续的
        prev_level = 1
        for i in range(len(toc_data)):
            current_level = toc_data[i][0]
            # 如果层级跳跃超过1，进行调整
            if current_level > prev_level + 1:
                toc_data[i][0] = prev_level + 1
            prev_level = toc_data[i][0]

        return toc_data

    def _get_output_filename(self):
        """生成输出文件名"""
        base_name = os.path.splitext(self.current_file)[0]
        return f"{base_name}_with_bookmarks.pdf"


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    generator = BookmarkGenerator()
    generator.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
