import zai
import json
import time
import random

class ZhipuAIClient:
    def __init__(self):
        # 硬编码API Token
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        
        if not self.api_key:
            raise ValueError("API Token 未设置")
        
        # 初始化zai-sdk客户端
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        
        print("✅ 智谱API客户端初始化成功，使用zai-sdk")
    
    def generate_comment(self, post_content, is_mention=False, thread_title="", max_tokens=200):
        """使用智谱API生成评论内容"""
        try:
            # 组合完整内容
            full_content = f"帖子标题：{thread_title}\n帖子内容：{post_content}"
            
            # 根据内容长度决定是否截断
            if len(full_content) > 800:
                full_content = full_content[:800] + "...[内容过长已截断]"
            
            # 根据是否是@mention使用不同的提示词
            if is_mention:
                prompt = f"""
有人在这个帖子中提到了你，请以论坛用户的身份进行自然回复：

{full_content}

请生成一个真实、自然的回复，要求：
1. 不要使用"感谢分享"、"很棒"等机械式鼓励
2. 像真实用户一样，可以调侃、提问或表达个人观点
3. 如果是技术问题，给出实用建议
4. 如果是闲聊，保持轻松幽默
5. 长度在30-100字之间
6. 直接回复内容，不要自称AI或机器人

请直接生成回复内容：
"""
            else:
                prompt = f"""
请根据以下论坛帖子内容，生成一个真实、自然的评论：

{full_content}

请模仿真实论坛用户的语气评论，要求：
1. 避免虚假鼓励和客套话
2. 可以表达质疑、补充信息或分享相关经验
3. 语气要接地气，像贴吧/微博的普通用户
4. 可以适当使用网络用语，但不要过度
5. 长度在20-80字之间
6. 直接评论内容，不要添加前缀

请直接生成评论内容：
"""
            
            print("🔄🔄 使用zai-sdk调用智谱API...")
            if is_mention:
                print("🔔🔔 生成@mention回复")
            else:
                print("💬💬 生成普通评论")
            
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
                    "type": "disabled"
                },
                stream=False,
                max_tokens=max_tokens,
                temperature=0.8  # 提高温度让回复更随机自然
            )
            
            # 处理响应
            if hasattr(response, 'choices') and len(response.choices) > 0:
                choice = response.choices[0]
                
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    comment = choice.message.content.strip()
                    
                    if comment and comment != "\\n":
                        print(f"✅ 成功获取AI评论: {comment}")
                        return self._clean_comment(comment, is_mention)
            
            print("❌❌ 无法从响应中提取评论内容")
            return self._get_fallback_comment(is_mention)
            
        except Exception as e:
            print(f"❌❌ zai-sdk调用异常: {e}")
            return self._get_fallback_comment(is_mention)
    
    def _clean_comment(self, comment, is_mention):
        """清理评论内容"""
        # 移除可能的前缀
        prefixes = ["评论：", "回复：", "回答：", "生成的评论：", "好的，", "嗯，"]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
        # 确保评论长度合理
        if len(comment) > 150:
            comment = comment[:150] + "..."
        elif len(comment) < 10:
            comment = self._get_fallback_comment(is_mention)
            
        return comment
    
    def _get_fallback_comment(self, is_mention):
        """获取备选评论"""
        if is_mention:
            fallback_comments = [
                "来了来了，刚看到消息",
                "嗯？有人叫我？",
                "这个问题有点意思...",
                "等我看看先",
                "这个我有点经验"
            ]
        else:
            fallback_comments = [
                "有点意思",
                "这个观点不错",
                "我来补充一下",
                "实际体验如何？",
                "有没有更多细节？",
                "这个我试过，效果还行",
                "等楼主更新",
                "mark一下",
                "先收藏了",
                "有没有其他方案？"
            ]
        
        fallback = random.choice(fallback_comments)
        print(f"🔄🔄 使用备选评论: {fallback}")
        return fallback


