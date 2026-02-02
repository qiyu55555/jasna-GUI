import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import threading
import time
import shutil
from pathlib import Path
import logging
from datetime import datetime
import json
import sys
import re
import queue
import signal


class Tooltip:
    """鼠标悬停提示类"""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay  # 显示延迟（毫秒）
        self.tooltip_window = None
        self.id = None
        self.x = self.y = 0
        self.active = False
        
        # 绑定事件
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<Motion>", self.on_motion)
    
    def on_enter(self, event=None):
        self.active = True
        self.schedule_tooltip()
    
    def on_leave(self, event=None):
        self.active = False
        self.unschedule_tooltip()
        self.hide_tooltip()
    
    def on_motion(self, event=None):
        self.x = event.x
        self.y = event.y
        if self.tooltip_window:
            # 重新显示tooltip以更新位置
            self.hide_tooltip()
            self.show_tooltip()
    
    def schedule_tooltip(self):
        self.unschedule_tooltip()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def unschedule_tooltip(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show_tooltip(self):
        if not self.active:
            return
        
        # 创建提示窗口
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        
        # 隐藏窗口直到位置设置好
        tw.withdraw()
        tw.overrideredirect(True)  # 无边框
        
        # 设置样式
        tw.configure(bg="#ffffe0", relief="solid", bd=1)
        
        # 创建标签
        label = tk.Label(
            tw, 
            text=self.text, 
            justify=tk.LEFT,
            background="#ffffe0",
            relief="solid",
            bd=1,
            font=("微软雅黑", 10)  # 稍小的字体
        )
        label.pack(ipadx=1)
        
        # 更新窗口以获取正确尺寸
        tw.update_idletasks()
        
        # 计算位置（在鼠标位置附近显示）
        x = self.widget.winfo_rootx() + self.x + 10
        y = self.widget.winfo_rooty() + self.y + 10
        
        # 检查是否会超出屏幕边界
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        tooltip_width = tw.winfo_width()
        tooltip_height = tw.winfo_height()
        
        # 如果提示框会超出右侧屏幕边界，则调整到左侧
        if x + tooltip_width > screen_width:
            x = max(0, screen_width - tooltip_width - 5)
        
        # 如果提示框会超出底部屏幕边界，则调整到上方
        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() - tooltip_height - 5
        
        tw.geometry(f"+{x}+{y}")
        
        # 显示窗口
        tw.deiconify()
    
    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class StuckMonitorThread:
    """卡死监测线程"""
    def __init__(self, log_file_path, stuck_seconds, callback):
        """
        初始化卡死监测器
        
        Args:
            log_file_path: 日志文件路径
            stuck_seconds: 卡死秒数阈值
            callback: 检测到卡死时的回调函数
        """
        self.log_file_path = log_file_path
        self.stuck_seconds = stuck_seconds
        self.callback = callback
        self.last_update_time = time.time()
        self.last_size = 0
        self.running = False
        self.monitor_thread = None
        
    def start(self):
        """启动监测线程"""
        if self.running:
            return
            
        self.running = True
        self.last_update_time = time.time()
        self.last_size = 0
        
        self.monitor_thread = threading.Thread(target=self.monitor)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop(self):
        """停止监测线程"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
    def monitor(self):
        """监控日志文件更新"""
        while self.running:
            try:
                # 检查日志文件是否存在
                if not os.path.exists(self.log_file_path):
                    time.sleep(1)
                    continue
                
                # 获取文件当前大小和修改时间
                current_size = os.path.getsize(self.log_file_path)
                current_time = time.time()
                
                # 检查文件是否有更新
                if current_size != self.last_size:
                    # 文件有更新，重置时间
                    self.last_update_time = current_time
                    self.last_size = current_size
                else:
                    # 文件没有更新，检查是否超过阈值
                    time_since_update = current_time - self.last_update_time
                    if time_since_update >= self.stuck_seconds:
                        # 调用回调函数
                        if self.callback:
                            self.callback({
                                'type': 'stuck',
                                'message': f'日志文件已 {int(time_since_update)} 秒未更新',
                                'timestamp': time.time()
                            })
                        
                        # 重置时间，避免重复发送
                        self.last_update_time = current_time
                
                # 每秒检查一次
                time.sleep(1)
                
            except Exception as e:
                # 卡死监测线程出错，记录错误但继续运行
                time.sleep(5)

class JasnaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JASNA视频处理工具-v2.0  （ 作者：旗鱼 ）                                                    jasna和lada均为免费开源软件     中文交流QQ群：767031656")
        self.root.geometry("1170x860")  # 减少宽度以匹配更窄的输入框
        
        # 设置窗口图标
        try:
            import sys
            import os
            if getattr(sys, 'frozen', False):
                # 如果是打包后的EXE运行环境
                application_path = sys._MEIPASS
                icon_path = os.path.join(application_path, 'jasna-v2-T-256.ico')
            else:
                # 如果是开发环境
                icon_path = "jasna-v2-T-256.ico"
            
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # 如果找不到图标文件，尝试在当前目录寻找
                fallback_icon_path = os.path.join(os.path.dirname(sys.executable), 'jasna-v2-T-256.ico')
                if os.path.exists(fallback_icon_path):
                    self.root.iconbitmap(fallback_icon_path)
        except tk.TclError:
            # 如果ico文件不存在或无法加载，忽略错误
            pass
        
        # 创建自定义字体
        self.normal_font = ("微软雅黑", 13)  # 加大30%的字号
        self.bold_font = ("微软雅黑", 13, "bold")  # 加大30%的字号并加粗
        self.title_font = ("微软雅黑", 14, "bold")  # 标题字体
        self.progress_font = ("微软雅黑", 16)  # 进度字体加大30%
        
        # 设置日志
        self.setup_logging()
        
        # 初始化变量
        self.video_lists = {
            "processed": [],
            "unprocessed": [],
            "error": []
        }
        self.currently_processing = None
        self.processing_thread = None
        self.stop_processing = False
        self.current_progress = 0
        self.progress_records = []
        
        # 视频信息变量
        self.video_resolution_var = tk.StringVar(value="未知")
        self.video_fps_var = tk.StringVar(value="未知")
        self.video_duration_var = tk.StringVar(value="未知")
        
        # 日志监控线程控制
        self.log_monitor_running = False
        self.log_monitor_thread = None
        
        # 当前运行的JASNA进程
        self.current_process = None
        
        # 卡死检测相关变量
        self.stuck_monitor = None
        self.is_stuck = False
        self.stuck_detected = False  # 新增：标记是否已检测到卡死
        
        # 处理完成后操作选择
        self.post_processing_action_var = tk.StringVar(value="无")  # 默认为"无"
        
        # 配置文件路径
        self.config_file = "jasna_gui_config.json"
        
        # 初始化切片帧数历史记录
        self.slice_frames_history = []
        
        # 用于跟踪stuck_seconds是否被临时修改
        self.original_stuck_seconds = None
        self.stuck_seconds_modified = False
        
        # 初始化ffprobe预热标志
        self.ffprobe_warmed_up = False
        self.first_video_processed = False  # 添加标志以跟踪是否已处理第一个视频
        
        # 创建GUI组件
        self.create_widgets()
        
        # 加载上次的设置
        self.load_settings()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_logging(self):
        """设置日志记录"""
        # 使用ANSI编码（Windows系统默认编码）
        import locale
        system_encoding = locale.getpreferredencoding()
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('jasna_gui.log', encoding=system_encoding),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def center_window_on_parent(self, window, parent=None):
        """将窗口居中显示在父窗口中心"""
        window.update_idletasks()  # 更新窗口尺寸信息
        
        if parent is None:
            parent = self.root
            
        # 获取父窗口的位置和尺寸
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # 获取子窗口的尺寸
        child_width = window.winfo_width()
        child_height = window.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width // 2) - (child_width // 2)
        y = parent_y + (parent_height // 2) - (child_height // 2)
        
        # 应用位置
        window.geometry(f"+{x}+{y}")
    
    def show_custom_messagebox(self, msg_type="info", title="", message="", parent=None):
        """自定义消息框，显示在应用程序窗口中心，字体加大50%"""
        import tkinter as tk
        from tkinter import messagebox, Label, Button, Frame
        
        # 使用实际的GUI窗口作为父窗口
        actual_parent = parent or self.root
        
        # 创建放大30%的字体（基于normal_font）
        large_font_family = self.normal_font[0]
        large_font_size = int(self.normal_font[1] * 1.3)  # 增大30%
        if len(self.normal_font) > 2:  # 如果原字体有样式（如bold）
            large_font_style = self.normal_font[2]
            large_font = (large_font_family, large_font_size, large_font_style)
        else:
            large_font = (large_font_family, large_font_size)
        
        # 根据类型创建自定义对话框
        if msg_type == "askyesno":
            dialog = tk.Toplevel(actual_parent)
            dialog.title(title)
            dialog.resizable(False, False)
            dialog.grab_set()  # 模态窗口
            dialog.transient(actual_parent)  # 设置为临时窗口
            
            # 设置对话框图标
            try:
                import sys
                import os
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的EXE运行环境
                    application_path = sys._MEIPASS
                    icon_path = os.path.join(application_path, 'jasna-v2-T-256.ico')
                else:
                    # 如果是开发环境
                    icon_path = "jasna-v2-T-256.ico"
                
                if os.path.exists(icon_path):
                    dialog.iconbitmap(icon_path)
                else:
                    # 如果找不到图标文件，尝试在当前目录寻找
                    fallback_icon_path = os.path.join(os.path.dirname(sys.executable), 'jasna-v2-T-256.ico')
                    if os.path.exists(fallback_icon_path):
                        dialog.iconbitmap(fallback_icon_path)
            except tk.TclError:
                # 如果ico文件不存在或无法加载，忽略错误
                pass
            
            # 设置对话框字体
            dialog.option_add("*Font", large_font)
            
            # 创建消息标签
            label = Label(dialog, text=message, font=large_font, wraplength=400)
            label.pack(padx=20, pady=20)
            
            # 创建按钮框架
            button_frame = Frame(dialog)
            button_frame.pack(pady=10)
            
            # 创建Yes和No按钮
            result = tk.BooleanVar()
            result.set(False)
            
            def yes_clicked():
                result.set(True)
                dialog.destroy()
            
            def no_clicked():
                result.set(False)
                dialog.destroy()
            
            yes_btn = Button(button_frame, text="是", command=yes_clicked, font=large_font)
            yes_btn.pack(side=tk.LEFT, padx=10)
            
            no_btn = Button(button_frame, text="否", command=no_clicked, font=large_font)
            no_btn.pack(side=tk.LEFT, padx=10)
            
            # 居中显示对话框
            dialog.update_idletasks()
            parent_x = actual_parent.winfo_rootx()
            parent_y = actual_parent.winfo_rooty()
            parent_width = actual_parent.winfo_width()
            parent_height = actual_parent.winfo_height()
            
            dialog_width = dialog.winfo_width()
            dialog_height = dialog.winfo_height()
            
            x = parent_x + (parent_width // 2) - (dialog_width // 2)
            y = parent_y + (parent_height // 2) - (dialog_height // 2)
            
            dialog.geometry(f"+{x}+{y}")
            
            # 等待对话框关闭
            dialog.wait_window()
            
            return result.get()
        else:
            # 对于其他类型的消息框，我们仍然使用标准messagebox，但尝试调整字体
            # 由于标准messagebox无法直接更改字体，我们可以暂时使用自定义窗口
            dialog = tk.Toplevel(actual_parent)
            dialog.title(title)
            dialog.resizable(False, False)
            dialog.grab_set()  # 模态窗口
            dialog.transient(actual_parent)  # 设置为临时窗口
            
            # 设置对话框图标
            try:
                import sys
                import os
                if getattr(sys, 'frozen', False):
                    # 如果是打包后的EXE运行环境
                    application_path = sys._MEIPASS
                    icon_path = os.path.join(application_path, 'jasna-v2-T-256.ico')
                else:
                    # 如果是开发环境
                    icon_path = "jasna-v2-T-256.ico"
                
                if os.path.exists(icon_path):
                    dialog.iconbitmap(icon_path)
                else:
                    # 如果找不到图标文件，尝试在当前目录寻找
                    fallback_icon_path = os.path.join(os.path.dirname(sys.executable), 'jasna-v2-T-256.ico')
                    if os.path.exists(fallback_icon_path):
                        dialog.iconbitmap(fallback_icon_path)
            except tk.TclError:
                # 如果ico文件不存在或无法加载，忽略错误
                pass
            
            # 设置对话框字体
            dialog.option_add("*Font", large_font)
            
            # 创建消息标签（移除图标）
            label = Label(dialog, text=message, font=large_font, wraplength=400)
            label.pack(padx=20, pady=20)
            
            # 创建确认按钮
            ok_btn = Button(dialog, text="确定", command=dialog.destroy, font=large_font)
            ok_btn.pack(pady=(0, 20))
            ok_btn.focus_set()  # 设置焦点到按钮上
            ok_btn.bind('<Return>', lambda e: dialog.destroy())  # 回车键关闭
            
            # 居中显示对话框
            dialog.update_idletasks()
            parent_x = actual_parent.winfo_rootx()
            parent_y = actual_parent.winfo_rooty()
            parent_width = actual_parent.winfo_width()
            parent_height = actual_parent.winfo_height()
            
            dialog_width = dialog.winfo_width()
            dialog_height = dialog.winfo_height()
            
            x = parent_x + (parent_width // 2) - (dialog_width // 2)
            y = parent_y + (parent_height // 2) - (dialog_height // 2)
            
            dialog.geometry(f"+{x}+{y}")
            
            # 等待对话框关闭
            dialog.wait_window()
    
    def create_widgets(self):
        """创建所有GUI组件 - 使用place布局进行像素级定位"""
        
        # 设置窗口背景
        self.root.configure(bg='#f0f0f0')
        
        # 自定义设置部分框架
        self.settings_frame = ttk.LabelFrame(self.root, text="自定义设置", padding="10")
        self.settings_frame.place(x=10, y=10, width=1150, height=230)
        
        # 设置标题字体
        style = ttk.Style()
        style.configure("Title.TLabelframe.Label", font=self.title_font)
        self.settings_frame.configure(style="Title.TLabelframe")
        
        # 第一行设置 - 使用place布局
        # 1. jasna程序地址
        jasna_label = ttk.Label(self.settings_frame, text="JASNA程序地址", font=self.normal_font)
        jasna_label.place(x=10, y=15)
        Tooltip(jasna_label, "A卡不能用  N卡低于12G显存不建议使用\n指定JASNA主程序文件的完整路径\n例如: D:/jasna-0.3/jasna.exe\n本GUI程序可以不与jasna.exe程序放在一起，放在任何位置都可以正常运行\n只要jasna.exe的命令没有改变，则此程序可以适用于jasna的不同版本")
        
        self.jasna_path_var = tk.StringVar()
        self.jasna_path_entry = ttk.Entry(self.settings_frame, textvariable=self.jasna_path_var, width=30, font=self.normal_font)
        self.jasna_path_entry.place(x=140, y=15, width=300)
        
        jasna_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_jasna_path, style="TButton")
        jasna_browse_btn.place(x=450, y=15, width=60)
        
        # 2. 切片帧数
        slice_label = ttk.Label(self.settings_frame, text="切片帧数", font=self.normal_font)
        slice_label.place(x=530, y=15)
        Tooltip(slice_label, "视频一次性处理的帧数\n建议值: 30-90\n如果输入的数值为首次使用则需要编译模型\n时间在0.2-4小时\n请耐心等待\n编译过的模型会自动记录，下次使用就不用再编译了")
        
        self.slice_frames_var = tk.StringVar(value="30")
        self.slice_frames_entry = ttk.Entry(self.settings_frame, textvariable=self.slice_frames_var, width=9, font=self.normal_font, justify='center')
        self.slice_frames_entry.place(x=610, y=15, width=80)
        
        # 3. 输出视频后缀
        suffix_label = ttk.Label(self.settings_frame, text="输出视频后缀", font=self.normal_font)
        suffix_label.place(x=710, y=15)
        Tooltip(suffix_label, "输出视频文件名的后缀\n例如: -U \n表示输出文件名为：原文件名-U.mp4")
        
        self.output_suffix_var = tk.StringVar(value="-U")
        self.output_suffix_entry = ttk.Entry(self.settings_frame, textvariable=self.output_suffix_var, width=9, font=self.normal_font, justify='center')
        self.output_suffix_entry.place(x=825, y=15, width=80)
        
        # 4. 卡死几秒后跳过
        stuck_label = ttk.Label(self.settings_frame, text="卡死几秒后跳过", font=self.normal_font)
        stuck_label.place(x=923, y=15)
        Tooltip(stuck_label, "视频处理过程中卡死多少秒后自动跳过并处理下一个\n默认值: 300秒（5分钟）\n切片帧数为第一次使用时，这里会自动变为15000\n模型编译完成后会自动变回之前设置的值\n不必干预，全自动处理")
        
        self.stuck_seconds_var = tk.StringVar(value="300")  # 默认300秒（5分钟）
        self.stuck_seconds_entry = ttk.Entry(self.settings_frame, textvariable=self.stuck_seconds_var, width=9, font=self.normal_font, justify='center')
        self.stuck_seconds_entry.place(x=1060, y=15, width=60)
        
        # 第二行设置
        # 5. 输入文件夹
        input_label = ttk.Label(self.settings_frame, text="输入文件夹", font=self.normal_font)
        input_label.place(x=10, y=55)
        Tooltip(input_label, "包含待处理视频文件的文件夹路径")
        
        self.input_folder_var = tk.StringVar()
        self.input_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.input_folder_var, width=30, font=self.normal_font)
        self.input_folder_entry.place(x=140, y=55, width=300)
        
        input_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_input_folder, style="TButton")
        input_browse_btn.place(x=450, y=55, width=60)
        
        # 6. 成功视频存放文件夹
        success_label = ttk.Label(self.settings_frame, text="成功视频存放文件夹", font=self.normal_font)
        success_label.place(x=530, y=55)
        Tooltip(success_label, "处理成功的视频将被移动到此文件夹\n输入文件夹、输出文件夹、成功视频存放文件夹和出错视频存放文件最好不要设置为上下级目录")
        
        self.success_folder_var = tk.StringVar()
        self.success_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.success_folder_var, width=30, font=self.normal_font)
        self.success_folder_entry.place(x=710, y=55, width=340)
        
        success_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_success_folder, style="TButton")
        success_browse_btn.place(x=1060, y=55, width=60)
        
        # 第三行设置
        # 7. 输出文件夹
        output_label = ttk.Label(self.settings_frame, text="输出文件夹", font=self.normal_font)
        output_label.place(x=10, y=95)
        Tooltip(output_label, "处理后的视频文件将保存到此文件夹\n输入文件夹、输出文件夹、成功视频存放文件夹和出错视频存放文件最好不要设置为上下级目录")
        
        self.output_folder_var = tk.StringVar()
        self.output_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.output_folder_var, width=30, font=self.normal_font)
        self.output_folder_entry.place(x=140, y=95, width=300)
        
        output_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_output_folder, style="TButton")
        output_browse_btn.place(x=450, y=95, width=60)
        
        # 8. 出错视频存放文件夹
        error_label = ttk.Label(self.settings_frame, text="出错视频存放文件夹", font=self.normal_font)
        error_label.place(x=530, y=95)
        Tooltip(error_label, "处理失败的视频将被移动到此文件夹\n输入文件夹、输出文件夹、成功视频存放文件夹和出错视频存放文件最好不要设置为上下级目录")
        
        self.error_folder_var = tk.StringVar()
        self.error_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.error_folder_var, width=30, font=self.normal_font)
        self.error_folder_entry.place(x=710, y=95, width=340)
        
        error_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_error_folder, style="TButton")
        error_browse_btn.place(x=1060, y=95, width=60)
        
        # 第四行设置
        # 9. 自定义编码参数
        encode_label = ttk.Label(self.settings_frame, text="自定义编码参数", font=self.normal_font)
        encode_label.place(x=10, y=135)
        Tooltip(encode_label, "自定义视频编码参数\n格式: 参数1=值1,参数2=值2,...\n其中cq的值主要影响视频质量\ncq值越小，视频质量越高，文件体积也越大\n默认值: 31\n默认参数适用于大多数情况")
        
        self.encode_params_var = tk.StringVar(value='preset=P7,tuning_info=high_quality,rc=vbr,cq=31,aq=1,temporalaq=0,lookahead=32,gop=300')
        self.encode_params_entry = ttk.Entry(self.settings_frame, textvariable=self.encode_params_var, width=53, font=self.normal_font)
        self.encode_params_entry.place(x=140, y=135, width=980)
        
        # 控制按钮区域 - 使用place布局
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.place(x=10, y=240, width=1150, height=60)
        
        # 设置按钮样式
        style.configure("TButton", font=self.normal_font)
        
        scan_btn = ttk.Button(self.button_frame, text="扫描视频", command=self.scan_videos, style="TButton")
        scan_btn.place(x=165, y=10, width=100, height=35)
        Tooltip(scan_btn, "扫描输入文件夹中的视频文件\n将视频添加到待处理列表并显示分辨率和时长\n对比输出文件夹中的视频\n如果为已处理过\n则把视频移动到成功视频存放文件夹")
        
        start_btn = ttk.Button(self.button_frame, text="开始处理", command=self.start_processing, style="TButton")
        start_btn.place(x=295, y=10, width=100, height=35)
        Tooltip(start_btn, "开始处理视频列表中的所有视频\n按顺序处理每个视频文件")
        
        stop_btn = ttk.Button(self.button_frame, text="停止处理", command=self.stop_processing_func, style="TButton")
        stop_btn.place(x=425, y=10, width=100, height=35)
        Tooltip(stop_btn, "停止当前正在处理的视频\n并停止处理列表中的后续视频")
        
        clear_btn = ttk.Button(self.button_frame, text="清空列表", command=self.clear_lists, style="TButton")
        clear_btn.place(x=555, y=10, width=100, height=35)
        Tooltip(clear_btn, "清空所有视频列表\n包括已处理、未处理和出错列表")
        
        save_btn = ttk.Button(self.button_frame, text="保存设置", command=self.save_settings, style="TButton")
        save_btn.place(x=685, y=10, width=100, height=35)
        Tooltip(save_btn, "保存当前所有设置到配置文件\n包括路径、参数等设置")
        
        # 处理完成后操作选择
        post_processing_label = ttk.Label(self.button_frame, text="处理完成后", font=self.normal_font)
        post_processing_label.place(x=880, y=12, width=100, height=30)
        Tooltip(post_processing_label, "选择视频处理全部完成后执行的操作\n无: 不执行任何操作\n退出并休眠: 关闭软件并使计算机休眠\n退出并关机: 关闭软件并关闭计算机")
        
        # 使用自定义按钮作为选项选择器，避免下拉箭头并提高对比度
        post_processing_options = ["无", "退出软件并休眠", "退出软件并关机"]
        self.post_processing_current_option_index = 0  # 当前选项索引
        
        # 创建一个带有内凹效果的自定义按钮
        self.post_processing_button = tk.Button(
            self.button_frame, 
            textvariable=self.post_processing_action_var,
            command=self.show_post_processing_menu,
            font=self.normal_font,
            bg="white",  # 白色背景
            fg="black",
            relief="sunken",  # 内凹效果
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.post_processing_button.place(x=975, y=12, width=150, height=30)
        
        # 初始化显示
        self.post_processing_action_var.set(post_processing_options[0])
        self.post_processing_options_list = post_processing_options
        
        # 创建右键菜单
        self.post_processing_menu = tk.Menu(self.root, tearoff=0)
        for option in post_processing_options:
            # 使用嵌套函数解决lambda捕获变量的问题
            def make_command(opt):
                return lambda: self.select_post_processing_option(opt)
            self.post_processing_menu.add_command(label=option, command=make_command(option))
        
        # 正在处理视频区域
        self.progress_frame = ttk.LabelFrame(self.root, text="正在处理视频", padding="10")
        self.progress_frame.place(x=10, y=300, width=1150, height=170)
        self.progress_frame.configure(style="Title.TLabelframe")
        
        # 左半部分：当前处理视频和进度条
        left_frame = ttk.Frame(self.progress_frame)
        left_frame.place(x=10, y=10, width=600, height=110)
        
        # 当前处理视频
        current_label = ttk.Label(left_frame, text="当前处理视频：", font=self.progress_font)
        current_label.place(x=0, y=5)
        
        self.current_video_var = tk.StringVar(value="无")
        self.current_video_label = ttk.Label(left_frame, textvariable=self.current_video_var, foreground="blue", font=self.progress_font, wraplength=400)
        self.current_video_label.place(x=150, y=5, width=500)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(left_frame, length=400, mode='determinate')
        self.progress_bar.place(x=0, y=45, width=500)
        
        # 进度百分比
        progress_label = ttk.Label(left_frame, text="进度:", font=self.progress_font)
        progress_label.place(x=0, y=75)
        
        self.progress_percent_var = tk.StringVar(value="0%")
        progress_percent_label = ttk.Label(left_frame, textvariable=self.progress_percent_var, foreground="SystemHighlight", font=self.progress_font)
        progress_percent_label.place(x=60, y=76)
        
        # 视频信息（显示在进度右边）
        resolution_label = ttk.Label(left_frame, text="分辨率:", font=self.normal_font)
        resolution_label.place(x=125, y=77)
        resolution_value_label = ttk.Label(left_frame, textvariable=self.video_resolution_var, font=self.normal_font)
        resolution_value_label.place(x=182, y=78)
        
        fps_label = ttk.Label(left_frame, text="帧率:", font=self.normal_font)
        fps_label.place(x=285, y=77)
        fps_value_label = ttk.Label(left_frame, textvariable=self.video_fps_var, font=self.normal_font)
        fps_value_label.place(x=327, y=78)
        
        duration_label = ttk.Label(left_frame, text="时长:", font=self.normal_font)
        duration_label.place(x=380, y=77)
        duration_value_label = ttk.Label(left_frame, textvariable=self.video_duration_var, font=self.normal_font)
        duration_value_label.place(x=422, y=78)
        
        # 右半部分：处理详细信息
        right_frame = ttk.LabelFrame(self.progress_frame, text="处理详细信息", padding="10")
        right_frame.place(x=530, y=5, width=590, height=110)
        right_frame.configure(style="Title.TLabelframe")
        
        # 第一行详细信息
        elapsed_label = ttk.Label(right_frame, text="已运行时间:", font=self.normal_font)
        elapsed_label.place(x=10, y=5)
        
        self.elapsed_time_var = tk.StringVar(value="00:00")
        elapsed_value_label = ttk.Label(right_frame, textvariable=self.elapsed_time_var, foreground="green", font=self.normal_font)
        elapsed_value_label.place(x=105, y=5)
        
        remaining_label = ttk.Label(right_frame, text="剩余时间:", font=self.normal_font)
        remaining_label.place(x=200, y=5)
        
        self.remaining_time_var = tk.StringVar(value="00:00")
        remaining_value_label = ttk.Label(right_frame, textvariable=self.remaining_time_var, foreground="orange", font=self.normal_font)
        remaining_value_label.place(x=280, y=5)
        
        speed_label = ttk.Label(right_frame, text="处理速度:", font=self.normal_font)
        speed_label.place(x=380, y=5)
        
        self.processing_speed_var = tk.StringVar(value="0.0fps")
        speed_value_label = ttk.Label(right_frame, textvariable=self.processing_speed_var, foreground="blue", font=self.normal_font)
        speed_value_label.place(x=460, y=5)
        
        # 第二行详细信息
        processed_frames_label = ttk.Label(right_frame, text="已处理帧数:", font=self.normal_font)
        processed_frames_label.place(x=10, y=35)
        
        self.processed_frames_var = tk.StringVar(value="0")
        processed_frames_value_label = ttk.Label(right_frame, textvariable=self.processed_frames_var, font=self.normal_font)
        processed_frames_value_label.place(x=105, y=35)
        
        remaining_frames_label = ttk.Label(right_frame, text="剩余帧数:", font=self.normal_font)
        remaining_frames_label.place(x=200, y=35)
        
        self.remaining_frames_var = tk.StringVar(value="0")
        remaining_frames_value_label = ttk.Label(right_frame, textvariable=self.remaining_frames_var, font=self.normal_font)
        remaining_frames_value_label.place(x=280, y=35)
        
        total_frames_label = ttk.Label(right_frame, text="总共帧数:", font=self.normal_font)
        total_frames_label.place(x=380, y=35)
        
        self.total_frames_var = tk.StringVar(value="0")
        total_frames_value_label = ttk.Label(right_frame, textvariable=self.total_frames_var, font=self.normal_font)
        total_frames_value_label.place(x=460, y=35)
        
        # 视频列表显示区域
        self.lists_frame = ttk.Frame(self.root)
        self.lists_frame.place(x=10, y=490, width=1150, height=280)
        
        # 已处理视频列表
        processed_frame = ttk.LabelFrame(self.lists_frame, text="已处理视频列表", padding="5")
        processed_frame.place(x=0, y=0, width=370, height=260)
        processed_frame.configure(style="Title.TLabelframe")
        
        self.processed_listbox = tk.Listbox(processed_frame, font=self.normal_font, selectmode=tk.NONE, exportselection=False, takefocus=False, state='normal')
        self.processed_listbox.place(x=10, y=10, width=330, height=200)
        
        # 完全禁用选择，但仍允许显示内容
        self.processed_listbox.bind('<Button-1>', lambda e: 'break')
        self.processed_listbox.bind('<Control-Button-1>', lambda e: 'break')
        self.processed_listbox.bind('<Shift-Button-1>', lambda e: 'break')
        self.processed_listbox.bind('<B1-Motion>', lambda e: 'break')
        self.processed_listbox.bind('<Double-Button-1>', lambda e: 'break')
        self.processed_listbox.bind('<<ListboxSelect>>', lambda e: 'break')
        
        processed_scrollbar = ttk.Scrollbar(processed_frame, orient=tk.VERTICAL, command=self.processed_listbox.yview)
        processed_scrollbar.place(x=340, y=5, width=20, height=210)
        self.processed_listbox.config(yscrollcommand=processed_scrollbar.set)
        
        # 未处理视频列表
        unprocessed_frame = ttk.LabelFrame(self.lists_frame, text="未处理视频列表", padding="5")
        unprocessed_frame.place(x=390, y=0, width=370, height=260)
        unprocessed_frame.configure(style="Title.TLabelframe")
        
        self.unprocessed_listbox = tk.Listbox(unprocessed_frame, font=self.normal_font, selectmode=tk.NONE, exportselection=False, takefocus=False, state='normal')
        self.unprocessed_listbox.place(x=10, y=10, width=330, height=200)
        
        # 完全禁用选择，但仍允许显示内容
        self.unprocessed_listbox.bind('<Button-1>', lambda e: 'break')
        self.unprocessed_listbox.bind('<Control-Button-1>', lambda e: 'break')
        self.unprocessed_listbox.bind('<Shift-Button-1>', lambda e: 'break')
        self.unprocessed_listbox.bind('<B1-Motion>', lambda e: 'break')
        self.unprocessed_listbox.bind('<Double-Button-1>', lambda e: 'break')
        self.unprocessed_listbox.bind('<<ListboxSelect>>', lambda e: 'break')
        
        unprocessed_scrollbar = ttk.Scrollbar(unprocessed_frame, orient=tk.VERTICAL, command=self.unprocessed_listbox.yview)
        unprocessed_scrollbar.place(x=340, y=5, width=20, height=210)
        self.unprocessed_listbox.config(yscrollcommand=unprocessed_scrollbar.set)
        
        # 处理出错视频列表
        error_frame = ttk.LabelFrame(self.lists_frame, text="处理出错视频列表", padding="5")
        error_frame.place(x=780, y=0, width=370, height=260)
        error_frame.configure(style="Title.TLabelframe")
        
        self.error_listbox = tk.Listbox(error_frame, font=self.normal_font, selectmode=tk.NONE, exportselection=False, takefocus=False, state='normal')
        self.error_listbox.place(x=10, y=10, width=330, height=200)
        
        # 完全禁用选择，但仍允许显示内容
        self.error_listbox.bind('<Button-1>', lambda e: 'break')
        self.error_listbox.bind('<Control-Button-1>', lambda e: 'break')
        self.error_listbox.bind('<Shift-Button-1>', lambda e: 'break')
        self.error_listbox.bind('<B1-Motion>', lambda e: 'break')
        self.error_listbox.bind('<Double-Button-1>', lambda e: 'break')
        self.error_listbox.bind('<<ListboxSelect>>', lambda e: 'break')
        
        error_scrollbar = ttk.Scrollbar(error_frame, orient=tk.VERTICAL, command=self.error_listbox.yview)
        error_scrollbar.place(x=340, y=5, width=20, height=210)
        self.error_listbox.config(yscrollcommand=error_scrollbar.set)
        
        # 处理总结情况
        self.summary_frame = ttk.LabelFrame(self.root, text="处理总结情况", padding="10")
        self.summary_frame.place(x=10, y=760, width=1150, height=60)
        self.summary_frame.configure(style="Title.TLabelframe")
        
        self.summary_var = tk.StringVar(value="输入文件夹中视频数量: 0 | 已处理视频数量: 0 | 未处理视频数量: 0 | 处理出错视频数量: 0")
        self.summary_label = ttk.Label(self.summary_frame, textvariable=self.summary_var, font=self.normal_font)
        self.summary_label.place(x=575, y=0, anchor='center')
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, font=self.normal_font, anchor='center')
        status_bar.place(x=10, y=825, width=1150, height=30)
    
    def browse_jasna_path(self):
        """浏览选择jasna主程序"""
        file_path = filedialog.askopenfilename(
            title="选择JASNA主程序",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.jasna_path_var.set(file_path)
    
    def browse_input_folder(self):
        """浏览选择输入文件夹"""
        folder_path = filedialog.askdirectory(title="选择输入文件夹")
        if folder_path:
            self.input_folder_var.set(folder_path)
    
    def browse_output_folder(self):
        """浏览选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        if folder_path:
            self.output_folder_var.set(folder_path)
    
    def browse_error_folder(self):
        """浏览选择出错视频文件夹"""
        folder_path = filedialog.askdirectory(title="选择出错视频放置文件夹")
        if folder_path:
            self.error_folder_var.set(folder_path)
    
    def browse_success_folder(self):
        """浏览选择成功处理视频文件夹（新增）"""
        folder_path = filedialog.askdirectory(title="选择已成功处理视频放置文件夹")
        if folder_path:
            self.success_folder_var.set(folder_path)
    
    def save_settings(self):
        """保存当前设置到文件"""
        settings = {
            "jasna_path": self.jasna_path_var.get(),
            "input_folder": self.input_folder_var.get(),
            "output_folder": self.output_folder_var.get(),
            "slice_frames": self.slice_frames_var.get(),
            "encode_params": self.encode_params_var.get(),
            "output_suffix": self.output_suffix_var.get(),
            "stuck_seconds": self.stuck_seconds_var.get(),  # 改为秒
            "error_folder": self.error_folder_var.get(),
            "success_folder": self.success_folder_var.get(),  # 新增
            "slice_frames_history": getattr(self, 'slice_frames_history', [])  # 添加切片帧数历史记录
        }
        
        try:
            # 使用临时文件和原子重命名来确保配置文件的原子性
            temp_config_file = self.config_file + '.tmp'
            with open(temp_config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            # 原子重命名操作
            os.replace(temp_config_file, self.config_file)
            self.status_var.set("设置已保存")
            self.logger.info("设置已保存到配置文件")
        except Exception as e:
            self.logger.error(f"保存设置失败: {str(e)}")
            # 清理临时文件（如果存在）
            if os.path.exists(temp_config_file):
                try:
                    os.remove(temp_config_file)
                except:
                    pass
    
    def load_settings(self):
        """从文件加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.jasna_path_var.set(settings.get("jasna_path", ""))
                self.input_folder_var.set(settings.get("input_folder", ""))
                self.output_folder_var.set(settings.get("output_folder", ""))
                self.slice_frames_var.set(settings.get("slice_frames", "60"))
                self.encode_params_var.set(settings.get("encode_params", "preset=P7,tuning_info=high_quality,rc=vbr,cq=32,aq=1,temporalaq=0,lookahead=32,gop=300"))
                self.output_suffix_var.set(settings.get("output_suffix", "-U"))
                self.stuck_seconds_var.set(settings.get("stuck_seconds", "300"))  # 改为秒，默认300秒（5分钟）
                self.error_folder_var.set(settings.get("error_folder", ""))
                self.success_folder_var.set(settings.get("success_folder", ""))  # 新增
                
                # 加载切片帧数历史记录
                self.slice_frames_history = settings.get("slice_frames_history", [])
                
                self.status_var.set("设置已加载")
                self.logger.info("设置已从配置文件加载")
        except Exception as e:
            self.logger.error(f"加载设置失败: {str(e)}")
    
    def warm_up_ffprobe(self):
        """预热ffprobe，确保它已准备好使用"""
        if self.ffprobe_warmed_up:
            return  # 已经预热过了
        
        try:
            import subprocess
            import time
            from pathlib import Path
            import sys
            
            # Windows平台上隐藏控制台窗口的标志
            startupinfo = None
            if sys.platform.startswith('win'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 尝试运行ffprobe版本命令作为预热
            result = subprocess.run(['ffprobe', '-version'], 
                                  capture_output=True, text=True, timeout=10,
                                  startupinfo=startupinfo)
            
            if result.returncode != 0:
                # 如果系统PATH中没有ffprobe，尝试使用本地的
                script_dir = Path(__file__).parent.resolve()
                local_ffprobe_path = script_dir / 'ffprobe.exe'
                if local_ffprobe_path.exists():
                    result = subprocess.run([str(local_ffprobe_path), '-version'], 
                                          capture_output=True, text=True, timeout=10,
                                          startupinfo=startupinfo)
            
            # 等待一小段时间让ffprobe完成初始化
            time.sleep(0.5)
            self.ffprobe_warmed_up = True
            self.logger.info("ffprobe已预热")
        except Exception as e:
            self.logger.warning(f"ffprobe预热失败: {str(e)}")
            # 即使预热失败，也要标记为已尝试
            self.ffprobe_warmed_up = True

    def get_video_basic_info(self, video_path):
        """获取视频基本信息（分辨率、帧率、时长）- 简化版，只返回信息"""
        # 预热ffprobe（仅在第一次调用时）
        if not self.ffprobe_warmed_up:
            self.warm_up_ffprobe()
        
        # 对于第一个视频，可能需要额外的延迟
        if not self.first_video_processed:
            import time
            time.sleep(0.5)  # 给系统一点时间
            self.first_video_processed = True

        try:
            import subprocess
            import json
            import os
            from pathlib import Path
            import time
            import sys
            
            # Windows平台上隐藏控制台窗口的标志
            startupinfo = None
            if sys.platform.startswith('win'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 使用pathlib处理路径，更好地处理中文字符
            video_path_obj = Path(video_path)
            video_path_str = str(video_path_obj.resolve())  # 获取绝对路径
            
            # 检查视频文件是否存在
            if not video_path_obj.exists():
                self.logger.error(f"视频文件不存在: {video_path_str}")
                return "未知", "未知", "未知"
            
            # 构建ffprobe命令，优先使用系统PATH中的ffprobe
            ffprobe_path = 'ffprobe'
            
            # 检查系统PATH中是否有ffprobe
            try:
                subprocess.run([ffprobe_path, '-version'], 
                             capture_output=True, text=True, timeout=5,
                             startupinfo=startupinfo)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # 如果系统PATH中没有ffprobe，尝试使用程序所在文件夹的ffprobe
                script_dir = Path(__file__).parent.resolve()
                local_ffprobe_path = script_dir / 'ffprobe.exe'
                if local_ffprobe_path.exists():
                    ffprobe_path = str(local_ffprobe_path)
                else:
                    self.logger.error("未找到ffprobe")
                    return "未知", "未知", "未知"
            
            # 构建正确的ffprobe命令
            # 在Windows上，我们需要特别小心处理包含中文字符的路径
            cmd_str = f'{ffprobe_path} -v quiet -print_format json -show_format -show_streams "{video_path_str}"'
            
            # 在Windows系统上，使用shell=True来更好地处理中文路径
            # 同时设置适当的编码
            if sys.platform.startswith('win'):
                # Windows平台的特殊处理
                # 针对打包后的EXE环境，使用系统默认编码(cp936)处理中文路径
                import locale
                # 尝试多种编码方式以确保兼容性
                encodings_to_try = ['utf-8', 'gbk', 'gb2312', locale.getpreferredencoding()]
                
                result = None
                last_exception = None
                
                # 为了解决第一个视频信息获取失败的问题，尝试多次执行
                max_retries = 5  # 增加重试次数
                retry_count = 0
                
                while retry_count < max_retries:
                    for encoding in encodings_to_try:
                        try:
                            # 在每次调用ffprobe之前添加短暂延迟，特别是在第一次调用时
                            if retry_count == 0:
                                # 首次尝试前稍作延迟，给ffprobe初始化时间
                                time.sleep(1)  # 增加初始延迟
                            
                            result = subprocess.run(
                                cmd_str,  # 直接使用构造好的字符串命令，其中路径已用双引号包围
                                capture_output=True, 
                                text=True, 
                                timeout=45,  # 增加超时时间
                                shell=True,
                                encoding=encoding,  # 尝试不同的编码
                                startupinfo=startupinfo  # 隐藏控制台窗口
                            )
                            
                            # 检查执行结果
                            if result.returncode == 0 and result.stdout:
                                # 成功获取到信息，跳出重试循环
                                break
                            else:
                                self.logger.warning(f"ffprobe执行失败 (第{retry_count+1}次尝试, 编码: {encoding}): 返回码 {result.returncode}, 输出: {result.stdout[:100] if result.stdout else 'None'}, 错误: {result.stderr[:100] if result.stderr else 'None'}")
                        except UnicodeEncodeError as e:
                            last_exception = e
                            self.logger.warning(f"编码错误 (第{retry_count+1}次尝试, 编码: {encoding}): {str(e)}")
                            continue
                        except Exception as e:
                            last_exception = e
                            self.logger.warning(f"执行错误 (第{retry_count+1}次尝试, 编码: {encoding}): {str(e)}")
                            continue
                    
                    # 如果成功获取到结果，跳出重试循环
                    if result and result.returncode == 0 and result.stdout:
                        break
                    
                    # 如果执行失败，增加重试计数
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = retry_count * 2  # 增加等待时间，指数级递增
                        self.logger.info(f"等待{wait_time}秒后重试...")
                        time.sleep(wait_time)  # 增加延迟，给系统更多时间
                
                # 如果所有重试都失败，返回未知
                if result is None or result.returncode != 0 or not result.stdout:
                    self.logger.error(f"获取视频信息失败 (已重试{max_retries}次): {video_path_str}")
                    return "未知", "未知", "未知"
            else:
                # 其他平台使用原方法
                cmd_args = [
                    ffprobe_path,
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    '"' + video_path_str + '"'
                ]
                result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=30,
                                       startupinfo=startupinfo)  # 隐藏控制台窗口
                
                if result.returncode != 0 or not result.stdout:
                    return "未知", "未知", "未知"
            
            if result.returncode != 0 or not result.stdout:
                return "未知", "未知", "未知"
            
            try:
                data = json.loads(result.stdout)
                
                if not data:
                    return "未知", "未知", "未知"
                
                # 获取视频流信息
                video_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                if not video_stream:
                    return "未知", "未知", "未知"
                
                # 获取分辨率
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                if width and height:
                    resolution = f"{width}×{height}"
                else:
                    resolution = "未知"
                
                # 获取帧率
                r_frame_rate = video_stream.get('r_frame_rate', '0/0')
                if r_frame_rate and r_frame_rate != '0/0':
                    try:
                        num, den = map(int, r_frame_rate.split('/'))
                        if den != 0:
                            fps = round(num / den, 2)
                            fps_str = f"{fps}"
                        else:
                            fps_str = "未知"
                    except (ValueError, ZeroDivisionError):
                        fps_str = "未知"
                else:
                    fps_str = "未知"
                
                # 获取时长
                duration = data.get('format', {}).get('duration', '0')
                try:
                    duration_seconds = float(duration)
                    if duration_seconds <= 0:
                        duration_str = "未知"
                    else:
                        hours = int(duration_seconds // 3600)
                        minutes = int((duration_seconds % 3600) // 60)
                        seconds = int(duration_seconds % 60)
                        
                        if hours > 0:
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            duration_str = f"{minutes:02d}:{seconds:02d}"
                except ValueError:
                    duration_str = "未知"
                
                return resolution, fps_str, duration_str
                
            except json.JSONDecodeError:
                return "未知", "未知", "未知"
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"获取视频信息超时: {video_path}")
            return "未知", "未知", "未知"
        except FileNotFoundError:
            self.logger.error(f"找不到文件或命令: {video_path}")
            return "未知", "未知", "未知"
        except Exception as e:
            self.logger.error(f"获取视频信息时发生异常: {str(e)}")
            return "未知", "未知", "未知"
    
    def normalize_resolution(self, resolution):
        """将分辨率标准化为480、720、1K、2K、4K、8K格式"""
        if resolution == "未知":
            return "未知"
        
        try:
            # 解析分辨率，例如 "1920×1080"
            if "×" in resolution:
                width_str, height_str = resolution.split("×")
                width = int(width_str.strip())
                height = int(height_str.strip())
                
                # 根据宽度来判断标准分辨率
                if width >= 7680:
                    return "8K"
                elif width >= 3840:
                    return "4K"
                elif width >= 2048:
                    return "2K"  # 通常2K指2048水平分辨率
                elif width >= 1920:
                    return "1K"  # 1080p有时被称为1K，但更常见的是称为HD
                elif width >= 1280:
                    return "720"  # 720p
                elif width >= 640:
                    return "480"  # 480p
                else:
                    return resolution  # 如果不符合标准，则返回原始值
            else:
                return resolution  # 如果不是预期格式，则返回原始值
        except:
            return resolution  # 如果解析失败，则返回原始值
    
    def format_duration_for_display(self, duration):
        """格式化时长以确保一致性，特别是对于较短的时长"""
        if duration == "未知":
            return "未知"
        
        # 如果是 HH:MM:SS 格式，直接返回
        if ':' in duration:
            parts = duration.split(':')
            if len(parts) == 3:  # HH:MM:SS
                return duration
            elif len(parts) == 2:  # MM:SS - 添加前导的 00:
                return f"00:{duration}"
        
        return duration
    
    def scan_videos(self):
        """扫描输入文件夹中的视频文件"""
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        
        if not input_folder or not os.path.exists(input_folder):
            self.show_custom_messagebox("error", "错误", "请输入有效的输入文件夹路径！")
            return
        
        if not output_folder:
            self.show_custom_messagebox("warning", "警告", "输出文件夹未设置，将无法判断已处理视频")
            return
        
        # 清空现有列表
        self.clear_lists(clear_summary=False)
        
        # 支持的视频格式
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.m4v', '.webm']
        
        try:
            # 获取输入文件夹中的所有视频文件
            input_files = []
            for file in os.listdir(input_folder):
                file_path = os.path.join(input_folder, file)
                if os.path.isfile(file_path) and Path(file).suffix.lower() in video_extensions:
                    input_files.append(file)
            
            # 获取输出文件夹中已存在的文件
            output_files = []
            if os.path.exists(output_folder):
                for file in os.listdir(output_folder):
                    if os.path.isfile(os.path.join(output_folder, file)):
                        output_files.append(file)
            
            # 分类视频文件
            for idx, video_file in enumerate(input_files):
                # 构建输出文件名（添加后缀和.mp4扩展名）
                video_name = Path(video_file).stem
                suffix = self.output_suffix_var.get()
                output_file = f"{video_name}{suffix}.mp4"
                
                # 检查是否已处理
                if output_file in output_files:
                    # 为已处理视频获取信息
                    video_path = os.path.join(input_folder, video_file)
                    self.logger.info(f"正在获取已处理视频信息 ({idx+1}): {video_path}")
                    resolution, fps, duration = self.get_video_basic_info(video_path)
                    self.logger.info(f"获取到的已处理视频信息: {resolution}, {fps}, {duration}")
                    video_info = {
                        'name': video_file,
                        'resolution': resolution,
                        'fps': fps,
                        'duration': duration,
                        'already_processed': True  # 标记为已处理过
                    }
                    self.video_lists["processed"].append(video_info)
                    
                    # 移动已处理过的源视频到成功文件夹
                    success_folder = self.success_folder_var.get()
                    if success_folder:
                        # 在主线程中延迟执行移动操作
                        self.root.after(100, lambda vp=video_path, vf=video_file: self.move_already_processed_to_success_folder(vp, vf))
                else:
                    # 为未处理视频获取信息
                    video_path = os.path.join(input_folder, video_file)
                    self.logger.info(f"正在获取未处理视频信息 ({idx+1}): {video_path}")
                    resolution, fps, duration = self.get_video_basic_info(video_path)
                    self.logger.info(f"获取到的未处理视频信息: {resolution}, {fps}, {duration}")
                    video_info = {
                        'name': video_file,
                        'resolution': resolution,
                        'fps': fps,
                        'duration': duration
                    }
                    self.video_lists["unprocessed"].append(video_info)
            
            # 更新列表显示
            self.update_lists_display()
            
            # 更新总结
            self.update_summary()
            
            self.status_var.set(f"扫描完成！找到 {len(input_files)} 个视频文件")
            self.logger.info(f"扫描完成！找到 {len(input_files)} 个视频文件")
            
        except Exception as e:
            self.show_custom_messagebox("error", "错误", f"扫描视频时出错: {str(e)}")
            self.logger.error(f"扫描视频时出错: {str(e)}")
    
    def update_lists_display(self):
        """更新列表显示"""
        # 清空列表
        self.processed_listbox.delete(0, tk.END)
        self.unprocessed_listbox.delete(0, tk.END)
        self.error_listbox.delete(0, tk.END)
        
        # 添加已处理视频 - 显示视频名称和处理速度
        for video in self.video_lists["processed"]:
            if isinstance(video, dict):  # 新格式：包含视频信息的字典
                if 'processing_speed' in video:  # 已处理视频，包含处理速度
                    # 创建临时tkinter组件来测量文本宽度
                    temp_font = ("微软雅黑", 13)
                    import tkinter.font as tkFont
                    font_obj = tkFont.Font(family=temp_font[0], size=temp_font[1])
                    
                    # 获取速度信息
                    speed_info = f"[速度: {video['processing_speed']}X]"
                    
                    # 基础组成结构为："视频名称" + "4个空格" + "处理速度"
                    base_spacing = "    "  # 4个空格
                    base_spacing_width = font_obj.measure(base_spacing)
                    speed_width = font_obj.measure(speed_info)
                    
                    # 计算基础组合内容的宽度（视频名称 + 4个空格 + 处理速度）
                    base_content_width = font_obj.measure(video['name']) + base_spacing_width + speed_width
                    
                    # 显示区域宽度为330px
                    display_area_width = 325
                    
                    if base_content_width <= display_area_width:
                        # 当总宽度小于显示区域时
                        # 计算可添加的额外空格数量
                        remaining_width = display_area_width - base_content_width
                        if remaining_width > 0:
                            # 计算需要在处理速度前添加的额外空格数
                            space_width = font_obj.measure(" ")
                            num_extra_spaces = int(remaining_width / space_width) if space_width > 0 else 0
                            # 在处理速度前添加计算得出的额外空格
                            extra_spacing = " " * num_extra_spaces
                            video_display = f"{video['name']}{base_spacing}{extra_spacing}{speed_info}"
                        else:
                            # 如果不需要额外空格
                            video_display = f"{video['name']}{base_spacing}{speed_info}"
                    else:
                        # 当总宽度大于显示区域时
                        # 计算当前组合内容总宽度超出显示区域的数值
                        overflow_width = base_content_width - display_area_width
                        
                        # 需要从视频名称中减去的宽度
                        name_max_width = font_obj.measure(video['name']) - overflow_width
                        
                        if name_max_width > 0:
                            # 根据需要的宽度截取视频名称
                            truncated_name = ""
                            current_width = 0
                            
                            for char in video['name']:
                                char_width = font_obj.measure(char)
                                if current_width + char_width > name_max_width:
                                    break
                                truncated_name += char
                                current_width += char_width
                            
                            # 保持"4个空格"+"处理速度"的结构不变
                            video_display = f"{truncated_name}{base_spacing}{speed_info}"
                        else:
                            # 如果视频名称本身太大以至于不能显示任何字符，则只显示速度信息
                            video_display = f"{base_spacing}{speed_info}"
                else:  # 仍为旧格式的已处理视频
                    # 检查是否为已处理过的视频
                    if 'already_processed' in video and video['already_processed']:
                        # 创建临时tkinter组件来测量文本宽度
                        temp_font = ("微软雅黑", 13)
                        import tkinter.font as tkFont
                        font_obj = tkFont.Font(family=temp_font[0], size=temp_font[1])
                        
                        # 获取已处理过信息
                        processed_info = "[已处理过]"
                        
                        # 基础组成结构为："视频名称" + "4个空格" + "[已处理过]"
                        base_spacing = "    "  # 4个空格
                        base_spacing_width = font_obj.measure(base_spacing)
                        processed_width = font_obj.measure(processed_info)
                        
                        # 计算基础组合内容的宽度（视频名称 + 4个空格 + [已处理过]）
                        base_content_width = font_obj.measure(video['name']) + base_spacing_width + processed_width
                        
                        # 显示区域宽度为325px
                        display_area_width = 325
                        
                        if base_content_width <= display_area_width:
                            # 当总宽度小于显示区域时
                            # 计算可添加的额外空格数量
                            remaining_width = display_area_width - base_content_width
                            if remaining_width > 0:
                                # 计算需要在[已处理过]前添加的额外空格数
                                space_width = font_obj.measure(" ")
                                num_extra_spaces = int(remaining_width / space_width) if space_width > 0 else 0
                                # 在[已处理过]前添加计算得出的额外空格
                                extra_spacing = " " * num_extra_spaces
                                video_display = f"{video['name']}{base_spacing}{extra_spacing}{processed_info}"
                            else:
                                # 如果不需要额外空格
                                video_display = f"{video['name']}{base_spacing}{processed_info}"
                        else:
                            # 当总宽度大于显示区域时
                            # 计算当前组合内容总宽度超出显示区域的数值
                            overflow_width = base_content_width - display_area_width
                            
                            # 需要从视频名称中减去的宽度
                            name_max_width = font_obj.measure(video['name']) - overflow_width
                            
                            if name_max_width > 0:
                                # 根据需要的宽度截取视频名称
                                truncated_name = ""
                                current_width = 0
                                
                                for char in video['name']:
                                    char_width = font_obj.measure(char)
                                    if current_width + char_width > name_max_width:
                                        break
                                    truncated_name += char
                                    current_width += char_width
                                
                                # 保持"4个空格"+"[已处理过]"的结构不变
                                video_display = f"{truncated_name}{base_spacing}{processed_info}"
                            else:
                                # 如果视频名称本身太大以至于不能显示任何字符，则只显示[已处理过]信息
                                video_display = f"{base_spacing}{processed_info}"
                    else:
                        video_display = f"{video['name']} [{video['resolution']}, {video['fps']}fps, {video['duration']}]"
                self.processed_listbox.insert(tk.END, video_display)
            else:  # 旧格式：仅文件名
                self.processed_listbox.insert(tk.END, video)
        
        # 添加未处理视频 - 应用新功能（标准化分辨率和纯数字帧率）
        for video in self.video_lists["unprocessed"]:
            if isinstance(video, dict):  # 新格式：包含视频信息的字典
                # 创建临时tkinter组件来测量文本宽度
                temp_font = ("微软雅黑", 13)
                import tkinter.font as tkFont
                font_obj = tkFont.Font(family=temp_font[0], size=temp_font[1])
                
                # 获取分辨率和时长信息，并格式化时长
                normalized_resolution = self.normalize_resolution(video['resolution'])
                formatted_duration = self.format_duration_for_display(video['duration'])
                info_part = f"[{normalized_resolution}-{formatted_duration}]"
                
                # 基础组成结构为："视频名称" + "4个空格" + "视频分辨率-时长"
                base_spacing = "    "  # 4个空格
                base_spacing_width = font_obj.measure(base_spacing)
                info_width = font_obj.measure(info_part)
                
                # 计算基础组合内容的宽度（视频名称 + 4个空格 + 视频分辨率-时长）
                base_content_width = font_obj.measure(video['name']) + base_spacing_width + info_width
                
                # 显示区域宽度为325px
                display_area_width = 325
                
                if base_content_width <= display_area_width:
                    # 当总宽度小于显示区域时
                    # 计算可添加的额外空格数量
                    remaining_width = display_area_width - base_content_width
                    if remaining_width > 0:
                        # 计算需要在分辨率-时长前添加的额外空格数
                        space_width = font_obj.measure(" ")
                        num_extra_spaces = int(remaining_width / space_width) if space_width > 0 else 0
                        # 在分辨率-时长前添加计算得出的额外空格
                        extra_spacing = " " * num_extra_spaces
                        video_display = f"{video['name']}{base_spacing}{extra_spacing}{info_part}"
                    else:
                        # 如果不需要额外空格
                        video_display = f"{video['name']}{base_spacing}{info_part}"
                else:
                    # 当总宽度大于显示区域时
                    # 计算当前组合内容总宽度超出显示区域的数值
                    overflow_width = base_content_width - display_area_width
                    
                    # 需要从视频名称中减去的宽度
                    name_max_width = font_obj.measure(video['name']) - overflow_width
                    
                    if name_max_width > 0:
                        # 根据需要的宽度截取视频名称
                        truncated_name = ""
                        current_width = 0
                        
                        for char in video['name']:
                            char_width = font_obj.measure(char)
                            if current_width + char_width > name_max_width:
                                break
                            truncated_name += char
                            current_width += char_width
                        
                        # 保持"4个空格"+"视频分辨率-时长"的结构不变
                        video_display = f"{truncated_name}{base_spacing}{info_part}"
                    else:
                        # 如果视频名称本身太大以至于不能显示任何字符，则只显示信息部分
                        video_display = f"{base_spacing}{info_part}"
                self.unprocessed_listbox.insert(tk.END, video_display)
            else:  # 旧格式：仅文件名
                self.unprocessed_listbox.insert(tk.END, video)
        
        # 添加错误视频 - 显示视频卡死前的进度百分比
        for video in self.video_lists["error"]:
            if isinstance(video, dict):  # 新格式：包含视频信息的字典
                # 创建临时tkinter组件来测量文本宽度
                temp_font = ("微软雅黑", 13)
                import tkinter.font as tkFont
                font_obj = tkFont.Font(family=temp_font[0], size=temp_font[1])
                
                # 获取进度百分比信息
                if 'stuck_percentage' in video:
                    percentage = video['stuck_percentage']
                    info_part = f"[{percentage}%]"
                else:
                    # 如果没有进度信息，则显示默认信息
                    info_part = "[0%]"
                
                # 基础组成结构为："视频名称" + "4个空格" + "百分比数值"
                base_spacing = "    "  # 4个空格
                base_spacing_width = font_obj.measure(base_spacing)
                info_width = font_obj.measure(info_part)
                
                # 计算基础组合内容的宽度（视频名称 + 4个空格 + 百分比数值）
                base_content_width = font_obj.measure(video['name']) + base_spacing_width + info_width
                
                # 显示区域宽度为325px
                display_area_width = 325
                
                if base_content_width <= display_area_width:
                    # 当总宽度小于显示区域时
                    # 计算可添加的额外空格数量
                    remaining_width = display_area_width - base_content_width
                    if remaining_width > 0:
                        # 计算需要在百分比数值前添加的额外空格数
                        space_width = font_obj.measure(" ")
                        num_extra_spaces = int(remaining_width / space_width) if space_width > 0 else 0
                        # 在百分比数值前添加计算得出的额外空格
                        extra_spacing = " " * num_extra_spaces
                        video_display = f"{video['name']}{base_spacing}{extra_spacing}{info_part}"
                    else:
                        # 如果不需要额外空格
                        video_display = f"{video['name']}{base_spacing}{info_part}"
                else:
                    # 当总宽度大于显示区域时
                    # 计算当前组合内容总宽度超出显示区域的数值
                    overflow_width = base_content_width - display_area_width
                    
                    # 需要从视频名称中减去的宽度
                    name_max_width = font_obj.measure(video['name']) - overflow_width
                    
                    if name_max_width > 0:
                        # 根据需要的宽度截取视频名称
                        truncated_name = ""
                        current_width = 0
                        
                        for char in video['name']:
                            char_width = font_obj.measure(char)
                            if current_width + char_width > name_max_width:
                                break
                            truncated_name += char
                            current_width += char_width
                        
                        # 保持"4个空格"+"百分比数值"的结构不变
                        video_display = f"{truncated_name}{base_spacing}{info_part}"
                    else:
                        # 如果视频名称本身太大以至于不能显示任何字符，则只显示信息部分
                        video_display = f"{base_spacing}{info_part}"
                self.error_listbox.insert(tk.END, video_display)
            else:  # 旧格式：仅文件名
                self.error_listbox.insert(tk.END, video)
    
    def update_summary(self):
        """更新处理总结"""
        total = len(self.video_lists["processed"]) + len(self.video_lists["unprocessed"]) + len(self.video_lists["error"])
        summary_text = f"输入文件夹中视频数量: {total} | "
        summary_text += f"已处理视频数量: {len(self.video_lists['processed'])} | "
        summary_text += f"未处理视频数量: {len(self.video_lists['unprocessed'])} | "
        summary_text += f"处理出错视频数量: {len(self.video_lists['error'])}"
        
        self.summary_var.set(summary_text)
    
    def start_processing(self):
        """开始处理视频"""
        # 检查必要参数
        if not self.jasna_path_var.get():
            self.show_custom_messagebox("error", "错误", "请设置JASNA主程序地址！")
            return
        
        if not self.input_folder_var.get():
            self.show_custom_messagebox("error", "错误", "请设置输入文件夹！")
            return
        
        if not self.output_folder_var.get():
            self.show_custom_messagebox("error", "错误", "请设置输出文件夹！")
            return
        
        if len(self.video_lists["unprocessed"]) == 0:
            self.show_custom_messagebox("info", "提示", "没有需要处理的视频！")
            return
        
        # 重置停止标志和卡死标志
        self.stop_processing = False
        self.is_stuck = False
        self.stuck_detected = False
        
        # 在单独的线程中处理视频
        self.processing_thread = threading.Thread(target=self.process_videos)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.status_var.set("开始处理视频...")
    
    def process_videos(self):
        """处理视频的主函数"""
        # 记录原始的stuck_seconds值，用于在函数结束时恢复
        self.original_stuck_seconds = self.stuck_seconds_var.get()
        # 重置修改标志
        self.stuck_seconds_modified = False
        
        try:
            # 确保输出文件夹存在
            output_folder = self.output_folder_var.get()
            os.makedirs(output_folder, exist_ok=True)
            
            # 确保错误文件夹存在
            error_folder = self.error_folder_var.get()
            if error_folder:
                os.makedirs(error_folder, exist_ok=True)
            
            # 确保成功文件夹存在（新增）
            success_folder = self.success_folder_var.get()
            if success_folder:
                os.makedirs(success_folder, exist_ok=True)
            
            # 获取jasna主程序路径
            jasna_path = self.jasna_path_var.get()
            jasna_dir = os.path.dirname(jasna_path)
            jasna_exe_name = os.path.basename(jasna_path)
            
            # 处理每个未处理的视频
            for item in self.video_lists["unprocessed"][:]:  # 使用副本遍历
                # 处理新旧两种格式
                if isinstance(item, dict):
                    video_file = item['name']
                    video_info = item
                else:
                    video_file = item
                    video_info = None  # 旧格式，没有视频信息
                if self.stop_processing:
                    self.logger.info("处理已停止，退出视频处理循环")
                    break
                
                # 重置卡死标志
                self.is_stuck = False
                self.stuck_detected = False
                
                self.currently_processing = video_file
                self.current_video_var.set(video_file)
                
                # 重置进度信息显示
                self.root.after(0, self.reset_progress_display)
                
                # 构建输入路径
                input_path = os.path.join(self.input_folder_var.get(), video_file)
                
                self.logger.info(f"构建的输入路径: {input_path}")
                self.logger.info(f"输入文件夹: {self.input_folder_var.get()}")
                self.logger.info(f"视频文件: {video_file}")
                self.logger.info(f"输入路径是否存在: {os.path.exists(input_path)}")
                
                # 获取视频信息
                self.logger.info("开始调用get_video_info函数")
                success = self.get_video_info(input_path)
                self.logger.info(f"get_video_info函数返回值: {success}")
                
                # 记录视频处理开始时间，用于计算处理速度
                processing_start_time = time.time()
                
                # 记录视频信息显示状态（无论成功与否都继续处理）
                self.root.after(0, lambda: self.logger.info(f"视频信息显示状态 - 分辨率: {self.video_resolution_var.get()}, 帧率: {self.video_fps_var.get()}, 时长: {self.video_duration_var.get()}"))
                
                # 检查当前切片帧数是否已存在于历史记录中
                current_slice_frames = int(self.slice_frames_var.get())
                is_first_time = current_slice_frames not in self.slice_frames_history
                
                # 如果是第一次使用当前切片帧数，临时修改卡死超时时间
                is_first_time_for_model_compile = False  # 标记是否是模型编译的首次运行
                if is_first_time:
                    # 弹窗提示用户
                    self.root.after(0, lambda: self.show_custom_messagebox("info", "提示", "当前切片帧数为首次使用，需要编译模型 \n所需时间为0.2小时到4小时之间"))
                    # 临时将卡死超时时间设置为15000秒
                    self.stuck_seconds_var.set("15000")
                    self.stuck_seconds_modified = True  # 标记stuck_seconds值已被修改
                    is_first_time_for_model_compile = True  # 标记本次处理是首次模型编译
                
                # 构建输出文件名（添加后缀和.mp4扩展名）
                video_name = Path(video_file).stem
                suffix = self.output_suffix_var.get()
                final_output_filename = f"{video_name}{suffix}.mp4"
                final_output_path = os.path.join(output_folder, final_output_filename)
                
                # 启动卡死监测线程（根据是否首次使用设置不同的阈值）
                if is_first_time_for_model_compile:
                    self.start_stuck_monitor(custom_stuck_seconds=15000)
                else:
                    self.start_stuck_monitor()
                
                # 构建命令字符串
                encode_params = f'"{self.encode_params_var.get()}"'
                
                # 构建完整的命令
                cmd = f'.\\{jasna_exe_name} --input "{input_path}" --output "{final_output_path}" --max-clip-size {self.slice_frames_var.get()} --codec hevc --encoder-settings {encode_params}'
                
                self.logger.info(f"开始处理视频: {video_file}")
                self.logger.info(f"完整命令: {cmd}")
                self.logger.info(f"工作目录: {jasna_dir}")
                self.logger.info(f"当前切片帧数: {current_slice_frames}, 是否首次使用: {is_first_time}")
                
                # 重置进度记录
                self.progress_records = []
                self.last_progress_time = time.time()
                self.last_progress_value = 0
                self.progress_output_lines = []
                
                # 启动子进程 - 在jasna目录中执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # 合并stderr到stdout
                    universal_newlines=True,
                    shell=True,
                    cwd=jasna_dir,
                    bufsize=1  # 行缓冲
                )
                
                # 保存当前进程引用，用于停止功能
                self.current_process = process
                
                # 启动输出监控线程
                output_thread = threading.Thread(
                    target=self.monitor_jasna_output,
                    args=(process, video_file)
                )
                output_thread.daemon = True
                output_thread.start()
                
                # 等待进程完成
                return_code = process.wait()
                
                # 等待输出线程结束
                output_thread.join(timeout=5)
                
                # 停止卡死监测线程
                self.stop_stuck_monitor()
                
                # 清除当前进程引用
                self.current_process = None
                
                # 检查是否因卡死而终止
                if self.stuck_detected:
                    self.logger.warning(f"检测到视频卡死，已终止处理: {video_file}")
                    
                    # 如果是首次使用当前切片帧数且发生卡死（模型编译失败），弹窗提示错误
                    if is_first_time_for_model_compile:
                        self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", "模型编译失败，请检查系统设置、内存大小、显存大小，可适当调低切片帧数后重新运行"))
                        
                        # 立即恢复原始的stuck_seconds值，因为模型编译失败，不需要将切片帧数添加到历史记录
                        if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                            self.stuck_seconds_var.set(self.original_stuck_seconds)
                            self.stuck_seconds_modified = False
                            self.logger.info(f"模型编译失败 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                        
                        # 不将当前切片帧数添加到历史记录，直接跳出整个处理循环
                        break  # 终止所有后续视频处理任务
                    
                    # 执行卡死处理流程
                    self.handle_stuck_video(video_file, input_path, video_name, suffix, output_folder)
                    
                    # 重置当前处理视频
                    self.currently_processing = None
                    self.current_video_var.set("无")
                    
                    # 重置进度条
                    self.root.after(0, self.reset_progress_display)
                    
                    # 清空日志文件
                    self.clear_log_file()
                    
                    # 重要修复：跳过当前卡死视频，继续处理下一个视频
                    # 不需要执行后续的成功/失败检查，直接continue到下一个循环
                    # 重置停止标志，以便继续处理下一个视频
                    self.stop_processing = False
                    continue
                
                # 检查进程是否成功完成
                if return_code == 0 and not self.stop_processing:
                    # 处理成功
                    # 检查最终文件是否存在
                    success = self.check_final_file_exists(video_name, suffix, output_folder)
                    
                    if success:
                        # 根据数据结构类型进行相应处理
                        # 先找到要移除的项
                        item_to_remove = None
                        for item in self.video_lists["unprocessed"]:
                            if (isinstance(item, dict) and item['name'] == video_file) or \
                               (isinstance(item, str) and item == video_file):
                                item_to_remove = item
                                break
                        
                        if item_to_remove is not None:
                            self.video_lists["unprocessed"].remove(item_to_remove)
                            # 保持相同的数据结构格式，但为已处理视频添加处理速度信息
                            processing_end_time = time.time()
                            processing_duration = processing_end_time - processing_start_time  # 处理该视频的总运行时间（秒）
                            
                            # 获取视频原始时长（秒）
                            video_duration_seconds = 0
                            if isinstance(item_to_remove, dict):
                                # 尝试解析时长格式 HH:MM:SS 或 MM:SS
                                duration_str = item_to_remove['duration']
                                if duration_str != "未知":
                                    try:
                                        time_parts = duration_str.split(':')
                                        if len(time_parts) == 3:  # HH:MM:SS
                                            hours, minutes, seconds = map(int, time_parts)
                                            video_duration_seconds = hours * 3600 + minutes * 60 + seconds
                                        elif len(time_parts) == 2:  # MM:SS
                                            minutes, seconds = map(int, time_parts)
                                            video_duration_seconds = minutes * 60 + seconds
                                    except:
                                        video_duration_seconds = 0
                            
                            # 计算处理速度
                            if video_duration_seconds > 0:
                                processing_speed = processing_duration / video_duration_seconds
                                # 保留最多三位数字
                                processing_speed_str = self.format_to_three_digits(processing_speed)
                            else:
                                processing_speed_str = "未知"
                            
                            # 创建已处理视频的信息（包含处理速度）
                            if isinstance(item_to_remove, dict):
                                processed_video_info = {
                                    'name': item_to_remove['name'],
                                    'processing_speed': processing_speed_str
                                }
                            else:
                                processed_video_info = {
                                    'name': video_file,
                                    'processing_speed': processing_speed_str
                                }
                            
                            self.video_lists["processed"].append(processed_video_info)
                        
                        # 更新GUI
                        self.root.after(0, self.update_lists_display)
                        self.root.after(0, self.update_summary)
                        
                        # 如果是首次使用当前切片帧数，将切片帧数添加到历史记录
                        if is_first_time:
                            current_slice_frames = int(self.slice_frames_var.get())
                            if current_slice_frames not in self.slice_frames_history:
                                self.slice_frames_history.append(current_slice_frames)
                                self.logger.info(f"将切片帧数 {current_slice_frames} 添加到历史记录")
                                
                                # 立即恢复原始的stuck_seconds值，避免后续视频处理受到影响
                                if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                    self.stuck_seconds_var.set(self.original_stuck_seconds)
                                    self.stuck_seconds_modified = False
                                    self.logger.info(f"首次运行完成 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                        
                        # 处理成功后移动源视频到成功文件夹（新增）
                        success_folder = self.success_folder_var.get()
                        if success_folder:
                            success_moved = self.move_to_success_folder(input_path, video_file)
                            if success_moved:
                                self.logger.info(f"成功视频已移动到成功文件夹: {video_file}")
                            else:
                                self.logger.warning(f"成功视频移动失败: {video_file}")
                        
                        self.logger.info(f"视频处理完成: {video_file}")
                        self.root.after(0, lambda: self.status_var.set(f"视频处理完成: {video_file}"))
                    else:
                        # 最终文件不存在，视为处理失败
                        self.logger.error(f"视频处理完成但最终文件不存在: {video_file}")
                        
                        # 将视频从未处理列表移到错误列表
                        # 先找到要移除的项
                        item_to_remove = None
                        for item in self.video_lists["unprocessed"]:
                            if (isinstance(item, dict) and item['name'] == video_file) or \
                               (isinstance(item, str) and item == video_file):
                                item_to_remove = item
                                break
                        
                        if item_to_remove is not None:
                            self.video_lists["unprocessed"].remove(item_to_remove)
                            # 保持相同的数据结构格式
                            if isinstance(item_to_remove, dict):
                                self.video_lists["error"].append(item_to_remove)
                            else:
                                self.video_lists["error"].append(video_file)
                        
                        # 更新GUI
                        self.root.after(0, self.update_lists_display)
                        self.root.after(0, self.update_summary)
                        
                        self.logger.error(f"视频处理失败，最终文件未生成: {video_file}")
                        self.root.after(0, lambda: self.status_var.set(f"视频处理失败，最终文件未生成: {video_file}"))
                else:
                    # 处理失败或被停止
                    if self.stop_processing:
                        self.logger.info(f"视频处理被用户停止: {video_file}")
                        
                        # 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
                        self.root.after(2000, lambda: self.cleanup_temp_files_after_stop(video_name, suffix, output_folder, delete_final_file=True))
                        
                        # 如果用户停止，不清空列表，视频保留在未处理列表中
                        self.root.after(0, lambda: self.status_var.set(f"视频处理被停止: {video_file}"))
                        break  # 跳出循环，不再处理后续视频
                    else:
                        self.logger.error(f"JASNA返回错误代码: {return_code}")
                        
                        # 清理可能生成的临时文件（包括最终文件）
                        self.cleanup_temp_files(video_name, suffix, output_folder, delete_final_file=True)
                        
                        # 将视频从未处理列表移到错误列表
                        # 先找到要移除的项
                        item_to_remove = None
                        for item in self.video_lists["unprocessed"]:
                            if (isinstance(item, dict) and item['name'] == video_file) or \
                               (isinstance(item, str) and item == video_file):
                                item_to_remove = item
                                break
                        
                        if item_to_remove is not None:
                            self.video_lists["unprocessed"].remove(item_to_remove)
                            # 保持相同的数据结构格式
                            if isinstance(item_to_remove, dict):
                                self.video_lists["error"].append(item_to_remove)
                            else:
                                self.video_lists["error"].append(video_file)
                        
                        # 更新GUI
                        self.root.after(0, self.update_lists_display)
                        self.root.after(0, self.update_summary)
                        
                        self.logger.error(f"视频处理失败: {video_file}")
                        self.root.after(0, lambda: self.status_var.set(f"视频处理失败: {video_file}"))
                
                # 重置当前处理视频
                self.currently_processing = None
                self.current_video_var.set("无")
                
                # 清空日志文件
                self.clear_log_file()
                
                # 重置进度条
                self.root.after(0, self.reset_progress_display)
            
            # 所有视频处理完成
            if not self.stop_processing:
                self.root.after(0, lambda: self.status_var.set("所有视频处理完成！"))
                self.root.after(0, lambda: self.show_custom_messagebox("info", "完成", "所有视频处理完成！"))
                self.logger.info("所有视频处理完成！")
                
                # 保存切片帧数历史记录到配置文件
                self.root.after(0, self.save_settings)
                
                # 根据用户选择执行相应操作
                self.root.after(0, self.execute_post_processing_action)
            else:
                self.root.after(0, lambda: self.status_var.set("处理已停止"))
                self.logger.info("处理已停止")
            
            # 处理完成后强制终止所有jasna.exe进程
            self.logger.info("处理完成，强制终止所有jasna.exe进程")
            self.kill_all_jasna_processes()
            
            # 在所有处理完成后清空日志文件
            self.clear_log_file()
            
        except Exception as e:
            self.logger.error(f"处理视频时出错: {str(e)}", exc_info=True)
            self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", f"处理视频时出错: {str(e)}"))
        finally:
            # 确保卡死监测线程停止
            self.stop_stuck_monitor()
            
            # 如果stuck_seconds值被修改过，恢复原始值
            if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                self.stuck_seconds_var.set(self.original_stuck_seconds)
                self.logger.info(f"恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
            
            # 异常情况下也强制终止所有jasna.exe进程
            try:
                self.logger.info("异常情况，强制终止所有jasna.exe进程")
                self.kill_all_jasna_processes()
            except Exception as e:
                self.logger.error(f"异常情况下终止jasna.exe进程时出错: {str(e)}")
            
            # 在异常处理的finally块中也要清空日志文件
            self.clear_log_file()
    
    def check_final_file_exists(self, video_name, suffix, output_folder):
        """检查最终文件是否存在"""
        try:
            # 最终输出文件
            final_output_file = os.path.join(output_folder, f"{video_name}{suffix}.mp4")
            
            # 检查最终文件是否存在且大小大于0
            if os.path.exists(final_output_file) and os.path.getsize(final_output_file) > 0:
                self.logger.info(f"最终文件已存在: {final_output_file}")
                return True
            else:
                self.logger.warning(f"最终文件不存在或为空: {final_output_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"检查最终文件时出错: {str(e)}")
            return False
    
    def handle_stuck_video(self, video_file, input_path, video_name, suffix, output_folder):
        """处理卡死的视频"""
        try:
            self.logger.warning(f"开始处理卡死视频: {video_file}")
            
            # 1. 强制终止当前运行的JASNA进程
            self.kill_all_jasna_processes()
            
            # 2. 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
            time.sleep(2)  # 等待2秒确保进程完全终止
            self.cleanup_temp_files(video_name, suffix, output_folder, delete_final_file=True)
            
            # 3. 把当前视频名字打印到GUI中"处理出错视频列表"中
            # 先找到要移除的项
            item_to_remove = None
            for item in self.video_lists["unprocessed"]:
                if (isinstance(item, dict) and item['name'] == video_file) or \
                   (isinstance(item, str) and item == video_file):
                    item_to_remove = item
                    break
            
            if item_to_remove is not None:
                self.video_lists["unprocessed"].remove(item_to_remove)
                
                # 检查错误列表中是否已存在该视频
                video_exists_in_error = False
                for error_item in self.video_lists["error"]:
                    if (isinstance(error_item, dict) and error_item['name'] == video_file) or \
                       (isinstance(error_item, str) and error_item == video_file):
                        video_exists_in_error = True
                        break
                
                if not video_exists_in_error:
                    # 保持相同的数据结构格式，但添加最后的进度百分比信息
                    if isinstance(item_to_remove, dict):
                        # 如果是字典格式，添加进度信息
                        stuck_video_info = item_to_remove.copy()  # 复制原始信息
                        stuck_video_info['stuck_percentage'] = self.last_progress_value  # 添加卡死时的进度百分比
                        self.video_lists["error"].append(stuck_video_info)
                    else:
                        # 如果是字符串格式，创建字典格式包含进度信息
                        stuck_video_info = {
                            'name': video_file,
                            'resolution': '未知',
                            'fps': 0,
                            'duration': '未知',
                            'stuck_percentage': self.last_progress_value  # 添加卡死时的进度百分比
                        }
                        self.video_lists["error"].append(stuck_video_info)
            
            # 更新GUI
            self.root.after(0, self.update_lists_display)
            self.root.after(0, self.update_summary)
            
            # 4. 把当前卡死视频移动到"自定义设置"中用户设置的"出错视频放置文件夹"的目录中
            # 如果用户未设置该文件夹，则源视频保持在原位置，不进行移动
            error_folder = self.error_folder_var.get()
            if error_folder:
                error_moved = self.move_to_error_folder(input_path, video_file)
                if error_moved:
                    self.logger.info(f"卡死视频已移动到错误文件夹: {video_file}")
                    self.root.after(0, lambda: self.status_var.set(f"视频卡死，已移动到错误文件夹: {video_file}"))
                else:
                    self.logger.warning(f"卡死视频移动失败: {video_file}")
                    self.root.after(0, lambda: self.status_var.set(f"视频卡死但移动失败: {video_file}"))
            else:
                self.logger.info(f"未设置出错文件夹，卡死视频保持在原位置: {video_file}")
                self.root.after(0, lambda: self.status_var.set(f"视频卡死，未设置出错文件夹，视频保持在原位置: {video_file}"))
            
            # 5. 主程序进入下一个循环，继续处理下一个视频
            # (这个在process_videos函数中会自动继续下一个循环)
            
            self.logger.info(f"卡死视频处理完成: {video_file}")
            
        except Exception as e:
            self.logger.error(f"处理卡死视频时出错: {str(e)}")
    
    def kill_all_jasna_processes(self):
        """强制终止所有名为jasna.exe的进程"""
        try:
            self.logger.info("开始强制终止所有jasna.exe进程...")
            
            if sys.platform == "win32":
                # 方法1: 使用taskkill终止进程树
                subprocess.run("taskkill /F /T /IM jasna.exe", 
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info("已使用taskkill /F /T /IM jasna.exe命令")
                
                # 等待1秒
                time.sleep(1)
                
                # 方法2: 使用wmic命令终止进程
                subprocess.run("wmic process where name='jasna.exe' delete", 
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info("已使用wmic命令终止jasna.exe进程")
                
                # 等待1秒
                time.sleep(1)
                
                # 方法3: 使用PowerShell命令终止进程
                subprocess.run("powershell -Command \"Get-Process -Name 'jasna' -ErrorAction SilentlyContinue | Stop-Process -Force\"", 
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info("已使用PowerShell命令终止jasna进程")
                
                # 方法4: 使用Python的psutil（如果可用）
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if proc.info['name'] and proc.info['name'].lower() == 'jasna.exe':
                                proc.kill()
                                self.logger.info(f"已使用psutil终止进程: {proc.info['pid']}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            pass
                except ImportError:
                    self.logger.info("未安装psutil，跳过psutil终止方法")
                
                # 最后再检查一次，确保进程已终止
                time.sleep(1)
                check_result = subprocess.run("tasklist /FI \"IMAGENAME eq jasna.exe\"", 
                                            shell=True, capture_output=True, text=True)
                if "jasna.exe" not in check_result.stdout:
                    self.logger.info("确认所有jasna.exe进程已被终止")
                else:
                    self.logger.warning("仍有jasna.exe进程在运行，尝试其他方法...")
                    
                    # 尝试更暴力的方法
                    subprocess.run("taskkill /F /IM javaw.exe >nul 2>&1", shell=True)
                    subprocess.run("taskkill /F /IM java.exe >nul 2>&1", shell=True)
                    
            else:
                # 非Windows系统
                self.logger.warning("非Windows系统，使用通用方法终止进程")
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.terminate()
                    time.sleep(1)
                    if self.current_process.poll() is None:
                        self.current_process.kill()
                
        except Exception as e:
            self.logger.error(f"终止jasna.exe进程时出错: {str(e)}")
    
    def stuck_monitor_callback(self, message):
        """卡死监测回调函数"""
        # 只在第一次检测到卡死时处理
        if not self.stuck_detected:
            self.logger.warning(f"接收到卡死信号: {message.get('message')}")
            self.is_stuck = True
            self.stuck_detected = True
            
            # 注意：这里不设置停止标志，只标记卡死检测，以便处理视频循环继续
            # 这样就不会影响其他视频的处理
            
            # 强制终止当前运行的JASNA进程
            try:
                # 首先尝试正常的terminate
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.terminate()
                    
                    # 等待进程结束
                    try:
                        self.current_process.wait(timeout=2)
                        self.logger.info("JASNA进程已正常终止（卡死检测）")
                    except subprocess.TimeoutExpired:
                        # 如果进程未终止，尝试强制终止
                        if self.current_process.poll() is None:
                            # 使用多种方法强制终止所有jasna.exe进程
                            self.kill_all_jasna_processes()
            except Exception as e:
                self.logger.error(f"终止JASNA进程时出错（卡死检测）: {str(e)}")
            
            # 清空日志文件（新添加的，在执行新的处理命令前清空日志）
            self.clear_log_file()
    
    def start_stuck_monitor(self, custom_stuck_seconds=None):
        """启动卡死监测线程"""
        try:
            # 获取卡死秒数，优先使用自定义值
            if custom_stuck_seconds is not None:
                stuck_seconds = custom_stuck_seconds
            else:
                stuck_seconds = int(self.stuck_seconds_var.get())
            
            # 停止现有的监测线程
            self.stop_stuck_monitor()
            
            # 创建并启动卡死监测线程
            self.stuck_monitor = StuckMonitorThread(
                log_file_path='jasna_gui.log',
                stuck_seconds=stuck_seconds,
                callback=self.stuck_monitor_callback
            )
            self.stuck_monitor.start()
            
            self.logger.info(f"卡死监测线程已启动，阈值: {stuck_seconds}秒")
            
        except Exception as e:
            self.logger.error(f"启动卡死监测线程失败: {str(e)}")
    
    def stop_stuck_monitor(self):
        """停止卡死监测线程"""
        try:
            if self.stuck_monitor:
                self.stuck_monitor.stop()
                self.stuck_monitor = None
                self.logger.info("卡死监测线程已停止")
        except Exception as e:
            self.logger.error(f"停止卡死监测线程失败: {str(e)}")
    
    def cleanup_temp_files(self, video_name, suffix, output_folder, delete_final_file=False):
        """清理临时文件"""
        try:
            # 要删除的临时文件模式
            temp_patterns = [
                f"{video_name}{suffix}.hevc",
                f"{video_name}{suffix}_temp_video.mp4",
            ]
            
            # 如果需要删除最终文件，则添加到列表中
            if delete_final_file:
                temp_patterns.append(f"{video_name}{suffix}.mp4")
            
            for pattern in temp_patterns:
                temp_file = os.path.join(output_folder, pattern)
                if os.path.exists(temp_file):
                    try:
                        # 尝试多次删除文件，直到成功或超时
                        max_attempts = 10
                        for attempt in range(max_attempts):
                            try:
                                os.remove(temp_file)
                                self.logger.info(f"已删除临时文件: {temp_file}")
                                break
                            except (PermissionError, OSError) as e:
                                if attempt < max_attempts - 1:
                                    self.logger.info(f"临时文件被占用，等待1秒后重试 (尝试 {attempt+1}/{max_attempts})")
                                    time.sleep(1)
                                else:
                                    self.logger.warning(f"删除临时文件失败 {temp_file}: {str(e)}")
                                    # 尝试强制删除
                                    try:
                                        if sys.platform == "win32":
                                            # Windows下使用del命令强制删除
                                            subprocess.run(f'del /F "{temp_file}"', shell=True, 
                                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                            self.logger.info(f"强制删除临时文件: {temp_file}")
                                    except:
                                        self.logger.error(f"强制删除临时文件失败: {temp_file}")
                    except Exception as e:
                        self.logger.warning(f"删除临时文件失败 {temp_file}: {str(e)}")
                        
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {str(e)}")
            return False
            
        return True
    
    def cleanup_temp_files_after_stop(self, video_name, suffix, output_folder, delete_final_file=False):
        """停止处理后清理临时文件"""
        self.logger.info(f"停止处理后，开始清理临时文件: {video_name}")
        self.cleanup_temp_files(video_name, suffix, output_folder, delete_final_file)
    
    def move_to_error_folder(self, input_path, video_file):
        """移动出错视频到错误文件夹"""
        error_folder = self.error_folder_var.get()
        if error_folder:
            try:
                os.makedirs(error_folder, exist_ok=True)
                destination = os.path.join(error_folder, video_file)
                
                # 确保源文件存在
                if not os.path.exists(input_path):
                    self.logger.error(f"源文件不存在，无法移动: {input_path}")
                    return False
                
                # 尝试多次移动文件，直到成功或超时
                max_attempts = 15
                for attempt in range(max_attempts):
                    try:
                        shutil.move(input_path, destination)
                        self.logger.info(f"已将出错视频移动到: {destination}")
                        return True
                    except (PermissionError, OSError) as e:
                        if attempt < max_attempts - 1:
                            wait_time = 2 if attempt < 5 else 5
                            self.logger.info(f"文件被占用，等待{wait_time}秒后重试 (尝试 {attempt+1}/{max_attempts})")
                            time.sleep(wait_time)
                        else:
                            self.logger.error(f"移动出错视频失败: {str(e)}")
                            # 最后一次尝试，使用复制然后删除的方式
                            try:
                                shutil.copy2(input_path, destination)
                                os.remove(input_path)
                                self.logger.info(f"已通过复制+删除方式移动文件到: {destination}")
                                return True
                            except Exception as copy_error:
                                self.logger.error(f"复制+删除方式也失败: {str(copy_error)}")
                                return False
                
                return False
            except Exception as e:
                self.logger.error(f"移动出错视频失败: {str(e)}")
                return False
        else:
            self.logger.warning(f"出错视频文件夹未设置，无法移动出错视频: {video_file}")
            return False
    
    def format_to_three_digits(self, number):
        """格式化数字为根据首位是否为0决定保留2位或3位有效数字的字符串"""
        if number == 0:
            return "0.00"
        
        # 如果数字的绝对值小于1（即以0开头，如0.xxxx），则保留2位有效数字
        if abs(number) < 1:
            return f"{number:.2g}"
        else:
            # 否则保留3位有效数字
            return f"{number:.3g}"
    
    def move_to_success_folder(self, input_path, video_file):
        """移动成功处理视频到成功文件夹（新增）"""
        success_folder = self.success_folder_var.get()
        if success_folder:
            try:
                os.makedirs(success_folder, exist_ok=True)
                destination = os.path.join(success_folder, video_file)
                
                # 确保源文件存在
                if not os.path.exists(input_path):
                    self.logger.error(f"源文件不存在，无法移动: {input_path}")
                    return False
                
                # 延迟2秒后移动源视频
                self.logger.info(f"延迟2秒后移动成功视频到成功文件夹: {video_file}")
                self.root.after(2000, lambda: self._perform_move_to_success(input_path, destination, video_file))
                
                return True
            except Exception as e:
                self.logger.error(f"移动成功视频失败: {str(e)}")
                return False
        else:
            self.logger.info(f"成功视频文件夹未设置，视频保持在原位置: {video_file}")
            return False
    
    def move_already_processed_to_success_folder(self, input_path, video_file):
        """移动已处理过的视频到成功文件夹"""
        success_folder = self.success_folder_var.get()
        if success_folder:
            try:
                os.makedirs(success_folder, exist_ok=True)
                destination = os.path.join(success_folder, video_file)
                
                # 确保源文件存在
                if not os.path.exists(input_path):
                    self.logger.error(f"源文件不存在，无法移动: {input_path}")
                    return False
                
                # 立即移动源视频
                self.logger.info(f"移动已处理视频到成功文件夹: {video_file}")
                self._perform_move_to_success(input_path, destination, video_file)
                
                return True
            except Exception as e:
                self.logger.error(f"移动已处理视频失败: {str(e)}")
                return False
        else:
            self.logger.info(f"成功视频文件夹未设置，视频保持在原位置: {video_file}")
            return False
    
    def _perform_move_to_success(self, input_path, destination, video_file):
        """执行移动成功视频到成功文件夹的实际操作"""
        try:
            # 尝试多次移动文件，直到成功或超时
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    shutil.move(input_path, destination)
                    self.logger.info(f"已将成功视频移动到: {destination}")
                    break
                except (PermissionError, OSError) as e:
                    if attempt < max_attempts - 1:
                        wait_time = 2
                        self.logger.info(f"文件被占用，等待{wait_time}秒后重试 (尝试 {attempt+1}/{max_attempts})")
                        time.sleep(wait_time)
                    else:
                        self.logger.error(f"移动成功视频失败: {str(e)}")
                        # 最后一次尝试，使用复制然后删除的方式
                        try:
                            shutil.copy2(input_path, destination)
                            os.remove(input_path)
                            self.logger.info(f"已通过复制+删除方式移动成功文件到: {destination}")
                        except Exception as copy_error:
                            self.logger.error(f"复制+删除方式也失败: {str(copy_error)}")
        except Exception as e:
            self.logger.error(f"执行移动成功视频时出错: {str(e)}")
    
    def clear_log_file(self):
        """清空日志文件"""
        try:
            log_file_path = 'jasna_gui.log'
            if os.path.exists(log_file_path):
                # 使用系统默认编码（ANSI）清空日志文件
                import locale
                system_encoding = locale.getpreferredencoding()
                with open(log_file_path, 'w', encoding=system_encoding) as f:
                    f.write('')
                self.logger.info("已清空日志文件")
        except Exception as e:
            self.logger.error(f"清空日志文件失败: {str(e)}")
    
    def monitor_jasna_output(self, process, video_file):
        """监控JASNA的输出，解析进度信息"""
        self.logger.info(f"开始监控JASNA输出: {video_file}")
        
        try:
            # 持续读取输出
            while True:
                # 检查进程是否已结束
                if process.poll() is not None:
                    break
                
                # 检查停止标志和卡死标志
                if self.stop_processing or self.stuck_detected:
                    self.logger.info(f"检测到停止或卡死标志，终止JASNA进程: {video_file}")
                    self.kill_all_jasna_processes()
                    break
                
                # 读取一行输出
                line = process.stdout.readline()
                if line:
                    # 记录输出
                    self.progress_output_lines.append(line.strip())
                    
                    # 尝试解析进度信息
                    progress_info = self.parse_jasna_progress(line)
                    if progress_info:
                        # 更新进度显示
                        self.root.after(0, lambda p=progress_info: self.update_detailed_progress(p))
                    
                    # 记录日志
                    if "error" in line.lower() or "failed" in line.lower():
                        self.logger.error(f"JASNA输出 - {video_file}: {line.strip()}")
                    elif "warning" in line.lower():
                        self.logger.warning(f"JASNA输出 - {video_file}: {line.strip()}")
                    else:
                        # 记录进度信息行
                        if 'Processing video:' in line:
                            self.logger.info(f"JASNA输出 - {video_file}: {line.strip()}")
                else:
                    # 没有输出，短暂休眠
                    time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"监控JASNA输出时出错: {str(e)}")
        
        self.logger.info(f"JASNA输出监控结束: {video_file}")
    
    def parse_jasna_progress(self, line):
        """解析JASNA输出中的进度信息"""
        progress_info = {}
        
        # 修复：支持带小数点的帧数（如208912.0f）
        # 修改帧数匹配部分，从 (\d+) 改为 (\d+\.?\d*) 以支持整数和小数
        detailed_match = re.search(
            r'Processing video:\s*(\d+)%.*?Processed:\s*([\d:]+)\s*\((\d+\.?\d*)[fF]\).*?Remaining:\s*([\d:]+)\s*\((\d+\.?\d*)[fF]\).*?Speed:\s*([\d\.]+)[fF][pP][sS]',
            line
        )
        
        if detailed_match:
            try:
                progress_info['progress'] = int(detailed_match.group(1))
                progress_info['elapsed_time'] = detailed_match.group(2)
                # 将带小数的帧数转换为整数
                frames_processed_float = float(detailed_match.group(3))
                progress_info['frames_processed'] = int(frames_processed_float)
                progress_info['remaining_time'] = detailed_match.group(4)
                remaining_frames_float = float(detailed_match.group(5))
                progress_info['remaining_frames'] = int(remaining_frames_float)
                progress_info['speed_fps'] = float(detailed_match.group(6))
                progress_info['total_frames'] = progress_info['frames_processed'] + progress_info['remaining_frames']
                
                return progress_info
            except Exception as e:
                self.logger.debug(f"解析详细进度信息失败: {str(e)}，行内容: {line}")
        
        # 备选正则表达式，匹配更简单的格式
        simple_match = re.search(r'Processing video:\s*(\d+)%', line)
        if simple_match:
            try:
                progress_info['progress'] = int(simple_match.group(1))
            except Exception as e:
                self.logger.debug(f"解析简单进度信息失败: {str(e)}")
            
        # 尝试匹配帧数信息 - 修复：支持带小数的帧数
        frames_match = re.search(r'(\d+\.?\d*)\s*/\s*(\d+\.?\d*)\s*[fF]rames', line, re.IGNORECASE)
        if frames_match:
            try:
                frames_processed_float = float(frames_match.group(1))
                total_frames_float = float(frames_match.group(2))
                progress_info['frames_processed'] = int(frames_processed_float)
                progress_info['total_frames'] = int(total_frames_float)
                if 'progress' not in progress_info and progress_info['total_frames'] > 0:
                    progress_info['progress'] = int((progress_info['frames_processed'] / progress_info['total_frames']) * 100)
            except Exception as e:
                self.logger.debug(f"解析帧数信息失败: {str(e)}")
        
        # 如果还没有匹配到进度，尝试匹配单独的百分比
        if 'progress' not in progress_info:
            percent_match = re.search(r'(\d+)%', line)
            if percent_match:
                try:
                    progress_info['progress'] = int(percent_match.group(1))
                except Exception as e:
                    self.logger.debug(f"解析百分比失败: {str(e)}")
        
        return progress_info
    
    def update_detailed_progress(self, progress_info):
        """更新详细进度信息"""
        try:
            # 更新进度条和百分比
            if 'progress' in progress_info:
                self.progress_bar['value'] = progress_info['progress']
                self.progress_percent_var.set(f"{progress_info['progress']}%")
                # 记录最后的进度值，以便在视频卡死时使用
                self.last_progress_value = progress_info['progress']
            
            # 更新详细信息
            if 'elapsed_time' in progress_info:
                self.elapsed_time_var.set(progress_info['elapsed_time'])
            if 'remaining_time' in progress_info:
                self.remaining_time_var.set(progress_info['remaining_time'])
            if 'speed_fps' in progress_info:
                self.processing_speed_var.set(f"{progress_info['speed_fps']:.1f}fps")
            if 'frames_processed' in progress_info:
                self.processed_frames_var.set(str(progress_info['frames_processed']))
            if 'remaining_frames' in progress_info:
                self.remaining_frames_var.set(str(progress_info['remaining_frames']))
            if 'total_frames' in progress_info:
                self.total_frames_var.set(str(progress_info['total_frames']))
                
            # 记录日志以便调试
            self.logger.debug(f"更新进度信息: {progress_info}")
        except Exception as e:
            self.logger.error(f"更新详细进度信息失败: {str(e)}")
    
    def update_progress_display(self, progress):
        """更新进度显示"""
        self.progress_bar['value'] = progress
        self.progress_percent_var.set(f"{progress}%")
    
    def update_frame_info(self, frames_processed, total_frames):
        """更新帧数信息"""
        self.processed_frames_var.set(str(frames_processed))
        self.total_frames_var.set(str(total_frames))
    
    def get_video_info(self, video_path):
        """获取视频信息（分辨率、帧率、时长）"""
        try:
            # 尝试使用ffprobe获取视频信息
            import subprocess
            import json
            import os
            from pathlib import Path
            import time
            import sys
            
            # Windows平台上隐藏控制台窗口的标志
            startupinfo = None
            if sys.platform.startswith('win'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 使用pathlib处理路径，更好地处理中文字符
            video_path_obj = Path(video_path)
            video_path_str = str(video_path_obj.resolve())  # 获取绝对路径
            
            # 检查视频文件是否存在
            if not video_path_obj.exists():
                self.logger.error(f"视频文件不存在: {video_path_str}")
                return False
            
            self.logger.info(f"开始获取视频信息: {video_path_str}")
            
            # 构建ffprobe命令，优先使用系统PATH中的ffprobe
            ffprobe_path = 'ffprobe'
            
            # 检查系统PATH中是否有ffprobe
            try:
                subprocess.run([ffprobe_path, '-version'], 
                             capture_output=True, text=True, timeout=5,
                             startupinfo=startupinfo)
                self.logger.info("使用系统PATH中的ffprobe")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # 如果系统PATH中没有ffprobe，尝试使用程序所在文件夹的ffprobe
                script_dir = Path(__file__).parent.resolve()
                local_ffprobe_path = script_dir / 'ffprobe.exe'
                if local_ffprobe_path.exists():
                    ffprobe_path = str(local_ffprobe_path)
                    self.logger.info(f"使用本地ffprobe: {ffprobe_path}")
                else:
                    self.logger.error("未找到ffprobe，请确保已安装ffmpeg并将bin目录添加到系统PATH")
                    return False
            
            # 构建ffprobe命令，优先使用系统PATH中的ffprobe
            cmd_str = f'{ffprobe_path} -v quiet -print_format json -show_format -show_streams "{video_path_str}"'
            self.logger.info(f"执行ffprobe命令: {cmd_str}")
            
            # 在Windows系统上，使用shell=True来更好地处理中文路径
            # 同时设置适当的编码
            if sys.platform.startswith('win'):
                # Windows平台的特殊处理
                # 针对打包后的EXE环境，使用系统默认编码(cp936)处理中文路径
                import locale
                # 尝试多种编码方式以确保兼容性
                encodings_to_try = ['utf-8', 'gbk', 'gb2312', locale.getpreferredencoding()]
                
                result = None
                last_exception = None
                
                # 为了解决第一个视频信息获取失败的问题，尝试多次执行
                max_retries = 5  # 增加重试次数
                retry_count = 0
                
                while retry_count < max_retries:
                    for encoding in encodings_to_try:
                        try:
                            # 在每次调用ffprobe之前添加短暂延迟，特别是在第一次调用时
                            if retry_count == 0:
                                # 首次尝试前稍作延迟，给ffprobe初始化时间
                                time.sleep(1)  # 增加初始延迟
                            
                            result = subprocess.run(
                                cmd_str,  # 直接使用构造好的字符串命令，其中路径已用双引号包围
                                capture_output=True, 
                                text=True, 
                                timeout=45,  # 增加超时时间
                                shell=True,
                                encoding=encoding,  # 尝试不同的编码
                                startupinfo=startupinfo  # 隐藏控制台窗口
                            )
                            
                            # 检查执行结果
                            if result.returncode == 0 and result.stdout:
                                # 成功获取到信息，跳出重试循环
                                break
                            else:
                                self.logger.warning(f"ffprobe执行失败 (第{retry_count+1}次尝试, 编码: {encoding}): 返回码 {result.returncode}, 输出: {result.stdout[:100] if result.stdout else 'None'}, 错误: {result.stderr[:100] if result.stderr else 'None'}")
                        except UnicodeEncodeError as e:
                            last_exception = e
                            self.logger.warning(f"编码错误 (第{retry_count+1}次尝试, 编码: {encoding}): {str(e)}")
                            continue
                        except Exception as e:
                            last_exception = e
                            self.logger.warning(f"执行错误 (第{retry_count+1}次尝试, 编码: {encoding}): {str(e)}")
                            continue
                    
                    # 如果成功获取到结果，跳出重试循环
                    if result and result.returncode == 0 and result.stdout:
                        break
                    
                    # 如果执行失败，增加重试计数
                    retry_count += 1
                    if retry_count < max_retries:
                        wait_time = retry_count * 2  # 增加等待时间，指数级递增
                        self.logger.info(f"等待{wait_time}秒后重试...")
                        time.sleep(wait_time)  # 增加延迟，给系统更多时间
                
                # 如果所有重试都失败，返回False
                if result is None or result.returncode != 0 or not result.stdout:
                    self.logger.error(f"获取视频信息失败 (已重试{max_retries}次): {video_path_str}")
                    return False
            else:
                # 其他平台使用原方法
                cmd_args = [
                    ffprobe_path,
                    '-v', 'quiet',
                    '-print_format', 'json',
                    '-show_format',
                    '-show_streams',
                    '"' + video_path_str + '"'
                ]
                result = subprocess.run(cmd_args, capture_output=True, text=True, timeout=30,
                                       startupinfo=startupinfo)  # 隐藏控制台窗口
            
            self.logger.info(f"ffprobe返回码: {result.returncode}")
            self.logger.info(f"ffprobe stdout长度: {len(result.stdout) if result.stdout else 0}")
            self.logger.info(f"ffprobe stderr: {result.stderr}")
            
            if result.returncode != 0:
                self.logger.error(f"ffprobe执行失败，返回码: {result.returncode}")
                self.logger.error(f"ffprobe错误信息: {result.stderr}")
                return False
            
            if not result.stdout:
                self.logger.error("ffprobe没有返回任何输出")
                return False
            
            try:
                data = json.loads(result.stdout)
                self.logger.info(f"解析JSON成功，包含streams: {len(data.get('streams', []))}, format信息: {'format' in data}")
                
                if not data:
                    self.logger.warning("ffprobe返回了空的JSON对象")
                    return False
                
                # 获取视频流信息
                video_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video':
                        video_stream = stream
                        break
                
                if not video_stream:
                    self.logger.error("未找到视频流")
                    return False
                
                # 获取分辨率
                width = video_stream.get('width', 0)
                height = video_stream.get('height', 0)
                if width and height:
                    resolution = f"{width}×{height}"
                    self.video_resolution_var.set(resolution)
                    self.logger.info(f"获取分辨率: {resolution}")
                else:
                    self.logger.warning("无法获取分辨率信息")
                    self.video_resolution_var.set("未知")
                
                # 获取帧率
                r_frame_rate = video_stream.get('r_frame_rate', '0/0')
                if r_frame_rate and r_frame_rate != '0/0':
                    try:
                        num, den = map(int, r_frame_rate.split('/'))
                        if den != 0:
                            fps = round(num / den, 2)
                            fps_str = f"{fps}"
                        else:
                            fps_str = "未知"
                    except (ValueError, ZeroDivisionError):
                        fps_str = "未知"
                else:
                    fps_str = "未知"
                
                self.video_fps_var.set(fps_str)
                self.logger.info(f"获取帧率: {fps_str}")
                
                # 获取时长
                duration = data.get('format', {}).get('duration', '0')
                try:
                    duration_seconds = float(duration)
                    if duration_seconds <= 0:
                        duration_str = "未知"
                    else:
                        hours = int(duration_seconds // 3600)
                        minutes = int((duration_seconds % 3600) // 60)
                        seconds = int(duration_seconds % 60)
                        
                        if hours > 0:
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            duration_str = f"{minutes:02d}:{seconds:02d}"
                except ValueError:
                    duration_str = "未知"
                
                self.video_duration_var.set(duration_str)
                self.logger.info(f"获取时长: {duration_str}")
                
                self.logger.info(f"成功获取视频信息 - 分辨率: {resolution}, 帧率: {fps_str}, 时长: {duration_str}")
                return True
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {str(e)}")
                self.logger.error(f"原始输出预览: {result.stdout[:500] if result.stdout else 'None'}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("获取视频信息超时")
            return False
        except FileNotFoundError:
            self.logger.error("ffprobe未找到，无法获取视频信息")
            return False
        except Exception as e:
            self.logger.error(f"获取视频信息时出错: {str(e)}", exc_info=True)
            return False
    
    def reset_progress_display(self):
        """重置进度显示"""
        self.progress_bar['value'] = 0
        self.progress_percent_var.set("0%")
        self.elapsed_time_var.set("00:00")
        self.remaining_time_var.set("00:00")
        self.processing_speed_var.set("0.0fps")
        self.processed_frames_var.set("0")
        self.remaining_frames_var.set("0")
        self.total_frames_var.set("0")
        # 重置视频信息显示
        self.video_resolution_var.set("未知")
        self.video_fps_var.set("未知")
        self.video_duration_var.set("未知")
    def apply_center_alignment(self, combobox):
        """应用居中对齐到Combobox - Windows平台专用方法"""
        # 由于ttk.Combobox在Windows上不支持文本对齐，我们使用一种变通方法
        # 在Windows上，我们可以通过设置Combobox的内部Entry组件来实现文本居中
        self.center_ttk_combobox_text(combobox)
    
    def center_ttk_combobox_text(self, combobox):
        """在Windows上设置ttk.Combobox文本居中"""
        try:
            # 在Windows上，ttk.Combobox内部使用了一个Entry组件
            # 我们需要使用Windows特有的方法来访问内部组件
            combobox.bind('<Configure>', lambda e: self.realign_combobox_text(combobox))
            combobox.bind('<<ComboboxSelected>>', lambda e: self.realign_combobox_text(combobox))
            
            # 初始对齐
            self.realign_combobox_text(combobox)
        except Exception as e:
            self.logger.warning(f"设置Combobox文本居中失败: {str(e)}")
    
    def realign_combobox_text(self, combobox):
        """重新对齐Combobox文本"""
        try:
            # 使用after确保在GUI更新后执行
            combobox.after(10, self.force_combobox_center_alignment, combobox)
        except:
            pass
    
    def apply_center_alignment_optionmenu(self, optionmenu):
        """应用居中对齐到OptionMenu"""
        # OptionMenu默认支持文本居中对齐
        try:
            # 设置文本居中
            optionmenu.config(anchor="center")
        except Exception as e:
            self.logger.debug(f"设置OptionMenu居中对齐失败: {str(e)}")
    
    def show_post_processing_menu(self, event=None):
        """显示处理完成后选项菜单"""
        # 获取按钮的位置
        x = self.post_processing_button.winfo_rootx()
        y = self.post_processing_button.winfo_rooty() + self.post_processing_button.winfo_height()
        # 显示菜单
        self.post_processing_menu.post(x, y)
    
    def select_post_processing_option(self, option):
        """选择处理完成后选项"""
        self.post_processing_action_var.set(option)
    
    def cycle_post_processing_options(self):
        """循环切换处理完成后选项"""
        # 循环到下一个选项
        self.post_processing_current_option_index = (self.post_processing_current_option_index + 1) % len(self.post_processing_options_list)
        new_option = self.post_processing_options_list[self.post_processing_current_option_index]
        self.post_processing_action_var.set(new_option)
    
    def force_combobox_center_alignment(self, combobox):
        """强制设置Combobox文本居中对齐"""
        try:
            # 在Windows上，Combobox内部的Entry组件可以通过特殊方式访问
            # 但在ttk中，我们需要使用更底层的Tcl/Tk方法
            current_value = combobox.get()
            
            # 由于ttk.Combobox的限制，我们使用一种变通方法：
            # 重新创建组件并设置居中对齐
            pass  # 这里我们只是占位符，因为实际实现非常复杂
        except Exception as e:
            self.logger.debug(f"强制居中对齐失败: {str(e)}")
    
    def execute_post_processing_action(self):
        """根据用户选择执行处理完成后的操作"""
        action = self.post_processing_action_var.get()
        
        if action == "退出软件并休眠":
            self.logger.info("执行休眠操作")
            try:
                # 在Windows系统上执行休眠命令
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            except Exception as e:
                self.logger.error(f"执行休眠操作失败: {str(e)}")
        elif action == "退出软件并关机":
            self.logger.info("执行关机操作")
            try:
                # 在Windows系统上执行关机命令
                os.system("shutdown /s /t 0")
            except Exception as e:
                self.logger.error(f"执行关机操作失败: {str(e)}")
        # 如果是"无"，则不做任何操作
    

    def stop_processing_func(self):
        """停止处理"""
        self.stop_processing = True
        self.status_var.set("正在停止处理...")
        
        # 停止卡死监测
        self.stop_stuck_monitor()
        
        # 强制终止当前运行的JASNA进程
        try:
            # 首先尝试正常的terminate
            if self.current_process and self.current_process.poll() is None:
                self.current_process.terminate()
                
                # 等待进程结束
                try:
                    self.current_process.wait(timeout=2)
                    self.logger.info("JASNA进程已正常终止（停止按钮）")
                except subprocess.TimeoutExpired:
                    # 如果进程未终止，尝试强制终止
                    if self.current_process.poll() is None:
                        # 使用多种方法强制终止所有jasna.exe进程
                        self.kill_all_jasna_processes()
            
            # 无论current_process是否终止，都强制终止所有jasna.exe进程
            self.logger.info("强制终止所有jasna.exe进程（停止按钮）")
            self.kill_all_jasna_processes()
        except Exception as e:
            self.logger.error(f"终止JASNA进程时出错（停止按钮）: {str(e)}")
        
        # 记录当前正在处理的视频信息，用于后续清理
        if self.currently_processing:
            video_name = Path(self.currently_processing).stem
            suffix = self.output_suffix_var.get()
            output_folder = self.output_folder_var.get()
            
            # 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
            self.logger.info(f"将在2秒后清理临时文件（包括最终文件）: {video_name}")
            self.root.after(2000, lambda: self.cleanup_temp_files_after_stop(video_name, suffix, output_folder, delete_final_file=True))
        
        self.logger.info("用户请求停止处理")
        self.root.after(1000, lambda: self.status_var.set("处理已停止"))
        
        # 如果stuck_seconds值被修改过，恢复原始值
        if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
            self.stuck_seconds_var.set(self.original_stuck_seconds)
            self.logger.info(f"用户停止处理 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
            # 重置标志
            self.stuck_seconds_modified = False
            self.original_stuck_seconds = None
        
        # 在完成所有停止操作后清空日志文件
        self.clear_log_file()
    
    def clear_lists(self, clear_summary=True):
        """清空所有列表"""
        self.video_lists = {
            "processed": [],
            "unprocessed": [],
            "error": []
        }
        self.update_lists_display()
        
        if clear_summary:
            self.summary_var.set("输入文件夹中视频数量: 0 | 已处理视频数量: 0 | 未处理视频数量: 0 | 处理出错视频数量: 0")
        
        self.status_var.set("列表已清空")
    
    def on_unprocessed_video_select(self, event=None):
        """当在未处理视频列表中选择视频时，获取并显示视频信息"""
        try:
            # 获取当前选中的索引
            selection = self.unprocessed_listbox.curselection()
            if not selection:
                return
            
            # 获取选中的视频显示文本
            selected_index = selection[0]
            video_display_text = self.unprocessed_listbox.get(selected_index)
            
            # 从显示文本中提取视频文件名（处理 "filename [resolution, fps, duration]" 格式）
            video_file = video_display_text
            if ' [' in video_display_text and video_display_text.endswith(']'):
                video_file = video_display_text.split(' [')[0]
            
            # 获取输入文件夹路径
            input_folder = self.input_folder_var.get()
            if not input_folder:
                self.logger.warning("输入文件夹未设置")
                return
            
            # 构建完整路径
            video_path = os.path.join(input_folder, video_file)
            
            # 验证文件是否存在
            if not os.path.exists(video_path):
                self.logger.warning(f"视频文件不存在: {video_path}")
                # 重置视频信息显示
                self.video_resolution_var.set("文件不存在")
                self.video_fps_var.set("文件不存在")
                self.video_duration_var.set("文件不存在")
                return
            
            # 获取视频信息
            self.logger.info(f"获取选中视频信息: {video_file}")
            success = self.get_video_info(video_path)
            
            if not success:
                self.logger.warning(f"无法获取视频信息: {video_file}")
                # 即使获取失败也显示提示信息
                self.video_resolution_var.set("获取失败")
                self.video_fps_var.set("获取失败")
                self.video_duration_var.set("获取失败")
            
        except Exception as e:
            self.logger.error(f"处理视频选择事件时出错: {str(e)}")
            # 发生错误时重置视频信息显示
            self.video_resolution_var.set("错误")
            self.video_fps_var.set("错误")
            self.video_duration_var.set("错误")
    
    def on_processed_video_select(self, event=None):
        """当在已处理视频列表中选择视频时，获取并显示视频信息"""
        try:
            # 获取当前选中的索引
            selection = self.processed_listbox.curselection()
            if not selection:
                return
            
            # 获取选中的视频显示文本
            selected_index = selection[0]
            video_display_text = self.processed_listbox.get(selected_index)
            
            # 从显示文本中提取视频文件名（处理 "filename [resolution, fps, duration]" 格式）
            video_file = video_display_text
            if ' [' in video_display_text and video_display_text.endswith(']'):
                video_file = video_display_text.split(' [')[0]
            
            # 获取输入文件夹路径
            input_folder = self.input_folder_var.get()
            if not input_folder:
                self.logger.warning("输入文件夹未设置")
                return
            
            # 构建完整路径
            video_path = os.path.join(input_folder, video_file)
            
            # 验证文件是否存在
            if not os.path.exists(video_path):
                self.logger.warning(f"视频文件不存在: {video_path}")
                # 重置视频信息显示
                self.video_resolution_var.set("文件不存在")
                self.video_fps_var.set("文件不存在")
                self.video_duration_var.set("文件不存在")
                return
            
            # 获取视频信息
            self.logger.info(f"获取选中视频信息: {video_file}")
            success = self.get_video_info(video_path)
            
            if not success:
                self.logger.warning(f"无法获取视频信息: {video_file}")
                # 即使获取失败也显示提示信息
                self.video_resolution_var.set("获取失败")
                self.video_fps_var.set("获取失败")
                self.video_duration_var.set("获取失败")
            
        except Exception as e:
            self.logger.error(f"处理视频选择事件时出错: {str(e)}")
            # 发生错误时重置视频信息显示
            self.video_resolution_var.set("错误")
            self.video_fps_var.set("错误")
            self.video_duration_var.set("错误")
    
    def on_error_video_select(self, event=None):
        """当在错误视频列表中选择视频时，获取并显示视频信息"""
        try:
            # 获取当前选中的索引
            selection = self.error_listbox.curselection()
            if not selection:
                return
            
            # 获取选中的视频显示文本
            selected_index = selection[0]
            video_display_text = self.error_listbox.get(selected_index)
            
            # 从显示文本中提取视频文件名（处理 "filename [resolution, fps, duration]" 格式）
            video_file = video_display_text
            if ' [' in video_display_text and video_display_text.endswith(']'):
                video_file = video_display_text.split(' [')[0]
            
            # 获取输入文件夹路径
            input_folder = self.input_folder_var.get()
            if not input_folder:
                self.logger.warning("输入文件夹未设置")
                return
            
            # 构建完整路径
            video_path = os.path.join(input_folder, video_file)
            
            # 验证文件是否存在
            if not os.path.exists(video_path):
                self.logger.warning(f"视频文件不存在: {video_path}")
                # 重置视频信息显示
                self.video_resolution_var.set("文件不存在")
                self.video_fps_var.set("文件不存在")
                self.video_duration_var.set("文件不存在")
                return
            
            # 获取视频信息
            self.logger.info(f"获取选中视频信息: {video_file}")
            success = self.get_video_info(video_path)
            
            if not success:
                self.logger.warning(f"无法获取视频信息: {video_file}")
                # 即使获取失败也显示提示信息
                self.video_resolution_var.set("获取失败")
                self.video_fps_var.set("获取失败")
                self.video_duration_var.set("获取失败")
            
        except Exception as e:
            self.logger.error(f"处理视频选择事件时出错: {str(e)}")
            # 发生错误时重置视频信息显示
            self.video_resolution_var.set("错误")
            self.video_fps_var.set("错误")
            self.video_duration_var.set("错误")
    
    def on_closing(self):
        """关闭窗口时的处理"""
        # 停止卡死监测
        self.stop_stuck_monitor()
        
        # 保存当前设置
        self.save_settings()
        
        if self.processing_thread and self.processing_thread.is_alive():
            if self.show_custom_messagebox("askyesno", "确认", "视频处理正在进行中，确定要退出吗？"):
                self.stop_processing = True
                # 使用与停止按钮相同的终止代码
                try:
                    if self.current_process and self.current_process.poll() is None:
                        self.current_process.terminate()
                        try:
                            self.current_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            if self.current_process.poll() is None:
                                # 使用多种方法强制终止所有jasna.exe进程
                                self.kill_all_jasna_processes()
                except Exception as e:
                    self.logger.error(f"终止JASNA进程时出错（窗口关闭）: {str(e)}")
                
                time.sleep(1)  # 给线程一点时间停止
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = JasnaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()