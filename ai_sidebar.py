from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTextEdit, QLabel, QScrollArea, QFrame, QSizePolicy,
                               QFileDialog, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QCursor, QPixmap
from openai import OpenAI
from pathlib import Path
import base64
import os
import re
import yaml
from style_settings import AISidebarStyles
from user_operations import UserOperations


class AIWorker(QThread):
    """AI工作线程"""
    response_chunk = Signal(str, str)  # 流式输出的每个片段和思考过程
    response_complete = Signal(str, str)  # 完整响应和思考过程
    error_occurred = Signal(str)
    
    def __init__(self, ai_sidebar, message, use_deep_thinking=False, use_search=False, has_images=False, has_documents=False):
        super().__init__()
        self.ai_sidebar = ai_sidebar
        self.message = message
        self.use_deep_thinking = use_deep_thinking
        self.use_search = use_search
        self.has_images = has_images
        self.has_documents = has_documents
        self.full_response = ""
        self.thought_process = ""
        
    def run(self):
        """线程运行方法"""
        try:
            # 流式输出
            self.full_response = ""
            self.thought_process = ""
            
            # 发送请求
            extra_body = {}
            if self.use_deep_thinking:
                extra_body["enable_thinking"] = True
            if self.use_search:
                extra_body["enable_search"] = True
            
            # 使用ai_sidebar中的流式对话方法
            response_generator = self.ai_sidebar._chat_stream_with_thinking(
                self.message, extra_body, has_images=self.has_images, has_documents=self.has_documents
            )
            
            for content, reasoning_content in response_generator:
                if reasoning_content:
                    self.thought_process += reasoning_content
                    self.response_chunk.emit(self.full_response, self.thought_process)
                
                if content:
                    self.full_response += content
                    self.response_chunk.emit(self.full_response, self.thought_process)
            
            self.response_complete.emit(self.full_response, self.thought_process)
        except Exception as e:
            error_msg = f"抱歉，AI服务暂时不可用: {str(e)}"
            self.error_occurred.emit(error_msg)


class AISidebar(QWidget):
    """AI侧边栏组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # 初始化AI客户端功能
        self._init_ai_client()
        
        self.messages = []  # 存储对话历史
        self.thoughts = []  # 存储思考过程
        self.current_ai_response = None  # 当前AI响应组件
        self.current_thought_content = None  # 当前思考内容组件
        self.current_thought_area = None  # 当前思考区域组件
        self.current_arrow = None  # 当前箭头组件
        self.auto_scroll_enabled = True  # 控制是否允许自动滚动
        self.use_deep_thinking = False  # 深度思考模式
        self.use_search = False  # 联网搜索模式
        self.thought_visible = True  # 思考过程显示状态
        self.buttons_enabled = True  # 按钮启用状态
        self.welcome_shown = True  # 标记欢迎消息是否已显示
        self.uploaded_images = []  # 存储上传的图片路径
        self.uploaded_documents = []  # 存储上传的文档路径
        self.cited_webpages = []  # 存储引用的网页URL列表
        self.cited_webpage_contents = {}  # 存储引用的网页内容 {url: content}
        
        self.setup_ui()
        
        # 延迟显示欢迎消息，确保UI完全加载
        QTimer.singleShot(100, self.show_welcome_message)
    
    def _init_ai_client(self):
        """初始化AI客户端"""
        # 从配置文件加载API密钥和基础URL
        config_path = Path("config.yaml")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            ai_config = config['ai']
            api_key = ai_config['api_key']
            base_url = ai_config['base_url']
            self.models_config = config['models']
        
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # 系统提示词
        self.system_prompt = """你是一个名为Mindra AI的浏览器助手。你具有以下特点和能力：

1. **身份定位**：你是集成在Mindra浏览器中的智能助手，专门帮助用户浏览网页、总结内容、翻译文本等。

2. **核心功能**：
   - 网页内容总结：帮助用户快速了解网页的核心信息和关键点
   - 文本翻译：支持多语言翻译，特别是中英文互译
   - 问题解答：回答用户关于网页内容或一般知识的问题
   - 学习辅助：帮助用户学习和理解新知识

3. **回答风格**：
   - 友好、耐心、专业
   - 回答要简洁明了，避免过于技术化的术语
   - 对于页面总结，提取关键信息，使用要点形式呈现
   - 保持积极助人的态度

4. **特殊能力**：
   - 能够理解网页上下文
   - 支持实时对话交流
   - 具备多轮对话记忆能力
   - 擅长从复杂内容中提取关键信息

