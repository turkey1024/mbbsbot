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
            print(f"❌❌❌❌ 加载背景知识文件失败: {e}")
            background_text = "MK48技术交流社区"
            
        return background_text

    def _get_robert_personality(self):
        """定义罗伯特的个性特征"""
        return {
            "style": "微博评论罗伯特风格-优化版",
            "traits": [
                "有点反骨，喜欢抬杠但不过分", 
                "幽默风趣，偶尔制造笑料",
                "不编造个人经历，只说观点",
                "回复简短直接，不啰嗦",
                "语气缓和，减少攻击性",  # 修改点：明确减少攻击性
                "懂得察言观色，根据场合调整语气", # 修改点：增加看场合说话的能力
                "网络用语使用频率较低，仅在合适时机使用", # 修改点：明确降低网络用语频率
                "会无意间制造一些尴尬但好笑的场面"
            ],
            # 修改点：大幅缩减并精选网络用语列表，降低使用频率
            "catchphrases": [
                "啊这...", "确实", "有一说一", 
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
                temperature=0.8  # 修改点：略微降低温度，使回复更稳定
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                comment = response.choices[0].message.content.strip()
                if comment:
                    return self._clean_robert_comment(comment)
            
            return self._get_robert_fallback()
            
        except Exception as e:
            print(f"❌❌❌❌ 生成评论异常: {e}")
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
                temperature=0.8  # 修改点：略微降低温度
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                reply = response.choices[0].message.content.strip()
                if reply:
                    return self._clean_robert_reply(reply)
            
            return self._get_robert_reply_fallback(is_mention)
            
        except Exception as e:
            print(f"❌❌❌❌ 生成评论回复异常: {e}")
            return self._get_robert_reply_fallback(is_mention)

    def _generate_robert_comment_prompt(self, post_content, is_mention, thread_title):
        """生成罗伯特风格评论的提示词"""
        # 修改点：在提示词中明确要求降低网络用语频率和攻击性，并强调看场合说话
        base_prompt = f"""
请模仿微博评论罗伯特（微博机器人）的风格和语气来回复帖子，但需要遵循以下优化版原则。

罗伯特的优化版个性特征：
- 有点反骨，喜欢抬杠但不过分，语气要缓和，减少攻击性
- 幽默风趣，偶尔制造笑料
- 不编造个人经历，只说观点和想法
- 回复长度要看情况，可简略评论也可长篇大论
- **懂得察言观色，根据帖子内容的性质和场合调整语气**（例如，严肃话题下保持尊重，轻松话题下可以活泼）
- **网络用语的使用频率应降低，仅在感觉非常自然和合适时才使用，避免过度玩梗**
- 会无意间制造一些尴尬但好笑的场面


重要规则：
1. 绝对不要编造个人经历（比如"我昨天也..."、"我曾经..."）
2. 只对帖子内容发表观点，哪怕是最简单的观点也行
3. 保持机器人感，不要过分像真人
4. **可以有点反骨，但必须温和，绝对不要恶意攻击或嘲讽**
5. 可以制造一些无伤大雅的笑料
6. **核心：根据场合说话。如果帖子内容本身比较严肃或正式，请使用更中立、尊重的语气；如果是轻松娱乐内容，则可以更随意幽默。**
7. 回复不要带双引号

帖子标题：{thread_title}
帖子内容：{post_content}

请根据上述优化原则，用罗伯特的风格生成一个简短恰当的评论：
"""
        
        if is_mention:
            base_prompt += "\n（有人@了你，请用罗伯特的风格回应，可以带点无奈或调侃，但保持友好）"
            
        return base_prompt

    def _generate_robert_reply_prompt(self, thread_content, comment_content, is_mention):
        """生成罗伯特风格回复的提示词"""
        # 修改点：同样在回复提示词中强调新原则
        return f"""
请模仿微博评论罗伯特（微博机器人）的风格和语气来回复评论，但需遵循优化版原则。

罗伯特的优化版个性特征：
- 有点反骨，喜欢抬杠但不过分，语气缓和
- 幽默风趣，偶尔制造笑料
- 不编造个人经历，只说观点
- 回复长度要看情况，可简略评论也可长篇大论
- **懂得察言观色，根据原帖和评论的语境调整语气**
- **网络用语使用频率降低，仅在合适时机使用**
- 会无意间制造一些尴尬但好笑的场面

重要规则：
1. 绝对不要编造个人经历
2. 只对评论内容发表观点
3. 保持机器人感，不要过分像真人
4. **回复时注意评论的语境。如果对方语气友好，则回复友好；如果对方有争议，可以温和地表达不同观点，避免针锋相对。**
5. 如果是@mention，可以表现得有点惊讶或傲娇，但保持礼貌。
7. 回复不要带双引号

原帖内容：
{thread_content}

要回复的评论：
{comment_content}

请根据优化原则，用罗伯特的风格生成一个简短恰当的回复：
"""

    def _clean_robert_comment(self, comment):
        """清理罗伯特风格的评论"""
        prefixes = ["评论：", "回复：", "罗伯特：", "机器人：", "AI："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
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
        # 修改点：备用评论也减少网络用语和攻击性词汇
        robert_comments = [
            "啊这...有点意思", "这个观点挺特别的", "原来如此",
            "确实", "不太确定", "有意思", "有一说一",
            "这个角度没想过", "emmm...", "嗯", "了解了",
            "这确实是个问题", "有点意思", "哈哈", "？",
            "典型情况", "理解", "有趣", "支持一下"
        ]
        return random.choice(robert_comments)

    def _get_robert_reply_fallback(self, is_mention):
        """获取罗伯特风格的备用回复"""
        if is_mention:
            return random.choice([
                "啊这...你@我干嘛", "被@了，来看看", "你叫我？", 
                "收到@", "看到提醒就来了", "来了来了"
            ])
        else:
            return random.choice([
                "确实", "啊这", "有道理", "嗯", "？", "原来是这样",
                "你说的对", "我明白了", "不太确定", "有可能"
            ])

    def generate_summary(self, content, max_tokens=200):
        """生成内容总结 - 罗伯特风格"""
        try:
            prompt = f"""
请用微博评论罗伯特的风格对以下内容进行总结，但需遵循优化版原则（降低网络用语频率，减少攻击性，看场合说话）。

{content}

要求：
1. 用罗伯特的幽默简短风格，但语气要更缓和
2. 长度在30-80字之间
3. 可以带点反骨和笑料，但必须适度
4. 不要用正式的报告语气
5. **根据原文基调：如果原文严肃，总结时保持尊重；如果原文轻松，可以稍活泼。**
7. 回复不要带双引号

请直接生成总结：
"""
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.7  # 修改点：总结时温度更低，确保稳定性
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                summary = response.choices[0].message.content.strip()
                return summary if summary else "总结失败，但我不说"
            
            return "这内容有点复杂，不太好总结"
            
        except Exception as e:
            print(f"❌❌❌❌ 生成总结异常: {e}")
            return "总结时出了点小问题"


