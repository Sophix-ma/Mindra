from PySide6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QWidget, 
                               QPushButton, QLabel, QStackedWidget, QLineEdit,
                               QMessageBox, QTableWidget, QTableWidgetItem,
                               QHeaderView)
from PySide6.QtCore import Qt
from style_settings import DialogStyles, ButtonStyles, InputStyles, MessageStyles
from user_operations import UserOperations


class SettingsDialog(QDialog):
    """设置窗口 - 与MoreDialog相同的布局结构"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setGeometry(200, 200, 800, 600)
        
        # Load current user info
        self.user_info = UserOperations.load_user_info()
        if not self.user_info:
            # Handle case where no user is logged in
            self.user_info = {'user_id': None, 'username': '未登录'}
        
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
        title_label = QLabel("设置")
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
        
        # 账号管理按钮
        self.account_btn = QPushButton("👤 账号管理")
        self.account_btn.setCheckable(True)
        self.account_btn.setChecked(True)
        self.account_btn.clicked.connect(lambda: self.switch_page(0))
        self.style_menu_button(self.account_btn)
        left_layout.addWidget(self.account_btn)
        self.menu_buttons.append(self.account_btn)
        
        # 大模型用量按钮
        self.credit_btn = QPushButton("🤖 大模型用量")
        self.credit_btn.setCheckable(True)
        self.credit_btn.clicked.connect(lambda: self.switch_page(1))
        self.style_menu_button(self.credit_btn)
        left_layout.addWidget(self.credit_btn)
        self.menu_buttons.append(self.credit_btn)
        
        left_layout.addStretch()
        
        layout.addWidget(self.left_panel)
        
        # 右侧内容区域 - 使用堆叠部件
        self.stack = QStackedWidget()
        
        # 创建账号管理页面
        self.account_page = self.create_account_page()
        self.stack.addWidget(self.account_page)
        
        # 创建大模型用量页面
        self.credit_page = self.create_credit_page()
        self.stack.addWidget(self.credit_page)
        
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
        
    def create_account_page(self):
        """创建账号管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("账号管理")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 20px;
            qproperty-alignment: 'AlignCenter';
        """)
        layout.addWidget(title_label)
        
        # 当前用户名显示
        current_user_layout = QHBoxLayout()
        current_user_layout.setSpacing(10)
        current_user_label = QLabel("当前用户:")
        current_user_label.setFixedWidth(80)
        self.current_user_value = QLabel(self.user_info['username'])  # Store reference to update later
        self.current_user_value.setStyleSheet("""
            color: #2c3e50;
            font-weight: normal;
            font-size: 14px;
        """)
        current_user_layout.addWidget(current_user_label)
        current_user_layout.addWidget(self.current_user_value)
        layout.addLayout(current_user_layout)
        
        layout.addSpacing(20)
        
        # 修改用户名部分
        username_group = self.create_username_change_section()
        layout.addWidget(username_group)
        
        layout.addSpacing(20)
        
        # 修改密码部分
        password_group = self.create_password_change_section()
        layout.addWidget(password_group)
        
        layout.addStretch()
        
        return page
    
    def create_username_change_section(self):
        """创建修改用户名部分"""
        group = QWidget()
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(15)
        
        # 标题
        section_title = QLabel("修改用户名")
        section_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1565c0;
            padding-bottom: 10px;
        """)
        group_layout.addWidget(section_title)
        
        # 当前密码输入（用于验证）
        current_pwd_layout = QHBoxLayout()
        current_pwd_layout.setSpacing(10)
        current_pwd_label = QLabel("当前密码:")
        current_pwd_label.setFixedWidth(80)
        self.current_pwd_for_username = QLineEdit()
        self.current_pwd_for_username.setPlaceholderText("请输入当前密码以验证身份")
        self.current_pwd_for_username.setEchoMode(QLineEdit.Password)
        self.current_pwd_for_username.setStyleSheet(InputStyles.get_line_edit_style())
        current_pwd_layout.addWidget(current_pwd_label)
        current_pwd_layout.addWidget(self.current_pwd_for_username)
        group_layout.addLayout(current_pwd_layout)
        
        # 新用户名输入
        new_username_layout = QHBoxLayout()
        new_username_layout.setSpacing(10)
        new_username_label = QLabel("新用户名:")
        new_username_label.setFixedWidth(80)
        self.new_username_input = QLineEdit()
        self.new_username_input.setPlaceholderText("请输入新的用户名")
        self.new_username_input.setStyleSheet(InputStyles.get_line_edit_style())
        new_username_layout.addWidget(new_username_label)
        new_username_layout.addWidget(self.new_username_input)
        group_layout.addLayout(new_username_layout)
        
        # 修改用户名按钮
        self.update_username_btn = QPushButton("更新用户名")
        self.update_username_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.update_username_btn.setFixedWidth(120)  # Set fixed width for consistent button size
        self.update_username_btn.clicked.connect(self.update_username)
        group_layout.addWidget(self.update_username_btn, alignment=Qt.AlignCenter)
        
        return group
    
    def create_password_change_section(self):
        """创建修改密码部分"""
        group = QWidget()
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(15)
        
        # 标题
        section_title = QLabel("修改密码")
        section_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1565c0;
            padding-bottom: 10px;
        """)
        group_layout.addWidget(section_title)
        
        # 当前密码输入
        current_pwd_layout = QHBoxLayout()
        current_pwd_layout.setSpacing(10)
        current_pwd_label = QLabel("当前密码:")
        current_pwd_label.setFixedWidth(80)
        self.current_password_input = QLineEdit()
        self.current_password_input.setPlaceholderText("请输入当前密码")
        self.current_password_input.setEchoMode(QLineEdit.Password)
        self.current_password_input.setStyleSheet(InputStyles.get_line_edit_style())
        current_pwd_layout.addWidget(current_pwd_label)
        current_pwd_layout.addWidget(self.current_password_input)
        group_layout.addLayout(current_pwd_layout)
        
        # 新密码输入
        new_pwd_layout = QHBoxLayout()
        new_pwd_layout.setSpacing(10)
        new_pwd_label = QLabel("新密码:")
        new_pwd_label.setFixedWidth(80)
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("请输入新密码（至少6位）")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setStyleSheet(InputStyles.get_line_edit_style())
        new_pwd_layout.addWidget(new_pwd_label)
        new_pwd_layout.addWidget(self.new_password_input)
        group_layout.addLayout(new_pwd_layout)
        
        # 确认新密码输入
        confirm_pwd_layout = QHBoxLayout()
        confirm_pwd_layout.setSpacing(10)
        confirm_pwd_label = QLabel("确认密码:")
        confirm_pwd_label.setFixedWidth(80)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("请再次输入新密码")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setStyleSheet(InputStyles.get_line_edit_style())
        confirm_pwd_layout.addWidget(confirm_pwd_label)
        confirm_pwd_layout.addWidget(self.confirm_password_input)
        group_layout.addLayout(confirm_pwd_layout)
        
        # 修改密码按钮
        self.update_password_btn = QPushButton("更新密码")
        self.update_password_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.update_password_btn.setFixedWidth(120)  # Set same fixed width as username button
        self.update_password_btn.clicked.connect(self.update_password)
        group_layout.addWidget(self.update_password_btn, alignment=Qt.AlignCenter)
        
        return group
    
    def update_username(self):
        """更新用户名"""
        if not self.user_info or not self.user_info['user_id']:
            msg_box = QMessageBox(QMessageBox.Warning, "错误", "请先登录", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        current_password = self.current_pwd_for_username.text().strip()
        new_username = self.new_username_input.text().strip()
        
        if not current_password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请输入当前密码", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if not new_username:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请输入新用户名", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        # 执行更新
        result = UserOperations.update_username(
            self.user_info['user_id'], 
            current_password, 
            new_username
        )
        
        if result['success']:
            # 更新本地用户信息文件
            UserOperations.save_user_info(self.user_info['user_id'], new_username)
            self.user_info['username'] = new_username
            
            # 更新当前用户显示
            self.current_user_value.setText(new_username)
            
            # 更新主窗口的用户信息按钮（if parent is BrowserWindow)
            if hasattr(self.parent(), 'user_info_btn'):
                self.parent().user_info_btn.setText(f"用户：{new_username}")
                # Also update the parent's username attribute
                if hasattr(self.parent(), 'username'):
                    self.parent().username = new_username
            
            msg_box = QMessageBox(QMessageBox.Information, "成功", result['message'], parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            
            # 清空输入框
            self.current_pwd_for_username.clear()
            self.new_username_input.clear()
        else:
            msg_box = QMessageBox(QMessageBox.Warning, "失败", result['message'], parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
    
    def update_password(self):
        """更新密码"""
        if not self.user_info or not self.user_info['user_id']:
            msg_box = QMessageBox(QMessageBox.Warning, "错误", "请先登录", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        current_password = self.current_password_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        
        if not current_password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请输入当前密码", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if not new_password or not confirm_password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请填写新密码和确认密码", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if new_password != confirm_password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "两次输入的密码不一致", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if len(new_password) < 6:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "新密码长度至少6位", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        # 执行更新
        result = UserOperations.update_password(
            self.user_info['user_id'], 
            current_password, 
            new_password
        )
        
        if result['success']:
            msg_box = QMessageBox(QMessageBox.Information, "成功", result['message'], parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            
            # 清空输入框
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
        else:
            msg_box = QMessageBox(QMessageBox.Warning, "失败", result['message'], parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
    
    def create_credit_page(self):
        """创建大模型用量页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 标题
        title_label = QLabel("大模型用量")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 20px;
            qproperty-alignment: 'AlignCenter';
        """)
        layout.addWidget(title_label)
        
        # 当前用户显示
        current_user_layout = QHBoxLayout()
        current_user_layout.setSpacing(10)
        current_user_label = QLabel("当前用户:")
        current_user_label.setFixedWidth(80)
        current_user_value = QLabel(self.user_info['username'])
        current_user_value.setStyleSheet("""
            color: #2c3e50;
            font-weight: normal;
            font-size: 14px;
        """)
        current_user_layout.addWidget(current_user_label)
        current_user_layout.addWidget(current_user_value)
        layout.addLayout(current_user_layout)
        
        # 剩余credit显示
        credit_balance_layout = QHBoxLayout()
        credit_balance_layout.setSpacing(10)
        credit_balance_label = QLabel("剩余Credit:")
        credit_balance_label.setFixedWidth(80)
        
        # 获取用户credit余额
        credit_balance = 0
        if self.user_info and self.user_info['user_id']:
            credit_balance = UserOperations.get_user_credit_balance(self.user_info['user_id'])
        
        self.credit_balance_value = QLabel(str(credit_balance))
        self.credit_balance_value.setStyleSheet("""
            color: #27ae60;
            font-weight: bold;
            font-size: 16px;
        """)
        credit_balance_layout.addWidget(credit_balance_label)
        credit_balance_layout.addWidget(self.credit_balance_value)
        layout.addLayout(credit_balance_layout)
        
        layout.addSpacing(20)
        
        # 用量历史标题和清空按钮
        history_layout = QHBoxLayout()
        history_title = QLabel("使用历史")
        history_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1565c0;
            padding-bottom: 10px;
        """)
        history_layout.addWidget(history_title)
        
        # 清空历史按钮
        self.clear_history_btn = QPushButton("清空历史")
        self.clear_history_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.clear_history_btn.setFixedWidth(100)
        self.clear_history_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(self.clear_history_btn)
        history_layout.addStretch()
        
        layout.addLayout(history_layout)
        
        # 用量历史表格
        self.credit_table = QTableWidget()
        self.credit_table.setColumnCount(5)
        self.credit_table.setHorizontalHeaderLabels(["任务类型", "输入Token", "输出Token", "消耗Credit", "使用时间"])
        
        # 设置列宽
        header = self.credit_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        
        # 设置表格属性
        self.credit_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.credit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.credit_table.setSelectionMode(QTableWidget.ExtendedSelection)
        
        # 填充表格数据
        if self.user_info and self.user_info['user_id']:
            self.load_credit_history()
        
        layout.addWidget(self.credit_table)
        
        return page
    
    def load_credit_history(self):
        """加载credit使用历史"""
        # 获取用户credit使用历史
        history = UserOperations.get_credit_usage_history(self.user_info['user_id'])
        
        # 清空表格
        self.credit_table.setRowCount(0)
        
        # 填充表格
        for row_idx, record in enumerate(history):
            self.credit_table.insertRow(row_idx)
            
            # 任务类型
            assignment_item = QTableWidgetItem(record['assignment'])
            self.credit_table.setItem(row_idx, 0, assignment_item)
            
            # 输入Token
            input_token_item = QTableWidgetItem(str(record['input_token_usage']))
            input_token_item.setTextAlignment(Qt.AlignRight)
            self.credit_table.setItem(row_idx, 1, input_token_item)
            
            # 输出Token
            output_token_item = QTableWidgetItem(str(record['output_token_usage']))
            output_token_item.setTextAlignment(Qt.AlignRight)
            self.credit_table.setItem(row_idx, 2, output_token_item)
            
            # 消耗Credit
            credit_usage_item = QTableWidgetItem(str(record['credit_usage']))
            credit_usage_item.setTextAlignment(Qt.AlignRight)
            self.credit_table.setItem(row_idx, 3, credit_usage_item)
            
            # 使用时间
            created_at_item = QTableWidgetItem(str(record['created_at']))
            self.credit_table.setItem(row_idx, 4, created_at_item)
    
    def clear_history(self):
        """清空credit使用历史"""
        if not self.user_info or not self.user_info['user_id']:
            msg_box = QMessageBox(QMessageBox.Warning, "错误", "请先登录", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
        
        # 确认清空操作
        reply = QMessageBox.question(self, "确认", "确定要清空所有使用历史吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 执行清空操作
            result = UserOperations.clear_credit_usage_history(self.user_info['user_id'])
            
            if result:
                # 更新表格显示
                self.load_credit_history()
                msg_box = QMessageBox(QMessageBox.Information, "成功", "使用历史已清空", parent=self)
                msg_box.setStyleSheet(MessageStyles.get_message_box_style())
                msg_box.exec()
            else:
                msg_box = QMessageBox(QMessageBox.Warning, "失败", "清空使用历史失败", parent=self)
                msg_box.setStyleSheet(MessageStyles.get_message_box_style())
                msg_box.exec()
    
    def keyPressEvent(self, event):
        """重写按键事件，忽略Enter键"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 忽略Enter键，不执行任何操作
            return
        super().keyPressEvent(event)