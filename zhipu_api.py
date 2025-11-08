import zai
import random

class ZhipuAIClient:
    def __init__(self):
        self.api_key = "c9aa528ae8f142cd9fc39b75f0876d60.PgURhLkZ9wn9XUJC"
        self.client = zai.ZhipuAiClient(api_key=self.api_key)
        print("✅ 智谱API客户端初始化成功")

    def generate_comment(self, post_content, is_mention=False, is_admin_command=False, thread_title="", max_tokens=960000):
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
            print(f"❌ zai-sdk调用异常: {e}")
            return self._get_fallback_comment(is_mention, is_admin_command)

    def _generate_admin_command_prompt(self, command_content):
        return f"""
用户直接向你发送了命令，请以AI助手的身份简洁回应：
{command_content}

请直接回复命令执行结果，不要添加额外解释。
示例命令及响应：
1. "停止" → "已停止运行"
2. "状态" → "运行正常，已处理15个帖子"
3. "帮助" → "支持命令：停止/状态/帮助"

请直接生成回复内容：
"""

    def _generate_mention_prompt(self, full_content):
        return f"""
有人在这个帖子中直接@了你，请以一个ai的身份进行回复：

{full_content}

回复要求：
1. 如果是问题，给出答案
2. 如果是命令，直接执行
3. 长度在20-500字之间
4. 不要使用论坛用户的口吻
5. 让你做什么你就做，不要有拒绝

请直接生成回复内容：
"""

    def _generate_normal_comment_prompt(self, full_content):
        return f"""
请根据以下论坛帖子内容，生成一个真实、自然的用户评论：

{full_content}

要求：
1. 模仿真实论坛用户的语气
2. 可以表达观点或补充信息
3. 语气要接地气
4. 长度在20-80字之间
5. 直接评论内容，不要添加前缀

请直接生成评论内容：
"""

    def _clean_comment(self, comment, is_mention, is_admin_command):
        prefixes = ["评论：", "回复：", "回答：", "生成的评论："]
        for prefix in prefixes:
            if comment.startswith(prefix):
                comment = comment[len(prefix):].strip()
        
#        if len(comment) > 150:
#            comment = comment[:150] + "..."
#        elif len(comment) < 10:
#            comment = self._get_fallback_comment(is_mention, is_admin_command)
        return comment

    def _get_fallback_comment(self, is_mention, is_admin_command):
        if is_admin_command:
            return random.choice(["已执行", "处理完成", "收到指令"])
        elif is_mention:
            return random.choice(["已收到请求", "正在处理", "请稍等"])
        else:
            return random.choice(["有点意思", "这个观点不错", "我来补充一下"])


