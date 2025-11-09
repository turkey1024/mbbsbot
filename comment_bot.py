from login import BBSTurkeyBotLogin
from post import BBSPoster
from zhipu_api import ZhipuAIClient
import time
from datetime import datetime
import re
import os

class AutoCommentBot:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.zhipu_client = ZhipuAIClient()
        
        self.session = None
        self.token = None
        self.user_id = None
        
        self.target_categories = [2]
        self.max_threads_to_check = 50
        self.comment_interval = 1800
        self.bot_keywords = ['turkeybot', 'bot', '机器人', '论坛机器人']
        
        # 新增：记录置顶帖子
        self.pinned_threads = set()
        
        # 新增：加载敏感词列表
        self.sensitive_words = self._load_sensitive_words()

    def _load_sensitive_words(self):
        """加载敏感词列表"""
        sensitive_file = "mgc.txt"
        sensitive_words = []
        
        try:
            if os.path.exists(sensitive_file):
                with open(sensitive_file, 'r', encoding='utf-8') as f:
                    # 读取所有行，去除空行和空白字符
                    sensitive_words = [line.strip() for line in f.readlines() if line.strip()]
                print(f"✅ 成功加载敏感词文件: {sensitive_file}, 共 {len(sensitive_words)} 个敏感词")
            else:
                print(f"⚠️ 未找到敏感词文件: {sensitive_file}，使用空列表")
                
        except Exception as e:
            print(f"❌ 加载敏感词文件失败: {e}")
            sensitive_words = []
            
        return sensitive_words

    def contains_sensitive_words(self, content):
        """检查内容是否包含敏感词"""
        if not content or not self.sensitive_words:
            return False
            
        content_lower = content.lower()
        for word in self.sensitive_words:
            if word and word.lower() in content_lower:
                return True
        return False

    def login(self):
        print("🔐🔐🔐🔐 正在登录论坛...")
        login_bot = BBSTurkeyBotLogin(self.base_url, self.username, self.password)
        login_success, login_result, session = login_bot.login_with_retry()
        
        if login_success:
            self.session = session
            self.token = login_result.get('data', {}).get('token')
            self.user_id = login_result.get('data', {}).get('id')
            print(f"✅ 登录成功！用户ID: {self.user_id}")
            return True
        else:
            print("❌❌❌❌ 登录失败")
            return False

    def should_comment(self, thread):
        if thread.get('user_id') == self.user_id:
            print("   ⏭⏭⏭⏭⏭⏭⏭⏭⏭ 跳过自己的帖子")
            return False
        
        # 新增：检查是否是置顶帖子
        if thread.get('is_pinned', False) or thread.get('id') in self.pinned_threads:
            print("   📌📌📌📌 跳过置顶帖子")
            self.pinned_threads.add(thread.get('id'))
            return False
            
        title = thread.get('title', '')
        content = thread.get('content', '') or thread.get('content_for_indexes', '') or ''
        
        # 新增：检查是否包含敏感词
        if self.contains_sensitive_words(title):
            print("   🚫🚫🚫🚫 帖子标题包含敏感词，跳过")
            return False
            
        if self.contains_sensitive_words(content):
            print("   🚫🚫🚫🚫 帖子内容包含敏感词，跳过")
            return False
            
        title_lower = title.lower()
        skip_keywords = ['自动推送', '测试', '公告', 'turkeybot']
        for keyword in skip_keywords:
            if keyword in title_lower:
                print(f"   ⏭⏭⏭⏭⏭⏭⏭⏭⏭ 跳过包含'{keyword}'的帖子")
                return False
        return True

    def has_bot_commented(self, thread_id):
        try:
            poster = BBSPoster(self.session, self.base_url)
            comments = poster.get_post_comments(self.token, thread_id)
            return any(comment.get('user_id') == self.user_id for comment in comments)
        except Exception as e:
            print(f"   ❌❌❌❌ 检查评论状态失败: {e}")
            return True

    def contains_mention(self, content):
        if not content:
            return False
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.bot_keywords)

    def process_threads(self):
        if not self.session or not self.token:
            print("❌❌❌❌ 未登录，无法处理帖子")
            return False
        
        poster = BBSPoster(self.session, self.base_url)
        commented_count = 0
        mention_count = 0
        skipped_sensitive_count = 0  # 新增：统计跳过的敏感帖子数量
        
        for category_id in self.target_categories:
            print(f"📋📋📋📋 检查板块 {category_id} 的帖子...")
            threads = poster.get_threads(self.token, category_id, self.max_threads_to_check)
            
            for thread in threads:
                thread_id = thread.get('id')
                thread_title = thread.get('title', '')
                thread_content = thread.get('content', '') or thread.get('content_for_indexes', '') or ''
                
                print(f"\n📄📄📄📄 检查帖子: {thread_title} (ID: {thread_id})")
                
                # 先检查是否应该评论（包含敏感词检查）
                if not self.should_comment(thread):
                    if (self.contains_sensitive_words(thread_title) or 
                        self.contains_sensitive_words(thread_content)):
                        skipped_sensitive_count += 1
                    continue
                
                if self.has_bot_commented(thread_id):
                    print("   ✅ 已评论过，跳过")
                    continue
                
                is_mention = self.contains_mention(thread_title) or self.contains_mention(thread_content)
                
                if is_mention:
                    mention_count += 1
                    print("   🔔🔔🔔🔔 检测到@mention")

                print("   💬💬💬💬 需要评论此帖子")
                
                try:
                    full_content = f"标题：{thread_title}\n内容：{thread_content}"
                    
                    # 再次检查生成的评论内容是否包含敏感词（额外安全措施）
                    if self.contains_sensitive_words(full_content):
                        print("   🚫🚫🚫🚫 评论内容可能包含敏感词，跳过评论")
                        continue
                    
                    ai_comment = self.zhipu_client.generate_comment(
                        full_content, 
                        is_mention=is_mention,
                        thread_title=thread_title
                    )
                    
                    if ai_comment:
                        # 最终检查AI生成的评论是否包含敏感词
                        if self.contains_sensitive_words(ai_comment):
                            print("   🚫🚫🚫🚫 AI生成的评论包含敏感词，跳过发布")
                            continue
                            
                        success = poster.create_comment(self.token, thread_id, ai_comment)
                        if success:
                            commented_count += 1
                            print(f"   🎉🎉🎉🎉🎉🎉🎉 评论发布成功！")
                            if is_mention:
                                time.sleep(5)
                        else:
                            print("   ❌❌❌❌ 评论发布失败")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"   ❌❌❌❌ 处理帖子时出错: {e}")
                    continue
        
        print(f"\n📊📊📊📊 本次运行统计:")
        print(f"📊📊📊📊 检查了 {len(threads)} 个帖子")
        print(f"📊📊📊📊 跳过了 {skipped_sensitive_count} 个包含敏感词的帖子")
        print(f"📊📊📊📊 检测到 {mention_count} 个@mention请求")
        print(f"📊📊📊📊 成功评论了 {commented_count} 个帖子")
        return commented_count > 0

    def run(self, continuous=False):
        print("=" * 40)
        print("🤖🤖🤖🤖 MBBS TurkeyBot 自动评论机器人")
        print("=" * 40)
        
        if not self.login():
            return False
        
        if continuous:
            print("🔄🔄🔄🔄 连续运行模式")
            while True:
                print(f"\n⏰⏰⏰⏰⏰⏰⏰⏰⏰ 开始执行于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.process_threads()
                print(f"💤💤💤💤 等待 {self.comment_interval} 秒后再次执行...")
                time.sleep(self.comment_interval)
        else:
            print("🚀🚀🚀🚀 单次执行模式")
            return self.process_threads()

    def update_sensitive_words(self, new_words_list):
        """动态更新敏感词列表"""
        if isinstance(new_words_list, list):
            self.sensitive_words = [word.strip() for word in new_words_list if word.strip()]
            print(f"✅ 敏感词列表已更新，共 {len(self.sensitive_words)} 个敏感词")
            return True
        return False

    def get_sensitive_words_count(self):
        """获取当前敏感词数量"""
        return len(self.sensitive_words)

if __name__ == "__main__":
    bot = AutoCommentBot("https://mk48by049.mbbs.cc", "turkeybot", "passwordbotonly")
    bot.run(continuous=False)


