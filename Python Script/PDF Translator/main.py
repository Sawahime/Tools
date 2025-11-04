import sys
import os
import fitz  # PyMuPDF
from googletrans import Translator
from langdetect import detect
import pytesseract
from PIL import Image
import io

from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit,
                             QProgressBar, QFileDialog, QMessageBox, QWidget,
                             QGroupBox, QCheckBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent


class TranslationThread(QThread):
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, pdf_path, target_lang, use_ocr=False):
        super().__init__()
        self.pdf_path = pdf_path
        self.target_lang = target_lang
        self.use_ocr = use_ocr
        self.translator = Translator()
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def detect_pdf_language(self, doc):
        """检测PDF的语言"""
        try:
            # 从第一页提取文本进行语言检测
            text_sample = ""
            for page_num in range(min(3, len(doc))):  # 检查前3页
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_sample += text[:500]  # 取前500个字符
                    break

            if text_sample:
                return detect(text_sample)
            return 'en'  # 默认英语
        except:
            return 'en'

    def extract_text_with_ocr(self, page):
        """使用OCR提取文本"""
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 提高分辨率
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(image, lang='eng+chi_sim')
            return text
        except Exception as e:
            return f"OCR Error: {str(e)}"

    def run(self):
        try:
            # 打开PDF文件
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)

            # 检测源语言
            self.status_updated.emit("检测PDF语言...")
            source_lang = self.detect_pdf_language(doc)
            self.status_updated.emit(f"检测到源语言: {source_lang}")

            # 创建新的PDF文档
            new_doc = fitz.open()

            # 处理书签
            toc = doc.get_toc()
            new_toc = []

            for page_num in range(total_pages):
                if self.cancelled:
                    break

                self.status_updated.emit(f"处理第 {page_num + 1}/{total_pages} 页...")

                # 获取当前页
                page = doc[page_num]

                # 提取文本
                if self.use_ocr:
                    text_blocks = self.extract_text_with_ocr(page)
                else:
                    text_blocks = page.get_text("dict")

                # 创建新页面
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

                if self.use_ocr:
                    # OCR模式的处理（这里简化处理，实际需要更复杂的文本定位）
                    if text_blocks and not text_blocks.startswith("OCR Error"):
                        try:
                            # 翻译文本
                            translated_text = self.translator.translate(
                                text_blocks, src=source_lang, dest=self.target_lang
                            ).text

                            # 在页面上添加翻译后的文本（简化处理）
                            new_page.insert_text((50, 50), translated_text[:1000])  # 限制文本长度
                        except Exception as e:
                            new_page.insert_text((50, 50), f"翻译错误: {str(e)}")
                else:
                    # 正常PDF文本处理
                    for block in text_blocks["blocks"]:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    original_text = span["text"]
                                    if original_text.strip():
                                        try:
                                            # 翻译文本
                                            translated_text = self.translator.translate(
                                                original_text, src=source_lang, dest=self.target_lang
                                            ).text

                                            # 保持原有格式
                                            new_page.insert_text(
                                                span["origin"],
                                                translated_text,
                                                fontsize=span["size"],
                                                fontname=span["font"],
                                                color=span["color"]
                                            )
                                        except Exception as e:
                                            # 如果翻译失败，保留原文
                                            new_page.insert_text(
                                                span["origin"],
                                                original_text,
                                                fontsize=span["size"],
                                                fontname=span["font"],
                                                color=span["color"]
                                            )

                # 更新进度
                progress = int((page_num + 1) / total_pages * 100)
                self.progress_updated.emit(progress)

            if not self.cancelled:
                # 添加书签
                for item in toc:
                    level, title, page_num = item
                    new_toc.append([level, title, page_num])

                new_doc.set_toc(new_toc)

                # 保存文件
                output_path = self.pdf_path.replace('.pdf', f'_translated_{self.target_lang}.pdf')
                new_doc.save(output_path)
                new_doc.close()
                doc.close()

                self.finished_signal.emit(output_path)
                self.status_updated.emit("翻译完成！")

        except Exception as e:
            self.error_occurred.emit(str(e))


class PDFTranslatorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translation_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('PDF翻译工具')
        self.setGeometry(100, 100, 800, 600)

        # 中心窗口
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 设置接受拖放
        self.setAcceptDrops(True)

        # 文件选择区域
        file_group = QGroupBox("PDF文件选择")
        file_layout = QVBoxLayout()

        # 拖放区域
        self.drop_label = QLabel("拖放PDF文件到这里，或使用下方按钮选择文件")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                background-color: #f9f9f9;
                font-size: 14px;
                color: #666;
            }
            QLabel:hover {
                background-color: #f0f0f0;
                border-color: #999;
            }
        """)
        self.drop_label.setMinimumHeight(120)
        file_layout.addWidget(self.drop_label)

        # 文件路径输入
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入PDF文件路径，或使用浏览按钮选择文件...")
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.browse_file)

        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_btn)
        file_layout.addLayout(path_layout)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 翻译设置区域
        settings_group = QGroupBox("翻译设置")
        settings_layout = QVBoxLayout()

        # OCR选项
        ocr_layout = QHBoxLayout()
        self.ocr_checkbox = QCheckBox("使用OCR处理扫描版PDF（速度较慢）")
        ocr_layout.addWidget(self.ocr_checkbox)
        ocr_layout.addStretch()
        settings_layout.addLayout(ocr_layout)

        # 语言选择
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("目标语言:"))

        self.target_lang_combo = QComboBox()
        self.target_lang_combo.addItems([
            "中文 (zh-cn)", "英语 (en)", "日语 (ja)", "韩语 (ko)",
            "法语 (fr)", "德语 (de)", "西班牙语 (es)", "俄语 (ru)"
        ])
        lang_layout.addWidget(self.target_lang_combo)
        lang_layout.addStretch()

        settings_layout.addLayout(lang_layout)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # 控制按钮
        btn_layout = QHBoxLayout()
        self.translate_btn = QPushButton("开始翻译")
        self.translate_btn.clicked.connect(self.start_translation)
        self.translate_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; padding: 8px; }")

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_translation)
        self.cancel_btn.setEnabled(False)

        btn_layout.addWidget(self.translate_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态显示
        self.status_label = QLabel("准备就绪")
        layout.addWidget(self.status_label)

        # 日志显示
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.path_edit.setText(file_path)
                self.log_text.append(f"已选择文件: {file_path}")
            else:
                QMessageBox.warning(self, "错误", "请选择PDF文件")

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择PDF文件", "", "PDF文件 (*.pdf)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            self.log_text.append(f"已选择文件: {file_path}")

    def start_translation(self):
        pdf_path = self.path_edit.text().strip()

        if not pdf_path:
            QMessageBox.warning(self, "错误", "请选择PDF文件")
            return

        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        # 获取目标语言代码
        lang_map = {
            "中文 (zh-cn)": "zh-cn",
            "英语 (en)": "en",
            "日语 (ja)": "ja",
            "韩语 (ko)": "ko",
            "法语 (fr)": "fr",
            "德语 (de)": "de",
            "西班牙语 (es)": "es",
            "俄语 (ru)": "ru"
        }
        target_lang = lang_map[self.target_lang_combo.currentText()]
        use_ocr = self.ocr_checkbox.isChecked()

        # 禁用界面
        self.translate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 开始翻译线程
        self.translation_thread = TranslationThread(pdf_path, target_lang, use_ocr)
        self.translation_thread.progress_updated.connect(self.progress_bar.setValue)
        self.translation_thread.status_updated.connect(self.status_label.setText)
        self.translation_thread.status_updated.connect(self.log_text.append)
        self.translation_thread.finished_signal.connect(self.translation_finished)
        self.translation_thread.error_occurred.connect(self.translation_error)
        self.translation_thread.start()

    def cancel_translation(self):
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.cancel()
            self.status_label.setText("正在取消...")

    def translation_finished(self, output_path):
        self.translate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.information(self, "完成", f"翻译完成！\n输出文件: {output_path}")

    def translation_error(self, error_msg):
        self.translate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(self, "错误", f"翻译过程中发生错误:\n{error_msg}")


def main():
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    window = PDFTranslatorApp()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
