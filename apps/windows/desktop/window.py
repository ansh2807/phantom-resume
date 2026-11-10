"""Native Windows workbench with animated navigation and background jobs."""
import json
import math
from pathlib import Path
import sys
import traceback
import html

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSettings, QUrl, QEvent
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QFont, QIcon, QDesktopServices, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox, QScrollArea,
    QFrame, QFileDialog, QStackedWidget, QSplitter, QTextBrowser, QTabWidget, QListWidget,
    QListWidgetItem, QProgressBar, QMessageBox, QGraphicsOpacityEffect, QSizePolicy)

from .catalog import TOOLS, BY_KEY, CHANNEL_INFO, CHANNELS
from .engine import run_tool, default_output, resource_root, serialize, data_root
from .jobs import Worker

STYLE = """
* {font-family: 'Segoe UI'; font-size: 13px;}
QMainWindow, QWidget#canvas {background: #F1F4F7; color: #17283A;}
QWidget#rail {background:#132737; color:#B7C8D2;}
QLabel#brand {font-size:20px; font-weight:700; color:#F5FFFD; letter-spacing:-.5px;}
QLabel#edition {font-size:10px; color:#7D9AA9; letter-spacing:2px;}
QLabel#group {font-size:10px; color:#7894A5; letter-spacing:1.4px; font-weight:700; padding-top:16px; padding-bottom:4px;}
QPushButton#nav {text-align:left; color:#B6C9D4; background:transparent; border:0; border-radius:7px; padding:10px 12px;}
QPushButton#nav:hover {background:#203C4C; color:white;}
QPushButton#nav:checked {background:#B9EED8; color:#16382C; font-weight:600;}
QLineEdit#search {background:#203847; color:#DEEBF1; border:1px solid #36505E; border-radius:7px; padding:9px;}
QLabel#eyebrow {color:#58786F; font-size:10px; font-weight:700; letter-spacing:1.6px;}
QLabel#title {font-size:30px; font-weight:650; letter-spacing:-1px; color:#152B3C;}
QLabel#subtitle {color:#6A7B8A; font-size:13px;}
QLabel#tag {background:#E0ECE7; color:#3F6758; padding:7px 12px; border-radius:12px; font-size:11px;}
QFrame#card {background:#FFFFFF; border:1px solid #DFE6EC; border-radius:14px;}
QLabel#cardTitle {font-size:17px; color:#203746; font-weight:600;}
QLabel#fieldLabel {color:#3E5564; font-size:12px; font-weight:600;}
QLabel#muted {color:#758794; font-size:11px;}
QLabel#note {color:#657D72; font-size:11px; background:#F1F7F4; border-radius:8px; padding:12px;}
QLineEdit, QPlainTextEdit, QComboBox {background:#F7F9FB; color:#233C4C; border:1px solid #DCE4E9; border-radius:7px; padding:10px; selection-background-color:#B9EED8; selection-color:#132737;}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {border:1px solid #5FAE8E; background:#FFFFFF;}
QComboBox {min-height:19px;}
QComboBox::drop-down {width:26px; border:0;}
QComboBox::down-arrow {image:url(__ARROW__); width:12px; height:12px;}
QComboBox QAbstractItemView {background:white; color:#203746; selection-background-color:#DBF2E8; selection-color:#183B2E;}
QCheckBox {color:#415A69; spacing:8px; padding:3px 0;}
QCheckBox::indicator {width:15px; height:15px; border-radius:4px; border:1px solid #ADC1CE; background:#F6F9FA;}
QCheckBox::indicator:checked {background:#46876C; border:1px solid #46876C; image:url(__CHECK__);}
QPushButton {background:white; color:#395667; border:1px solid #D9E3E9; border-radius:7px; padding:9px 14px; font-weight:600;}
QPushButton:hover {background:#EAF4EF; border-color:#A1CDB9;}
QPushButton:pressed {background:#D7EBDD;}
QPushButton:disabled {background:#EEF2F4; color:#9DADB8; border-color:#E0E7EC;}
QPushButton#primary {background:#1E5F49; color:#F2FFF9; border:0; padding:14px; font-size:13px;}
QPushButton#primary:hover {background:#287457;}
QPushButton#primary:disabled {background:#86A697; color:#D8E7DF;}
QPushButton#quiet {background:transparent; border:0; color:#7F9CA9; text-align:left; font-size:11px; padding:5px;}
QPushButton#quiet:hover {color:#D6F9E9;}
QScrollArea {background:transparent; border:0;}
QScrollBar:vertical {background:transparent; width:6px; margin:0;}
QScrollBar::handle:vertical {background:#B6C7CE; border-radius:3px; min-height:30px;}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0;}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background:transparent;}
QTabWidget::pane {border:0; background:transparent;}
QTabBar::tab {color:#738793; padding:12px 18px; background:transparent; border-bottom:2px solid transparent;}
QTabBar::tab:selected {color:#1E5F49; border-bottom:2px solid #5EAC8A; font-weight:600;}
QTextBrowser, QListWidget {background:transparent; color:#304856; border:0; padding:8px;}
QListWidget::item {border:1px solid #E3EBEF; border-radius:7px; padding:12px; margin:4px;}
QListWidget::item:selected {background:#E1F2E9; color:#1E5F49;}
QProgressBar {border:0; border-radius:3px; background:#E1ECE6; height:4px; max-height:4px;}
QProgressBar::chunk {background:#5CB38A; border-radius:3px;}
QSplitter::handle {background:transparent; width:14px;}
QStatusBar {background:#E8EEF2; color:#6F818D; font-size:11px;}
QToolTip {background:#193746; color:#F5FFFA; padding:8px; border:0;}
"""


