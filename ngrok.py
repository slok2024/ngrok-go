import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser
import atexit

class ModernNgrokGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ngrok Tunnel Pro")
        self.root.geometry("500x400") # 稍微调高一点高度
        self.root.configure(bg="#F5F7FA")
        self.kernel_process = None
        
        self.cleanup_existing_kernels()

        # --- 界面初始化 ---
        self.header = tk.Frame(root, bg="#2D3436", height=5).pack(fill="x")
        self.main_frame = tk.Frame(root, bg="#F5F7FA", padx=30, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        tk.Label(self.main_frame, text="内网穿透管理终端", font=("Microsoft YaHei UI", 16, "bold"), 
                 bg="#F5F7FA", fg="#2D3436").pack(pady=(0, 10))

        # --- 新增：显示当前检测到的内核版本 ---
        self.arch_info = self.get_arch_string()
        tk.Label(self.main_frame, text=f"系统架构: {self.arch_info}", font=("Microsoft YaHei UI", 8), 
                 bg="#F5F7FA", fg="#95A5A6").pack()

        # 端口输入
        input_frame = tk.Frame(self.main_frame, bg="#F5F7FA")
        input_frame.pack(fill="x", pady=10)
        tk.Label(input_frame, text="转发端口:", font=("Microsoft YaHei UI", 10), bg="#F5F7FA").pack(side="left")
        self.port_var = tk.StringVar(value="80")
        self.port_entry = tk.Entry(input_frame, textvariable=self.port_var, font=("Consolas", 12), relief="flat", highlightthickness=1, highlightbackground="#DCDDE1")
        self.port_entry.pack(side="left", padx=10, fill="x", expand=True)

        # 状态指示
        self.status_circle = tk.Canvas(self.main_frame, width=12, height=12, bg="#F5F7FA", highlightthickness=0)
        self.circle = self.status_circle.create_oval(2, 2, 10, 10, fill="#DCDDE1")
        self.status_circle.pack(pady=(5, 0))
        self.status_text = tk.Label(self.main_frame, text="等待启动", font=("Microsoft YaHei UI", 9), bg="#F5F7FA", fg="#7F8C8D")
        self.status_text.pack()

        # URL 显示
        self.url_display = tk.Text(self.main_frame, height=2, font=("Consolas", 10), bd=0, bg="#EBEEF2", padx=10, pady=10, state="disabled")
        self.url_display.pack(fill="x", pady=15)

        # 按钮区
        btn_frame = tk.Frame(self.main_frame, bg="#F5F7FA")
        btn_frame.pack(fill="x", pady=5)

        self.start_btn = tk.Button(btn_frame, text="启动服务", command=self.start_service, bg="#0984E3", fg="white", font=("Microsoft YaHei UI", 10, "bold"), relief="flat", cursor="hand2")
        self.start_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.open_btn = tk.Button(btn_frame, text="浏览器打开", command=self.open_browser, bg="#DCDDE1", fg="#636E72", font=("Microsoft YaHei UI", 10), relief="flat", cursor="hand2", state="disabled")
        self.open_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.stop_btn = tk.Button(btn_frame, text="停止", command=self.stop_service, bg="#DCDDE1", fg="#636E72", font=("Microsoft YaHei UI", 10), relief="flat", cursor="hand2", state="disabled")
        self.stop_btn.pack(side="left", expand=True, fill="x", padx=2)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def get_arch_string(self):
        """返回架构描述字符串"""
        arch = os.environ.get('PROCESSOR_ARCHITECTURE', '').upper()
        if arch == 'AMD64' or os.environ.get('PROCESSOR_ARCHITEW6432'):
            return "Windows x64 (使用 64位内核)"
        return "Windows x86 (使用 32位内核)"

    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def cleanup_existing_kernels(self):
        # 增加参数确保 taskkill 本身也不弹窗
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.call('taskkill /f /t /im kernel_x64.exe', startupinfo=si, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        subprocess.call('taskkill /f /t /im kernel_x86.exe', startupinfo=si, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    def get_kernel_path(self):
        arch = os.environ.get('PROCESSOR_ARCHITECTURE', '').upper()
        is_64bit = arch == 'AMD64' or os.environ.get('PROCESSOR_ARCHITEW6432')
        kernel_name = "kernel_x64.exe" if is_64bit else "kernel_x86.exe"
        return self.get_resource_path(kernel_name)

    def start_service(self):
        kernel = self.get_kernel_path()
        if not os.path.exists(kernel):
            messagebox.showerror("错误", f"找不到内核: {os.path.basename(kernel)}")
            return

        self.start_btn.config(state="disabled", bg="#DCDDE1")
        self.stop_btn.config(state="normal", bg="#FF7675", fg="white")
        self.status_text.config(text="连接中...", fg="#0984E3")
        self.status_circle.itemconfig(self.circle, fill="#F1C40F")
        
        threading.Thread(target=self.run_thread, args=(kernel, self.port_var.get()), daemon=True).start()

    def run_thread(self, kernel, port):
        try:
            # --- 核心：彻底禁止黑框闪烁的配置 ---
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 0 # SW_HIDE

            self.kernel_process = subprocess.Popen(
                [kernel, port], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, 
                startupinfo=si, # 使用 startupinfo 代替 creationflags
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            # -----------------------------------

            for line in self.kernel_process.stdout:
                if "STATUS:CONNECTED" in line:
                    self.root.after(0, lambda: self.update_status("服务运行中", "#27AE60", "#2ECC71"))
                if "URL:" in line:
                    url = line.split("URL:")[1].strip()
                    self.root.after(0, lambda u=url: self.update_url(u))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", str(e)))

    def update_status(self, text, color, circle_color):
        self.status_text.config(text=text, fg=color)
        self.status_circle.itemconfig(self.circle, fill=circle_color)

    def update_url(self, url):
        self.url_display.config(state="normal")
        self.url_display.delete(1.0, tk.END)
        self.url_display.insert(tk.END, url)
        self.url_display.config(state="disabled")
        self.open_btn.config(state="normal", bg="#6C5CE7", fg="white")
        self.root.clipboard_clear()
        self.root.clipboard_append(url)

    def open_browser(self):
        url = self.url_display.get(1.0, tk.END).strip()
        if url: webbrowser.open(url)

    def stop_service(self):
        if self.kernel_process:
            self.kernel_process.terminate()
            self.kernel_process = None
        self.cleanup_existing_kernels()
        self.update_status("服务已停止", "#7F8C8D", "#DCDDE1")
        self.start_btn.config(state="normal", bg="#0984E3")
        self.open_btn.config(state="disabled", bg="#DCDDE1", fg="#636E72")
        self.stop_btn.config(state="disabled", bg="#DCDDE1", fg="#636E72")

    def on_closing(self):
        self.stop_service()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernNgrokGUI(root)
    root.mainloop()