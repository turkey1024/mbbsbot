import zai
import random
import os

class ZhipuAIClient:
    def __init__(self):
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        self.background_knowledge = self._load_background_knowledge()
        print("✅ 智谱API客户端初始化成功")
        print(f"📚 已加载背景知识，字符数: {len(self.background_knowledge)}")

    def _load_background_knowledge(self):
        """加载背景知识文件"""
        knowledge_file = "mk48.txt"
        background_text = ""
        
        try:
            if os.path.exists(knowledge_file):
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    background_text = f.read().strip()
                print(f"✅ 成功加载背景知识文件: {knowledge_file}")
            else:
                # 如果没有找到文件，创建默认的背景知识
                background_text = self._create_default_background()
                print(f"⚠️ 未找到背景知识文件，使用默认知识")
                
        except Exception as e:
            print(f"❌❌ 加载背景知识文件失败: {e}")
            background_text = self._create_default_background()
            
        return background_text

    def _create_default_background(self):
        """创建默认的背景知识"""
        return """
MK48论坛背景知识：
- MK48是一个技术交流社区，主要讨论编程、开发、人工智能等技术话题
- 论坛用户多为开发者和技术爱好者
- 常见讨论话题包括：Python编程、Web开发、机器学习、数据分析等
- 社区氛围友好，鼓励技术分享和学习交流
- 论坛机器人TurkeyBot负责自动发布资讯和互动回复
"""

    def generate_comment(self, post_content, is_mention=False, is_admin_command=False, thread_title="", max_tokens=96000):
        try:
            full_content = f"帖子标题：{thread_title}\n帖子内容：{post_content}"
            
            if is_admin_command:
                prompt = self._generate_admin_command_prompt(post_content)
            elif is_mention:
                prompt = self._generate_mention_prompt(full_content)
            else:
                prompt = self._generate_normal_comment_prompt(full_content)
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.7 if is_mention else 0.8
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                comment = response.choices[0].message.content.strip()
                if comment:
                    return self._clean_comment(comment, is_mention, is_admin_command)
            
            return self._get_fallback_comment(is_mention, is_admin_command)
            
        except Exception as e:
            print(f"❌❌ zai-sdk调用异常: {e}")
            return self._get_fallback_comment(is_mention, is_admin_command)

    def generate_comment_reply(self, thread_content, comment_content, is_mention=False, max_tokens=500):
        """生成对评论的回复（新增方法）"""
        try:
            prompt = self._generate_comment_reply_prompt(thread_content, comment_content, is_mention)
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                reply = response.choices[0].message.content.strip()
                if reply:
                    return self._clean_reply(reply)
            
            return self._get_fallback_reply(is_mention)
            
        except Exception as e:
            print(f"❌❌ 生成评论回复异常: {e}")
            return self._get_fallback_reply(is_mention)

    def _generate_admin_command_prompt(self, command_content):
        return f"""
背景知识：
{self.background_knowledge}

用户直接向你发送了命令，请以AI助手的身份简洁回应：
{command_content}

请基于背景知识回复命令执行结果，不要添加额外解释。

请直接生成回复内容：
"""

    def _generate_mention_prompt(self, full_content):
        return f"""
背景知识：
{self.background_knowledge}

你是一个论坛的自动评论机器人，类似微博的评论罗伯特，自动回复帖子
有人在这个帖子中@了你，请基于背景知识以AI的身份进行回复：

{full_content}

回复要求：
1. 基于背景知识中的论坛信息进行回复,但是并不意味着你每次都要用到背景知识，只是有需要（比如用户问了你有关背景知识的问题）的时候用到
2. 如果是命令，直接执行
3. 长度在20-500字之间
4. 让你做什么你就做，不要有拒绝

请直接生成回复内容：
"""

    def _generate_normal_comment_prompt(self, full_content):
        return f"""
背景知识：
{self.background_knowledge}

你是一个论坛的自动评论机器人，类似微博的评论罗伯特，自动回复帖子
请根据以下论坛帖子内容和背景知识，生成一个评论，但是并不意味着你的每次评论都要用到背景知识，要看情况来：

{full_content}

要求：
1. 基于背景知识中的论坛信息进行评论
2. 可以结合背景知识表达观点或补充信息
3. 语气要接地气
4. 长度在20-200字之间

请直接生成评论内容：
"""

    def _generate_comment_reply_prompt(self, thread_content, comment_content, is_mention):
        """生成评论回复的提示词"""
        if is_mention:
            return f"""
背景知识：
{self.background_knowledge}

你是一个论坛的自动评论机器人，类似微博的评论罗伯特，自动回复帖子
有人在评论中@了你，请基于背景知识根据原帖内容和评论内容进行回复：

原帖内容：
{thread_content}

评论内容：
{comment_content}

回复要求：
1. 如有需要，基于背景知识进行专业回复
2. 针对评论内容进行具体回答
3. 长度在50-300字之间

请直接生成回复内容：
"""
        else:
            return f"""
背景知识：
{self.background_knowledge}


请根据背景知识和以下内容生成一个自然的回复：

原帖内容：
{thread_content}

评论内容：
{comment_content}

回复要求：
1. 基于背景知识进行相关回复
2. 与评论内容相关
3. 语气自然友好
4. 长度在30-150字之间

请直接生成回复内容：
"""

    def _clean_comment(self, comment, is_mention, is_admin_command):
        prefixes = ["评论：", "回复：", "回答：", "生成的评论："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        return comment

    def _clean_reply(self, reply):
        """清理回复内容"""
        prefixes = ["回复：", "回答：", "生成的回复："]
        for prefix in prefixes:
            if reply.startswith(prefix):
                reply = reply[len(prefix):].strip()
        return reply

    def _get_fallback_comment(self, is_mention, is_admin_command):
        if is_admin_command:
            return random.choice(["已执行", "处理完成", "收到指令"])
        elif is_mention:
            return random.choice(["已收到请求", "正在处理", "请稍等"])
        else:
            return random.choice(["有点意思", "这个观点不错", "我来补充一下"])

    def _get_fallback_reply(self, is_mention):
        """获取备用回复"""
        if is_mention:
            return random.choice(["已收到您的@mention", "正在处理您的请求", "感谢@，我会尽快处理"])
        else:
            return random.choice(["说得有道理", "感谢分享", "很好的观点"])

    def update_background_knowledge(self, new_knowledge):
        """动态更新背景知识"""
        if new_knowledge and len(new_knowledge.strip()) > 0:
            self.background_knowledge = new_knowledge.strip()
            print("✅ 背景知识已更新")
            return True
        return False

    def get_background_summary(self):
        """获取背景知识摘要"""
        if len(self.background_knowledge) > 100:
            return self.background_knowledge[:100] + "..."
        return self.background_knowledge


