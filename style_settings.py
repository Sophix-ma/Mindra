class MenuStyles:
    """右键菜单样式管理类"""
    
    @staticmethod
    def get_context_menu_style():
        """获取统一的右键菜单样式"""
        return """
            QMenu {
                background-color: #f8f9fa;
                border: 1px solid #e3f2fd;
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 15px;
                border-radius: 8px;
                color: #333;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
        """


class ButtonStyles:
    """按钮样式管理类"""
    
    @staticmethod
    def get_control_button_style():
        """获取控制按钮样式"""
        return """
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                margin: 2px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
        """
    
    @staticmethod
    def get_menu_button_style():
        """获取菜单按钮样式"""
        return """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: #555;
                font-weight: bold;
                font-family: "Microsoft YaHei";
                font-size: 13px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                color: #1565c0;
            }
            QPushButton:checked {
                background-color: #64b5f6;
                color: white;
            }
        """
    

class InputStyles:
    """输入框样式管理类"""
    
    @staticmethod
    def get_line_edit_style():
        """获取文本输入框样式"""
        return """
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
        """
    
    @staticmethod
    def get_combo_box_style():
        """获取下拉框样式"""
        return """
            QComboBox {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-family: "Microsoft YaHei";
            }
        """
    
    @staticmethod
    def get_date_edit_style():
        """获取日期选择框样式"""
        return """
            QDateEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-family: "Microsoft YaHei";
            }
        """


class DialogStyles:
    """对话框样式管理类"""
    
    @staticmethod
    def get_bookmarks_manager_style():
        """获取书签管理器样式"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                margin: 2px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                gridline-color: #e3f2fd;
                selection-background-color: #e3f2fd;
                selection-color: #333;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e3f2fd;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
        """
    
    @staticmethod
    def get_download_manager_style():
        """获取下载管理器样式"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                margin: 2px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                gridline-color: #e3f2fd;
                selection-background-color: #e3f2fd;
                selection-color: #333;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e3f2fd;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
            QProgressBar {
                font-family: "Microsoft YaHei";
            }
        """
    
    @staticmethod
    def get_history_manager_style():
        """获取历史记录管理器样式"""
        return """
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                margin: 2px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                gridline-color: #e3f2fd;
                selection-background-color: #e3f2fd;
                selection-color: #333;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e3f2fd;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
        """
    
    @staticmethod
    def get_more_dialog_style():
        """获取更多功能对话框样式"""
        return """
            QDialog {
                background-color: white;
            }
            QPushButton {
                font-family: "Microsoft YaHei";
            }
            QLabel {
                font-family: "Microsoft YaHei";
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                gridline-color: #e3f2fd;
                selection-background-color: #e3f2fd;
                selection-color: #333;
                outline: none;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e3f2fd;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #333;
            }
            QHeaderView::section {
                background-color: #e3f2fd;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QComboBox {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-family: "Microsoft YaHei";
            }
            QDateEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-family: "Microsoft YaHei";
            }
            QProgressBar {
                border: 1px solid #bbdefb;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #64b5f6;
                border-radius: 4px;
            }
        """


class MainWindowStyles:
    """主窗口样式管理类"""
    
    @staticmethod
    def get_main_window_style():
        """获取主窗口样式"""
        return """
            QMainWindow {
                background-color: #f8f9fa;
            }
            QToolBar {
                background-color: #f8f9fa;
                padding: 5px;
            }
            QToolBar QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #e3f2fd;
                border-radius: 10px;
                padding: 8px 15px;
                color: #333;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QToolBar QPushButton:hover {
                background-color: #e9ecef;
                border: 1px solid #e9ecef;
            }
            QToolBar QPushButton:pressed {
                background-color: #dee2e6;
                border: 1px solid #dee2e6;
            }
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: white;
                font-size: 14px;
                font-family: "Microsoft YaHei";
            }
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 10px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
            QTabWidget::pane {
                border: none;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #e3f2fd;
                padding: 8px 15px;
                margin-right: 2px;
                width: 150px;
                font-family: "Microsoft YaHei";
                color: #333;
                font-weight: bold;
                border-radius: 10px;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
                border: 1px solid #e9ecef;
            }
            QTabBar::tab:selected {
                background-color: #e3f2fd;
                color: #333;
                border: 1px solid #e3f2fd;
            }
            QTabBar::close-button {
                background-color: transparent;
                border: none;
                image: none;
            }
            QTabBar::close-button:hover {
                background-color: transparent;
                border: none;
            }
            QSplitter::handle {
                background-color: #f8f9fa;
            }
        """
    
    @staticmethod
    def get_tab_close_button_style():
        """获取标签页关闭按钮样式"""
        return """
            QLabel {
                background-color: transparent;
                color: #666666;
                font-size: 18px;
                font-weight: 300;
                padding-bottom: 2px;
                border: none;
                border-radius: 3px;
            }
            QLabel:hover {
                color: #333333;
                background-color: rgba(0, 0, 0, 0.1);
            }
        """


class AISidebarStyles:
    """AI侧边栏样式管理类"""
    
    @staticmethod
    def get_sidebar_style():
        """获取侧边栏整体样式"""
        return """
            QWidget {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-weight: bold;
                margin: 2px;
                font-family: "Microsoft YaHei";
            }
            QPushButton:hover {
                background-color: #42a5f5;
            }
            QPushButton:pressed {
                background-color: #1e88e5;
            }
        """
    
    @staticmethod
    def get_chat_scroll_style():
        """获取聊天滚动区域样式"""
        return """
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """
    
    @staticmethod
    def get_input_field_style():
        """获取输入框样式"""
        return """
            QTextEdit {
                border: none;
                padding: 0px;
                background-color: transparent;
                font-family: "Microsoft YaHei";
                font-size: 14px;
                color: #333333;
            }
        """
    
    @staticmethod
    def get_tool_button_style(hover_color, pressed_color):
        """获取工具按钮样式（可自定义悬停和按下颜色）"""
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 4px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-radius: 4px;
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
                border-radius: 4px;
            }}
        """
    
    @staticmethod
    def get_toggle_button_style():
        """获取切换按钮样式（带checked状态）"""
        return """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
                border-radius: 4px;
            }
            QPushButton:checked:pressed {
                background-color: #bbdefb;
                border-radius: 4px;
            }
        """
    
    @staticmethod
    def get_send_button_style():
        """获取发送按钮样式"""
        return """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e8f5e9;
                border-radius: 4px;
            }
            QPushButton:pressed {
                background-color: #c8e6c9;
                border-radius: 4px;
            }
        """


class MessageStyles:
    """消息框样式管理类"""
    
    @staticmethod
    def get_message_box_style():
        """获取消息框样式"""
        return """
            QMessageBox {
                background-color: #f8f9fa;
                font-family: "Microsoft YaHei";
                width: 350px;
                height: 120px;
            }
            QMessageBox QLabel {
                color: #333;
                font-size: 14px;
                width: 300px;
                height: 80px;
            }
            QMessageBox QPushButton {
                background-color: #64b5f6;
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                color: white;
                font-weight: bold;
                font-family: "Microsoft YaHei";
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #42a5f5;
            }
            QMessageBox QPushButton:pressed {
                background-color: #1e88e5;
            }
        """
