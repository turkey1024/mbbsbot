import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from login import BBSTurkeyBotLogin

class TestSpamBot:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        
        self.session = None
        self.token = None
        self.user_id = None
        
        # 目标帖子标题
        self.target_thread_title = "test"
        self.target_thread_id = None
        
        # 评论内容
        self.comment_content = "phpbest"
        
        # 并发配置
        self.max_workers = 10  # 并发线程数
        self.comments_per_batch = 50  # 每批评论数量
        self.delay_between_batches = 0.1  # 批次间延迟（秒）

    def login(self):
        """登录论坛"""
        print("🔐 正在登录论坛...")
        login_bot = BBSTurkeyBotLogin(self.base_url, self.username, self.password)
        login_success, login_result, session = login_bot.login_with_retry()
        
        if login_success:
            self.session = session
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
            
            response = self.session.get(list_threads_url, headers=headers, params=params, timeout=15)
            
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
                "content": f"{self.comment_content}_{comment_index}"  # 添加索引避免重复检测
            }
            
            response = self.session.post(create_post_url, json=post_data, headers=headers, timeout=10)
            
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

    def spam_comments_concurrent(self, total_comments=1000):
        """并发发送评论"""
        if not self.target_thread_id:
            print("❌ 未找到目标帖子，无法开始评论")
            return
        
        print(f"🚀 开始并发评论攻击！目标: {total_comments} 条评论")
        print(f"🔧 并发配置: {self.max_workers} 线程, 每批 {self.comments_per_batch} 条")
        
        successful_comments = 0
        failed_comments = 0
        
        # 分批处理，避免内存问题
        batches = total_comments // self.comments_per_batch
        if total_comments % self.comments_per_batch > 0:
            batches += 1
        
        for batch in range(batches):
            start_index = batch * self.comments_per_batch
            end_index = min((batch + 1) * self.comments_per_batch, total_comments)
            batch_size = end_index - start_index
            
            print(f"\n🔄 处理批次 {batch + 1}/{batches}, 评论 {start_index + 1}-{end_index}")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_index = {
                    executor.submit(self.create_comment, i): i 
                    for i in range(start_index + 1, end_index + 1)
                }
                
                # 等待任务完成
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        success = future.result()
                        if success:
                            successful_comments += 1
                        else:
                            failed_comments += 1
                    except Exception as e:
                        print(f"❌ 评论 {index} 执行异常: {e}")
                        failed_comments += 1
            
            # 批次间短暂延迟
            if batch < batches - 1:  # 不是最后一个批次
                time.sleep(self.delay_between_batches)
        
        print(f"\n📊 评论攻击完成！")
        print(f"✅ 成功: {successful_comments} 条")
        print(f"❌ 失败: {failed_comments} 条")
        print(f"📈 成功率: {successful_comments/total_comments*100:.2f}%")

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
                
                # 无间隔连续发送
                # time.sleep(0)  # 完全无延迟
                
        except KeyboardInterrupt:
            print(f"\n🛑 用户中断！总共发送了 {comment_count} 条评论")
        except Exception as e:
            print(f"❌ 持续评论异常: {e}")

    def run(self, mode="continuous", total_comments=1000):
        """运行机器人"""
        print("=" * 50)
        print("🤖 Test Spam Bot - 专注test帖子评论")
        print("=" * 50)
        
        if not self.login():
            return False
        
        if not self.find_test_thread():
            return False
        
        if mode == "continuous":
            self.spam_comments_continuous()
        elif mode == "batch":
            self.spam_comments_concurrent(total_comments)
        else:
            print("❌ 无效模式，使用 continuous 或 batch")

if __name__ == "__main__":
    # 配置论坛地址和账户
    BOT_CONFIG = {
        "base_url": "https://chess.free.mbbs.cc",
        "username": "turkeybot", 
        "password": "passwordbotonly"
    }
    
    # 创建并运行机器人
    bot = TestSpamBot(**BOT_CONFIG)
    
    # 运行模式选择：
    # 1. continuous - 持续不断直到手动停止
    # 2. batch - 指定数量并发评论
    bot.run(mode="continuous")  # 持续模式
    # bot.run(mode="batch", total_comments=500)  # 批量模式，发送500条评论


