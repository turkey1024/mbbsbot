# github_login_test.py
import requests
import json
import base64
from io import BytesIO

class GitHubBBSTurkeyBot:
    def __init__(self):
        # 硬编码配置
        self.base_url = "https://mk48by049.mbbs.cc"
        self.api_base = f"{self.base_url}/bbs"
        self.username = "turkeybot"
        self.password = "passwordbotonly"
        
        # API 端点
        self.captcha_url = f"{self.api_base}/login/captcha"
        self.login_url = f"{self.api_base}/login"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Termux) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/login',
            'Content-Type': 'application/json'
        })
        
        # 初始化 ddddocr
        try:
            import ddddocr
            self.ocr = ddddocr.DdddOcr(show_ad=False)
            print("✅ ddddocr 初始化成功")
        except ImportError:
            print("❌ ddddocr 未安装")
            self.ocr = None
    
    def svg_to_png_cairosvg(self, svg_content: str) -> bytes:
        """使用 cairosvg 将 SVG 转换为 PNG"""
        try:
            import cairosvg
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=300,
                output_height=100,
                dpi=200
            )
            return png_data
        except Exception as e:
            print(f"❌ cairosvg 转换失败: {e}")
            return None
    
    def get_login_captcha(self):
        """获取登录验证码"""
        try:
            print("📷 获取登录验证码...")
            response = self.session.get(self.captcha_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                captcha_data = data.get('data', {})
                captcha_id = captcha_data.get('id')
                svg_data = captcha_data.get('svg')
                
                if captcha_id and svg_data:
                    print(f"✅ 验证码获取成功, ID: {captcha_id}")
                    return captcha_id, svg_data
            
            print("❌ 验证码获取失败")
            return None, None
            
        except Exception as e:
            print(f"❌ 获取验证码错误: {e}")
            return None, None
    
    def recognize_captcha(self, svg_data: str) -> str:
        """识别验证码"""
        if not self.ocr:
            print("❌ ddddocr 未初始化")
            return "FAIL"
            
        try:
            # 转换 SVG 为 PNG
            png_data = self.svg_to_png_cairosvg(svg_data)
            if not png_data:
                return "FAIL"
            
            # 识别验证码
            result = self.ocr.classification(png_data)
            
            # 清理结果，只保留字母数字
            import re
            cleaned = re.sub(r'[^A-Za-z0-9]', '', result)
            
            if cleaned:
                print(f"✅ 验证码识别结果: {cleaned.upper()}")
                return cleaned.upper()
            else:
                return "FAIL"
                
        except Exception as e:
            print(f"❌ 验证码识别失败: {e}")
            return "FAIL"
    
    def login(self):
        """执行登录"""
        print("🚀 开始登录流程...")
        print(f"📝 用户名: {self.username}")
        
        # 1. 获取验证码
        captcha_id, svg_data = self.get_login_captcha()
        if not captcha_id:
            return False, "获取验证码失败"
        
        # 2. 识别验证码
        captcha_text = self.recognize_captcha(svg_data)
        if captcha_text == "FAIL":
            return False, "验证码识别失败"
        
        # 3. 执行登录
        try:
            login_data = {
                "username": self.username,
                "password": self.password,
                "captcha_id": captcha_id,
                "captcha_text": captcha_text
            }
            
            print(f"🔐 提交登录请求...")
            response = self.session.post(self.login_url, json=login_data, timeout=15)
            
            print(f"📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 登录响应: {json.dumps(result, ensure_ascii=False)}")
                
                # 检查登录成功标志
                if 'id' in result or 'token' in result:
                    print("🎉 登录成功!")
                    return True, result
                else:
                    error_msg = result.get('message', '未知错误')
                    print(f"❌ 登录失败: {error_msg}")
                    return False, error_msg
            else:
                print(f"❌ HTTP 错误: {response.status_code}")
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"❌ 登录请求异常: {e}")
            return False, str(e)
    
    def test_api_connectivity(self):
        """测试 API 连通性"""
        try:
            print("🔗 测试 API 连通性...")
            response = self.session.get(f"{self.api_base}/login/captcha", timeout=10)
            print(f"📡 API 响应状态: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API 连通性测试失败: {e}")
            return False

def main():
    print("=" * 50)
    print("🤖 MBBS TurkeyBot GitHub Actions 登录测试")
    print("=" * 50)
    
    # 创建机器人实例
    bot = GitHubBBSTurkeyBot()
    
    # 测试连通性
    if not bot.test_api_connectivity():
        print("❌ API 无法访问，退出测试")
        return
    
    # 执行登录
    success, result = bot.login()
    
    if success:
        print("🎉 登录测试通过！")
        # 这里可以继续发帖逻辑
    else:
        print(f"💥 登录测试失败: {result}")

if __name__ == "__main__":
    main()
