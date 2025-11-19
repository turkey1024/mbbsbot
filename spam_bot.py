import requests
import json
import time
import threading
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from login import BBSTurkeyBotLogin

# 禁用SSL警告和验证
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TestSpamBot:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        
        # 创建自定义session，禁用SSL验证
        self.session = requests.Session()
        self.session.verify = False
        
        self.token = None
        self.user_id = None
        
        # 目标帖子标题
        self.target_thread_title = "test"
        self.target_thread_id = None
        
        # 评论内容
        self.comment_content = "phpbest"
        
        # 并发配置
        self.max_workers = 500  # 增加并发线程数
        self.comments_per_batch = 100  # 增加每批评论数量
        self.delay_between_batches = 0  # 无延迟

    def login(self):
        """登录论坛"""
        print("🔐 正在登录论坛...")
        login_bot = BBSTurkeyBotLogin(self.base_url, self.username, self.password)
        login_success, login_result, session = login_bot.login_with_retry()
        
        if login_success:
            # 使用自定义session而不是返回的session
            self.token = login_result.get('data', {}).get('token')
            self.user_id = login_result.get('data', {}).get('id')
            print(f"✅ 登录成功！用户ID: {self.user_id}")
            return True
        else:
            print("❌ 登录失败")
            return False

    def find_test_thread(self):
        """查找标题为test的帖子"""
        try:
            # 获取帖子列表
            list_threads_url = f"{self.base_url}/bbs/threads/list"
            headers = {
                'Authorization': self.token, 
                'Content-Type': 'application/json'
            }
            
            params = {
                "page_limit": 100,
                "page_offset": 0,
                "sort": "-created_at"
            }
            
            response = self.session.get(
                list_threads_url, 
                headers=headers, 
                params=params, 
                timeout=15,
                verify=False  # 禁用SSL验证
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    threads = result.get('data', [])
                    
                    for thread in threads:
                        title = thread.get('title', '').lower()
                        if 'test' in title:
                            self.target_thread_id = thread.get('id')
                            print(f"✅ 找到目标帖子: {thread.get('title')} (ID: {self.target_thread_id})")
                            return True
                    
                    print("❌ 未找到标题包含'test'的帖子")
                    return False
                else:
                    print(f"❌ 获取帖子列表失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 获取帖子列表HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 查找帖子异常: {e}")
            return False

    def create_comment(self, comment_index):
        """创建评论（单个评论任务）"""
        try:
            create_post_url = f"{self.base_url}/bbs/posts/create"
            headers = {
                'Authorization': self.token, 
                'Content-Type': 'application/json'
            }
            
            post_data = {
                "thread_id": self.target_thread_id,
                "content": f"{self.comment_content}_{comment_index}"
            }
            
            response = self.session.post(
                create_post_url, 
                json=post_data, 
                headers=headers, 
                timeout=10,
                verify=False  # 禁用SSL验证
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    print(f"✅ 评论 {comment_index} 发布成功！")
                    return True
                else:
                    print(f"❌ 评论 {comment_index} 发布失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 评论 {comment_index} HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 评论 {comment_index} 异常: {e}")
            return False

    def spam_comments_continuous(self):
        """持续不断发送评论"""
        if not self.target_thread_id:
            print("❌ 未找到目标帖子，无法开始评论")
            return
        
        print("🚀 开始持续评论攻击！按 Ctrl+C 停止")
        comment_count = 0
        
        try:
            while True:
                comment_count += 1
                success = self.create_comment(comment_count)
                
                if success:
                    print(f"📈 总成功评论数: {comment_count}")
                
                # 完全无间隔
                # time.sleep(0)
                
        except KeyboardInterrupt:
            print(f"\n🛑 用户中断！总共发送了 {comment_count} 条评论")
        except Exception as e:
            print(f"❌ 持续评论异常: {e}")

    def run(self):
        """运行机器人"""
        print("=" * 50)
        print("🤖 Test Spam Bot - 专注test帖子评论")
        print("=" * 50)
        
        if not self.login():
            return False
        
        if not self.find_test_thread():
            return False
        
        self.spam_comments_continuous()

if __name__ == "__main__":
    # 配置论坛地址和账户
    BOT_CONFIG = {
        "base_url": "https://chess.free.mbbs.cc",
        "username": "turkeybot", 
        "password": "passwordbotonly"
    }
    
    # 创建并运行机器人
    bot = TestSpamBot(**BOT_CONFIG)
    bot.run()

