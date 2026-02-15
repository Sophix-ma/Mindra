![Mindra Logo](Mindra_logo.png)

<div align="center">
  English | <a href="README_ch.md">Chinese</a>
</div>

**Mindra** is an innovative AI-powered web browser that integrates advanced artificial intelligence capabilities directly into your browsing experience. With features like AI sidebar assistance, intelligent content parsing, and seamless user management, Mindra transforms how you interact with the web.

## Features

- **AI-Powered Sidebar**: Get real-time AI assistance while browsing with support for text, image, and document analysis
- **Advanced Models Integration**: Supports multiple AI models for different tasks (text parsing, image analysis, daily conversation)
- **User Management System**: Secure user authentication with activation codes and credit balance tracking
- **Customizable Interface**: Modern PySide6-based interface with customizable styles and settings
- **Cookie Management**: Built-in cookie management for enhanced privacy and session control
- **Home Page Integration**: Custom homepage with quick access to AI features

## Database Setup

### Creating the Database

1. **Create the Database Schema**

   Use the provided `mindra.sql` file to create the required database structure:

   ```sql
   -- Connect to your MySQL server
   mysql -u your_username -p
   
   -- Create the mindra database
   CREATE DATABASE mindra CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   
   -- Use the database
   USE mindra;
   
   -- Execute the mindra.sql file
   SOURCE /path/to/mindra.sql;
   ```

2. **Database Schema Overview**

   The database contains two main tables:

   - **`users` table**:
     - `user_id`: Primary key (integer)
     - `username`: User's username (varchar)
     - `password`: Hashed password (varchar)
     - `created_at`: Account creation timestamp
     - `credit_balance`: User's credit balance (decimal)

   - **`activation` table**:
     - `activation_code`: Unique activation code (varchar)
     - `user_id`: Foreign key linking to users table (integer)

### Database Configuration

After creating the database, configure the connection in `config.yaml`:

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
  text_parsing: "your_text_parsing_model" # eg. qwen-long-latest
  image_parsing: "your_image_parsing_model" # eg. qwen3-vl-plus
  daily_conversation: "your_daily_conversation_model" # eg. deepseek-v3.1
```

## Installation

### Prerequisites

- Python 3.8+
- MySQL 8.0+

### Required Python Packages

Install the following Python packages:

```bash
pip install PySide6 openai pymysql PyYAML
```

### Setup Steps

1. **Clone or download the project**
2. **Configure the database** using the steps above
3. **Update `config.yaml`** with your database and AI service credentials
4. **Run the application**:

```bash
python main.py
```

## Usage

1. **First Launch**: The application will prompt you to log in or register
2. **AI Sidebar**: Access AI assistance through the integrated sidebar
3. **Browser Functions**: Standard web browsing with enhanced AI capabilities
4. **Settings**: Configure AI models, appearance, and other preferences through the settings dialog

## Configuration

### config.yaml Structure

The configuration file controls both database connections and AI service integration:

- **Database Section**: MySQL connection parameters
- **AI Section**: API credentials for AI services
- **Models Section**: Specify which AI models to use for different tasks

### User Management

- New users need activation codes to register
- User credits are tracked in the database
- Passwords are securely hashed

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify MySQL server is running
   - Check database credentials in `config.yaml`
   - Ensure the `mindra` database exists and has proper permissions

2. **AI Service Errors**:
   - Verify API key and base URL in `config.yaml`
   - Check that specified models are available in your AI service

3. **Missing Dependencies**:
   - Ensure all required Python packages are installed
   - Use `pip list` to verify installations