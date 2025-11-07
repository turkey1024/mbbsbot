    def process_threads(self):
        """处理帖子并自动评论"""
        if not self.session or not self.token:
            print("❌ 未登录，无法处理帖子")
            return False
        
        poster = BBSPoster(self.session, self.base_url)
        commented_count = 0
        checked_count = 0
        
        for category_id in self.target_categories:
            print(f"📋📋 检查板块 {category_id} 的帖子...")
            
            # 获取最新帖子
            threads = poster.get_threads(self.token, category_id, self.max_threads_to_check)
            
            for thread in threads:
                checked_count += 1
                thread_id = thread.get('id')
                thread_title = thread.get('title', '')
                
                print(f"\n📄 检查帖子 [{checked_count}/{len(threads)}]: {thread_title} (ID: {thread_id})")
                
                # 判断是否应该评论
                if not self.should_comment(thread):
                    continue
                
                # 获取帖子的评论
                comments = poster.get_post_comments(self.token, thread_id)
                
                # 检查是否已经评论过
                if poster.has_commented(comments, self.user_id):
                    print("   ✅ 已评论过，跳过")
                    continue
                
                print("   💬 需要评论此帖子")
                
                # 获取帖子内容 - 这里需要确保获取到完整内容
                thread_content = thread.get('content', '') 
                if not thread_content:
                    thread_content = thread.get('content_for_indexes', '')
                if not thread_content:
                    thread_content = thread_title
                
                print(f"   📝 帖子内容长度: {len(thread_content)} 字符")
                print(f"   📋 内容预览: {thread_content[:200]}...")
                
                # 如果内容过短，添加更多上下文
                if len(thread_content) < 50:
                    thread_content = f"帖子标题: {thread_title}\n帖子内容: {thread_content}"
                
                # 使用智谱API生成评论
                try:
                    ai_comment = self.zhipu_client.generate_comment(thread_content)
                    if ai_comment and not ai_comment.startswith("感谢分享"):  # 避免使用备选评论
                        # 发布评论
                        success = poster.create_comment(self.token, thread_id, ai_comment)
                        if success:
                            commented_count += 1
                            print(f"   🎉 评论发布成功！")
                        else:
                            print("   ❌ 评论发布失败")
                    else:
                        print("   ⏭️ 跳过使用备选评论")
                    
                    # 避免频繁调用API，添加延迟
                    time.sleep(3)
                    
                except Exception as e:
                    print(f"   ❌ 处理帖子时出错: {e}")
                    continue
        
        print(f"\n📊 本次运行检查了 {checked_count} 个帖子，成功评论了 {commented_count} 个帖子")
        return commented_count > 0


