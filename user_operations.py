import hashlib
import pymysql
import json
import csv
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from pymysql import Error
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox)
from PySide6.QtCore import Qt
from style_settings import ButtonStyles, InputStyles, MessageStyles


class DBConnection:
    def __init__(self):
        # Load database configuration from config.yaml
        config_path = Path("config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            db_config = config['database']
            self.host = db_config['host']
            self.database = db_config['database']
            self.user = db_config['user']
            self.password = db_config['password']
        
        self.connection = None
        self.connect()
        
    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                cursorclass=pymysql.cursors.DictCursor  # 返回字典格式结果
            )
            self.connection.ping(reconnect=False)
            return True
        except Error as e:
            print(f"数据库连接错误: {e}")
            return False
        
    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Error as e:
                print(f"关闭数据库连接错误: {e}")
            
    def get_cursor(self):
        if self.connection:
            try:
                # 检查连接并自动重连
                self.connection.ping(reconnect=True)
                return self.connection.cursor()
            except Error as e:
                print(f"获取数据库游标错误: {e}")
                return None
        return None


class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录 - Mindra")
        self.setFixedSize(350, 250)
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        """设置对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f5ff;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
    def setup_ui(self):
        """设置登录界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("用户登录")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)  # 设置固定高度确保文字完整显示
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 20px;
            qproperty-alignment: 'AlignCenter';
        """)
        layout.addWidget(title_label)
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_layout.setSpacing(10)
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(50)  # 设置固定宽度
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet(InputStyles.get_line_edit_style())
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_layout.setSpacing(10)
        password_label = QLabel("密码:")
        password_label.setFixedWidth(50)  # 设置固定宽度
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(InputStyles.get_line_edit_style())
        # 移除 returnPressed 连接，使 Enter 键无反应
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)

        layout.addSpacing(20)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.register_btn.clicked.connect(self.open_register)
        # 移除 setDefault(True)，确保 Enter 键无反应
        button_layout.addWidget(self.register_btn)

        self.login_btn = QPushButton("登录")
        self.login_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.login_btn.clicked.connect(self.attempt_login)
        # 移除 setDefault(True)，确保 Enter 键无反应
        button_layout.addWidget(self.login_btn)
        
        layout.addLayout(button_layout)
        
    def open_register(self):
        """打开注册窗口"""
        self.register_dialog = RegisterDialog(self)
        if self.register_dialog.exec() == QDialog.Accepted:
            # 注册成功，自动填充用户名
            self.username_input.setText(self.register_dialog.username)
        
    def attempt_login(self):
        """尝试登录"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请输入用户名和密码", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        # 验证登录
        user_info = UserOperations.verify_login(username, password)
        if user_info:
            self.user_id = user_info['user_id']
            self.username = user_info['username']
            
            # 保存用户登录信息
            if UserOperations.save_user_info(self.user_id, self.username):
                self.accept()  # 登录成功
            else:
                msg_box = QMessageBox(QMessageBox.Warning, "登录失败", "保存用户信息失败", parent=self)
                msg_box.setStyleSheet(MessageStyles.get_message_box_style())
                msg_box.exec()
        else:
            msg_box = QMessageBox(QMessageBox.Warning, "登录失败", "用户名或密码错误", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
    
    def keyPressEvent(self, event):
        """重写按键事件，忽略Enter键"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 忽略Enter键，不执行任何操作
            return
        super().keyPressEvent(event)


class RegisterDialog(QDialog):
    """注册对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("注册 - Mindra")
        self.setFixedSize(400, 350)
        self.setup_styles()
        self.setup_ui()
        
    def setup_styles(self):
        """设置对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f5ff;
                font-family: "Microsoft YaHei";
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        
    def setup_ui(self):
        """设置注册界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("用户注册")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)  # 设置固定高度确保文字完整显示
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #1a73e8;
            margin-bottom: 20px;
            qproperty-alignment: 'AlignCenter';
        """)
        layout.addWidget(title_label)
        
        # 用户名输入
        username_layout = QHBoxLayout()
        username_layout.setSpacing(10)
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(60)  # 设置固定宽度
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet(InputStyles.get_line_edit_style())
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        layout.addLayout(username_layout)
        
        # 密码输入
        password_layout = QHBoxLayout()
        password_layout.setSpacing(10)
        password_label = QLabel("密码:")
        password_label.setFixedWidth(60)  # 设置固定宽度
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(InputStyles.get_line_edit_style())
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # 确认密码输入
        confirm_layout = QHBoxLayout()
        confirm_layout.setSpacing(10)
        confirm_label = QLabel("确认密码:")
        confirm_label.setFixedWidth(60)  # 设置固定宽度
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("请再次输入密码")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setStyleSheet(InputStyles.get_line_edit_style())
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addLayout(confirm_layout)
        
        # 激活码输入
        activation_layout = QHBoxLayout()
        activation_layout.setSpacing(10)
        activation_label = QLabel("激活码:")
        activation_label.setFixedWidth(60)  # 设置固定宽度
        self.activation_input = QLineEdit()
        self.activation_input.setPlaceholderText("请输入激活码")
        self.activation_input.setStyleSheet(InputStyles.get_line_edit_style())
        # 移除 returnPressed 连接，使 Enter 键无反应
        activation_layout.addWidget(activation_label)
        activation_layout.addWidget(self.activation_input)
        layout.addLayout(activation_layout)

        layout.addSpacing(20)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.back_btn = QPushButton("返回")
        self.back_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.back_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.back_btn)
        
        self.register_btn = QPushButton("注册")
        self.register_btn.setStyleSheet(ButtonStyles.get_control_button_style())
        self.register_btn.clicked.connect(self.attempt_register)
        button_layout.addWidget(self.register_btn)
        
        layout.addLayout(button_layout)
        
    def attempt_register(self):
        """尝试注册"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_input.text().strip()
        activation_code = self.activation_input.text().strip()
        
        # 验证输入
        if not username or not password or not confirm_password or not activation_code:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "请填写所有字段", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if password != confirm_password:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "两次输入的密码不一致", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        if len(password) < 6:
            msg_box = QMessageBox(QMessageBox.Warning, "输入错误", "密码长度至少6位", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            return
            
        # 执行注册
        result = UserOperations.register_user(username, password, activation_code)
        if result['success']:
            self.user_id = result['user_id']
            self.username = username
            msg_box = QMessageBox(QMessageBox.Information, "注册成功", "账号注册成功！", parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
            self.accept()  # 注册成功
        else:
            msg_box = QMessageBox(QMessageBox.Warning, "注册失败", result['message'], parent=self)
            msg_box.setStyleSheet(MessageStyles.get_message_box_style())
            msg_box.exec()
    
    def keyPressEvent(self, event):
        """重写按键事件，忽略Enter键"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # 忽略Enter键，不执行任何操作
            return
        super().keyPressEvent(event)


class UserOperations:
    """用户操作类"""
    
    # 用户信息文件路径
    USER_INFO_FILE = Path("Mindra_data") / "user_info.json"
    
    @staticmethod
    def _load_models_config():
        """加载模型配置"""
        config_path = Path("config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config['models']
    
    @staticmethod
    def hash_password(password):
        """密码加密"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    @staticmethod
    def save_user_info(user_id, username):
        """保存用户登录信息到文件"""
        try:
            # 确保目录存在
            UserOperations.USER_INFO_FILE.parent.mkdir(exist_ok=True)
            
            user_info = {
                'user_id': user_id,
                'username': username,
                'login_time': datetime.now().isoformat(),
                'last_login': datetime.now().isoformat()
            }
            
            with open(UserOperations.USER_INFO_FILE, 'w', encoding='utf-8') as f:
                json.dump(user_info, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"保存用户信息错误: {e}")
            return False
    
    @staticmethod
    def load_user_info():
        """从文件加载用户登录信息"""
        try:
            if not UserOperations.USER_INFO_FILE.exists():
                return None
            
            with open(UserOperations.USER_INFO_FILE, 'r', encoding='utf-8') as f:
                user_info = json.load(f)
            
            # 验证信息完整性
            if all(key in user_info for key in ['user_id', 'username', 'login_time', 'last_login']):
                return user_info
            else:
                return None
                
        except Exception as e:
            print(f"加载用户信息错误: {e}")
            return None
    
    @staticmethod
    def should_relogin():
        """检查是否需要重新登录（超过一周）"""
        user_info = UserOperations.load_user_info()
        if not user_info:
            return True
        
        try:
            last_login = datetime.fromisoformat(user_info['last_login'])
            current_time = datetime.now()
            
            # 检查是否超过一周（7天）
            if current_time - last_login > timedelta(days=7):
                return True
            else:
                # 更新最后登录时间
                user_info['last_login'] = current_time.isoformat()
                with open(UserOperations.USER_INFO_FILE, 'w', encoding='utf-8') as f:
                    json.dump(user_info, f, ensure_ascii=False, indent=2)
                return False
                
        except Exception as e:
            print(f"检查重新登录错误: {e}")
            return True
    
    @staticmethod
    def clear_user_info():
        """清除用户登录信息"""
        try:
            if UserOperations.USER_INFO_FILE.exists():
                UserOperations.USER_INFO_FILE.unlink()
            return True
        except Exception as e:
            print(f"清除用户信息错误: {e}")
            return False
    
    @staticmethod
    def verify_login(username, password):
        """验证用户登录"""
        try:
            # 连接到 mindra 数据库
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return None
                
            hashed_password = UserOperations.hash_password(password)
            
            # 查询用户（使用 BINARY 确保区分大小写）
            query = "SELECT user_id, username FROM users WHERE BINARY username = %s AND BINARY password = %s"
            cursor.execute(query, (username, hashed_password))
            result = cursor.fetchone()
            
            cursor.close()
            db.disconnect()
            
            return result if result else None
            
        except Exception as e:
            print(f"登录验证错误: {e}")
            return None
    
    @staticmethod
    def register_user(username, password, activation_code):
        """注册新用户"""
        try:
            # 连接到 mindra 数据库
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return {'success': False, 'message': '数据库连接失败'}
            
            # 检查用户名是否已存在（使用 BINARY 确保区分大小写）
            check_query = "SELECT user_id FROM users WHERE BINARY username = %s"
            cursor.execute(check_query, (username,))
            if cursor.fetchone():
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '用户名已存在'}
            
            # 验证激活码
            activation_query = "SELECT user_id FROM activation WHERE activation_code = %s"
            cursor.execute(activation_query, (activation_code,))
            activation_result = cursor.fetchone()
            
            if not activation_result:
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '激活码无效'}
            
            user_id = activation_result['user_id']
            hashed_password = UserOperations.hash_password(password)
            
            # 插入用户数据
            insert_query = "INSERT INTO users (user_id, username, password, credit_balance) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (user_id, username, hashed_password, 0))
            db.connection.commit()
            
            cursor.close()
            db.disconnect()
            
            return {'success': True, 'user_id': user_id}
            
        except Exception as e:
            print(f"用户注册错误: {e}")
            return {'success': False, 'message': '注册失败，请重试'}

    @staticmethod
    def update_username(user_id, current_password, new_username):
        """更新用户名"""
        try:
            # 连接到 mindra 数据库
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return {'success': False, 'message': '数据库连接失败'}
            
            # 验证当前密码是否正确
            hashed_current_password = UserOperations.hash_password(current_password)
            verify_query = "SELECT user_id FROM users WHERE user_id = %s AND BINARY password = %s"
            cursor.execute(verify_query, (user_id, hashed_current_password))
            if not cursor.fetchone():
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '当前密码错误'}
            
            # 检查新用户名是否已存在（使用 BINARY 确保区分大小写）
            check_query = "SELECT user_id FROM users WHERE BINARY username = %s"
            cursor.execute(check_query, (new_username,))
            if cursor.fetchone():
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '用户名已存在'}
            
            # 更新用户名
            update_query = "UPDATE users SET username = %s WHERE user_id = %s"
            cursor.execute(update_query, (new_username, user_id))
            db.connection.commit()
            
            cursor.close()
            db.disconnect()
            
            return {'success': True, 'message': '用户名更新成功'}
            
        except Exception as e:
            print(f"更新用户名错误: {e}")
            return {'success': False, 'message': '更新失败，请重试'}

    @staticmethod
    def update_password(user_id, current_password, new_password):
        """更新密码"""
        try:
            # 连接到 mindra 数据库
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return {'success': False, 'message': '数据库连接失败'}
            
            # 验证当前密码是否正确
            hashed_current_password = UserOperations.hash_password(current_password)
            verify_query = "SELECT user_id FROM users WHERE user_id = %s AND BINARY password = %s"
            cursor.execute(verify_query, (user_id, hashed_current_password))
            if not cursor.fetchone():
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '当前密码错误'}
            
            # 验证新密码长度
            if len(new_password) < 6:
                cursor.close()
                db.disconnect()
                return {'success': False, 'message': '新密码长度至少6位'}
            
            # 更新密码
            hashed_new_password = UserOperations.hash_password(new_password)
            update_query = "UPDATE users SET password = %s WHERE user_id = %s"
            cursor.execute(update_query, (hashed_new_password, user_id))
            db.connection.commit()
            
            cursor.close()
            db.disconnect()
            
            return {'success': True, 'message': '密码更新成功'}
            
        except Exception as e:
            print(f"更新密码错误: {e}")
            return {'success': False, 'message': '更新失败，请重试'}
    
    @staticmethod
    def get_user_credit_balance(user_id):
        """获取用户credit余额"""
        try:
            # 连接到 mindra 数据库
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return None
            
            # 查询用户credit余额
            query = "SELECT credit_balance FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            
            cursor.close()
            db.disconnect()
            
            return result['credit_balance'] if result else 0
            
        except Exception as e:
            print(f"获取credit余额错误: {e}")
            return 0
    
    @staticmethod
    def check_credit_balance(user_id, required_credit=0):
        """检查用户credit余额是否足够"""
        try:
            # 获取用户credit余额
            balance = UserOperations.get_user_credit_balance(user_id)
            
            # 检查余额是否足够
            if balance is not None and balance >= required_credit:
                return True
            else:
                return False
                
        except Exception as e:
            print(f"检查credit余额错误: {e}")
            return False
    
    @staticmethod
    def calculate_credit_usage(model, input_tokens, output_tokens):
        """计算credit使用量"""
        # 加载模型配置
        models_config = UserOperations._load_models_config()
        
        # 定义不同模型的token价格
        model_prices = {
            models_config['text_parsing']: {"input": 0.0005, "output": 0.002},  # 文本解析
            models_config['image_parsing']: {"input": 0.002, "output": 0.02},  # 图片解析
            models_config['daily_conversation']: {"input": 0.004, "output": 0.012}  # 日常对话
        }
        
        # 默认价格
        input_price = 0.0005
        output_price = 0.002
        
        # 如果模型在价格表中，使用对应价格
        if model in model_prices:
            input_price = model_prices[model]["input"]
            output_price = model_prices[model]["output"]
        
        # 计算credit使用量
        input_credit = (input_tokens / 1000) * input_price
        output_credit = (output_tokens / 1000) * output_price
        total_credit = input_credit + output_credit
        
        return round(total_credit, 4)
    
    @staticmethod
    def get_llm_history_file():
        """获取大模型历史记录文件路径"""
        return Path("Mindra_data") / "llm_history.csv"
    
    @staticmethod
    def record_credit_usage(user_id, model, input_tokens, output_tokens):
        """记录credit使用情况"""
        try:
            # 计算credit使用量
            credit_usage = UserOperations.calculate_credit_usage(model, input_tokens, output_tokens)
            
            # 加载模型配置
            models_config = UserOperations._load_models_config()
            
            # 定义模型对应的assignment
            model_assignments = {
                models_config['text_parsing']: "文本解析",
                models_config['image_parsing']: "图片解析",
                models_config['daily_conversation']: "日常对话"
            }
            
            assignment = model_assignments.get(model, "其他")
            
            # 记录到CSV文件
            history_file = UserOperations.get_llm_history_file()
            history_file.parent.mkdir(exist_ok=True)
            
            # 检查文件是否存在，不存在则创建并写入表头
            file_exists = history_file.exists()
            
            with open(history_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['user_id', 'assignment', 'input_token_usage', 'output_token_usage', 'credit_usage', 'created_at'])
                writer.writerow([user_id, assignment, input_tokens, output_tokens, credit_usage, datetime.now().isoformat()])
            
            # 连接到 mindra 数据库更新余额
            db = DBConnection()
            cursor = db.get_cursor()
            if not cursor:
                return False
            
            # 更新用户credit余额，确保不会变为负数
            update_query = "UPDATE users SET credit_balance = GREATEST(credit_balance - %s, 0) WHERE user_id = %s"
            cursor.execute(update_query, (credit_usage, user_id))
            
            db.connection.commit()
            
            cursor.close()
            db.disconnect()
            
            return True
            
        except Exception as e:
            print(f"记录credit使用错误: {e}")
            return False
    
    @staticmethod
    def get_credit_usage_history(user_id):
        """获取用户credit使用历史"""
        try:
            history_file = UserOperations.get_llm_history_file()
            if not history_file.exists():
                return []
            
            history = []
            with open(history_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['user_id'] == str(user_id):
                        history.append({
                            'assignment': row['assignment'],
                            'input_token_usage': int(row['input_token_usage']),
                            'output_token_usage': int(row['output_token_usage']),
                            'credit_usage': float(row['credit_usage']),
                            'created_at': row['created_at']
                        })
            
            # 按时间倒序排序
            history.sort(key=lambda x: x['created_at'], reverse=True)
            
            return history
            
        except Exception as e:
            print(f"获取credit使用历史错误: {e}")
            return []
    
    @staticmethod
    def clear_credit_usage_history(user_id):
        """清空用户credit使用历史"""
        try:
            history_file = UserOperations.get_llm_history_file()
            if not history_file.exists():
                return True
            
            # 读取所有历史记录
            all_history = []
            with open(history_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                header = reader.fieldnames
                for row in reader:
                    all_history.append(row)
            
            # 过滤掉指定用户的历史记录
            filtered_history = [row for row in all_history if row['user_id'] != str(user_id)]
            
            # 写回过滤后的历史记录
            with open(history_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                writer.writerows(filtered_history)
            
            return True
            
        except Exception as e:
            print(f"清空credit使用历史错误: {e}")
            return False