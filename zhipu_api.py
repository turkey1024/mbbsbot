import requests
import json
import time

class ZhipuAIClient:
    def __init__(self):
        # 硬编码API Token
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        if not self.api_key:
            raise ValueError("API Token 未设置")
        
        print("✅ 智谱API客户端初始化成功，使用GLM-4.5-Flash模型")
    
    def generate_comment(self, post_content, max_tokens=200):
        """使用智谱API生成评论内容"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 构建提示词，让AI生成合适的评论
            prompt = f"""
            请根据以下帖子内容生成一个简短、友好、有意义的评论。
            评论应该：
            1. 表达对帖子内容的理解或赞赏
            2. 提出有建设性的观点或问题
            3. 保持积极友好的语气
            4. 长度在50-150字之间
            5. 不要使用"我认为"、"我觉得"等主观表达
            6. 直接针对帖子内容进行回应
            
            帖子内容：
            {post_content[:1000]}  # 限制内容长度避免token超限
            
            请直接生成评论内容，不要添加任何前缀或说明。
            """
            
            data = {
                "model": "GLM-4.5-Flash",  # 使用免费的Flash模型
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False
            }
            
            print("🔄 调用智谱API生成评论...")
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code} - {response.text}")
                return self._get_fallback_comment()
            
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                print(f"❌ API响应格式异常: {result}")
                return self._get_fallback_comment()
            
            comment = result['choices'][0]['message']['content'].strip()
            
            # 清理评论内容
            comment = self._clean_comment(comment)
            
            print(f"✅ 智谱API评论生成成功: {comment[:80]}...")
            return comment
            
        except requests.exceptions.Timeout:
            print("❌ 智谱API请求超时")
            return self._get_fallback_comment()
        except Exception as e:
            print(f"❌ 智谱API调用失败: {e}")
            return self._get_fallback_comment()
    
    def _clean_comment(self, comment):
        """清理评论内容，移除不必要的标记和空白"""
        # 移除可能的前缀
        prefixes = ["评论：", "回复：", "回答：", "生成的评论："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
        # 移除引号
        comment = comment.strip('"').strip("'").strip()
        
        # 确保评论长度合理
        if len(comment) > 300:
            comment = comment[:300] + "..."
        elif len(comment) < 10:
            comment = "感谢分享！内容很有价值。"
            
        return comment
    
    def _get_fallback_comment(self):
        """获取备选评论（当API失败时使用）"""
        fallback_comments = [
            "感谢分享！内容很有价值，期待更多精彩内容！",
            "很有意思的帖子，学到了新知识！",
            "观点独特，很有启发性！",
            "谢谢分享，这对大家很有帮助！",
            "内容详实，分析到位！"
        ]
        import random
        return random.choice(fallback_comments)

