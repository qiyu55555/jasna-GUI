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
    """工具提示类，用于显示悬停说明"""
    def __init__(self, widget, text, delay=500):
        """
        初始化Tooltip
        
        参数:
            widget: 要添加提示的组件
            text: 提示文本
            delay: 延迟显示时间(毫秒)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        # 绑定事件
        self.widget.bind('<Enter>', self.schedule)
        self.widget.bind('<Leave>', self.cancel)
        self.widget.bind('<Button-1>', self.cancel)
    
    def schedule(self, event=None):
        """安排显示提示"""
        self.cancel()
        self.id = self.widget.after(self.delay, self.showtip, event)
    
    def cancel(self, event=None):
        """取消显示提示"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
        self.hidetip()
    
    def showtip(self, event=None):
        """显示提示"""
        if self.tooltip_window:
            return
        
        # 获取鼠标位置
        x, y, cx, cy = self.widget.bbox('insert')
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        # 创建提示窗口
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # 无标题栏
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # 设置提示窗口样式
        self.tooltip_window.config(
            bg="#ffffe0",  # 浅黄色背景
            relief="solid",
            bd=1,  # 边框宽度
            padx=10,
            pady=5
        )
        
        # 添加阴影效果
        try:
            self.tooltip_window.attributes('-alpha', 0.95)  # 半透明效果
            if os.name == 'nt':  # Windows系统
                self.tooltip_window.attributes('-toolwindow', True)
                self.tooltip_window.attributes('-topmost', True)
        except:
            pass
        
        # 创建提示标签
        label = ttk.Label(
            self.tooltip_window,
            text=self.text,
            justify='left',
            background="#ffffe0",
            foreground="#333333",
            font=('Microsoft YaHei', 10),
            wraplength=300  # 文本换行宽度
        )
        label.pack(ipadx=1, ipady=1)
        
        # 确保提示窗口在屏幕范围内
        self.ensure_tooltip_visibility()
    
    def ensure_tooltip_visibility(self):
        """确保提示窗口在屏幕范围内"""
        if not self.tooltip_window:
            return
        
        # 获取屏幕尺寸
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        
        # 获取提示窗口尺寸
        tooltip_width = self.tooltip_window.winfo_reqwidth()
        tooltip_height = self.tooltip_window.winfo_reqheight()
        
        # 获取当前提示窗口位置
        tooltip_x = self.tooltip_window.winfo_x()
        tooltip_y = self.tooltip_window.winfo_y()
        
        # 调整位置，确保提示窗口在屏幕范围内
        if tooltip_x + tooltip_width > screen_width:
            tooltip_x = screen_width - tooltip_width - 10
        if tooltip_y + tooltip_height > screen_height:
            tooltip_y = screen_height - tooltip_height - 10
        if tooltip_x < 0:
            tooltip_x = 10
        if tooltip_y < 0:
            tooltip_y = 10
        
        # 更新提示窗口位置
        self.tooltip_window.wm_geometry(f"+{tooltip_x}+{tooltip_y}")
    
    def hidetip(self):
        """隐藏提示"""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            finally:
                self.tooltip_window = None


