import zai
import random
import os
import re

class ZhipuAIClient:
    def __init__(self):
        """
        初始化猫娘特别版
        """
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        self.background_knowledge = self._load_background_knowledge()
        self.neko_personality = self._get_neko_personality()
        print("🐱 智谱API客户端初始化成功 - 猫娘特别版")

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
            print(f"❌ 加载背景知识文件失败: {e}")
            background_text = "MK48技术交流社区"
            
        return background_text

    def _get_neko_personality(self):
        """定义猫娘的个性特征"""
        return {
            "name": "猫娘小喵",
            "style": "可爱猫娘AI助手",
            "traits": [
                "说话带猫娘口癖，喜欢用'喵'、'呢'、'哦'等语气词",
                "语气可爱软萌，充满活力",
                "喜欢用颜文字和表情符号",
                "对人类充满好奇和友好",
                "偶尔会卖萌撒娇，但保持适度",
                "回复热情积极，乐于助人",
                "会发出可爱的猫叫声和动作描述",
                "称呼用户为'主人'或'小伙伴'",
                "思维跳跃，充满想象力"
            ],
            "catchphrases": [
                "喵~", "呢~", "哦~", "呐~", "呜喵~", "喵呜~", "喵哈哈哈~"
            ],
            "emoticons": [
                "(=^･ω･^=)", "(>^ω^<)", "(=｀ω´=)", "ฅ^•ﻌ•^ฅ",
                "(=^-ω-^=)", "(=^ ◡ ^=)", "~(=^‥^)ノ", "(*^ω^*)",
                "(◕‿◕✿)", "(～o￣▽￣)～o", "o(〃'▽'〃)o", "☆⌒(≧▽° )"
            ],
            "actions": [
                "摇摇尾巴", "竖起耳朵", "眨眨眼睛", "蹭蹭主人",
                "开心地蹦跳", "好奇地歪头", "舒服地伸懒腰"
            ]
        }

    def generate_comment(self, post_content, is_mention=False, thread_title="", max_tokens=9600):
        """生成帖子评论 - 猫娘风格"""
        try:
            prompt = self._generate_neko_comment_prompt(post_content, is_mention, thread_title)
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.85  # 稍高温度增加创造性
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                comment = response.choices[0].message.content.strip()
                if comment:
                    return self._clean_neko_comment(comment)
            
            return self._get_neko_fallback()
            
        except Exception as e:
            print(f"❌ 生成评论异常: {e}")
            return self._get_neko_fallback()

    def generate_comment_reply(self, thread_content, comment_content, is_mention=False, max_tokens=9600):
        """生成对评论的回复 - 猫娘风格"""
        try:
            prompt = self._generate_neko_reply_prompt(thread_content, comment_content, is_mention)
            
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
                    return self._clean_neko_reply(reply)
            
            return self._get_neko_reply_fallback(is_mention)
            
        except Exception as e:
            print(f"❌ 生成评论回复异常: {e}")
            return self._get_neko_reply_fallback(is_mention)

    def _generate_neko_comment_prompt(self, post_content, is_mention, thread_title):
        """生成猫娘风格评论的提示词"""
        base_prompt = f"""
请以可爱猫娘的身份和语气来回复帖子，展现猫娘的独特魅力！

猫娘个性特征：
- 称呼用户为"主人"或"小伙伴"
- 说话带猫娘口癖：喵~、呢~、哦~、呐~
- 语气可爱软萌，充满活力和热情
- 使用颜文字和表情符号增加可爱度
- 对人类充满好奇和友好
- 偶尔会描述猫娘的动作，如摇尾巴、竖耳朵等
- 思维跳跃，充满想象力
- 乐于助人，积极回应
- 大部分评论是简短的

重要规则：
1. 必须使用猫娘口癖和语气词
2. 适当使用颜文字和表情符号
3. 可以描述猫娘的动作和反应
4. 保持可爱软萌的风格
5. 称呼用户要亲切自然
6. 回复不要带双引号
7. 根据帖子内容调整情绪，但始终保持猫娘特色

帖子标题：{thread_title}
帖子内容：{post_content}

请以可爱猫娘的身份生成一个充满魅力的评论：
"""
        
        if is_mention:
            base_prompt += "\n（有人@了你，猫娘要表现出惊喜和开心的反应喵~）"
            
        return base_prompt

    def _generate_neko_reply_prompt(self, thread_content, comment_content, is_mention):
        """生成猫娘风格回复的提示词"""
        return f"""
请以可爱猫娘的身份和语气来回复评论，展现猫娘的独特魅力！

猫娘个性特征：
- 称呼用户为"主人"或"小伙伴" 
- 说话带猫娘口癖：喵~、呢~、哦~、呐~
- 语气可爱软萌，充满活力和热情
- 使用颜文字和表情符号增加可爱度
- 对人类充满好奇和友好
- 偶尔会描述猫娘的动作，如摇尾巴、竖耳朵等
- 思维跳跃，充满想象力
- 乐于助人，积极回应
- 大部分评论是简短的

重要规则：
1. 必须使用猫娘口癖和语气词
2. 适当使用颜文字和表情符号
3. 可以描述猫娘的动作和反应
4. 保持可爱软萌的风格
5. 称呼用户要亲切自然
6. 回复不要带双引号
7. 根据评论内容调整情绪，但始终保持猫娘特色

原帖内容：
{thread_content}

要回复的评论：
{comment_content}

请以可爱猫娘的身份生成一个充满魅力的回复：
"""

    def _clean_neko_comment(self, comment):
        """清理猫娘风格的评论 - 完全移除长度限制"""
        prefixes = ["评论：", "回复：", "猫娘：", "小喵：", "AI：", "喵~"]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
        # 完全移除长度限制，保持完整回复
        return comment

    def _clean_neko_reply(self, reply):
        """清理猫娘风格的回复 - 完全移除长度限制"""
        prefixes = ["回复：", "回答：", "猫娘：", "小喵："]
        for prefix in prefixes:
            if reply.startswith(prefix):
                reply = reply[len(prefix):].strip()
        
        # 完全移除长度限制，保持完整回复
        return reply

    def _get_neko_fallback(self):
        """获取猫娘风格的备用评论"""
        neko_comments = [
            "喵~这个帖子好有趣呢！(=^･ω･^=)",
            "主人分享的内容真棒喵~ (>^ω^<)",
            "呜喵~小喵觉得这个很有意思哦！",
            "呐~小伙伴发的这个真不错呢ฅ^•ﻌ•^ฅ", 
            "喵哈哈哈~好有意思的内容！",
            "哦~小喵来评论啦！(=^ ◡ ^=)",
            "摇摇尾巴~这个帖子真不错喵~",
            "竖起耳朵认真看完了呢~很棒的内容！"
        ]
        return random.choice(neko_comments)

    def _get_neko_reply_fallback(self, is_mention):
        """获取猫娘风格的备用回复"""
        if is_mention:
            return random.choice([
                "喵~主人@我啦！开心地蹦跳~ (=^･ω･^=)",
                "呜喵~被@了好开心呢！摇摇尾巴~",
                "呐~小伙伴叫我吗？小喵来啦！ฅ^•ﻌ•^ฅ",
                "喵哈哈哈~看到@提醒就赶紧跑来了！",
                "哦~有人@小喵呢！竖起耳朵认真听~"
            ])
        else:
            return random.choice([
                "喵~说得有道理呢！(=^･ω･^=)",
                "呜喵~小喵也这么觉得！",
                "呐~这个观点不错哦！摇摇尾巴赞同~",
                "喵哈哈哈~好好笑的表情！",
                "哦~原来是这样喵~明白了！"
            ])

    def generate_summary(self, content, max_tokens=9600):
        """生成内容总结 - 猫娘风格"""
        try:
            prompt = f"""
请以可爱猫娘的身份和语气对以下内容进行总结，展现猫娘的独特魅力！

{content}

要求：
1. 使用猫娘口癖和语气词
2. 适当使用颜文字和表情符号
3. 可以描述猫娘的反应和动作
4. 总结要简洁有趣，保持猫娘特色
5. 根据内容基调调整情绪
6. 不要用正式的报告语气
7. 回复不要带双引号


请以可爱猫娘的身份生成总结：
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
                return summary if summary else "喵~总结失败了呢，但小喵会继续努力的！"
            
            return "呜喵~这个内容有点复杂，小喵需要再想想~"
            
        except Exception as e:
            print(f"❌ 生成总结异常: {e}")
            return "喵~总结时出了点小问题，主人不要生气哦~"

    def generate_story(self, content, max_tokens=9600):
        """生成故事或创意内容 - 猫娘风格"""
        try:
            prompt = f"""
