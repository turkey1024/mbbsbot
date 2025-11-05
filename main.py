# main.py
from login import BBSTurkeyBotLogin
from post import BBSPoster
from api import ContentAPI
import time
from datetime import datetime

def main():
    print("=" * 60)
    print("🤖 MBBS TurkeyBot 每日内容推送")
    print("=" * 60)
    
    # 配置
    base_url = "https://mk48by049.mbbs.cc"
    username = "turkeybot"
    password = "passwordbotonly"
    chat_category_id = 2
    
    # 1. 获取每日内容
    print("📝 正在获取每日内容...")
    content_api = ContentAPI()
    post_content = content_api.get_daily_content()
    
    if not post_content:
        print("❌ 内容获取失败，停止执行")
        return False
    
    # 生成标题（包含日期）
    current_date = datetime.now().strftime('%Y-%m-%d')
    post_title = f"每日内容推送 {current_date}"
    
    print(f"📄 帖子标题: {post_title}")
    print(f"📝 内容长度: {len(post_content)} 字符")
    
    # 2. 登录
    login_bot = BBSTurkeyBotLogin(base_url, username, password)
    start_time = time.time()
    login_success, login_result, session = login_bot.login_with_retry()
    end_time = time.time()
    
    if not login_success:
        print("💥 登录失败，停止测试")
        return False
    
    print(f"⏱️ 登录耗时: {end_time - start_time:.2f} 秒")
    
    # 3. 获取 token 和用户信息
    user_data = login_result.get('data', {})
    token = user_data.get('token')
    user_id = user_data.get('id')
    
    if not token:
        print("❌ 未获取到 token，停止测试")
        return False
    
    print(f"🔑 获取到 Token: {token[:10]}...")
    print(f"👤 用户 ID: {user_id}")
    
    # 4. 发帖
    poster = BBSPoster(session, base_url)
    print(f"🎯 使用聊天板块ID: {chat_category_id}")
    
    print(f"\n📮 准备发帖...")
    print(f"  标题: {post_title}")
    print(f"  板块ID: {chat_category_id}")
    
    post_success, post_result = poster.create_thread(token, chat_category_id, post_title, post_content)
    
    if post_success:
        print("🎉 每日内容推送成功！")
        return True
    else:
        print("💥 发帖失败")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 60)
    print("📊 最终执行结果")
    print("=" * 60)
    print(f"✅ 状态: {'成功' if success else '失败'}")
    
    if success:
        print("🎉 每日内容推送完成！")
        print("📍 帖子已发布到聊天板块")
    else:
        print("💥 执行失败，请检查日志")
