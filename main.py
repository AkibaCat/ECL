#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy Minecraft Launcher
使用Python开发的Minecraft启动器 - 当期阶段：开发测试版
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import json
import os
import sys
import subprocess
import threading
import requests
from pathlib import Path

from enhanced_version_manager import EnhancedVersionManager
from asset_downloader import AssetDownloader
from library_manager import LibraryManager
from launch_config import LaunchConfig
from dependency_checker import DependencyChecker
from process_manager import ProcessManager
from version_list_manager import VersionListManager, VersionListDialog

class MinecraftLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Easy Minecraft Launcher - 开发测试版")
        self.root.geometry("625x700")
        
        # 配置管理 - 将配置文件创建在程序所在目录
        program_dir = Path(__file__).parent
        config_path = program_dir / "config.json"
        self.config = LaunchConfig(config_path)
        
        # Minecraft文件夹路径
        self.minecraft_path = self.config.get('game_directory')
        
        # 管理器实例
        self.version_manager = EnhancedVersionManager(self.minecraft_path, self.progress_callback)
        self.asset_downloader = AssetDownloader(self.minecraft_path, self.progress_callback, max_workers=8)  # 添加多线程支持
        self.library_manager = LibraryManager(self.minecraft_path, self.progress_callback)
        self.dependency_checker = DependencyChecker(self.minecraft_path)
        self.process_manager = ProcessManager()
        self.version_list_manager = VersionListManager(self.minecraft_path, self.progress_callback)
        
        # 版本管理
        self.versions = []
        self.current_version = None
        self.available_versions = []
        
        # 初始化UI
        self.setup_ui()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 加载版本列表
        self.refresh_versions()
        self.load_available_versions()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="Easy Minecraft Launcher - Alpha_v0.1.20", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=10)
        
        # 版本选择区域
        version_frame = ttk.LabelFrame(main_frame, text="版本管理", padding="10")
        version_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 本地版本选择
        ttk.Label(version_frame, text="本地版本:").grid(row=0, column=0, sticky=tk.W)
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(version_frame, textvariable=self.version_var, width=25)
        self.version_combo.grid(row=0, column=1, padx=5)
        self.version_combo['state'] = 'readonly'
        
        # 绑定版本选择事件
        self.version_combo.bind('<<ComboboxSelected>>', self.on_version_selected)
        
        # 在线版本选择
        ttk.Label(version_frame, text="在线版本:").grid(row=0, column=2, sticky=tk.W, padx=10)
        self.online_version_var = tk.StringVar()
        self.online_version_combo = ttk.Combobox(version_frame, textvariable=self.online_version_var, width=25)
        self.online_version_combo.grid(row=0, column=3, padx=5)
        self.online_version_combo['state'] = 'readonly'
        
        # 按钮区域
        button_frame = ttk.Frame(version_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="刷新版本", 
                  command=self.refresh_versions).grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="下载版本", 
                  command=self.download_version).grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="版本列表", 
                  command=self.show_version_list).grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="检查Java", 
                  command=self.check_java).grid(row=0, column=3, padx=5)
        
        # 添加资源管理按钮
        ttk.Button(button_frame, text="检查资源", 
                  command=self.check_assets).grid(row=0, column=4, padx=5)
        
        ttk.Button(button_frame, text="下载资源", 
                  command=self.download_missing_assets).grid(row=0, column=5, padx=5)
        
        # 启动设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="启动设置", padding="10")
        settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 内存设置
        ttk.Label(settings_frame, text="内存 (MB):").grid(row=0, column=0, sticky=tk.W)
        self.memory_var = tk.StringVar(value=str(self.config.get('memory', 2048)))
        memory_entry = ttk.Entry(settings_frame, textvariable=self.memory_var, width=10)
        memory_entry.grid(row=0, column=1, padx=5)
        
        # 用户名设置
        ttk.Label(settings_frame, text="用户名:").grid(row=0, column=2, sticky=tk.W, padx=10)
        self.username_var = tk.StringVar(value=self.config.get('username', 'Player'))
        username_entry = ttk.Entry(settings_frame, textvariable=self.username_var, width=15)
        username_entry.grid(row=0, column=3, padx=5)
        
        # 游戏目录设置
        ttk.Label(settings_frame, text="游戏目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.game_dir_var = tk.StringVar(value=self.minecraft_path)
        game_dir_entry = ttk.Entry(settings_frame, textvariable=self.game_dir_var, width=50)
        game_dir_entry.grid(row=1, column=1, columnspan=2, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(settings_frame, text="浏览", 
                  command=self.browse_game_dir).grid(row=1, column=3, padx=5)
        
        # Java路径设置
        ttk.Label(settings_frame, text="Java路径:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.java_path_var = tk.StringVar(value=self.config.get('java_path', ''))
        java_path_entry = ttk.Entry(settings_frame, textvariable=self.java_path_var, width=50)
        java_path_entry.grid(row=2, column=1, columnspan=2, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(settings_frame, text="浏览", 
                  command=self.browse_java_path).grid(row=2, column=3, padx=5)
        
        # 启动按钮
        launch_frame = ttk.Frame(main_frame)
        launch_frame.grid(row=3, column=0, pady=20)
        
        self.launch_button = ttk.Button(launch_frame, text="启动游戏", 
                                       command=self.launch_game, style="Accent.TButton")
        self.launch_button.grid(row=0, column=0, padx=10)
        
        # 进度显示
        self.progress_var = tk.StringVar(value="就绪")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=4, column=0, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="启动日志", padding="10")
        log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
# 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 绑定事件
        self.memory_var.trace('w', self.on_settings_changed)
        self.username_var.trace('w', self.on_settings_changed)
        self.game_dir_var.trace('w', self.on_settings_changed)
        self.java_path_var.trace('w', self.on_settings_changed)
    
    def on_version_selected(self, event):
        """版本选择事件处理"""
        selected_version = self.version_var.get()
        if selected_version:
            self.current_version = selected_version
            self.log_message(f"已选择版本: {self.current_version}")
    
    def show_version_list(self):
        """显示版本列表对话框"""
        try:
            VersionListDialog(self.root, self.version_list_manager, self.minecraft_path)
        except Exception as e:
            messagebox.showerror("错误", f"打开版本列表失败: {e}")

    def progress_callback(self, message, progress):
        """进度回调函数"""
        def update():
            self.progress_var.set(message)
            if progress >= 0:
                self.progress_bar['value'] = progress
            else:
                self.progress_bar['mode'] = 'indeterminate'
                self.progress_bar.start()
            self.root.update()
        
        self.root.after(0, update)
    
    def log_message(self, message):
        """添加日志消息"""
        def update():
            self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            self.root.update()
        
        self.root.after(0, update)
    
    def on_settings_changed(self, *args):
        """设置改变时的回调"""
        self.config.set('memory', int(self.memory_var.get() or 2048))
        self.config.set('username', self.username_var.get())
        self.config.set('game_directory', self.game_dir_var.get())
        self.config.set('java_path', self.java_path_var.get())
    
    def load_available_versions(self):
        """加载可用的在线版本"""
        try:
            self.available_versions = self.version_manager.get_available_versions('release')
            version_ids = [v['id'] for v in self.available_versions[:20]]  # 只显示最新的20个版本
            self.online_version_combo['values'] = version_ids
            if version_ids:
                self.online_version_combo.set(version_ids[0])
        except Exception as e:
            self.log_message(f"加载在线版本失败: {e}")
    
    def refresh_versions(self):
        """刷新本地版本列表"""
        try:
            self.versions = self.version_manager.get_local_versions()
            version_ids = [v['id'] for v in self.versions]
            self.version_combo['values'] = version_ids
            if version_ids:
                # 不再自动设置当前版本，让用户选择
                self.version_combo.set("")
                self.log_message(f"找到 {len(version_ids)} 个本地版本，请选择要启动的版本")
            else:
                self.current_version = None
                self.log_message("未找到本地版本")
        except Exception as e:
            self.log_message(f"刷新版本失败: {e}")
    
    def download_version(self):
        """下载Minecraft版本"""
        selected_version = self.online_version_var.get()
        if not selected_version:
            messagebox.showerror("错误", "请选择要下载的版本")
            return
        
        def download_thread():
            try:
                # 下载版本
                version_data = self.version_manager.download_version(
                    selected_version, self.progress_callback)
                
                # 下载资源
                self.asset_downloader.download_assets(version_data, self.progress_callback)
                
                # 下载依赖库
                self.library_manager.download_libraries(version_data, self.progress_callback)
                
                self.log_message(f"版本 {selected_version} 下载完成")
                self.refresh_versions()
                
            except Exception as e:
                self.log_message(f"下载失败: {e}")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def check_java(self):
        """检查Java环境"""
        java_path = self.config.get_java_path()
        if java_path:
            self.java_path_var.set(java_path)
            self.log_message(f"找到Java: {java_path}")
        else:
            self.log_message("未找到Java运行时环境")
    
    def browse_game_dir(self):
        """浏览选择游戏目录"""
        directory = filedialog.askdirectory(initialdir=self.minecraft_path)
        if directory:
            self.game_dir_var.set(directory)
            self.minecraft_path = directory
            self.refresh_versions()
    
    def browse_java_path(self):
        """浏览选择Java路径"""
        file_path = filedialog.askopenfilename(
            title="选择Java可执行文件",
            filetypes=[("Java Executable", "javaw.exe"), ("All Files", "*.*")]
        )
        if file_path:
            self.java_path_var.set(file_path)
    
    def check_assets(self):
        """检查游戏资源完整性"""
        if not self.current_version:
            messagebox.showwarning("警告", "请先选择要检查的版本")
            return
        
        def check_thread():
            try:
                # 读取版本数据
                version_dir = Path(self.minecraft_path) / "versions" / self.current_version
                json_file = version_dir / f"{self.current_version}.json"
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                # 检查资源完整性
                success, message = self.asset_downloader.check_assets_integrity(
                    version_data, self.progress_callback)
                
                if success:
                    messagebox.showinfo("资源检查", f"✓ {message}")
                else:
                    if messagebox.askyesno("资源不完整", 
                                         f"{message}\n是否自动下载缺失的资源？"):
                        self.download_missing_assets()
                
            except Exception as e:
                messagebox.showerror("错误", f"资源检查失败: {e}")
        threading.Thread(target=check_thread, daemon=True).start()

    def check_dependencies(self):
        """检查游戏依赖是否完整"""
        try:
            if not self.current_version:
                return False, "请先选择版本"
            
            version_dir = Path(self.minecraft_path) / "versions" / self.current_version
            json_file = version_dir / f"{self.current_version}.json"
            
            if not json_file.exists():
                return False, f"版本配置文件不存在: {json_file}"
            
            # 检查游戏JAR文件
            jar_file = version_dir / f"{self.current_version}.jar"
            if not jar_file.exists():
                return False, f"游戏文件不存在: {jar_file}"
            
            # 检查资源完整性
            with open(json_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            self.log_message("检查游戏资源完整性...")
            assets_success, assets_message = self.asset_downloader.check_assets_integrity(
                version_data, self.progress_callback)
            
            if not assets_success:
                self.log_message(f"✗ 资源检查失败: {assets_message}")
                return False, f"资源不完整: {assets_message}"
            else:
                self.log_message(f"✓ {assets_message}")
            
            # 检查依赖库
            success, message = self.dependency_checker.check_version_dependencies(self.current_version)
            if success:
                self.log_message("✓ 依赖检查通过")
            else:
                self.log_message(f"✗ {message}")
            return success, message
        except Exception as e:
            self.log_message(f"依赖检查失败: {e}")
            return False, str(e)
    
    def _launch_game_thread(self):
        """在新线程中启动游戏"""
        try:
            # 检查Java环境
            java_path = self.config.get_java_path()
            if not java_path:
                self.log_message("错误: 未找到Java运行时环境")
                self.log_message("请手动设置Java路径或安装Java")
                self.launch_button['state'] = 'normal'
                return
            
            self.log_message(f"使用Java路径: {java_path}")
            
            # 验证Java版本
            try:
                result = subprocess.run([java_path, '-version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.log_message("Java版本检查通过")
                else:
                    self.log_message("警告: Java版本检查失败")
            except Exception as e:
                self.log_message(f"Java版本检查失败: {e}")
            
            # 读取版本数据
            version_dir = Path(self.minecraft_path) / "versions" / self.current_version
            json_file = version_dir / f"{self.current_version}.json"
            jar_file = version_dir / f"{self.current_version}.jar"
            
            if not json_file.exists():
                self.log_message(f"错误: 未找到版本配置文件 {json_file}")
                self.launch_button['state'] = 'normal'
                return
            
            if not jar_file.exists():
                self.log_message(f"错误: 未找到游戏文件 {jar_file}")
                self.launch_button['state'] = 'normal'
                return
            
            with open(json_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            # 检查资源完整性
            self.log_message("检查游戏资源完整性...")
            assets_success, assets_message = self.asset_downloader.check_assets_integrity(
                version_data, self.progress_callback)
            
            if not assets_success:
                self.log_message(f"资源不完整: {assets_message}")
                # 询问是否下载缺失资源
                if messagebox.askyesno("资源不完整", 
                                      f"{assets_message}\n是否自动下载缺失的资源？"):
                    self.log_message("开始下载缺失资源...")
                    self.asset_downloader.download_assets(version_data, self.progress_callback)
                    self.log_message("资源下载完成")
                else:
                    self.log_message("用户取消资源下载")
                    self.launch_button['state'] = 'normal'
                    return
            else:
                self.log_message(f"资源完整性检查通过: {assets_message}")
            
            # 检查依赖库是否完整
            self.log_message("检查依赖库完整性...")
            from library_manager import LibraryManager
            library_manager = LibraryManager(self.minecraft_path)
            
            # 强制重新下载所有依赖库
            self.log_message("下载依赖库...")
            library_manager.download_libraries(version_data, self.progress_callback)
            
            classpath = library_manager.get_classpath(version_data, self.minecraft_path)
            self.log_message(f"找到 {len(classpath)} 个库文件")
            
            # 构建启动命令
            cmd = self.config.get_launch_arguments(
                version_data, self.current_version, self.minecraft_path)
            
            self.log_message(f"启动命令: {' '.join(cmd[:10])}...")
            
            # 使用进程管理器启动游戏
            success = self.process_manager.start_process(
                cmd, 
                cwd=self.minecraft_path,
                callback=self._safe_log_message
            )
            
            if success:
                self.log_message("Minecraft 启动成功!")
                # 添加进程状态监控
                self._start_process_monitor()
            else:
                self.log_message("启动失败")
                self.launch_button['state'] = 'normal'
            
        except Exception as e:
            self.log_message(f"启动失败: {e}")
            import traceback
            self.log_message(f"详细错误信息: {traceback.format_exc()}")
            self.launch_button['state'] = 'normal'
    
    def _start_process_monitor(self):
        """启动进程状态监控"""
        def monitor():
            # 等待几秒后检查进程状态
            time.sleep(3)
            
            if self.process_manager.is_process_running():
                self.log_message("游戏进程运行中...")
                # 重新启用启动按钮
                self.launch_button['state'] = 'normal'
            else:
                self.log_message("游戏进程可能已退出")
                self.launch_button['state'] = 'normal'
        
        threading.Thread(target=monitor, daemon=True).start()
    
    def on_closing(self):
        """窗口关闭时的处理"""
        # 如果游戏正在运行，询问是否终止
        if self.process_manager.is_process_running():
            if messagebox.askyesno("确认", "游戏正在运行，确定要关闭启动器吗？"):
                try:
                    self.process_manager.terminate_process()
                except:
                    pass
                finally:
                    self.root.destroy()
        else:
            self.root.destroy()
    
    def _safe_log_message(self, message):
        """线程安全的日志消息添加"""
        def update_log():
            try:
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
                # 限制日志长度，避免内存占用过大
                lines = int(self.log_text.index('end-1c').split('.')[0])
                if lines > 1000:
                    self.log_text.delete('1.0', f'{lines-500}.0')
            except Exception:
                pass  # 忽略日志更新错误
        
        # 在主线程中更新GUI
        if self.root and self.root.winfo_exists():
            self.root.after(0, update_log)
    
    def launch_game(self):
        """启动Minecraft游戏 - 修复版本"""
        # 获取当前选择的版本
        selected_version = self.version_var.get()
        if not selected_version:
            messagebox.showerror("错误", "请选择要启动的版本")
            return
        
        # 更新当前版本变量
        self.current_version = selected_version
        
        # 禁用启动按钮，避免重复启动
        self.launch_button['state'] = 'disabled'
        
        # 清空日志
        self.log_text.delete('1.0', tk.END)
        
        # 直接启动游戏，让_launch_game_thread统一处理所有检查
        threading.Thread(target=self._launch_game_thread, daemon=True).start()
    
    def download_missing_assets(self):
        """下载缺失的游戏资源"""
        if not self.current_version:
            return
        
        def download_thread():
            try:
                # 读取版本数据
                version_dir = Path(self.minecraft_path) / "versions" / self.current_version
                json_file = version_dir / f"{self.current_version}.json"
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                # 下载资源
                self.asset_downloader.download_assets(version_data, self.progress_callback)
                self.log_message("游戏资源下载完成")
                
            except Exception as e:
                self.log_message(f"下载资源失败: {e}")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_missing_dependencies(self):
        """下载缺失的依赖"""
        if not self.current_version:
            return
        
        def download_thread():
            try:
                # 读取版本数据
                version_dir = Path(self.minecraft_path) / "versions" / self.current_version
                json_file = version_dir / f"{self.current_version}.json"
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                # 下载依赖库
                self.library_manager.download_libraries(version_data, self.progress_callback)
                self.log_message("依赖库下载完成")
                
                # 重新检查依赖
                self.check_dependencies()
                
            except Exception as e:
                self.log_message(f"下载依赖失败: {e}")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def run(self):
        """运行启动器"""
        self.root.mainloop()

if __name__ == "__main__":
    launcher = MinecraftLauncher()
    launcher.run()