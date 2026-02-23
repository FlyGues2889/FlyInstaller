import tkinter as tk
import customtkinter as ctk
import subprocess
import os
import threading
from pathlib import Path
import sys
import time

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLORS = {
    "global_bg": "#EFF4F9",      # 全局画布背景
    "panel_bg": "#f0f0f2",       # 右侧功能面板背景（保持参考图样式）
    "content_bg": "#ffffff",     # 输入框/列表/日志背景
    "text_primary": "#000000",   # 大标题/小标题文字
    "text_secondary": "#666666", # 说明文字
    "btn_primary_bg": "#1a365d", # 开始安装按钮背景
    "btn_primary_text": "#ffffff",# 开始安装按钮文字
    "btn_cancel_text": "#1a365d", # 取消按钮文字
    "progress_bg": "#e0e0e0",    # 进度条背景
    "progress_fg": "#1a365d",    # 进度条进度色
    "border_color": "#e5e5e7",   # 边框色
    "left_bg": "#EFF4F9"         # 左侧区域背景
}

# 间距定义（严格按要求）
PADDING = {
    "panel_pad": 36,             # 面板内边距
    "title_to_subtitle": 16,      # 大标题到小标题
    "subtitle_to_content": 6,    # 小标题到内容
    "section_gap": 6            # 区域之间间隔
}

class FlyInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("FlyInstaller")
        self.root.geometry("960x760") 
        self.root.resizable(False, False)
        
        # 获取屏幕宽高
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # 计算窗口居中坐标
        window_width = 960
        window_height = 760
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        # 设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ========== 关键：字体平滑配置 + 系统默认字体 ==========
        # 开启Windows字体平滑（抗锯齿）
        if os.name == "nt":
            self.root.tk.call("tk", "scaling", 1.0)  # 适配系统DPI
            # 开启字体抗锯齿（Windows专属）
            self.root.tk.call("set", "tk_useSystemFontSettings", "1")
        
        # 获取系统默认字体配置
        self.default_font = tk.font.nametofont("TkDefaultFont")
        # 先获取默认字体配置，再修改weight（避免参数重复）
        font_config = self.default_font.configure()
        font_config["weight"] = "bold"
        self.bold_font = tk.font.Font(** font_config)
        
        # 关键：显式设置root窗口背景
        self.root.configure(fg_color=COLORS["global_bg"])
        
        # 初始化变量
        self.install_files = []
        self.is_installing = False
        self.cancel_flag = False
        self.exe_silent_params = ["/S", "/verysilent", "/silent", "/quiet", "/qn", "/norestart"]
        
        # ========== 新增：安装目标目录默认值 ==========
        self.target_path_var = tk.StringVar(value="C:\\Program Files\\")  # 默认安装路径
        # 获取默认package路径（适配exe/源码运行）
        default_package_path = self.get_default_package_path()
        default_path = default_package_path if os.path.exists(default_package_path) else "当前未选择文件夹（默认路径./package不存在）"
        self.path_var = tk.StringVar(value=default_path)
        
        # 创建整体布局
        self.create_main_layout()
        
        # 初始化日志
        self.add_log("✅ 程序已启动，等待选择安装包文件夹...")
        
        # 自动加载默认文件夹
        self.load_default_folder()
    
    # ========== 新增：获取默认package路径（适配exe运行） ==========
    def get_default_package_path(self):
        if getattr(sys, 'frozen', False):
            # exe运行时：获取exe文件所在目录（而非临时解压目录）
            base_path = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # 源码运行时：获取脚本所在目录
            base_path = os.path.dirname(os.path.abspath(__file__))
        # 返回应用目录下的package文件夹
        return os.path.join(base_path, "package")
    
    def create_main_layout(self):
        # 主容器（左右布局）
        main_container = ctk.CTkFrame(
            self.root,
            fg_color=COLORS["global_bg"],
            border_width=0
        )
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. 左侧图标区域（显示📦 emoji）
        left_frame = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["left_bg"],
            border_width=0,
            width=250
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))
        left_frame.pack_propagate(False)
        
        # 显示📦 emoji（使用系统默认字体，仅调整大小）
        emoji_label = ctk.CTkLabel(
            left_frame,
            text="📦",
            # 去掉family，使用系统默认字体
            font=ctk.CTkFont(size=120),
            text_color="#1a365d"
        )
        emoji_label.pack(expand=True)
        
        # 显示版本号行
        version_label = ctk.CTkLabel(
            left_frame,
            text="v0.1.1 By Lvi_Fly",
            font=ctk.CTkFont(size=10),
            text_color="#868686"
        )
        version_label.pack(side=tk.LEFT, expand=True, padx=100, pady=10)
        
        # 2. 右侧功能面板（核心区域）
        right_panel = ctk.CTkFrame(
            main_container,
            fg_color=COLORS["panel_bg"],
            corner_radius=12,
            border_width=2,
            border_color="#e0e0e0",
            bg_color=COLORS["global_bg"]
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 面板内边距36px
        panel_inner = ctk.CTkFrame(
            right_panel,
            fg_color="transparent",
            border_width=0
        )
        panel_inner.pack(fill=tk.BOTH, expand=True, padx=PADDING["panel_pad"], pady=PADDING["panel_pad"])
        
        # ========== 2.1 大标题 ==========
        title_label = ctk.CTkLabel(
            panel_inner,
            text="FlyInstaller",
            # 仅保留size和weight，使用系统默认字体
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        title_label.pack(anchor=tk.W, pady=(0, PADDING["title_to_subtitle"]))
        
        # ========== 2.2 安装包目录区域 ==========
        # 小标题
        dir_subtitle = ctk.CTkLabel(
            panel_inner,
            text="安装包目录",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_primary"]
        )
        dir_subtitle.pack(anchor=tk.W, pady=(0, PADDING["subtitle_to_content"]))
        
        # 路径选择行（输入框+按钮）
        dir_frame = ctk.CTkFrame(
            panel_inner,
            fg_color="transparent",
            border_width=0
        )
        dir_frame.pack(fill=tk.X, pady=(0, PADDING["section_gap"]))
        
        path_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self.path_var,
            font=ctk.CTkFont(size=12),
            state="readonly",
            border_width=0,
            corner_radius=6,
            fg_color="#F0F0F2",
            text_color=COLORS["text_secondary"],
            height=38
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        select_btn = ctk.CTkButton(
            dir_frame,
            text="更改",
            command=self.select_folder,
            font=ctk.CTkFont(size=12),
            fg_color="#f8f8f9",
            text_color=COLORS["text_primary"],
            border_color=COLORS["border_color"],
            border_width=1,
            corner_radius=6,
            height=38,
            width=80,
            hover_color="#e0e0e0"
        )
        select_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # ========== 新增：2.3 安装目标目录区域 ==========
        # 小标题
        target_subtitle = ctk.CTkLabel(
            panel_inner,
            text="目标目录",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_primary"]
        )
        target_subtitle.pack(anchor=tk.W, pady=(PADDING["section_gap"], PADDING["subtitle_to_content"]))
        
        # 目标路径选择行（输入框+按钮）
        target_frame = ctk.CTkFrame(
            panel_inner,
            fg_color="transparent",
            border_width=0
        )
        target_frame.pack(fill=tk.X, pady=(0, PADDING["section_gap"]))
        
        target_entry = ctk.CTkEntry(
            target_frame,
            textvariable=self.target_path_var,
            font=ctk.CTkFont(size=12),
            state="readonly",
            border_width=0,
            corner_radius=6,
            fg_color="#F0F0F2",
            text_color=COLORS["text_secondary"],
            height=38
        )
        target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        target_select_btn = ctk.CTkButton(
            target_frame,
            text="更改",
            command=self.select_target_folder,
            font=ctk.CTkFont(size=12),
            fg_color="#f8f8f9",
            text_color=COLORS["text_primary"],
            border_color=COLORS["border_color"],
            border_width=1,
            corner_radius=6,
            height=38,
            width=80,
            hover_color="#e0e0e0"
        )
        target_select_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # ========== 2.4 安装列表区域 ==========
        # 小标题
        list_subtitle = ctk.CTkLabel(
            panel_inner,
            text="安装列表",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_primary"]
        )
        list_subtitle.pack(anchor=tk.W, pady=(PADDING["section_gap"], PADDING["subtitle_to_content"]))
        
        # 说明文字
        list_note = ctk.CTkLabel(
            panel_inner,
            text="自动识别出的 .exe 和 .msi 文件会显示在下方",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        )
        list_note.pack(anchor=tk.W, pady=(0, PADDING["subtitle_to_content"]))
        
        # 列表框（原生tk组件，使用系统默认字体+平滑）
        list_frame = ctk.CTkFrame(
            panel_inner,
            fg_color=COLORS["content_bg"],
            border_color=COLORS["border_color"],
            border_width=1,
            corner_radius=6,
            height=100
        )
        list_frame.pack(fill=tk.X, pady=(0, PADDING["section_gap"]))
        list_frame.pack_propagate(False)
        
        self.file_listbox = tk.Listbox(
            list_frame,
            # 使用系统默认字体，指定大小
            font=(self.default_font.actual()["family"], 14),
            selectmode=tk.EXTENDED,
            bg=COLORS["content_bg"],
            fg=COLORS["text_primary"],
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            # 开启列表框字体平滑
            activestyle="none"
        )
        # 强制开启抗锯齿（Windows）
        if os.name == "nt":
            self.file_listbox.configure(font=("Segoe UI", 14))  # Windows默认无衬线字体
        self.file_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # ========== 2.5 日志输出区域 ==========
        # 小标题
        log_subtitle = ctk.CTkLabel(
            panel_inner,
            text="输出",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_primary"]
        )
        log_subtitle.pack(anchor=tk.W, pady=(PADDING["section_gap"], PADDING["subtitle_to_content"]))
        
        # 日志框（原生tk组件，字体优化）
        log_frame = ctk.CTkFrame(
            panel_inner,
            fg_color=COLORS["content_bg"],
            border_color=COLORS["border_color"],
            border_width=1,
            corner_radius=6,
            height=100
        )
        log_frame.pack(fill=tk.X, pady=(0, PADDING["panel_pad"]))
        log_frame.pack_propagate(False)
        
        self.log_text = tk.Text(
            log_frame,
            # 使用系统默认字体
            font=(self.default_font.actual()["family"], 14),
            bg=COLORS["content_bg"],
            fg=COLORS["text_primary"],
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        # Windows下强制使用Segoe UI（系统默认，自带抗锯齿）
        if os.name == "nt":
            self.log_text.configure(font=("Segoe UI", 14))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        # ========== 2.6 进度条 ==========
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            panel_inner,
            variable=self.progress_var,
            height=6,
            corner_radius=3,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["progress_fg"]
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, PADDING["panel_pad"]))
        
        # ========== 2.7 按钮区域 ==========
        btn_frame = ctk.CTkFrame(
            panel_inner,
            fg_color="transparent",
            border_width=0
        )
        btn_frame.pack(fill=tk.X, anchor=tk.E)
        
        self.cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            command=self.cancel_install,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=COLORS["btn_cancel_text"],
            border_width=0,
            corner_radius=6,
            height=38,
            width=40,
             hover_color="#F0F0F2"

        )
        self.cancel_btn.pack(side=tk.LEFT, padx=0)

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="开始批量安装",
            command=self.start_install,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLORS["btn_primary_bg"],
            text_color=COLORS["btn_primary_text"],
            border_width=0,
            corner_radius=6,
            height=38,
            width=120,
            hover_color="#2c4a78"
        )
        self.start_btn.pack(side=tk.RIGHT)
    
    # ========== 新增：选择安装目标目录 ==========
    def select_target_folder(self):
        """选择安装目标目录"""
        target_folder = ctk.filedialog.askdirectory(title="选择安装目标目录")
        if target_folder:
            self.target_path_var.set(target_folder)
            self.add_log(f"📁 已选择安装目标目录：{target_folder}")
    
    def select_folder(self):
        """选择文件夹并识别安装包"""
        self.add_log("📂 开始选择安装包文件夹...")
        folder_path = ctk.filedialog.askdirectory(title="选择安装包文件夹")
        if not folder_path:
            self.add_log("❌ 取消了文件夹选择")
            return
        
        self.add_log(f"📁 已选择文件夹：{folder_path}")
        self.path_var.set(folder_path)
        self.install_files.clear()
        self.file_listbox.delete(0, tk.END)
        
        try:
            file_count = 0
            for file in os.listdir(folder_path):
                file_path = Path(folder_path) / file
                if file_path.suffix.lower() in [".exe", ".msi"]:
                    self.install_files.append(str(file_path))
                    self.file_listbox.insert(tk.END, file)
                    file_count += 1
                    self.add_log(f"🔍 识别到安装包：{file}")
            
            if file_count == 0:
                self.add_log("⚠️ 未在该文件夹中找到.exe或.msi安装包")
            else:
                self.add_log(f"✅ 共识别到 {file_count} 个安装包")
        except Exception as e:
            self.add_log(f"❌ 读取文件夹失败：{str(e)}")
    
    # ========== 新增：加载默认package文件夹 ==========
    def load_default_folder(self):
        """自动加载默认路径./package的安装包"""
        default_package_path = self.get_default_package_path()
        if not os.path.exists(default_package_path):
            self.add_log(f"⚠️ 默认路径 {default_package_path} 不存在，需手动选择文件夹")
            return
        
        self.add_log(f"📁 自动加载默认文件夹：{default_package_path}")
        self.path_var.set(default_package_path)
        self.install_files.clear()
        self.file_listbox.delete(0, tk.END)
        
        try:
            file_count = 0
            for file in os.listdir(default_package_path):
                file_path = Path(default_package_path) / file
                if file_path.suffix.lower() in [".exe", ".msi"]:
                    self.install_files.append(str(file_path))
                    self.file_listbox.insert(tk.END, file)
                    file_count += 1
                    self.add_log(f"🔍 识别到安装包：{file}")
            
            if file_count == 0:
                self.add_log("⚠️ 默认文件夹中未找到.exe或.msi安装包")
            else:
                self.add_log(f"✅ 共识别到 {file_count} 个安装包")
        except Exception as e:
            self.add_log(f"❌ 读取默认文件夹失败：{str(e)}")
    
    def add_log(self, message):
        """线程安全的日志添加"""
        def update_log():
            try:
                self.log_text.config(state=tk.NORMAL)
                timestamp = time.strftime("[%H:%M:%S]")
                self.log_text.insert(tk.END, f"{timestamp} {message}\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
                self.root.update()
            except Exception as e:
                print(f"日志更新失败：{e}")
        
        self.root.after(10, update_log)
    
    def update_progress(self, value):
        """线程安全的进度条更新"""
        def update_ui():
            self.progress_var.set(value)
            self.root.update()
        
        self.root.after(10, update_ui)
    
    def cancel_install(self):
        """取消安装"""
        self.cancel_flag = True
        self.add_log("⚠️ 触发取消安装操作，将终止后续安装")
        self.root.after(10, lambda: self.cancel_btn.configure(state=tk.DISABLED))
    
    def safe_decode(self, byte_data):
        """安全解码字节流"""
        if not byte_data:
            return ""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        for encoding in encodings:
            try:
                return byte_data.decode(encoding)
            except:
                continue
        return byte_data.decode('utf-8', errors='ignore')
    
    def install_file(self, file_path):
        """安装单个文件（适配安装目标目录）"""
        try:
            self.add_log(f"\n📦 开始安装：{os.path.basename(file_path)}")
            self.add_log(f"📂 文件路径：{file_path}")
            # 新增：打印安装目标目录
            target_path = self.target_path_var.get()
            self.add_log(f"📌 安装目标目录：{target_path}")

            success = False

            # --------------------------
            # 1. 处理 .exe 静默安装（适配目标路径）
            # --------------------------
            if file_path.lower().endswith(".exe"):
                # 常见的EXE安装路径参数（不同安装包可能不同）
                exe_target_params = [
                    f"/DIR={target_path}",  # Inno Setup 安装包
                    f"/INSTALLDIR={target_path}",  # NSIS 安装包
                    f"-dir {target_path}",  # 部分自定义安装包
                ]
                # 组合静默参数+目标路径参数
                for silent_param in self.exe_silent_params:
                    if self.cancel_flag:
                        break
                    # 先试带目标路径的参数
                    for target_param in exe_target_params:
                        cmd = [file_path, silent_param, target_param]
                        self.add_log(f"🔧 尝试执行：{' '.join(cmd)}")
                        
                        try:
                            result = subprocess.run(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=300,
                                shell=True,
                                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
                            )
                            stdout = self.safe_decode(result.stdout)
                            stderr = self.safe_decode(result.stderr)

                            # 成功判断：0=成功，259=仍在运行（也算成功）
                            if result.returncode in (0, 259):
                                self.add_log(f"✅ 参数 {silent_param} + {target_param} 静默安装成功")
                                if stdout:
                                    self.add_log(f"📝 输出：{stdout[:300]}")
                                success = True
                                break
                            elif result.returncode in (1, 2):
                                self.add_log(f"⚠️ 参数 {silent_param} + {target_param} 触发交互安装（需手动完成）")
                                success = True
                                break
                            else:
                                self.add_log(f"⚠️ 参数组合失败，返回码：{result.returncode}")
                                if stderr:
                                    self.add_log(f"❌ 错误：{stderr[:300]}")
                        except Exception as e:
                            self.add_log(f"⚠️ 参数组合执行异常：{str(e)}")
                    if success:
                        break
                
                # 所有带目标路径的参数都失败 → 试仅静默参数
                if not success:
                    for silent_param in self.exe_silent_params:
                        if self.cancel_flag:
                            break
                        cmd = [file_path, silent_param]
                        self.add_log(f"🔧 尝试仅静默参数：{' '.join(cmd)}")
                        try:
                            result = subprocess.run(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                timeout=300,
                                shell=True
                            )
                            if result.returncode in (0, 259, 1, 2):
                                self.add_log(f"✅ 仅静默参数 {silent_param} 安装成功（使用默认路径）")
                                success = True
                                break
                            else:
                                self.add_log(f"⚠️ 仅静默参数失败，返回码：{result.returncode}")
                        except Exception as e:
                            self.add_log(f"⚠️ 仅静默参数执行异常：{str(e)}")

                # 所有静默参数都失败 → 手动运行
                if not success:
                    self.add_log("⚠️ 所有静默参数失败，尝试手动安装")
                    cmd = [file_path]
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300,
                        shell=True
                    )
                    success = result.returncode not in (-1, 127)

            # --------------------------
            # 2. 处理 .msi 静默安装（适配目标路径）
            # --------------------------
            elif file_path.lower().endswith(".msi"):
                try:
                    # 管理员权限检测（必须）
                    import ctypes
                    try:
                        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
                        if not is_admin:
                            self.add_log("❌ 错误：当前无管理员权限，MSI 无法安装！")
                            self.add_log("ℹ️ 请右键程序 → 以管理员身份运行")
                            return False
                    except Exception as e:
                        self.add_log(f"⚠️ 管理员检测异常：{str(e)}")

                    # 路径处理（彻底解决引号/空格问题）
                    msi_path = os.path.abspath(file_path)
                    if not os.path.exists(msi_path):
                        self.add_log(f"❌ MSI 文件不存在：{msi_path}")
                        return False

                    # 构建 MSI 命令（带目标路径 INSTALLDIR）
                    cmd = [
                        "msiexec.exe",
                        "/i", f'"{msi_path}"',
                        f'INSTALLDIR="{target_path}"',  # 新增：指定MSI安装路径
                        "/qb",                  # 半静默（显示进度，比 /qn 稳定）
                        "/norestart"            # 不自动重启
                    ]
                    self.add_log(f"🔧 MSI 命令（带目标路径）：{' '.join(cmd)}")

                    # 执行 MSI 安装
                    result = subprocess.run(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=300,
                        shell=True,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
                    )
                    stdout = self.safe_decode(result.stdout)
                    stderr = self.safe_decode(result.stderr)

                    # MSI 成功返回码（微软官方）
                    msi_success = [0, 1641, 3010, 259]
                    if result.returncode in msi_success:
                        self.add_log(f"✅ MSI 安装成功，返回码：{result.returncode}")
                        if stdout:
                            self.add_log(f"📝 MSI 输出：{stdout[:300]}")
                        success = True
                    else:
                        self.add_log(f"❌ MSI 安装失败（带目标路径），返回码：{result.returncode}")
                        if stderr:
                            self.add_log(f"❌ MSI 错误：{stderr[:500]}")

                        # 失败重试：去掉目标路径，用默认路径
                        self.add_log("ℹ️ 重试：使用默认安装路径")
                        retry_cmd = [
                            "msiexec.exe",
                            "/i", f'"{msi_path}"',
                            "/qb",
                            "/norestart"
                        ]
                        self.add_log(f"🔧 重试命令：{' '.join(retry_cmd)}")
                        retry_result = subprocess.run(
                            retry_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=300,
                            shell=True
                        )
                        if retry_result.returncode in msi_success:
                            self.add_log("✅ MSI 重试安装成功（默认路径）")
                            success = True
                        else:
                            self.add_log(f"❌ 重试失败，返回码：{retry_result.returncode}")
                            if self.safe_decode(retry_result.stderr):
                                self.add_log(f"❌ 重试错误：{self.safe_decode(retry_result.stderr)[:500]}")

                except Exception as e:
                    self.add_log(f"❌ MSI 执行异常：{str(e)}")

            # --------------------------
            # 3. 最终结果返回
            # --------------------------
            if success:
                self.add_log(f"✅ 安装完成：{os.path.basename(file_path)}")
                return True
            else:
                self.add_log(f"❌ 安装失败：{os.path.basename(file_path)}")
                self.add_log("ℹ️ 建议：手动运行该安装包，或检查管理员权限")
                return False

        except Exception as e:
            self.add_log(f"❌ 安装异常：{os.path.basename(file_path)} - {str(e)}")
            return False
        
    def batch_install(self):
        """批量安装核心逻辑"""
        total_files = len(self.install_files)
        if total_files == 0:
            self.add_log("❌ 没有待安装的文件，请先选择包含安装包的文件夹")
            self.root.after(10, lambda: self.reset_ui())
            return
        
        self.cancel_flag = False
        success_count = 0
        
        self.add_log(f"\n🚀 开始批量安装，共 {total_files} 个安装包")
        self.add_log("==================================================")
        
        for index, file_path in enumerate(self.install_files):
            if self.cancel_flag:
                self.add_log("\n🛑 检测到取消信号，终止安装流程")
                break
            
            if self.install_file(file_path):
                success_count += 1
            
            progress = (index + 1) / total_files * 100
            self.update_progress(progress)
        
        # 最终UI更新
        self.root.after(10, lambda: self.finalize_install(success_count, total_files))
    
    def reset_ui(self):
        """重置UI状态"""
        self.is_installing = False
        self.start_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
    
    def finalize_install(self, success_count, total_files):
        """安装完成后的收尾"""
        self.is_installing = False
        self.start_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        
        final_progress = 100 if not self.cancel_flag else self.progress_var.get()
        self.progress_var.set(final_progress)
        
        self.add_log("\n==================================================")
        if self.cancel_flag:
            self.add_log(f"⛔ 安装已取消，成功安装 {success_count}/{total_files} 个包")
        else:
            self.add_log(f"✅ 批量安装完成，成功安装 {success_count}/{total_files} 个包")
        
        if success_count < total_files and not self.cancel_flag:
            self.add_log("⚠️ 部分安装包安装失败，请查看日志并手动安装")
    
    def start_install(self):
        """启动安装"""
        if self.is_installing:
            self.add_log("⚠️ 已有安装任务在执行，请勿重复点击")
            return
        
        if not self.install_files:
            self.add_log("❌ 没有待安装的文件，请先选择包含安装包的文件夹")
            return
        
        self.add_log("\n🚀 点击了开始批量安装按钮")
        self.add_log("ℹ️ 提示：部分安装包可能需要手动确认，或管理员权限")
        
        self.is_installing = True
        self.root.after(10, lambda: self.update_btn_states())
        
        install_thread = threading.Thread(target=self.batch_install)
        install_thread.daemon = True
        install_thread.start()
    
    def update_btn_states(self):
        """更新按钮状态"""
        self.start_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0)

if __name__ == "__main__":
    if os.name != "nt":
        print("❌ 该程序仅支持Windows系统")
        sys.exit(1)
    
    root = ctk.CTk()
    app = FlyInstaller(root)
    root.mainloop()