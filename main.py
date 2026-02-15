import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout,
                               QWidget, QLineEdit, QPushButton, QTabWidget, QTabBar, QToolBar,
                               QMenu, QSplitter, QLabel, QMessageBox, QDialog)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PySide6.QtCore import Qt, QUrl, QSize, QTimer
from PySide6.QtGui import QCursor, QIcon
from ai_sidebar import AISidebar
from cookie_manager import CookieManager
from more_dialog import MoreDialog
from settings_dialog import SettingsDialog
from style_settings import MenuStyles, MainWindowStyles
from user_operations import LoginDialog, UserOperations
import html as html_module
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class BrowserWindow(QMainWindow):
    """主浏览器窗口"""
    
    # 首页URL常量
    HOME_URL = "mindra:home"
    
    def __init__(self):
        super().__init__()

        # 创建数据目录
        self.data_dir = Path("Mindra_data")
        self.data_dir.mkdir(exist_ok=True)

        # 创建cookie目录
        self.cookie_dir = self.data_dir / "cookie"
        self.cookie_dir.mkdir(exist_ok=True)

        # 设置窗口属性
        self.setWindowTitle("Mindra")
        
        # 初始化更多对话框引用
        self.more_dialog = None
        
        # 用户登录状态
        self.user_id = None
        self.username = None
        
        # 检查用户登录
        if not self.check_user_login():
            # 用户未登录，显示登录对话框
            login_dialog = LoginDialog(self)
            if login_dialog.exec() == QDialog.Accepted:
                # 登录成功
                self.user_id = login_dialog.user_id
                self.username = login_dialog.username
            else:
                # 用户取消登录，清除用户信息并退出程序
                UserOperations.clear_user_info()
                sys.exit(0)
        
        # 设置样式
        self.setup_styles()
        
        # 初始化组件
        self.setup_ui()
        
        # 初始化管理器
        self.setup_managers()

        # 创建首页标签
        self.create_home_tab()
        
    def setup_styles(self):
        """设置应用程序样式"""
        self.setStyleSheet(MainWindowStyles.get_main_window_style())
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建顶部工具栏
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # 创建分割器（主内容区 + AI侧边栏）
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # 创建浏览器区域
        self.browser_area = QWidget()
        self.browser_layout = QVBoxLayout(self.browser_area)
        self.browser_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)  # 启用标签页拖动交换位置
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)  # 监听标签页切换
        self.browser_layout.addWidget(self.tabs)
        
        # 创建AI侧边栏
        self.ai_sidebar = AISidebar(self)
        
        # 添加到分割器
        self.splitter.addWidget(self.browser_area)
        self.splitter.addWidget(self.ai_sidebar)
        
        # 设置初始大小比例（侧边栏默认隐藏）
        self.splitter.setSizes([1000, 0])
        
        # 创建状态栏
        self.setup_statusbar()
        
    def create_toolbar(self):
        """创建顶部工具栏"""
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setMovable(False)
        
        # 后退按钮
        back_btn = QPushButton("⬅️")
        back_btn.setToolTip("后退")
        back_btn.clicked.connect(self.navigate_back)
        self.toolbar.addWidget(back_btn)
        
        # 前进按钮
        forward_btn = QPushButton("➡️")
        forward_btn.setToolTip("前进")
        forward_btn.clicked.connect(self.navigate_forward)
        self.toolbar.addWidget(forward_btn)
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("刷新")
        refresh_btn.clicked.connect(self.refresh_page)
        self.toolbar.addWidget(refresh_btn)
        
        # 主页按钮
        home_btn = QPushButton("🏠")
        home_btn.setToolTip("主页")
        home_btn.clicked.connect(self.go_home)
        self.toolbar.addWidget(home_btn)
        
        # 地址栏
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("输入网址或搜索内容...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_bar)
        
        # 新标签页按钮
        new_tab_btn = QPushButton("新建标签页")
        new_tab_btn.clicked.connect(self.create_new_tab)
        self.toolbar.addWidget(new_tab_btn)

        # AI侧边栏切换按钮
        self.ai_toggle_btn = QPushButton("Mindra AI")
        self.ai_toggle_btn.setCheckable(True)
        self.ai_toggle_btn.clicked.connect(self.toggle_ai_sidebar)
        self.toolbar.addWidget(self.ai_toggle_btn)
        
        # 功能菜单按钮
        self.create_function_menu()
        
    def create_function_menu(self):
        """创建功能菜单"""
        # 更多按钮 - 整合书签、下载、历史记录
        more_btn = QPushButton("更多")
        more_btn.setToolTip("更多功能")
        more_btn.clicked.connect(self.show_more_dialog)
        self.toolbar.addWidget(more_btn)
        
        # 添加用户信息按钮
        self.user_info_btn = QPushButton(f"用户：{self.username}")
        self.user_info_btn.setToolTip("当前登录用户")
        self.user_info_btn.clicked.connect(self.show_settings)
        self.toolbar.addWidget(self.user_info_btn)
        
    def setup_statusbar(self):
        """设置状态栏"""
        self.statusBar().showMessage("")
        
    def check_user_login(self):
        """检查用户是否已登录（基于本地保存的登录状态）"""
        # 检查是否需要重新登录（超过一周）
        if UserOperations.should_relogin():
            return False
        
        # 加载用户信息
        user_info = UserOperations.load_user_info()
        if user_info:
            self.user_id = user_info['user_id']
            self.username = user_info['username']
            return True
        
        return False
        
    def setup_managers(self):
        """初始化各种管理器"""
        self.cookie_manager = CookieManager(self.data_dir)
        
        # 加载保存的cookie
        self.cookie_manager.load_cookies()
        
    def ensure_more_dialog(self):
        """确保更多对话框已创建"""
        if not hasattr(self, 'more_dialog') or self.more_dialog is None:
            self.more_dialog = MoreDialog(self, self)
        return self.more_dialog
        
    @property
    def download_manager(self):
        """获取下载管理器"""
        return self.ensure_more_dialog().download_manager
        
    @property
    def bookmarks_manager(self):
        """获取书签管理器"""
        return self.ensure_more_dialog().bookmarks_manager
        
    @property
    def history_manager(self):
        """获取历史记录管理器"""
        return self.ensure_more_dialog().history_manager
        
    def create_home_tab(self):
        """创建首页标签页"""
        self.create_new_tab(title="首页")
        
    def create_new_tab(self, url=None, title="新标签页", index=None):
        """创建新标签页

        Args:
            url: 要加载的URL
            title: 标签页标题
            index: 指定插入位置，None表示在末尾添加
        """
        # 如果没有提供URL，使用默认首页URL
        if url is None:
            url = self.HOME_URL

        # 确保url是字符串类型
        if not isinstance(url, str):
            url = str(url)

        # 检查是否是首页URL
        if url == "mindra:home" or url == self.HOME_URL:
            # 使用QWebEngineView加载homepage.html
            browser = QWebEngineView()

            # 创建自定义页面以处理新窗口
            page = BrowserPage(self, browser)

            # 设置跨域请求支持 - 允许 file:// 协议访问网络
            page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

            browser.setPage(page)

            # 设置下载处理器（只连接一次，避免重复弹窗）
            profile = browser.page().profile()
            if not hasattr(profile, '_download_connected'):
                profile.downloadRequested.connect(self.download_manager.handle_download_request)
                profile._download_connected = True

            # 加载homepage.html
            html_file = Path(__file__).parent / "homepage.html"
            if html_file.exists():
                browser.setUrl(QUrl.fromLocalFile(str(html_file.absolute())))
            else:
                # 如果文件不存在，显示错误页面
                error_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>错误</title>
                </head>
                <body>
                    <h1>首页文件未找到</h1>
                    <p>无法找到 homepage.html 文件</p>
                </body>
                </html>
                """
                browser.setHtml(error_html)

            # 连接信号
            browser.titleChanged.connect(lambda title: self.update_tab_title(browser, title))
            browser.urlChanged.connect(lambda url: self.update_url_bar(url))

            # 添加上下文菜单
            browser.setContextMenuPolicy(Qt.CustomContextMenu)
            browser.customContextMenuRequested.connect(
                lambda pos: self.show_context_menu(browser, pos))

            # 添加标签页
            if index is None:
                insert_index = self.tabs.addTab(browser, "Mindra:HOME")
            else:
                insert_index = self.tabs.insertTab(index, browser, "Mindra:HOME")
            self.tabs.setCurrentIndex(insert_index)
            
            # 设置自定义关闭按钮
            self.setup_tab_close_button(insert_index)

            return browser

        # 创建浏览器视图
        browser = QWebEngineView()

        # 设置自定义页面以处理新窗口
        page = BrowserPage(self, browser)
        browser.setPage(page)

        # 设置下载处理器（只连接一次，避免重复弹窗）
        profile = browser.page().profile()
        if not hasattr(profile, '_download_connected'):
            profile.downloadRequested.connect(self.download_manager.handle_download_request)
            profile._download_connected = True

        # 加载页面
        browser.load(QUrl(url))

        # 连接信号
        browser.titleChanged.connect(lambda title: self.update_tab_title(browser, title))
        browser.urlChanged.connect(lambda url: self.update_url_bar(url))
        browser.loadProgress.connect(self.update_progress)
        browser.loadFinished.connect(self.page_loaded)

        # 添加上下文菜单
        browser.setContextMenuPolicy(Qt.CustomContextMenu)
        browser.customContextMenuRequested.connect(
            lambda pos: self.show_context_menu(browser, pos))

        # 添加标签页
        if index is None:
            insert_index = self.tabs.addTab(browser, title)
        else:
            insert_index = self.tabs.insertTab(index, browser, title)
        self.tabs.setCurrentIndex(insert_index)
        
        # 设置自定义关闭按钮
        self.setup_tab_close_button(insert_index)

        return browser
        
    def close_tab(self, index):
        """关闭标签页"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            # 只有一个标签页时，重置为首页而不是关闭
            self.go_home()
    
    def setup_tab_close_button(self, index):
        """为标签页设置自定义关闭按钮"""
        # 只创建关闭按钮
        close_btn = QLabel("×")
        close_btn.setFixedSize(18, 18)
        close_btn.setAlignment(Qt.AlignCenter)
        close_btn.setStyleSheet(MainWindowStyles.get_tab_close_button_style())
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 绑定关闭事件 - 动态查找当前索引
        def on_close_clicked(event):
            # 找到这个按钮当前所在的标签页索引
            for i in range(self.tabs.count()):
                btn = self.tabs.tabBar().tabButton(i, QTabBar.RightSide)
                if btn == close_btn:
                    self.close_tab(i)
                    break
        
        close_btn.mousePressEvent = on_close_clicked
        
        # 设置标签页的自定义关闭按钮
        self.tabs.tabBar().setTabButton(index, QTabBar.RightSide, close_btn)
        
        # 禁用默认关闭按钮
        self.tabs.tabBar().setTabButton(index, QTabBar.LeftSide, None)
        
    def navigate_back(self):
        """后退"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 普通网页
            if hasattr(current_widget, 'back'):
                current_widget.back()

    def navigate_forward(self):
        """前进"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 普通网页
            if hasattr(current_widget, 'forward'):
                current_widget.forward()
            
    def refresh_page(self):
        """刷新页面"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 检查是否是首页（通过URL判断）
            if hasattr(current_widget, 'url'):
                url = current_widget.url().toString()
                if url.startswith("file://") and "homepage.html" in url:
                    # 首页重新加载
                    current_widget.reload()
                    return
            # 普通网页
            if hasattr(current_widget, 'reload'):
                current_widget.reload()
            
    def go_home(self):
        """返回首页"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 检查是否已经是首页（通过URL判断）
            if hasattr(current_widget, 'url'):
                url = current_widget.url().toString()
                if url.startswith("file://") and "homepage.html" in url:
                    return

            # 删除当前标签页并在同一位置创建首页
            current_index = self.tabs.currentIndex()
            self.tabs.removeTab(current_index)
            self.create_new_tab(url=self.HOME_URL, title="Mindra:HOME", index=current_index)
            
    def navigate_to_url(self):
        """导航到URL"""
        url = self.url_bar.text()

        # 检查是否是首页URL
        if url == "mindra:home" or url == self.HOME_URL:
            self.go_home()
            return

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 检查是否是首页（通过URL判断）
            if hasattr(current_widget, 'url'):
                current_url = current_widget.url().toString()
                if current_url.startswith("file://") and "homepage.html" in current_url:
                    # 首页需要创建新的浏览器标签页
                    self.create_new_tab(url=url, title="新标签页")
                    return

            # 普通网页浏览器
            if hasattr(current_widget, 'load'):
                current_widget.load(QUrl(url))
            
    def update_tab_title(self, browser, title):
        """更新标签页标题"""
        index = self.tabs.indexOf(browser)
        if index != -1:
            # 限制标题长度
            if len(title) > 20:
                display_title = title[:20] + "..."
            else:
                display_title = title
            self.tabs.setTabText(index, display_title)
            
            # 设置标签页工具提示显示完整标题
            self.tabs.setTabToolTip(index, title)
            
    def on_tab_changed(self, index):
        """标签页切换时更新地址栏"""
        if index >= 0:  # 确保有有效的标签页索引
            current_widget = self.tabs.widget(index)
            if current_widget:
                # 检查是否是首页（通过URL判断）
                if hasattr(current_widget, 'url'):
                    url = current_widget.url().toString()
                    if url.startswith("file://") and "homepage.html" in url:
                        self.url_bar.setText(self.HOME_URL)
                    else:
                        # 普通网页浏览器
                        self.url_bar.setText(url)
                
    def update_url_bar(self, url):
        """更新地址栏"""
        current_widget = self.tabs.currentWidget()
        if current_widget:
            # 检查是否是首页
            if hasattr(current_widget, 'url'):
                current_url = current_widget.url().toString()
                if current_url.startswith("file://") and "homepage.html" in current_url:
                    # 首页，显示首页URL
                    self.url_bar.setText(self.HOME_URL)
                    return

            # 普通网页
            if hasattr(current_widget, 'url') and current_widget.url() == url:
                self.url_bar.setText(url.toString())

                # 添加到历史记录
                if hasattr(current_widget, 'title'):
                    self.history_manager.add_entry(url.toString(),
                                                 current_widget.title(),
                                                 datetime.now())
            
    def update_progress(self, progress):
        """更新加载进度"""
        if progress < 100:
            self.statusBar().showMessage(f"加载中... {progress}%")
        else:
            self.statusBar().showMessage("页面加载完成")
            QTimer.singleShot(1000, lambda: self.statusBar().clearMessage())
            
    def page_loaded(self):
        """页面加载完成"""
        self.statusBar().showMessage("页面加载完成")
        QTimer.singleShot(1000, lambda: self.statusBar().clearMessage())
        
    def toggle_ai_sidebar(self):
        """切换AI侧边栏显示/隐藏"""
        if self.ai_toggle_btn.isChecked():
            # 显示侧边栏 - 设置初始宽度为400像素，允许用户拉伸
            self.splitter.setSizes([800, 400])  # 侧边栏初始宽度400像素
            self.ai_sidebar.show()
        else:
            # 隐藏侧边栏
            self.splitter.setSizes([1000, 0])
            self.ai_sidebar.hide()
            
    def show_context_menu(self, browser, pos):
        """显示右键上下文菜单 - 根据是否选中文本动态显示选项"""
        # 检查当前页面是否是首页（homepage.html）
        current_url = browser.url().toString()
        if current_url.startswith("file://") and "homepage.html" in current_url:
            # 在首页禁用右键菜单
            return
        
        # 先获取选中的文本，然后根据结果显示菜单
        js_code = """
            (function() {
                var selection = window.getSelection();
                var text = selection ? selection.toString() : '';
                if (!text && document.activeElement) {
                    var el = document.activeElement;
                    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                        text = el.value.substring(el.selectionStart, el.selectionEnd);
                    }
                }
                return text || '';
            })()
        """
        
        # 使用闭包捕获 browser 和 pos
        def on_selection_received(selected_text):
            self._display_context_menu(browser, pos, selected_text)
        
        browser.page().runJavaScript(js_code, on_selection_received)
    
    def _display_context_menu(self, browser, pos, selected_text):
        """根据选中的文本显示上下文菜单"""
        menu = QMenu(self)
        
        # 应用统一的右键菜单样式
        menu.setStyleSheet(MenuStyles.get_context_menu_style())
        
        # 添加基本选项（始终显示）
        menu.addAction("📄 页面总结", self.summarize_current_page)
        menu.addAction("查看页面源代码", 
                      lambda: self.view_page_source(browser))
        menu.addAction("添加到书签", self.add_current_to_bookmarks)
        
        # 检查是否有选中的文本
        has_selection = isinstance(selected_text, str) and selected_text.strip()
        
        # 如果有选中的文本，添加划词解释和翻译选项
        if has_selection:
            selection_text = selected_text.strip()
            menu.addSeparator()
            menu.addAction("📖 划词解释", 
                          lambda: self.handle_selection_explain(selection_text))
            menu.addAction("🌍 划词翻译", 
                          lambda: self.handle_selection_translate(selection_text))
        
        # 显示菜单
        menu.exec_(browser.mapToGlobal(pos))
        
    def handle_selection_explain(self, text):
        """处理划词解释"""
        # 确保AI侧边栏可见
        if not self.ai_toggle_btn.isChecked():
            self.ai_toggle_btn.setChecked(True)
            self.toggle_ai_sidebar()
            
        # 发送到AI侧边栏
        self.ai_sidebar.handle_selection_explain(text)
        
    def handle_selection_translate(self, text):
        """处理划词翻译"""
        # 确保AI侧边栏可见
        if not self.ai_toggle_btn.isChecked():
            self.ai_toggle_btn.setChecked(True)
            self.toggle_ai_sidebar()
            
        # 发送到AI侧边栏
        self.ai_sidebar.handle_selection_translate(text)
        
    def summarize_current_page(self):
        """总结当前页面"""
        # 确保AI侧边栏可见
        if not self.ai_toggle_btn.isChecked():
            self.ai_toggle_btn.setChecked(True)
            self.toggle_ai_sidebar()
            
        # 调用AI侧边栏的页面总结功能
        self.ai_sidebar.explain_current_page()
        
    def view_page_source(self, browser):
        """查看页面源代码"""
        browser.page().toHtml(lambda html: self.show_page_source(html))
        
    def show_page_source(self, page_html):
        """显示页面源代码"""
        # 创建新的浏览器实例用于显示源代码
        source_browser = QWebEngineView()
        
        # 转义HTML代码以便在pre标签中正确显示
        escaped_html = html_module.escape(page_html)
        
        # 创建格式化的源代码页面
        source_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>页面源代码</title>
            <style>
                body {{ 
                    font-family: "Microsoft YaHei"; 
                    background-color: #f5f5f5; 
                    margin: 20px; 
                    line-height: 1.4;
                }}
                pre {{ 
                    background-color: #fff; 
                    padding: 20px; 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    white-space: pre-wrap; 
                    word-wrap: break-word;
                    font-size: 12px;
                }}
                h1 {{ 
                    color: #333; 
                    margin-bottom: 15px;
                }}
            </style>
        </head>
        <body>
            <h1>页面源代码</h1>
            <pre>{escaped_html}</pre>
        </body>
        </html>
        """
        
        # 添加到标签页
        index = self.tabs.addTab(source_browser, "页面源代码")
        self.tabs.setCurrentIndex(index)
        
        # 设置自定义关闭按钮
        self.setup_tab_close_button(index)
        
        # 设置HTML内容
        source_browser.setHtml(source_html, QUrl("about:blank"))
        
    def add_current_to_bookmarks(self):
        """添加当前页面到书签"""
        current_browser = self.tabs.currentWidget()
        if current_browser:
            url = current_browser.url().toString()
            title = current_browser.title()
            self.bookmarks_manager.add_bookmark(url, title)
            
    def show_settings(self):
        """显示设置窗口"""
        dialog = SettingsDialog(self)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def show_more_dialog(self):
        """显示更多功能对话框"""
        dialog = self.ensure_more_dialog()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存cookie
        self.cookie_manager.save_cookies()
        event.accept()


class BrowserPage(QWebEnginePage):
    """自定义浏览器页面，处理新窗口打开和导航请求"""
    
    # 常见视频网站列表（域名关键字）
    VIDEO_SITES = [
        # 国内视频网站
        'bilibili.com', 'b23.tv',
        'youtube.com', 'youtu.be',
        'iqiyi.com', 'iq.com',
        'youku.com',
        'v.qq.com', 'm.v.qq.com',
        'mgtv.com',
        'le.com',
        'pptv.com',
        'acfun.cn',
        'xinpianchang.com',
        'douyin.com', 'iesdouyin.com',
        'kuaishou.com',
        'ixigua.com',
        'haokan.baidu.com',
        # 国外视频网站
        'netflix.com',
        'hulu.com',
        'disneyplus.com', 'disney.com',
        'primevideo.com', 'amazon.com/video',
        'hbomax.com', 'max.com',
        'vimeo.com',
        'dailymotion.com',
        'twitch.tv',
        'tiktok.com',
        'twitter.com', 'x.com',
        'facebook.com', 'fb.watch',
        'instagram.com',
    ]
    
    def __init__(self, parent=None, browser_view=None):
        super().__init__(parent)
        self.parent = parent
        self.browser_view = browser_view
        
    def is_video_site(self, url):
        """判断URL是否是视频网站"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # 移除 www. 前缀进行匹配
            if domain.startswith('www.'):
                domain = domain[4:]
            
            for site in self.VIDEO_SITES:
                if site in domain:
                    return True
            return False
        except:
            return False
    
    def acceptNavigationRequest(self, url, type, isMainFrame):
        """拦截导航请求，检测视频网站"""
        url_str = url.toString()
        
        # 只检测用户点击链接的情况，其他情况（重定向、输入URL等）不检测
        if type != QWebEnginePage.NavigationTypeLinkClicked:
            return True
        
        # 检查是否是视频网站
        if self.is_video_site(url_str):
            # 获取网站名称用于提示
            domain = urlparse(url_str).netloc.lower()
            site_name = domain.replace('www.', '')
            
            # 弹出确认对话框
            msg_box = QMessageBox(self.parent)
            msg_box.setWindowTitle("视频网站检测")
            msg_box.setText(f"检测到视频网站: {site_name}")
            msg_box.setInformativeText("由于浏览器内置的 Qt WebEngine 不支持专有视频编解码器，\n该网站的视频可能无法正常播放。\n\n是否使用系统默认浏览器打开？")
            msg_box.setIcon(QMessageBox.Question)
            
            open_external_btn = msg_box.addButton("使用默认浏览器打开", QMessageBox.YesRole)
            continue_btn = msg_box.addButton("继续在当前页面打开", QMessageBox.NoRole)
            msg_box.setDefaultButton(open_external_btn)
            
            msg_box.exec()
            
            clicked_btn = msg_box.clickedButton()
            
            if clicked_btn == open_external_btn:
                # 使用系统默认浏览器打开
                webbrowser.open(url_str)
                # 关闭当前标签页
                if self.browser_view and self.parent:
                    index = self.parent.tabs.indexOf(self.browser_view)
                    if index != -1:
                        self.parent.close_tab(index)
                return False  # 阻止在当前页面加载
            else:
                # 用户选择继续在当前页面打开
                return True
        
        # 非视频网站，正常加载
        return True
        
    def createWindow(self, webWindowType):
        """创建新窗口（标签页）"""
        if self.parent:
            # 创建新的浏览器页面
            new_browser = self.parent.create_new_tab()
            if new_browser:
                return new_browser.page()
        return None

def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Mindra")
    app.setApplicationVersion("1.0.0")
    app.setWindowIcon(QIcon(resource_path("Mindra_logo.png")))
    
    # 创建主窗口
    window = BrowserWindow()
    window.setWindowIcon(QIcon(resource_path("Mindra_logo.png")))
    window.showMaximized()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()