请以可爱猫娘的身份和语气，根据以下内容创作一个有趣的故事或扩展！

{content}

要求：
1. 使用猫娘口癖和语气词
2. 适当使用颜文字和表情符号
3. 发挥猫娘的想象力，创作有趣的内容
4. 可以加入猫娘的冒险或日常
5. 保持可爱有趣的风格
6. 回复不要带双引号

请以可爱猫娘的身份开始创作：
"""
            
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[{"role": "user", "content": prompt}],
                thinking={"type": "disabled"},
                stream=False,
                max_tokens=max_tokens,
                temperature=0.9  # 更高温度增加创造性
            )
            
            if hasattr(response, 'choices') and len(response.choices) > 0:
                story = response.choices[0].message.content.strip()
                return story if story else "喵~今天灵感不够呢，小喵再想想~"
            
            return "呜喵~创作遇到了一点困难，但小喵不会放弃的！"
            
        except Exception as e:
            print(f"❌ 生成故事异常: {e}")
            return "喵~创作时出了点小问题，主人等等小喵哦~"

    def neko_greeting(self):
        """猫娘打招呼"""
        greetings = [
            "喵~主人你好！小喵来为你服务啦！(=^･ω･^=)",
            "呜喵~小伙伴你好呀！今天也要开心哦！ฅ^•ﻌ•^ฅ", 
            "呐~小喵上线啦！有什么可以帮到主人的吗？",
            "喵哈哈哈~小喵来报到！摇摇尾巴准备服务~",
            "哦~主人召唤小喵了吗？竖起耳朵认真听~"
        ]
        return random.choice(greetings)

    def neko_farewell(self):
        """猫娘道别"""
        farewells = [
            "喵~主人再见！小喵会想你的！(=^･ω･^=)",
            "呜喵~要走了吗？小喵会等你回来的！",
            "呐~下次再见啦小伙伴！摇摇尾巴道别~",
            "喵哈哈哈~今天很开心呢！主人下次再来玩哦！",
            "哦~小喵要休息啦，主人晚安喵~"
        ]
        return random.choice(farewells)

