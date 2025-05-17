import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QWidget, QMessageBox, 
                             QGroupBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyPDF2 import PdfReader, PdfWriter

class DropArea(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("拖放PDF文件到这里")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 20px;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #777;
            }
        """)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.fileDropped.emit(file_path)

class PDFCropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF裁剪工具")
        self.setGeometry(100, 100, 500, 400)
        
        self.initUI()
        self.current_file = None
        self.total_pages = 0

    def initUI(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 文件选择部分
        file_group = QGroupBox("PDF文件选择")
        file_layout = QVBoxLayout()
        
        self.drop_area = DropArea()
        self.drop_area.fileDropped.connect(self.load_pdf)
        file_layout.addWidget(self.drop_area)
        
        browse_btn = QPushButton("浏览文件")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        self.file_path_label = QLabel("未选择文件")
        self.file_path_label.setWordWrap(True)
        file_layout.addWidget(self.file_path_label)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 页面信息部分
        info_group = QGroupBox("PDF信息")
        info_layout = QHBoxLayout()
        
        self.page_info_label = QLabel("总页数: 0")
        info_layout.addWidget(self.page_info_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # 裁剪设置部分
        crop_group = QGroupBox("裁剪设置")
        crop_layout = QVBoxLayout()
        
        # 起始页和结束页
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("起始页:"))
        
        self.start_page = QSpinBox()
        self.start_page.setMinimum(1)
        self.start_page.setMaximum(1)
        page_layout.addWidget(self.start_page)
        
        page_layout.addWidget(QLabel("结束页:"))
        
        self.end_page = QSpinBox()
        self.end_page.setMinimum(1)
        self.end_page.setMaximum(1)
        page_layout.addWidget(self.end_page)
        
        crop_layout.addLayout(page_layout)
        
        # 保存路径
        save_layout = QHBoxLayout()
        save_layout.addWidget(QLabel("保存路径:"))
        
        self.save_path = QLineEdit(os.path.expanduser("~/Desktop"))
        save_layout.addWidget(self.save_path)
        
        browse_save_btn = QPushButton("浏览")
        browse_save_btn.clicked.connect(self.browse_save_path)
        save_layout.addWidget(browse_save_btn)
        
        crop_layout.addLayout(save_layout)
        
        # 裁剪按钮
        self.crop_btn = QPushButton("裁剪PDF")
        self.crop_btn.clicked.connect(self.crop_pdf)
        self.crop_btn.setEnabled(False)
        crop_layout.addWidget(self.crop_btn)
        
        crop_group.setLayout(crop_layout)
        main_layout.addWidget(crop_group)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)"
        )
        if file_path:
            self.load_pdf(file_path)
    
    def load_pdf(self, file_path):
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                self.total_pages = len(reader.pages)
                
                self.current_file = file_path
                self.file_path_label.setText(file_path)
                self.page_info_label.setText(f"总页数: {self.total_pages}")
                
                self.start_page.setMaximum(self.total_pages)
                self.end_page.setMaximum(self.total_pages)
                self.start_page.setValue(1)
                self.end_page.setValue(self.total_pages)
                
                self.crop_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载PDF文件:\n{str(e)}")
    
    def browse_save_path(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.save_path.text()
        )
        if dir_path:
            self.save_path.setText(dir_path)
    
    def crop_pdf(self):
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先选择PDF文件")
            return
        
        start = self.start_page.value()
        end = self.end_page.value()
        
        if start > end:
            QMessageBox.warning(self, "警告", "起始页不能大于结束页")
            return
        
        try:
            # 读取原始PDF
            with open(self.current_file, 'rb') as input_file:
                reader = PdfReader(input_file)
                writer = PdfWriter()
                
                # 添加选定的页面范围
                for page_num in range(start-1, end):
                    writer.add_page(reader.pages[page_num])
                
                # 保留原始文档的元数据和书签
                writer.clone_reader_document_root(reader)
                
                # 生成输出文件名
                base_name = os.path.splitext(os.path.basename(self.current_file))[0]
                output_file = os.path.join(
                    self.save_path.text(),
                    f"{base_name}_裁剪_页{start}-{end}.pdf"
                )
                
                # 确保目录存在
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                # 写入新PDF
                with open(output_file, 'wb') as output:
                    writer.write(output)
                
                QMessageBox.information(
                    self, "完成", 
                    f"PDF裁剪完成!\n保存到: {output_file}"
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"裁剪PDF时出错:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFCropper()
    window.show()
    sys.exit(app.exec_())