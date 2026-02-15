![Mindra Logo](Mindra_logo.png)

<div align="center">
  中文 | <a href="README.MD">英文</a>
</div>

**Mindra**是一款创新的AI驱动网络浏览器，将先进的人工智能功能直接集成到您的浏览体验中。通过AI侧边栏助手、智能内容解析和无缝用户管理等功能，Mindra彻底改变了您与网络交互的方式。

## 功能特性

- **AI驱动侧边栏**：在浏览时获得实时AI助手支持，支持文本、图像和文档分析
- **高级模型集成**：支持多种AI模型处理不同任务（文本解析、图像分析、日常对话）
- **用户管理系统**：安全的用户认证系统，支持激活码和信用余额跟踪
- **可自定义界面**：基于PySide6的现代化界面，支持样式和设置自定义
- **Cookie管理**：内置Cookie管理，增强隐私保护和会话控制
- **主页集成**：自定义主页，快速访问AI功能

## 数据库设置

### 创建数据库

1. **创建数据库架构**

   使用提供的`mindra.sql`文件创建所需的数据库结构：

   ```sql
   -- 连接到您的MySQL服务器
   mysql -u your_username -p
   
   -- 创建mindra数据库
   CREATE DATABASE mindra CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- 使用数据库
   USE mindra;
   
   -- 执行mindra.sql文件
   SOURCE /path/to/mindra.sql;
   ```

2. **数据库架构概览**

   数据库包含两个主要表：

   - **`users`表**：
     - `user_id`：主键（整数）
     - `username`：用户名（varchar）
     - `password`：哈希密码（varchar）
     - `created_at`：账户创建时间戳
     - `credit_balance`：用户信用余额（decimal）

   - **`activation`表**：
     - `activation_code`：唯一激活码（varchar）
     - `user_id`：外键，关联到users表（整数）

### 数据库配置

创建数据库后，在`config.yaml`中配置连接：

```yaml
database:
  host: "your_database_host"
  database: "mindra"
  user: "your_database_username"
  password: "your_database_password"

ai:
  api_key: "your_ai_api_key"
  base_url: "your_ai_base_url"

models:
  text_parsing: "your_text_parsing_model" # 例如: qwen-long-latest
  image_parsing: "your_image_parsing_model" # 例如: qwen3-vl-plus
  daily_conversation: "your_daily_conversation_model" # 例如: deepseek-v3.1
```

## 安装

### 先决条件

- Python 3.8+
- MySQL 8.0+

### 所需Python包

安装以下Python包：

```bash
pip install PySide6 openai pymysql PyYAML
```

### 设置步骤

1. **克隆或下载项目**
2. **按照上述步骤配置数据库**
3. **在`config.yaml`中更新数据库和AI服务凭据**
4. **运行应用程序**：

```bash
python main.py
```

## 使用方法

1. **首次启动**：应用程序将提示您登录或注册
2. **AI侧边栏**：通过集成的侧边栏访问AI助手
3. **浏览器功能**：标准网页浏览，增强AI功能
4. **设置**：通过设置对话框配置AI模型、外观和其他偏好设置

## 配置

### config.yaml结构

配置文件控制数据库连接和AI服务集成：

- **Database部分**：MySQL连接参数
- **AI部分**：AI服务的API凭据
- **Models部分**：指定用于不同任务的AI模型

### 用户管理

- 新用户需要激活码才能注册
- 用户信用额度在数据库中跟踪
- 密码经过安全哈希处理

## 故障排除

### 常见问题

1. **数据库连接错误**：
   - 验证MySQL服务器是否正在运行
   - 检查`config.yaml`中的数据库凭据
   - 确保`mindra`数据库存在并具有适当权限

2. **AI服务错误**：
   - 验证`config.yaml`中的API密钥和基础URL
   - 检查指定的模型在您的AI服务中是否可用

3. **缺少依赖项**：
   - 确保安装了所有必需的Python包
   - 使用`pip list`验证安装