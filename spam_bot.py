import requests
import json
import time
import threading
import urllib3
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from login import BBSTurkeyBotLogin

# 彻底禁用SSL验证和警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建自定义SSL上下文
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class TestSpamBot:
    def __init__(self, base_url, username, password):
        # 确保使用HTTP而不是HTTPS（如果服务器支持）
        if base_url.startswith('https://'):
            base_url = base_url.replace('https://', 'http://')
        self.base_url = base_url
        
        self.username = username
        self.password = password
        
        # 创建自定义session，完全禁用SSL验证
        self.session = requests.Session()
        self.session.verify = False
        self.session.mount('https://', requests.adapters.HTTPAdapter(
            max_retries=3,
            ssl_context=ssl_context
        ))
        
        self.token = None
        self.user_id = None
        self.target_thread_id = None
        self.comment_content = "phpbest"
        self.max_workers = 30  # 更高的并发数

    def login(self):
        """登录论坛（带重试机制）"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                print(f"🔐 正在尝试登录（尝试 {attempt + 1}/{max_retries}）...")
                login_bot = BBSTurkeyBotLogin(
                    self.base_url, 
                    self.username, 
                    self.password
                )
                login_success, login_result, _ = login_bot.login_with_retry()
                
                if login_success:
                    self.token = login_result.get('data', {}).get('token')
                    self.user_id = login_result.get('data', {}).get('id')
                    print(f"✅ 登录成功！用户ID: {self.user_id}")
                    return True
                
            except Exception as e:
                print(f"❌ 登录尝试 {attempt + 1} 失败: {str(e)}")
                time.sleep(2)  # 重试前等待
        
        print("❌ 所有登录尝试均失败")
        return False

    def find_test_thread(self):
        """查找test帖子（带异常处理）"""
        try:
            url = f"{self.base_url}/bbs/threads/list"
            headers = {'Authorization': self.token}
            params = {"page_limit": 100, "sort": "-created_at"}
            
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=10,
                verify=False
            )
            
            if response.ok:
                threads = response.json().get('data', [])
                for thread in threads:
                    if 'test' in thread.get('title', '').lower():
                        self.target_thread_id = thread.get('id')
                        print(f"✅ 找到目标帖子: ID {self.target_thread_id}")
                        return True
                
                print("❌ 未找到test帖子")
                return False
            
            print(f"❌ 获取帖子列表失败: HTTP {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ 查找帖子异常: {str(e)}")
            return False

    def spam_comments(self):
        """无限发送评论"""
        if not self.target_thread_id:
            return
            
        print("🚀 开始疯狂评论模式！按Ctrl+C停止")
        count = 0
        
        try:
            while True:
                count += 1
                try:
                    response = self.session.post(
                        f"{self.base_url}/bbs/posts/create",
                        headers={
                            'Authorization': self.token,
                            'Content-Type': 'application/json'
                        },
                        json={
                            "thread_id": self.target_thread_id,
                            "content": f"{self.comment_content}_{count}"
                        },
                        timeout=5,
                        verify=False
                    )
                    
                    if response.ok and response.json().get('success'):
                        print(f"✅ 已发送 {count} 条评论")
                    else:
                        print(f"❌ 评论失败: {response.text}")
                        
                except Exception as e:
                    print(f"⚠️ 评论异常: {str(e)}")
                    
                # 完全无间隔
                # time.sleep(0)
                
        except KeyboardInterrupt:
            print(f"\n🛑 已停止！总共发送了 {count} 条评论")

    def run(self):
        """主运行方法"""
        print("="*50)
        print("🤖 终极Test帖子刷评论机器人")
        print("="*50)
        
        if self.login() and self.find_test_thread():
            # 启动多线程评论
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self.spam_comments) for _ in range(self.max_workers)]
                for future in futures:
                    future.result()

if __name__ == "__main__":
    BOT_CONFIG = {
        "base_url": "http://chess.free.mbbs.cc",  # 强制使用HTTP
        "username": "turkeybot", 
        "password": "passwordbotonly"
    }
    
    bot = TestSpamBot(**BOT_CONFIG)
    bot.run()


