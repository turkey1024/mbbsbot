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
            
            print(f"📝 创建帖子: {title}")
            print(f"🔑 使用认证方式: 直接Token认证")
            
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
                        return False, None
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌ 发帖失败: {error_msg}")
                    return False, None
            else:
                print(f"❌ 发帖失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")
                return False, None
                
        except Exception as e:
            print(f"❌ 发帖请求异常: {e}")
            return False, None