def label(text, name=None, wrap=False):
    obj = QLabel(text)
    if name:
        obj.setObjectName(name)
    obj.setWordWrap(wrap)
    return obj


def button(text, callback, name=None):
    obj = QPushButton(text)
    if name:
        obj.setObjectName(name)
    obj.setCursor(Qt.PointingHandCursor)
    obj.clicked.connect(callback)
    return obj


class Orbit(QWidget):
    """Original vector illustration: a document passing through a scan ring."""
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.setMinimumHeight(230)
        self.setMaximumHeight(270)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.frames_left = 0

    def animate_briefly(self):
        self.frames_left = 30
        self.timer.start(67)

    def tick(self):
        if self.isVisible() and self.frames_left > 0:
            self.frames_left -= 1
            self.phase += .025
            self.update()
        else:
            self.timer.stop()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width()/2, self.height()/2
        p.translate(cx, cy)
        for radius in (78, 106):
            p.setPen(QPen(QColor('#DCE9E5'), 1))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(-radius, -radius, 2*radius, 2*radius)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#5CA888'))
        p.drawEllipse(math.cos(self.phase)*106-4, math.sin(self.phase)*106-4, 8, 8)
        p.save()
        p.translate(0, math.sin(self.phase)*4)
        p.rotate(-6)
        p.setBrush(QColor('#E2EBE7'))
        p.drawRoundedRect(-49, -66, 110, 144, 12, 12)
        p.setPen(QPen(QColor('#CCDCD4'), 1))
        p.setBrush(QColor('#FFFFFF'))
        p.drawRoundedRect(-56, -76, 110, 144, 12, 12)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor('#B9EED8'))
        p.drawRoundedRect(-41, -57, 32, 32, 8, 8)
        p.setBrush(QColor('#214B3B'))
        p.drawEllipse(-33, -46, 5, 7)
        p.drawEllipse(-21, -46, 5, 7)
        for y, width in [(-12, 72), (1, 58), (14, 72), (36, 48), (49, 62)]:
            p.setBrush(QColor('#9FB9AC') if y == -12 else QColor('#DFE8E3'))
            p.drawRoundedRect(-40, y, width, 4, 2, 2)
        p.restore()
        p.setBrush(QColor('#1E5F49'))
        p.drawEllipse(35, 30, 44, 44)
        p.setPen(QPen(QColor('white'), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QPainterPath()
        path.moveTo(48, 52)
        path.lineTo(55, 59)
        path.lineTo(67, 46)
        p.drawPath(path)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PhantomResume Desktop')
        self.setWindowIcon(QIcon(str(resource_root()/'assets'/'phantom.ico')))
        self.resize(1440, 940)
        self.setMinimumSize(1080, 720)
        self.setAcceptDrops(True)
        self.settings = QSettings('PhantomResume', 'Desktop')
        self.output = self.settings.value('output', str(default_output()))
        self.shared_input = ''
        self.saved_forms = {}
        self.current_key = None
        self.worker = None
        self.closing = False
        self.results = {}
        self.widgets = {}
        self.nav_buttons = {}
        self.animations = []
        self.build()
        self.select_tool('inject')
        QShortcut(QKeySequence('Ctrl+O'), self, activated=self.choose_resume)
        QShortcut(QKeySequence('Ctrl+Return'), self, activated=self.start_job)
        self.statusBar().showMessage('Ready   •   Originals stay unchanged   •   Ctrl+O to choose a resume')

    def build(self):
        canvas = QWidget()
        canvas.setObjectName('canvas')
        self.setCentralWidget(canvas)
        outer = QHBoxLayout(canvas)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        rail = QWidget()
        rail.setObjectName('rail')
        rail.setFixedWidth(222)
        sidebar = QVBoxLayout(rail)
        sidebar.setContentsMargins(18, 26, 18, 18)
        sidebar.setSpacing(6)
        brand = QHBoxLayout()
        mark = label('◉')
        mark.setStyleSheet('color:#B9EED8;font-size:28px;')
        brand.addWidget(mark)
        brand.addWidget(label('PhantomResume', 'brand'))
        sidebar.addLayout(brand)
        sidebar.addWidget(label('DESKTOP  /  1.3', 'edition'))
        sidebar.addSpacing(18)
        self.search = QLineEdit()
        self.search.setObjectName('search')
        self.search.setPlaceholderText('Find a tool…')
        self.search.textChanged.connect(self.filter_tools)
        sidebar.addWidget(self.search)
        self.group_filter = QComboBox()
        self.group_filter.addItems(['All tools', 'INJECTION TOOLS', 'WORKSPACE', 'DOCUMENT LAB', 'RESEARCH'])
        self.group_filter.setToolTip('Filter the tool list by category')
        self.group_filter.currentTextChanged.connect(lambda _: self.filter_tools(self.search.text()))
        sidebar.addWidget(self.group_filter)
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav = QWidget()
        nav.setObjectName('navBody')
        nav.setStyleSheet('QWidget#navBody {background:transparent;}')
        layout = QVBoxLayout(nav)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        group = None
        for i, tool in enumerate(TOOLS):
            if tool.group != group:
                group = tool.group
                layout.addWidget(label(group, 'group'))
            b = button(tool.title, lambda checked=False, key=tool.key: self.select_tool(key), 'nav')
            b.setCheckable(True)
            b.setToolTip(tool.description)
            layout.addWidget(b)
            self.nav_buttons[tool.key] = b
        layout.addStretch()
        nav_scroll.setWidget(nav)
        sidebar.addWidget(nav_scroll, 1)
        sidebar.addWidget(button('＋  Try a sample resume', self.make_demo, 'quiet'))
        sidebar.addWidget(button('↗  Open export folder', self.open_output, 'quiet'))
        self.motion = QCheckBox('Reduce motion')
        self.motion.setStyleSheet('color:#91ACBA;font-size:11px;')
        self.motion.setChecked(self.settings.value('reduce_motion', False, type=bool))
        self.motion.toggled.connect(self.set_motion)
        sidebar.addWidget(self.motion)
        outer.addWidget(rail)

        workspace = QVBoxLayout()
        workspace.setContentsMargins(30, 26, 30, 22)
        workspace.setSpacing(16)
        topline = QHBoxLayout()
        topline.addWidget(label('YOUR DOCUMENT WORKBENCH', 'eyebrow'))
        topline.addStretch()
        topline.addWidget(label('●  Local document processing', 'tag'))
        workspace.addLayout(topline)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(5)
        self.title = label('', 'title')
        self.subtitle = label('', 'subtitle', True)
        titles.addWidget(self.title)
        titles.addWidget(self.subtitle)
        heading.addLayout(titles, 1)
        self.load_button = button('Choose resume   ↗', self.choose_resume)
        heading.addWidget(self.load_button, 0, Qt.AlignVCenter)
        workspace.addLayout(heading)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(14)
        self.splitter.setChildrenCollapsible(False)
        self.setup_card = QFrame()
        self.setup_card.setObjectName('card')
        self.setup_card.setMinimumWidth(315)
        setup_layout = QVBoxLayout(self.setup_card)
        setup_layout.setContentsMargins(20, 20, 20, 20)
        setup_layout.setSpacing(12)
        form_heading = QHBoxLayout()
        form_heading.addWidget(label('Set up your run', 'cardTitle'))
        form_heading.addStretch()
        form_heading.addWidget(label('01', 'muted'))
        setup_layout.addLayout(form_heading)
        self.form_scroll = QScrollArea()
        self.form_scroll.setWidgetResizable(True)
        self.form_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        setup_layout.addWidget(self.form_scroll, 1)
        self.run_button = button('', self.start_job, 'primary')
        setup_layout.addWidget(self.run_button)
        self.cancel_button = button('Cancel this run', self.cancel_job)
        self.cancel_button.hide()
        setup_layout.addWidget(self.cancel_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        setup_layout.addWidget(self.progress)
        self.run_status = label('New files are saved in a separate run folder.', 'muted', True)
        setup_layout.addWidget(self.run_status)
        self.splitter.addWidget(self.setup_card)

        results = QFrame()
        results.setObjectName('card')
        results.setMinimumWidth(400)
        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(22, 20, 22, 18)
        head = QHBoxLayout()
        head.addWidget(label('Results', 'cardTitle'))
        head.addStretch()
        self.result_badge = label('READY WHEN YOU ARE', 'muted')
        head.addWidget(self.result_badge)
        results_layout.addLayout(head)
        self.result_stack = QStackedWidget()
        self.empty = QWidget()
        empty_layout = QVBoxLayout(self.empty)
        empty_layout.addStretch()
        self.orbit = Orbit()
        empty_layout.addWidget(self.orbit)
        empty_title = label('A clearer view of your resume.')
        empty_title.setAlignment(Qt.AlignCenter)
        empty_title.setStyleSheet('font-size:24px;font-weight:600;color:#264537;')
        empty_layout.addWidget(empty_title)
        subtitle = label('Choose a document, select a tool, and run it.\nYour results and saved files appear here.', 'subtitle', True)
        subtitle.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(subtitle)
        empty_layout.addSpacing(18)
        pill = label('DOCX   /   PDF   /   TEXT', 'eyebrow')
        pill.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(pill)
        empty_layout.addStretch()
        self.result_stack.addWidget(self.empty)
        self.tabs = QTabWidget()
        self.overview = QTextBrowser()
        self.overview.setOpenExternalLinks(False)
        self.overview.anchorClicked.connect(lambda url: QDesktopServices.openUrl(url) if url.isLocalFile() else None)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setStyleSheet('font-family:Consolas;font-size:12px;border:0;background:#F7F9FA;')
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file_item)
        self.tabs.addTab(self.overview, 'Overview')
        self.tabs.addTab(self.details, 'Details')
        self.tabs.addTab(self.file_list, 'Saved files')
        self.result_stack.addWidget(self.tabs)
        results_layout.addWidget(self.result_stack, 1)
        footer = QHBoxLayout()
        self.result_hint = label('Drop a resume anywhere to get started.', 'muted', True)
        footer.addWidget(self.result_hint, 1)
        self.copy_button = button('Copy results', self.copy_results)
        self.copy_button.hide()
        footer.addWidget(self.copy_button)
        self.files_button = button('Open run folder  ↗', self.open_run)
        self.files_button.hide()
        footer.addWidget(self.files_button)
        results_layout.addLayout(footer)
        self.splitter.addWidget(results)
        self.splitter.setSizes([365, 740])
        workspace.addWidget(self.splitter, 1)
        bottom = QHBoxLayout()
        self.destination_label = label('', 'muted')
        self.update_destination()
        bottom.addWidget(self.destination_label, 1)
        bottom.addWidget(button('Change folder', self.choose_output))
        workspace.addLayout(bottom)
        outer.addLayout(workspace, 1)
        self.setStyleSheet(STYLE.replace('__CHECK__', (resource_root()/'assets'/'check.svg').as_posix()).replace('__ARROW__', (resource_root()/'assets'/'arrow.svg').as_posix()))
        self.set_motion(self.motion.isChecked())

    def set_motion(self, reduced):
        self.settings.setValue('reduce_motion', reduced)
        if hasattr(self, 'orbit'):
            if reduced:
                self.orbit.timer.stop()
            else:
                self.orbit.animate_briefly()

    def filter_tools(self, text):
        for key, b in self.nav_buttons.items():
            matches = text.lower() in BY_KEY[key].title.lower() or text.lower() in BY_KEY[key].description.lower()
            group = self.group_filter.currentText() if hasattr(self, 'group_filter') else 'All tools'
            b.setVisible(matches and (group == 'All tools' or BY_KEY[key].group == group))

    def values(self):
        values = {}
        for key, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                values[key] = widget.text().strip()
            elif isinstance(widget, QPlainTextEdit):
                values[key] = widget.toPlainText()
            elif isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, dict):
                values[key] = [k for k, checkbox in widget.items() if checkbox.isChecked()]
        return values

    def select_tool(self, key):
        if self.worker and self.worker.isRunning():
            return
        if self.current_key:
            self.saved_forms[self.current_key] = self.values()
        self.current_key = key
        tool = BY_KEY[key]
        for k, b in self.nav_buttons.items():
            b.setChecked(k == key)
        self.title.setText(tool.title)
        self.subtitle.setText(tool.description)
        self.run_button.setText(tool.button+'   →')
        self.widgets = {}
        content = QWidget()
        content.setObjectName('formBody')
        content.setStyleSheet('QWidget#formBody {background:transparent;}')
        form = QVBoxLayout(content)
        form.setContentsMargins(0, 0, 5, 0)
        form.setSpacing(10)
        saved = self.saved_forms.get(key, {})
        self.channels_container = None
        for field in tool.fields:
            value = saved.get(field.key, field.default)
            if field.key == 'input' and not value:
                value = self.shared_input
            if field.kind not in ('bool', 'checks'):
                form.addWidget(label(field.label + (' *' if field.required else ''), 'fieldLabel'))
            if field.kind in ('file', 'folder'):
                row = QHBoxLayout()
                row.setSpacing(6)
                widget = QLineEdit(str(value))
                widget.setPlaceholderText(field.hint or 'Choose a folder…')
                widget.setMinimumWidth(50)
                widget.setToolTip(field.hint)
                row.addWidget(widget, 1)
                browse = button('…', lambda checked=False, f=field, w=widget: self.browse_field(f, w))
                browse.setFixedWidth(38)
                browse.setToolTip('Browse for '+field.label.lower())
                row.addWidget(browse)
                form.addLayout(row)
            elif field.kind == 'area':
                widget = QPlainTextEdit(str(value))
                widget.setPlaceholderText(field.hint)
                widget.setMinimumHeight(110)
                widget.setMaximumHeight(180)
                form.addWidget(widget)
            elif field.kind == 'choice':
                widget = QComboBox()
                widget.addItems(field.options)
                widget.setCurrentText(str(value))
                form.addWidget(widget)
            elif field.kind == 'bool':
                widget = QCheckBox(field.label)
                widget.setChecked(bool(value))
                form.addWidget(widget)
            elif field.kind == 'checks':
                container = QWidget()
                controls = QVBoxLayout(container)
                controls.setContentsMargins(0, 0, 0, 0)
                controls.addWidget(label(field.label, 'fieldLabel'))
                quick = QHBoxLayout()
                quick.setSpacing(5)
                all_button = button('All channels', lambda checked=False, k=field.key: self.select_channels(k, True))
                none_button = button('Clear', lambda checked=False, k=field.key: self.select_channels(k, False))
                quick.addWidget(all_button)
                quick.addWidget(none_button)
                controls.addLayout(quick)
                layout = QGridLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(3)
                widget = {}
                for index, name in enumerate(field.options):
                    checkbox = QCheckBox(name.replace('_', ' ').capitalize())
                    if name in CHANNEL_INFO:
                        checkbox.setToolTip(CHANNEL_INFO[name][1])
                    checkbox.setChecked(name in value)
                    if field.key == 'channels':
                        checkbox.clicked.connect(lambda checked: self.widgets['custom'].setChecked(True))
                    layout.addWidget(checkbox, index//2, index%2)
                    widget[name] = checkbox
                controls.addLayout(layout)
                form.addWidget(container)
                if field.key == 'channels':
                    self.channels_container = container
            else:
                widget = QLineEdit(str(value))
                widget.setPlaceholderText(field.hint)
                form.addWidget(widget)
            if not isinstance(widget, dict):
                widget.setObjectName('field_'+field.key)
                widget.setAccessibleName(field.label)
            self.widgets[field.key] = widget
        if 'custom' in self.widgets and self.channels_container:
            self.widgets['custom'].toggled.connect(lambda _: self.sync_mode_channels())
            self.widgets['mode'].currentTextChanged.connect(lambda _: self.sync_mode_channels())
            self.sync_mode_channels()
        if tool.note:
            form.addSpacing(5)
            form.addWidget(label(tool.note, 'note', True))
        form.addStretch()
        old = self.form_scroll.takeWidget()
        if old:
            old.deleteLater()
        self.form_scroll.setWidget(content)
        self.run_status.setText('New files are saved in a separate run folder.')
        if key in self.results:
            self.show_result(self.results[key])
        else:
            self.result_stack.setCurrentIndex(0)
            self.result_badge.setText('READY WHEN YOU ARE')
            self.files_button.hide()
            self.copy_button.hide()
            self.result_hint.setText('Drop a resume anywhere to get started.')
        if not self.motion.isChecked():
            self.orbit.animate_briefly()
            effect = QGraphicsOpacityEffect(content)
            content.setGraphicsEffect(effect)
            animation = QPropertyAnimation(effect, b'opacity', content)
            animation.setDuration(220)
            animation.setStartValue(.25)
            animation.setEndValue(1.0)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
            self.animations = [animation]

    def select_channels(self, key, selected):
        if key == 'channels':
            self.widgets['custom'].setChecked(True)
        for checkbox in self.widgets.get(key, {}).values():
            checkbox.setChecked(selected)
        if key == 'channels' and selected:
            self.widgets['mode'].setCurrentText('nuclear')

    def sync_mode_channels(self):
        if self.widgets['custom'].isChecked():
            return
        mode = self.widgets['mode'].currentText()
        choices = CHANNELS if mode == 'nuclear' else ['metadata', 'hidden_text', 'comments', 'zero_width', 'image', 'qr'] if mode == 'aggressive' else ['metadata']
        for name, checkbox in self.widgets['channels'].items():
            checkbox.setChecked(name in choices)

    def browse_field(self, field, widget):
        if field.kind == 'folder':
            path = QFileDialog.getExistingDirectory(self, field.label, widget.text() or str(Path.home()))
        else:
            patterns = '*.docx *.pdf *.txt *.png *.jpg *.jpeg *.webp *.bmp *.json'
            path, _ = QFileDialog.getOpenFileName(self, field.label, widget.text() or str(Path.home()), f'Supported files ({patterns});;All files (*)')
        if path:
            widget.setText(path)
            if field.key == 'input':
                self.shared_input = path

    def choose_resume(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Choose a resume', self.shared_input or str(Path.home()), 'Resumes (*.docx *.pdf *.txt)')
        if path:
            self.set_input(path)

    def set_input(self, path):
        self.shared_input = str(path)
        if 'input' not in self.widgets:
            self.select_tool('review')
        if 'input' in self.widgets:
            self.widgets['input'].setText(str(path))
        self.statusBar().showMessage('Selected: '+str(path))

    def make_demo(self):
        if self.worker and self.worker.isRunning():
            return
        from examples.create_demo import create_demo
        import uuid
        try:
            path = create_demo(Path(self.output)/('Sample-'+uuid.uuid4().hex[:6]))
            self.select_tool('review')
            self.set_input(path)
            self.run_status.setText('Synthetic sample ready. Select Analyze resume to try it.')
        except Exception as e:
            self.show_error(str(e))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not (self.worker and self.worker.isRunning()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            path = Path(urls[0].toLocalFile())
            if path.is_file():
                self.set_input(path)

    def start_job(self):
        if self.worker and self.worker.isRunning():
            return
        params = self.values()
        for field in BY_KEY[self.current_key].fields:
            if field.required and not str(params.get(field.key, '')).strip():
                self.run_status.setText(field.label+' is required.')
                self.widgets[field.key].setFocus()
                return
        params['output'] = self.output
        self.saved_forms[self.current_key] = params.copy()
        if self.worker:
            self.worker.deleteLater()
        self.worker = Worker(self.current_key, params, self)
        self.worker.progress.connect(self.on_progress)
        self.worker.done.connect(self.on_done)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(self.on_finished)
        self.run_button.setEnabled(False)
        self.load_button.setEnabled(False)
        self.form_scroll.setEnabled(False)
        for b in self.nav_buttons.values():
            b.setEnabled(False)
        self.progress.show()
        self.cancel_button.show()
        self.result_badge.setText('WORKING')
        self.worker.start()

    def on_progress(self, message):
        self.run_status.setText(message)
        self.statusBar().showMessage(message)

    def on_done(self, result):
        if self.closing:
            return
        # Retain only three bounded previews; complete output remains on disk.
        self.results.pop(self.current_key, None)
        self.results[self.current_key] = result
        while len(self.results) > 3:
            del self.results[next(iter(self.results))]
        self.show_result(result)

    def on_finished(self):
        self.run_button.setEnabled(True)
        self.load_button.setEnabled(True)
        self.form_scroll.setEnabled(True)
        for b in self.nav_buttons.values():
            b.setEnabled(True)
        self.progress.hide()
        self.cancel_button.hide()

    def show_error(self, message):
        if self.closing:
            return
        self.result_badge.setText('NEEDS ATTENTION')
        self.run_status.setText('Could not complete this run. See the error in Results.')
        self.overview.setHtml('<h2 style="color:#8B4B36">This run needs attention</h2><p style="white-space:pre-wrap">'+html.escape(message).replace('\n', '<br>')+'</p><p>Your original file has not been modified. Check the input and run again.</p>')
        self.details.setPlainText(message)
        self.file_list.clear()
        self.result_stack.setCurrentIndex(1)
        self.tabs.setCurrentIndex(0)
        self.files_button.hide()
        self.copy_button.hide()
        self.statusBar().showMessage('Run failed — details are shown in Results.')

    def show_result(self, result):
        self.result_stack.setCurrentIndex(1)
        self.tabs.setCurrentIndex(0)
        self.result_badge.setText('COMPLETE WITH NOTES' if result['warnings'] else 'COMPLETE')
        self.details.setPlainText(serialize(result['data']))
        self.file_list.clear()
        for value in result['files']:
            path = Path(value)
            size = path.stat().st_size if path.exists() else 0
            item = QListWidgetItem(f'{path.name}\n{size/1024:,.1f} KB  ·  {path.suffix.upper()[1:]}')
            item.setData(Qt.UserRole, value)
            item.setToolTip(value+'\nDouble-click to open')
            self.file_list.addItem(item)
        self.result_hint.setText('Bounded preview • Open result.json for complete data. Double-click a saved file to open it.')
        self.files_button.show()
        self.copy_button.show()
        data = result['data']
        out = '<style>body{color:#304856;font-family:Segoe UI;font-size:13px;}h2{font-size:22px;color:#244D3B;}h3{font-size:15px;color:#395E4E;}p{line-height:150%;}pre{white-space:pre-wrap;font-family:Consolas;font-size:12px;}td{padding:10px;}</style>'
        for warning in result['warnings']:
            out += '<p style="color:#956B2A;background:#FFF4DB;padding:10px">'+html.escape(warning)+'</p>'
        analysis = data.get('analysis')
        if analysis:
            out += f'<table width="100%" bgcolor="#E8F5EE"><tr><td><span style="font-size:54px;color:#245E46;font-weight:700">{analysis["score"]}</span><span style="font-size:18px"> / 100</span><br>Local resume score</td><td>{len(analysis.get("issues", []))} issues found<br>{len(data.get("suggestions", []))} writing suggestions</td></tr></table>'
            out += '<h3>Score breakdown</h3><pre>'+html.escape(serialize(analysis.get('breakdown', {})))+'</pre>'
            out += '<h3>Issues to review</h3>'
            for issue in analysis.get('issues', []):
                out += '<p>• '+html.escape(str(issue))+'</p>'
            out += '<h3>Writing suggestions</h3>'
            for s in data.get('suggestions', [])[:40]:
                out += '<p><b>'+html.escape(s['type'])+'</b><br><span style="color:#84978F">'+html.escape(s['before'])+'</span><br>→ '+html.escape(s['after'])+'</p>'
        if 'injection' in data:
            out += '<h3>Applied steps</h3>'
            for step in data['injection'].get('steps', []):
                out += '<p>✓ '+html.escape(step)+'</p>'
            for skipped in data.get('skipped_channels', []):
                out += '<p style="color:#956B2A">Skipped: '+html.escape(skipped)+'</p>'
        for name in ('draft', 'note', 'text_diff', 'transformed'):
            if name in data:
                out += '<h3>'+name.replace('_', ' ').title()+'</h3><p>'+html.escape(str(data[name])).replace('\n', '<br>')+'</p>'
        if not analysis and 'injection' not in data and not any(k in data for k in ('draft', 'note', 'text_diff', 'transformed')):
            preview = {k: v for k, v in data.items() if k not in ('other_parts', 'inspection', 'page_text')}
            out += '<h2>'+html.escape(result['tool'])+' complete</h2><pre>'+html.escape(serialize(preview)[:18000])+'</pre>'
        if 'inspection' in data:
            inspect = data['inspection']
            out += '<h3>Document check</h3><p>'+str(len(inspect.get('images', [])))+' embedded images · '+str(len(inspect.get('fonts', [])))+' fonts · '+str(len(inspect.get('xml_parse_errors', [])))+' XML parsing errors</p>'
        out += '<p style="color:#84978F">The Details tab contains the complete result. Your export folder includes an HTML report and JSON data.</p>'
        self.overview.setHtml(out)
        self.statusBar().showMessage('Saved to '+result['output_directory'])

    def open_file_item(self, item):
        path = Path(item.data(Qt.UserRole))
        if path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def open_run(self):
        result = self.results.get(self.current_key)
        if result:
            QDesktopServices.openUrl(QUrl.fromLocalFile(result['output_directory']))

    def copy_results(self):
        result = self.results.get(self.current_key)
        if result:
            path = Path(result['output_directory'])/'result.json'
            if path.stat().st_size > 10*1024*1024:
                self.statusBar().showMessage('Result is too large for clipboard preview; open result.json from Saved files.')
                return
            full = json.loads(path.read_text(encoding='utf-8'))
            QApplication.clipboard().setText(serialize(full['data']))
            self.statusBar().showMessage('Results copied to clipboard.')

    def open_output(self):
        try:
            Path(self.output).mkdir(parents=True, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output))
        except Exception as e:
            self.show_error(str(e))

    def update_destination(self):
        self.destination_label.setText('EXPORTS   '+self.output)
        self.destination_label.setToolTip(self.output)

    def choose_output(self):
        path = QFileDialog.getExistingDirectory(self, 'Choose export folder', self.output)
        if path:
            self.output = path
            self.settings.setValue('output', path)
            self.update_destination()

    def cancel_job(self):
        if self.worker:
            self.worker.cancel()

    def shutdown(self):
        if self.closing:
            return
        self.closing = True
        self.orbit.timer.stop()
        for animation in self.animations:
            animation.stop()
        if self.worker:
            self.worker.shutdown()
        self.results.clear()

    def changeEvent(self, event):
        if event.type() in (QEvent.WindowStateChange, QEvent.ActivationChange) and hasattr(self, 'orbit'):
            if self.isMinimized() or not self.isActiveWindow():
                self.orbit.timer.stop()
        super().changeEvent(event)

    def closeEvent(self, event):
        self.shutdown()
        event.accept()
