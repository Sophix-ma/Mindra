import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton,
                               QLabel, QMessageBox, QDialog, QTableWidget,
                               QTableWidgetItem, QHeaderView, QComboBox, QStackedWidget,
                               QDateEdit, QMenu, QInputDialog, QProgressBar, QFileDialog)
from PySide6.QtCore import Qt, QDate, QUrl, QTimer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from style_settings import MenuStyles, DialogStyles, ButtonStyles
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest


# ========== 数据类 ==========

class Bookmark:
    """书签类"""
    
    def __init__(self, url, title, folder="默认", created_time=None):
        self.url = url
        self.title = title
        self.folder = folder
        self.created_time = created_time or datetime.now()
        
    def to_dict(self):
        """转换为字典"""
        return {
            "url": self.url,
            "title": self.title,
            "folder": self.folder,
            "created_time": self.created_time.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        return cls(
            data["url"],
            data["title"],
            data.get("folder", "默认"),
            datetime.fromisoformat(data["created_time"])
        )


class DownloadItem:
    """下载项类"""
    
    def __init__(self, url, filename, save_path, total_size=0):
        self.url = url
        self.filename = filename
        self.save_path = save_path
        self.total_size = total_size
        self.downloaded_size = 0
        self.status = "等待中"  # 等待中、下载中、已完成、已取消、错误
        self.start_time = datetime.now()
        self.end_time = None
        self.speed = "0 KB/s"
        
    def to_dict(self):
        """转换为字典"""
        return {
            "url": self.url,
            "filename": self.filename,
            "save_path": str(self.save_path),
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "status": self.status,
            "speed": self.speed,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        item = cls(data["url"], data["filename"], Path(data["save_path"]))
        item.total_size = data["total_size"]
        item.downloaded_size = data["downloaded_size"]
        item.status = data["status"]
        item.speed = data.get("speed", "0 KB/s")
        item.start_time = datetime.fromisoformat(data["start_time"])
        if data["end_time"]:
            item.end_time = datetime.fromisoformat(data["end_time"])
        return item


class HistoryEntry:
    """历史记录条目类"""
    
    def __init__(self, url, title, visit_time):
        self.url = url
        self.title = title
        self.visit_time = visit_time
        
    def to_dict(self):
        """转换为字典"""
        return {
            "url": self.url,
            "title": self.title,
            "visit_time": self.visit_time.isoformat()
        }
        
    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        return cls(
            data["url"],
            data["title"],
            datetime.fromisoformat(data["visit_time"])
        )


# ========== 管理器类 ==========

class BookmarksManager:
    """书签管理器 - 纯数据管理"""
    
    def __init__(self, data_dir, parent=None):
        self.parent = parent
        self.data_dir = Path(data_dir)
        self.bookmarks_file = self.data_dir / "bookmarks.json"
        
        self.bookmarks = []
        self.folders = set(["默认"])
        self.load_bookmarks()
        
    def add_bookmark(self, url, title, folder="默认"):
        """添加书签"""
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # 检查URL是否已存在
        for bookmark in self.bookmarks:
            if bookmark.url == url:
                QMessageBox.warning(self.parent, "提示", f"该URL已存在:\n标题: {bookmark.title}\n文件夹: {bookmark.folder}")
                return
            
        # 创建书签
        bookmark = Bookmark(url, title, folder)
        self.bookmarks.append(bookmark)
        
        # 更新文件夹列表
        if folder not in self.folders:
            self.folders.add(folder)
            
        self.save_bookmarks()
        QMessageBox.information(self.parent, "成功", f"已添加书签: {title}")
        
    def load_bookmarks(self):
        """加载书签"""
        if self.bookmarks_file.exists():
            try:
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.bookmarks = [Bookmark.from_dict(item) for item in data]
                    
                    # 收集所有文件夹
                    for bookmark in self.bookmarks:
                        self.folders.add(bookmark.folder)
                        
            except Exception as e:
                print(f"加载书签失败: {e}")
                self.bookmarks = []
                
    def save_bookmarks(self):
        """保存书签"""
        try:
            data = [bookmark.to_dict() for bookmark in self.bookmarks]
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存书签失败: {e}")


class DownloadManager:
    """下载管理器 - 纯数据管理"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.downloads_dir = Path("Mindra_data") / "Downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloads = []
        self.on_download_progress_callback = None  # UI刷新回调
        self.load_downloads()
        
    def add_download(self, url, suggested_filename=None, custom_save_path=None):
        """添加下载任务"""
        # 生成文件名
        if suggested_filename:
            filename = suggested_filename
        else:
            filename = os.path.basename(url) or "download"
            
        # 确定保存路径
        if custom_save_path:
            save_path = Path(custom_save_path)
            filename = save_path.name
        else:
            save_path = self.downloads_dir / filename
            counter = 1
            while save_path.exists():
                name, ext = os.path.splitext(filename)
                new_filename = f"{name}({counter}){ext}"
                save_path = self.downloads_dir / new_filename
                filename = new_filename
                counter += 1
            
        # 创建下载项
        download = DownloadItem(url, filename, save_path)
        self.downloads.insert(0, download)
        
        self.save_downloads()
        return download
        
    def start_download(self, download):
        """开始下载"""
        try:
            self.network_manager = QNetworkAccessManager()
            request = QNetworkRequest(QUrl(download.url))
            self.reply = self.network_manager.get(request)
            
            self.reply.downloadProgress.connect(
                lambda bytes_received, bytes_total: 
                self.on_download_progress(download, bytes_received, bytes_total))
            self.reply.finished.connect(
                lambda: self.on_download_finished(download))
            self.reply.errorOccurred.connect(
                lambda error: self.on_download_error(download, error))
            
            download.status = "下载中"
            
        except Exception as e:
            download.status = f"错误: {str(e)}"
            download.end_time = datetime.now()
            self.save_downloads()
    
    def on_download_progress(self, download, bytes_received, bytes_total):
        """下载进度更新"""
        download.downloaded_size = bytes_received
        download.total_size = bytes_total
        
        elapsed = (datetime.now() - download.start_time).total_seconds()
        if elapsed > 0:
            speed = bytes_received / elapsed
            download.speed = self.format_size(speed) + "/s"
    
    def on_download_finished(self, download):
        """下载完成"""
        try:
            data = self.reply.readAll()
            
            with open(download.save_path, 'wb') as f:
                f.write(data)
            
            download.status = "已完成"
            download.end_time = datetime.now()
            download.downloaded_size = len(data) if data else 0
            
            if download.total_size <= 0:
                download.total_size = download.downloaded_size
            
            if download.total_size > 0:
                download.downloaded_size = download.total_size
            
            self.save_downloads()
            
        except Exception as e:
            download.status = f"保存错误: {str(e)}"
            download.end_time = datetime.now()
            self.save_downloads()
    
    def on_download_error(self, download, error):
        """下载错误"""
        download.status = f"错误: {error}"
        download.end_time = datetime.now()
        self.save_downloads()
    
    def handle_download_request(self, download_item):
        """处理浏览器下载请求"""
        try:
            url = download_item.url().toString()
            
            # 检查是否已经有相同的URL正在下载
            for download in self.downloads:
                if download.url == url and download.status in ["等待中", "下载中"]:
                    download_item.accept()
                    return
            
            suggested_filename = download_item.suggestedFileName()
            if not suggested_filename:
                suggested_filename = os.path.basename(url) or "download"
            
            # 弹出文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self.parent, 
                "保存文件",
                str(self.downloads_dir / suggested_filename),
                "所有文件 (*.*)"
            )
            
            if not file_path:
                download_item.cancel()
                return
            
            # 添加到下载管理
            download = self.add_download(url, os.path.basename(file_path), file_path)
            
            # 自动打开“更多”窗口并切换到下载管理页
            more_dialog = self.parent.more_dialog
            more_dialog.show()
            more_dialog.raise_()
            more_dialog.activateWindow()
            more_dialog.switch_page(1)  # 下载管理页索引为1
            
            # 设置下载路径
            download_item.setDownloadDirectory(os.path.dirname(file_path))
            download_item.setDownloadFileName(os.path.basename(file_path))
            
            # 更新下载状态（在accept之前）
            download.status = "下载中"
            download.total_size = download_item.totalBytes()
            self.save_downloads()
            
            # 连接下载进度信号（使用默认参数捕获当前值）
            download_item.receivedBytesChanged.connect(
                lambda d=download, di=download_item: self.on_webengine_download_progress(d, di))
            download_item.stateChanged.connect(
                lambda state, d=download, di=download_item: self.on_webengine_download_state_changed(d, di, state))
            
            # 接受下载请求 - 由 Qt WebEngine 处理实际下载
            download_item.accept()
            
        except Exception as e:
            print(f"处理下载请求失败: {e}")
            download_item.cancel()
    
    def on_webengine_download_progress(self, download, download_item):
        """处理 WebEngine 下载进度更新"""
        download.downloaded_size = download_item.receivedBytes()
        download.total_size = download_item.totalBytes()
        
        elapsed = (datetime.now() - download.start_time).total_seconds()
        if elapsed > 0:
            speed = download.downloaded_size / elapsed
            download.speed = self.format_size(speed) + "/s"
        
        # 保存下载状态到文件（每1秒保存一次，避免频繁IO）
        if not hasattr(self, '_last_save_time'):
            self._last_save_time = 0
        current_time = datetime.now().timestamp()
        if current_time - self._last_save_time >= 1:
            self.save_downloads()
            self._last_save_time = current_time
        
        # 触发UI刷新回调
        if hasattr(self, 'on_download_progress_callback') and self.on_download_progress_callback:
            self.on_download_progress_callback()
    
    def on_webengine_download_state_changed(self, download, download_item, state):
        """处理 WebEngine 下载状态变化"""
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            download.status = "已完成"
            download.end_time = datetime.now()
            download.downloaded_size = download_item.receivedBytes()
            download.total_size = download_item.totalBytes()
            self.save_downloads()
        elif state == QWebEngineDownloadRequest.DownloadCancelled:
            download.status = "已取消"
            download.end_time = datetime.now()
            self.save_downloads()
        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            download.status = f"错误: {download_item.interruptReasonString()}"
            download.end_time = datetime.now()
            self.save_downloads()
        
        # 触发UI刷新回调
        if hasattr(self, 'on_download_progress_callback') and self.on_download_progress_callback:
            self.on_download_progress_callback()
        
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
            
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"
        
    def load_downloads(self):
        """加载下载记录"""
        downloads_file = self.downloads_dir.parent / "downloads.json"
        
        if downloads_file.exists():
            try:
                with open(downloads_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.downloads = [DownloadItem.from_dict(item) for item in data]
            except Exception as e:
                print(f"加载下载记录失败: {e}")
                self.downloads = []
                
    def save_downloads(self):
        """保存下载记录"""
        downloads_file = self.downloads_dir.parent / "downloads.json"
        
        try:
            data = [download.to_dict() for download in self.downloads]
            with open(downloads_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存下载记录失败: {e}")


class HistoryManager:
    """历史记录管理器 - 纯数据管理"""
    
    def __init__(self, data_dir, parent=None):
        self.parent = parent
        self.data_dir = Path(data_dir)
        self.history_file = self.data_dir / "history.json"
        
        self.history = []
        self.load_history()
        
    def add_entry(self, url, title, visit_time):
        """添加历史记录条目"""
        entry = HistoryEntry(url, title, visit_time)
        self.history.append(entry)
        
        # 限制历史记录数量（最多1000条）
        if len(self.history) > 1000:
            self.history = self.history[-1000:]
            
        self.save_history()
        
    def clear_today_history(self):
        """清除今天的历史记录"""
        today = datetime.now().date()
        self.history = [entry for entry in self.history 
                       if entry.visit_time.date() != today]
        self.save_history()
        
    def clear_week_history(self):
        """清除本周的历史记录"""
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        self.history = [entry for entry in self.history 
                       if entry.visit_time < week_start]
        self.save_history()
        
    def clear_all_history(self):
        """清除所有历史记录"""
        self.history.clear()
        self.save_history()
            
    def load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [HistoryEntry.from_dict(item) for item in data]
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                self.history = []
                
    def save_history(self):
        """保存历史记录"""
        try:
            data = [entry.to_dict() for entry in self.history]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")


# ========== 主对话框类 ==========

class MoreDialog(QDialog):
    """更多功能对话框 - 整合书签、下载、历史记录"""
    
    def __init__(self, browser_window, parent=None):
        super().__init__(parent)
        self.browser_window = browser_window
        self.setWindowTitle("更多")
        self.setGeometry(150, 150, 1000, 650)
        
        # 初始化管理器
        self.bookmarks_manager = BookmarksManager(browser_window.data_dir, browser_window)
        self.download_manager = DownloadManager(browser_window)
        self.history_manager = HistoryManager(browser_window.data_dir, browser_window)
        
        # 设置下载进度回调
        self.download_manager.on_download_progress_callback = self.on_download_progress_update
        
        # 创建定时器用于刷新下载列表
        self.download_refresh_timer = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI布局"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左侧功能菜单
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(180)
        self.left_panel.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
            }
        """)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(10, 20, 10, 20)
        left_layout.setSpacing(8)
        
        # 标题
        title_label = QLabel("功能菜单")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1565c0;
                padding-bottom: 10px;
                border: none;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title_label)
        
        left_layout.addSpacing(10)
        
        # 功能按钮
        self.menu_buttons = []
        
        # 书签按钮
        self.bookmarks_btn = QPushButton("📚 查看书签")
        self.bookmarks_btn.setCheckable(True)
        self.bookmarks_btn.setChecked(True)
        self.bookmarks_btn.clicked.connect(lambda: self.switch_page(0))
        self.style_menu_button(self.bookmarks_btn)
        left_layout.addWidget(self.bookmarks_btn)
        self.menu_buttons.append(self.bookmarks_btn)
        
        # 下载按钮
        self.downloads_btn = QPushButton("⬇️ 下载管理")
        self.downloads_btn.setCheckable(True)
        self.downloads_btn.clicked.connect(lambda: self.switch_page(1))
        self.style_menu_button(self.downloads_btn)
        left_layout.addWidget(self.downloads_btn)
        self.menu_buttons.append(self.downloads_btn)
        
        # 历史按钮
        self.history_btn = QPushButton("🕐 历史记录")
        self.history_btn.setCheckable(True)
        self.history_btn.clicked.connect(lambda: self.switch_page(2))
        self.style_menu_button(self.history_btn)
        left_layout.addWidget(self.history_btn)
        self.menu_buttons.append(self.history_btn)
        
        left_layout.addStretch()
        
        layout.addWidget(self.left_panel)
        
        # 右侧内容区域 - 使用堆叠部件
        self.stack = QStackedWidget()
        
        # 创建三个管理器页面
        self.bookmarks_page = self.create_bookmarks_page()
        self.downloads_page = self.create_downloads_page()
        self.history_page = self.create_history_page()
        
        self.stack.addWidget(self.bookmarks_page)
        self.stack.addWidget(self.downloads_page)
        self.stack.addWidget(self.history_page)
        
        layout.addWidget(self.stack, 1)
        
        # 设置对话框样式
        self.setStyleSheet(DialogStyles.get_more_dialog_style())
        
    def style_menu_button(self, btn):
        """设置菜单按钮样式"""
        btn.setStyleSheet(ButtonStyles.get_menu_button_style())
        
    def switch_page(self, index):
        """切换页面"""
        # 更新按钮状态
        for i, btn in enumerate(self.menu_buttons):
            btn.setChecked(i == index)
        
        # 切换堆叠部件
        self.stack.setCurrentIndex(index)
        
        # 刷新对应页面数据
        if index == 0:
            self.refresh_bookmarks()
        elif index == 1:
            self.refresh_downloads()
            self.start_download_refresh_timer()
        else:
            self.stop_download_refresh_timer()
            
        if index == 2:
            self.refresh_history()
            
    def create_bookmarks_page(self):
        """创建书签页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 搜索和过滤区域
        filter_layout = QHBoxLayout()
        
        search_label = QLabel("搜索:")
        filter_layout.addWidget(search_label)
        
        self.bookmarks_search = QLineEdit()
        self.bookmarks_search.setPlaceholderText("输入标题或URL进行搜索...")
        self.bookmarks_search.textChanged.connect(self.filter_bookmarks)
        filter_layout.addWidget(self.bookmarks_search)
        
        folder_label = QLabel("文件夹:")
        filter_layout.addWidget(folder_label)
        
        self.bookmarks_folder_combo = QComboBox()
        self.bookmarks_folder_combo.addItem("全部")
        self.bookmarks_folder_combo.currentTextChanged.connect(self.filter_bookmarks)
        filter_layout.addWidget(self.bookmarks_folder_combo)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        add_bookmark_btn = QPushButton("➕ 添加书签")
        add_bookmark_btn.clicked.connect(self.add_bookmark_dialog)
        self.style_control_button(add_bookmark_btn)
        control_layout.addWidget(add_bookmark_btn)
        
        edit_bookmark_btn = QPushButton("✏️ 编辑书签")
        edit_bookmark_btn.clicked.connect(self.edit_bookmark_dialog)
        self.style_control_button(edit_bookmark_btn)
        control_layout.addWidget(edit_bookmark_btn)
        
        delete_bookmark_btn = QPushButton("🗑️ 删除书签")
        delete_bookmark_btn.clicked.connect(self.delete_bookmark_dialog)
        self.style_control_button(delete_bookmark_btn)
        control_layout.addWidget(delete_bookmark_btn)
        
        add_folder_btn = QPushButton("📁 新建文件夹")
        add_folder_btn.clicked.connect(self.add_folder_dialog)
        self.style_control_button(add_folder_btn)
        control_layout.addWidget(add_folder_btn)
        
        delete_folder_btn = QPushButton("📂 删除文件夹")
        delete_folder_btn.clicked.connect(self.delete_folder_dialog)
        self.style_control_button(delete_folder_btn)
        control_layout.addWidget(delete_folder_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 书签表格
        self.bookmarks_table = QTableWidget()
        self.bookmarks_table.setColumnCount(4)
        self.bookmarks_table.setHorizontalHeaderLabels(["标题", "URL", "文件夹", "添加时间"])
        
        header = self.bookmarks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        self.bookmarks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.bookmarks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bookmarks_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.bookmarks_table.doubleClicked.connect(self.open_bookmark)
        self.bookmarks_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmarks_table.customContextMenuRequested.connect(self.show_bookmarks_context_menu)
        
        layout.addWidget(self.bookmarks_table)
        
        self.refresh_bookmarks()
        
        return page
        
    def create_downloads_page(self):
        """创建下载页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        clear_all_btn = QPushButton("🗑️ 清除全部")
        clear_all_btn.clicked.connect(self.clear_all_downloads)
        self.style_control_button(clear_all_btn)
        control_layout.addWidget(clear_all_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 下载表格
        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(6)
        self.downloads_table.setHorizontalHeaderLabels(["文件名", "大小", "进度", "状态", "速度", "时间"])
        
        header = self.downloads_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.downloads_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.downloads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloads_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.downloads_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.downloads_table.customContextMenuRequested.connect(self.show_downloads_context_menu)
        
        layout.addWidget(self.downloads_table)
        
        self.refresh_downloads()
        
        return page
        
    def create_history_page(self):
        """创建历史记录页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 搜索和过滤区域
        filter_layout = QHBoxLayout()
        
        search_label = QLabel("搜索:")
        filter_layout.addWidget(search_label)
        
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("输入标题或URL进行搜索...")
        self.history_search.textChanged.connect(self.filter_history)
        filter_layout.addWidget(self.history_search)
        
        date_label = QLabel("日期:")
        filter_layout.addWidget(date_label)

        self.history_start_date = QDateEdit()
        self.history_start_date.setDate(QDate.currentDate().addDays(-7))
        self.history_start_date.dateChanged.connect(self.filter_history)
        filter_layout.addWidget(self.history_start_date)
        
        end_label = QLabel("到")
        filter_layout.addWidget(end_label)
        
        self.history_end_date = QDateEdit()
        self.history_end_date.setDate(QDate.currentDate())
        self.history_end_date.dateChanged.connect(self.filter_history)
        filter_layout.addWidget(self.history_end_date)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 控制按钮
        control_layout = QHBoxLayout()
        
        clear_today_btn = QPushButton("🗑️ 清除今天")
        clear_today_btn.clicked.connect(self.clear_today_history)
        self.style_control_button(clear_today_btn)
        control_layout.addWidget(clear_today_btn)
        
        clear_week_btn = QPushButton("🗑️ 清除本周")
        clear_week_btn.clicked.connect(self.clear_week_history)
        self.style_control_button(clear_week_btn)
        control_layout.addWidget(clear_week_btn)
        
        clear_all_btn = QPushButton("🗑️ 清除全部")
        clear_all_btn.clicked.connect(self.clear_all_history)
        self.style_control_button(clear_all_btn)
        control_layout.addWidget(clear_all_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["标题", "URL", "访问时间"])
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setSelectionMode(QTableWidget.SingleSelection)
        self.history_table.doubleClicked.connect(self.open_history)
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_history_context_menu)
        
        layout.addWidget(self.history_table)
        
        self.refresh_history()
        
        return page
        
    def style_control_button(self, btn):
        """设置控制按钮样式"""
        btn.setStyleSheet(ButtonStyles.get_control_button_style())
        
    # ========== 书签功能 ==========
    def refresh_bookmarks(self):
        """刷新书签表格"""
        bm = self.bookmarks_manager
        bm.load_bookmarks()
        
        # 更新文件夹下拉框
        self.bookmarks_folder_combo.clear()
        self.bookmarks_folder_combo.addItem("全部")
        self.bookmarks_folder_combo.addItems(sorted(bm.folders))
        
        self.filter_bookmarks()
        
    def filter_bookmarks(self):
        """过滤书签"""
        bm = self.bookmarks_manager
        search_text = self.bookmarks_search.text().lower()
        folder_filter = self.bookmarks_folder_combo.currentText()
        
        filtered = []
        for bookmark in bm.bookmarks:
            if search_text and (search_text not in bookmark.title.lower() and 
                               search_text not in bookmark.url.lower()):
                continue
            if folder_filter != "全部" and bookmark.folder != folder_filter:
                continue
            filtered.append(bookmark)
        
        self.bookmarks_table.setRowCount(len(filtered))
        for row, bookmark in enumerate(filtered):
            self.bookmarks_table.setItem(row, 0, QTableWidgetItem(bookmark.title))
            self.bookmarks_table.setItem(row, 1, QTableWidgetItem(bookmark.url))
            self.bookmarks_table.setItem(row, 2, QTableWidgetItem(bookmark.folder))
            time_text = bookmark.created_time.strftime("%Y-%m-%d %H:%M")
            self.bookmarks_table.setItem(row, 3, QTableWidgetItem(time_text))
            
    def open_bookmark(self, index):
        """打开书签"""
        row = index.row()
        bm = self.bookmarks_manager
        search_text = self.bookmarks_search.text().lower()
        folder_filter = self.bookmarks_folder_combo.currentText()
        
        filtered = [b for b in bm.bookmarks 
                   if (not search_text or search_text in b.title.lower() or search_text in b.url.lower())
                   and (folder_filter == "全部" or b.folder == folder_filter)]
        
        if row < len(filtered):
            self.browser_window.create_new_tab(filtered[row].url, filtered[row].title)
            
    def show_bookmarks_context_menu(self, pos):
        """书签右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(MenuStyles.get_context_menu_style())
        
        selected_rows = set(index.row() for index in self.bookmarks_table.selectedIndexes())
        if selected_rows:
            open_action = menu.addAction("打开网页")
            open_action.triggered.connect(lambda: self.open_selected_bookmarks(selected_rows))
        menu.exec_(self.bookmarks_table.mapToGlobal(pos))
        
    def open_selected_bookmarks(self, rows):
        """打开选中的书签"""
        bm = self.bookmarks_manager
        search_text = self.bookmarks_search.text().lower()
        folder_filter = self.bookmarks_folder_combo.currentText()
        
        filtered = [b for b in bm.bookmarks 
                   if (not search_text or search_text in b.title.lower() or search_text in b.url.lower())
                   and (folder_filter == "全部" or b.folder == folder_filter)]
        
        for row in rows:
            if row < len(filtered):
                self.browser_window.create_new_tab(filtered[row].url, filtered[row].title)
                
    def add_bookmark_dialog(self):
        """添加书签对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加书签")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        bm = self.bookmarks_manager
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        title_input = QLineEdit()
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        url_input = QLineEdit()
        url_layout.addWidget(url_input)
        layout.addLayout(url_layout)
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("文件夹:"))
        folder_combo = QComboBox()
        folder_combo.addItems(sorted(bm.folders))
        folder_layout.addWidget(folder_combo)
        layout.addLayout(folder_layout)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加")
        cancel_btn = QPushButton("取消")
        add_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.Accepted:
            title = title_input.text().strip()
            url = url_input.text().strip()
            folder = folder_combo.currentText()
            if title and url:
                bm.add_bookmark(url, title, folder)
                self.refresh_bookmarks()
                
    def edit_bookmark_dialog(self):
        """编辑书签对话框"""
        selected_rows = set(index.row() for index in self.bookmarks_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要编辑的书签")
            return
        if len(selected_rows) > 1:
            QMessageBox.warning(self, "提示", "一次只能编辑一个书签")
            return
            
        bm = self.bookmarks_manager
        search_text = self.bookmarks_search.text().lower()
        folder_filter = self.bookmarks_folder_combo.currentText()
        
        filtered = [b for b in bm.bookmarks 
                   if (not search_text or search_text in b.title.lower() or search_text in b.url.lower())
                   and (folder_filter == "全部" or b.folder == folder_filter)]
        
        row = list(selected_rows)[0]
        if row >= len(filtered):
            return
        bookmark = filtered[row]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑书签")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("标题:"))
        title_input = QLineEdit(bookmark.title)
        title_layout.addWidget(title_input)
        layout.addLayout(title_layout)
        
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        url_input = QLineEdit(bookmark.url)
        url_layout.addWidget(url_input)
        layout.addLayout(url_layout)
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("文件夹:"))
        folder_combo = QComboBox()
        folder_combo.addItems(sorted(bm.folders))
        folder_combo.setCurrentText(bookmark.folder)
        folder_layout.addWidget(folder_combo)
        layout.addLayout(folder_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if dialog.exec() == QDialog.Accepted:
            title = title_input.text().strip()
            url = url_input.text().strip()
            folder = folder_combo.currentText()
            if title and url:
                bookmark.title = title
                bookmark.url = url
                bookmark.folder = folder
                if folder not in bm.folders:
                    bm.folders.add(folder)
                bm.save_bookmarks()
                self.refresh_bookmarks()
                
    def delete_bookmark_dialog(self):
        """删除书签对话框"""
        selected_rows = set(index.row() for index in self.bookmarks_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的书签")
            return
            
        reply = QMessageBox.question(self, "确认", 
                                    f"确定要删除选中的 {len(selected_rows)} 个书签吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            bm = self.bookmarks_manager
            search_text = self.bookmarks_search.text().lower()
            folder_filter = self.bookmarks_folder_combo.currentText()
            
            filtered = [b for b in bm.bookmarks 
                       if (not search_text or search_text in b.title.lower() or search_text in b.url.lower())
                       and (folder_filter == "全部" or b.folder == folder_filter)]
            
            bookmarks_to_delete = []
            for row in sorted(selected_rows, reverse=True):
                if row < len(filtered):
                    bookmarks_to_delete.append(filtered[row])
            
            for bookmark in bookmarks_to_delete:
                bm.bookmarks.remove(bookmark)
                
            bm.save_bookmarks()
            self.refresh_bookmarks()
            
    def add_folder_dialog(self):
        """添加文件夹对话框"""
        folder, ok = QInputDialog.getText(self, "新建文件夹", "文件夹名称:")
        if ok and folder:
            bm = self.bookmarks_manager
            if folder not in bm.folders:
                bm.folders.add(folder)
                self.refresh_bookmarks()
                QMessageBox.information(self, "成功", f"已创建文件夹: {folder}")
            else:
                QMessageBox.warning(self, "提示", "文件夹已存在")
                
    def delete_folder_dialog(self):
        """删除文件夹对话框"""
        bm = self.bookmarks_manager
        if not bm.folders:
            QMessageBox.information(self, "提示", "没有可删除的文件夹")
            return
            
        folder, ok = QInputDialog.getItem(self, "删除文件夹", "选择要删除的文件夹:",
                                          sorted(bm.folders), 0, False)
        
        if ok and folder:
            bookmarks_in_folder = [b for b in bm.bookmarks if b.folder == folder]
            if bookmarks_in_folder:
                reply = QMessageBox.question(self, "确认", 
                                          f"文件夹 '{folder}' 中有 {len(bookmarks_in_folder)} 个书签，\n"
                                          "删除文件夹将同时删除这些书签，确定继续吗？",
                                          QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                bm.bookmarks = [b for b in bm.bookmarks if b.folder != folder]
            
            bm.folders.discard(folder)
            bm.save_bookmarks()
            self.refresh_bookmarks()
            QMessageBox.information(self, "成功", f"已删除文件夹: {folder}")
            
    # ========== 下载功能 ==========
    def start_download_refresh_timer(self):
        """启动下载列表刷新定时器"""
        if self.download_refresh_timer is None:
            self.download_refresh_timer = QTimer(self)
            self.download_refresh_timer.timeout.connect(self.refresh_downloads)
            self.download_refresh_timer.start(500)  # 每500毫秒刷新一次
    
    def stop_download_refresh_timer(self):
        """停止下载列表刷新定时器"""
        if self.download_refresh_timer is not None:
            self.download_refresh_timer.stop()
            self.download_refresh_timer = None
    
    def on_download_progress_update(self):
        """下载进度更新回调"""
        # 只有当下载页面可见时才刷新
        if self.stack.currentIndex() == 1:
            self.refresh_downloads()
    
    def refresh_downloads(self):
        """刷新下载表格"""
        dm = self.download_manager
        # 注意：不要在这里调用 dm.load_downloads()，否则会覆盖内存中的实时数据
        
        self.downloads_table.setRowCount(len(dm.downloads))
        for row, download in enumerate(dm.downloads):
            self.downloads_table.setItem(row, 0, QTableWidgetItem(download.filename))
            
            if download.total_size > 0:
                size_text = self.format_size(download.total_size)
            else:
                size_text = "未知"
            self.downloads_table.setItem(row, 1, QTableWidgetItem(size_text))
            
            # 进度条
            progress_widget = QWidget()
            progress_layout = QHBoxLayout(progress_widget)
            progress_layout.setContentsMargins(2, 2, 2, 2)
            progress_bar = QProgressBar()
            progress_bar.setTextVisible(False)
            if download.total_size > 0:
                progress = int((download.downloaded_size / download.total_size) * 100)
            else:
                progress = 0
            progress_bar.setValue(progress)
            progress_layout.addWidget(progress_bar)
            self.downloads_table.setCellWidget(row, 2, progress_widget)
            
            self.downloads_table.setItem(row, 3, QTableWidgetItem(download.status))
            self.downloads_table.setItem(row, 4, QTableWidgetItem(download.speed))
            time_text = download.start_time.strftime("%H:%M:%S")
            self.downloads_table.setItem(row, 5, QTableWidgetItem(time_text))
            
    def show_downloads_context_menu(self, pos):
        """下载右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(MenuStyles.get_context_menu_style())
        
        selected_rows = set(index.row() for index in self.downloads_table.selectedIndexes())
        
        if selected_rows:
            open_action = menu.addAction("📂 打开文件")
            open_action.triggered.connect(lambda: self.open_downloaded_files(selected_rows))
            
            open_folder_action = menu.addAction("📁 打开所在文件夹")
            open_folder_action.triggered.connect(lambda: self.open_download_folders(selected_rows))
            menu.addSeparator()
            
            delete_action = menu.addAction("🗑️ 删除记录")
            delete_action.triggered.connect(lambda: self.delete_download_records(selected_rows))
            
        menu.exec_(self.downloads_table.mapToGlobal(pos))
        
    def open_downloaded_files(self, rows):
        """打开下载的文件"""
        dm = self.download_manager
        for row in sorted(rows):
            if row < len(dm.downloads):
                path = dm.downloads[row].save_path
                if path.exists():
                    os.startfile(str(path))
                    
    def open_download_folders(self, rows):
        """打开下载文件夹"""
        dm = self.download_manager
        for row in sorted(rows):
            if row < len(dm.downloads):
                folder = dm.downloads[row].save_path.parent
                if folder.exists():
                    os.startfile(str(folder))
                    
    def delete_download_records(self, rows):
        """删除下载记录"""
        dm = self.download_manager
        for row in sorted(rows, reverse=True):
            if row < len(dm.downloads):
                dm.downloads.pop(row)
        dm.save_downloads()
        self.refresh_downloads()
        
    def clear_all_downloads(self):
        """清除所有下载记录"""
        reply = QMessageBox.question(self, "确认", 
                                   "确定要清除所有下载记录吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            dm = self.download_manager
            dm.downloads.clear()
            dm.save_downloads()
            self.refresh_downloads()
            
    def format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
        
    # ========== 历史记录功能 ==========
    def refresh_history(self):
        """刷新历史记录表格"""
        hm = self.history_manager
        hm.load_history()
        self.filter_history()
        
    def filter_history(self):
        """过滤历史记录"""
        hm = self.history_manager
        search_text = self.history_search.text().lower()
        start_date = self.history_start_date.date().toPython()
        end_date = self.history_end_date.date().toPython() + timedelta(days=1)
        
        filtered = []
        for entry in hm.history:
            if search_text and (search_text not in entry.title.lower() and 
                               search_text not in entry.url.lower()):
                continue
            if entry.visit_time.date() < start_date or entry.visit_time.date() >= end_date:
                continue
            filtered.append(entry)
        
        filtered.sort(key=lambda x: x.visit_time, reverse=True)
        
        self.history_table.setRowCount(len(filtered))
        for row, entry in enumerate(filtered):
            self.history_table.setItem(row, 0, QTableWidgetItem(entry.title))
            self.history_table.setItem(row, 1, QTableWidgetItem(entry.url))
            time_text = entry.visit_time.strftime("%Y-%m-%d %H:%M:%S")
            self.history_table.setItem(row, 2, QTableWidgetItem(time_text))
            
        self.display_history = filtered
        
    def open_history(self, index):
        """打开历史记录"""
        row = index.row()
        if hasattr(self, 'display_history') and row < len(self.display_history):
            entry = self.display_history[row]
            self.browser_window.create_new_tab(entry.url, entry.title)
            
    def show_history_context_menu(self, pos):
        """历史记录右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet(MenuStyles.get_context_menu_style())
        
        selected_rows = set(index.row() for index in self.history_table.selectedIndexes())
        if selected_rows and hasattr(self, 'display_history'):
            open_action = menu.addAction("打开网页")
            open_action.triggered.connect(lambda: self.open_selected_history(selected_rows))
            
        menu.exec_(self.history_table.mapToGlobal(pos))
        
    def open_selected_history(self, rows):
        """打开选中的历史记录"""
        if hasattr(self, 'display_history'):
            for row in rows:
                if row < len(self.display_history):
                    entry = self.display_history[row]
                    self.browser_window.create_new_tab(entry.url, entry.title)
                    
    def clear_today_history(self):
        """清除今天的历史记录"""
        hm = self.history_manager
        today = datetime.now().date()
        hm.history = [entry for entry in hm.history 
                     if entry.visit_time.date() != today]
        hm.save_history()
        self.refresh_history()
        QMessageBox.information(self, "成功", "今天的历史记录已清除")
        
    def clear_week_history(self):
        """清除本周的历史记录"""
        hm = self.history_manager
        now = datetime.now()
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        hm.history = [entry for entry in hm.history 
                     if entry.visit_time < week_start]
        hm.save_history()
        self.refresh_history()
        QMessageBox.information(self, "成功", "本周的历史记录已清除")
        
    def clear_all_history(self):
        """清除所有历史记录"""
        reply = QMessageBox.question(self, "确认", 
                                   "确定要清除所有历史记录吗？",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            hm = self.history_manager
            hm.history.clear()
            hm.save_history()
            self.refresh_history()
            QMessageBox.information(self, "成功", "所有历史记录已清除")
    
    def closeEvent(self, event):
        """对话框关闭事件"""
        self.stop_download_refresh_timer()
        event.accept()