请根据以上定位为用户提供最好的服务！"""
        
        # 对话历史
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]
    
    def _chat_stream_with_thinking(self, user_message, extra_body=None, has_images=False, has_documents=False):
        """支持思考过程的流式对话"""
        try:
            # 检查用户credit余额是否足够
            user_info = UserOperations.load_user_info()
            if user_info and user_info['user_id']:
                # 检查余额是否足够（设置最小阈值0.001）
                if not UserOperations.check_credit_balance(user_info['user_id'], 0.001):
                    yield "抱歉，您的Credit余额不足，请联系管理员充值后再使用大模型服务。", ""
                    return
            
            # 处理文档上传的情况
            if has_documents:
                # 上传所有文档并获取文件ID
                file_ids = []
                for doc_path in user_message.get('documents', []):
                    try:
                        file_object = self.client.files.create(file=Path(doc_path), purpose="file-extract")
                        file_ids.append(file_object.id)
                    except Exception as e:
                        print(f"上传文档失败 {doc_path}: {e}")
                        yield f"上传文档失败: {e}", ""
                        return
                
                # 构建文件ID字符串
                file_id_content = ",".join([f"fileid://{fid}" for fid in file_ids])
                
                messages = [
                    {"role": "system", "content": file_id_content},
                    {"role": "user", "content": user_message.get('text', '')}
                ]
                
                response = self.client.chat.completions.create(
                    model=self.models_config['text_parsing'],
                    messages=messages,
                    stream=True,
                    temperature=0.7,
                    max_tokens=2000,
                    stream_options={"include_usage": True}
                )
                
                full_response = ""
                input_tokens = 0
                output_tokens = 0
                
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        content = ""
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            full_response += content
                        yield content, ""
                    
                    # 检查是否包含 usage（通常在最后一个 chunk）
                    if hasattr(chunk, 'usage') and chunk.usage is not None:
                        usage = chunk.usage
                        input_tokens = usage.prompt_tokens
                        output_tokens = usage.completion_tokens
                
                # 添加到对话历史
                self.conversation_history.append({
                    "role": "user",
                    "content": user_message.get('text', '')
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
                # 限制历史长度
                if len(self.conversation_history) > 20:
                    self.conversation_history = [
                        self.conversation_history[0],
                        *self.conversation_history[-18:]
                    ]
                
                # 记录credit使用情况
                if input_tokens > 0 or output_tokens > 0:
                    # 获取用户ID
                    user_info = UserOperations.load_user_info()
                    if user_info and user_info['user_id']:
                        UserOperations.record_credit_usage(user_info['user_id'], self.models_config['text_parsing'], input_tokens, output_tokens)
                
                return
            
            # 添加用户消息到历史
            if has_images and isinstance(user_message, list):
                # 图片+文本消息
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message
                })
            else:
                # 纯文本消息
                self.conversation_history.append({
                    "role": "user", 
                    "content": user_message
                })
            
            # 根据是否有图片选择模型
            model_name = self.models_config['image_parsing'] if has_images else self.models_config['daily_conversation']
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=self.conversation_history,
                stream=True,
                temperature=0.7,
                max_tokens=2000,
                extra_body=extra_body or {},
                stream_options={"include_usage": True}
            )
            
            full_response = ""
            input_tokens = 0
            output_tokens = 0
            
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    
                    # 处理思考过程
                    reasoning_content = ""
                    if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                        reasoning_content = delta.reasoning_content
                    
                    # 处理响应内容
                    content = ""
                    if hasattr(delta, 'content') and delta.content:
                        content = delta.content
                        full_response += content
                    
                    yield content, reasoning_content
                
                # 检查是否包含 usage（通常在最后一个 chunk）
                if hasattr(chunk, 'usage') and chunk.usage is not None:
                    usage = chunk.usage
                    input_tokens = usage.prompt_tokens
                    output_tokens = usage.completion_tokens
                    
            # 添加到对话历史
            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            
            # 限制历史长度
            if len(self.conversation_history) > 20:
                self.conversation_history = [
                    self.conversation_history[0],
                    *self.conversation_history[-18:]
                ]
                
            # 记录credit使用情况
            if input_tokens > 0 or output_tokens > 0:
                # 获取用户ID
                user_info = UserOperations.load_user_info()
                if user_info and user_info['user_id']:
                    UserOperations.record_credit_usage(user_info['user_id'], model_name, input_tokens, output_tokens)
                
        except Exception as e:
            error_msg = f"抱歉，流式输出失败: {str(e)}"
            yield error_msg, ""
            
    def clear_history(self):
        """清除对话历史"""
        self.conversation_history = [
            {"role": "system", "content": self.system_prompt}
        ]

    def setup_ui(self):
        """设置UI布局"""
        self.setFixedWidth(400)  # 设置固定宽度为400像素
        self.setStyleSheet(AISidebarStyles.get_sidebar_style())
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(10)
        
        # 聊天消息区域 - 使用单一容器
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 隐藏垂直滚动条
        self.chat_scroll.setStyleSheet(AISidebarStyles.get_chat_scroll_style())
        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background-color: transparent;")
        self.chat_layout = QVBoxLayout()
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_container.setLayout(self.chat_layout)
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 1)
        self.chat_scroll.verticalScrollBar().actionTriggered.connect(self.on_scrollbar_action)
        
        # 输入区域
        self.setup_input_area(layout)
        
    def show_welcome_message(self):
        """显示欢迎消息"""
        if not self.welcome_shown:
            return
            
        # 清空聊天布局
        self.clear_chat_layout()
        
        # 创建欢迎消息容器
        welcome_frame = QFrame()
        welcome_frame.setFrameShape(QFrame.NoFrame)  # 去掉边框
        welcome_frame.setStyleSheet("border-radius: 8px;")
        welcome_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        welcome_layout = QVBoxLayout()
        welcome_layout.setContentsMargins(20, 30, 20, 30)
        welcome_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("欢迎使用 Mindra AI")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        title_label.setStyleSheet("color: black;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 副标题
        subtitle_label = QLabel("您的智能浏览助手")
        subtitle_label.setFont(QFont("Microsoft YaHei", 12))
        subtitle_label.setStyleSheet("color: black;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        # 功能介绍
        features_frame = QFrame()
        features_layout = QVBoxLayout()
        features_layout.setContentsMargins(15, 15, 15, 15)
        features_layout.setSpacing(10)
        
        features_title = QLabel("✨ 功能介绍：")
        features_title.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        features_title.setStyleSheet("color: black;")
        
        features_list = [
            "💬 智能对话：在下方输入框直接提问",
            "📄 页面总结：点击按钮总结当前网页内容",
            "🔍 划词解释：选中网页文本进行解释",
            "🌍 划词翻译：选中网页文本进行翻译",
            "🤔 深度思考：开启后可查看AI思考过程"
        ]
        
        for feature in features_list:
            feature_label = QLabel(feature)
            feature_label.setFont(QFont("Microsoft YaHei", 10))
            feature_label.setStyleSheet("color: black; border: none")
            features_layout.addWidget(feature_label)
        
        features_frame.setLayout(features_layout)
        
        # 将所有部件添加到欢迎布局
        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(subtitle_label)
        welcome_layout.addWidget(features_frame)
        
        welcome_frame.setLayout(welcome_layout)
        
        # 将欢迎消息添加到聊天区域中央
        center_layout = QVBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(welcome_frame)
        center_layout.addStretch()
        center_layout.setAlignment(welcome_frame, Qt.AlignCenter)
        
        # 创建容器用于居中
        center_container = QWidget()
        center_container.setLayout(center_layout)
        
        # 添加到聊天布局
        self.chat_layout.addWidget(center_container)
        
    def clear_chat_layout(self):
        """清空聊天布局中的所有内容"""
        # 移除所有子部件
        while self.chat_layout.count() > 0:
            item = self.chat_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                # 递归清除子布局
                sub_layout = item.layout()
                while sub_layout.count() > 0:
                    sub_item = sub_layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
        
    def setup_input_area(self, layout):
        """设置输入区域"""
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建输入框容器
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 2px solid #d0d0d0;
                border-radius: 10px;
            }
        """)
        input_container_layout = QVBoxLayout(input_container)
        input_container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 图片预览区域（位于输入框上方）
        self.image_preview_widget = QWidget()
        self.image_preview_widget.setStyleSheet("background-color: transparent; border: none;")
        self.image_preview_layout = QHBoxLayout(self.image_preview_widget)
        self.image_preview_layout.setContentsMargins(0, 0, 0, 5)
        self.image_preview_layout.setSpacing(8)
        self.image_preview_layout.setAlignment(Qt.AlignLeft)
        self.image_preview_widget.hide()  # 初始隐藏
        input_container_layout.addWidget(self.image_preview_widget)
        
        # 输入框 - 改用QTextEdit支持多行
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("输入您的问题...")
        self.input_field.setFixedHeight(75)
        self.input_field.setStyleSheet(AISidebarStyles.get_input_field_style())
        # 设置粘贴为纯文本模式
        self.input_field.setAcceptRichText(False)
        self.input_field.installEventFilter(self)
        input_container_layout.addWidget(self.input_field)
        
        # 创建底部按钮行布局
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.setSpacing(0)
        bottom_button_layout.setContentsMargins(0, 5, 0, 0)
        
        # 上传图片按钮（放在最左侧）
        self.upload_image_btn = QPushButton("🖼️")
        self.upload_image_btn.setToolTip("上传图片")
        self.upload_image_btn.setStyleSheet(AISidebarStyles.get_tool_button_style("#fff3e0", "#ffe0b2"))
        self.upload_image_btn.clicked.connect(self.on_upload_image)
        bottom_button_layout.addWidget(self.upload_image_btn)
        
        # 上传文档按钮
        self.upload_doc_btn = QPushButton("📄")
        self.upload_doc_btn.setToolTip("上传文档")
        self.upload_doc_btn.setStyleSheet(AISidebarStyles.get_tool_button_style("#dcf4ee", "#b4f0dc"))
        self.upload_doc_btn.clicked.connect(self.on_upload_document)
        bottom_button_layout.addWidget(self.upload_doc_btn)
        
        # 引用当前网页按钮
        self.cite_webpage_btn = QPushButton("🔗")
        self.cite_webpage_btn.setToolTip("引用当前网页")
        self.cite_webpage_btn.setStyleSheet(AISidebarStyles.get_tool_button_style("#fce4ec", "#f8bbd9"))
        self.cite_webpage_btn.clicked.connect(self.on_cite_webpage)
        bottom_button_layout.addWidget(self.cite_webpage_btn)
        
        # 添加弹性空间，将按钮推到两侧
        bottom_button_layout.addStretch()
        
        # 清空按钮
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setToolTip("清空聊天")
        self.clear_btn.setStyleSheet(AISidebarStyles.get_tool_button_style("#ffebee", "#ffcdd2"))
        self.clear_btn.clicked.connect(self.on_clear_chat)
        bottom_button_layout.addWidget(self.clear_btn)
        
        # 联网搜索按钮
        self.search_toggle_btn = QPushButton("🌐")
        self.search_toggle_btn.setToolTip("联网搜索")
        self.search_toggle_btn.setCheckable(True)
        self.search_toggle_btn.setStyleSheet(AISidebarStyles.get_toggle_button_style())
        self.search_toggle_btn.clicked.connect(self.on_toggle_search)
        bottom_button_layout.addWidget(self.search_toggle_btn)
        
        # 深度思考按钮
        self.think_toggle_btn = QPushButton("💭")
        self.think_toggle_btn.setToolTip("深度思考")
        self.think_toggle_btn.setCheckable(True)
        self.think_toggle_btn.setStyleSheet(AISidebarStyles.get_toggle_button_style())
        self.think_toggle_btn.clicked.connect(self.on_toggle_deep_thinking)
        bottom_button_layout.addWidget(self.think_toggle_btn)
        
        # 发送按钮
        self.send_btn = QPushButton("🚀")
        self.send_btn.setToolTip("发送消息 (Enter)")
        self.send_btn.setStyleSheet(AISidebarStyles.get_send_button_style())
        self.send_btn.clicked.connect(self.send_message)
        bottom_button_layout.addWidget(self.send_btn)
        
        # 将底部按钮行添加到输入容器布局
        input_container_layout.addLayout(bottom_button_layout)
        
        # 将输入容器添加到输入布局
        input_layout.addWidget(input_container)
        
        layout.addLayout(input_layout)
        
    def on_scrollbar_action(self, _):
        scroll_bar = self.chat_scroll.verticalScrollBar()
        current_value = scroll_bar.value()
        max_value = scroll_bar.maximum()
        threshold = 10
        
        if max_value - current_value <= threshold:
            self.auto_scroll_enabled = True
        else:
            self.auto_scroll_enabled = False
            
    def on_clear_chat(self):
        """清空聊天记录"""
        # 清空大模型的对话历史
        self.clear_history()
        
        # 清空消息历史
        self.messages.clear()
        self.thoughts.clear()
        
        # 重置组件引用
        self.current_ai_response = None
        self.current_thought_content = None
        self.current_thought_area = None
        self.current_arrow = None
        self.thought_visible = True
        
        # 清空上传的图片、文档和引用的网页
        self.clear_uploaded_images()
        self.clear_uploaded_documents()
        self.clear_cited_webpages()
        
        # 重置标志，显示欢迎消息
        self.welcome_shown = True
        
        # 清除聊天布局并显示欢迎消息
        self.clear_chat_layout()
        self.show_welcome_message()
        
    def on_toggle_deep_thinking(self):
        """切换深度思考模式"""
        self.use_deep_thinking = self.think_toggle_btn.isChecked()
        
    def on_toggle_search(self):
        """切换联网搜索模式"""
        self.use_search = self.search_toggle_btn.isChecked()
        
    def set_buttons_enabled(self, enabled):
        """设置按钮启用状态"""
        self.buttons_enabled = enabled
        self.send_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        
        # 深度思考按钮：只有在启用状态且没有文档时才启用
        if enabled and self.uploaded_documents:
            self.think_toggle_btn.setEnabled(False)
            self.think_toggle_btn.setChecked(False)
            self.use_deep_thinking = False
        else:
            self.think_toggle_btn.setEnabled(enabled)
        
        # 上传图片按钮：只有在启用状态且没有文档和引用网页时才启用
        if enabled and (self.uploaded_documents or self.cited_webpages):
            self.upload_image_btn.setEnabled(False)
        else:
            self.upload_image_btn.setEnabled(enabled)
        
        # 上传文档按钮：只有在启用状态且没有图片和引用网页时才启用
        if enabled and (self.uploaded_images or self.cited_webpages):
            self.upload_doc_btn.setEnabled(False)
        else:
            self.upload_doc_btn.setEnabled(enabled)
        
        # 引用网页按钮：只有在启用状态且没有图片和文档时才启用
        if enabled and (self.uploaded_images or self.uploaded_documents):
            self.cite_webpage_btn.setEnabled(False)
        else:
            self.cite_webpage_btn.setEnabled(enabled)
        
        # 搜索按钮：只有在启用状态且没有图片和文档时才启用
        if enabled and (self.uploaded_images or self.uploaded_documents):
            self.search_toggle_btn.setEnabled(False)
            self.search_toggle_btn.setChecked(False)
            self.use_search = False
        else:
            self.search_toggle_btn.setEnabled(enabled)
            
    def scroll_to_bottom(self):
        """滚动到底部"""
        if self.auto_scroll_enabled:
            QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
                self.chat_scroll.verticalScrollBar().maximum()))
                
    def toggle_thought_display(self, event, thought_content, arrow):
        """切换单个消息的思考过程显示状态"""
        if thought_content.isVisible():
            thought_content.hide()
            arrow.setText("▼")
            self.thought_visible = False
        else:
            thought_content.show()
            arrow.setText("▲")
            self.thought_visible = True
        
        # 确保布局正确更新
        thought_content.parent().updateGeometry()
        
        # 滚动到底部，确保内容可见
        self.scroll_to_bottom()
        
        # 调用父类事件处理，防止事件被吞噬
        super(QLabel, arrow).mousePressEvent(event)
                
    def send_message(self):
        """发送消息到AI"""
        if not self.buttons_enabled:
            return
            
        message = self.input_field.toPlainText().strip()
        if not message and not self.uploaded_images and not self.uploaded_documents and not self.cited_webpages:
            return
            
        # 构建用户显示文本
        display_text = message if message else ""
        
        # 保存路径（在清空前）
        image_paths = self.uploaded_images.copy()
        doc_paths = self.uploaded_documents.copy()
        webpage_urls = self.cited_webpages.copy()
        has_images = len(image_paths) > 0
        has_documents = len(doc_paths) > 0
        has_webpages = len(webpage_urls) > 0
        
        # 处理文档上传
        if has_documents:
            # 构建文档消息
            doc_message = {
                'text': message,
                'documents': doc_paths
            }
            
            # 清空输入框和文档
            self.input_field.clear()
            self.clear_uploaded_documents()
            
            # 使用通用方法处理AI请求
            self._process_ai_request(doc_message, display_text, self.use_deep_thinking, self.use_search, 
                                    has_images=False, image_paths=None, has_documents=True, doc_paths=doc_paths,
                                    has_webpages=False, webpage_urls=None)
            return
        
        # 构建发送到AI的消息内容（图片+文本+网页内容）
        content_list = []
        
        # 添加图片（如果有）
        for img_path in image_paths:
            # 读取图片并转换为base64
            try:
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                # 获取图片格式
                ext = img_path.split('.')[-1].lower()
                if ext == 'jpg':
                    ext = 'jpeg'
                mime_type = f"image/{ext}"
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{img_data}"}
                })
            except Exception as e:
                print(f"读取图片失败: {e}")
        
        # 构建文本消息
        full_message = message if message else ""

        # 添加引用网页的内容（使用实际提取的网页内容）
        if has_webpages:
            webpage_contents = []
            for url in webpage_urls:
                # 获取存储的网页内容
                page_content = self.cited_webpage_contents.get(url, "[页面内容未获取]")
                webpage_contents.append(f"引用网页 [{url}] 的内容：\n{page_content}")
            if webpage_contents:
                full_message += "\n\n" + "\n\n".join(webpage_contents)
        
        # 添加文本（如果有）
        if full_message:
            content_list.append({"type": "text", "text": full_message})
        
        # 清空输入框、图片和引用的网页
        self.input_field.clear()
        self.clear_uploaded_images()
        self.clear_cited_webpages()
        
        # 使用通用方法处理AI请求
        self._process_ai_request(content_list, display_text, self.use_deep_thinking, self.use_search, 
                                has_images=has_images, image_paths=image_paths, has_documents=False, doc_paths=None,
                                has_webpages=has_webpages, webpage_urls=webpage_urls)
        
    def eventFilter(self, obj, event):
        """事件过滤器，处理QTextEdit的键盘事件"""
        if obj is self.input_field and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() & Qt.ControlModifier or event.modifiers() & Qt.ShiftModifier:
                    # Ctrl+Enter 或 Shift+Enter: 插入换行
                    cursor = self.input_field.textCursor()
                    cursor.insertText("\n")
                    return True
                else:
                    # Enter: 发送消息
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)
        
    def handle_ai_chunk(self, response, thought_process):
        """处理AI响应片段（流式输出）"""
        if self.current_ai_response:
            self.current_ai_response.setText(response)
            
            # 更新思考过程（如果启用深度思考）
            if self.use_deep_thinking and self.current_thought_content:
                self.current_thought_content.setText(thought_process)
                
            self.scroll_to_bottom()
        
    def handle_ai_complete(self, response, thought_process):
        """处理AI响应完成"""
        # 存储思考过程
        if thought_process:
            self.thoughts.append(thought_process)
        
        # 添加到消息历史
        self.messages.append({"role": "assistant", "content": response})
        
        # 重新启用按钮
        self.set_buttons_enabled(True)
        
    def handle_ai_error(self, error_msg):
        """处理AI错误"""
        # 显示错误信息
        if self.current_ai_response:
            self.current_ai_response.setText(error_msg)

        # 重新启用按钮
        self.set_buttons_enabled(True)

    def on_link_clicked(self, url):
        """处理AI消息中的链接点击，在当前浏览器中打开"""
        if self.parent:
            self.parent.create_new_tab(url=url)

    def add_message(self, text="", is_ai=False, has_images=False, image_paths=None, has_documents=False, doc_paths=None, use_deep_thinking=None, has_webpages=False, webpage_urls=None):
        """添加消息到聊天界面"""
        # 如果未指定，使用全局设置
        if use_deep_thinking is None:
            use_deep_thinking = self.use_deep_thinking
        
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.NoFrame)
        message_frame.setStyleSheet(
            "background-color: #f8f9fa; border-radius: 10px;" if is_ai 
            else "background-color: white; border-radius: 10px;"
        )
        message_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)

        msg_layout = QVBoxLayout()
        msg_layout.setContentsMargins(10, 8, 10, 8)
        
        content_layout = QVBoxLayout()
        
        if is_ai:
            content = QLabel()
            content.setFont(QFont("Microsoft YaHei", 11))
            content.setStyleSheet("color: black;")
            content.setWordWrap(True)
            content.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
            content.setOpenExternalLinks(False)  # 不使用默认浏览器打开链接
            content.setTextFormat(Qt.MarkdownText)  # 使用 Markdown 格式
            content.setFixedWidth(self.chat_scroll.width()*0.93)
            # 连接链接点击信号，在当前浏览器中打开
            content.linkActivated.connect(self.on_link_clicked)
            
            # 存储当前消息的引用
            self.current_ai_response = content
            
            # 深度思考模式时添加思考过程区域
            if use_deep_thinking:
                # 为每个消息创建独立的思考过程区域
                thought_area = QWidget(message_frame)
                thought_layout = QVBoxLayout(thought_area)
                thought_layout.setContentsMargins(0, 5, 0, 0)
                
                # 箭头和标题布局
                arrow_layout = QHBoxLayout()
                arrow = QLabel("▲")
                arrow.setFont(QFont("Arial", 8, QFont.Bold))
                arrow.setStyleSheet("color: #666666;")
                arrow.setCursor(QCursor(Qt.PointingHandCursor))
                
                thought_label = QLabel("思考过程")
                thought_label.setFont(QFont("Microsoft YaHei", 9))
                thought_label.setStyleSheet("color: #666666;")
                
                arrow_layout.addWidget(arrow)
                arrow_layout.addWidget(thought_label)
                arrow_layout.addStretch()
                
                # 思考内容区域
                thought_content = QLabel(thought_area)
                thought_content.setFont(QFont("Microsoft YaHei", 9))
                thought_content.setStyleSheet("margin-left: 10px; color: #666666")
                thought_content.setTextFormat(Qt.MarkdownText)
                thought_content.setTextInteractionFlags(Qt.TextSelectableByMouse)
                thought_content.setWordWrap(True)
                thought_content.setFixedWidth(self.chat_scroll.width()*0.93)
                
                # 深度思考模式时默认显示思考区域
                thought_content.show()
                arrow.setText("▲")
                thought_layout.addLayout(arrow_layout)
                thought_layout.addWidget(thought_content)
                content_layout.addWidget(thought_area)
                
                # 为箭头连接点击事件
                arrow.mousePressEvent = lambda event, t=thought_content, a=arrow: self.toggle_thought_display(event, t, a)
                
                # 存储当前消息的思考过程组件
                self.current_thought_area = thought_area
                self.current_thought_content = thought_content
                self.current_arrow = arrow
            
            content_layout.addWidget(content)
        else:
            # 用户消息，显示文本、图片和文档
            if text:
                content = QLabel(text)
                content.setFont(QFont("Microsoft YaHei", 11))
                content.setStyleSheet("color: black;")
                content.setWordWrap(True)
                content.setTextInteractionFlags(Qt.TextSelectableByMouse)
                
                # 计算消息框宽度
                max_width = int(self.chat_scroll.width() * 0.93)
                
                # 根据文本长度动态计算宽度
                font_metrics = content.fontMetrics()
                text_width = font_metrics.horizontalAdvance(text)
                
                # 设置最小宽度和最大宽度
                calculated_width = min(text_width, max_width)
                
                content.setFixedWidth(calculated_width)
            
            # 如果有文档，显示文档缩略图
            if has_documents and doc_paths:
                for i, doc_path in enumerate(doc_paths):
                    try:
                        # 创建文档行的水平布局
                        doc_row_layout = QHBoxLayout()
                        doc_row_layout.setContentsMargins(0, 0, 0, 0)
                        doc_row_layout.addStretch()
                        
                        # 创建文档标签
                        doc_label = QLabel(f"📄 文档{i+1}")
                        doc_label.setFont(QFont("Microsoft YaHei", 10))
                        doc_label.setStyleSheet("""
                            QLabel {
                                color: #60A893;
                                background-color: #dcf4ee;
                                padding: 8px 12px;
                                border-radius: 6px;
                                border: 1px solid #b4f0dc;
                            }
                            QLabel QToolTip {
                                background-color: white;
                                color: black;
                                border: 1px solid #cccccc;
                                padding: 4px 8px;
                                border-radius: 4px;
                                font-size: 12px;
                            }
                        """)
                        doc_label.setToolTip(os.path.basename(doc_path))  # 鼠标悬停显示文件名
                        doc_row_layout.addWidget(doc_label)
                        doc_row_layout.addStretch()
                        
                        content_layout.addLayout(doc_row_layout)
                    except Exception as e:
                        print(f"加载文档显示失败: {e}")
            
            # 如果有引用的网页，显示网页标签
            if has_webpages and webpage_urls:
                for i, url in enumerate(webpage_urls):
                    try:
                        # 创建网页行的水平布局
                        page_row_layout = QHBoxLayout()
                        page_row_layout.setContentsMargins(0, 0, 0, 0)
                        page_row_layout.addStretch()
                        
                        # 创建网页标签
                        page_label = QLabel(f"🔗 网页{i+1}")
                        page_label.setFont(QFont("Microsoft YaHei", 10))
                        page_label.setStyleSheet("""
                            QLabel {
                                color: #c2185b;
                                background-color: #fce4ec;
                                padding: 8px 12px;
                                border-radius: 6px;
                                border: 1px solid #f8bbd9;
                            }
                            QLabel QToolTip {
                                background-color: white;
                                color: black;
                                border: 1px solid #cccccc;
                                padding: 4px 8px;
                                border-radius: 4px;
                                font-size: 12px;
                            }
                        """)
                        page_label.setToolTip(url)  # 鼠标悬停显示URL
                        page_row_layout.addWidget(page_label)
                        page_row_layout.addStretch()
                        
                        content_layout.addLayout(page_row_layout)
                    except Exception as e:
                        print(f"加载网页显示失败: {e}")
            
            # 如果有图片，每个图片占一行显示
            if has_images and image_paths:
                for img_path in image_paths:
                    try:
                        pixmap = QPixmap(img_path)
                        if not pixmap.isNull():
                            # 创建图片行的水平布局，使图片居中
                            img_row_layout = QHBoxLayout()
                            img_row_layout.setContentsMargins(0, 0, 0, 0)
                            img_row_layout.addStretch()
                            
                            # 缩放为200x200的缩略图
                            scaled_pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            img_label = QLabel()
                            img_label.setPixmap(scaled_pixmap)
                            img_label.setFixedSize(200, 200)
                            img_label.setStyleSheet("border-radius: 4px;")
                            img_row_layout.addWidget(img_label)
                            img_row_layout.addStretch()
                            
                            content_layout.addLayout(img_row_layout)
                    except Exception as e:
                        print(f"加载图片缩略图失败: {e}")
            
            # 文字消息显示在最后
            if text:
                content_layout.addWidget(content)

        msg_layout.addLayout(content_layout)
        message_frame.setLayout(msg_layout)
        
        h_layout = QHBoxLayout()
        if is_ai:
            h_layout.setAlignment(Qt.AlignLeft)  # AI消息在左边
            h_layout.addWidget(message_frame)
            h_layout.addStretch()  # 添加弹性空间，确保气泡在左半边
        else:
            h_layout.setAlignment(Qt.AlignRight)  # 用户消息在右边
            h_layout.addStretch()  # 添加弹性空间，确保气泡在右半边
            h_layout.addWidget(message_frame)
        
        # 添加到聊天布局
        self.chat_layout.addLayout(h_layout)
        self.scroll_to_bottom()
            
    def _process_ai_request(self, prompt, user_message_text, use_deep_thinking=False, use_search=False, 
                           has_images=False, image_paths=None, has_documents=False, doc_paths=None,
                           has_webpages=False, webpage_urls=None):
        """处理AI请求的通用方法"""
        # 禁用按钮
        self.set_buttons_enabled(False)
        
        # 如果是欢迎页面，先清空欢迎页面
        if self.welcome_shown:
            self.welcome_shown = False
            self.clear_chat_layout()
        
        # 显示用户消息
        self.add_message(user_message_text, False, has_images=has_images, image_paths=image_paths, 
                        has_documents=has_documents, doc_paths=doc_paths,
                        has_webpages=has_webpages, webpage_urls=webpage_urls)
        
        # 创建AI消息容器（传递 use_deep_thinking 参数控制是否显示思考过程）
        self.add_message("", True, use_deep_thinking=use_deep_thinking)
        
        # 使用线程安全方式发送到AI
        self.ai_worker = AIWorker(self, prompt, use_deep_thinking=use_deep_thinking, use_search=use_search, 
                                 has_images=has_images, has_documents=has_documents)
        self.ai_worker.response_chunk.connect(self.handle_ai_chunk)
        self.ai_worker.response_complete.connect(self.handle_ai_complete)
        self.ai_worker.error_occurred.connect(self.handle_ai_error)
        self.ai_worker.start()
        
    def explain_current_page(self):
        """总结当前页面 - 使用JavaScript提取页面文本"""
        current_browser = self.parent.tabs.currentWidget()
        if current_browser:
            # 使用JavaScript提取页面可见文本（不修改DOM）
            js_code = """
            (function() {
                // 获取正文文本（不修改页面DOM）
                var body = document.body;
                if (!body) return '';
                var text = body.innerText || body.textContent;
                // 清理多余空白，保留换行符以便阅读
                text = text.replace(/[ \\t]+/g, ' ');
                text = text.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n');
                return text.trim();
            })()
            """
            current_browser.page().runJavaScript(
                js_code, lambda text: self.process_page_explain(text))
            
    def process_page_explain(self, content):
        """处理页面总结 - 改进版，自动识别HTML或纯文本"""
        
        # 检查内容是否为空
        if not content or len(content.strip()) == 0:
            prompt = "无法获取页面内容，请确保页面已加载完成。"
            self._process_ai_request(prompt, "请总结当前页面内容", use_deep_thinking=False)
            return
        
        # 判断content是HTML还是纯文本
        # 如果包含明显的HTML标签对，则视为HTML
        is_html = re.search(r'<[^>]+>', content) and re.search(r'</[^>]+>', content)
        
        if is_html:
            # HTML处理流程
            # 1. 提取body标签内容（不区分大小写）
            body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
            if body_match:
                text = body_match.group(1)
            else:
                text = content
            
            # 2. 移除script标签及其内容
            text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
            # 3. 移除style标签及其内容
            text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
            # 4. 移除其他不需要的标签（如noscript, iframe等）
            text = re.sub(r'<(noscript|iframe|object|embed)[^>]*>.*?</\1>', ' ', text, flags=re.IGNORECASE | re.DOTALL)
            # 5. 移除所有剩余的HTML标签
            text = re.sub(r'<[^>]+>', ' ', text)
            # 6. 替换HTML实体
            text = re.sub(r'&(?:[a-zA-Z]+|#\d+);', ' ', text)
            # 7. 合并空白字符
            text = re.sub(r'\s+', ' ', text)
            # 8. 去除首尾空白
            text = text.strip()
        else:
            # 纯文本处理
            text = content.strip()
            # 合并多余空白
            text = re.sub(r'\s+', ' ', text)
        
        # 如果内容太短，尝试使用HTML解析作为后备（仅当原始内容是HTML时）
        if len(text) < 100 and is_html:
            # 简单的HTML标签移除
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
        
        # 智能截断
        max_length = 3000
        if len(text) > max_length:
            # 尝试在句号、问号、感叹号后截断
            truncate_pos = text.rfind('。', 0, max_length)
            if truncate_pos == -1:
                truncate_pos = text.rfind('.', 0, max_length)
            if truncate_pos == -1:
                truncate_pos = text.rfind('?', 0, max_length)
            if truncate_pos == -1:
                truncate_pos = text.rfind('!', 0, max_length)
            if truncate_pos == -1:
                truncate_pos = max_length
            text = text[:truncate_pos + 1]
        
        prompt = f"请总结以下网页内容，提取关键信息：\n\n{text}"
        self._process_ai_request(prompt, "请总结当前页面内容", use_deep_thinking=False)
        
    def handle_selection_explain(self, text):
        """处理划词解释"""
        prompt = f"请解释以下文本：\n\n{text}"
        if len(text) < 100:
            self._process_ai_request(prompt, f"请解释选中的文本：\n{text}", use_deep_thinking=False)
        else:
            self._process_ai_request(prompt, f"请解释选中的文本：\n{text[:100]}\n......", use_deep_thinking=False)
        
    def on_cite_webpage(self):
        """引用当前网页 - 提取网页内容"""
        current_browser = self.parent.tabs.currentWidget()
        if current_browser:
            # 获取当前网页URL
            url = current_browser.url().toString()

            # 检查是否已经引用过
            if url in self.cited_webpages:
                return

            # 使用JavaScript提取页面内容（参考explain_current_page的实现）
            js_code = """
            (function() {
                // 获取正文文本（不修改页面DOM）
                var body = document.body;
                if (!body) return '';
                var text = body.innerText || body.textContent;
                // 清理多余空白，保留换行符以便阅读
                text = text.replace(/[ \\t]+/g, ' ');
                text = text.replace(/\\n\\s*\\n\\s*\\n/g, '\\n\\n');
                return text.trim();
            })()
            """
            current_browser.page().runJavaScript(
                js_code, lambda text: self.process_cite_webpage(url, text))

    def process_cite_webpage(self, url, content):
        """处理引用的网页内容"""
        # 检查内容是否为空
        if not content or len(content.strip()) == 0:
            # 如果无法获取内容，只添加URL
            page_content = "[无法获取页面内容]"
        else:
            # 清理内容（参考process_page_explain的处理）
            text = content.strip()
            # 合并多余空白
            text = re.sub(r'\s+', ' ', text)
            # 智能截断，限制内容长度
            max_length = 3000
            if len(text) > max_length:
                # 尝试在句号、问号、感叹号后截断
                truncate_pos = text.rfind('。', 0, max_length)
                if truncate_pos == -1:
                    truncate_pos = text.rfind('.', 0, max_length)
                if truncate_pos == -1:
                    truncate_pos = text.rfind('?', 0, max_length)
                if truncate_pos == -1:
                    truncate_pos = text.rfind('!', 0, max_length)
                if truncate_pos == -1:
                    truncate_pos = max_length
                text = text[:truncate_pos + 1]
            page_content = text

        # 存储URL和内容
        self.cited_webpages.append(url)
        self.cited_webpage_contents[url] = page_content
        
        # 不再清除已上传的文档和图片，因为引用网页可以与上传内容共存
        # 但根据业务逻辑，引用网页时确实不能同时有上传的图片和文档
        # 所以需要清除上传的内容，但不能清除预览布局中的其他网页缩略图
        if self.uploaded_documents:
            self.clear_uploaded_documents()
        if self.uploaded_images:
            self.clear_uploaded_images()
        
        self.add_webpage_thumbnail(url, len(self.cited_webpages))

        # 显示预览区域
        if self.cited_webpages:
            self.image_preview_widget.show()
            # 有引用网页时禁用上传图片按钮和上传文档按钮
            self.upload_image_btn.setEnabled(False)
            self.upload_doc_btn.setEnabled(False)
    
    def add_webpage_thumbnail(self, url, page_index):
        """添加网页缩略图到预览区域"""
        # 创建缩略图容器
        thumbnail_container = QFrame()
        thumbnail_container.setFixedSize(60, 60)
        thumbnail_container.setStyleSheet("""
            QFrame {
                background-color: #fce4ec;
                border-radius: 4px;
                border: 1px solid #f8bbd9;
            }
        """)
        # 存储URL到容器属性
        thumbnail_container.setProperty("webpage_url", url)
        
        container_layout = QVBoxLayout(thumbnail_container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)
        
        # 显示网页序号
        page_label = QLabel(f"网页{page_index}")
        page_label.setFont(QFont("Microsoft YaHei", 9))
        page_label.setStyleSheet("""
            QLabel {
                color: #c2185b;
                background-color: transparent;
                border: none;
            }
            QLabel QToolTip {
                background-color: white;
                color: black;
                border: 1px solid #cccccc;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        page_label.setAlignment(Qt.AlignCenter)
        page_label.setToolTip(url)  # 鼠标悬停显示URL
        container_layout.addWidget(page_label, alignment=Qt.AlignCenter)
        
        # 创建删除按钮
        delete_btn = QLabel("×", thumbnail_container)
        delete_btn.setFixedSize(20, 20)
        delete_btn.setAlignment(Qt.AlignCenter)
        delete_btn.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #666666;
                font-size: 16px;
                font-weight: 300;
                padding-top: -4px;
                font-family: sans-serif;
                border: none;
            }
            QLabel:hover {
                color: #333333;
                border: none;
            }
        """)
        delete_btn.move(42, 0)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 绑定删除事件
        delete_btn.mousePressEvent = lambda _, u=url, container=thumbnail_container: self.remove_webpage(u, container)
        
        # 使用 QGraphicsOpacityEffect 实现平滑淡入淡出动画
        opacity_effect = QGraphicsOpacityEffect(delete_btn)
        delete_btn.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)
        
        fade_in_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_in_anim.setDuration(200)
        fade_in_anim.setStartValue(0.0)
        fade_in_anim.setEndValue(1.0)
        fade_in_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        fade_out_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out_anim.setDuration(150)
        fade_out_anim.setStartValue(1.0)
        fade_out_anim.setEndValue(0.0)
        fade_out_anim.setEasingCurve(QEasingCurve.InCubic)
        
        def on_enter(_):
            fade_in_anim.start()
        
        def on_leave(_):
            fade_out_anim.start()
        
        thumbnail_container.enterEvent = on_enter
        thumbnail_container.leaveEvent = on_leave
        
        # 添加到预览布局
        self.image_preview_layout.addWidget(thumbnail_container)
        
        # 更新所有网页缩略图的序号
        self.update_webpage_labels()
    
    def update_webpage_labels(self):
        """更新所有网页缩略图的序号显示"""
        for i in range(self.image_preview_layout.count()):
            item = self.image_preview_layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                # 获取容器存储的URL
                url = container.property("webpage_url")
                if url and url in self.cited_webpages:
                    # 找到容器中的 QLabel（网页标签）
                    for j in range(container.layout().count()):
                        widget = container.layout().itemAt(j).widget()
                        if isinstance(widget, QLabel) and widget.text().startswith("网页"):
                            page_index = self.cited_webpages.index(url) + 1
                            widget.setText(f"网页{page_index}")
    
    def remove_webpage(self, url, container):
        """移除引用的网页"""
        if url in self.cited_webpages:
            self.cited_webpages.remove(url)
        
        # 从布局中移除并删除容器
        self.image_preview_layout.removeWidget(container)
        container.deleteLater()
        
        # 如果没有引用的网页了，隐藏预览区域并启用上传按钮
        if not self.cited_webpages:
            self.upload_image_btn.setEnabled(True)
            self.upload_doc_btn.setEnabled(True)
            if not self.uploaded_images and not self.uploaded_documents:
                self.image_preview_widget.hide()
        else:
            # 更新剩余网页的序号
            self.update_webpage_labels()
    
    def clear_cited_webpages(self):
        """清空所有引用的网页"""
        self.cited_webpages.clear()
        self.cited_webpage_contents.clear()

        # 清除所有网页缩略图（粉色背景）
        i = 0
        while i < self.image_preview_layout.count():
            item = self.image_preview_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 检查是否是网页缩略图（粉色背景）
                if "fce4ec" in widget.styleSheet():
                    self.image_preview_layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    i += 1
            else:
                i += 1
        
        # 启用上传图片和文档按钮
        self.upload_image_btn.setEnabled(True)
        self.upload_doc_btn.setEnabled(True)
        
        # 如果没有图片和文档了，隐藏预览区域
        if not self.uploaded_images and not self.uploaded_documents:
            self.image_preview_widget.hide()
        
    def on_upload_image(self):
        """处理图片上传"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择图片")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                if file_path not in self.uploaded_images:
                    self.uploaded_images.append(file_path)
                    self.add_image_thumbnail(file_path)
            
            # 显示图片预览区域
            if self.uploaded_images:
                self.image_preview_widget.show()
                # 有图片时禁用联网搜索按钮、引用网页按钮、上传文档按钮，并取消勾选
                self.search_toggle_btn.setEnabled(False)
                self.search_toggle_btn.setChecked(False)
                self.use_search = False
                self.cite_webpage_btn.setEnabled(False)
                self.upload_doc_btn.setEnabled(False)
    
    def add_image_thumbnail(self, img_path):
        """添加图片缩略图到预览区域"""
        # 创建缩略图容器
        thumbnail_container = QFrame()
        thumbnail_container.setFixedSize(60, 60)
        thumbnail_container.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 4px;
                border: 1px solid #ffe0b2;
            }
        """)
        
        container_layout = QVBoxLayout(thumbnail_container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)
        
        # 加载并显示图片
        try:
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                # 缩放为50x50的缩略图
                scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                img_label = QLabel()
                img_label.setPixmap(scaled_pixmap)
                img_label.setFixedSize(50, 50)
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("background-color: transparent; border: none;")
                container_layout.addWidget(img_label, alignment=Qt.AlignCenter)
        except Exception as e:
            print(f"加载图片失败: {e}")
            return
        
        # 创建删除按钮
        delete_btn = QLabel("×", thumbnail_container)
        delete_btn.setFixedSize(20, 20)
        delete_btn.setAlignment(Qt.AlignCenter)
        delete_btn.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #666666;
                font-size: 16px;
                font-weight: 300;
                padding-top: -4px;
                font-family: sans-serif;
                border: none;
            }
            QLabel:hover {
                color: #333333;
                border: none;
            }
        """)
        delete_btn.move(42, 0)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 绑定删除事件
        delete_btn.mousePressEvent = lambda _, path=img_path, container=thumbnail_container: self.remove_image(path, container)
        
        # 使用 QGraphicsOpacityEffect 实现平滑淡入淡出动画
        opacity_effect = QGraphicsOpacityEffect(delete_btn)
        delete_btn.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)
        
        fade_in_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_in_anim.setDuration(200)
        fade_in_anim.setStartValue(0.0)
        fade_in_anim.setEndValue(1.0)
        fade_in_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        fade_out_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out_anim.setDuration(150)
        fade_out_anim.setStartValue(1.0)
        fade_out_anim.setEndValue(0.0)
        fade_out_anim.setEasingCurve(QEasingCurve.InCubic)
        
        def on_enter(_):
            fade_in_anim.start()
        
        def on_leave(_):
            fade_out_anim.start()
        
        thumbnail_container.enterEvent = on_enter
        thumbnail_container.leaveEvent = on_leave
        
        # 添加到预览布局
        self.image_preview_layout.addWidget(thumbnail_container)
    
    def remove_image(self, img_path, container):
        """移除上传的图片"""
        if img_path in self.uploaded_images:
            self.uploaded_images.remove(img_path)
        
        # 从布局中移除并删除容器
        self.image_preview_layout.removeWidget(container)
        container.deleteLater()
        
        # 如果没有图片了，隐藏预览区域并启用搜索按钮、引用网页按钮和上传文档按钮
        if not self.uploaded_images:
            self.image_preview_widget.hide()
            self.search_toggle_btn.setEnabled(True)
            self.cite_webpage_btn.setEnabled(True)
            self.upload_doc_btn.setEnabled(True)
    
    def clear_uploaded_images(self):
        """清空所有上传的图片"""
        self.uploaded_images.clear()
        
        # 只清除图片缩略图（灰色背景），保留网页和文档缩略图
        i = 0
        while i < self.image_preview_layout.count():
            item = self.image_preview_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 检查是否是图片缩略图（灰色背景 #f5f5f5）
                if "#f5f5f5" in widget.styleSheet():
                    self.image_preview_layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    i += 1
            else:
                i += 1
        
        # 如果没有引用的网页和文档了，隐藏预览区域
        if not self.cited_webpages and not self.uploaded_documents:
            self.image_preview_widget.hide()
        # 启用联网搜索按钮、引用网页按钮和上传文档按钮
        self.search_toggle_btn.setEnabled(True)
        self.cite_webpage_btn.setEnabled(True)
        self.upload_doc_btn.setEnabled(True)
        
    def handle_selection_translate(self, text):
        """处理划词翻译"""
        prompt = f"请翻译以下文本：\n\n{text}"
        if len(text) < 100:
            self._process_ai_request(prompt, f"请翻译选中的文本：\n{text}", use_deep_thinking=False)
        else:
            self._process_ai_request(prompt, f"请翻译选中的文本：\n{text[:100]}\n......", use_deep_thinking=False)
        
    def on_upload_document(self):
        """处理文档上传"""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择文档")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("文档文件 (*.txt *.docx *.pdf *.xlsx *.md *.csv)")
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                if file_path not in self.uploaded_documents:
                    self.uploaded_documents.append(file_path)
                    self.add_document_thumbnail(file_path, len(self.uploaded_documents))
            
            # 显示文档预览区域
            if self.uploaded_documents:
                self.image_preview_widget.show()
                # 有文档时禁用上传图片按钮、联网搜索按钮、深度思考按钮和引用网页按钮
                self.upload_image_btn.setEnabled(False)
                self.search_toggle_btn.setEnabled(False)
                self.search_toggle_btn.setChecked(False)
                self.cite_webpage_btn.setEnabled(False)
                self.use_search = False
                self.think_toggle_btn.setEnabled(False)
                self.think_toggle_btn.setChecked(False)
                self.use_deep_thinking = False
    
    def add_document_thumbnail(self, doc_path, doc_index):
        """添加文档缩略图到预览区域"""
        # 创建缩略图容器
        thumbnail_container = QFrame()
        thumbnail_container.setFixedSize(60, 60)
        thumbnail_container.setStyleSheet("""
            QFrame {
                background-color: #dcf4ee;
                border-radius: 4px;
                border: 1px solid #b4f0dc;
            }
        """)
        # 存储完整文档路径到容器属性
        thumbnail_container.setProperty("doc_path", doc_path)
        
        container_layout = QVBoxLayout(thumbnail_container)
        container_layout.setContentsMargins(2, 2, 2, 2)
        container_layout.setSpacing(0)
        
        # 显示文档序号
        doc_label = QLabel(f"文档{doc_index}")
        doc_label.setFont(QFont("Microsoft YaHei", 9))
        doc_label.setStyleSheet("""
            QLabel {
                color: #60A893;
                background-color: transparent;
                border: none;
            }
            QLabel QToolTip {
                background-color: white;
                color: black;
                border: 1px solid #cccccc;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
            }
        """)
        doc_label.setAlignment(Qt.AlignCenter)
        doc_label.setToolTip(os.path.basename(doc_path))  # 鼠标悬停显示文件名
        container_layout.addWidget(doc_label, alignment=Qt.AlignCenter)
        
        # 创建删除按钮
        delete_btn = QLabel("×", thumbnail_container)
        delete_btn.setFixedSize(20, 20)
        delete_btn.setAlignment(Qt.AlignCenter)
        delete_btn.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #666666;
                font-size: 16px;
                font-weight: 300;
                padding-top: -4px;
                font-family: sans-serif;
                border: none;
            }
            QLabel:hover {
                color: #333333;
                border: none;
            }
        """)
        delete_btn.move(42, 0)
        delete_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        # 绑定删除事件
        delete_btn.mousePressEvent = lambda _, path=doc_path, container=thumbnail_container: self.remove_document(path, container)
        
        # 使用 QGraphicsOpacityEffect 实现平滑淡入淡出动画
        opacity_effect = QGraphicsOpacityEffect(delete_btn)
        delete_btn.setGraphicsEffect(opacity_effect)
        opacity_effect.setOpacity(0.0)
        
        fade_in_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_in_anim.setDuration(200)
        fade_in_anim.setStartValue(0.0)
        fade_in_anim.setEndValue(1.0)
        fade_in_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        fade_out_anim = QPropertyAnimation(opacity_effect, b"opacity")
        fade_out_anim.setDuration(150)
        fade_out_anim.setStartValue(1.0)
        fade_out_anim.setEndValue(0.0)
        fade_out_anim.setEasingCurve(QEasingCurve.InCubic)
        
        def on_enter(_):
            fade_in_anim.start()
        
        def on_leave(_):
            fade_out_anim.start()
        
        thumbnail_container.enterEvent = on_enter
        thumbnail_container.leaveEvent = on_leave
        
        # 添加到预览布局
        self.image_preview_layout.addWidget(thumbnail_container)
        
        # 更新所有文档缩略图的序号
        self.update_document_labels()
    
    def update_document_labels(self):
        """更新所有文档缩略图的序号显示"""
        for i in range(self.image_preview_layout.count()):
            item = self.image_preview_layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                # 获取容器存储的文档路径
                doc_path = container.property("doc_path")
                if doc_path and doc_path in self.uploaded_documents:
                    # 找到容器中的 QLabel（文档标签）
                    for j in range(container.layout().count()):
                        widget = container.layout().itemAt(j).widget()
                        if isinstance(widget, QLabel) and widget.text().startswith("文档"):
                            doc_index = self.uploaded_documents.index(doc_path) + 1
                            widget.setText(f"文档{doc_index}")
                            # 更新 tooltip 为新的文件名
                            widget.setToolTip(os.path.basename(doc_path))
    
    def remove_document(self, doc_path, container):
        """移除上传的文档"""
        if doc_path in self.uploaded_documents:
            self.uploaded_documents.remove(doc_path)
        
        # 从布局中移除并删除容器
        self.image_preview_layout.removeWidget(container)
        container.deleteLater()
        
        # 如果没有文档了，隐藏预览区域并启用上传图片按钮、搜索按钮、深度思考按钮和引用网页按钮
        if not self.uploaded_documents:
            self.image_preview_widget.hide()
            self.upload_image_btn.setEnabled(True)
            self.search_toggle_btn.setEnabled(True)
            self.think_toggle_btn.setEnabled(True)
            self.cite_webpage_btn.setEnabled(True)
        else:
            # 更新剩余文档的序号
            self.update_document_labels()
    
    def clear_uploaded_documents(self):
        """清空所有上传的文档"""
        self.uploaded_documents.clear()
        
        # 清除所有文档缩略图（只保留图片和网页缩略图）
        i = 0
        while i < self.image_preview_layout.count():
            item = self.image_preview_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 检查是否是文档缩略图（绿色背景 #dcf4ee）
                if "#dcf4ee" in widget.styleSheet():
                    self.image_preview_layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    i += 1
            else:
                i += 1
        
        # 如果没有图片和引用的网页了，隐藏预览区域
        if not self.uploaded_images and not self.cited_webpages:
            self.image_preview_widget.hide()
        
        # 启用上传图片按钮、联网搜索按钮、深度思考按钮和引用网页按钮
        self.upload_image_btn.setEnabled(True)
        self.search_toggle_btn.setEnabled(True)
        self.think_toggle_btn.setEnabled(True)
        self.cite_webpage_btn.setEnabled(True)