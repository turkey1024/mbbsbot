import requests
import json
import time

class BBSPoster:
    def __init__(self, session, base_url):
        self.session = session
        self.base_url = base_url
        self.api_base = f"{base_url}/bbs"
        
        # API 端点
        self.create_thread_url = f"{self.api_base}/threads/create"
        self.list_threads_url = f"{self.api_base}/threads/list"
        self.list_posts_url = f"{self.api_base}/posts/list"
        self.create_post_url = f"{self.api_base}/posts/create"
        self.create_comment_url = f"{self.api_base}/posts/createComment"
    
    def create_thread(self, token, category_id, title, content):
        """创建帖子"""
        try:
            # 只使用成功的认证方式：方式3（直接使用token）
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            
            thread_data = {
                "category_id": category_id,
                "title": title,
                "content": content
            }
            
            print(f"📝📝 创建帖子: {title}")
            print(f"🔑🔑 使用认证方式: 直接Token认证")
            
            response = self.session.post(
                self.create_thread_url, 
                json=thread_data, 
                headers=headers, 
                timeout=15
            )
            
            print(f"📊📊 发帖响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 发帖响应: {json.dumps(result, ensure_ascii=False)}")
                
                if result.get('success') is True:
                    thread_data = result.get('data', {})
                    if 'id' in thread_data:
                        print(f"🎉🎉 发帖成功！帖子ID: {thread_data.get('id')}")
                        return True, thread_data
                    else:
                        error_msg = "发帖响应数据不完整"
                        print(f"❌❌ 发帖失败: {error_msg}")
                        return False, None
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌❌ 发帖失败: {error_msg}")
                    return False, None
            else:
                print(f"❌❌ 发帖失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌❌ 发帖请求异常: {e}")
            return False, None
    
    def get_threads(self, token, category_id=None, page_limit=20):
        """获取帖子列表"""
        try:
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            
            params = {
                "page_limit": page_limit,
                "page_offset": 0,
                "sort": "-created_at"  # 按创建时间倒序，获取最新帖子
            }
            
            if category_id:
                params["category_id"] = category_id
            
            response = self.session.get(self.list_threads_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    threads = result.get('data', [])
                    print(f"✅ 获取到 {len(threads)} 个帖子")
                    return threads
                else:
                    print(f"❌❌ 获取帖子列表失败: {result.get('message')}")
                    return []
            else:
                print(f"❌❌ 获取帖子列表HTTP错误: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌❌ 获取帖子列表异常: {e}")
            return []
    
    def get_post_comments(self, token, thread_id):
        """获取帖子的所有评论"""
        try:
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            
            params = {
                "thread_id": thread_id,
                "page_limit": 50,  # 假设一个帖子最多50条评论
                "page_offset": 0
            }
            
            response = self.session.get(self.list_posts_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    posts = result.get('data', [])
                    # 过滤掉第一条（帖子内容本身），只返回评论
                    comments = [post for post in posts if not post.get('is_first', True)]
                    return comments
                else:
                    print(f"❌❌ 获取评论失败: {result.get('message')}")
                    return []
            else:
                print(f"❌❌ 获取评论HTTP错误: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌❌ 获取评论异常: {e}")
            return []
    
    def has_commented(self, comments, user_id):
        """检查是否已经评论过"""
        for comment in comments:
            if comment.get('user_id') == user_id:
                return True
        return False
    
    def create_comment(self, token, thread_id, content):
        """创建评论（一级评论）"""
        try:
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            
            post_data = {
                "thread_id": thread_id,
                "content": content
            }
            
            response = self.session.post(self.create_post_url, json=post_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    print(f"✅ 评论发布成功！帖子ID: {thread_id}")
                    return True
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌❌ 评论发布失败: {error_msg}")
                    return False
            else:
                print(f"❌❌ 评论发布HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌❌ 评论发布异常: {e}")
            return False
    
    def create_comment_reply(self, token, post_id, content, comment_post_id=None):
        """创建评论回复（二级评论，回复特定评论）"""
        try:
            headers = {'Authorization': token, 'Content-Type': 'application/json'}
            
            post_data = {
                "post_id": post_id,
                "content": content
            }
            
            if comment_post_id:
                post_data["comment_post_id"] = comment_post_id
            
            response = self.session.post(self.create_comment_url, json=post_data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') is True:
                    print(f"✅ 评论回复发布成功！评论ID: {post_id}")
                    return True
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌❌ 评论回复发布失败: {error_msg}")
                    return False
            else:
                print(f"❌❌ 评论回复发布HTTP错误: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌❌ 评论回复发布异常: {e}")
            return False
    
    def check_mentions(self, content):
        """检查内容中是否包含提及机器人的关键词"""
        mention_keywords = [
            '@turkeybot', 
            '@turkey', 
            '@论坛机器人', 
            '@机器人',
            'turkeybot',
            '论坛机器人'
        ]
        
        for keyword in mention_keywords:
            if keyword.lower() in content.lower():
                return True, keyword
        return False, None


