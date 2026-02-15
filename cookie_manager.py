import json
from PySide6.QtCore import QDateTime, QTimer
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtWebEngineCore import QWebEngineProfile


class CookieManager:
    """Cookie管理器类"""
    
    def __init__(self, data_dir):
        """初始化Cookie管理器"""
        self.data_dir = data_dir
        self.cookie_dir = self.data_dir / "cookie"
        self.cookie_dir.mkdir(exist_ok=True)
        
        # 获取默认浏览器配置文件
        self.profile = QWebEngineProfile.defaultProfile()
        
        # 连接cookie变化信号
        self.profile.cookieStore().cookieAdded.connect(self.on_cookie_added)
        self.profile.cookieStore().cookieRemoved.connect(self.on_cookie_removed)
        
        # 使用定时器延迟保存，避免频繁保存
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._save_cookies_delayed)
        
        # 存储当前所有cookie
        self.cookies = []
    
    def on_cookie_added(self, cookie):
        """当有新cookie添加时调用"""
        # 检查定时器是否仍然有效
        if not hasattr(self, 'save_timer') or self.save_timer is None:
            return
            
        # 检查C++对象是否已被删除
        try:
            if not self.save_timer.isActive():
                # 如果无法访问isActive，说明对象已被删除
                return
        except RuntimeError:
            # C++对象已被删除，直接返回
            return
            
        # 添加到cookie列表
        cookie_data = self._cookie_to_dict(cookie)
        # 检查是否已存在相同cookie
        for i, existing_cookie in enumerate(self.cookies):
            if (existing_cookie['name'] == cookie_data['name'] and 
                existing_cookie['domain'] == cookie_data['domain'] and 
                existing_cookie['path'] == cookie_data['path']):
                # 更新现有cookie
                self.cookies[i] = cookie_data
                break
        else:
            # 添加新cookie
            self.cookies.append(cookie_data)
        
        # 延迟保存，避免频繁IO操作（检查timer是否有效）
        try:
            if self.save_timer.isActive():
                self.save_timer.stop()
            self.save_timer.start(1000)  # 1秒后保存
        except RuntimeError:
            # C++对象已被删除，直接返回
            return
    
    def on_cookie_removed(self, cookie):
        """当有cookie删除时调用"""
        # 检查定时器是否仍然有效
        if not hasattr(self, 'save_timer') or self.save_timer is None:
            return
            
        # 检查C++对象是否已被删除
        try:
            if not self.save_timer.isActive():
                # 如果无法访问isActive，说明对象已被删除
                return
        except RuntimeError:
            # C++对象已被删除，直接返回
            return
            
        cookie_data = self._cookie_to_dict(cookie)
        # 从列表中移除
        self.cookies = [c for c in self.cookies 
                       if not (c['name'] == cookie_data['name'] and 
                              c['domain'] == cookie_data['domain'] and 
                              c['path'] == cookie_data['path'])]
        
        # 延迟保存（检查timer是否有效）
        try:
            if self.save_timer.isActive():
                self.save_timer.stop()
            self.save_timer.start(1000)  # 1秒后保存
        except RuntimeError:
            # C++对象已被删除，直接返回
            return
    
    def _cookie_to_dict(self, cookie):
        """将QNetworkCookie转换为字典"""
        # 处理SameSite枚举类型，转换为字符串
        same_site_policy = cookie.sameSitePolicy()
        same_site_str = ""
        
        # 使用枚举值进行比较，避免属性名错误
        if same_site_policy == QNetworkCookie.SameSite.Lax:
            same_site_str = "Lax"
        elif same_site_policy == QNetworkCookie.SameSite.Strict:
            same_site_str = "Strict"
        elif same_site_policy == QNetworkCookie.SameSite(0):  # 无限制模式
            same_site_str = "NoRestriction"
        else:
            same_site_str = "Default"
            
        return {
            'name': cookie.name().data().decode('utf-8'),
            'value': cookie.value().data().decode('utf-8'),
            'domain': cookie.domain(),
            'path': cookie.path(),
            'expiration': cookie.expirationDate().toString('yyyy-MM-dd hh:mm:ss') if cookie.expirationDate().isValid() else '',
            'secure': cookie.isSecure(),
            'http_only': cookie.isHttpOnly(),
            'same_site': same_site_str
        }
    
    def _dict_to_cookie(self, cookie_dict):
        """将字典转换为QNetworkCookie"""
        cookie = QNetworkCookie()
        cookie.setName(cookie_dict['name'].encode('utf-8'))
        cookie.setValue(cookie_dict['value'].encode('utf-8'))
        cookie.setDomain(cookie_dict['domain'])
        cookie.setPath(cookie_dict['path'])
        
        if cookie_dict['expiration']:
            cookie.setExpirationDate(QDateTime.fromString(cookie_dict['expiration'], 'yyyy-MM-dd hh:mm:ss'))
        
        cookie.setSecure(cookie_dict['secure'])
        cookie.setHttpOnly(cookie_dict['http_only'])
        
        # 将字符串转换回SameSite枚举类型
        same_site_str = cookie_dict['same_site']
        if same_site_str == "Lax":
            cookie.setSameSitePolicy(QNetworkCookie.SameSite.Lax)
        elif same_site_str == "Strict":
            cookie.setSameSitePolicy(QNetworkCookie.SameSite.Strict)
        elif same_site_str == "NoRestriction":
            cookie.setSameSitePolicy(QNetworkCookie.SameSite(0))  # 无限制模式
        else:
            cookie.setSameSitePolicy(QNetworkCookie.SameSite.Default)
        
        return cookie
    
    def _save_cookies_delayed(self):
        """延迟保存cookie"""
        try:
            # 保存到JSON文件
            cookie_file = self.cookie_dir / "cookies.json"
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(self.cookies, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存cookie时出错: {str(e)}")
    
    def save_cookies(self):
        """立即保存所有cookie"""
        # 检查定时器是否仍然有效
        if not hasattr(self, 'save_timer') or self.save_timer is None:
            return
            
        # 检查C++对象是否已被删除
        try:
            if self.save_timer.isActive():
                self.save_timer.stop()
        except RuntimeError:
            # C++对象已被删除，直接返回
            return
            
        # 立即保存
        self._save_cookies_delayed()
    
    def load_cookies(self):
        """从文件加载cookie"""
        try:
            cookie_file = self.cookie_dir / "cookies.json"
            if not cookie_file.exists():
                return
            
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data_list = json.load(f)
            
            # 清空当前列表
            self.cookies.clear()
            
            # 加载cookie到浏览器
            for cookie_data in cookie_data_list:
                cookie = self._dict_to_cookie(cookie_data)
                self.profile.cookieStore().setCookie(cookie)
                # 同时添加到内存列表
                self.cookies.append(cookie_data)
                
        except Exception as e:
            print(f"加载cookie时出错: {str(e)}")
    
    def clear_cookies(self):
        """清除所有cookie"""
        self.profile.cookieStore().deleteAllCookies()
        self.cookies.clear()
        
        # 删除cookie文件
        cookie_file = self.cookie_dir / "cookies.json"
        if cookie_file.exists():
            cookie_file.unlink()