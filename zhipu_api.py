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
        print(f"✅ zai-sdk版本: {zai.__version__}")
    
    def generate_comment(self, post_content, max_tokens=200):
        """使用智谱API生成评论内容"""
        try:
            # 简化内容，避免过长
            if len(post_content) > 500:
                post_content = post_content[:500] + "..."
            
            # 构建提示词
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
            print(f"📝 帖子内容预览: {post_content[:100]}...")
            
            # 根据官方文档示例调用API
            response = self.client.chat.completions.create(
                model="glm-4.5-flash",
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                thinking={
                    "type": "enabled"  # 启用思考模式
                },
                stream=False,  # 非流式输出
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            print(f"✅ API调用成功，响应类型: {type(response)}")
            
            # 处理响应（根据zai-sdk的响应结构）
            if hasattr(response, 'choices') and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and hasattr(response.choices[0].message, 'content'):
                    comment = response.choices[0].message.content.strip()
                    
                    if comment:
                        print(f"✅ 成功获取AI评论: {comment}")
                        return self._clean_comment(comment)
            
            # 如果上述方式不成功，尝试其他方式解析响应
            print("🔍 尝试其他方式解析响应...")
            
            # 将响应转换为字典查看结构
            response_dict = response.__dict__ if hasattr(response, '__dict__') else {}
            print(f"🔍 响应结构: {json.dumps(response_dict, ensure_ascii=False, default=str)}")
            
            # 尝试从字典中获取内容
            if 'choices' in response_dict and len(response_dict['choices']) > 0:
                choice = response_dict['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    comment = choice['message']['content'].strip()
                    if comment:
                        print(f"✅ 从字典获取评论: {comment}")
                        return self._clean_comment(comment)
            
            print("❌ 无法从响应中提取评论内容")
            return self._get_fallback_comment()
            
        except Exception as e:
            print(f"❌ zai-sdk调用异常: {e}")
            return self._get_fallback_comment()
    
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
    
    def _get_fallback_comment(self):
        """获取备选评论"""
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