def resource_path(relative_path):
    """
    获取资源文件的绝对路径，用于处理PyInstaller打包后的资源访问
    :param relative_path: 资源文件的相对路径
    :return: 资源文件的绝对路径
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


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
        self.root.title("JASNA视频处理工具-v9.1  （ 作者：旗鱼 ）                                             jasna和lada均为免费开源软件     中文交流QQ群：1083672873")
        self.root.geometry("1170x1005")  # 窗口高度增加15像素
        
        # 设置窗口图标
        try:
            import sys
            import os
            if getattr(sys, 'frozen', False):
                # 如果是打包后的EXE运行环境
                icon_path = resource_path('jasna-v2-T-256.ico')
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
        
        # 处理错误相关变量
        self.processing_error = False  # 标记处理过程中是否出现了错误
        
        # 处理完成后操作选择
        self.post_processing_action_var = tk.StringVar(value="无")  # 默认为"无"
        
        # 二次修复相关变量
        self.secondary_fix_var = tk.StringVar(value="无")  # 二次修复选项：无、TVAI、RTX-SR
        self.ffmpeg_path_var = tk.StringVar()  # ffmpeg程序地址
        self.tvai_model_var = tk.StringVar(value="iris-2")  # TVAI模型名称
        self.tvai_scale_var = tk.StringVar(value="4")  # TVAI缩放选项
        self.tvai_threads_var = tk.StringVar(value="2")  # TVAI线程数
        self.tvai_params_var = tk.StringVar(value="preblur=0:noise=0:details=0:halo=0:blur=0:compression=0:estimate=8:blend=0.2:device=-2:vram=1:instances=1")  # TVAI附加参数
        # RTX-SR相关参数
        self.rtx_sr_scale_var = tk.StringVar(value="4X")  # RTX-SR缩放：2X、4X，默认4X
        self.rtx_sr_quality_var = tk.StringVar(value="高")  # RTX-SR质量：低、中、高、超高，默认高
        self.rtx_sr_denoise_var = tk.StringVar(value="低")  # RTX-SR降噪：无、低、中、高、超高，默认低
        self.rtx_sr_deblur_var = tk.StringVar(value="低")  # RTX-SR去模糊：无、低、中、高、超高，默认低
        self.secondary_fix_display_var = tk.StringVar()  # 二次修复显示/隐藏选项
        self.settings_mode_var = tk.StringVar(value="二次修复")  # 设置模式：二次修复、全部设置
        
        # 视频转码参数
        self.transcode_params_var = tk.StringVar(value='-hwaccel cuda -hwaccel_output_format cuda -c:v hevc_nvenc -preset p5 -tune hq -rc constqp -qp 15 -qp_cb_offset -2 -qp_cr_offset -2 -spatial_aq 1 -aq-strength 1 -c:a aac -b:a 128k')
        
        # 处理状态（破解或转码）
        self.processing_mode_var = tk.StringVar(value="破解")
        
        # VR模式
        self.vr_mode_var = tk.StringVar(value="关闭")
        
        # 配置文件路径
        self.config_file = "jasna_gui_config.json"
        
        # 初始化切片帧数历史记录
        self.slice_frames_history = []
        # 初始化检测模型历史记录
        self.detection_model_history = []
        
        # 用于跟踪stuck_seconds是否被临时修改
        self.original_stuck_seconds = None
        self.stuck_seconds_modified = False
        

        self.first_video_processed = False  # 添加标志以跟踪是否已处理第一个视频
        
        # 创建GUI组件
        self.create_widgets()
        
        # 加载上次的设置
        self.load_settings()
        
        # 根据加载的设置值动态调整UI布局
        self.update_module_visibility()
        
        # 初始化二次修复状态标签
        self.update_secondary_fix_status_label()
        
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
                    icon_path = resource_path('jasna-v2-T-256.ico')
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
                    icon_path = resource_path('jasna-v2-T-256.ico')
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
            
            # 添加3分钟后自动关闭功能
            dialog.after(180000, lambda: dialog.destroy())  # 180000毫秒 = 3分钟
            
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
        self.settings_frame.place(x=10, y=10, width=1150, height=240)
        
        # 设置标题字体
        style = ttk.Style()
        style.configure("Title.TLabelframe.Label", font=self.title_font)
        self.settings_frame.configure(style="Title.TLabelframe")
        
        # 创建自定义样式，用于Swin2SR详细设置子模块
        # 将标签文本定位到左侧横线上并水平居中
        style.configure("LeftAligned.TLabelframe", padding=(10, 20, 10, 10))
        style.configure("LeftAligned.TLabelframe.Label", 
                       font=self.title_font,
                       anchor="center",  # 水平居中
                       justify="center")
        
        # 第一行设置 - 使用place布局
        # 1. jasna程序地址
        jasna_label = ttk.Label(self.settings_frame, text="jasna-cli的地址", font=self.normal_font)
        jasna_label.place(x=10, y=0)
        Tooltip(jasna_label, "A卡不能用\n\n指定jasna-cli主程序文件的完整路径\n\n例如: D:/jasna-0.5/jasna-cli.exe\n\n本GUI程序可以不与jasna-cli.exe程序放在一起\n放在任何位置都可以正常运行\n只要jasna-cli.exe的命令没有改变\n则此程序可以适用于jasna的不同版本")
        
        self.jasna_path_var = tk.StringVar()
        self.jasna_path_entry = ttk.Entry(self.settings_frame, textvariable=self.jasna_path_var, width=30, font=self.normal_font)
        self.jasna_path_entry.place(x=140, y=0, width=300)
        
        jasna_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_jasna_path, style="TButton")
        jasna_browse_btn.place(x=450, y=0, width=60)
        
        # 2. 切片帧数
        slice_label = ttk.Label(self.settings_frame, text="切片帧数", font=self.normal_font)
        slice_label.place(x=530, y=0)
        Tooltip(slice_label, "视频一次性处理的帧数\n\n建议值: 30-90\n\n如果输入的数值为首次使用则需要编译模型\n时间在0.2-4小时\n请耐心等待\n\n如果编译失败\n则把数值调小后重新尝试运行\n\n编译过的模型会自动记录\n下次使用就不用再编译了")
        
        self.slice_frames_var1 = tk.StringVar(value="60")
        self.slice_frames_entry1 = ttk.Entry(self.settings_frame, textvariable=self.slice_frames_var1, width=4, font=self.normal_font, justify='center')
        self.slice_frames_entry1.place(x=610, y=0, width=45)
        Tooltip(self.slice_frames_entry1, "用于1080P分辨率的切片帧数\n\n所有分辨率低于4K的视频都会使用此切片帧数")
        
        self.slice_frames_var2 = tk.StringVar(value="30")
        self.slice_frames_entry2 = ttk.Entry(self.settings_frame, textvariable=self.slice_frames_var2, width=4, font=self.normal_font, justify='center')
        self.slice_frames_entry2.place(x=660, y=0, width=45)
        Tooltip(self.slice_frames_entry2, "用于4K分辨率的切片帧数\n\n所有分辨率大于或等于4K的视频都会使用此切片帧数")
        
        # 3. 输出视频后缀
        suffix_label = ttk.Label(self.settings_frame, text="输出视频后缀", font=self.normal_font)
        suffix_label.place(x=720, y=0)
        Tooltip(suffix_label, "输出视频文件名的后缀\n\n例如: -U \n\n表示输出文件名为：原文件名-U.mp4")
        
        self.output_suffix_var = tk.StringVar(value="-U")
        self.output_suffix_entry = ttk.Entry(self.settings_frame, textvariable=self.output_suffix_var, width=9, font=self.normal_font, justify='center')
        self.output_suffix_entry.place(x=835, y=0, width=80)
        
        # 4. 卡死几秒后跳过
        stuck_label = ttk.Label(self.settings_frame, text="卡死几秒后跳过", font=self.normal_font)
        stuck_label.place(x=928, y=0)
        Tooltip(stuck_label, "视频处理过程中卡死多少秒后自动跳过并处理下一个\n\n默认值: 900秒（15分钟）\n\n切片帧数为第一次使用时\n这里会自动变为15000\n模型编译完成后会自动变回之前设置的值\n不必干预，全自动处理")
        
        self.stuck_seconds_var = tk.StringVar(value="900")  # 默认900秒（15分钟）
        self.stuck_seconds_entry = ttk.Entry(self.settings_frame, textvariable=self.stuck_seconds_var, width=9, font=self.normal_font, justify='center')
        self.stuck_seconds_entry.place(x=1060, y=0, width=60)
        
        # 第二行设置
        # 5. 视频输入文件夹
        input_label = ttk.Label(self.settings_frame, text="视频输入文件夹", font=self.normal_font)
        input_label.place(x=10, y=40)
        Tooltip(input_label, "包含待处理视频文件的文件夹路径\n\n例如: D:/videos/输入文件夹\n\n输入、输出、成功、出错文件夹最好不要为上下级目录或同一目录\n否则可能会导致处理失败")
        
        self.input_folder_var = tk.StringVar()
        self.input_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.input_folder_var, width=30, font=self.normal_font)
        self.input_folder_entry.place(x=140, y=40, width=300)
        
        input_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_input_folder, style="TButton")
        input_browse_btn.place(x=450, y=40, width=60)
        
        # 6. 成功原视频存放文件夹
        success_label = ttk.Label(self.settings_frame, text="成功原视频存放文件夹", font=self.normal_font)
        success_label.place(x=530, y=40)
        Tooltip(success_label, "处理成功后的原视频文件（也就是有马赛克的视频）将被移动到此文件夹\n\n例如: D:/videos/成功视频文件夹\n\n输入、输出、成功、出错文件夹最好不要为上下级目录或同一目录\n否则可能会导致处理失败")
        
        self.success_folder_var = tk.StringVar()
        self.success_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.success_folder_var, width=30, font=self.normal_font)
        self.success_folder_entry.place(x=710, y=40, width=340)
        
        success_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_success_folder, style="TButton")
        success_browse_btn.place(x=1060, y=40, width=60)
        
        # 第三行设置
        # 7. 视频输出文件夹
        output_label = ttk.Label(self.settings_frame, text="视频输出文件夹", font=self.normal_font)
        output_label.place(x=10, y=80)
        Tooltip(output_label, "处理后的视频文件（也就是无马赛克的视频）将保存到此文件夹\n\n例如: D:/videos/输出文件夹\n\n输入、输出、成功、出错文件夹最好不要为上下级目录或同一目录\n否则可能会导致处理失败")
        
        self.output_folder_var = tk.StringVar()
        self.output_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.output_folder_var, width=30, font=self.normal_font)
        self.output_folder_entry.place(x=140, y=80, width=300)
        
        output_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_output_folder, style="TButton")
        output_browse_btn.place(x=450, y=80, width=60)
        
        # 8. 出错原视频存放文件夹
        error_label = ttk.Label(self.settings_frame, text="出错原视频存放文件夹", font=self.normal_font)
        error_label.place(x=530, y=80)
        Tooltip(error_label, "处理失败的原视频文件（也就是有马赛克的视频）将被移动到此文件夹\n\n例如: D:/videos/出错视频文件夹\n\n输入、输出、成功、出错文件夹最好不要为上下级目录或同一目录\n否则可能会导致处理失败")
        
        self.error_folder_var = tk.StringVar()
        self.error_folder_entry = ttk.Entry(self.settings_frame, textvariable=self.error_folder_var, width=30, font=self.normal_font)
        self.error_folder_entry.place(x=710, y=80, width=340)
        
        error_browse_btn = ttk.Button(self.settings_frame, text="浏览", command=self.browse_error_folder, style="TButton")
        error_browse_btn.place(x=1060, y=80, width=60)
        
        # 第四行设置
        # 9. 自定义编码参数
        encode_label = ttk.Label(self.settings_frame, text="自定义编码参数", font=self.normal_font)
        encode_label.place(x=10, y=120)
        Tooltip(encode_label, "自定义视频编码参数\n\n此参数决定最后成品视频的质量和文件体积\n\n格式: 参数1=值1,参数2=值2,...\n\n其中cq的值主要影响视频质量\ncq值越小\n视频质量越高\n文件体积也越大\n默认值: 31\n\n默认参数适用于大多数情况")
        
        self.encode_params_var = tk.StringVar(value='preset=p7,tune=hq,profile=main10,tier=high,rc=vbr,cq=31,rc-lookahead=32,temporal-aq=1,spatial_aq=0,bf=3,b_ref_mode=middle,g=300')
        self.encode_params_entry = ttk.Entry(self.settings_frame, textvariable=self.encode_params_var, width=53, font=self.normal_font)
        self.encode_params_entry.place(x=140, y=120, width=980)
        
        # 14. 卡死后转码参数
        transcode_label = ttk.Label(self.settings_frame, text="卡死后转码参数", font=self.normal_font)
        transcode_label.place(x=10, y=160)
        Tooltip(transcode_label, "视频转码参数，用于处理出错视频的转码参数\n\n此参数决定转码后的视频质量和文件体积\n不影响最终的成品视频体积\n只决定转码后视频与原视频的质量接近程度\n所以qp的值越低越好（值越低代表质量越高）\n建议14-16\n\n默认参数: -preset p5 -tune hq -rc constqp -qp 15 -c:a aac -b:a 256k\n\n默认使用英伟达自带的硬件编码器和解码器\n\n-preset p5：使用p5预设\n-tune hq：使用hq调优\n-rc constqp：使用常量qp模式\n-qp 15：设置qp值为15\n-c:a aac：使用aac编码器\n-b:a 256k：设置音频码率为256k\n\n音频会首先使用复制模式\n复制失败后才会使用你设置的音频编码参数")
        
        self.transcode_params_var = tk.StringVar(value='-preset p5 -tune hq -rc constqp -qp 15 -c:a aac -b:a 256k')
        self.transcode_params_entry = ttk.Entry(self.settings_frame, textvariable=self.transcode_params_var, width=53, font=self.normal_font)
        self.transcode_params_entry.place(x=140, y=160, width=440)
        
        # 检测模型选择
        detection_model_label = ttk.Label(self.settings_frame, text="检测模型", font=self.normal_font)
        detection_model_label.place(x=600, y=160, width=80, height=30)
        Tooltip(detection_model_label, '''选择使用的检测模型\n\n默认值: rfdetr-v6\n\n最好先使用CMD命令行把要用的检测模型先编译完成\n\nrfdetr-v6: 最新版本的RFDetr模型\nrfdetr-v6-large: RFDetr模型的large大模型版本\nlada-yolo-v4: 最新版本的Lada-YOLO模型\nrfdetr-v5: RFDetr模型v5版本\nrfdetr-vr-v1: RFDetr的VR专用模型''')

        # 使用自定义按钮作为选项选择器，避免下拉箭头并提高对比度
        detection_model_options = ["rfdetr-v6", "rfdetr-v6-large", "lada-yolo-v4", "rfdetr-v5", "rfdetr-vr-v1"]
        self.detection_model_current_option_index = 0  # 当前选项索引，默认rfdetr-v6
        
        # 确保detection_model_var被正确初始化
        if not hasattr(self, 'detection_model_var') or self.detection_model_var is None:
            self.detection_model_var = tk.StringVar()
        
        # 创建一个带有内凹效果的自定义按钮
        self.detection_model_button = tk.Button(
            self.settings_frame, 
            textvariable=self.detection_model_var,
            command=self.show_detection_model_menu,
            font=self.normal_font,
            bg="white",  # 白色背景
            fg="black",
            relief="sunken",  # 内凹效果
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.detection_model_button.place(x=680, y=160, width=160, height=30)
        
        # 初始化显示，默认使用rfdetr-v6
        self.detection_model_var.set(detection_model_options[0])
        self.detection_model_options_list = detection_model_options
        
        # 创建右键菜单
        self.detection_model_menu = tk.Menu(self.root, tearoff=0)
        for option in detection_model_options:
            # 使用嵌套函数解决lambda捕获变量的问题
            def make_command(opt):
                return lambda: self.select_detection_model_option(opt)
            self.detection_model_menu.add_command(label=option, command=make_command(option))
        
        # VR模式选择
        vr_mode_label = ttk.Label(self.settings_frame, text="VR", font=self.normal_font)
        vr_mode_label.place(x=860, y=160, width=30, height=30)
        Tooltip(vr_mode_label, "选择VR处理模式\n\n关闭：不添加任何VR参数\n自动：添加 --vr-mode auto 参数\nSBS：添加 --vr-mode sbs 参数\n鱼眼：添加 --vr-mode sbs-fisheye 参数\n\n默认值为\"关闭\"")
        
        vr_mode_options = ["关闭", "自动", "SBS", "鱼眼"]
        self.vr_mode_current_option_index = 0  # 当前选项索引，默认关闭
        
        self.vr_mode_button = tk.Button(
            self.settings_frame, 
            textvariable=self.vr_mode_var,
            command=self.show_vr_mode_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.vr_mode_button.place(x=890, y=160, width=80, height=30)
        
        self.vr_mode_var.set(vr_mode_options[0])
        self.vr_mode_options_list = vr_mode_options
        
        # 创建VR模式右键菜单
        self.vr_mode_menu = tk.Menu(self.root, tearoff=0)
        for option in vr_mode_options:
            def make_vr_command(opt):
                return lambda: self.select_vr_mode_option(opt)
            self.vr_mode_menu.add_command(label=option, command=make_vr_command(option))
        
        # 检测阈值
        detection_threshold_label = ttk.Label(self.settings_frame, text="检测阈值", font=self.normal_font)
        detection_threshold_label.place(x=990, y=160, width=80, height=30)
        Tooltip(detection_threshold_label, "马赛克检测的置信度阈值\n\n取值范围：0.00-1.00\n默认值：0.20\n\n数值越小，检测越严格，可能漏检更少的马赛克\n数值越大，检测越宽松，可能减少误检\n请谨慎修改此值！")
        
        self.detection_threshold_var = tk.StringVar(value="0.20")
        self.detection_threshold_entry = ttk.Entry(self.settings_frame, textvariable=self.detection_threshold_var, width=6, font=self.normal_font, justify='center')
        self.detection_threshold_entry.place(x=1070, y=160, width=50, height=30)
        # 绑定修改事件，弹窗提示用户（使用FocusOut事件，只在输入框失去焦点且值改变时触发）
        self._detection_threshold_last_value = "0.20"
        self.detection_threshold_entry.bind('<FocusOut>', self.on_detection_threshold_focus_out)
        self.detection_threshold_entry.bind('<Return>', self.on_detection_threshold_focus_out)
        
        # 二次修复模块 - 插入到自定义设置模块下方
        self.secondary_fix_frame = ttk.LabelFrame(self.root, text="二次修复", padding="10")
        self.secondary_fix_frame.place(x=10, y=255, width=1150, height=150)
        self.secondary_fix_frame.configure(style="Title.TLabelframe")
        
        # 二次修复主模块组件
        secondary_fix_label = ttk.Label(self.secondary_fix_frame, text="使用软件", font=self.normal_font)
        secondary_fix_label.place(x=10, y=10)
        Tooltip(secondary_fix_label, "选择二次修复使用的软件\n\n无：不使用任何二次修复软件\nTVAI：使用Topaz Video AI进行二次修复\nRTX-SR：使用NVIDIA RTX Super Resolution进行超分辨率修复\n\n默认值为\"无\"\n\n如果要使用的话作者K佬是推荐使用RTX-SR的")
        
        # 二次修复选项 - 使用自定义按钮实现，避免下拉箭头
        secondary_fix_options = ["无", "RTX-SR"]
        self.secondary_fix_current_option_index = 0  # 当前选项索引
        
        # 创建一个带有内凹效果的自定义按钮
        self.secondary_fix_button = tk.Button(
            self.secondary_fix_frame, 
            textvariable=self.secondary_fix_var,
            command=self.show_secondary_fix_menu,
            font=self.normal_font,
            bg="white",  # 白色背景
            fg="black",
            relief="sunken",  # 内凹效果
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.secondary_fix_button.place(x=100, y=10, width=95, height=30)
        
        # 初始化显示
        self.secondary_fix_var.set(secondary_fix_options[0])
        self.secondary_fix_options_list = secondary_fix_options
        
        # 创建右键菜单
        self.secondary_fix_menu = tk.Menu(self.root, tearoff=0)
        for option in secondary_fix_options:
            # 使用嵌套函数解决lambda捕获变量的问题
            def make_command(opt):
                return lambda: self.select_secondary_fix_option(opt)
            self.secondary_fix_menu.add_command(label=option, command=make_command(option))
        
        # RTX-SR详细设置子模块
        self.rtx_sr_frame = ttk.LabelFrame(self.secondary_fix_frame, text="RTX-SR详细设置", padding=(10, 20, 10, 10))
        self.rtx_sr_frame.place(x=350, y=0, width=435, height=100)
        self.rtx_sr_frame.configure(style="LeftAligned.TLabelframe")

        # RTX-SR缩放
        rtx_sr_scale_label = ttk.Label(self.rtx_sr_frame, text="缩放", font=self.normal_font)
        rtx_sr_scale_label.place(x=0, y=0, width=40)
        Tooltip(rtx_sr_scale_label, "RTX-SR处理时的缩放设置\n\n2X：放大2倍\n4X：放大4倍\n\n默认值为\"4X\"")

        # RTX-SR缩放下拉选项
        self.rtx_sr_scale_options = ["2X", "4X"]
        self.rtx_sr_scale_current_index = 1  # 默认选中"4X"
        self.rtx_sr_scale_button = tk.Button(
            self.rtx_sr_frame,
            textvariable=self.rtx_sr_scale_var,
            command=self.show_rtx_sr_scale_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.rtx_sr_scale_button.place(x=40, y=0, width=50, height=30)
        self.rtx_sr_scale_var.set(self.rtx_sr_scale_options[0])  # 默认"2X"

        # 创建缩放下拉菜单
        self.rtx_sr_scale_menu = tk.Menu(self.root, tearoff=0)
        for option in self.rtx_sr_scale_options:
            def make_command(opt):
                return lambda: self.select_rtx_sr_scale_option(opt)
            self.rtx_sr_scale_menu.add_command(label=option, command=make_command(option))

        # RTX-SR质量（位置向右移动100像素）
        rtx_sr_quality_label = ttk.Label(self.rtx_sr_frame, text="质量", font=self.normal_font)
        rtx_sr_quality_label.place(x=100, y=0)
        Tooltip(rtx_sr_quality_label, "RTX-SR处理时的质量设置\n\n低：low\n中：medium\n高：high\n超高：ultra\n\n默认值为\"高\"")

        # RTX-SR质量下拉选项
        self.rtx_sr_quality_options = ["低", "中", "高", "超高"]
        self.rtx_sr_quality_current_index = 2  # 默认选中"高"
        self.rtx_sr_quality_button = tk.Button(
            self.rtx_sr_frame,
            textvariable=self.rtx_sr_quality_var,
            command=self.show_rtx_sr_quality_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.rtx_sr_quality_button.place(x=140, y=0, width=50, height=30)
        self.rtx_sr_quality_var.set(self.rtx_sr_quality_options[2])  # 默认"高"

        # 创建质量下拉菜单
        self.rtx_sr_quality_menu = tk.Menu(self.root, tearoff=0)
        for option in self.rtx_sr_quality_options:
            def make_command(opt):
                return lambda: self.select_rtx_sr_quality_option(opt)
            self.rtx_sr_quality_menu.add_command(label=option, command=make_command(option))

        # RTX-SR降噪（位置向右移动100像素）
        rtx_sr_denoise_label = ttk.Label(self.rtx_sr_frame, text="降噪", font=self.normal_font)
        rtx_sr_denoise_label.place(x=200, y=0)
        Tooltip(rtx_sr_denoise_label, "RTX-SR处理时的降噪设置\n\n无：none\n低：low\n中：medium\n高：high\n超高：ultra\n\n默认值为\"低\"")

        # RTX-SR降噪下拉选项
        self.rtx_sr_denoise_options = ["无", "低", "中", "高", "超高"]
        self.rtx_sr_denoise_current_index = 1  # 默认选中"低"
        self.rtx_sr_denoise_button = tk.Button(
            self.rtx_sr_frame,
            textvariable=self.rtx_sr_denoise_var,
            command=self.show_rtx_sr_denoise_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.rtx_sr_denoise_button.place(x=240, y=0, width=50, height=30)
        self.rtx_sr_denoise_var.set(self.rtx_sr_denoise_options[1])  # 默认"低"

        # 创建降噪下拉菜单
        self.rtx_sr_denoise_menu = tk.Menu(self.root, tearoff=0)
        for option in self.rtx_sr_denoise_options:
            def make_command(opt):
                return lambda: self.select_rtx_sr_denoise_option(opt)
            self.rtx_sr_denoise_menu.add_command(label=option, command=make_command(option))

        # RTX-SR去模糊（位置向右移动90像素）
        rtx_sr_deblur_label = ttk.Label(self.rtx_sr_frame, text="去模糊", font=self.normal_font)
        rtx_sr_deblur_label.place(x=300, y=0)
        Tooltip(rtx_sr_deblur_label, "RTX-SR处理时的去模糊设置\n\n无：none\n低：low\n中：medium\n高：high\n超高：ultra\n\n默认值为\"低\"")

        # RTX-SR去模糊下拉选项
        self.rtx_sr_deblur_options = ["无", "低", "中", "高", "超高"]
        self.rtx_sr_deblur_current_index = 1  # 默认选中"低"
        self.rtx_sr_deblur_button = tk.Button(
            self.rtx_sr_frame,
            textvariable=self.rtx_sr_deblur_var,
            command=self.show_rtx_sr_deblur_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.rtx_sr_deblur_button.place(x=360, y=0, width=50, height=30)
        self.rtx_sr_deblur_var.set(self.rtx_sr_deblur_options[1])  # 默认"低"

        # 创建去模糊下拉菜单
        self.rtx_sr_deblur_menu = tk.Menu(self.root, tearoff=0)
        for option in self.rtx_sr_deblur_options:
            def make_command(opt):
                return lambda: self.select_rtx_sr_deblur_option(opt)
            self.rtx_sr_deblur_menu.add_command(label=option, command=make_command(option))
        
        # 控制按钮区域 - 使用place布局
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.place(x=10, y=440, width=1150, height=60)
        
        # 设置按钮样式
        style.configure("TButton", font=self.normal_font)
        
        # 第一个下拉选项：显示/隐藏
        secondary_fix_display_options = ["显示", "隐藏"]
        self.secondary_fix_display_current_option_index = 1  # 当前选项索引，默认值为"隐藏"
        
        # 创建第一个下拉按钮
        self.secondary_fix_display_button = tk.Button(
            self.button_frame, 
            textvariable=self.secondary_fix_display_var,
            command=self.show_secondary_fix_display_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.secondary_fix_display_button.place(x=10, y=12, width=70, height=30)
        Tooltip(self.secondary_fix_display_button, "选择显示或隐藏\n\n显示：显示对应的设置模块\n隐藏：隐藏对应的设置模块\n\n默认值为\"隐藏\"。")
        
        # 初始化显示
        self.secondary_fix_display_var.set(secondary_fix_display_options[1])
        self.secondary_fix_display_options_list = secondary_fix_display_options
        
        # 创建第一个下拉菜单
        self.secondary_fix_display_menu = tk.Menu(self.root, tearoff=0)
        for option in secondary_fix_display_options:
            def make_command(opt):
                return lambda: self.select_secondary_fix_display_option(opt)
            self.secondary_fix_display_menu.add_command(label=option, command=make_command(option))
        
        # 第二个下拉选项：二次修复/全部设置
        settings_mode_options = ["二次修复", "全部设置"]
        self.settings_mode_current_option_index = 0  # 当前选项索引，默认值为"二次修复"
        
        # 创建第二个下拉按钮
        self.settings_mode_button = tk.Button(
            self.button_frame, 
            textvariable=self.settings_mode_var,
            command=self.show_settings_mode_menu,
            font=self.normal_font,
            bg="white",
            fg="black",
            relief="sunken",
            bd=2,
            anchor="center",
            highlightthickness=0
        )
        self.settings_mode_button.place(x=90, y=12, width=90, height=30)
        Tooltip(self.settings_mode_button, "选择设置模式\n\n二次修复：控制二次修复模块的显示/隐藏\n全部设置：控制自定义设置和二次修复模块的显示/隐藏\n\n默认值为\"二次修复\"。")
        
        # 二次修复状态标签（当二次修复隐藏时显示当前使用的软件）
        self.secondary_fix_status_var = tk.StringVar(value="")
        self.secondary_fix_status_label = ttk.Label(
            self.button_frame,
            textvariable=self.secondary_fix_status_var,
            font=("Microsoft YaHei", 9)  # 比normal_font小一点的字号
        )
        self.secondary_fix_status_label.place(x=185, y=15, width=80, height=25)
        
        # 初始化显示
        self.settings_mode_var.set(settings_mode_options[0])
        self.settings_mode_options_list = settings_mode_options
        
        # 创建第二个下拉菜单
        self.settings_mode_menu = tk.Menu(self.root, tearoff=0)
        for option in settings_mode_options:
            def make_command(opt):
                return lambda: self.select_settings_mode_option(opt)
            self.settings_mode_menu.add_command(label=option, command=make_command(option))
        
        scan_btn = ttk.Button(self.button_frame, text="扫描视频", command=self.scan_videos, style="TButton")
        scan_btn.place(x=275, y=10, width=100, height=35)
        Tooltip(scan_btn, "扫描输入文件夹中的视频文件\n将视频添加到待处理列表并显示分辨率和时长\n对比输出文件夹中的视频\n如果为已处理过\n则把视频移动到成功视频存放文件夹")
        
        start_btn = ttk.Button(self.button_frame, text="开始处理", command=self.start_processing, style="TButton")
        start_btn.place(x=405, y=10, width=100, height=35)
        Tooltip(start_btn, "开始处理视频列表中的所有视频\n按顺序处理每个视频文件\n如果视频处理失败\n则根据设置将视频移动到出错视频存放文件夹\n并根据转码参数尝试转码+重新处理视频")
        
        stop_btn = ttk.Button(self.button_frame, text="停止处理", command=self.stop_processing_func, style="TButton")
        stop_btn.place(x=535, y=10, width=100, height=35)
        Tooltip(stop_btn, "停止当前正在处理的视频\n并停止处理列表中的后续视频")
        
        realtime_btn = ttk.Button(self.button_frame, text="实时播放", command=self.start_realtime_playback, style="TButton")
        realtime_btn.place(x=665, y=10, width=100, height=35)
        Tooltip(realtime_btn, "启动jasna-cli实时播放模式\n使用当前设置的参数运行实时视频处理")
        
        save_btn = ttk.Button(self.button_frame, text="保存设置", command=self.save_settings, style="TButton")
        save_btn.place(x=795, y=10, width=100, height=35)
        Tooltip(save_btn, "保存当前所有设置到配置文件\n包括路径、参数等设置")
        

        
        # 处理完成后操作选择
        post_processing_label = ttk.Label(self.button_frame, text="处理完成后", font=self.normal_font)
        post_processing_label.place(x=975, y=12, width=100, height=30)
        Tooltip(post_processing_label, "选择视频处理全部完成后执行的操作\n无: 不执行任何操作\n退出并休眠: 关闭软件并使计算机休眠\n退出并关机: 关闭软件并关闭计算机")
        
        # 使用自定义按钮作为选项选择器，避免下拉箭头并提高对比度
        post_processing_options = ["无", "休眠", "关机"]
        self.post_processing_current_option_index = 0  # 当前选项索引
        
        # 确保post_processing_action_var被正确初始化
        if not hasattr(self, 'post_processing_action_var') or self.post_processing_action_var is None:
            self.post_processing_action_var = tk.StringVar()
        
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
        self.post_processing_button.place(x=1070, y=12, width=70, height=30)
        
        # 初始化显示，确保每次启动时均初始化为默认的"无"选项
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
        self.progress_frame.place(x=10, y=490, width=1150, height=165)
        self.progress_frame.configure(style="Title.TLabelframe")
        
        # 左半部分：当前处理视频和进度条
        left_frame = ttk.Frame(self.progress_frame)
        left_frame.place(x=10, y=0, width=600, height=110)
        
        # 当前处理视频
        current_label = ttk.Label(left_frame, text="当前处理视频：", font=self.progress_font)
        current_label.place(x=0, y=5)
        
        self.current_video_var = tk.StringVar(value="无")
        self.current_video_label = ttk.Label(left_frame, textvariable=self.current_video_var, foreground="blue", font=self.progress_font, wraplength=400)
        self.current_video_label.place(x=150, y=5, width=280, height=30)
        
        # 处理状态指示器（破解或转码）
        self.processing_mode_var = tk.StringVar(value="破解")
        self.processing_mode_label = tk.Label(left_frame, textvariable=self.processing_mode_var, bg="#4CAF50", fg="white", 
                                             font=self.progress_font, relief="raised", bd=2, anchor="center")
        # 绑定变量追踪，当处理模式变化时更新背景色
        self.processing_mode_var.trace_add("write", self._on_processing_mode_change)
        # 初始状态下隐藏状态指示器
        self.processing_mode_label.place(x=450, y=5, width=50, height=30)
        # 默认隐藏
        self.processing_mode_label.place_forget()
        
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
        duration_label.place(x=385, y=77)
        duration_value_label = ttk.Label(left_frame, textvariable=self.video_duration_var, font=self.normal_font)
        duration_value_label.place(x=427, y=78)
        
        # 右半部分：处理详细信息
        right_frame = ttk.LabelFrame(self.progress_frame, text="处理详细信息", padding="10")
        right_frame.place(x=560, y=0, width=560, height=110)
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
        self.lists_frame.place(x=10, y=675, width=1150, height=280)
        
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
        self.summary_frame.place(x=10, y=945, width=1150, height=60)
        self.summary_frame.configure(style="Title.TLabelframe")
        
        self.summary_var = tk.StringVar(value="输入文件夹中视频数量: 0 | 已处理视频数量: 0 | 未处理视频数量: 0 | 处理出错视频数量: 0")
        self.summary_label = ttk.Label(self.summary_frame, textvariable=self.summary_var, font=self.normal_font)
        self.summary_label.place(x=575, y=0, anchor='center')
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, font=self.normal_font, anchor='center')
        status_bar.place(x=10, y=1015, width=1150, height=30)
    
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
    
    def browse_ffmpeg_path(self):
        """浏览选择ffmpeg程序"""
        file_path = filedialog.askopenfilename(
            title="选择ffmpeg主程序",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            self.ffmpeg_path_var.set(file_path)
    
    def on_secondary_fix_change(self, event):
        """处理二次修复下拉菜单的选择事件"""
        selected_option = self.secondary_fix_var.get()
        # 取消子模块隐藏功能，所有子模块始终显示
        # 不再需要根据选择显示/隐藏子模块
    
    def show_secondary_fix_menu(self):
        """显示二次修复选项菜单"""
        # 在按钮位置显示菜单
        try:
            self.secondary_fix_menu.tk_popup(
                self.secondary_fix_button.winfo_rootx(),
                self.secondary_fix_button.winfo_rooty() + self.secondary_fix_button.winfo_height()
            )
        finally:
            # 确保菜单被正确销毁
            self.secondary_fix_menu.grab_release()
    
    def select_secondary_fix_option(self, option):
        """选择二次修复选项"""
        self.secondary_fix_var.set(option)
        # 触发选择事件
        self.on_secondary_fix_change(None)
        # 更新状态标签（如果二次修复处于隐藏状态）
        self.update_secondary_fix_status_label()

    def translate_rtx_option_to_english(self, chinese_option):
        """将RTX-SR中文选项转换为英文"""
        translation_map = {
            "无": "none",
            "低": "low",
            "中": "medium",
            "高": "high",
            "超高": "ultra"
        }
        return translation_map.get(chinese_option, "medium")

    def translate_rtx_option_to_chinese(self, english_option):
        """将RTX-SR英文选项转换为中文"""
        translation_map = {
            "none": "无",
            "low": "低",
            "medium": "中",
            "high": "高",
            "ultra": "超高"
        }
        return translation_map.get(english_option, "中")

    def show_rtx_sr_quality_menu(self):
        """显示RTX-SR质量选项菜单"""
        try:
            self.rtx_sr_quality_menu.tk_popup(
                self.rtx_sr_quality_button.winfo_rootx(),
                self.rtx_sr_quality_button.winfo_rooty() + self.rtx_sr_quality_button.winfo_height()
            )
        finally:
            self.rtx_sr_quality_menu.grab_release()

    def select_rtx_sr_quality_option(self, option):
        """选择RTX-SR质量选项"""
        self.rtx_sr_quality_var.set(option)

    def show_rtx_sr_denoise_menu(self):
        """显示RTX-SR降噪选项菜单"""
        try:
            self.rtx_sr_denoise_menu.tk_popup(
                self.rtx_sr_denoise_button.winfo_rootx(),
                self.rtx_sr_denoise_button.winfo_rooty() + self.rtx_sr_denoise_button.winfo_height()
            )
        finally:
            self.rtx_sr_denoise_menu.grab_release()

    def select_rtx_sr_denoise_option(self, option):
        """选择RTX-SR降噪选项"""
        self.rtx_sr_denoise_var.set(option)

    def show_rtx_sr_deblur_menu(self):
        """显示RTX-SR去模糊选项菜单"""
        try:
            self.rtx_sr_deblur_menu.tk_popup(
                self.rtx_sr_deblur_button.winfo_rootx(),
                self.rtx_sr_deblur_button.winfo_rooty() + self.rtx_sr_deblur_button.winfo_height()
            )
        finally:
            self.rtx_sr_deblur_menu.grab_release()

    def select_rtx_sr_deblur_option(self, option):
        """选择RTX-SR去模糊选项"""
        self.rtx_sr_deblur_var.set(option)

    def show_rtx_sr_scale_menu(self):
        """显示RTX-SR缩放选项菜单"""
        try:
            self.rtx_sr_scale_menu.tk_popup(
                self.rtx_sr_scale_button.winfo_rootx(),
                self.rtx_sr_scale_button.winfo_rooty() + self.rtx_sr_scale_button.winfo_height()
            )
        finally:
            self.rtx_sr_scale_menu.grab_release()

    def select_rtx_sr_scale_option(self, option):
        """选择RTX-SR缩放选项"""
        self.rtx_sr_scale_var.set(option)

    def show_tvai_model_menu(self):
        """显示TVAI模型选项菜单"""
        # 在按钮位置显示菜单
        try:
            self.tvai_model_menu.tk_popup(
                self.tvai_model_button.winfo_rootx(),
                self.tvai_model_button.winfo_rooty() + self.tvai_model_button.winfo_height()
            )
        finally:
            # 确保菜单被正确销毁
            self.tvai_model_menu.grab_release()
    
    def select_tvai_model_option(self, option):
        """选择TVAI模型选项"""
        self.tvai_model_var.set(option)
    
    def show_tvai_scale_menu(self):
        """显示TVAI缩放选项菜单"""
        # 在按钮位置显示菜单
        try:
            self.tvai_scale_menu.tk_popup(
                self.tvai_scale_button.winfo_rootx(),
                self.tvai_scale_button.winfo_rooty() + self.tvai_scale_button.winfo_height()
            )
        finally:
            # 确保菜单被正确销毁
            self.tvai_scale_menu.grab_release()
    
    def select_tvai_scale_option(self, option):
        """选择TVAI缩放选项"""
        self.tvai_scale_var.set(option)
    
    def save_settings(self):
        """保存当前设置到文件"""
        settings = {
            "jasna_path": self.jasna_path_var.get(),
            "input_folder": self.input_folder_var.get(),
            "output_folder": self.output_folder_var.get(),
            "slice_frames_1": self.slice_frames_var1.get(),
            "slice_frames_2": self.slice_frames_var2.get(),
            "encode_params": self.encode_params_var.get(),
            "transcode_params": self.transcode_params_var.get(),  # 新增转码参数
            "output_suffix": self.output_suffix_var.get(),
            "stuck_seconds": self.stuck_seconds_var.get(),  # 改为秒
            "error_folder": self.error_folder_var.get(),
            "success_folder": self.success_folder_var.get(),  # 新增
            "slice_frames_history": getattr(self, 'slice_frames_history', []),  # 添加切片帧数历史记录
            "detection_model_history": getattr(self, 'detection_model_history', []),  # 添加检测模型历史记录
            # 检测模型设置
            "detection_model": self.detection_model_var.get(),  # 新增检测模型
            "detection_threshold": self.detection_threshold_var.get(),  # 检测阈值
            # VR模式设置
            "vr_mode": self.vr_mode_var.get(),
            # 二次修复相关设置
            "secondary_fix": self.secondary_fix_var.get(),
            "ffmpeg_path": self.ffmpeg_path_var.get(),
            "tvai_model": self.tvai_model_var.get(),
            "tvai_scale": self.tvai_scale_var.get(),
            "tvai_threads": self.tvai_threads_var.get(),
            "tvai_params": self.tvai_params_var.get(),
            # RTX-SR相关设置（保存为英文值）
            "rtx_sr_scale": self.rtx_sr_scale_var.get().replace("X", ""),  # 2X->2, 4X->4
            "rtx_sr_quality": self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get()),
            "rtx_sr_denoise": self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get()),
            "rtx_sr_deblur": self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get()),
            "secondary_fix_display": self.secondary_fix_display_var.get(),
            "settings_mode": self.settings_mode_var.get()
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
                self.slice_frames_var1.set(settings.get("slice_frames_1", "30"))
                self.slice_frames_var2.set(settings.get("slice_frames_2", "30"))
                self.encode_params_var.set(settings.get("encode_params", "preset=p7,tune=hq,profile=main10,tier=high,rc=vbr,cq=31,rc-lookahead=32,temporal-aq=1,spatial_aq=0,bf=3,b_ref_mode=middle,g=300"))
                self.transcode_params_var.set(settings.get("transcode_params", "-hwaccel cuda -hwaccel_output_format cuda -c:v hevc_nvenc -preset p5 -tune hq -rc constqp -qp 15 -qp_cb_offset -2 -qp_cr_offset -2 -spatial_aq 1 -aq-strength 1 -c:a aac -b:a 128k"))  # 新增转码参数
                self.output_suffix_var.set(settings.get("output_suffix", "-U"))
                self.stuck_seconds_var.set(settings.get("stuck_seconds", "300"))  # 改为秒，默认300秒（5分钟）
                self.error_folder_var.set(settings.get("error_folder", ""))
                self.success_folder_var.set(settings.get("success_folder", ""))  # 新增
                
                # 加载切片帧数历史记录
                self.slice_frames_history = settings.get("slice_frames_history", [])
                # 加载检测模型历史记录
                self.detection_model_history = settings.get("detection_model_history", [])
                
                # 加载检测模型设置
                self.detection_model_var.set(settings.get("detection_model", "rfdetr-v6"))  # 新增检测模型，默认rfdetr-v6
                self.detection_threshold_var.set(settings.get("detection_threshold", "0.20"))  # 检测阈值，默认0.20
                # 更新检测阈值的上次值，避免加载配置后触发弹窗
                self._detection_threshold_last_value = self.detection_threshold_var.get()
                # 加载VR模式设置
                self.vr_mode_var.set(settings.get("vr_mode", "关闭"))
                
                # 加载二次修复相关设置
                self.secondary_fix_var.set(settings.get("secondary_fix", "无"))
                self.ffmpeg_path_var.set(settings.get("ffmpeg_path", ""))
                self.tvai_model_var.set(settings.get("tvai_model", "iris-2"))
                self.tvai_scale_var.set(settings.get("tvai_scale", "4"))
                self.tvai_threads_var.set(settings.get("tvai_threads", "2"))
                self.tvai_params_var.set(settings.get("tvai_params", "preblur=0:noise=0:details=0:halo=0:blur=0:compression=0:estimate=8:blend=0.2:device=-2:vram=1:instances=1"))
                # 加载RTX-SR相关设置
                rtx_scale_value = settings.get("rtx_sr_scale", "2")  # 默认2
                self.rtx_sr_scale_var.set(f"{rtx_scale_value}X")  # 2->2X, 4->4X
                rtx_quality_english = settings.get("rtx_sr_quality", "high")
                rtx_denoise_english = settings.get("rtx_sr_denoise", "medium")
                rtx_deblur_english = settings.get("rtx_sr_deblur", "none")
                self.rtx_sr_quality_var.set(self.translate_rtx_option_to_chinese(rtx_quality_english))
                self.rtx_sr_denoise_var.set(self.translate_rtx_option_to_chinese(rtx_denoise_english))
                self.rtx_sr_deblur_var.set(self.translate_rtx_option_to_chinese(rtx_deblur_english))
                # 加载二次修复显示/隐藏设置
                self.secondary_fix_display_var.set(settings.get("secondary_fix_display", "隐藏"))
                # 加载设置模式
                self.settings_mode_var.set(settings.get("settings_mode", "二次修复"))
                
                self.status_var.set("设置已加载")
                self.logger.info("设置已从配置文件加载")
        except Exception as e:
            self.logger.error(f"加载设置失败: {str(e)}")
    


    def get_video_basic_info(self, video_path):
        """获取视频基本信息（分辨率、帧率、时长）- 简化版，只返回信息"""
        try:
            from pymediainfo import MediaInfo
            import os
            from pathlib import Path
            
            # 检查视频文件是否存在
            video_path_obj = Path(video_path)
            if not video_path_obj.exists():
                self.logger.error(f"视频文件不存在: {video_path}")
                return "未知", "未知", "未知"
            
            # 使用pymediainfo获取视频信息
            media_info = MediaInfo.parse(str(video_path_obj))
            
            # 查找视频轨道
            width, height = 0, 0
            fps = 0
            duration = 0
            
            for track in media_info.tracks:
                if track.track_type == 'Video':
                    # 获取分辨率
                    if hasattr(track, 'width') and track.width:
                        width = int(track.width)
                    if hasattr(track, 'height') and track.height:
                        height = int(track.height)
                    
                    # 获取帧率
                    if hasattr(track, 'avg_frame_rate') and track.avg_frame_rate:
                        try:
                            # avg_frame_rate 可能是分数形式如 "25000/1000"
                            if '/' in str(track.avg_frame_rate):
                                num, den = map(int, str(track.avg_frame_rate).split('/'))
                                if den != 0:
                                    fps = round(num / den, 2)
                                else:
                                    fps = 0
                            else:
                                fps = float(track.avg_frame_rate)
                        except (ValueError, TypeError):
                            fps = 0
                    elif hasattr(track, 'frame_rate') and track.frame_rate:
                        try:
                            fps = float(track.frame_rate)
                        except (ValueError, TypeError):
                            fps = 0
                    
                    # 获取时长
                    if hasattr(track, 'duration') and track.duration:
                        try:
                            duration = float(track.duration) / 1000  # 转换为秒
                        except (ValueError, TypeError):
                            duration = 0
                    elif hasattr(track, 'other_duration') and track.other_duration:
                        try:
                            # 尝试从其他格式获取时长
                            duration_str = track.other_duration[0]  # 格式如 "1mn 23s"
                            duration = self.parse_duration_string(duration_str)
                        except:
                            duration = 0
                    break
            
            # 格式化结果
            resolution = f"{width}×{height}" if width and height else "未知"
            fps_str = f"{fps}" if fps else "未知"
            duration_str = self.format_seconds_to_hms(duration) if duration > 0 else "未知"
            
            return resolution, fps_str, duration_str
            
        except ImportError:
            self.logger.error("pymediainfo库未安装")
            return "未知", "未知", "未知"
        except Exception as e:
            self.logger.error(f"使用pymediainfo获取视频信息时发生异常: {str(e)}")
            return "未知", "未知", "未知"

    def parse_duration_string(self, duration_str):
        """解析MediaInfo提供的时长字符串，转换为秒数"""
        import re
        
        # 匹配 "Xmn Ys" 或 "Xh Ymn Zs" 等格式
        hours = minutes = seconds = 0
        
        # 匹配小时
        hour_match = re.search(r'(\d+)h', duration_str, re.IGNORECASE)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # 匹配分钟
        min_match = re.search(r'(\d+)mn', duration_str, re.IGNORECASE)
        if min_match:
            minutes = int(min_match.group(1))
        
        # 匹配秒
        sec_match = re.search(r'(\d+(?:\.\d+)?)s', duration_str, re.IGNORECASE)
        if sec_match:
            seconds = float(sec_match.group(1))
        
        return hours * 3600 + minutes * 60 + seconds

    def format_seconds_to_hms(self, seconds):
        """将秒数格式化为HH:MM:SS或MM:SS格式"""
        try:
            total_seconds = int(float(seconds))
            if total_seconds <= 0:
                return "未知"
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            secs = total_seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
            else:
                return f"{minutes:02d}:{secs:02d}"
        except:
            return "未知"
    
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
        """扫描输入文件夹中的视频文件 - 异步执行"""
        # 在新线程中执行扫描操作，避免阻塞UI
        scan_thread = threading.Thread(target=self._async_scan_videos, daemon=True)
        scan_thread.start()
    
    def _async_scan_videos(self):
        """异步扫描视频文件的内部实现"""
        input_folder = self.input_folder_var.get()
        output_folder = self.output_folder_var.get()
        
        if not input_folder or not os.path.exists(input_folder):
            self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", "请输入有效的输入文件夹路径！"))
            return
        
        if not output_folder:
            self.root.after(0, lambda: self.show_custom_messagebox("warning", "警告", "输出文件夹未设置，将无法判断已处理视频"))
            return
        
        # 清空现有列表
        self.root.after(0, lambda: self.clear_lists(clear_summary=False))
        
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
            
            # 更新状态，显示正在扫描
            self.root.after(0, lambda: self.status_var.set(f"正在扫描视频... (0/{len(input_files)})"))
            
            # 分类视频文件
            for idx, video_file in enumerate(input_files):
                # 更新进度
                self.root.after(0, lambda i=idx+1, t=len(input_files): self.status_var.set(f"正在扫描视频... ({i}/{t})"))
                
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
                    # 在主线程中更新视频列表
                    self.root.after(0, lambda v=video_info: self.video_lists["processed"].append(v))
                    
                    # 移动已处理过的源视频到成功文件夹
                    success_folder = self.success_folder_var.get()
                    if success_folder:
                        # 在主线程中执行移动操作
                        self.root.after(0, lambda vp=video_path, vf=video_file: self.move_already_processed_to_success_folder(vp, vf))
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
                    # 在主线程中更新视频列表
                    self.root.after(0, lambda v=video_info: self.video_lists["unprocessed"].append(v))
            
            # 在主线程中更新列表显示和总结
            self.root.after(0, self.update_lists_display)
            self.root.after(0, self.update_summary)
            self.root.after(0, lambda: self.status_var.set(f"扫描完成！找到 {len(input_files)} 个视频文件"))
            self.logger.info(f"扫描完成！找到 {len(input_files)} 个视频文件")
            
        except Exception as e:
            self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", f"扫描视频时出错: {str(e)}"))
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
                    speed_info = f"[速度: {video['processing_speed']}]"
                    
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
    
    def show_processing_mode_indicator(self):
        """显示处理状态指示器"""
        self.processing_mode_label.place(x=450, y=5, width=50, height=30)
    
    def hide_processing_mode_indicator(self):
        """隐藏处理状态指示器"""
        self.processing_mode_label.place_forget()
    
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
        self.is_transcoding = False  # 添加转码状态标志
        
        # 显示处理状态指示器
        self.root.after(0, self.show_processing_mode_indicator)
        
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
            
            # 开始处理前，显示"破解"状态标识
            self.processing_mode_var.set("破解")
            self.processing_mode_label.place(x=450, y=5, width=50, height=30)
            
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
                
                # 重置处理错误标志
                self.processing_error = False
                
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
                
                # 检查视频帧率是否是标准帧率
                fps_str = self.video_fps_var.get()
                standard_fps = [23.976, 24, 25, 29.97, 30, 59.94, 60, 120]
                is_standard_fps = False
                
                if fps_str != "未知":
                    try:
                        fps = float(fps_str)
                        # 检查帧率是否在标准帧率列表中，允许小误差
                        for standard_f in standard_fps:
                            if abs(fps - standard_f) < 0.001:
                                is_standard_fps = True
                                break
                    except ValueError:
                        pass
                
                # 记录视频信息显示状态
                self.root.after(0, lambda: self.logger.info(f"视频信息显示状态 - 分辨率: {self.video_resolution_var.get()}, 帧率: {self.video_fps_var.get()}, 时长: {self.video_duration_var.get()}"))
                
                # 如果帧率不是标准帧率，则直接标记为处理出错并进行转码处理
                if not is_standard_fps:
                    self.logger.warning(f"视频帧率不是标准帧率: {fps_str}，直接标记为处理出错并进行转码处理")
                    
                    # 将视频从未处理列表移到错误列表
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
                    
                    # 移动源视频到错误文件夹
                    error_folder = self.error_folder_var.get()
                    if error_folder:
                        error_moved = self.move_to_error_folder(input_path, video_file)
                        if error_moved:
                            self.logger.info(f"错误视频已移动到错误文件夹: {video_file}")
                        else:
                            self.logger.warning(f"错误视频移动失败: {video_file}")
                    
                    # 更新GUI
                    self.root.after(0, self.update_lists_display)
                    self.root.after(0, self.update_summary)
                    
                    self.logger.error(f"视频处理失败: {video_file}")
                    self.root.after(0, lambda: self.status_var.set(f"视频处理失败: {video_file}"))
                    
                    # 立即对错误视频执行转码操作
                    if error_folder and os.path.exists(error_folder):
                        error_video_path = os.path.join(error_folder, video_file)
                        if os.path.exists(error_video_path):
                            # 检查是否用户请求停止处理
                            if self.stop_processing:
                                self.logger.info("用户请求停止处理，跳过转码")
                                break
                            
                            self.logger.info(f"开始转码错误视频: {video_file}")
                            
                            # 设置转码状态
                            self.root.after(0, lambda vm=video_file: self.current_video_var.set(vm))
                            self.root.after(0, lambda: self.processing_mode_var.set("转码"))
                            
                            # 执行转码
                            transcoded_video_name = f"{Path(video_file).stem}-转码{Path(video_file).suffix}"
                            transcoded_video_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                            
                            transcode_success = self.transcode_video(error_video_path, transcoded_video_path)
                            
                            # 检查是否用户请求停止处理
                            if self.stop_processing:
                                self.logger.info("用户请求停止处理，跳过再次处理")
                                break
                            
                            if transcode_success:
                                # 转码成功，立即对转码后的视频再次执行处理操作
                                self.logger.info(f"转码成功，开始再次处理转码后的视频: {transcoded_video_name}")
                                
                                # 重置卡死标志
                                self.is_stuck = False
                                self.stuck_detected = False
                                
                                # 重置处理错误标志
                                self.processing_error = False
                                
                                self.currently_processing = transcoded_video_name
                                self.current_video_var.set(transcoded_video_name)
                                self.processing_mode_var.set("破解")  # 设置为破解模式
                                
                                # 重置进度信息显示
                                self.root.after(0, self.reset_progress_display)
                                
                                # 构建输入路径
                                transcoded_input_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                                
                                self.logger.info(f"构建的转码后视频输入路径: {transcoded_input_path}")
                                self.logger.info(f"输入文件夹: {self.input_folder_var.get()}")
                                self.logger.info(f"转码后视频文件: {transcoded_video_name}")
                                self.logger.info(f"输入路径是否存在: {os.path.exists(transcoded_input_path)}")
                                
                                # 获取视频信息
                                self.logger.info("开始调用get_video_info函数")
                                success = self.get_video_info(transcoded_input_path)
                                self.logger.info(f"get_video_info函数返回值: {success}")
                                
                                # 记录视频处理开始时间，用于计算处理速度
                                processing_start_time = time.time()
                                
                                # 获取视频信息并检测分辨率
                                video_width = self.get_video_info(transcoded_input_path)
                                is_4k_video = video_width >= 3840
                                
                                # 记录视频信息显示状态（无论成功与否都继续处理）
                                self.root.after(0, lambda: self.logger.info(f"视频信息显示状态 - 分辨率: {self.video_resolution_var.get()}, 帧率: {self.video_fps_var.get()}, 时长: {self.video_duration_var.get()}"))
                                
                                # 根据分辨率选择切片帧数参数
                                if is_4k_video:
                                    current_slice_frames = int(self.slice_frames_var2.get())
                                    self.logger.info(f"视频分辨率为4K及以上，使用第二个输入框的切片帧数: {current_slice_frames}")
                                else:
                                    current_slice_frames = int(self.slice_frames_var1.get())
                                    self.logger.info(f"视频分辨率低于4K，使用第一个输入框的切片帧数: {current_slice_frames}")
                                
                                # 检查当前切片帧数是否已存在于历史记录中
                                is_slice_frames_first_time = current_slice_frames not in self.slice_frames_history
                                
                                # 检查当前检测模型是否已存在于历史记录中
                                current_detection_model = self.detection_model_var.get()
                                is_detection_model_first_time = current_detection_model not in self.detection_model_history
                                
                                # 判断是否需要首次编译
                                is_first_time_for_model_compile = False  # 标记是否是模型编译的首次运行
                                if is_slice_frames_first_time or is_detection_model_first_time:
                                    # 弹窗提示用户
                                    self.root.after(0, lambda: self.show_custom_messagebox("info", "提示", "当前切片帧数或检测模型为首次使用\n需要编译模型 \n\n所需时间为0.2小时到4小时之间"))
                                    # 临时将卡死超时时间设置为15000秒
                                    self.stuck_seconds_var.set("15000")
                                    self.stuck_seconds_modified = True  # 标记stuck_seconds值已被修改
                                    is_first_time_for_model_compile = True  # 标记本次处理是首次模型编译
                                
                                # 记录检查结果
                                self.logger.info(f"双重检查结果 - 切片帧数首次使用: {is_slice_frames_first_time}, 检测模型首次使用: {is_detection_model_first_time}")
                                
                                # 构建输出文件名（添加后缀和.mp4扩展名）
                                transcoded_video_name_only = Path(transcoded_video_name).stem
                                suffix = self.output_suffix_var.get()
                                final_output_filename = f"{transcoded_video_name_only}{suffix}.mp4"
                                final_output_path = os.path.join(output_folder, final_output_filename)
                                
                                # 启动卡死监测线程（根据是否首次使用设置不同的阈值）
                                if is_first_time_for_model_compile:
                                    self.start_stuck_monitor(custom_stuck_seconds=15000)
                                else:
                                    self.start_stuck_monitor()
                                
                                # 构建命令字符串
                                encode_params = f'"{self.encode_params_var.get()}"'
                                
                                # 构建基础命令，使用根据分辨率选择的切片帧数
                                cmd = f'.\\{jasna_exe_name} --input "{transcoded_input_path}" --output "{final_output_path}" --max-clip-size {current_slice_frames} --codec hevc --encoder-settings {encode_params} --log-level info --detection-model {self.detection_model_var.get()} --detection-score-threshold {self.detection_threshold_var.get()}'
                                
                                # 根据二次修复模块中"使用软件"组件的选择，添加相应参数
                                secondary_fix_option = self.secondary_fix_var.get()
                                if secondary_fix_option == "TVAI":
                                    # 添加TVAI相关参数
                                    ffmpeg_path = self.ffmpeg_path_var.get()
                                    model_name = self.tvai_model_var.get()
                                    scale = self.tvai_scale_var.get()
                                    threads = self.tvai_threads_var.get()
                                    tvai_params = self.tvai_params_var.get()
                                    
                                    # 处理TVAI缩放参数的特殊转换规则
                                    if scale == "1":
                                        tvai_scale = "0"
                                    else:
                                        tvai_scale = scale
                                    
                                    cmd += f' --secondary-restoration tvai --tvai-ffmpeg-path "{ffmpeg_path}" --tvai-model {model_name} --tvai-scale {tvai_scale} --tvai-workers {threads} --tvai-args "{tvai_params}"'
                                elif secondary_fix_option == "RTX-SR":
                                    # 添加RTX-SR相关参数
                                    rtx_scale = self.rtx_sr_scale_var.get().replace("X", "")  # 2X->2, 4X->4
                                    rtx_quality = self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get())
                                    rtx_denoise = self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get())
                                    rtx_deblur = self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get())
                                    cmd += f' --secondary-restoration rtx-super-res --rtx-quality {rtx_quality} --rtx-denoise {rtx_denoise} --rtx-deblur {rtx_deblur} --rtx-scale {rtx_scale}'

                                # 添加VR模式参数
                                vr_mode = self.vr_mode_var.get()
                                if vr_mode == "自动":
                                    cmd += ' --vr-mode auto'
                                elif vr_mode == "SBS":
                                    cmd += ' --vr-mode sbs'
                                elif vr_mode == "鱼眼":
                                    cmd += ' --vr-mode sbs-fisheye'

                                self.logger.info(f"开始处理转码后的视频: {transcoded_video_name}")
                                self.logger.info(f"完整命令: {cmd}")
                                self.logger.info(f"工作目录: {jasna_dir}")
                                self.logger.info(f"当前切片帧数: {current_slice_frames}, 是否首次使用: {is_first_time_for_model_compile}")
                                
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
                                    args=(process, transcoded_video_name)
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
                                    self.logger.warning(f"检测到转码后视频卡死，已终止处理: {transcoded_video_name}")
                                    
                                    # 如果是首次使用当前切片帧数且发生卡死（模型编译失败），弹窗提示错误
                                    if is_first_time_for_model_compile:
                                        self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", "模型编译失败，请检查系统设置、内存大小、显存大小，可适当调低切片帧数后重新运行"))
                                        
                                        # 立即恢复原始的stuck_seconds值，因为模型编译失败，不需要将切片帧数添加到历史记录
                                        if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                            self.stuck_seconds_var.set(self.original_stuck_seconds)
                                            self.stuck_seconds_modified = False
                                            self.logger.info(f"模型编译失败 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                        
                                        # 不将当前切片帧数添加到历史记录，直接跳出
                                        continue
                                    
                                    # 执行卡死处理流程（已转码重试，标记is_retry=True）
                                    self.handle_stuck_video(transcoded_video_name, transcoded_input_path, transcoded_video_name_only, suffix, output_folder, is_retry=True)
                                    
                                    # 检查是否用户请求停止处理
                                    if self.stop_processing:
                                        self.logger.info("用户请求停止处理，退出视频处理循环")
                                        break
                                    
                                    # 重置当前处理视频
                                    self.currently_processing = None
                                    self.current_video_var.set("无")
                                    self.processing_mode_var.set("破解")  # 重置为默认破解模式
                                    
                                    # 重置进度条
                                    self.root.after(0, self.reset_progress_display)
                                    
                                    # 清空日志文件
                                    self.clear_log_file()
                                    
                                    # 重置停止标志，以便继续处理下一个视频
                                    self.stop_processing = False
                                    continue
                                
                                # 检查进程是否成功完成
                                if return_code == 0 and not self.stop_processing:
                                    # 处理成功
                                    # 检查最终文件是否存在
                                    success = self.check_final_file_exists(transcoded_video_name_only, suffix, output_folder)
                                    
                                    if success:
                                        # 计算处理速度 - 与直接处理成功的计算方式一致
                                        processing_end_time = time.time()
                                        processing_duration = processing_end_time - processing_start_time  # 处理该视频的总运行时间（秒）
                                        
                                        # 使用总帧数除以处理时间来计算速度
                                        total_frames = self.estimate_total_frames(transcoded_input_path)
                                        if total_frames > 0 and processing_duration > 0:
                                            processing_speed = total_frames / processing_duration
                                            processing_speed_str = f"{int(processing_speed)}fps"
                                        else:
                                            processing_speed_str = "未知"
                                        
                                        # 将转码后的视频从未处理列表移到已处理列表
                                        # 先找到要移除的项
                                        item_to_remove = None
                                        for item in self.video_lists["unprocessed"]:
                                            if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                               (isinstance(item, str) and item == transcoded_video_name):
                                                item_to_remove = item
                                                break
                                        
                                        if item_to_remove is not None:
                                            self.video_lists["unprocessed"].remove(item_to_remove)
                                            # 保持相同的数据结构格式，但为已处理视频添加处理速度信息
                                            if isinstance(item_to_remove, dict):
                                                processed_video_info = {
                                                    'name': item_to_remove['name'],
                                                    'processing_speed': processing_speed_str
                                                }
                                            else:
                                                processed_video_info = {
                                                    'name': transcoded_video_name,
                                                    'processing_speed': processing_speed_str
                                                }
                                            
                                            self.video_lists["processed"].append(processed_video_info)
                                        
                                        # 处理成功后移动源视频到成功文件夹
                                        success_folder = self.success_folder_var.get()
                                        if success_folder:
                                            success_moved = self.move_to_success_folder(transcoded_input_path, transcoded_video_name)
                                            if success_moved:
                                                self.logger.info(f"成功视频已移动到成功文件夹: {transcoded_video_name}")
                                            else:
                                                self.logger.warning(f"成功视频移动失败: {transcoded_video_name}")
                                        
                                        # 从错误列表中移除原始视频并添加到已处理列表
                                        # 先找到要移除的原始视频项
                                        original_item_to_remove = None
                                        for item in self.video_lists["error"]:
                                            if (isinstance(item, dict) and item['name'] == video_file) or \
                                               (isinstance(item, str) and item == video_file):
                                                original_item_to_remove = item
                                                break
                                        
                                        if original_item_to_remove is not None:
                                            self.video_lists["error"].remove(original_item_to_remove)
                                            # 创建已处理视频的信息（包含处理速度）
                                            if isinstance(original_item_to_remove, dict):
                                                processed_original_video_info = {
                                                    'name': original_item_to_remove['name'],
                                                    'processing_speed': processing_speed_str
                                                }
                                            else:
                                                processed_original_video_info = {
                                                    'name': video_file,
                                                    'processing_speed': processing_speed_str
                                                }
                                            self.video_lists["processed"].append(processed_original_video_info)
                                            
                                            # 将原始视频从错误文件夹移动到成功文件夹
                                            success_folder = self.success_folder_var.get()
                                            if success_folder:
                                                original_error_video_path = os.path.join(error_folder, video_file)
                                                if os.path.exists(original_error_video_path):
                                                    # 构建成功文件夹中的目标路径
                                                    success_original_video_path = os.path.join(success_folder, video_file)
                                                    try:
                                                        # 移动文件
                                                        shutil.move(original_error_video_path, success_original_video_path)
                                                        self.logger.info(f"原始错误视频已移动到成功文件夹: {video_file}")
                                                    except Exception as e:
                                                        self.logger.error(f"移动原始错误视频时出错: {str(e)}")
                                        
                                        # 如果是首次使用且处理成功，将切片帧数和检测模型添加到历史记录
                                        if is_first_time_for_model_compile:
                                            current_detection_model = self.detection_model_var.get()
                                            # 检查切片帧数是否已存在于历史记录中，避免重复添加
                                            if current_slice_frames not in self.slice_frames_history:
                                                self.slice_frames_history.append(current_slice_frames)
                                                self.logger.info(f"将切片帧数 {current_slice_frames} 添加到历史记录")
                                            # 检查检测模型是否已存在于历史记录中，避免重复添加
                                            if current_detection_model not in self.detection_model_history:
                                                self.detection_model_history.append(current_detection_model)
                                                self.logger.info(f"将检测模型 {current_detection_model} 添加到历史记录")
                                                
                                            # 立即恢复原始的stuck_seconds值，避免后续视频处理受到影响
                                            if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                                self.stuck_seconds_var.set(self.original_stuck_seconds)
                                                self.stuck_seconds_modified = False
                                                self.logger.info(f"首次运行完成 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                            
                                            # 立即保存配置文件，确保历史记录被保存
                                            self.save_settings()
                                            self.logger.info("编译模式处理成功，已保存配置文件")
                                        
                                        # 更新GUI
                                        self.root.after(0, self.update_lists_display)
                                        self.root.after(0, self.update_summary)
                                        
                                        self.logger.info(f"转码后视频处理完成: {transcoded_video_name}")
                                        self.root.after(0, lambda: self.status_var.set(f"转码后视频处理完成: {transcoded_video_name}"))
                                    else:
                                        # 最终文件不存在，视为处理失败
                                        self.logger.error(f"转码后视频处理完成但最终文件不存在: {transcoded_video_name}")
                                        
                                        # 将视频从未处理列表移到错误列表
                                        # 先找到要移除的项
                                        item_to_remove = None
                                        for item in self.video_lists["unprocessed"]:
                                            if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                               (isinstance(item, str) and item == transcoded_video_name):
                                                item_to_remove = item
                                                break
                                        
                                        if item_to_remove is not None:
                                            self.video_lists["unprocessed"].remove(item_to_remove)
                                            # 保持相同的数据结构格式
                                            if isinstance(item_to_remove, dict):
                                                self.video_lists["error"].append(item_to_remove)
                                            else:
                                                self.video_lists["error"].append(transcoded_video_name)
                                        
                                        # 删除转码后的视频文件
                                        if os.path.exists(transcoded_input_path):
                                            try:
                                                os.remove(transcoded_input_path)
                                                self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                            except Exception as e:
                                                self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                        
                                        # 更新GUI
                                        self.root.after(0, self.update_lists_display)
                                        self.root.after(0, self.update_summary)
                                        
                                        self.logger.error(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}")
                                        self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}"))
                                else:
                                    # 处理失败或被停止
                                    if self.stop_processing:
                                        self.logger.info(f"转码后视频处理被用户停止: {transcoded_video_name}")
                                        
                                        # 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
                                        self.root.after(2000, lambda: self.cleanup_temp_files_after_stop(transcoded_video_name_only, suffix, output_folder, delete_final_file=True))
                                        
                                        # 如果用户停止，不清空列表，视频保留在未处理列表中
                                        self.root.after(0, lambda: self.status_var.set(f"转码后视频处理被停止: {transcoded_video_name}"))
                                        break  # 跳出循环，不再处理后续视频
                                    else:
                                        # 处理失败后恢复原始的stuck_seconds值
                                        if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                            self.stuck_seconds_var.set(self.original_stuck_seconds)
                                            self.stuck_seconds_modified = False
                                            self.logger.info(f"转码后视频处理失败 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                        
                                        self.logger.error(f"JASNA返回错误代码: {return_code}")
                                        
                                        # 清理可能生成的临时文件（包括最终文件）
                                        self.cleanup_temp_files(transcoded_video_name_only, suffix, output_folder, delete_final_file=True)
                                        
                                        # 将视频从未处理列表移到错误列表
                                        # 先找到要移除的项
                                        item_to_remove = None
                                        for item in self.video_lists["unprocessed"]:
                                            if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                               (isinstance(item, str) and item == transcoded_video_name):
                                                item_to_remove = item
                                                break
                                        
                                        if item_to_remove is not None:
                                            self.video_lists["unprocessed"].remove(item_to_remove)
                                            # 保持相同的数据结构格式
                                            if isinstance(item_to_remove, dict):
                                                self.video_lists["error"].append(item_to_remove)
                                            else:
                                                self.video_lists["error"].append(transcoded_video_name)
                                        
                                        # 删除转码后的视频文件
                                        if os.path.exists(transcoded_input_path):
                                            try:
                                                os.remove(transcoded_input_path)
                                                self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                            except Exception as e:
                                                self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                        
                                        # 更新GUI
                                        self.root.after(0, self.update_lists_display)
                                        self.root.after(0, self.update_summary)
                                        
                                        self.logger.error(f"转码后视频处理失败: {transcoded_video_name}")
                                        self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败: {transcoded_video_name}"))
                            else:
                                self.logger.error(f"转码失败: {video_file}")
                    
                    # 重置当前处理视频
                    self.currently_processing = None
                    self.current_video_var.set("无")
                    
                    # 重置进度条
                    self.root.after(0, self.reset_progress_display)
                    
                    # 清空日志文件
                    self.clear_log_file()
                    
                    # 重置停止标志，以便继续处理下一个视频
                    self.stop_processing = False
                    continue
                
                # 记录视频处理开始时间，用于计算处理速度
                processing_start_time = time.time()
                
                # 获取视频信息并检测分辨率
                video_width = self.get_video_info(input_path)
                is_4k_video = video_width >= 3840
                
                # 根据分辨率选择切片帧数参数
                if is_4k_video:
                    current_slice_frames = int(self.slice_frames_var2.get())
                    self.logger.info(f"视频分辨率为4K及以上，使用第二个输入框的切片帧数: {current_slice_frames}")
                else:
                    current_slice_frames = int(self.slice_frames_var1.get())
                    self.logger.info(f"视频分辨率低于4K，使用第一个输入框的切片帧数: {current_slice_frames}")
                
                # 检查当前切片帧数是否已存在于历史记录中
                is_slice_frames_first_time = current_slice_frames not in self.slice_frames_history
                
                # 检查当前检测模型是否已存在于历史记录中
                current_detection_model = self.detection_model_var.get()
                is_detection_model_first_time = current_detection_model not in self.detection_model_history
                
                # 判断是否需要首次编译
                is_first_time_for_model_compile = False  # 标记是否是模型编译的首次运行
                if is_slice_frames_first_time or is_detection_model_first_time:
                    # 弹窗提示用户
                    self.root.after(0, lambda: self.show_custom_messagebox("info", "提示", "当前切片帧数或检测模型为首次使用\n需要编译模型 \n\n所需时间为0.2小时到4小时之间"))
                    # 临时将卡死超时时间设置为15000秒
                    self.stuck_seconds_var.set("15000")
                    self.stuck_seconds_modified = True  # 标记stuck_seconds值已被修改
                    is_first_time_for_model_compile = True  # 标记本次处理是首次模型编译
                
                # 记录检查结果
                self.logger.info(f"双重检查结果 - 切片帧数首次使用: {is_slice_frames_first_time}, 检测模型首次使用: {is_detection_model_first_time}")
                
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
                
                # 构建基础命令，使用根据分辨率选择的切片帧数
                cmd = f'.\\{jasna_exe_name} --input "{input_path}" --output "{final_output_path}" --max-clip-size {current_slice_frames} --codec hevc --encoder-settings {encode_params} --log-level info --detection-model {self.detection_model_var.get()} --detection-score-threshold {self.detection_threshold_var.get()}'
                
                # 根据二次修复模块中"使用软件"组件的选择，添加相应参数
                secondary_fix_option = self.secondary_fix_var.get()
                if secondary_fix_option == "TVAI":
                    # 添加TVAI相关参数
                    ffmpeg_path = self.ffmpeg_path_var.get()
                    model_name = self.tvai_model_var.get()
                    scale = self.tvai_scale_var.get()
                    threads = self.tvai_threads_var.get()
                    tvai_params = self.tvai_params_var.get()
                    
                    # 处理TVAI缩放参数的特殊转换规则
                    if scale == "1":
                        tvai_scale = "0"
                    else:
                        tvai_scale = scale
                    
                    cmd += f' --secondary-restoration tvai --tvai-ffmpeg-path "{ffmpeg_path}" --tvai-model {model_name} --tvai-scale {tvai_scale} --tvai-workers {threads} --tvai-args "{tvai_params}"'
                elif secondary_fix_option == "RTX-SR":
                    # 添加RTX-SR相关参数
                    rtx_scale = self.rtx_sr_scale_var.get().replace("X", "")  # 2X->2, 4X->4
                    rtx_quality = self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get())
                    rtx_denoise = self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get())
                    rtx_deblur = self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get())
                    cmd += f' --secondary-restoration rtx-super-res --rtx-quality {rtx_quality} --rtx-denoise {rtx_denoise} --rtx-deblur {rtx_deblur} --rtx-scale {rtx_scale}'

                # 添加VR模式参数
                vr_mode = self.vr_mode_var.get()
                if vr_mode == "自动":
                    cmd += ' --vr-mode auto'
                elif vr_mode == "SBS":
                    cmd += ' --vr-mode sbs'
                elif vr_mode == "鱼眼":
                    cmd += ' --vr-mode sbs-fisheye'

                self.logger.info(f"开始处理视频: {video_file}")
                self.logger.info(f"完整命令: {cmd}")
                self.logger.info(f"工作目录: {jasna_dir}")
                self.logger.info(f"当前切片帧数: {current_slice_frames}, 是否首次使用: {is_first_time_for_model_compile}")
                
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
                    
                    # 检查是否用户请求停止处理
                    if self.stop_processing:
                        self.logger.info("用户请求停止处理，退出视频处理循环")
                        break
                    
                    # 重置当前处理视频
                    self.currently_processing = None
                    self.current_video_var.set("无")
                    
                    # 重置进度条
                    self.root.after(0, self.reset_progress_display)
                    
                    # 清空日志文件
                    self.clear_log_file()
                    
                    # 不使用continue，因为handle_stuck_video方法已经包含了转码和再次处理的逻辑
                    # 直接继续执行后续代码
                
                # 检查进程是否成功完成
                if return_code == 0 and not self.stop_processing and not self.processing_error:
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
                            if processing_duration > 0:
                                # 使用总帧数除以处理时间（秒）计算fps
                                input_path = os.path.join(self.input_folder_var.get(), video_file)
                                total_frames = self.estimate_total_frames(input_path)
                                if total_frames > 0:
                                    processing_speed = total_frames / processing_duration
                                    # 只保留整数
                                    processing_speed_str = f"{int(processing_speed)}fps"
                                else:
                                    processing_speed_str = "未知"
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
                        
                        # 如果是首次使用且处理成功，将切片帧数和检测模型添加到历史记录
                        if is_first_time_for_model_compile:
                            current_detection_model = self.detection_model_var.get()
                            # 检查切片帧数是否已存在于历史记录中，避免重复添加
                            if current_slice_frames not in self.slice_frames_history:
                                self.slice_frames_history.append(current_slice_frames)
                                self.logger.info(f"将切片帧数 {current_slice_frames} 添加到历史记录")
                            # 检查检测模型是否已存在于历史记录中，避免重复添加
                            if current_detection_model not in self.detection_model_history:
                                self.detection_model_history.append(current_detection_model)
                                self.logger.info(f"将检测模型 {current_detection_model} 添加到历史记录")
                                
                            # 立即恢复原始的stuck_seconds值，避免后续视频处理受到影响
                            if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                self.stuck_seconds_var.set(self.original_stuck_seconds)
                                self.stuck_seconds_modified = False
                                self.logger.info(f"首次运行完成 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                            
                            # 立即保存配置文件，确保历史记录被保存
                            self.save_settings()
                            self.logger.info("编译模式处理成功，已保存配置文件")
                        
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
                        # 检查是否是处理过程中出现错误
                        if self.processing_error:
                            self.logger.error(f"JASNA处理过程中出现错误")
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
                        
                        # 移动源视频到错误文件夹
                        error_folder = self.error_folder_var.get()
                        if error_folder:
                            error_moved = self.move_to_error_folder(input_path, video_file)
                            if error_moved:
                                self.logger.info(f"错误视频已移动到错误文件夹: {video_file}")
                            else:
                                self.logger.warning(f"错误视频移动失败: {video_file}")
                        
                        # 更新GUI
                        self.root.after(0, self.update_lists_display)
                        self.root.after(0, self.update_summary)
                        
                        # 处理失败后恢复原始的stuck_seconds值
                        if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                            self.stuck_seconds_var.set(self.original_stuck_seconds)
                            self.stuck_seconds_modified = False
                            self.logger.info(f"视频处理失败 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                        
                        self.logger.error(f"视频处理失败: {video_file}")
                        self.root.after(0, lambda: self.status_var.set(f"视频处理失败: {video_file}"))
                        
                        # 立即对错误视频执行转码操作
                        if error_folder and os.path.exists(error_folder):
                            error_video_path = os.path.join(error_folder, video_file)
                            if os.path.exists(error_video_path):
                                # 检查是否用户请求停止处理
                                if self.stop_processing:
                                    self.logger.info("用户请求停止处理，跳过转码")
                                    break
                                
                                self.logger.info(f"开始转码错误视频: {video_file}")
                                
                                # 设置转码状态
                                self.root.after(0, lambda vm=video_file: self.current_video_var.set(vm))
                                self.root.after(0, lambda: self.processing_mode_var.set("转码"))
                                
                                # 执行转码
                                transcoded_video_name = f"{Path(video_file).stem}-转码{Path(video_file).suffix}"
                                transcoded_video_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                                
                                transcode_success = self.transcode_video(error_video_path, transcoded_video_path)
                                
                                # 检查是否用户请求停止处理
                                if self.stop_processing:
                                    self.logger.info("用户请求停止处理，跳过再次处理")
                                    break
                                
                                if transcode_success:
                                    # 转码成功，立即对转码后的视频再次执行处理操作
                                    self.logger.info(f"转码成功，开始再次处理转码后的视频: {transcoded_video_name}")
                                    
                                    # 重置卡死标志
                                    self.is_stuck = False
                                    self.stuck_detected = False
                                    
                                    # 重置处理错误标志
                                    self.processing_error = False
                                    
                                    self.currently_processing = transcoded_video_name
                                    self.current_video_var.set(transcoded_video_name)
                                    self.processing_mode_var.set("破解")  # 设置为破解模式
                                    
                                    # 重置进度信息显示
                                    self.root.after(0, self.reset_progress_display)
                                    
                                    # 构建输入路径
                                    transcoded_input_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                                    
                                    self.logger.info(f"构建的转码后视频输入路径: {transcoded_input_path}")
                                    self.logger.info(f"输入文件夹: {self.input_folder_var.get()}")
                                    self.logger.info(f"转码后视频文件: {transcoded_video_name}")
                                    self.logger.info(f"输入路径是否存在: {os.path.exists(transcoded_input_path)}")
                                    
                                    # 获取视频信息
                                    self.logger.info("开始调用get_video_info函数")
                                    success = self.get_video_info(transcoded_input_path)
                                    self.logger.info(f"get_video_info函数返回值: {success}")
                                    
                                    # 记录视频处理开始时间，用于计算处理速度
                                    processing_start_time = time.time()
                                    
                                    # 获取视频信息并检测分辨率
                                    video_width = self.get_video_info(transcoded_input_path)
                                    is_4k_video = video_width >= 3840
                                    
                                    # 记录视频信息显示状态（无论成功与否都继续处理）
                                    self.root.after(0, lambda: self.logger.info(f"视频信息显示状态 - 分辨率: {self.video_resolution_var.get()}, 帧率: {self.video_fps_var.get()}, 时长: {self.video_duration_var.get()}"))
                                    
                                    # 根据分辨率选择切片帧数参数
                                    if is_4k_video:
                                        current_slice_frames = int(self.slice_frames_var2.get())
                                        self.logger.info(f"视频分辨率为4K及以上，使用第二个输入框的切片帧数: {current_slice_frames}")
                                    else:
                                        current_slice_frames = int(self.slice_frames_var1.get())
                                        self.logger.info(f"视频分辨率低于4K，使用第一个输入框的切片帧数: {current_slice_frames}")
                                    
                                    # 检查当前切片帧数是否已存在于历史记录中
                                    is_slice_frames_first_time = current_slice_frames not in self.slice_frames_history
                                    
                                    # 检查当前检测模型是否已存在于历史记录中
                                    current_detection_model = self.detection_model_var.get()
                                    is_detection_model_first_time = current_detection_model not in self.detection_model_history
                                    
                                    # 判断是否需要首次编译
                                    is_first_time_for_model_compile = False  # 标记是否是模型编译的首次运行
                                    if is_slice_frames_first_time or is_detection_model_first_time:
                                        # 弹窗提示用户
                                        self.root.after(0, lambda: self.show_custom_messagebox("info", "提示", "当前切片帧数或检测模型为首次使用\n需要编译模型 \n\n所需时间为0.2小时到4小时之间"))
                                        # 临时将卡死超时时间设置为15000秒
                                        self.stuck_seconds_var.set("15000")
                                        self.stuck_seconds_modified = True  # 标记stuck_seconds值已被修改
                                        is_first_time_for_model_compile = True  # 标记本次处理是首次模型编译
                                    
                                    # 记录检查结果
                                    self.logger.info(f"双重检查结果 - 切片帧数首次使用: {is_slice_frames_first_time}, 检测模型首次使用: {is_detection_model_first_time}")
                                    
                                    # 构建输出文件名（添加后缀和.mp4扩展名）
                                    transcoded_video_name_only = Path(transcoded_video_name).stem
                                    suffix = self.output_suffix_var.get()
                                    final_output_filename = f"{transcoded_video_name_only}{suffix}.mp4"
                                    final_output_path = os.path.join(output_folder, final_output_filename)
                                    
                                    # 启动卡死监测线程（根据是否首次使用设置不同的阈值）
                                    if is_first_time_for_model_compile:
                                        self.start_stuck_monitor(custom_stuck_seconds=15000)
                                    else:
                                        self.start_stuck_monitor()
                                    
                                    # 构建命令字符串
                                    encode_params = f'"{self.encode_params_var.get()}"'
                                    
                                    # 构建基础命令，使用根据分辨率选择的切片帧数
                                    cmd = f'.\\{jasna_exe_name} --input "{transcoded_input_path}" --output "{final_output_path}" --max-clip-size {current_slice_frames} --codec hevc --encoder-settings {encode_params} --log-level info --detection-model {self.detection_model_var.get()} --detection-score-threshold {self.detection_threshold_var.get()}'
                                    
                                    # 根据二次修复模块中"使用软件"组件的选择，添加相应参数
                                    secondary_fix_option = self.secondary_fix_var.get()
                                    if secondary_fix_option == "TVAI":
                                        # 添加TVAI相关参数
                                        ffmpeg_path = self.ffmpeg_path_var.get()
                                        model_name = self.tvai_model_var.get()
                                        scale = self.tvai_scale_var.get()
                                        threads = self.tvai_threads_var.get()
                                        tvai_params = self.tvai_params_var.get()
                                        
                                        # 处理TVAI缩放参数的特殊转换规则
                                        if scale == "1":
                                            tvai_scale = "0"
                                        else:
                                            tvai_scale = scale
                                        
                                        cmd += f' --secondary-restoration tvai --tvai-ffmpeg-path "{ffmpeg_path}" --tvai-model {model_name} --tvai-scale {tvai_scale} --tvai-workers {threads} --tvai-args "{tvai_params}"'
                                    elif secondary_fix_option == "RTX-SR":
                                        # 添加RTX-SR相关参数
                                        rtx_scale = self.rtx_sr_scale_var.get().replace("X", "")  # 2X->2, 4X->4
                                        rtx_quality = self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get())
                                        rtx_denoise = self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get())
                                        rtx_deblur = self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get())
                                        cmd += f' --secondary-restoration rtx-super-res --rtx-quality {rtx_quality} --rtx-denoise {rtx_denoise} --rtx-deblur {rtx_deblur} --rtx-scale {rtx_scale}'

                                    # 添加VR模式参数
                                    vr_mode = self.vr_mode_var.get()
                                    if vr_mode == "自动":
                                        cmd += ' --vr-mode auto'
                                    elif vr_mode == "SBS":
                                        cmd += ' --vr-mode sbs'
                                    elif vr_mode == "鱼眼":
                                        cmd += ' --vr-mode sbs-fisheye'

                                    self.logger.info(f"开始处理转码后的视频: {transcoded_video_name}")
                                    self.logger.info(f"完整命令: {cmd}")
                                    self.logger.info(f"工作目录: {jasna_dir}")
                                    self.logger.info(f"当前切片帧数: {current_slice_frames}, 是否首次使用: {is_first_time_for_model_compile}")
                                    
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
                                        args=(process, transcoded_video_name)
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
                                        self.logger.warning(f"检测到视频卡死，已终止处理: {transcoded_video_name}")
                                        
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
                                        
                                        # 执行卡死处理流程（已转码重试，标记is_retry=True）
                                        self.handle_stuck_video(transcoded_video_name, transcoded_input_path, transcoded_video_name_only, suffix, output_folder, is_retry=True)
                                        
                                        # 重置当前处理视频
                                        self.currently_processing = None
                                        self.current_video_var.set("无")
                                        self.processing_mode_var.set("破解")  # 重置为默认破解模式
                                        
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
                                        success = self.check_final_file_exists(transcoded_video_name_only, suffix, output_folder)
                                        
                                        if success:
                                            # 计算处理速度 - 与直接处理成功的计算方式一致
                                            # 使用总帧数除以处理时间来计算速度
                                            processing_end_time = time.time()
                                            processing_duration = processing_end_time - processing_start_time  # 处理该视频的总运行时间（秒）
                                            total_frames = self.estimate_total_frames(transcoded_input_path)
                                            if total_frames > 0 and processing_duration > 0:
                                                processing_speed = total_frames / processing_duration
                                                processing_speed_str = f"{int(processing_speed)}fps"
                                            else:
                                                processing_speed_str = "未知"
                                            
                                            # 将转码后的视频从未处理列表移到已处理列表
                                            # 先找到要移除的项
                                            item_to_remove = None
                                            for item in self.video_lists["unprocessed"]:
                                                if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                                   (isinstance(item, str) and item == transcoded_video_name):
                                                    item_to_remove = item
                                                    break
                                            
                                            if item_to_remove is not None:
                                                self.video_lists["unprocessed"].remove(item_to_remove)
                                                # 保持相同的数据结构格式，但为已处理视频添加处理速度信息
                                                # 创建已处理视频的信息（包含处理速度）
                                                if isinstance(item_to_remove, dict):
                                                    processed_video_info = {
                                                        'name': item_to_remove['name'],
                                                        'processing_speed': processing_speed_str
                                                    }
                                                else:
                                                    processed_video_info = {
                                                        'name': transcoded_video_name,
                                                        'processing_speed': processing_speed_str
                                                    }
                                                
                                                self.video_lists["processed"].append(processed_video_info)
                                            
                                            # 处理成功后移动源视频到成功文件夹（新增）
                                            success_folder = self.success_folder_var.get()
                                            if success_folder:
                                                success_moved = self.move_to_success_folder(transcoded_input_path, transcoded_video_name)
                                                if success_moved:
                                                    self.logger.info(f"成功视频已移动到成功文件夹: {transcoded_video_name}")
                                                else:
                                                    self.logger.warning(f"成功视频移动失败: {transcoded_video_name}")
                                            
                                            # 从错误列表中移除原始视频并添加到已处理列表
                                            # 先找到要移除的原始视频项
                                            original_item_to_remove = None
                                            for item in self.video_lists["error"]:
                                                if (isinstance(item, dict) and item['name'] == video_file) or \
                                                   (isinstance(item, str) and item == video_file):
                                                    original_item_to_remove = item
                                                    break
                                            
                                            if original_item_to_remove is not None:
                                                self.video_lists["error"].remove(original_item_to_remove)
                                                # 创建已处理视频的信息（包含处理速度）
                                                if isinstance(original_item_to_remove, dict):
                                                    processed_original_video_info = {
                                                        'name': original_item_to_remove['name'],
                                                        'processing_speed': processing_speed_str
                                                    }
                                                else:
                                                    processed_original_video_info = {
                                                        'name': video_file,
                                                        'processing_speed': processing_speed_str
                                                    }
                                                self.video_lists["processed"].append(processed_original_video_info)
                                                
                                                # 将原始视频从错误文件夹移动到成功文件夹
                                                if success_folder:
                                                    original_error_video_path = os.path.join(error_folder, video_file)
                                                    if os.path.exists(original_error_video_path):
                                                        # 构建成功文件夹中的目标路径
                                                        success_original_video_path = os.path.join(success_folder, video_file)
                                                        try:
                                                            # 移动文件
                                                            shutil.move(original_error_video_path, success_original_video_path)
                                                            self.logger.info(f"原始错误视频已移动到成功文件夹: {video_file}")
                                                        except Exception as e:
                                                            self.logger.error(f"移动原始错误视频时出错: {str(e)}")
                                            
                                            # 如果是首次使用且处理成功，将切片帧数和检测模型添加到历史记录
                                            if is_first_time_for_model_compile:
                                                current_detection_model = self.detection_model_var.get()
                                                # 检查切片帧数是否已存在于历史记录中，避免重复添加
                                                if current_slice_frames not in self.slice_frames_history:
                                                    self.slice_frames_history.append(current_slice_frames)
                                                    self.logger.info(f"将切片帧数 {current_slice_frames} 添加到历史记录")
                                                # 检查检测模型是否已存在于历史记录中，避免重复添加
                                                if current_detection_model not in self.detection_model_history:
                                                    self.detection_model_history.append(current_detection_model)
                                                    self.logger.info(f"将检测模型 {current_detection_model} 添加到历史记录")
                                                    
                                                # 立即恢复原始的stuck_seconds值，避免后续视频处理受到影响
                                                if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                                    self.stuck_seconds_var.set(self.original_stuck_seconds)
                                                    self.stuck_seconds_modified = False
                                                    self.logger.info(f"首次运行完成 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                                
                                                # 立即保存配置文件，确保历史记录被保存
                                                self.save_settings()
                                                self.logger.info("编译模式处理成功，已保存配置文件")
                                            
                                            # 更新GUI
                                            self.root.after(0, self.update_lists_display)
                                            self.root.after(0, self.update_summary)
                                            
                                            self.logger.info(f"转码后视频处理完成: {transcoded_video_name}")
                                            self.root.after(0, lambda: self.status_var.set(f"转码后视频处理完成: {transcoded_video_name}"))
                                        else:
                                            # 最终文件不存在，视为处理失败
                                            self.logger.error(f"转码后视频处理完成但最终文件不存在: {transcoded_video_name}")
                                            
                                            # 将视频从未处理列表移到错误列表
                                            # 先找到要移除的项
                                            item_to_remove = None
                                            for item in self.video_lists["unprocessed"]:
                                                if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                                   (isinstance(item, str) and item == transcoded_video_name):
                                                    item_to_remove = item
                                                    break
                                            
                                            if item_to_remove is not None:
                                                self.video_lists["unprocessed"].remove(item_to_remove)
                                                # 保持相同的数据结构格式
                                                if isinstance(item_to_remove, dict):
                                                    self.video_lists["error"].append(item_to_remove)
                                                else:
                                                    self.video_lists["error"].append(transcoded_video_name)
                                            
                                            # 删除转码后的视频文件
                                            if os.path.exists(transcoded_input_path):
                                                try:
                                                    os.remove(transcoded_input_path)
                                                    self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                                except Exception as e:
                                                    self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                            
                                            # 更新GUI
                                            self.root.after(0, self.update_lists_display)
                                            self.root.after(0, self.update_summary)
                                            
                                            self.logger.error(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}")
                                            self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}"))
                                    else:
                                        # 处理失败或被停止
                                        if self.stop_processing:
                                            self.logger.info(f"转码后视频处理被用户停止: {transcoded_video_name}")
                                            
                                            # 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
                                            self.root.after(2000, lambda: self.cleanup_temp_files_after_stop(transcoded_video_name_only, suffix, output_folder, delete_final_file=True))
                                            
                                            # 如果用户停止，不清空列表，视频保留在未处理列表中
                                            self.root.after(0, lambda: self.status_var.set(f"转码后视频处理被停止: {transcoded_video_name}"))
                                            break  # 跳出循环，不再处理后续视频
                                        else:
                                            self.logger.error(f"JASNA返回错误代码: {return_code}")
                                            
                                            # 清理可能生成的临时文件（包括最终文件）
                                            self.cleanup_temp_files(transcoded_video_name_only, suffix, output_folder, delete_final_file=True)
                                            
                                            # 将视频从未处理列表移到错误列表
                                            # 先找到要移除的项
                                            item_to_remove = None
                                            for item in self.video_lists["unprocessed"]:
                                                if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                                   (isinstance(item, str) and item == transcoded_video_name):
                                                    item_to_remove = item
                                                    break
                                            
                                            if item_to_remove is not None:
                                                self.video_lists["unprocessed"].remove(item_to_remove)
                                                # 保持相同的数据结构格式
                                                if isinstance(item_to_remove, dict):
                                                    self.video_lists["error"].append(item_to_remove)
                                                else:
                                                    self.video_lists["error"].append(transcoded_video_name)
                                            
                                            # 删除转码后的视频文件
                                            if os.path.exists(transcoded_input_path):
                                                try:
                                                    os.remove(transcoded_input_path)
                                                    self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                                except Exception as e:
                                                    self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                            
                                            # 更新GUI
                                            self.root.after(0, self.update_lists_display)
                                            self.root.after(0, self.update_summary)
                                            
                                            self.logger.error(f"转码后视频处理失败: {transcoded_video_name}")
                                            self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败: {transcoded_video_name}"))
                                else:
                                    self.logger.error(f"转码失败: {video_file}")
                
                # 重置当前处理视频
                self.currently_processing = None
                self.current_video_var.set("无")
                
                # 清空日志文件
                self.clear_log_file()
                
                # 重置进度条
                self.root.after(0, self.reset_progress_display)
            
            # 检查是否还有未处理或错误的视频
            if len(self.video_lists["unprocessed"]) == 0 and len(self.video_lists["error"]) == 0:
                self.root.after(0, lambda: self.status_var.set("所有视频处理完成！"))
                self.logger.info("所有视频处理完成！")
                
                # 保存切片帧数历史记录到配置文件
                self.root.after(0, self.save_settings)
                
                # 根据用户选择执行相应操作
                self.root.after(0, self.execute_post_processing_action)
            else:
                # 如果仍有视频未处理，等待用户操作
                self.root.after(0, lambda: self.status_var.set("处理完成，仍有视频未处理"))
            
            # 只有在不是用户停止的情况下，才强制终止所有jasna进程（进程名由用户配置决定）
            if not self.stop_processing:
                # 处理完成后强制终止所有jasna进程
                self.logger.info(f"处理完成，强制终止所有{self.get_jasna_exe_name()}进程")
                self.kill_all_jasna_processes()
            
            # 在所有处理完成后清空日志文件
            self.clear_log_file()
            
            # 隐藏处理状态指示器
            self.root.after(0, self.hide_processing_mode_indicator)
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"处理视频时出错: {error_message}", exc_info=True)
            self.root.after(0, lambda msg=error_message: self.show_custom_messagebox("error", "错误", f"处理视频时出错: {msg}"))
        finally:
            # 确保卡死监测线程停止
            self.stop_stuck_monitor()
            
            # 如果stuck_seconds值被修改过，恢复原始值
            if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                self.stuck_seconds_var.set(self.original_stuck_seconds)
                self.logger.info(f"恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
            
            # 异常情况下也强制终止所有jasna进程（进程名由用户配置决定）
            try:
                self.logger.info(f"异常情况，强制终止所有{self.get_jasna_exe_name()}进程")
                self.kill_all_jasna_processes()
            except Exception as e:
                self.logger.error(f"异常情况下终止{self.get_jasna_exe_name()}进程时出错: {str(e)}")
            
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
    
    def handle_stuck_video(self, video_file, input_path, video_name, suffix, output_folder, is_retry=False):
        """处理卡死的视频
        
        参数:
            is_retry: 是否是转码后的重试调用。如果为True，转码后的视频再次卡死时不再递归，直接标记失败。
        """
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
                    return  # 移动失败，无法继续转码
            else:
                self.logger.info(f"未设置出错文件夹，卡死视频保持在原位置: {video_file}")
                self.root.after(0, lambda: self.status_var.set(f"视频卡死，未设置出错文件夹，视频保持在原位置: {video_file}"))
                return  # 未设置出错文件夹，无法继续转码
            
            # 5. 立即对卡死视频执行转码并再次处理
            # 这部分逻辑与正常出错时的处理流程一致
            if error_folder and os.path.exists(error_folder):
                error_video_path = os.path.join(error_folder, video_file)
                if os.path.exists(error_video_path):
                    # 检查是否用户请求停止处理
                    if self.stop_processing:
                        self.logger.info("用户请求停止转码")
                        return
                    
                    self.logger.info(f"开始转码卡死视频: {video_file}")
                    
                    # 设置转码状态
                    self.root.after(0, lambda vm=video_file: self.current_video_var.set(vm))
                    self.root.after(0, lambda: self.processing_mode_var.set("转码"))
                    
                    # 执行转码
                    transcoded_video_name = f"{Path(video_file).stem}-转码{Path(video_file).suffix}"
                    transcoded_video_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                    
                    transcode_success = self.transcode_video(error_video_path, transcoded_video_path)
                    
                    if transcode_success:
                        # 转码成功，立即对转码后的视频再次执行处理操作
                        self.logger.info(f"转码成功，开始再次处理转码后的视频: {transcoded_video_name}")
                        
                        # 重置卡死标志
                        self.is_stuck = False
                        self.stuck_detected = False
                        
                        # 重置处理错误标志
                        self.processing_error = False
                        
                        self.currently_processing = transcoded_video_name
                        self.current_video_var.set(transcoded_video_name)
                        self.processing_mode_var.set("破解")  # 设置为破解模式
                        
                        # 重置进度信息显示
                        self.root.after(0, self.reset_progress_display)
                        
                        # 构建输入路径
                        transcoded_input_path = os.path.join(self.input_folder_var.get(), transcoded_video_name)
                        
                        self.logger.info(f"构建的转码后视频输入路径: {transcoded_input_path}")
                        self.logger.info(f"输入文件夹: {self.input_folder_var.get()}")
                        self.logger.info(f"转码后视频文件: {transcoded_video_name}")
                        self.logger.info(f"输入路径是否存在: {os.path.exists(transcoded_input_path)}")
                        
                        # 获取视频信息
                        self.logger.info("开始调用get_video_info函数")
                        success = self.get_video_info(transcoded_input_path)
                        self.logger.info(f"get_video_info函数返回值: {success}")
                        
                        # 记录视频处理开始时间，用于计算处理速度
                        processing_start_time = time.time()
                        
                        # 获取视频信息并检测分辨率
                        video_width = self.get_video_info(transcoded_input_path)
                        is_4k_video = video_width >= 3840
                        
                        # 记录视频信息显示状态（无论成功与否都继续处理）
                        self.root.after(0, lambda: self.logger.info(f"视频信息显示状态 - 分辨率: {self.video_resolution_var.get()}, 帧率: {self.video_fps_var.get()}, 时长: {self.video_duration_var.get()}"))
                        
                        # 根据分辨率选择切片帧数参数
                        if is_4k_video:
                            current_slice_frames = int(self.slice_frames_var2.get())
                            self.logger.info(f"视频分辨率为4K及以上，使用第二个输入框的切片帧数: {current_slice_frames}")
                        else:
                            current_slice_frames = int(self.slice_frames_var1.get())
                            self.logger.info(f"视频分辨率低于4K，使用第一个输入框的切片帧数: {current_slice_frames}")
                        
                        # 检查当前切片帧数是否已存在于历史记录中
                        is_slice_frames_first_time = current_slice_frames not in self.slice_frames_history
                        
                        # 检查当前检测模型是否已存在于历史记录中
                        current_detection_model = self.detection_model_var.get()
                        is_detection_model_first_time = current_detection_model not in self.detection_model_history
                        
                        # 判断是否需要首次编译
                        is_first_time_for_model_compile = False  # 标记是否是模型编译的首次运行
                        if is_slice_frames_first_time or is_detection_model_first_time:
                            # 弹窗提示用户
                            self.root.after(0, lambda: self.show_custom_messagebox("info", "提示", "当前切片帧数或检测模型为首次使用\n需要编译模型 \n\n所需时间为0.2小时到4小时之间"))
                            # 临时将卡死超时时间设置为15000秒
                            self.stuck_seconds_var.set("15000")
                            self.stuck_seconds_modified = True  # 标记stuck_seconds值已被修改
                            is_first_time_for_model_compile = True  # 标记本次处理是首次模型编译
                        
                        # 记录检查结果
                        self.logger.info(f"双重检查结果 - 切片帧数首次使用: {is_slice_frames_first_time}, 检测模型首次使用: {is_detection_model_first_time}")
                        
                        # 构建输出文件名（添加后缀和.mp4扩展名）
                        transcoded_video_name_only = Path(transcoded_video_name).stem
                        suffix = self.output_suffix_var.get()
                        final_output_filename = f"{transcoded_video_name_only}{suffix}.mp4"
                        final_output_path = os.path.join(output_folder, final_output_filename)
                        
                        # 启动卡死监测线程（根据是否首次使用设置不同的阈值）
                        if is_first_time_for_model_compile:
                            self.start_stuck_monitor(custom_stuck_seconds=15000)
                        else:
                            self.start_stuck_monitor()
                        
                        # 构建命令字符串
                        encode_params = f'"{self.encode_params_var.get()}"'
                        
                        # 构建基础命令，使用根据分辨率选择的切片帧数
                        # 获取JASNA程序地址，与第一次处理视频时的方式一致
                        jasna_path = self.jasna_path_var.get()
                        jasna_dir = os.path.dirname(jasna_path)
                        jasna_exe_name = os.path.basename(jasna_path)
                        cmd = f'.\\{jasna_exe_name} --input "{transcoded_input_path}" --output "{final_output_path}" --max-clip-size {current_slice_frames} --codec hevc --encoder-settings {encode_params} --log-level info --detection-model {self.detection_model_var.get()} --detection-score-threshold {self.detection_threshold_var.get()}'
                        
                        # 确保JASNA目录存在
                        if not os.path.exists(jasna_dir):
                            self.logger.error(f"JASNA目录不存在: {jasna_dir}")
                            return
                        
                        # 根据二次修复模块中"使用软件"组件的选择，添加相应参数
                        secondary_fix_option = self.secondary_fix_var.get()
                        if secondary_fix_option == "TVAI":
                            # 添加TVAI相关参数
                            ffmpeg_path = self.ffmpeg_path_var.get()
                            model_name = self.tvai_model_var.get()
                            scale = self.tvai_scale_var.get()
                            threads = self.tvai_threads_var.get()
                            tvai_params = self.tvai_params_var.get()
                            
                            # 处理TVAI缩放参数的特殊转换规则
                            if scale == "1":
                                tvai_scale = "0"
                            else:
                                tvai_scale = scale
                            
                            cmd += f' --secondary-restoration tvai --tvai-ffmpeg-path "{ffmpeg_path}" --tvai-model {model_name} --tvai-scale {tvai_scale} --tvai-workers {threads} --tvai-args "{tvai_params}"'
                        elif secondary_fix_option == "RTX-SR":
                            # 添加RTX-SR相关参数
                            rtx_scale = self.rtx_sr_scale_var.get().replace("X", "")  # 2X->2, 4X->4
                            rtx_quality = self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get())
                            rtx_denoise = self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get())
                            rtx_deblur = self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get())
                            cmd += f' --secondary-restoration rtx-super-res --rtx-quality {rtx_quality} --rtx-denoise {rtx_denoise} --rtx-deblur {rtx_deblur} --rtx-scale {rtx_scale}'

                        # 添加VR模式参数
                        vr_mode = self.vr_mode_var.get()
                        if vr_mode == "自动":
                            cmd += ' --vr-mode auto'
                        elif vr_mode == "SBS":
                            cmd += ' --vr-mode sbs'
                        elif vr_mode == "鱼眼":
                            cmd += ' --vr-mode sbs-fisheye'

                        self.logger.info(f"开始处理转码后的视频: {transcoded_video_name}")
                        self.logger.info(f"完整命令: {cmd}")
                        self.logger.info(f"工作目录: {jasna_dir}")
                        self.logger.info(f"当前切片帧数: {current_slice_frames}, 是否首次使用: {is_first_time_for_model_compile}")
                        
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
                            args=(process, transcoded_video_name)
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
                            self.logger.warning(f"检测到转码后视频卡死，已终止处理: {transcoded_video_name}")
                            
                            # 如果是首次使用当前切片帧数且发生卡死（模型编译失败），弹窗提示错误
                            if is_first_time_for_model_compile:
                                self.root.after(0, lambda: self.show_custom_messagebox("error", "错误", "模型编译失败，请检查系统设置、内存大小、显存大小，可适当调低切片帧数后重新运行"))
                                
                                # 立即恢复原始的stuck_seconds值，因为模型编译失败，不需要将切片帧数添加到历史记录
                                if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                    self.stuck_seconds_var.set(self.original_stuck_seconds)
                                    self.stuck_seconds_modified = False
                                    self.logger.info(f"模型编译失败 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                
                                # 不将当前切片帧数添加到历史记录，直接跳出
                                return
                            
                            # 执行卡死处理流程
                            if is_retry:
                                # 已经是转码重试后的再次卡死，不再递归，直接标记为处理失败
                                self.logger.error(f"转码后视频再次卡死，不再重试: {transcoded_video_name}")
                                self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败: {transcoded_video_name}"))
                            else:
                                self.handle_stuck_video(transcoded_video_name, transcoded_input_path, transcoded_video_name_only, suffix, output_folder, is_retry=True)
                            
                            # 重置当前处理视频
                            self.currently_processing = None
                            self.current_video_var.set("无")
                            self.processing_mode_var.set("破解")  # 重置为默认破解模式
                            
                            # 重置进度条
                            self.root.after(0, self.reset_progress_display)
                            
                            # 清空日志文件
                            self.clear_log_file()
                            
                            return
                        
                        # 检查进程是否成功完成
                        if return_code == 0 and not self.stop_processing:
                            # 处理成功
                            # 检查最终文件是否存在
                            success = self.check_final_file_exists(transcoded_video_name_only, suffix, output_folder)
                            
                            if success:
                                # 初始化处理速度变量
                                processing_speed_str = "未知"
                                
                                # 计算处理速度 - 与直接处理成功的计算方式一致
                                processing_end_time = time.time()
                                processing_duration = processing_end_time - processing_start_time  # 处理该视频的总运行时间（秒）
                                
                                # 使用总帧数除以处理时间来计算速度
                                total_frames = self.estimate_total_frames(transcoded_input_path)
                                if total_frames > 0 and processing_duration > 0:
                                    processing_speed = total_frames / processing_duration
                                    processing_speed_str = f"{int(processing_speed)}fps"
                                else:
                                    processing_speed_str = "未知"
                                
                                # 将转码后的视频从未处理列表移到已处理列表
                                # 先找到要移除的项
                                item_to_remove = None
                                for item in self.video_lists["unprocessed"]:
                                    if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                       (isinstance(item, str) and item == transcoded_video_name):
                                        item_to_remove = item
                                        break
                                
                                if item_to_remove is not None:
                                    self.video_lists["unprocessed"].remove(item_to_remove)
                                    # 保持相同的数据结构格式，但为已处理视频添加处理速度信息
                                    if isinstance(item_to_remove, dict):
                                        processed_video_info = {
                                            'name': item_to_remove['name'],
                                            'processing_speed': processing_speed_str
                                        }
                                    else:
                                        processed_video_info = {
                                            'name': transcoded_video_name,
                                            'processing_speed': processing_speed_str
                                        }
                                    
                                    self.video_lists["processed"].append(processed_video_info)
                                
                                # 从错误列表中移除原始视频并添加到已处理列表
                                # 先找到要移除的原始视频项
                                original_item_to_remove = None
                                for item in self.video_lists["error"]:
                                    if (isinstance(item, dict) and item['name'] == video_file) or \
                                       (isinstance(item, str) and item == video_file):
                                        original_item_to_remove = item
                                        break
                                
                                if original_item_to_remove is not None:
                                    self.video_lists["error"].remove(original_item_to_remove)
                                    # 创建已处理视频的信息（包含处理速度）
                                    if isinstance(original_item_to_remove, dict):
                                        processed_original_video_info = {
                                            'name': original_item_to_remove['name'],
                                            'processing_speed': processing_speed_str
                                        }
                                    else:
                                        processed_original_video_info = {
                                            'name': video_file,
                                            'processing_speed': processing_speed_str
                                        }
                                    self.video_lists["processed"].append(processed_original_video_info)
                                    
                                    # 将原始视频从错误文件夹移动到成功文件夹
                                    success_folder = self.success_folder_var.get()
                                    if success_folder:
                                        original_error_video_path = os.path.join(error_folder, video_file)
                                        if os.path.exists(original_error_video_path):
                                            # 构建成功文件夹中的目标路径
                                            success_original_video_path = os.path.join(success_folder, video_file)
                                            try:
                                                # 移动文件
                                                shutil.move(original_error_video_path, success_original_video_path)
                                                self.logger.info(f"原始错误视频已移动到成功文件夹: {video_file}")
                                            except Exception as e:
                                                self.logger.error(f"移动原始错误视频时出错: {str(e)}")
                                
                                # 处理成功后移动转码后的视频到成功文件夹
                                success_folder = self.success_folder_var.get()
                                if success_folder:
                                    success_moved = self.move_to_success_folder(transcoded_input_path, transcoded_video_name)
                                    if success_moved:
                                        self.logger.info(f"成功视频已移动到成功文件夹: {transcoded_video_name}")
                                    else:
                                        self.logger.warning(f"成功视频移动失败: {transcoded_video_name}")
                                
                                # 更新GUI
                                self.root.after(0, self.update_lists_display)
                                self.root.after(0, self.update_summary)
                                
                                # 如果是首次使用且处理成功，将切片帧数和检测模型添加到历史记录
                                if is_first_time_for_model_compile:
                                    current_detection_model = self.detection_model_var.get()
                                    # 检查切片帧数是否已存在于历史记录中，避免重复添加
                                    if current_slice_frames not in self.slice_frames_history:
                                        self.slice_frames_history.append(current_slice_frames)
                                        self.logger.info(f"将切片帧数 {current_slice_frames} 添加到历史记录")
                                    # 检查检测模型是否已存在于历史记录中，避免重复添加
                                    if current_detection_model not in self.detection_model_history:
                                        self.detection_model_history.append(current_detection_model)
                                        self.logger.info(f"将检测模型 {current_detection_model} 添加到历史记录")
                                    
                                    # 立即恢复原始的stuck_seconds值，避免后续视频处理受到影响
                                    if self.stuck_seconds_modified and self.original_stuck_seconds is not None:
                                        self.stuck_seconds_var.set(self.original_stuck_seconds)
                                        self.stuck_seconds_modified = False
                                        self.logger.info(f"首次运行完成 - 恢复卡死超时时间至原始值: {self.original_stuck_seconds}")
                                    
                                    # 立即保存配置文件，确保历史记录被保存
                                    self.save_settings()
                                    self.logger.info("编译模式处理成功，已保存配置文件")
                                
                                self.logger.info(f"转码后视频处理完成: {transcoded_video_name}")
                                self.root.after(0, lambda: self.status_var.set(f"转码后视频处理完成: {transcoded_video_name}"))
                            else:
                                # 最终文件不存在，视为处理失败
                                self.logger.error(f"转码后视频处理完成但最终文件不存在: {transcoded_video_name}")
                                
                                # 将视频从未处理列表移到错误列表
                                # 先找到要移除的项
                                item_to_remove = None
                                for item in self.video_lists["unprocessed"]:
                                    if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                       (isinstance(item, str) and item == transcoded_video_name):
                                        item_to_remove = item
                                        break
                                
                                if item_to_remove is not None:
                                    self.video_lists["unprocessed"].remove(item_to_remove)
                                    # 保持相同的数据结构格式
                                    if isinstance(item_to_remove, dict):
                                        self.video_lists["error"].append(item_to_remove)
                                    else:
                                        self.video_lists["error"].append(transcoded_video_name)
                                
                                # 删除转码后的视频文件
                                if os.path.exists(transcoded_input_path):
                                    try:
                                        os.remove(transcoded_input_path)
                                        self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                    except Exception as e:
                                        self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                
                                # 更新GUI
                                self.root.after(0, self.update_lists_display)
                                self.root.after(0, self.update_summary)
                                
                                self.logger.error(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}")
                                self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败，最终文件未生成: {transcoded_video_name}"))
                        else:
                            # 处理失败或被停止
                            if self.stop_processing:
                                self.logger.info(f"转码后视频处理被用户停止: {transcoded_video_name}")
                                
                                # 延迟2秒后删除输出文件夹中所有该视频的临时文件（包括最终文件）
                                self.root.after(2000, lambda: self.cleanup_temp_files_after_stop(transcoded_video_name_only, suffix, output_folder, delete_final_file=True))
                                
                                # 如果用户停止，不清空列表，视频保留在未处理列表中
                                self.root.after(0, lambda: self.status_var.set(f"转码后视频处理被停止: {transcoded_video_name}"))
                            else:
                                self.logger.error(f"JASNA返回错误代码: {return_code}")
                                
                                # 清理可能生成的临时文件（包括最终文件）
                                self.cleanup_temp_files(transcoded_video_name_only, suffix, output_folder, delete_final_file=True)
                                
                                # 将视频从未处理列表移到错误列表
                                # 先找到要移除的项
                                item_to_remove = None
                                for item in self.video_lists["unprocessed"]:
                                    if (isinstance(item, dict) and item['name'] == transcoded_video_name) or \
                                       (isinstance(item, str) and item == transcoded_video_name):
                                        item_to_remove = item
                                        break
                                
                                if item_to_remove is not None:
                                    self.video_lists["unprocessed"].remove(item_to_remove)
                                    # 保持相同的数据结构格式
                                    if isinstance(item_to_remove, dict):
                                        self.video_lists["error"].append(item_to_remove)
                                    else:
                                        self.video_lists["error"].append(transcoded_video_name)
                                
                                # 删除转码后的视频文件
                                if os.path.exists(transcoded_input_path):
                                    try:
                                        os.remove(transcoded_input_path)
                                        self.logger.info(f"已删除转码后的视频文件: {transcoded_video_name}")
                                    except Exception as e:
                                        self.logger.error(f"删除转码后视频文件时出错: {str(e)}")
                                
                                # 更新GUI
                                self.root.after(0, self.update_lists_display)
                                self.root.after(0, self.update_summary)
                                
                                self.logger.error(f"转码后视频处理失败: {transcoded_video_name}")
                                self.root.after(0, lambda: self.status_var.set(f"转码后视频处理失败: {transcoded_video_name}"))
                    else:
                        self.logger.error(f"转码失败: {video_file}")
            
            self.logger.info(f"卡死视频处理完成: {video_file}")
            
        except Exception as e:
            self.logger.error(f"处理卡死视频时出错: {str(e)}")
    
    def get_jasna_exe_name(self):
        """从JASNA程序地址中提取程序名字"""
        jasna_path = self.jasna_path_var.get()
        if not jasna_path:
            return "jasna-cli.exe"  # 默认值
        
        # 提取程序名字
        import os
        return os.path.basename(jasna_path)
    
    def kill_all_jasna_processes(self, jasna_exe_name=None):
        """强制终止所有指定名称的进程"""
        # 如果没有提供jasna_exe_name，从JASNA程序地址中提取
        if jasna_exe_name is None:
            jasna_exe_name = self.get_jasna_exe_name()
        
        try:
            self.logger.info(f"开始强制终止所有{jasna_exe_name}进程...")
            
            if sys.platform == "win32":
                # 方法1: 使用taskkill终止进程树
                subprocess.run(f"taskkill /F /T /IM {jasna_exe_name}", 
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.logger.info(f"已使用taskkill /F /T /IM {jasna_exe_name}命令")
                
                
                # 最后再检查一次，确保进程已终止
                time.sleep(1)
                check_result = subprocess.run(f"tasklist /FI \"IMAGENAME eq {jasna_exe_name}\"", 
                                            shell=True, capture_output=True, text=True)
                if jasna_exe_name not in check_result.stdout:
                    self.logger.info(f"确认所有{jasna_exe_name}进程已被终止")
                else:
                    self.logger.warning(f"仍有{jasna_exe_name}进程在运行，尝试其他方法...")
                    
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
            self.logger.error(f"终止{jasna_exe_name}进程时出错: {str(e)}")
    
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
                            # 使用多种方法强制终止所有jasna进程（进程名由用户配置决定）
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
    
    def _on_processing_mode_change(self, *args):
        """处理模式变化时更新状态指示器颜色"""
        current_mode = self.processing_mode_var.get()
        if current_mode == "转码":
            # 设置为橙色背景
            self.processing_mode_label.config(bg="#FFA500")  # 标准橙色
        else:
            # 恢复原始绿色背景
            self.processing_mode_label.config(bg="#4CAF50")  # 原始绿色
    
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
                    line_stripped = line.strip()
                    self.progress_output_lines.append(line_stripped)
                    
                    # 将jasna-cli.exe的输出写入日志文件
                    self.logger.info(f"jasna-cli: {line_stripped}")
                    
                    # 尝试解析进度信息
                    progress_info = self.parse_jasna_progress(line)
                    if progress_info:
                        # 更新进度显示
                        self.root.after(0, lambda p=progress_info: self.update_detailed_progress(p))
                    
                    # 记录日志（保持原有逻辑，用于错误和警告的特殊处理）
                    if "error" in line.lower() or "failed" in line.lower():
                        self.logger.error(f"JASNA输出 - {video_file}: {line_stripped}")
                        self.processing_error = True
                    elif "warning" in line.lower():
                        self.logger.warning(f"JASNA输出 - {video_file}: {line_stripped}")
                    else:
                        # 记录进度信息行（保持原有逻辑）
                        if 'Processing video:' in line:
                            self.logger.info(f"JASNA输出 - {video_file}: {line_stripped}")
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
            from pymediainfo import MediaInfo
            import os
            from pathlib import Path
            import time
            import sys
            
            # 使用pathlib处理路径，更好地处理中文字符
            video_path_obj = Path(video_path)
            video_path_str = str(video_path_obj.resolve())  # 获取绝对路径
            
            # 检查视频文件是否存在
            if not video_path_obj.exists():
                self.logger.error(f"视频文件不存在: {video_path_str}")
                return False
            
            self.logger.info(f"开始获取视频信息: {video_path_str}")
            
            # 使用pymediainfo获取视频信息
            media_info = MediaInfo.parse(str(video_path_obj))
            
            # 查找视频轨道
            width, height = 0, 0
            fps = 0
            duration = 0
            
            for track in media_info.tracks:
                if track.track_type == 'Video':
                    # 获取分辨率
                    if hasattr(track, 'width') and track.width:
                        width = int(track.width)
                        self.logger.info(f"视频宽度: {width}")
                    if hasattr(track, 'height') and track.height:
                        height = int(track.height)
                        self.logger.info(f"视频高度: {height}")
                    
                    # 获取帧率
                    if hasattr(track, 'avg_frame_rate') and track.avg_frame_rate:
                        try:
                            # avg_frame_rate 可能是分数形式如 "25000/1000"
                            if '/' in str(track.avg_frame_rate):
                                num, den = map(int, str(track.avg_frame_rate).split('/'))
                                if den != 0:
                                    fps = round(num / den, 2)
                                else:
                                    fps = 0
                            else:
                                fps = float(track.avg_frame_rate)
                        except (ValueError, TypeError):
                            fps = 0
                    elif hasattr(track, 'frame_rate') and track.frame_rate:
                        try:
                            fps = float(track.frame_rate)
                        except (ValueError, TypeError):
                            fps = 0
                    
                    # 获取时长
                    if hasattr(track, 'duration') and track.duration:
                        try:
                            duration = float(track.duration) / 1000  # 转换为秒
                        except (ValueError, TypeError):
                            duration = 0
                    elif hasattr(track, 'other_duration') and track.other_duration:
                        try:
                            # 尝试从其他格式获取时长
                            duration_str = track.other_duration[0]  # 格式如 "1mn 23s"
                            duration = self.parse_duration_string(duration_str)
                        except:
                            duration = 0
                    break
            
            # 设置GUI变量
            resolution = f"{width}×{height}" if width and height else "未知"
            fps_str = f"{fps}" if fps else "未知"
            duration_str = self.format_seconds_to_hms(duration) if duration > 0 else "未知"
            
            self.video_resolution_var.set(resolution)
            self.video_fps_var.set(fps_str)
            self.video_duration_var.set(duration_str)
            
            self.logger.info(f"成功获取视频信息 - 分辨率: {resolution}, 帧率: {fps_str}, 时长: {duration_str}")
            return width
            
        except ImportError:
            self.logger.error("pymediainfo库未安装")
            return 0
        except Exception as e:
            self.logger.error(f"使用pymediainfo获取视频信息时出错: {str(e)}", exc_info=True)
            return 0
        
    def estimate_total_frames(self, video_path):
        """估算视频总帧数"""
        try:
            # 获取视频信息
            self.get_video_info(video_path)
            
            # 从GUI变量获取时长和帧率
            duration_str = self.video_duration_var.get()
            fps_str = self.video_fps_var.get()
            
            if duration_str != "未知" and fps_str != "未知":
                # 解析时长（格式如 01:56:47）
                duration_parts = duration_str.split(':')
                if len(duration_parts) == 3:  # HH:MM:SS
                    hours = int(duration_parts[0])
                    minutes = int(duration_parts[1])
                    seconds = int(duration_parts[2])
                    total_seconds = hours * 3600 + minutes * 60 + seconds
                elif len(duration_parts) == 2:  # MM:SS
                    minutes = int(duration_parts[0])
                    seconds = int(duration_parts[1])
                    total_seconds = minutes * 60 + seconds
                else:
                    total_seconds = 0
                
                # 解析帧率
                fps = float(fps_str)
                
                # 计算总帧数
                total_frames = int(total_seconds * fps)
                return total_frames
            else:
                self.logger.warning(f"无法估算视频总帧数: {video_path}，时长={duration_str}, 帧率={fps_str}")
                return 0
                
        except Exception as e:
            self.logger.error(f"估算视频总帧数时出错: {str(e)}")
            return 0

    def format_time(self, seconds):
        """格式化时间（秒）为HH:MM:SS格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def test_ffmpeg_output(self, input_path, output_path):
        """测试FFmpeg输出格式"""
        try:
            # 使用预设的转码参数进行测试
            transcode_params = '-hwaccel cuda -hwaccel_output_format cuda -c:v hevc_nvenc -preset p5 -tune hq -rc constqp -qp 15 -qp_cb_offset -2 -qp_cr_offset -2 -spatial_aq 1 -aq-strength 1 -c:a aac -b:a 128k'
            
            # 确保输出格式为MP4
            if not output_path.lower().endswith('.mp4'):
                output_path += '.mp4'
            
            cmd = ['ffmpeg', '-i', input_path] + transcode_params.split() + ['-y', output_path]
            
            self.logger.info(f"测试FFmpeg命令: {' '.join(cmd)}")
            
            # 执行命令并捕获输出
            result = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 将stderr重定向到stdout
                universal_newlines=True,
                bufsize=1
            )
            
            # 实时读取输出
            self.logger.info("开始读取FFmpeg输出:")
            while True:
                line = result.stdout.readline()
                if not line and result.poll() is not None:
                    break
                
                if line.strip():  # 如果行不为空
                    self.logger.info(f"FFmpeg输出: {line.strip()}")
                    
                    # 检测是否包含进度信息
                    if 'frame=' in line:
                        self.logger.info(f"检测到进度信息: {line.strip()}")
            
            return_code = result.returncode
            self.logger.info(f"FFmpeg测试完成，返回码: {return_code}")
            return return_code == 0
            
        except Exception as e:
            self.logger.error(f"测试FFmpeg输出时出错: {str(e)}")
            return False

    def delete_transcoding_temp_files(self, output_path):
        """删除转码过程中的临时文件"""
        try:
            output_path_obj = Path(output_path)
            temp_dir = output_path_obj.parent
            base_name = output_path_obj.stem  # 文件名（不含扩展名）
            
            # 查找所有相关的临时文件
            temp_patterns = [
                f"{base_name}*.mp4",  # 输出文件可能的临时版本
                f"{base_name}*.temp*",  # 临时文件
                f"{base_name}*.tmp*",   # 临时文件
            ]
            
            for pattern in temp_patterns:
                for temp_file in temp_dir.glob(pattern):
                    try:
                        if temp_file.exists():
                            temp_file.unlink()
                            self.logger.info(f"已删除转码临时文件: {temp_file}")
                    except Exception as e:
                        self.logger.error(f"删除临时文件失败 {temp_file}: {str(e)}")
            
            # 特别检查输出文件是否存在，如果存在但用户请求停止则删除
            if output_path_obj.exists() and self.stop_processing:
                try:
                    output_path_obj.unlink()
                    self.logger.info(f"已删除未完成的转码输出文件: {output_path_obj}")
                except Exception as e:
                    self.logger.error(f"删除未完成的转码输出文件失败 {output_path_obj}: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"删除转码临时文件时出错: {str(e)}")
    
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
        """选择处理完成后操作选项"""
        self.post_processing_action_var.set(option)
    
    def show_detection_model_menu(self, event=None):
        """显示检测模型选项菜单"""
        # 获取按钮的位置
        x = self.detection_model_button.winfo_rootx()
        y = self.detection_model_button.winfo_rooty() + self.detection_model_button.winfo_height()
        # 显示菜单
        self.detection_model_menu.post(x, y)
    
    def select_detection_model_option(self, option):
        """选择检测模型选项"""
        self.detection_model_var.set(option)
    
    def show_vr_mode_menu(self, event=None):
        """显示VR模式选项菜单"""
        x = self.vr_mode_button.winfo_rootx()
        y = self.vr_mode_button.winfo_rooty() + self.vr_mode_button.winfo_height()
        self.vr_mode_menu.post(x, y)
    
    def select_vr_mode_option(self, option):
        """选择VR模式选项"""
        self.vr_mode_var.set(option)
    
    def on_detection_threshold_focus_out(self, event=None):
        """检测阈值输入框失去焦点时的回调函数，弹窗提示用户
        
        只在值真正发生改变时才弹窗提示，避免初始化时弹窗
        """
        current_value = self.detection_threshold_var.get()
        # 检查值是否发生变化
        if current_value != self._detection_threshold_last_value:
            self._detection_threshold_last_value = current_value
            messagebox.showwarning("警告", "此数值影响马赛克检测效果，请谨慎修改！")
    
    def show_secondary_fix_display_menu(self):
        """显示二次修复显示/隐藏选项菜单"""
        # 在按钮位置显示菜单
        x = self.secondary_fix_display_button.winfo_rootx()
        y = self.secondary_fix_display_button.winfo_rooty() + self.secondary_fix_display_button.winfo_height()
        # 显示菜单
        self.secondary_fix_display_menu.post(x, y)
    
    def show_settings_mode_menu(self):
        """显示设置模式选项菜单"""
        # 在按钮位置显示菜单
        x = self.settings_mode_button.winfo_rootx()
        y = self.settings_mode_button.winfo_rooty() + self.settings_mode_button.winfo_height()
        # 显示菜单
        self.settings_mode_menu.post(x, y)
    
    def update_secondary_fix_status_label(self):
        """更新二次修复状态标签的显示
        
        当"显示/隐藏"下拉选项为"显示"时，不显示任何内容
        当"显示/隐藏"下拉选项为"隐藏"时，显示当前选择的二次修复使用软件
        """
        display_status = self.secondary_fix_display_var.get()
        if display_status == "显示":
            # 二次修复显示时，状态标签不显示任何内容
            self.secondary_fix_status_var.set("")
        else:
            # 二次修复隐藏时，显示当前使用的软件
            secondary_fix_software = self.secondary_fix_var.get()
            if secondary_fix_software == "无":
                self.secondary_fix_status_var.set("（无）")
            else:
                self.secondary_fix_status_var.set(f"（{secondary_fix_software}）")
    
    def select_secondary_fix_display_option(self, option):
        """选择二次修复显示/隐藏选项"""
        self.secondary_fix_display_var.set(option)
        # 更新状态标签
        self.update_secondary_fix_status_label()
        # 根据两个下拉选项的组合来显示或隐藏模块
        self.update_module_visibility()
    
    def select_settings_mode_option(self, option):
        """选择设置模式选项"""
        self.settings_mode_var.set(option)
        # 根据两个下拉选项的组合来显示或隐藏模块
        self.update_module_visibility()
    
    def update_module_visibility(self):
        """根据两个下拉选项的组合更新模块的显示/隐藏状态
        
        显示+二次修复：隐藏"自定义设置"模块+显示"二次修复"模块
        显示+全部设置：显示"自定义设置"模块+显示"二次修复"模块
        隐藏+二次修复：显示"自定义设置"模块+隐藏"二次修复"模块
        隐藏+全部设置：隐藏"自定义设置"模块+隐藏"二次修复"模块
        
        注意：实际的模块放置由update_ui_layout统一管理
        """
        # 调用update_ui_layout方法来调整UI布局（内部会根据状态决定显示哪些模块）
        self.update_ui_layout()
    
    def update_ui_layout(self):
        """更新UI布局，根据自定义设置和二次修复模块的显示状态调整下方组件的位置和窗口大小
        
        完全重新计算所有模块的位置和窗口高度：
        - 自定义设置模块高度: 240像素
        - 二次修复模块高度: 150像素
        - 按钮控制区域高度: 60像素
        - 进度区域高度: 165像素
        - 视频列表区域高度: 280像素
        - 处理总结高度: 60像素
        - 状态栏高度: 30像素
        - 模块间距: 5像素
        """
        # 模块高度定义
        SETTINGS_HEIGHT = 240      # 自定义设置模块高度
        SECONDARY_HEIGHT = 150     # 二次修复模块高度
        BUTTON_HEIGHT = 60         # 按钮控制区域高度
        PROGRESS_HEIGHT = 165      # 进度区域高度
        LISTS_HEIGHT = 280         # 视频列表区域高度
        SUMMARY_HEIGHT = 60        # 处理总结高度
        STATUS_HEIGHT = 30         # 状态栏高度
        SPACING = 5                # 模块间距
        MARGIN_TOP = 10            # 顶部边距
        
        # 获取当前窗口宽度
        current_width = self.root.winfo_width()
        
        # 检查两个模块的显示状态
        # 根据两个下拉选项的组合决定显示哪些模块：
        # 显示+二次修复：隐藏自定义设置，显示二次修复
        # 显示+全部设置：显示自定义设置，显示二次修复
        # 隐藏+二次修复：显示自定义设置，隐藏二次修复
        # 隐藏+全部设置：隐藏自定义设置，隐藏二次修复
        display_status = self.secondary_fix_display_var.get()
        settings_mode = self.settings_mode_var.get()
        
        if display_status == "显示" and settings_mode == "二次修复":
            is_settings_visible = False
            is_secondary_fix_visible = True
        elif display_status == "显示" and settings_mode == "全部设置":
            is_settings_visible = True
            is_secondary_fix_visible = True
        elif display_status == "隐藏" and settings_mode == "二次修复":
            is_settings_visible = True
            is_secondary_fix_visible = False
        else:  # 隐藏+全部设置
            is_settings_visible = False
            is_secondary_fix_visible = False
        
        # 计算当前Y坐标（从顶部开始）
        current_y = MARGIN_TOP
        
        # 放置自定义设置模块
        if is_settings_visible:
            self.settings_frame.place(x=10, y=current_y, width=1150, height=SETTINGS_HEIGHT)
            current_y += SETTINGS_HEIGHT + SPACING
        else:
            self.settings_frame.place_forget()
        
        # 放置二次修复模块
        if is_secondary_fix_visible:
            self.secondary_fix_frame.place(x=10, y=current_y, width=1150, height=SECONDARY_HEIGHT)
            current_y += SECONDARY_HEIGHT + SPACING
        else:
            self.secondary_fix_frame.place_forget()
        
        # 放置按钮控制区域
        self.button_frame.place(x=10, y=current_y, width=1150, height=BUTTON_HEIGHT)
        current_y += BUTTON_HEIGHT + SPACING
        
        # 放置进度区域
        self.progress_frame.place(x=10, y=current_y, width=1150, height=PROGRESS_HEIGHT)
        current_y += PROGRESS_HEIGHT + SPACING
        
        # 放置视频列表区域
        self.lists_frame.place(x=10, y=current_y, width=1150, height=LISTS_HEIGHT)
        current_y += LISTS_HEIGHT + SPACING
        
        # 放置处理总结
        self.summary_frame.place(x=10, y=current_y, width=1150, height=SUMMARY_HEIGHT)
        current_y += SUMMARY_HEIGHT + SPACING
        
        # 放置状态栏
        status_bar = self.root.children.get('!label')
        if status_bar:
            status_bar.place(x=10, y=current_y, width=1150, height=STATUS_HEIGHT)
        current_y += STATUS_HEIGHT + SPACING
        
        # 计算窗口高度（加上底部边距）
        new_height = current_y + MARGIN_TOP
        
        # 重新调整窗口大小
        self.root.geometry(f"{current_width}x{new_height}")
        # 更新窗口以确保所有更改生效
        self.root.update_idletasks()
    
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
        
        if action == "休眠":
            # 在单独的线程中执行，避免阻塞主线程
            def sleep_action():
                # 等待10秒钟
                self.logger.info(f"等待10秒钟后执行{action}操作")
                time.sleep(10)
                self.logger.info("执行休眠操作")
                try:
                    # 在Windows系统上执行休眠命令
                    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                except Exception as e:
                    self.logger.error(f"执行休眠操作失败: {str(e)}")
            
            # 启动线程
            threading.Thread(target=sleep_action, daemon=True).start()
        elif action == "关机":
            # 在单独的线程中执行，避免阻塞主线程
            def shutdown_action():
                # 等待10秒钟
                self.logger.info(f"等待10秒钟后执行{action}操作")
                time.sleep(10)
                self.logger.info("执行关机操作")
                try:
                    # 在Windows系统上执行关机命令
                    os.system("shutdown /s /t 0")
                except Exception as e:
                    self.logger.error(f"执行关机操作失败: {str(e)}")
            
            # 启动线程
            threading.Thread(target=shutdown_action, daemon=True).start()
        # 如果是"无"，则不做任何操作
    

    def stop_processing_func(self):
        """停止处理"""
        self.stop_processing = True
        self.status_var.set("正在停止处理...")
        
        # 无论当前处理模式，立即隐藏状态标识
        self.processing_mode_label.place_forget()
        
        # 检查当前处理模式来决定终止哪个进程
        current_mode = self.processing_mode_var.get()
        
        if current_mode == "转码":
            # 当前在转码过程中，需要终止FFmpeg进程
            try:
                # 强制终止当前运行的FFmpeg进程
                if self.current_process and self.current_process.poll() is None:
                    self.current_process.terminate()
                    
                    # 等待进程结束
                    try:
                        self.current_process.wait(timeout=2)
                        self.logger.info("FFmpeg转码进程已正常终止（停止按钮）")
                    except subprocess.TimeoutExpired:
                        # 如果进程未终止，强制杀死进程
                        self.current_process.kill()
                        self.logger.info("FFmpeg转码进程已被强制终止（停止按钮）")
                
                # 删除在输入文件夹中生成的所有转码临时文件
                if self.currently_processing:
                    input_folder = self.input_folder_var.get()
                    if input_folder:
                        input_path_obj = Path(self.currently_processing)
                        base_name = input_path_obj.stem  # 文件名（不含扩展名）
                        
                        # 删除转码过程中的临时文件
                        self.delete_transcoding_temp_files(str(input_path_obj))
                        
                        # 在输入文件夹中查找相关临时文件
                        temp_patterns = [
                            f"{base_name}*.mp4",
                            f"{base_name}*.temp*",
                            f"{base_name}*.tmp*",
                        ]
                        
                        input_dir = Path(input_folder)
                        for pattern in temp_patterns:
                            for temp_file in input_dir.glob(pattern):
                                try:
                                    if temp_file.exists():
                                        temp_file.unlink()
                                        self.logger.info(f"已删除输入文件夹中的转码临时文件: {temp_file}")
                                except Exception as e:
                                    self.logger.error(f"删除输入文件夹中的临时文件失败 {temp_file}: {str(e)}")
            
            except Exception as e:
                self.logger.error(f"终止转码进程时出错（停止按钮）: {str(e)}")
        else:
            # 当前在破解过程中，使用原有逻辑
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
                            # 使用多种方法强制终止所有jasna进程（进程名由用户配置决定）
                            self.kill_all_jasna_processes()
                
                # 无论current_process是否终止，都强制终止所有jasna进程（进程名由用户配置决定）
                self.logger.info(f"强制终止所有{self.get_jasna_exe_name()}进程（停止按钮）")
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
        
        # 隐藏处理状态指示器
        self.root.after(0, self.hide_processing_mode_indicator)
    
    def start_realtime_playback(self):
        """启动jasna-cli实时播放模式"""
        import os
        import subprocess
        
        jasna_path = self.jasna_path_var.get().strip()
        if not jasna_path:
            self.show_custom_messagebox("error", "错误", "请先设置jasna-cli的地址")
            return
        
        jasna_path = jasna_path.replace("/", "\\")
        if not os.path.exists(jasna_path):
            self.show_custom_messagebox("error", "错误", f"jasna-cli程序不存在:\n{jasna_path}")
            return
        
        jasna_dir = os.path.dirname(jasna_path)
        jasna_exe_name = os.path.basename(jasna_path)
        
        slice_frames_4k = self.slice_frames_var2.get().strip()
        detection_model = self.detection_model_var.get()
        detection_threshold = self.detection_threshold_var.get().strip()
        
        cmd = f'.\\{jasna_exe_name} --stream --max-clip-size {slice_frames_4k} --temporal-overlap 8 --detection-model {detection_model} --detection-score-threshold {detection_threshold} --log-level info'
        
        secondary_fix_software = self.secondary_fix_var.get()
        if secondary_fix_software == "RTX-SR":
            rtx_scale = self.rtx_sr_scale_var.get().replace("X", "")
            rtx_quality = self.translate_rtx_option_to_english(self.rtx_sr_quality_var.get())
            rtx_denoise = self.translate_rtx_option_to_english(self.rtx_sr_denoise_var.get())
            rtx_deblur = self.translate_rtx_option_to_english(self.rtx_sr_deblur_var.get())
            cmd += f' --secondary-restoration rtx-super-res --rtx-scale {rtx_scale} --rtx-quality {rtx_quality} --rtx-denoise {rtx_denoise} --rtx-deblur {rtx_deblur}'
        
        # 添加VR模式参数
        vr_mode = self.vr_mode_var.get()
        if vr_mode == "自动":
            cmd += ' --vr-mode auto'
        elif vr_mode == "SBS":
            cmd += ' --vr-mode sbs'
        elif vr_mode == "鱼眼":
            cmd += ' --vr-mode sbs-fisheye'
        
        self.logger.info(f"启动实时播放模式，工作目录: {jasna_dir}")
        self.logger.info(f"执行命令: {cmd}")
        self.status_var.set("正在运行实时播放模式...")
        
        try:
            if subprocess.Popen(
                cmd,
                shell=True,
                cwd=jasna_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            ):
                self.logger.info("实时播放模式已启动")
        except Exception as e:
            self.logger.error(f"启动实时播放模式失败: {str(e)}")
            self.show_custom_messagebox("error", "错误", f"启动实时播放模式失败:\n{str(e)}")
    
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
                                # 使用多种方法强制终止所有jasna进程（进程名由用户配置决定）
                                self.kill_all_jasna_processes()
                except Exception as e:
                    self.logger.error(f"终止JASNA进程时出错（窗口关闭）: {str(e)}")

                time.sleep(1)  # 给线程一点时间停止
                self.root.destroy()
        else:
            self.root.destroy()

    def get_jasna_ffmpeg_path(self):
        r"""获取JASNA程序目录下的ffmpeg.exe路径
        
        从jasna_path_var中提取JASNA程序所在目录，按优先级查找ffmpeg.exe:
        1. JASNA目录\tools\ffmpeg.exe
        2. JASNA目录\_internal\tools\ffmpeg.exe
        
        例如: E:\AI\jasna-0.5.0-alpha6\jasna-cli.exe -> 
              优先查找: E:\AI\jasna-0.5.0-alpha6\tools\ffmpeg.exe
              其次查找: E:\AI\jasna-0.5.0-alpha6\_internal\tools\ffmpeg.exe
        
        Returns:
            str: ffmpeg.exe的完整路径，如果都不存在则返回None
        """
        jasna_path = self.jasna_path_var.get()
        if not jasna_path:
            return None
        
        # 获取JASNA程序所在目录（去掉文件名）
        jasna_dir = os.path.dirname(jasna_path)
        if not jasna_dir:
            return None
        
        # 优先级1: JASNA目录\tools\ffmpeg.exe
        ffmpeg_path = os.path.join(jasna_dir, 'tools', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
        
        # 优先级2: JASNA目录\_internal\tools\ffmpeg.exe
        ffmpeg_path = os.path.join(jasna_dir, '_internal', 'tools', 'ffmpeg.exe')
        if os.path.exists(ffmpeg_path):
            return ffmpeg_path
        
        return None

    def transcode_video(self, input_path, output_path):
        """使用FFmpeg对视频进行转码，使用CUDA解码器和hevc_nvenc编码器"""
        try:
            # 设置转码状态标志
            self.is_transcoding = True
            
            # 获取转码参数
            transcode_params = self.transcode_params_var.get()
            
            # 确保输出格式为MP4
            if not output_path.lower().endswith('.mp4'):
                output_path += '.mp4'
            
            # 构建FFmpeg命令，按照规范结构组织参数
            # 基础硬件加速参数
            base_hwaccel_params = ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
            # 固定编码设置
            fixed_encode_params = ['-c:v', 'hevc_nvenc']
            # 用户自定义参数（从transcode_params中提取除固定参数外的部分）
            custom_params = self.parse_custom_params_for_transcode(transcode_params)
            
            # 记录参数解析详情
            self.logger.info(f"原始转码参数: {transcode_params}")
            self.logger.info(f"解析出的自定义参数: {' '.join(custom_params)}")
            
            # 优先使用JASNA目录下的ffmpeg.exe
            jasna_ffmpeg = self.get_jasna_ffmpeg_path()
            if jasna_ffmpeg:
                ffmpeg_executable = jasna_ffmpeg
                self.logger.info(f"使用JASNA目录下的FFmpeg: {jasna_ffmpeg}")
            else:
                ffmpeg_executable = 'ffmpeg'
                self.logger.info("使用系统PATH中的FFmpeg")
            
            # 构建完整的FFmpeg命令，确保硬件加速参数在输入文件之前
            cmd = [ffmpeg_executable] + base_hwaccel_params + ['-i', input_path] + fixed_encode_params + custom_params + ['-c:a', 'copy', output_path]
            
            self.logger.info(f"开始转码视频: {input_path}")
            self.logger.info(f"FFmpeg命令: {' '.join(cmd)}")
            self.logger.info(f"NVIDIA硬件加速参数: -hwaccel cuda -hwaccel_output_format cuda -c:v hevc_nvenc")
            
            # 获取视频信息用于进度显示
            video_info_result = self.get_video_info(input_path)
            if not video_info_result:
                self.logger.error(f"获取视频信息失败: {input_path}")
                return False
            
            # 由于get_video_info函数设置的是GUI变量而不是返回字典，我们需要从变量中获取信息
            video_info = {
                'resolution': self.video_resolution_var.get(),
                'fps': self.video_fps_var.get(),
                'duration': self.video_duration_var.get()
            }
            
            # 尝试获取总帧数（如果可用）
            try:
                # 这里需要通过其他方式获取总帧数，因为get_video_info不直接返回字典
                total_frames = self.estimate_total_frames(input_path)
            except:
                total_frames = 0  # 如果无法估算，则设为0
            
            # 更新处理模式为转码
            self.processing_mode_var.set("转码")
            
            # 显示当前正在转码的视频信息
            self.root.after(0, lambda: self.current_video_var.set(
                f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码中..."
            ))
            
            # 执行转码命令并实时监控进度
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # 合并输出流，捕获所有输出
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',  # 指定UTF-8编码以支持中文路径
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows隐藏控制台窗口
            )
            
            # 实时读取输出来获取进度信息
            processed_frames = 0
            start_time = time.time()
            
            while True:
                if self.stop_processing:
                    # 用户请求停止处理，终止ffmpeg进程
                    self.logger.info("用户请求停止转码")
                    self.current_process.terminate()
                    try:
                        self.current_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        self.current_process.kill()
                        self.logger.info("FFmpeg进程已被强制终止")
                    
                    # 删除转码过程中生成的临时文件
                    self.delete_transcoding_temp_files(output_path)
                    return False
                
                line = self.current_process.stdout.readline()
                
                if not line and self.current_process.poll() is not None:
                    break
                
                # 记录所有FFmpeg输出到日志
                if line.strip():  # 只记录非空行
                    self.logger.info(f"FFmpeg输出: {line.strip()}")
                
                # 解析FFmpeg进度信息
                # FFmpeg输出格式可能是类似 "frame=  123 fps=..." 的形式
                if 'frame=' in line:
                    # 使用更精确的正则表达式来匹配frame
                    frame_match = re.search(r'frame=\s*(\d+)', line)
                    if frame_match:
                        try:
                            frame_num = int(frame_match.group(1))
                            if frame_num > processed_frames:
                                processed_frames = frame_num
                                
                                # 计算进度百分比
                                progress_percent = (processed_frames / total_frames * 100) if total_frames > 0 else 0
                                
                                # 计算已运行时间和预估剩余时间
                                elapsed_time = time.time() - start_time
                                fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
                                remaining_frames = total_frames - processed_frames
                                eta = remaining_frames / fps if fps > 0 else 0
                                
                                # 格式化时间显示
                                elapsed_str = self.format_time(elapsed_time)
                                eta_str = self.format_time(eta) if eta > 0 else "未知"
                                
                                # 更新进度信息显示到各个变量
                                self.root.after(0, lambda t=elapsed_str: self.elapsed_time_var.set(t))
                                self.root.after(0, lambda t=eta_str: self.remaining_time_var.set(t))
                                self.root.after(0, lambda s=fps: self.processing_speed_var.set(f"{s:.2f}fps"))
                                self.root.after(0, lambda p=processed_frames: self.processed_frames_var.set(str(p)))
                                self.root.after(0, lambda r=total_frames-processed_frames: self.remaining_frames_var.set(str(r)))
                                self.root.after(0, lambda t=total_frames: self.total_frames_var.set(str(t)))
                                
                                # 更新进度条和进度百分比显示（显示为整数）
                                self.root.after(0, lambda p=progress_percent: self.progress_bar.configure(value=int(p)))
                                self.root.after(0, lambda p=progress_percent: self.progress_percent_var.set(f"{int(p)}%"))
                                
                                # 更新当前视频信息显示进度
                                self.root.after(0, lambda: self.current_video_var.set(
                                    f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码进度: {progress_percent:.1f}%"
                                ))
                        
                        except ValueError:
                            pass  # 忽略无法解析的帧数
            
            # 等待进程结束并获取返回码
            return_code = self.current_process.wait()
            
            if return_code == 0:
                self.logger.info(f"转码成功: {output_path}")
                
                # 检查输出文件是否存在且大小大于0
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    self.logger.info(f"转码文件验证成功: {output_path}")
                    return True
                else:
                    self.logger.error(f"转码文件不存在或为空: {output_path}")
                    return False
            else:
                self.logger.error(f"转码失败，FFmpeg返回码: {return_code}")
                self.logger.info(f"音频复制模式失败，切换到音频编码模式: {input_path}")
                # 音频复制失败时，使用AAC编码
                # 备用模式也使用相同的ffmpeg_executable
                fallback_cmd = [ffmpeg_executable] + base_hwaccel_params + ['-i', input_path] + fixed_encode_params + custom_params + ['-c:a', 'aac', '-b:a', '256k', output_path]
                
                self.logger.info(f"使用音频编码模式转码: {input_path}")
                self.logger.info(f"FFmpeg命令: {' '.join(fallback_cmd)}")
                
                # 执行备用转码命令
                try:
                    self.current_process = subprocess.Popen(
                        fallback_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,  # 合并输出流，捕获所有输出
                        universal_newlines=True,
                        bufsize=1,
                        encoding='utf-8',  # 指定UTF-8编码以支持中文路径
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows隐藏控制台窗口
                    )
                    
                    # 实时读取输出来获取进度信息
                    processed_frames = 0
                    start_time = time.time()
                    
                    while True:
                        if self.stop_processing:
                            # 用户请求停止处理，终止ffmpeg进程
                            self.logger.info("用户请求停止转码")
                            self.current_process.terminate()
                            try:
                                self.current_process.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                self.current_process.kill()
                                self.logger.info("FFmpeg进程已被强制终止")
                            
                            # 删除转码过程中生成的临时文件
                            self.delete_transcoding_temp_files(output_path)
                            return False
                        
                        line = self.current_process.stdout.readline()
                        
                        if not line and self.current_process.poll() is not None:
                            break
                        
                        # 记录所有FFmpeg输出到日志
                        if line.strip():  # 只记录非空行
                            self.logger.info(f"FFmpeg输出: {line.strip()}")
                        
                        # 解析FFmpeg进度信息
                        # FFmpeg输出格式可能是类似 "frame=  123 fps=..." 的形式
                        if 'frame=' in line:
                            # 使用更精确的正则表达式来匹配frame
                            frame_match = re.search(r'frame=\s*(\d+)', line)
                            if frame_match:
                                try:
                                    frame_num = int(frame_match.group(1))
                                    if frame_num > processed_frames:
                                        processed_frames = frame_num
                                        
                                        # 计算进度百分比
                                        progress_percent = (processed_frames / total_frames * 100) if total_frames > 0 else 0
                                        
                                        # 计算已运行时间和预估剩余时间
                                        elapsed_time = time.time() - start_time
                                        fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
                                        remaining_frames = total_frames - processed_frames
                                        eta = remaining_frames / fps if fps > 0 else 0
                                        
                                        # 格式化时间显示
                                        elapsed_str = self.format_time(elapsed_time)
                                        eta_str = self.format_time(eta) if eta > 0 else "未知"
                                        
                                        # 更新进度信息显示到各个变量
                                        self.root.after(0, lambda t=elapsed_str: self.elapsed_time_var.set(t))
                                        self.root.after(0, lambda t=eta_str: self.remaining_time_var.set(t))
                                        self.root.after(0, lambda s=fps: self.processing_speed_var.set(f"{s:.2f}fps"))
                                        self.root.after(0, lambda p=processed_frames: self.processed_frames_var.set(str(p)))
                                        self.root.after(0, lambda r=total_frames-processed_frames: self.remaining_frames_var.set(str(r)))
                                        self.root.after(0, lambda t=total_frames: self.total_frames_var.set(str(t)))
                                        
                                        # 更新进度条和进度百分比显示（显示为整数）
                                        self.root.after(0, lambda val=progress_percent: self.progress_bar.configure(value=int(val)))
                                        self.root.after(0, lambda p=progress_percent: self.progress_percent_var.set(f"{int(p)}%"))
                                        
                                        # 更新当前视频信息显示进度
                                        self.root.after(0, lambda: self.current_video_var.set(
                                            f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码进度: {progress_percent:.1f}%"
                                        ))
                                
                                except ValueError:
                                    pass  # 忽略无法解析的帧数
                    
                    # 等待进程结束并获取返回码
                    return_code = self.current_process.wait()
                    
                    if return_code == 0:
                        self.logger.info(f"备用音频编码模式转码成功: {output_path}")
                        
                        # 检查输出文件是否存在且大小大于0
                        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                            self.logger.info(f"转码文件验证成功: {output_path}")
                            return True
                        else:
                            self.logger.error(f"转码文件不存在或为空: {output_path}")
                            return False
                    else:
                        self.logger.error(f"备用音频编码模式转码失败，FFmpeg返回码: {return_code}")
                        return False
                        
                except Exception as e:
                    self.logger.error(f"备用转码过程中出错: {str(e)}")
                    return False
                
        except FileNotFoundError:
            self.logger.error("FFmpeg未找到，请确保已安装FFmpeg并添加到系统PATH")
            # 尝试使用JASNA目录下的ffmpeg或本地ffmpeg
            try:
                # 首先尝试JASNA目录下的ffmpeg
                jasna_ffmpeg = self.get_jasna_ffmpeg_path()
                if jasna_ffmpeg:
                    local_ffmpeg = jasna_ffmpeg
                    self.logger.info(f"FileNotFoundError后使用JASNA目录下的FFmpeg: {jasna_ffmpeg}")
                else:
                    # 尝试使用本地ffmpeg
                    local_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
                    if not os.path.exists(local_ffmpeg):
                        self.logger.error("未找到可用的FFmpeg，转码失败")
                        return False
                    self.logger.info(f"FileNotFoundError后使用本地FFmpeg: {local_ffmpeg}")
                
                # 重新构建命令使用本地ffmpeg
                transcode_params = self.transcode_params_var.get()
                # 使用预设的转码参数（已包含CUDA解码和hevc_nvenc编码）
                
                output_path_with_mp4 = output_path if output_path.lower().endswith('.mp4') else output_path + '.mp4'
                
                # 获取视频信息用于进度显示
                video_info_result = self.get_video_info(input_path)
                if not video_info_result:
                    self.logger.error(f"获取视频信息失败: {input_path}")
                    return False
                
                # 由于get_video_info函数设置的是GUI变量而不是返回字典，我们需要从变量中获取信息
                video_info = {
                    'resolution': self.video_resolution_var.get(),
                    'fps': self.video_fps_var.get(),
                    'duration': self.video_duration_var.get()
                }
                
                # 尝试获取总帧数（如果可用）
                try:
                    # 这里需要通过其他方式获取总帧数，因为get_video_info不直接返回字典
                    total_frames = self.estimate_total_frames(input_path)
                except:
                    total_frames = 0  # 如果无法估算，则设为0
                
                # 更新处理模式为转码
                self.processing_mode_var.set("转码")
                
                # 显示当前正在转码的视频信息
                self.root.after(0, lambda: self.current_video_var.set(
                    f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码中..."
                ))
                
                # 构建本地FFmpeg命令，按照规范结构组织参数
                # 基础硬件加速参数
                base_hwaccel_params = ['-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda']
                # 固定编码设置
                fixed_encode_params = ['-c:v', 'hevc_nvenc']
                # 用户自定义参数（从transcode_params中提取除固定参数外的部分）
                custom_params = self.parse_custom_params_for_transcode(transcode_params)
                
                # 记录参数解析详情
                self.logger.info(f"原始转码参数: {transcode_params}")
                self.logger.info(f"解析出的自定义参数: {' '.join(custom_params)}")
                
                # 构建完整的本地FFmpeg命令，确保硬件加速参数在输入文件之前
                cmd = [local_ffmpeg] + base_hwaccel_params + ['-i', input_path] + fixed_encode_params + custom_params + ['-c:a', 'copy', output_path_with_mp4]
                
                self.logger.info(f"使用本地FFmpeg转码: {input_path}")
                self.logger.info(f"本地FFmpeg命令: {' '.join(cmd)}")
                self.logger.info(f"NVIDIA硬件加速参数: -hwaccel cuda -hwaccel_output_format cuda -c:v hevc_nvenc")
                
                # 执行转码命令并实时监控进度
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # 合并输出流，捕获所有输出
                    universal_newlines=True,
                    bufsize=1,
                    encoding='utf-8',  # 指定UTF-8编码以支持中文路径
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows隐藏控制台窗口
                )
                
                # 实时读取stderr来获取进度信息
                processed_frames = 0
                start_time = time.time()
                
                while True:
                    if self.stop_processing:
                        # 用户请求停止处理，终止ffmpeg进程
                        self.logger.info("用户请求停止转码")
                        self.current_process.terminate()
                        try:
                            self.current_process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            self.current_process.kill()
                            self.logger.info("FFmpeg进程已被强制终止")
                        
                        # 删除转码过程中生成的临时文件
                        self.delete_transcoding_temp_files(output_path_with_mp4)
                        return False
                    
                    line = self.current_process.stdout.readline()
                    
                    if not line and self.current_process.poll() is not None:
                        break
                    
                    # 记录所有FFmpeg输出到日志
                    if line.strip():  # 只记录非空行
                        self.logger.info(f"FFmpeg输出: {line.strip()}")
                    
                    # 解析FFmpeg进度信息
                    # FFmpeg输出格式可能是类似 "frame=  123 fps=..." 的形式
                    if 'frame=' in line:
                        # 使用更精确的正则表达式来匹配frame
                        frame_match = re.search(r'frame=\s*(\d+)', line)
                        if frame_match:
                            try:
                                frame_num = int(frame_match.group(1))
                                if frame_num > processed_frames:
                                    processed_frames = frame_num
                                    
                                    # 计算进度百分比
                                    progress_percent = (processed_frames / total_frames * 100) if total_frames > 0 else 0
                                    
                                    # 计算已运行时间和预估剩余时间
                                    elapsed_time = time.time() - start_time
                                    fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
                                    remaining_frames = total_frames - processed_frames
                                    eta = remaining_frames / fps if fps > 0 else 0
                                    
                                    # 格式化时间显示
                                    elapsed_str = self.format_time(elapsed_time)
                                    eta_str = self.format_time(eta) if eta > 0 else "未知"
                                    
                                    # 更新进度信息显示到各个变量
                                    self.root.after(0, lambda t=elapsed_str: self.elapsed_time_var.set(t))
                                    self.root.after(0, lambda t=eta_str: self.remaining_time_var.set(t))
                                    self.root.after(0, lambda s=fps: self.processing_speed_var.set(f"{s:.2f}fps"))
                                    self.root.after(0, lambda p=processed_frames: self.processed_frames_var.set(str(p)))
                                    self.root.after(0, lambda r=total_frames-processed_frames: self.remaining_frames_var.set(str(r)))
                                    self.root.after(0, lambda t=total_frames: self.total_frames_var.set(str(t)))
                                    
                                    # 更新进度条和进度百分比显示
                                    self.root.after(0, lambda val=progress_percent: self.progress_bar.configure(value=int(val)))
                                    self.root.after(0, lambda p=progress_percent: self.progress_percent_var.set(f"{int(p)}%"))
                                    
                                    # 更新当前视频信息显示进度
                                    self.root.after(0, lambda: self.current_video_var.set(
                                        f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码进度: {progress_percent:.1f}%"
                                    ))
                            
                            except ValueError:
                                pass  # 忽略无法解析的帧数
                
                # 等待进程结束并获取返回码
                return_code = self.current_process.wait()
                
                if return_code == 0 and os.path.exists(output_path_with_mp4) and os.path.getsize(output_path_with_mp4) > 0:
                    self.logger.info(f"本地FFmpeg转码成功: {output_path_with_mp4}")
                    return True
                else:
                        self.logger.error(f"本地FFmpeg转码失败，返回码: {return_code}")
                        self.logger.info(f"本地FFmpeg音频复制模式失败，切换到音频编码模式: {input_path}")
                        # 本地FFmpeg音频复制失败时，使用AAC编码
                        local_fallback_cmd = [local_ffmpeg] + base_hwaccel_params + ['-i', input_path] + fixed_encode_params + custom_params + ['-c:a', 'aac', '-b:a', '256k', output_path_with_mp4]
                        
                        self.logger.info(f"使用本地FFmpeg音频编码模式转码: {input_path}")
                        self.logger.info(f"本地FFmpeg备用命令: {' '.join(local_fallback_cmd)}")
                        
                        # 执行备用转码命令
                        try:
                            self.current_process = subprocess.Popen(
                                local_fallback_cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,  # 合并输出流，捕获所有输出
                                universal_newlines=True,
                                bufsize=1,
                                encoding='utf-8',  # 指定UTF-8编码以支持中文路径
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0  # Windows隐藏控制台窗口
                            )
                            
                            # 实时读取输出来获取进度信息
                            processed_frames = 0
                            start_time = time.time()
                            
                            while True:
                                if self.stop_processing:
                                    # 用户请求停止处理，终止ffmpeg进程
                                    self.logger.info("用户请求停止转码")
                                    self.current_process.terminate()
                                    try:
                                        self.current_process.wait(timeout=2)
                                    except subprocess.TimeoutExpired:
                                        self.current_process.kill()
                                        self.logger.info("FFmpeg进程已被强制终止")
                                    
                                    # 删除转码过程中生成的临时文件
                                    self.delete_transcoding_temp_files(output_path_with_mp4)
                                    return False
                                
                                line = self.current_process.stdout.readline()
                                
                                if not line and self.current_process.poll() is not None:
                                    break
                                
                                # 记录所有FFmpeg输出到日志
                                if line.strip():  # 只记录非空行
                                    self.logger.info(f"FFmpeg输出: {line.strip()}")
                                
                                # 解析FFmpeg进度信息
                                # FFmpeg输出格式可能是类似 "frame=  123 fps=..." 的形式
                                if 'frame=' in line:
                                    # 使用更精确的正则表达式来匹配frame
                                    frame_match = re.search(r'frame=\s*(\d+)', line)
                                    if frame_match:
                                        try:
                                            frame_num = int(frame_match.group(1))
                                            if frame_num > processed_frames:
                                                processed_frames = frame_num
                                                
                                                # 计算进度百分比
                                                progress_percent = (processed_frames / total_frames * 100) if total_frames > 0 else 0
                                                
                                                # 计算已运行时间和预估剩余时间
                                                elapsed_time = time.time() - start_time
                                                fps = processed_frames / elapsed_time if elapsed_time > 0 else 0
                                                remaining_frames = total_frames - processed_frames
                                                eta = remaining_frames / fps if fps > 0 else 0
                                                
                                                # 格式化时间显示
                                                elapsed_str = self.format_time(elapsed_time)
                                                eta_str = self.format_time(eta) if eta > 0 else "未知"
                                                
                                                # 更新进度信息显示到各个变量
                                                self.root.after(0, lambda t=elapsed_str: self.elapsed_time_var.set(t))
                                                self.root.after(0, lambda t=eta_str: self.remaining_time_var.set(t))
                                                self.root.after(0, lambda s=fps: self.processing_speed_var.set(f"{s:.2f}fps"))
                                                self.root.after(0, lambda p=processed_frames: self.processed_frames_var.set(str(p)))
                                                self.root.after(0, lambda r=total_frames-processed_frames: self.remaining_frames_var.set(str(r)))
                                                self.root.after(0, lambda t=total_frames: self.total_frames_var.set(str(t)))
                                                
                                                # 更新进度条和进度百分比显示（显示为整数）
                                                self.root.after(0, lambda val=progress_percent: self.progress_bar.configure(value=int(val)))
                                                self.root.after(0, lambda p=progress_percent: self.progress_percent_var.set(f"{int(p)}%"))
                                                
                                                # 更新当前视频信息显示进度
                                                self.root.after(0, lambda: self.current_video_var.set(
                                                    f"{os.path.basename(input_path)} | {video_info['resolution']} | {video_info['fps']}fps | {video_info['duration']} | 转码进度: {progress_percent:.1f}%"
                                                ))
                                        
                                        except ValueError:
                                            pass  # 忽略无法解析的帧数
                            
                            # 等待进程结束并获取返回码
                            return_code = self.current_process.wait()
                            
                            if return_code == 0 and os.path.exists(output_path_with_mp4) and os.path.getsize(output_path_with_mp4) > 0:
                                self.logger.info(f"本地FFmpeg备用音频编码模式转码成功: {output_path_with_mp4}")
                                return True
                            else:
                                self.logger.error(f"本地FFmpeg备用音频编码模式转码失败，返回码: {return_code}")
                                return False
                                
                        except Exception as e:
                            self.logger.error(f"本地FFmpeg备用转码过程中出错: {str(e)}")
                            return False
            except Exception as e:
                self.logger.error(f"使用本地FFmpeg转码时出错: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"转码视频时出错: {str(e)}")
            return False

    def parse_custom_params_for_transcode(self, transcode_params):
        """解析用户自定义参数，移除固定参数部分，只保留用户自定义部分"""
        # 移除固定参数部分，只保留用户可能自定义的参数
        params_list = transcode_params.split()
        
        # 定义需要移除的固定参数组合
        fixed_pairs = [
            ('-hwaccel', 'cuda'),
            ('-hwaccel_output_format', 'cuda'),
            ('-c:v', 'hevc_nvenc'),
            ('-c:a', 'aac'),
            ('-b:a', '256k')
        ]
        
        # 过滤掉固定参数，保留用户自定义参数
        filtered_params = []
        i = 0
        while i < len(params_list):
            # 检查是否是双参数组合
            found_pair = False
            for pair in fixed_pairs:
                if (i + 1 < len(params_list) and 
                    params_list[i] == pair[0] and 
                    params_list[i + 1] == pair[1]):
                    i += 2  # 跳过这对参数
                    found_pair = True
                    break
            
            if not found_pair:
                # 检查是否是单个固定参数
                is_single_fixed = False
                for pair in fixed_pairs:
                    if params_list[i] == pair[0]:
                        # 这是一个固定参数的第一部分，但后面跟的不是对应的值
                        # 这种情况不应该发生，但我们仍需处理
                        if i + 1 < len(params_list) and params_list[i + 1] == pair[1]:
                            i += 2  # 跳过这对参数
                            is_single_fixed = True
                            break
                
                if not is_single_fixed:
                    filtered_params.append(params_list[i])
                    i += 1
            else:
                # 已经处理了参数对，继续循环
                continue
        
        return filtered_params




def main():
    root = tk.Tk()
    app = JasnaGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()