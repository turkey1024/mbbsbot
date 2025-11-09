from login import BBSTurkeyBotLogin
from post import BBSPoster
from zhipu_api import ZhipuAIClient
import time
from datetime import datetime
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
        
        # 记录置顶帖子
        self.pinned_threads = set()
        
        # 加载敏感词列表
        self.sensitive_words = self._load_text_list("mgc.txt", "敏感词")
        
        # 加载黑名单用户
        self.blacklist_users = self._load_text_list("hmd.txt", "黑名单用户")

    def _load_text_list(self, filename, description):
        """通用方法：加载文本文件中的列表"""
        items = set()
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    items = {line.strip() for line in f if line.strip() and not line.startswith('#')}
                print(f"✅ 成功加载{description}文件: {filename}, 共 {len(items)} 个")
            else:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"# {description}列表\n")
                    f.write("# 每行一个项目\n")
                print(f"✅ 创建默认{description}文件: {filename}")
        except Exception as e:
            print(f"❌ 加载{description}文件失败: {e}")
        return items

    def login(self):
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

    def should_comment(self, thread):
        thread_user_id = str(thread.get('user_id', ''))
        
        # 跳过自己的帖子
        if thread_user_id == str(self.user_id):
            print("   ⏭ 跳过自己的帖子")
            return False
            
        # 跳过黑名单用户
        if thread_user_id in self.blacklist_users:
            print(f"   🚫 跳过黑名单用户 {thread_user_id} 的帖子")
            return False
            
        # 跳过置顶帖子
        if thread.get('is_pinned', False) or thread.get('id') in self.pinned_threads:
            print("   📌 跳过置顶帖子")
            self.pinned_threads.add(thread.get('id'))
            return False
            
        title = thread.get('title', '')
        content = thread.get('content', '') or thread.get('content_for_indexes', '') or ''
        
        # 检查敏感词
        if self._contains_sensitive(title) or self._contains_sensitive(content):
            print("   🚫 帖子包含敏感词，跳过")
            return False
            
        # 跳过特定关键词的帖子
        title_lower = title.lower()
        skip_keywords = ['自动推送', '测试', '公告', 'turkeybot']
        if any(keyword in title_lower for keyword in skip_keywords):
            print(f"   ⏭ 跳过包含关键词的帖子")
            return False
            
        return True

    def _contains_sensitive(self, content):
        """检查内容是否包含敏感词"""
        if not content or not self.sensitive_words:
            return False
        content_lower = content.lower()
        return any(word.lower() in content_lower for word in self.sensitive_words)

    def has_bot_commented(self, thread_id):
        try:
            poster = BBSPoster(self.session, self.base_url)
            comments = poster.get_post_comments(self.token, thread_id)
            return any(comment.get('user_id') == self.user_id for comment in comments)
        except Exception as e:
            print(f"   ❌ 检查评论状态失败: {e}")
            return True

    def contains_mention(self, content):
        if not content:
            return False
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self.bot_keywords)

    def process_threads(self):
        if not self.session or not self.token:
            print("❌ 未登录，无法处理帖子")
            return False
        
        poster = BBSPoster(self.session, self.base_url)
        commented_count = 0
        mention_count = 0
        skipped_count = 0
        
        for category_id in self.target_categories:
            print(f"📋 检查板块 {category_id} 的帖子...")
            threads = poster.get_threads(self.token, category_id, self.max_threads_to_check)
            
            for thread in threads:
                thread_id = thread.get('id')
                thread_title = thread.get('title', '')
                thread_content = thread.get('content', '') or thread.get('content_for_indexes', '') or ''
                
                print(f"\n📄 检查帖子: {thread_title} (ID: {thread_id})")
                
                if not self.should_comment(thread):
                    skipped_count += 1
                    continue
                
                if self.has_bot_commented(thread_id):
                    print("   ✅ 已评论过，跳过")
                    continue
                
                is_mention = self.contains_mention(thread_title) or self.contains_mention(thread_content)
                
                if is_mention:
                    mention_count += 1
                    print("   🔔 检测到@mention")

                print("   💬 需要评论此帖子")
                
                try:
                    full_content = f"标题：{thread_title}\n内容：{thread_content}"
                    
                    if self._contains_sensitive(full_content):
                        print("   🚫 评论内容可能包含敏感词，跳过")
                        continue
                    
                    ai_comment = self.zhipu_client.generate_comment(
                        full_content, 
                        is_mention=is_mention,
                        thread_title=thread_title
                    )
                    
                    if ai_comment and not self._contains_sensitive(ai_comment):
                        success = poster.create_comment(self.token, thread_id, ai_comment)
                        if success:
                            commented_count += 1
                            print(f"   🎉 评论发布成功！")
                            if is_mention:
                                time.sleep(5)
                        else:
                            print("   ❌ 评论发布失败")
                    else:
                        print("   ❌ AI评论生成失败或包含敏感词")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"   ❌ 处理帖子时出错: {e}")
                    continue
        
        print(f"\n📊 本次运行统计:")
        print(f"📊 检查了 {len(threads)} 个帖子")
        print(f"📊 跳过了 {skipped_count} 个帖子")
        print(f"📊 检测到 {mention_count} 个@mention请求")
        print(f"📊 成功评论了 {commented_count} 个帖子")
        return commented_count > 0

    def run(self, continuous=False):
        print("=" * 40)
        print("🤖 MBBS TurkeyBot 自动评论机器人")
        print("=" * 40)
        
        if not self.login():
            return False
        
        if continuous:
            print("🔄 连续运行模式")
            while True:
                print(f"\n⏰ 开始执行于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.process_threads()
                print(f"💤 等待 {self.comment_interval} 秒后再次执行...")
                time.sleep(self.comment_interval)
        else:
            print("🚀 单次执行模式")
            return self.process_threads()

if __name__ == "__main__":
    bot = AutoCommentBot("https://mk48by049.mbbs.cc", "turkeybot", "passwordbotonly")
    bot.run(continuous=False)


