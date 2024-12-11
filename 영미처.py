import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QFileDialog, QLabel, QVBoxLayout, 
    QWidget, QColorDialog, QSlider, QHBoxLayout, QPushButton, QGridLayout, QMessageBox
)
from PyQt5.QtCore import QTranslator, QLocale, QLibraryInfo
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QComboBox,QSpinBox, QLineEdit, QDialog
from PyQt5.QtGui import QCursor
from PIL import Image, ImageDraw, ImageFont


class ImageEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image = np.ones((700, 900, 3), dtype=np.uint8) * 255  # 기본 흰 캔버스
        self.brush_color = (0, 0, 0)  # 브러쉬 색상 (BGR)
        self.brush_size = 5  # 브러쉬 크기
        self.last_point = None
        self.tool_mode = "brush"  # 기본 도구 모드
        self.drawing_path = []  # 그리기 경로 저장
        self.filling = False
        self.image_loaded = False  # 이미지 로딩 상태
        self.history = []  # 작업 히스토리 리스트
        self.history_index = -1  # 히스토리 인덱스 초기화
        self.zoom_mode = False  # 확대/축소 모드
        self.zoom_factor = 1.1  # 확대/축소 비율
        self.text_mode = False  # 텍스트 모드 상태
        self.font_face = 0  # 기본 글꼴
        self.font_size = 20  # 기본 글꼴 크기
        self.text_position = None  # 텍스트 입력 위치
        self.current_shape = None
        self.start_point = None
        self.end_point = None
        self.lens_mode = False
        self.initUI()

    def add_to_history(self):
        # 현재 상태를 작업 히스토리에 추가
        if len(self.history) > self.history_index + 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(self.image.copy())
        self.history_index += 1

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.image = self.history[self.history_index].copy()
            self.display_image()

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.image = self.history[self.history_index].copy()
            self.display_image()


    def initUI(self):
        self.setWindowTitle("이미지 편집기 - 2020E7307")
        self.setGeometry(100, 100, 1000, 800)
        self.setFixedSize(1000, 800)

        # 메뉴바
        menubar = self.menuBar()
        file_menu = menubar.addMenu("파일")
        help_menu = menubar.addMenu("도움말")

        open_action = QAction("열기", self)
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)

        save_action = QAction("다른 이름으로 저장", self)
        save_action.triggered.connect(self.save_image)
        file_menu.addAction(save_action)

        reset_action = QAction("새 캔버스", self)
        reset_action.triggered.connect(self.reset_canvas)
        file_menu.addAction(reset_action)

        exit_action = QAction("종료", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        about_action = QAction("프로그램 정보", self)
        about_action.triggered.connect(self.show_about_popup)
        help_menu.addAction(about_action)

        # Undo/Redo 단축키
        undo_action = QAction("되돌리기", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self.undo)
        self.addAction(undo_action)

        redo_action = QAction("다시 실행", self)
        redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        redo_action.triggered.connect(self.redo)
        self.addAction(redo_action)

        # 메인 레이아웃
        central_widget = QWidget()
        main_layout = QHBoxLayout()

        # 왼쪽 도구 레이아웃
        tool_layout = QGridLayout()

        self.color_button = QPushButton()
        self.color_button.setStyleSheet("background-color: black; border: 1px solid black;")
        self.color_button.clicked.connect(self.select_brush_color)
        tool_layout.addWidget(self.color_button, 0, 0)

        self.brush_button = QPushButton("그리기🖊️")
        self.brush_button.clicked.connect(self.set_brush_mode)
        tool_layout.addWidget(self.brush_button, 1, 0)

        self.eraser_button = QPushButton("지우개")
        self.eraser_button.clicked.connect(self.set_eraser_mode)
        tool_layout.addWidget(self.eraser_button, 2, 0)

        self.paint_button = QPushButton("페인트🪣")
        self.paint_button.clicked.connect(self.set_fill_mode)
        tool_layout.addWidget(self.paint_button, 3, 0)

        self.blur_button = QPushButton("블러 처리")
        self.blur_button.clicked.connect(self.apply_blur)
        tool_layout.addWidget(self.blur_button, 4, 0)

        self.invert_button = QPushButton("색 반전")
        self.invert_button.clicked.connect(self.apply_color_inversion)
        tool_layout.addWidget(self.invert_button, 5, 0)

        self.zoom_button = QPushButton("확대/축소")
        self.zoom_button.clicked.connect(self.set_zoom_mode)
        tool_layout.addWidget(self.zoom_button, 6, 0)

        self.text_button = QPushButton("텍스트")
        self.text_button.clicked.connect(self.set_text_mode)
        tool_layout.addWidget(self.text_button, 7, 0)

        self.rotate_button = QPushButton("회전")
        self.rotate_button.clicked.connect(self.set_rotate_mode)
        tool_layout.addWidget(self.rotate_button, 8, 0)

        self.diagram_button = QPushButton("도형")
        self.diagram_button.clicked.connect(self.set_diagram_mode)
        tool_layout.addWidget(self.diagram_button, 9, 0)

        self.perspective_button = QPushButton("원근 변환")
        self.perspective_button.clicked.connect(self.apply_perspective_transform)
        self.perspective_button.setEnabled(False)  # 초기에는 비활성화
        tool_layout.addWidget(self.perspective_button, 10, 0)

        self.grayscale_button = QPushButton("흑백 변환")
        self.grayscale_button.clicked.connect(self.apply_grayscale)
        self.grayscale_button.setEnabled(False)  # 초기에는 비활성화
        tool_layout.addWidget(self.grayscale_button, 11, 0)

        self.radial_distortion_button = QPushButton("렌즈왜곡")
        self.radial_distortion_button.clicked.connect(self.set_lens_mode)
        tool_layout.addWidget(self.radial_distortion_button, 12, 0)

        self.auto_correction_button = QPushButton("자동보정")
        self.auto_correction_button.clicked.connect(self.apply_auto_correction)
        tool_layout.addWidget(self.auto_correction_button, 13, 0)

        self.reprojection_button = QPushButton("역투영")
        self.reprojection_button.clicked.connect(self.apply_reprojection)
        tool_layout.addWidget(self.reprojection_button, 14, 0)

        self.composite_button = QPushButton("합성")
        self.composite_button.clicked.connect(self.composite_images)
        tool_layout.addWidget(self.composite_button, 15, 0)

        self.threshold_button = QPushButton("스레시홀드", self)
        self.threshold_button.clicked.connect(self.apply_threshold)
        tool_layout.addWidget(self.threshold_button, 16, 0)

        tool_layout.setAlignment(Qt.AlignTop)
        main_layout.addLayout(tool_layout)

        # 오른쪽 메인 영역
        right_layout = QVBoxLayout()

        # 상단 슬라이더 영역
        self.slider_layout = QHBoxLayout()

        # "브러쉬 크기:" 라벨 참조 추가
        self.brush_size_text_label = QLabel("브러쉬 크기:")
        self.brush_size_text_label.setFixedHeight(20)
        self.slider_layout.addWidget(self.brush_size_text_label)

        # 슬라이더 추가
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setValue(self.brush_size)
        self.slider.valueChanged.connect(self.update_brush_size)
        self.slider.setFixedHeight(23)
        self.slider_layout.addWidget(self.slider)

        # 브러쉬 크기 라벨 추가
        self.brush_size_label = QLabel(f"{self.brush_size}px")
        self.slider_layout.addWidget(self.brush_size_label)
        self.brush_size_label.setFixedHeight(23)  # 높이 고정

        right_layout.addLayout(self.slider_layout)

        # 텍스트 설정 영역 (초기에는 숨김)
        self.font_label = QLabel("글꼴:")
        self.font_label.setFixedHeight(23)
        self.font_combo = QComboBox()
        self.font_combo.setFixedHeight(23)
        self.font_combo.addItems(["SIMPLEX", "COMPLEX", "DUPLEX", "COMPLEX|I"])
        self.font_combo.currentIndexChanged.connect(self.update_font)
        right_layout.addWidget(self.font_label)
        right_layout.addWidget(self.font_combo)

        self.font_size_label = QLabel("글꼴 크기:")
        self.font_size_label.setFixedHeight(23)
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setFixedHeight(23)
        self.font_size_spinbox.setValue(self.font_size)
        self.font_size_spinbox.setMinimum(5)
        self.font_size_spinbox.setMaximum(100)
        self.font_size_spinbox.valueChanged.connect(self.update_font_size)
        right_layout.addWidget(self.font_size_label)
        right_layout.addWidget(self.font_size_spinbox)

        self.text_input_field = QLineEdit()
        self.text_input_field.setFixedHeight(23)
        self.text_input_field.setPlaceholderText("텍스트 입력")
        right_layout.addWidget(self.text_input_field)

        # 초기 숨김 설정
        self.font_label.setVisible(False)
        self.font_combo.setVisible(False)
        self.font_size_label.setVisible(False)
        self.font_size_spinbox.setVisible(False)
        self.text_input_field.setVisible(False)

        # 회전 설정 영역 (초기 숨김)
        self.rotate_ccw_button = QPushButton("🔄️")
        self.rotate_ccw_button.clicked.connect(self.rotate_counter_clockwise)
        self.rotate_ccw_button.setFixedWidth(30)
        self.rotate_ccw_button.setFixedHeight(23)
        self.rotate_ccw_button.setVisible(False)

        self.rotate_cw_button = QPushButton("🔃")
        self.rotate_cw_button.clicked.connect(self.rotate_clockwise)
        self.rotate_cw_button.setFixedWidth(30)
        self.rotate_cw_button.setFixedHeight(23)
        self.rotate_cw_button.setVisible(False)

        self.label_rotate_ccw = QLabel("반시계")
        self.label_rotate_ccw.setFixedHeight(23)
        self.label_rotate_ccw.setFixedWidth(35)
        self.label_rotate_ccw.setVisible(False)
        self.label_separator = QLabel("|")
        self.label_separator.setFixedHeight(23)
        self.label_separator.setFixedWidth(10)
        self.label_separator.setVisible(False)
        self.label_rotate_cw = QLabel("시계")
        self.label_rotate_cw.setFixedHeight(23)
        self.label_rotate_cw.setFixedWidth(35)
        self.label_rotate_cw.setVisible(False)

        self.slider_layout.addWidget(self.label_rotate_ccw, 0)
        self.slider_layout.addWidget(self.rotate_ccw_button, 1)
        self.slider_layout.addWidget(self.label_separator, 2)
        self.slider_layout.addWidget(self.label_rotate_cw, 3)
        self.slider_layout.addWidget(self.rotate_cw_button, 4)



        self.rectangle_button = QPushButton('□')
        self.rectangle_button.setFixedHeight(23)
        self.rectangle_button.setVisible(False)
        self.circle_button = QPushButton('○')
        self.circle_button.setFixedHeight(23)
        self.circle_button.setVisible(False)
        self.triangle_button = QPushButton('△')
        self.triangle_button.setFixedHeight(23)
        self.triangle_button.setVisible(False)

        self.rectangle_button.clicked.connect(lambda: self.select_shape('rectangle'))
        self.circle_button.clicked.connect(lambda: self.select_shape('circle'))
        self.triangle_button.clicked.connect(lambda: self.select_shape('triangle'))

        self.slider_layout.addWidget(self.rectangle_button)
        self.slider_layout.addWidget(self.circle_button)
        self.slider_layout.addWidget(self.triangle_button)

        # 캔버스 영역
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # 왼쪽 상단 정렬
        self.image_label.mousePressEvent = self.start_action
        self.image_label.mouseMoveEvent = self.draw
        self.image_label.mouseReleaseEvent = self.stop_action

        # 캔버스를 right_layout에 추가
        right_layout.addWidget(self.image_label)

        # 캔버스를 메인 레이아웃에 추가
        main_layout.addLayout(right_layout, stretch=1)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.display_image()

    def set_text_mode(self):
        self.unvisibleRotate()
        self.zoom_mode = False
        self.lens_mode = False
        self.hide_toolbars()
        self.reset_ui_for_brush_mode()
        """텍스트 모드 활성화"""
        self.text_mode = True
        self.tool_mode = "text"
        self.set_cursor(QCursor(Qt.IBeamCursor))  # 텍스트 모드 커서

        # 브러쉬 관련 컴포넌트 숨기기
        for widget in [self.brush_size_text_label, self.slider, self.brush_size_label]:
            widget.setVisible(False)

        # 텍스트 설정 UI 보이기
        self.font_label.setVisible(True)
        self.font_combo.setVisible(True)
        self.font_size_label.setVisible(True)
        self.font_size_spinbox.setVisible(True)
        self.text_input_field.setVisible(True)

        # 텍스트 설정 영역을 한 줄로 정렬
        self.slider_layout.addWidget(self.font_label)
        self.slider_layout.addWidget(self.font_combo)
        self.slider_layout.addWidget(self.font_size_label)
        self.slider_layout.addWidget(self.font_size_spinbox)
        self.slider_layout.addWidget(self.text_input_field)

        # 텍스트 버튼 활성화 표시
        self.text_button.setStyleSheet("background-color: lightblue;")

    # 기존 상단 영역 복구
    def reset_ui_for_brush_mode(self):
        # 기본 커서로 변경
        self.set_cursor(QCursor(Qt.ArrowCursor))  

        # 텍스트 관련 컴포넌트 숨기기
        for widget in [self.font_label, self.font_combo, self.font_size_label, 
                    self.font_size_spinbox, self.text_input_field]:
            widget.setVisible(False)

        # 브러쉬 관련 컴포넌트 보이기
        for widget in [self.brush_size_text_label, self.slider, self.brush_size_label]:
            widget.setVisible(True)

        # 텍스트 버튼 비활성화 표시
        self.text_button.setStyleSheet("background-color: none;")
        
        # 상단 슬라이더 영역 복구
        self.slider_layout.addWidget(self.brush_size_text_label)
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.brush_size_label)

    def update_font(self):
        """현재 설정에 따라 폰트를 업데이트"""
        font_choice = self.font_combo.currentText()

        # 선택한 기본 글꼴 설정
        if font_choice == "COMPLEX":
            self.font_face = cv2.FONT_HERSHEY_COMPLEX
        elif font_choice == "SIMPLEX":
            self.font_face = cv2.FONT_HERSHEY_SIMPLEX
        elif font_choice == "COMPLEX|I":
            self.font_face = cv2.FONT_HERSHEY_COMPLEX | cv2.FONT_ITALIC
        else:
            self.font_face = cv2.FONT_HERSHEY_DUPLEX


    def set_brush_mode(self):
        self.unvisibleRotate()
        self.hide_toolbars()
        self.text_mode = False
        self.tool_mode = "brush"
        self.filling = False
        self.reset_ui_for_brush_mode()
        self.zoom_mode = False
        self.lens_mode = False
        

    def set_cursor(self, cursor):
        self.setCursor(cursor)

    def update_font_size(self, value):
        self.font_size = value

    def add_text(self, position):
        text = self.text_input_field.text()
        if not text:  # 텍스트가 없으면 기본 텍스트 삽입
            text = "Hello"

        # 한글인지 영어인지 확인
        if any('\uac00' <= char <= '\ud7af' for char in text):
            pil_image = Image.fromarray(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image)

            try:
                font_path = "C:/Windows/Fonts/malgun.ttf"
                font = ImageFont.truetype(font_path, self.font_size)
            except IOError:
                font = ImageFont.load_default()


            # 텍스트 크기 및 색상 설정
            draw.text((position.x(), position.y()), text, font=font, fill=(self.brush_color[2], self.brush_color[1], self.brush_color[0]))

            # 수정된 이미지를 다시 OpenCV 배열로 변환
            self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        else:
            # 한글이 아닐 경우 cv2.putText() 사용
            font_scale = self.font_size / 20  # 글꼴 크기 비율에 맞게 font_scale 계산
            cv2.putText(self.image, text, (position.x(), position.y()), self.font_face, font_scale, 
                        (self.brush_color[2], self.brush_color[1], self.brush_color[0]), 2, cv2.LINE_AA)

        self.add_to_history()
        self.display_image()


    def toggle_zoom_mode(self):
        self.zoom_mode = not self.zoom_mode

    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "이미지 열기", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            data = np.fromfile(file_path, dtype=np.uint8)
            self.image = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if self.image is None:
                QMessageBox.critical(self, "오류", "이미지를 불러올 수 없습니다.")
                return
            self.image = cv2.resize(self.image, (900, 700),interpolation=cv2.INTER_CUBIC)
            self.image_loaded = True
            self.perspective_button.setEnabled(True)
            self.grayscale_button.setEnabled(True)
            self.add_to_history()
            self.display_image()

    def reset_canvas(self):
        self.image = np.ones((700, 900, 3), dtype=np.uint8) * 255
        self.image_loaded = False
        self.perspective_button.setEnabled(False)
        self.grayscale_button.setEnabled(False)
        self.add_to_history()
        self.display_image()

    def display_image(self):
        if self.image is not None:
            height, width, channel = self.image.shape
            bytes_per_line = channel * width
            q_image = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(q_image)

            # QLabel에 이미지를 표시
            self.image_label.setPixmap(pixmap)



    def update_brush_size(self, value):
        self.brush_size = value
        self.brush_size_label.setText(f"{value}px")

    def set_zoom_mode(self):
        self.tool_mode = "zoom"
        self.zoom_mode = True

    def set_lens_mode(self):
        self.tool_mode = "lens"
        self.lens_mode = True

    def start_action(self, event):
        if self.zoom_mode:
            self.apply_zoom(event)
        elif self.text_mode:  # 텍스트 모드일 때
            self.text_position = event.pos()
            self.text_mode = False  # 텍스트 입력 후 텍스트 모드 해제
            self.set_cursor(QCursor(Qt.ArrowCursor))  # 기본 커서로 돌아가기
            self.add_text(event.pos())
        elif self.lens_mode:  # 렌즈 왜곡 모드일 때
            label_pos = event.pos()
            image_pos = self.image_label.mapTo(self.image_label, label_pos)

            x, y = image_pos.x(), image_pos.y()

            h, w, _ = self.image.shape
            if 0 <= x < w and 0 <= y < h:
                if event.button() == Qt.LeftButton:  # 볼록 렌즈 효과 (왼쪽 클릭)
                    self.apply_lens_distortion(x, y, "convex")
                elif event.button() == Qt.RightButton:  # 오목 렌즈 효과 (오른쪽 클릭)
                    self.apply_lens_distortion(x, y, "concave")
        else:
            label_pos = event.pos()
            image_pos = self.image_label.mapTo(self.image_label, label_pos)

            x, y = image_pos.x(), image_pos.y()

            h, w, _ = self.image.shape
            if 0 <= x < w and 0 <= y < h:
                if self.filling:
                    mask = np.zeros((h + 2, w + 2), np.uint8)
                    
                    # 색상 차이를 설정 (낮은 값과 높은 값으로 범위를 설정)
                    loDiff = (3, 3, 3)  # 허용되는 최소 색상 차이 (B, G, R)
                    upDiff = (5, 5, 5)  # 허용되는 최대 색상 차이 (B, G, R)
                    
                    # floodFill 실행
                    cv2.floodFill(self.image, mask, (x, y), self.brush_color, loDiff=loDiff, upDiff=upDiff)
                    
                    self.add_to_history()
                    self.display_image()
                else:
                    self.drawing_path = []
                    self.last_point = (x, y)  # 그리기 시작
                    self.drawing_path.append(self.last_point)
                    self.add_to_history()

    def resizeEvent(self, event):
        event.ignore()

    def draw(self, event):
        if event.buttons() == Qt.LeftButton and self.last_point:
            # 마우스 좌표 그대로 사용
            current_point = (event.x(), event.y())

            if self.tool_mode == "brush":
                cv2.line(self.image, self.last_point, current_point, self.brush_color, self.brush_size)
                self.drawing_path.append(current_point)  # 경로에 점 추가
            elif self.tool_mode == "eraser":
                cv2.line(self.image, self.last_point, current_point, (255, 255, 255), self.brush_size)

            self.last_point = current_point
            self.display_image()

    def stop_action(self, event):
        if self.tool_mode == "brush" and self.last_point is not None:
            self.last_point = None
            self.add_to_history()

    def set_fill_mode(self):
        self.hide_toolbars()
        self.unvisibleRotate()
        self.zoom_mode = False
        self.lens_mode = False
        if not self.filling:  # 페인트 모드가 활성화되지 않았다면
            self.tool_mode = "fill"  # 페인트 모드로 전환
            self.filling = True  # 페인트 모드 활성화
        else:
            self.tool_mode = "brush"  # 그리기 모드로 전환
            self.filling = False  # 페인트 모드 비활성화
        self.reset_ui_for_brush_mode()

    def set_eraser_mode(self):
        self.unvisibleRotate()
        self.hide_toolbars()
        self.zoom_mode = False
        self.lens_mode = False
        self.tool_mode = "eraser"
        self.filling = False  # 페인트 모드 비활성화
        self.reset_ui_for_brush_mode()

    def select_brush_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = (color.blue(), color.green(), color.red())
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def apply_zoom(self, event):
        if self.zoom_mode and event.button() in [Qt.LeftButton, Qt.RightButton]:
            scale_factor = 1.2 if event.button() == Qt.LeftButton else 0.8

            # 클릭 위치 가져오기
            click_x, click_y = event.pos().x(), event.pos().y()
            label_w, label_h = self.image_label.width(), self.image_label.height()
            img_h, img_w, _ = self.image.shape

            # 캔버스에서 이미지 좌표로 변환
            img_click_x = int(click_x * img_w / label_w)
            img_click_y = int(click_y * img_h / label_h)

            # 이미지 확대/축소
            new_w, new_h = int(img_w * scale_factor), int(img_h * scale_factor)
            resized_image = cv2.resize(self.image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

            # 확대/축소된 이미지에서 클릭 위치 중심으로 이동
            center_x = int(img_click_x * scale_factor)
            center_y = int(img_click_y * scale_factor)

            # 캔버스 크기 설정
            canvas_w, canvas_h = 900, 700
            canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

            # 중심 위치 계산
            start_x = max(0, center_x - canvas_w // 2)
            start_y = max(0, center_y - canvas_h // 2)
            end_x = min(new_w, start_x + canvas_w)
            end_y = min(new_h, start_y + canvas_h)

            # 잘라낸 이미지를 캔버스에 복사
            cropped_image = resized_image[start_y:end_y, start_x:end_x]
            canvas[:end_y - start_y, :end_x - start_x] = cropped_image

            self.image = canvas
            self.display_image()
            self.add_to_history()


    def apply_blur(self):
        self.unvisibleRotate()
        self.hide_toolbars()
        self.zoom_mode = False
        self.lens_mode = False
        if self.image is not None:
            roi = cv2.selectROI("Select ROI for Blur", self.image, showCrosshair=True, fromCenter=False)
            if roi[2] > 0 and roi[3] > 0:
                x, y, w, h = roi
                self.image[y:y + h, x:x + w] = cv2.blur(self.image[y:y + h, x:x + w], (15, 15))
                self.add_to_history()
                self.display_image()
            cv2.destroyWindow("Select ROI for Blur")

    def apply_perspective_transform(self):
        self.unvisibleRotate()
        self.hide_toolbars()
        self.zoom_mode = False
        self.lens_mode = False
        if self.image is not None:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            for cnt in contours:
                approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
                if len(approx) == 4:
                    points = approx.reshape(4, 2)
                    break
            else:
                return

            width, height = 800, 600
            points_dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")

            matrix = cv2.getPerspectiveTransform(np.float32(points), points_dst)

            self.image = cv2.warpPerspective(self.image, matrix, (width, height), flags=cv2.INTER_CUBIC)

            self.image = cv2.flip(self.image, 1)

            self.image = cv2.resize(self.image, (900, 700), interpolation=cv2.INTER_CUBIC)

            self.add_to_history()
            self.display_image()
    

    # 흑백변환
    def apply_grayscale(self):
        if self.image is not None:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)  # 흑백 유지
            self.display_image()
            self.add_to_history()

    # 색 반전
    def apply_color_inversion(self):
        if self.image is not None:
            self.image = cv2.bitwise_not(self.image)
            self.display_image()
            self.add_to_history()

    # 회전 기능
    def set_rotate_mode(self):
        self.tool_mode = "rotate"
        self.text_mode = False
        self.zoom_mode = False
        self.lens_mode = False
        self.hide_toolbars()
        
        # 브러쉬 및 텍스트 설정 UI 숨기기
        for widget in [self.brush_size_text_label, self.slider, self.brush_size_label,
                    self.font_label, self.font_combo, self.font_size_label,
                    self.font_size_spinbox, self.text_input_field]:
            widget.setVisible(False)
        
        # 회전 UI 보이기
        for widget in [self.label_rotate_ccw, self.label_separator, self.label_rotate_cw,
         self.rotate_ccw_button, self.rotate_cw_button]:
            widget.setVisible(True)

    # 반시계 방향 회전
    def rotate_counter_clockwise(self):
        self.apply_rotation(45)

    # 시계 방향 회전
    def rotate_clockwise(self):
        self.apply_rotation(-45)

    # 회전 적용 함수
    def apply_rotation(self, angle):
        rows, cols = self.image.shape[:2]
        center = (cols // 2, rows // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 이미지 회전
        self.image = cv2.warpAffine(self.image, rotation_matrix, (cols, rows), 
                                borderValue=(255, 255, 255), 
                                flags=cv2.INTER_CUBIC)
        self.add_to_history()  # 작업 히스토리에 추가
        self.display_image()

    # 회전 상단 영역 안보이게 하기
    def unvisibleRotate(self):
        self.label_rotate_ccw.setVisible(False)
        self.rotate_ccw_button.setVisible(False)
        self.label_separator.setVisible(False)
        self.label_rotate_cw.setVisible(False)
        self.rotate_cw_button.setVisible(False)
        self.update()  # UI 업데이트

    # 도형 모드
    def set_diagram_mode(self):
        self.text_mode = False
        self.zoom_mode = False
        self.lens_mode = False
        self.tool_mode = "diagram"
        # 브러쉬 및 텍스트 설정 UI 숨기기
        for widget in [self.brush_size_text_label, self.slider, self.brush_size_label,
                    self.font_label, self.font_combo, self.font_size_label,
                    self.font_size_spinbox, self.text_input_field,self.label_rotate_ccw, self.label_separator,
                     self.label_rotate_cw, self.rotate_ccw_button, self.rotate_cw_button]:
            widget.setVisible(False)

        self.rectangle_button.setVisible(True)
        self.circle_button.setVisible(True)
        self.triangle_button.setVisible(True)

    # 도형 모드 숨기기
    def hide_toolbars(self):
        self.rectangle_button.setVisible(False)
        self.circle_button.setVisible(False)
        self.triangle_button.setVisible(False)

    # 도형 삽입
    def apply_shape(self):
        if self.image is not None and self.start_point and self.end_point:
            x1, y1 = self.start_point
            x2, y2 = self.end_point
            color = self.brush_color  #선택된 브러쉬 색상

            if self.current_shape == 'rectangle':
                cv2.rectangle(self.image, (x1, y1), (x2, y2), color, -1)
            elif self.current_shape == 'circle':
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                radius = min(abs(x2 - x1), abs(y2 - y1)) // 2
                cv2.circle(self.image, center, radius, color, -1)
            elif self.current_shape == 'triangle':
                triangle_points = np.array([
                    [((x1 + x2) // 2, y1)],
                    [(x1, y2)],
                    [(x2, y2)]
                ], np.int32)
                cv2.polylines(self.image, [triangle_points], isClosed=True, color=color, thickness=3)
                cv2.fillPoly(self.image, [triangle_points], color=color)

            self.add_to_history()
            self.display_image()

    #도형 ROI 선택
    def select_roi_for_shape(self):
        if self.image is not None:
            roi = cv2.selectROI("Select ROI for Shape", self.image, showCrosshair=True, fromCenter=False)
            cv2.destroyWindow("Select ROI for Shape")

            if roi[2] > 0 and roi[3] > 0:
                x, y, w, h = roi
                self.start_point = (x, y)
                self.end_point = (x + w, y + h)
                self.apply_shape()

    def select_shape(self, shape):
        self.current_shape = shape
        self.select_roi_for_shape()

    #렌즈 왜곡
    def apply_lens_distortion(self, center_x, center_y, distortion_type):
        h, w, _ = self.image.shape

        # 렌즈 왜곡 파라미터 (강도, 왜곡 범위)
        exp = 2 
        scale = 1 

        # 매핑 배열 생성
        mapy, mapx = np.indices((h, w), dtype=np.float32)

        # 좌상단 기준좌표에서 -1~1로 정규화된 중심점 기준 좌표로 변경
        mapx = 2 * mapx / (w - 1) - 1
        mapy = 2 * mapy / (h - 1) - 1

        # 직교좌표를 극 좌표로 변환
        r, theta = cv2.cartToPolar(mapx, mapy)

        # 왜곡 영역만 중심확대/축소 지수 적용
        if distortion_type == "convex":  # 볼록 렌즈
            r[r < scale] = r[r < scale] ** exp
        elif distortion_type == "concave":  # 오목 렌즈
            r[r < scale] = r[r < scale] ** (1 / exp)

        # 극 좌표를 직교좌표로 변환
        mapx, mapy = cv2.polarToCart(r, theta)

        # 중심점 기준에서 좌상단 기준으로 변경
        mapx = ((mapx + 1) * w - 1) / 2
        mapy = ((mapy + 1) * h - 1) / 2

        # 재매핑 변환
        distorted = cv2.remap(self.image, mapx, mapy, cv2.INTER_LINEAR)

        # 왜곡된 이미지를 다시 적용
        self.image = distorted

        # 작업 히스토리 추가
        self.add_to_history()
        self.display_image()

    # equalizeHist+CLAHE 자동으로 함수
    def apply_auto_correction(self):
        if len(self.image.shape) == 3:
            # 각 채널에 대해 개별적으로 equalizeHist() 적용
            b, g, r = cv2.split(self.image)
            b = cv2.equalizeHist(b)
            g = cv2.equalizeHist(g)
            r = cv2.equalizeHist(r)
            self.image = cv2.merge((b, g, r))
        else:
            self.image = cv2.equalizeHist(self.image)

        # CLAHE를 사용해 대비 조정 (Automatic Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))  # CLAHE 객체 생성
        if len(self.image.shape) == 3:
            b, g, r = cv2.split(self.image)
            b = clahe.apply(b)
            g = clahe.apply(g)
            r = clahe.apply(r)
            self.image = cv2.merge((b, g, r))
        else:
            self.image = clahe.apply(self.image)

        canvas_width = self.image_label.width()
        canvas_height = self.image_label.height()
        self.image = cv2.resize(self.image, (900, 700),interpolation=cv2.INTER_CUBIC)

        self.add_to_history()
        self.display_image()

    def masking(self, bp, win_name):
        disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cv2.filter2D(bp, -1, disc, bp)
        _, mask = cv2.threshold(bp, 1, 255, cv2.THRESH_BINARY)
        result = cv2.bitwise_and(self.image, self.image, mask=mask)  # self.image 사용
        return result

    def backProject_manual(self, hist_roi, hsv_img):
        hist_img = cv2.calcHist([hsv_img], [0, 1], None, [180, 256], [0, 180, 0, 256])
        hist_rate = hist_roi / (hist_img + 1)

        # 비율에 맞는 픽셀 값 매핑
        h, s, v = cv2.split(hsv_img)
        bp = hist_rate[h.ravel(), s.ravel()]

        bp = np.minimum(bp, 1)
        bp = bp.reshape(hsv_img.shape[:2])
        cv2.normalize(bp, bp, 0, 255, cv2.NORM_MINMAX)
        bp = bp.astype(np.uint8)

        return self.masking(bp, 'result_manual')

    def backProject_cv(self, hist_roi, hsv_img):
        # 역투영 함수
        bp = cv2.calcBackProject([hsv_img], [0, 1], hist_roi, [0, 180, 0, 256], 1)
        return self.masking(bp, 'result_cv')

    # 역투영 진행
    def apply_reprojection(self):
        self.unvisibleRotate()
        self.hide_toolbars()
        self.zoom_mode = False
        self.lens_mode = False
        
        if self.image is not None:
            # ROI 선택 창을 띄움
            roi = cv2.selectROI("Select ROI for Reprojection", self.image, showCrosshair=True, fromCenter=False)
            
            if roi[2] == 0 or roi[3] == 0:
                cv2.destroyWindow("Select ROI for Reprojection")
                return
            
            # ROI가 선택된 경우
            x, y, w, h = roi
            # ROI 영역 추출
            roi_image = self.image[y:y+h, x:x+w]
            
            # ROI 이미지를 HSV로 변환
            hsv_roi = cv2.cvtColor(roi_image, cv2.COLOR_BGR2HSV)
            
            # H, S 채널에 대한 히스토그램 계산
            hist_roi = cv2.calcHist([hsv_roi], [0, 1], None, [180, 256], [0, 180, 0, 256])
            
            # 전체 이미지에서 H, S 채널을 분리하고 히스토그램을 계산
            hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            
            # ROI에서 계산된 히스토그램을 매뉴얼 구현함수와 OpenCV 이용하는 함수에 각각 전달
            result_manual = self.backProject_manual(hist_roi, hsv_image)
            
            self.image = result_manual

            self.add_to_history()
            self.display_image()
            cv2.destroyWindow("Select ROI for Reprojection")

    #이미지 합성 하는 함수
    def composite_images(self):
        # 이미지 합성을 위한 두 번째 이미지 선택
        file_path, _ = QFileDialog.getOpenFileName(self, "합성할 이미지 열기", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            data = np.fromfile(file_path, dtype=np.uint8)
            img2 = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if img2 is None:
                QMessageBox.critical(self, "오류", "합성할 이미지를 불러올 수 없습니다.")
                return

            # 마스크 생성 (합성할 이미지의 크기와 같은 크기)
            mask = np.full_like(img2, 255)

            r = cv2.selectROI("ROI 선택", self.image)

            # 선택된 영역의 x, y, width, height 값
            x, y, w, h = r

            if w == 0 or h == 0:
                QMessageBox.warning(self, "경고", "유효한 영역이 선택되지 않았습니다.")
                return

            # 선택한 영역의 중심 좌표 계산
            center = (x + w // 2, y + h // 2)

            # seamlessClone으로 이미지 합성
            composite_image = cv2.seamlessClone(img2, self.image, mask, center, cv2.NORMAL_CLONE)
            self.image = composite_image
            self.display_image()
            self.add_to_history()

    #적응형스레시홀드 함수
    def apply_threshold(self):
        if not hasattr(self, 'image') or self.image is None:
            QMessageBox.critical(self, "오류", "이미지가 로드되지 않았습니다.")
            return

        adaptive_thresh_mean_c = 10

        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        # adaptiveThreshold 적용
        threshold_image = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, adaptive_thresh_mean_c
        )

        # 결과 이미지를 캔버스에 띄우기
        self.image = cv2.cvtColor(threshold_image, cv2.COLOR_GRAY2BGR)  # 결과를 컬러로 변환
        self.display_image()
        self.add_to_history()

    #이미지 저장
    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "이미지 저장", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            success = cv2.imwrite(file_path, self.image)
            if not success:
                QMessageBox.critical(self, "오류", "이미지를 저장할 수 없습니다.")

    def show_about_popup(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("프로그램 정보")
        
        layout = QVBoxLayout()
        
        message = (
            "<strong>이미지 편집 프로그램 v2.6</strong><br>"
            "GUI: PyQt5 5.15.11<br>"
            "Editor: openCV 4.10.0.84<br><br>"
            "제작자: minari0v0<br>"
            "깃허브: <a href='https://github.com/minari0v0'>GitHub_minari0v0</a>"
        )
    
        label = QLabel(message)
        label.setOpenExternalLinks(True)  # Make links clickable
        layout.addWidget(label)
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = ImageEditor()
    editor.show()
    sys.exit(app.exec_())