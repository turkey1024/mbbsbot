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

class MultiAccountSpamBot:
    def __init__(self, base_url, accounts):
        self.base_url = base_url.replace('https://', 'http://')
        self.accounts = accounts  # 账号列表
        self.comments_per_account = 50  # 每个账号评论50条
        self.target_thread_id = None
        self.comment_content = "phpbest"
        
        # 存储每个账号的session和token
        self.account_sessions = {}
        self.account_tokens = {}

    def aggressive_request(self, method, url, session, token=None, **kwargs):
        """激进请求方法"""
        kwargs.update({
            'timeout': 3,
            'verify': False,
            'headers': kwargs.get('headers', {})
        })
        
        headers = kwargs['headers']
        headers.update({
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if token:
            headers['Authorization'] = token
        
        for _ in range(3):  # 自动重试3次
            try:
                return session.request(method, url, **kwargs)
            except:
                time.sleep(0.1)
        return None

    def login_account(self, username, password):
        """登录单个账号"""
        print(f"🔐 正在登录账号: {username}")
        
        # 创建session
        session = requests.Session()
        session.verify = False
        session.trust_env = False
        
        adapter = requests.adapters.HTTPAdapter(
            max_retries=3,
            pool_connections=10,
            pool_maxsize=10
        )
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        login_bot = BBSTurkeyBotLogin(self.base_url, username, password)
        login_bot.session = session
        
        for attempt in range(3):
            try:
                success, result, _ = login_bot.login_with_retry()
                if success:
                    token = result['data']['token']
                    user_id = result['data']['id']
                    self.account_sessions[username] = session
                    self.account_tokens[username] = token
                    print(f"✅ {username} 登录成功！用户ID: {user_id}")
                    return True
            except Exception as e:
                print(f"❌ {username} 登录失败 {attempt+1}/3: {str(e)}")
                time.sleep(2)
        
        print(f"💥 {username} 登录彻底失败")
        return False

    def login_all_accounts(self):
        """登录所有账号"""
        print("👥 开始登录所有账号...")
        success_count = 0
        
        for account in self.accounts:
            if self.login_account(account['username'], account['password']):
                success_count += 1
            time.sleep(1)  # 账号间登录间隔
        
        print(f"📊 账号登录完成: {success_count}/{len(self.accounts)} 成功")
        return success_count > 0
    def find_test_thread(self, username):
        """查找test帖子"""
        try:
            session = self.account_sessions[username]
            token = self.account_tokens[username]
            
            response = self.aggressive_request(
                'GET',
                f"{self.base_url}/bbs/threads/list",
                session=session,
                token=token,
                params={'page_limit': 50}
            )
            
            if response and response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    for thread in data.get('data', []):
                        if 'test' in thread.get('title', '').lower():
                            if not self.target_thread_id:
                                self.target_thread_id = thread['id']
                                print(f"🎯 找到目标帖子ID: {self.target_thread_id}")
                            return True
        except Exception as e:
            print(f"⚠️ {username} 查找帖子异常: {str(e)}")
        return False

    def spam_with_account(self, username):
        """单个账号评论任务"""
        if not self.target_thread_id:
            if not self.find_test_thread(username):
                print(f"❌ {username} 未找到目标帖子")
                return 0
        
        session = self.account_sessions[username]
        token = self.account_tokens[username]
        success_count = 0
        
        print(f"🚀 {username} 开始评论...")
        
        for i in range(self.comments_per_account):
            try:
                response = self.aggressive_request(
                    'POST',
                    f"{self.base_url}/bbs/posts/create",
                    session=session,
                    token=token,
                    json={
                        'thread_id': self.target_thread_id,
                        'content': f"{self.comment_content}_{username}_{i+1}"
                    }
                )
                
                if response and response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        success_count += 1
                        if success_count % 10 == 0:
                            print(f"✅ {username} 已评论 {success_count} 条")
                    else:
                        print(f"⚠️ {username} 评论失败: {data.get('message')}")
                else:
                    print(f"❌ {username} HTTP错误")
                
                # 稍微延迟避免过快被限制
                time.sleep(0.5)
                
            except Exception as e:
                print(f"💥 {username} 评论异常: {str(e)}")
        
        print(f"📊 {username} 评论完成: {success_count}/{self.comments_per_account} 成功")
        return success_count

    def run_spam_attack(self):
        """执行多账号评论攻击"""
        print("="*60)
        print("🤖 多账号轮换评论机器人")
        print("="*60)
        
        if not self.login_all_accounts():
            print("❌ 账号登录失败，无法继续")
            return False
        
        # 先找到目标帖子
        found_thread = False
        for username in self.account_sessions.keys():
            if self.find_test_thread(username):
                found_thread = True
                break
        
        if not found_thread:
            print("❌ 未找到目标test帖子")
            return False
        
        print(f"🎯 开始多账号评论攻击，目标: {self.comments_per_account} 条/账号")
        
        total_comments = 0
        with ThreadPoolExecutor(max_workers=len(self.account_sessions)) as executor:
            # 提交所有账号的评论任务
            future_to_account = {
                executor.submit(self.spam_with_account, username): username 
                for username in self.account_sessions.keys()
            }
            
            # 等待所有任务完成
            for future in as_completed(future_to_account):
                username = future_to_account[future]
                try:
                    count = future.result()
                    total_comments += count
                except Exception as e:
                    print(f"💥 {username} 任务异常: {str(e)}")
        
        print(f"🎉 本轮评论完成! 总评论数: {total_comments}")
        return total_comments > 0

def main():
    """主函数"""
    # 配置所有账号
    ACCOUNTS = [
        {'username': 'turkeybot', 'password': 'passwordbotonly'},
        {'username': 'turkeybot1', 'password': 'passwordbotonly'},
        {'username': 'turkeybot2', 'password': 'passwordbotonly'},
        {'username': 'turkeybot3', 'password': 'passwordbotonly'},
        {'username': 'turkeybot4', 'password': 'passwordbotonly'}
    ]
    
    BOT_CONFIG = {
        "base_url": "http://chess.free.mbbs.cc",
        "accounts": ACCOUNTS
    }
    
    bot = MultiAccountSpamBot(**BOT_CONFIG)
    bot.run_spam_attack()

if __name__ == "__main__":
    main()

