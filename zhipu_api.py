import zai
import json
import time

class ZhipuAIClient:
    def __init__(self):
        # 硬编码API Token
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        
        if not self.api_key:
            raise ValueError("API Token 未设置")
        
        # 初始化zai-sdk客户端
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        
        print("✅ 智谱API客户端初始化成功，使用zai-sdk")
    
    def generate_comment(self, post_content, max_tokens=200, is_mention=False, mention_content=""):
        """使用智谱API生成评论内容"""
        try:
            # 简化内容，避免过长
            if len(post_content) > 500:
                post_content = post_content[:500] + "..."
            
            # 根据是否是被提及来构建不同的提示词
            if is_mention and mention_content:
                prompt = f"""
你是一个论坛机器人，用户通过以下方式提到了你：{mention_content}

请根据用户的提及内容，生成一个有针对性的回复。如果是要求总结帖子，请简要总结帖子内容；如果是提问，请给出专业回答；如果是闲聊，请友好回应。

帖子内容：
{post_content}

请生成一个50-150字的回复，要求：
1. 直接回应用户的提及
2. 保持专业友好的语气
3. 如果用户要求总结，请简洁明了地总结帖子要点
4. 如果用户提问，请给出有价值的回答

请直接生成回复内容，不要添加任何前缀或说明。
"""
            else:
                prompt = f"""
请根据以下论坛帖子内容，生成一个简短、友好且有意义的评论。

帖子内容：
{post_content}

请生成一个50-150字的评论，要求：
1. 表达对帖子内容的理解或赞赏
2. 提出有建设性的观点或问题
3. 保持积极友好的语气
4. 直接针对帖子内容进行回应

请直接生成评论内容，不要添加任何前缀或说明。
"""
            
            print("🔄 使用zai-sdk调用智谱API...")
            
            # 禁用思考模式
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                thinking={
                    "type": "disabled"  # 禁用思考模式
                },
                stream=False,  # 非流式输出
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            # 处理响应
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                
                # 直接获取message.content
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    comment = choice.message.content.strip()
                    
                    if comment and comment != "\\n":  # 检查是否为空或只有换行符
                        print(f"✅ 成功获取AI评论: {comment}")
                        return self._clean_comment(comment)
            
            print("❌ 无法从响应中提取评论内容")
            return self._get_fallback_comment(is_mention)
            
        except Exception as e:
            print(f"❌ zai-sdk调用异常: {e}")
            return self._get_fallback_comment(is_mention)
    
    def _clean_comment(self, comment):
        """清理评论内容"""
        # 移除可能的前缀
        prefixes = ["评论：", "回复：", "回答：", "生成的评论："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
        # 确保评论长度合理
        if len(comment) > 300:
            comment = comment[:300] + "..."
        elif len(comment) < 10:
            comment = "感谢分享！内容很有价值。"
            
        return comment
    
    def _get_fallback_comment(self, is_mention=False):
        """获取备选评论"""
        if is_mention:
            fallback_comments = [
                "收到您的提及！我会认真阅读帖子内容并给出回复。",
                "感谢您的提及，我正在分析帖子内容...",
                "您好！我看到您提到了我，有什么可以帮您的吗？"
            ]
        else:
            fallback_comments = [
                "观点很有启发性！",
                "内容很实用，谢谢分享！",
                "这个话题很有意思！",
                "学到了新知识！",
                "感谢分享宝贵经验！"
            ]
        import random
        fallback = random.choice(fallback_comments)
        print(f"🔄 使用备选评论: {fallback}")
        return fallback

