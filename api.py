# api.py
import requests
import json
import time
from datetime import datetime
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ContentAPI:
    def __init__(self):
        # 硬编码 API tokens
        self.zhihu_token = "t6rshmnm0sfqfyfpvttaj5kocefnck"
        self.weibo_token = "p2wpki7ps4qgtx51xzbfw6yjvkzgpk"
        self.session = requests.Session()
        
        # 设置重试策略 - 兼容新版本 urllib3
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        # 创建适配器并禁用 SSL 验证
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*'
        })
    
    def fetch_zhihu_daily(self):
        """获取知乎日报内容"""
        try:
            print("📰 获取知乎日报...")
            
            api_url = f"https://v3.alapi.cn/api/zhihu?token={self.zhihu_token}"
            print(f"🔗 API URL: {api_url}")
            
            # 禁用 SSL 验证
            response = self.session.get(api_url, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 知乎API响应代码: {data.get('code')}")
                
                if data.get('code') == 200 and data.get('success'):
                    stories_count = len(data.get('data', {}).get('stories', []))
                    print(f"✅ 知乎日报获取成功，故事数量: {stories_count}")
                    return self._format_zhihu_content(data)
                else:
                    error_msg = data.get('message', '未知错误')
                    print(f"❌ 知乎API返回错误: {error_msg}")
                    return None
            else:
                print(f"❌ 知乎日报获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取知乎日报异常: {e}")
            return None
    
    def fetch_weibo_hot(self):
        """获取微博热搜榜"""
        try:
            print("🔥 获取微博热搜榜...")
            
            api_url = f"https://v3.alapi.cn/api/new/wbtop?token={self.weibo_token}"
            print(f"🔗 API URL: {api_url}")
            
            # 禁用 SSL 验证
            response = self.session.get(api_url, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 微博API响应代码: {data.get('code')}")
                
                if data.get('code') == 200 and data.get('success'):
                    hot_items = data.get('data', [])
                    print(f"✅ 微博热搜获取成功，热搜数量: {len(hot_items)}")
                    return self._format_weibo_content(data)
                else:
                    error_msg = data.get('message', '未知错误')
                    print(f"❌ 微博API返回错误: {error_msg}")
                    return None
            else:
                print(f"❌ 微博热搜获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取微博热搜异常: {e}")
            return None
    
    def _parse_hint(self, hint):
        """解析hint字段 - 基于你的 JavaScript 逻辑"""
        author = '未知作者'
        reading_time = ''
        
        if hint:
            import re
            # 匹配模式：作者 · 时间阅读 或 作者 / 时间阅读
            match = re.match(r'^(.+?)[·/]\s*(\d+\s*分钟阅读)$', hint)
            if match:
                author = match.group(1).strip()
                reading_time = match.group(2).strip()
            elif '分钟阅读' in hint:
                # 如果只有时间没有作者
                reading_time = hint.strip()
            else:
                # 如果只有作者没有时间，或者格式不符
                author = hint.strip()
        
        return author, reading_time
    
    def _format_zhihu_content(self, zhihu_data):
        """格式化知乎日报内容"""
        try:
            data = zhihu_data.get('data', {})
            date = data.get('date', '')
            stories = data.get('stories', [])
            
            # 格式化日期
            formatted_date = ''
            if date and len(date) == 8:
                formatted_date = f"{date[0:4]}-{date[4:6]}-{date[6:8]}"
            
            content = f"# 知乎日报 {formatted_date}\n\n"
            
            # 添加所有故事
            for index, story in enumerate(stories):
                author, reading_time = self._parse_hint(story.get('hint', ''))
                
                content += f"## {index + 1}. {story.get('title', '')}\n"
                content += f"**作者**: {author}\n"
                
                if reading_time:
                    content += f"**阅读时间**: {reading_time}\n\n"
                else:
                    content += '\n'
                
                # 添加图片
                images = story.get('images', [])
                if images and len(images) > 0:
                    content += f"![图片]({images[0]})\n\n"
                
                # 添加原文链接
                url = story.get('url', '')
                if url:
                    content += f"[阅读原文]({url})\n\n"
                
                content += "---\n\n"
            
            # 添加生成时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content += f"*自动生成于 {current_time}*"
            
            return content
            
        except Exception as e:
            print(f"❌ 格式化知乎内容异常: {e}")
            return None
    
    def _format_weibo_content(self, weibo_data):
        """格式化微博热搜内容"""
        try:
            hot_items = weibo_data.get('data', [])
            
            content = "# 微博热搜榜\n\n"
            
            # 添加前20条热搜
            for index, item in enumerate(hot_items[:20]):
                hot_word = item.get('hot_word', '')
                hot_num = item.get('hot_num', '')
                url = item.get('url', '')
                
                content += f"**{index + 1}. {hot_word}**"
                
                if hot_num:
                    content += f" 🔥 {hot_num}"
                
                content += "\n"
                
                if url and not url.startswith('javascript'):
                    content += f"[查看详情]({url})\n"
                
                content += "\n"
            
            # 添加生成时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content += f"*自动生成于 {current_time}*"
            
            return content
            
        except Exception as e:
            print(f"❌ 格式化微博内容异常: {e}")
            return None
    
    def get_daily_content(self):
        """获取每日内容（知乎日报 + 微博热搜）"""
        print("🔄 开始获取每日内容...")
        
        # 获取知乎日报
        zhihu_content = self.fetch_zhihu_daily()
        
        # 获取微博热搜
        weibo_content = self.fetch_weibo_hot()
        
        # 构建完整的帖子内容
        full_content = "置顶广告位\n\n"
        full_content += "## 📰 知乎日报\n\n"
        
        if zhihu_content:
            full_content += zhihu_content + "\n\n"
        else:
            full_content += "今日知乎日报内容获取失败，请稍后重试。\n\n"
        
        full_content += "## 📰 新闻\n\n"
        full_content += "（新闻内容待添加）\n\n"
        
        full_content += "## 🔥 微博热搜\n\n"
        if weibo_content:
            full_content += weibo_content + "\n\n"
        else:
            full_content += "今日微博热搜内容获取失败，请稍后重试。\n\n"
        
        full_content += "## 🖼️ 美图\n\n"
        full_content += "（美图内容待添加）\n\n"
        full_content += "广告位\n\n"
        full_content += "*本帖由 TurkeyBot 自动生成*"
        
        return full_content
    
    def _get_fallback_content(self):
        """备用内容"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        return f"""置顶广告位

## 📰 知乎日报

# 知乎日报 {current_date}

今日知乎日报内容获取失败，请稍后重试。

## 📰 新闻

（新闻内容待添加）

## 🔥 微博热搜

今日微博热搜内容获取失败，请稍后重试。

## 🖼️ 美图

（美图内容待添加）

广告位

*本帖由 TurkeyBot 自动生成*"""
