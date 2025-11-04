# post.py
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
    
    def create_thread(self, token, category_id, title, content):
        """创建帖子"""
        try:
            # 尝试不同的认证方式
            headers_list = [
                {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                {'Authorization': f'Token {token}', 'Content-Type': 'application/json'},
                {'Authorization': token, 'Content-Type': 'application/json'},  # 直接使用token
                {'X-Auth-Token': token, 'Content-Type': 'application/json'},
                {'Content-Type': 'application/json'}  # 不使用token头，可能通过cookie认证
            ]
            
            thread_data = {
                "category_id": category_id,
                "title": title,
                "content": content
            }
            
            print(f"📝 创建帖子: {title}")
            
            for i, headers in enumerate(headers_list):
                print(f"🔄 尝试认证方式 {i+1}/{len(headers_list)}...")
                
                try:
                    response = self.session.post(
                        self.create_thread_url, 
                        json=thread_data, 
                        headers=headers, 
                        timeout=15
                    )
                    
                    print(f"📊 发帖响应状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ 发帖响应: {json.dumps(result, ensure_ascii=False)}")
                        
                        if result.get('success') is True:
                            thread_data = result.get('data', {})
                            if 'id' in thread_data:
                                print(f"🎉 发帖成功！帖子ID: {thread_data.get('id')}")
                                return True, thread_data
                            else:
                                error_msg = "发帖响应数据不完整"
                                print(f"❌ 发帖失败: {error_msg}")
                        else:
                            error_msg = result.get('message', '未知错误')
                            print(f"❌ 发帖失败: {error_msg}")
                    else:
                        print(f"❌ 认证方式 {i+1} 失败: HTTP {response.status_code}")
                        if response.status_code == 401:
                            print("  认证失败，尝试下一种方式...")
                            continue
                        else:
                            print(f"  响应内容: {response.text}")
                            
                except Exception as e:
                    print(f"❌ 认证方式 {i+1} 请求异常: {e}")
                    continue
            
            print("💥 所有认证方式尝试失败")
            return False, None
                
        except Exception as e:
            print(f"❌ 发帖请求异常: {e}")
            return False, None
