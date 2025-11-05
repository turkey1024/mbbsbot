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
        self.zhihu_token = "p2wpki7ps4qgtx51xzbfw6yjvkzgpk"
        self.weibo_token = "p2wpki7ps4qgtx51xzbfw6yjvkzgpk"
        self.news_token = "p2wpki7ps4qgtx51xzbfw6yjvkzgpk"
        self.acg_token = "p2wpki7ps4qgtx51xzbfw6yjvkzgpk"
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
    
    def fetch_news(self):
        """获取新闻内容"""
        try:
            print("📰 获取新闻...")
            
            api_url = f"https://v3.alapi.cn/api/new/toutiao?token={self.news_token}"
            print(f"🔗 API URL: {api_url}")
            
            # 禁用 SSL 验证
            response = self.session.get(api_url, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 新闻API响应代码: {data.get('code')}")
                
                if data.get('code') == 200 and data.get('success'):
                    news_items = data.get('data', [])
                    print(f"✅ 新闻获取成功，新闻数量: {len(news_items)}")
                    return self._format_news_content(data)
                else:
                    error_msg = data.get('message', '未知错误')
                    print(f"❌ 新闻API返回错误: {error_msg}")
                    return None
            else:
                print(f"❌ 新闻获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取新闻异常: {e}")
            return None
    
    def fetch_acg_image(self):
        """获取美图"""
        try:
            print("🖼️ 获取美图...")
            
            api_url = f"https://v3.alapi.cn/api/acg?token={self.acg_token}&format=json"
            print(f"🔗 API URL: {api_url}")
            
            # 禁用 SSL 验证
            response = self.session.get(api_url, timeout=15, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 美图API响应代码: {data.get('code')}")
                
                if data.get('code') == 200 and data.get('success'):
                    image_data = data.get('data', {})
                    print(f"✅ 美图获取成功")
                    return self._format_acg_content(data)
                else:
                    error_msg = data.get('message', '未知错误')
                    print(f"❌ 美图API返回错误: {error_msg}")
                    return None
            else:
                print(f"❌ 美图获取失败: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 获取美图异常: {e}")
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
                
                # 每个热搜之间空一行（在链接后面空行）
                if index < len(hot_items[:20]) - 1:  # 不是最后一个
                    content += "\n"
            
            # 添加生成时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content += f"*自动生成于 {current_time}*"
            
            return content
            
        except Exception as e:
            print(f"❌ 格式化微博内容异常: {e}")
            return None
    
    def _format_news_content(self, news_data):
        """格式化新闻内容"""
        try:
            news_items = news_data.get('data', [])
            
            content = "# 今日新闻\n\n"
            
            # 添加前10条新闻
            for index, item in enumerate(news_items[:10]):
                title = item.get('title', '')
                source = item.get('source', '')
                time_str = item.get('time', '')
                digest = item.get('digest', '')
                url = item.get('pc_url', '') or item.get('m_url', '')
                imgsrc = item.get('imgsrc', '')
                
                content += f"## {index + 1}. {title}\n"
                content += f"**来源**: {source}\n"
                
                if time_str:
                    content += f"**时间**: {time_str}\n"
                
                if digest:
                    content += f"**摘要**: {digest}\n"
                
                content += "\n"
                
                # 添加图片
                if imgsrc:
                    content += f"![新闻图片]({imgsrc})\n\n"
                
                # 添加原文链接
                if url:
                    content += f"[阅读原文]({url})\n\n"
                
                content += "---\n\n"
            
            # 添加生成时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content += f"*自动生成于 {current_time}*"
            
            return content
            
        except Exception as e:
            print(f"❌ 格式化新闻内容异常: {e}")
            return None
    
    def _format_acg_content(self, acg_data):
        """格式化美图内容"""
        try:
            image_data = acg_data.get('data', {})
            image_url = image_data.get('url', '')
            width = image_data.get('width', '')
            height = image_data.get('height', '')
            
            content = "# 每日美图\n\n"
            
            if image_url:
                content += f"![每日美图]({image_url})\n\n"
                if width and height:
                    content += f"**图片尺寸**: {width} × {height}\n\n"
            
            # 添加生成时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content += f"*自动生成于 {current_time}*"
            
            return content
            
        except Exception as e:
            print(f"❌ 格式化美图内容异常: {e}")
            return None
    
    def get_daily_content(self):
        """获取每日内容（知乎日报 + 新闻 + 微博热搜 + 美图）"""
        print("🔄 开始获取每日内容...")
        
        # 获取知乎日报
        zhihu_content = self.fetch_zhihu_daily()
        
        # 获取新闻
        news_content = self.fetch_news()
        
        # 获取微博热搜
        weibo_content = self.fetch_weibo_hot()
        
        # 获取美图
        acg_content = self.fetch_acg_image()
        
        # 构建完整的帖子内容
        full_content = "置顶广告位\n\n"
        full_content += "## 📰 知乎日报\n\n"
        
        if zhihu_content:
            full_content += zhihu_content + "\n\n"
        else:
            full_content += "今日知乎日报内容获取失败，请稍后重试。\n\n"
        
        full_content += "## 📰 新闻\n\n"
        if news_content:
            full_content += news_content + "\n\n"
        else:
            full_content += "今日新闻内容获取失败，请稍后重试。\n\n"
        
        full_content += "## 🔥 微博热搜\n\n"
        if weibo_content:
            full_content += weibo_content + "\n\n"
        else:
            full_content += "今日微博热搜内容获取失败，请稍后重试。\n\n"
        
        full_content += "## ❤ ACG动漫图片\n\n"
        if acg_content:
            full_content += acg_content + "\n\n"
        else:
            full_content += "今日美图内容获取失败，请稍后重试。\n\n"
        
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

今日新闻内容获取失败，请稍后重试。

## 🔥 微博热搜

今日微博热搜内容获取失败，请稍后重试。

## 🖼️ 美图

今日美图内容获取失败，请稍后重试。

广告位

！！！turkeybot运行出错，请联系turkey1024

*本帖由 TurkeyBot 自动生成*"""
