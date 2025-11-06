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
        self.target_categories = [2]  # 要监控的板块ID，可以配置多个
        self.max_threads_to_check = 15  # 每次检查的最新帖子数量
        self.comment_interval = 1800  # 30分钟（秒）
        self.min_post_length = 20  # 帖子内容最小长度
        
        # 记录已评论的帖子ID和评论ID，避免重复
        self.commented_threads = set()
        self.replied_comments = set()
        
        # 从文件加载已评论记录（持久化）
        self.load_commented_history()
    
    def load_commented_history(self):
        """从文件加载已评论历史记录"""
        try:
            if os.path.exists("commented_history.txt"):
                with open("commented_history.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("THREAD:"):
                            self.commented_threads.add(line[7:])
                        elif line.startswith("COMMENT:"):
                            self.replied_comments.add(line[8:])
                print(f"✅ 加载历史记录: {len(self.commented_threads)} 个帖子, {len(self.replied_comments)} 条评论")
        except Exception as e:
            print(f"❌ 加载历史记录失败: {e}")
    
    def save_commented_history(self):
        """保存已评论历史记录到文件"""
        try:
            with open("commented_history.txt", "w", encoding="utf-8") as f:
                for thread_id in self.commented_threads:
                    f.write(f"THREAD:{thread_id}\n")
                for comment_id in self.replied_comments:
                    f.write(f"COMMENT:{comment_id}\n")
            print("✅ 历史记录已保存")
        except Exception as e:
            print(f"❌ 保存历史记录失败: {e}")
    
    def login(self):
        """登录论坛"""
        print("🔐🔐 正在登录论坛...")
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
            print("❌ 登录失败")
            return False
    
    def should_comment(self, thread):
        """判断是否应该评论这个帖子"""
        thread_id = str(thread.get('id'))
        
        # 跳过自己发的帖子
        if thread.get('user_id') == self.user_id:
            print("   ⏭️ 跳过自己的帖子")
            return False
        
        # 跳过已经评论过的帖子
        if thread_id in self.commented_threads:
            print("   ⏭️ 已经评论过此帖子")
            return False
        
        # 跳过标题包含特定关键词的帖子
        title = thread.get('title', '').lower()
        skip_keywords = ['自动推送', '测试', '公告']
        for keyword in skip_keywords:
            if keyword in title:
                print(f"   ⏭️ 跳过包含'{keyword}'的帖子")
                return False
        
        # 检查帖子内容长度
        content = thread.get('content', '') or thread.get('content_for_indexes', '')
        if len(content) < self.min_post_length:
            print(f"   ⏭️ 帖子内容过短 ({len(content)} 字符)")
            return False
            
        return True
    
    def check_and_handle_mentions(self, poster, thread, comments):
        """检查并处理提及"""
        thread_id = str(thread.get('id'))
        thread_content = thread.get('content', '') or thread.get('content_for_indexes', '') or thread.get('title', '')
        
        # 检查帖子内容中是否有提及
        has_mention, keyword = poster.check_mentions(thread_content)
        if has_mention:
            print(f"   🔔 帖子内容中检测到提及: {keyword}")
            
            # 生成有针对性的回复
            ai_comment = self.zhipu_client.generate_comment(
                thread_content, 
                is_mention=True, 
                mention_content=f"帖子中提到了 {keyword}"
            )
            
            if ai_comment:
                success = poster.create_comment(self.token, thread_id, ai_comment)
                if success:
                    self.commented_threads.add(thread_id)
                    print(f"   🎉 针对提及的评论发布成功！")
                    return True
            return False
        
        # 检查评论中是否有提及
        for comment in comments:
            comment_id = str(comment.get('id'))
            comment_content = comment.get('content', '')
            
            # 跳过已经回复过的评论
            if comment_id in self.replied_comments:
                continue
                
            has_mention, keyword = poster.check_mentions(comment_content)
            if has_mention:
                print(f"   🔔 评论中检测到提及: {keyword} (评论ID: {comment_id})")
                
                # 生成有针对性的回复
                ai_reply = self.zhipu_client.generate_comment(
                    thread_content,
                    is_mention=True,
                    mention_content=f"评论中提到了 {keyword}，评论内容: {comment_content[:100]}"
                )
                
                if ai_reply:
                    # 回复这条评论
                    success = poster.create_comment_reply(self.token, comment_id, ai_reply)
                    if success:
                        self.replied_comments.add(comment_id)
                        print(f"   🎉 评论回复发布成功！")
                        return True
                break  # 只回复第一个提及的评论
        
        return False
    
    def process_threads(self):
        """处理帖子并自动评论"""
        if not self.session or not self.token:
            print("❌ 未登录，无法处理帖子")
            return False
        
        poster = BBSPoster(self.session, self.base_url)
        commented_count = 0
        checked_count = 0
        mention_handled = 0
        
        for category_id in self.target_categories:
            print(f"📋📋 检查板块 {category_id} 的帖子...")
            
            # 获取最新帖子
            threads = poster.get_threads(self.token, category_id, self.max_threads_to_check)
            
            for thread in threads:
                checked_count += 1
                thread_id = str(thread.get('id'))
                thread_title = thread.get('title', '')
                
                print(f"\n📄 检查帖子 [{checked_count}/{len(threads)}]: {thread_title} (ID: {thread_id})")
                
                # 判断是否应该评论
                if not self.should_comment(thread):
                    continue
                
                # 获取帖子的评论
                comments = poster.get_post_comments(self.token, thread_id)
                
                # 检查是否已经评论过（通过API检查）
                if poster.has_commented(comments, self.user_id):
                    print("   ✅ 已评论过，跳过")
                    self.commented_threads.add(thread_id)  # 添加到已评论记录
                    continue
                
                # 优先处理提及
                if self.check_and_handle_mentions(poster, thread, comments):
                    mention_handled += 1
                    commented_count += 1
                    continue
                
                print("   💬 需要评论此帖子")
                
                # 获取帖子内容
                thread_content = thread.get('content', '') or thread.get('content_for_indexes', '') or thread_title
                
                # 如果内容过短，添加更多上下文
                if len(thread_content) < 50:
                    thread_content = f"帖子标题: {thread_title}\n帖子内容: {thread_content}"
                
                # 使用智谱API生成评论
                try:
                    ai_comment = self.zhipu_client.generate_comment(thread_content)
                    if ai_comment:
                        # 发布评论
                        success = poster.create_comment(self.token, thread_id, ai_comment)
                        if success:
                            commented_count += 1
                            self.commented_threads.add(thread_id)
                            print(f"   🎉 评论发布成功！")
                        else:
                            print("   ❌ 评论发布失败")
                    
                    # 避免频繁调用API，添加延迟
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"   ❌ 处理帖子时出错: {e}")
                    continue
        
        # 保存历史记录
        self.save_commented_history()
        
        print(f"\n📊 本次运行检查了 {checked_count} 个帖子")
        print(f"📝 成功评论了 {commented_count} 个帖子")
        print(f"🔔 处理了 {mention_handled} 个提及")
        
        return commented_count > 0 or mention_handled > 0
    
    def run(self, continuous=False):
        """运行自动评论机器人"""
        print("=" * 60)
        print("🤖🤖 MBBS TurkeyBot 自动评论机器人")
        print(f"🔧 使用模型: GLM-4.5-Flash")
        print("=" * 60)
        
        if not self.login():
            return False
        
        if continuous:
            print("🔄 连续运行模式，每30分钟执行一次")
            while True:
                print(f"\n⏰ 开始执行于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.process_threads()
                print(f"💤 等待 {self.comment_interval} 秒后再次执行...")
                time.sleep(self.comment_interval)
        else:
            print("🚀 单次执行模式")
            success = self.process_threads()
            return success

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
    print("📊📊 执行结果")
    print("=" * 60)
    print(f"✅ 状态: {'成功' if success else '完成（可能没有需要评论的帖子）'}")
    
    

