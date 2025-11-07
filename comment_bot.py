from login import BBSTurkeyBotLogin
from post import BBSPoster
from zhipu_api import ZhipuAIClient
import time
from datetime import datetime
import os
import re

class AutoCommentBot:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.zhipu_client = ZhipuAIClient()
        
        # 登录相关
        self.session = None
        self.token = None
        self.user_id = None
        
        # 配置
        self.target_categories = [2]  # 要监控的板块ID
        self.max_threads_to_check = 15  # 每次检查的最新帖子数量
        self.comment_interval = 1800  # 30分钟
        self.bot_keywords = ['turkeybot', 'bot', '机器人', '论坛机器人', '@turkeybot', '@bot', '@机器人', '@论坛机器人']
        
        # 记录已评论的帖子（避免重复评论）
        self.commented_threads = set()
    
    def login(self):
        """登录论坛"""
        print("🔐🔐🔐🔐 正在登录论坛...")
        login_bot = BBSTurkeyBotLogin(self.base_url, self.username, self.password)
        login_success, login_result, session = login_bot.login_with_retry()
        
        if login_success:
            self.session = session
            user_data = login_result.get('data', {})
            self.token = user_data.get('token')
            self.user_id = user_data.get('id')
            print(f"✅ 登录成功！用户ID: {self.user_id}")
            return True
        else:
            print("❌❌ 登录失败")
            return False
    
    def should_comment(self, thread):
        """判断是否应该评论这个帖子"""
        # 跳过自己发的帖子
        if thread.get('user_id') == self.user_id:
            print("   ⏭⏭⏭️ 跳过自己的帖子")
            return False
        
        # 跳过标题包含特定关键词的帖子
        title = thread.get('title', '').lower()
        skip_keywords = ['自动推送', '测试', '公告', 'turkeybot']
        for keyword in skip_keywords:
            if keyword in title:
                print(f"   ⏭⏭⏭️ 跳过包含'{keyword}'的帖子")
                return False
        
        # 检查是否已经评论过（通过API检查当前帖子下的评论）
        return True
    
    def has_bot_commented(self, thread_id):
        """检查该帖子下是否有bot的评论"""
        try:
            poster = BBSPoster(self.session, self.base_url)
            comments = poster.get_post_comments(self.token, thread_id)
            
            for comment in comments:
                if comment.get('user_id') == self.user_id:
                    print(f"   ✅ 检测到已在该帖子评论过")
                    return True
            return False
        except Exception as e:
            print(f"   ❌❌ 检查评论状态失败: {e}")
            return False
    
    def contains_mention(self, content):
        """检查内容是否包含@mention"""
        if not content:
            return False
        
        content_lower = content.lower()
        for keyword in self.bot_keywords:
            if keyword in content_lower:
                return True
        return False
    
    def process_threads(self):
        """处理帖子并自动评论"""
        if not self.session or not self.token:
            print("❌❌ 未登录，无法处理帖子")
            return False
        
        poster = BBSPoster(self.session, self.base_url)
        commented_count = 0
        checked_count = 0
        mention_count = 0
        
        for category_id in self.target_categories:
            print(f"📋📋📋📋 检查板块 {category_id} 的帖子...")
            
            # 获取最新帖子
            threads = poster.get_threads(self.token, category_id, self.max_threads_to_check)
            
            for thread in threads:
                checked_count += 1
                thread_id = thread.get('id')
                thread_title = thread.get('title', '')
                thread_content = thread.get('content', '') or thread.get('content_for_indexes', '') or ''
                
                print(f"\n📄📄 检查帖子 [{checked_count}/{len(threads)}]: {thread_title} (ID: {thread_id})")
                
                # 判断是否应该评论
                if not self.should_comment(thread):
                    continue
                
                # 检查是否已经评论过（通过API实时检查）
                if self.has_bot_commented(thread_id):
                    print("   ✅ 已评论过，跳过")
                    continue
                
                # 检查是否是@mention
                is_mention = False
                if self.contains_mention(thread_title) or self.contains_mention(thread_content):
                    is_mention = True
                    mention_count += 1
                    print("   🔔🔔 检测到@mention，优先处理")
                
                print("   💬💬 需要评论此帖子")
                
                # 使用智谱API生成评论
                try:
                    # 组合标题和内容
                    full_content = f"标题：{thread_title}\n内容：{thread_content}"
                    
                    # 根据是否是mention使用不同的提示词
                    ai_comment = self.zhipu_client.generate_comment(
                        full_content, 
                        is_mention=is_mention,
                        thread_title=thread_title
                    )
                    
                    if ai_comment:
                        # 发布评论
                        success = poster.create_comment(self.token, thread_id, ai_comment)
                        if success:
                            commented_count += 1
                            self.commented_threads.add(thread_id)
                            print(f"   🎉🎉🎉 评论发布成功！")
                            
                            # 如果是mention，添加额外延迟
                            if is_mention:
                                time.sleep(5)
                        else:
                            print("   ❌❌ 评论发布失败")
                    
                    # 避免频繁调用API，添加延迟
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"   ❌❌ 处理帖子时出错: {e}")
                    continue
        
        print(f"\n📊📊 本次运行检查了 {checked_count} 个帖子")
        print(f"📊📊 检测到 {mention_count} 个@mention请求")
        print(f"📊📊 成功评论了 {commented_count} 个帖子")
        return commented_count > 0
    
    def run(self, continuous=False):
        """运行自动评论机器人"""
        print("=" * 60)
        print("🤖🤖🤖🤖 MBBS TurkeyBot 自动评论机器人")
        print(f"🔧🔧 使用模型: GLM-4.5-Flash")
        print("🔧🔧 支持@mention关键词:", ", ".join(self.bot_keywords))
        print("=" * 60)
        
        if not self.login():
            return False
        
        if continuous:
            print("🔄🔄 连续运行模式，每30分钟执行一次")
            while True:
                print(f"\n⏰⏰⏰ 开始执行于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.process_threads()
                print(f"💤💤 等待 {self.comment_interval} 秒后再次执行...")
                time.sleep(self.comment_interval)
        else:
            print("🚀🚀 单次执行模式")
            return self.process_threads()

def main():
    # 配置
    base_url = "https://mk48by049.mbbs.cc"
    username = "turkeybot"
    password = "passwordbotonly"
    
    # 创建机器人实例
    bot = AutoCommentBot(base_url, username, password)
    
    # 运行机器人（单次模式）
    success = bot.run(continuous=False)
    
    print("\n" + "=" * 60)
    print("📊📊📊📊 执行结果")
    print("=" * 60)
    print(f"✅ 状态: {'成功' if success else '完成（可能没有需要评论的帖子）'}")
    
    return success

if __name__ == "__main__":
    main()


