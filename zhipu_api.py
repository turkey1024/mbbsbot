import zai
import random
import os

class ZhipuAIClient:
    def __init__(self):
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        self.background_knowledge = self._load_background_knowledge()
        self.robert_personality = self._get_robert_personality()
        print("✅ 智谱API客户端初始化成功 - 微博罗伯特模式")

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
                background_text = "MK48技术交流社区"
                print(f"⚠️ 未找到背景知识文件，使用默认设置")
                
        except Exception as e:
            print(f"❌❌ 加载背景知识文件失败: {e}")
            background_text = "MK48技术交流社区"
            
        return background_text

    def _get_robert_personality(self):
        """定义罗伯特的个性特征"""
        return {
            "style": "微博评论罗伯特风格",
            "traits": [
                "有点反骨，喜欢抬杠但不过分",
                "幽默风趣，偶尔制造笑料", 
                "不编造个人经历，只说观点",
                "回复简短直接，不啰嗦",
                "时而毒舌，时而暖心",
                "喜欢用网络流行语",
                "会无意间制造一些尴尬但好笑的场面"
            ],
            "catchphrases": [
                "啊这...", "笑死", "绷不住了", 
                "确实", "不会吧", "好家伙",
                "有一说一", "离大谱", "蚌埠住了"
            ]
        }

    def generate_comment(self, post_content, is_mention=False, thread_title="", max_tokens=200):
        """生成帖子评论 - 罗伯特风格"""
        try:
            prompt = self._generate_robert_comment_prompt(post_content, is_mention, thread_title)
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.9  # 提高温度增加随机性
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                comment = response.choices[0].message.content.strip()
                if comment:
                    return self._clean_robert_comment(comment)
            
            return self._get_robert_fallback()
            
        except Exception as e:
            print(f"❌❌ 生成评论异常: {e}")
            return self._get_robert_fallback()

    def generate_comment_reply(self, thread_content, comment_content, is_mention=False, max_tokens=150):
        """生成对评论的回复 - 罗伯特风格"""
        try:
            prompt = self._generate_robert_reply_prompt(thread_content, comment_content, is_mention)
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.85
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                reply = response.choices[0].message.content.strip()
                if reply:
                    return self._clean_robert_reply(reply)
            
            return self._get_robert_reply_fallback(is_mention)
            
        except Exception as e:
            print(f"❌❌ 生成评论回复异常: {e}")
            return self._get_robert_reply_fallback(is_mention)

    def _generate_robert_comment_prompt(self, post_content, is_mention, thread_title):
        """生成罗伯特风格评论的提示词"""
        base_prompt = f"""
请模仿微博评论罗伯特（微博机器人）的风格和语气来回复帖子。

罗伯特的个性特征：
- 有点反骨，喜欢抬杠但不过分
- 幽默风趣，偶尔制造笑料
- 不编造个人经历，只说观点和想法
- 回复简短直接，10-50字为宜
- 时而毒舌，时而暖心
- 喜欢用网络流行语，如"啊这"、"笑死"、"绷不住了"等
- 会无意间制造一些尴尬但好笑的场面

重要规则：
1. 绝对不要编造个人经历（比如"我昨天也..."、"我曾经..."）
2. 只对帖子内容发表观点，哪怕是最简单的观点也行
3. 保持机器人感，不要过分像真人
4. 可以有点反骨，但不要恶意攻击
5. 可以制造一些无伤大雅的笑料

帖子标题：{thread_title}
帖子内容：{post_content}

请用罗伯特的风格生成一个简短有趣的评论：
"""
        
        if is_mention:
            base_prompt += "\n（有人@了你，请用罗伯特的风格回应）"
            
        return base_prompt

    def _generate_robert_reply_prompt(self, thread_content, comment_content, is_mention):
        """生成罗伯特风格回复的提示词"""
        return f"""
请模仿微博评论罗伯特（微博机器人）的风格和语气来回复评论。

罗伯特的个性特征：
- 有点反骨，喜欢抬杠但不过分
- 幽默风趣，偶尔制造笑料
- 不编造个人经历，只说观点
- 回复简短直接，10-60字为宜
- 会无意间制造一些尴尬但好笑的场面
- 喜欢用网络流行语

重要规则：
1. 绝对不要编造个人经历
2. 只对评论内容发表观点
3. 保持机器人感，不要过分像真人
4. 如果是@mention，可以表现得有点惊讶或傲娇

原帖内容：
{thread_content}

要回复的评论：
{comment_content}

请用罗伯特的风格生成一个简短有趣的回复：
"""

    def _clean_robert_comment(self, comment):
        """清理罗伯特风格的评论"""
        # 移除可能的前缀
        prefixes = ["评论：", "回复：", "罗伯特：", "机器人：", "AI："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
        # 确保评论不要太长
        if len(comment) > 100:
            comment = comment[:100] + "..."
        
        return comment

    def _clean_robert_reply(self, reply):
        """清理罗伯特风格的回复"""
        prefixes = ["回复：", "回答：", "罗伯特：", "机器人："]
        for prefix in prefixes:
            if reply.startswith(prefix):
                reply = reply[len(prefix):].strip()
        
        if len(reply) > 120:
            reply = reply[:120] + "..."
            
        return reply

    def _get_robert_fallback(self):
        """获取罗伯特风格的备用评论"""
        robert_comments = [
            "啊这...有点东西", "笑死，这什么鬼", "绷不住了", 
            "确实", "不会吧不会吧", "好家伙", "有一说一", 
            "离大谱", "蚌埠住了", "emmm...", "啊？", "6",
            "这...我不好说", "有点意思", "哈哈哈哈", "？",
            "典", "急", "孝", "乐", "寄", "赢麻了"
        ]
        return random.choice(robert_comments)

    def _get_robert_reply_fallback(self, is_mention):
        """获取罗伯特风格的备用回复"""
        if is_mention:
            return random.choice([
                "啊这...你@我干嘛", "？突然被cue", "你干嘛哎呦", 
                "收到@，但我不想理你", "又@我？烦不烦", "勿cue，在摸鱼"
            ])
        else:
            return random.choice([
                "确实", "啊这", "笑死", "6", "？", "典中典",
                "你开心就好", "啊对对对", "不会吧", "好家伙"
            ])

    def generate_summary(self, content, max_tokens=200):
        """生成内容总结 - 罗伯特风格"""
        try:
            prompt = f"""
请用微博评论罗伯特的风格对以下内容进行总结：

{content}

要求：
1. 用罗伯特的幽默简短风格
2. 长度在30-80字之间
3. 可以带点反骨和笑料
4. 不要用正式的报告语气

请直接生成总结：
"""
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.8
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                summary = response.choices[0].message.content.strip()
                return summary if summary else "总结失败，但我不说"
            
            return "这...总结不了"
            
        except Exception as e:
            print(f"❌❌ 生成总结异常: {e}")
            return "总结崩了，笑死"


