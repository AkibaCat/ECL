"""
版本列表管理器模块
集成version_list.pyw的功能到启动器中
"""

import requests
import datetime
import time
import json
from pathlib import Path
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


class VersionListManager:
    """版本列表管理器类"""
    
    def __init__(self, minecraft_path, progress_callback=None):
        self.minecraft_path = Path(minecraft_path)
        self.progress_callback = progress_callback or self._default_progress_callback
        self.versions_cache = {}
        self.cache_file = Path.home() / ".amcl_cache" / "version_cache.json"
        
    def _default_progress_callback(self, message, progress):
        """默认进度回调函数"""
        pass
    
    def get_cache_path(self):
        """获取缓存文件路径"""
        cache_dir = Path.home() / ".amcl_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / "version_cache.json"
    
    def load_versions_from_api(self, force_refresh=False):
        """从API加载版本数据"""
        try:
            # 尝试从缓存加载
            cache_path = self.get_cache_path()
            if not force_refresh and cache_path.exists():
                cache_time = cache_path.stat().st_mtime
                # 如果缓存时间在1小时内，使用缓存
                if time.time() - cache_time < 3600:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return self.process_versions_data(data)
            
            # 从API获取数据
            response = requests.get('https://bmclapi2.bangbang93.com/mc/game/version_manifest.json', timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 保存到缓存
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            
            return self.process_versions_data(data)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"获取版本数据失败: {e}")
        except Exception as e:
            raise Exception(f"处理版本数据失败: {e}")
    
    def process_versions_data(self, data):
        """处理版本数据"""
        categorized_versions = {
            'release': [],
            'snapshot': [],
            'fool': [],
            'ancient': []
        }
        
        for version_manifest in data['versions']:
            release_time = version_manifest['releaseTime']
            utc_time = datetime.datetime.strptime(release_time, "%Y-%m-%dT%H:%M:%S%z")
            
            # 判断是否为特殊愚人节版本ID
            fool_version_ids = {
                "15w14a", "1.RV-Pre1", "3d shareware v1.34", "20w14infinite", "22w13oneblockatatime", "23w13a_or_b", "24w14potato", "25w14craftmine"
            }
            is_special_fool_version = version_manifest['id'] in fool_version_ids
            # 4/1 自动视作愚人节版
            is_fool_version = utc_time.month == 4 and utc_time.day == 1
            
            # 根据版本类型分类
            category = 'fool' if is_fool_version or is_special_fool_version else \
                       'release' if version_manifest['type'] == 'release' else \
                       'snapshot' if version_manifest['type'] == 'snapshot' else \
                       'ancient'
            
            if category in categorized_versions:
                # 将UTC时间转换为北京时间
                beijing_time = utc_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
                formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M")
                
                version_info = {
                    'id': version_manifest['id'],
                    'type': version_manifest['type'],
                    'release_time': formatted_time,
                    'url': version_manifest['url'],
                    'original_data': version_manifest
                }
                
                categorized_versions[category].append(version_info)
        
        return categorized_versions
    
    def get_category_label(self, category):
        """根据分类获取标签"""
        labels = {
            'release': '正式版',
            'snapshot': '预览版',
            'fool': '愚人节版',
            'ancient': '远古版',
        }
        return labels.get(category, '其他')
    
    def download_client_version(self, version_info, progress_callback=None):
        """下载客户端版本"""
        if progress_callback:
            progress_callback(f"开始下载 {version_info['id']}", 0)
        
        try:
            # 获取版本详情
            version_url = version_info['url']
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            version_details = response.json()
            
            # 获取下载链接
            download_url = version_details['downloads']['client']['url']
            
            # 创建下载目录
            download_dir = self.minecraft_path / "versions" / version_info['id']
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载文件
            file_path = download_dir / f"{version_info['id']}.jar"
            
            if progress_callback:
                progress_callback(f"下载客户端文件...", 10)
            
            # 使用线程下载文件
            success = self._download_file(download_url, file_path, progress_callback)
            
            if success:
                # 保存版本JSON文件
                json_file_path = download_dir / f"{version_info['id']}.json"
                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(version_details, f, indent=4)
                
                if progress_callback:
                    progress_callback(f"版本 {version_info['id']} 下载完成", 100)
                
                return True, f"客户端 {version_info['id']} 下载成功"
            else:
                return False, "下载失败"
                
        except Exception as e:
            return False, f"下载失败: {e}"
    
    def download_server_version(self, version_info, save_path=None):
        """下载服务端版本"""
        try:
            # 获取版本详情
            version_url = version_info['url']
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            version_details = response.json()
            
            # 获取下载链接
            download_url = version_details['downloads']['server']['url']
            
            if not save_path:
                # 默认保存路径
                save_path = Path.cwd() / f"{version_info['id']}_server.jar"
            
            # 下载文件
            success = self._download_file(download_url, save_path)
            
            if success:
                return True, f"服务端 {version_info['id']} 下载成功"
            else:
                return False, "下载失败"
                
        except Exception as e:
            return False, f"下载失败: {e}"
    
    def _download_file(self, url, file_path, progress_callback=None):
        """下载文件的通用方法"""
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                # 确保目录存在
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # 过滤掉保持连接的块
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0 and progress_callback:
                                progress = int(100 * downloaded_size / total_size)
                                progress_callback(f"下载进度: {progress}%", progress)
                
                return True
                
        except Exception as e:
            print(f"下载文件失败: {e}")
            return False
    
    def open_wiki_page(self, version_id, version_type):
        """打开Minecraft Wiki页面"""
        import webbrowser
        if version_type == "release":
            url = f"https://zh.minecraft.wiki/w/Java版{version_id}"
        else:
            url = f"https://zh.minecraft.wiki/w/{version_id}"
        webbrowser.open(url)


class VersionListDialog:
    """版本列表对话框类（基于tkinter）"""
    
    def __init__(self, parent, version_manager, minecraft_path):
        self.parent = parent
        self.version_manager = version_manager
        self.minecraft_path = minecraft_path
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Minecraft版本列表")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_versions()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Minecraft版本列表", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=10)
        
        # 创建标签页容器
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建不同分类的列表控件
        self.category_frames = {}
        self.category_lists = {}
        
        categories = ['release', 'snapshot', 'fool', 'ancient']
        for category in categories:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=self.version_manager.get_category_label(category))
            
            # 创建滚动框架
            scroll_frame = ttk.Frame(frame)
            scroll_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # 创建列表框和滚动条
            listbox_frame = ttk.Frame(scroll_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True)
            
            listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE, font=("Arial", 10))
            scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 绑定双击事件
            listbox.bind('<Double-Button-1>', lambda e, cat=category: self.show_version_detail(cat))
            
            self.category_frames[category] = frame
            self.category_lists[category] = listbox
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="刷新列表", 
                  command=self.refresh_versions).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="查看详情", 
                  command=self.show_selected_version_detail).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="关闭", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_versions(self):
        """加载版本数据"""
        try:
            categorized_versions = self.version_manager.load_versions_from_api()
            
            for category, versions in categorized_versions.items():
                listbox = self.category_lists.get(category)
                if listbox:
                    listbox.delete(0, tk.END)
                    for version in versions:
                        display_text = f"{version['id']} - {version['release_time']}"
                        listbox.insert(tk.END, display_text)
                        # 存储版本信息
                        listbox.version_data = getattr(listbox, 'version_data', {})
                        listbox.version_data[display_text] = version
            
        except Exception as e:
            messagebox.showerror("错误", f"加载版本数据失败: {e}")
    
    def refresh_versions(self):
        """刷新版本列表"""
        try:
            categorized_versions = self.version_manager.load_versions_from_api(force_refresh=True)
            
            for category, versions in categorized_versions.items():
                listbox = self.category_lists.get(category)
                if listbox:
                    listbox.delete(0, tk.END)
                    for version in versions:
                        display_text = f"{version['id']} - {version['release_time']}"
                        listbox.insert(tk.END, display_text)
                        # 存储版本信息
                        listbox.version_data = getattr(listbox, 'version_data', {})
                        listbox.version_data[display_text] = version
            
            messagebox.showinfo("成功", "版本列表已刷新")
            
        except Exception as e:
            messagebox.showerror("错误", f"刷新版本列表失败: {e}")
    
    def get_selected_version(self):
        """获取选中的版本"""
        current_tab = self.notebook.index(self.notebook.select())
        categories = ['release', 'snapshot', 'fool', 'ancient']
        
        if 0 <= current_tab < len(categories):
            category = categories[current_tab]
            listbox = self.category_lists.get(category)
            
            if listbox and listbox.curselection():
                selected_index = listbox.curselection()[0]
                display_text = listbox.get(selected_index)
                return listbox.version_data.get(display_text)
        
        return None
    
    def show_selected_version_detail(self):
        """显示选中版本的详情"""
        version_info = self.get_selected_version()
        if version_info:
            self.show_version_detail_dialog(version_info)
        else:
            messagebox.showwarning("警告", "请先选择一个版本")
    
    def show_version_detail(self, category):
        """显示版本详情（双击事件）"""
        listbox = self.category_lists.get(category)
        if listbox and listbox.curselection():
            selected_index = listbox.curselection()[0]
            display_text = listbox.get(selected_index)
            version_info = listbox.version_data.get(display_text)
            
            if version_info:
                self.show_version_detail_dialog(version_info)
    
    def show_version_detail_dialog(self, version_info):
        """显示版本详情对话框"""
        detail_dialog = tk.Toplevel(self.dialog)
        detail_dialog.title(f"版本详情 - {version_info['id']}")
        detail_dialog.geometry("400x300")
        detail_dialog.transient(self.dialog)
        detail_dialog.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(detail_dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 版本信息
        info_frame = ttk.LabelFrame(main_frame, text="版本信息", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text=f"版本ID: {version_info['id']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"版本类型: {version_info['type']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"发布时间: {version_info['release_time']}").pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="查看Wiki", 
                  command=lambda: self.version_manager.open_wiki_page(version_info['id'], version_info['type'])).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="下载客户端", 
                  command=lambda: self.download_client(version_info)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="下载服务端", 
                  command=lambda: self.download_server(version_info)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="关闭", 
                  command=detail_dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def download_client(self, version_info):
        """下载客户端"""
        def download_thread():
            try:
                success, message = self.version_manager.download_client_version(version_info)
                if success:
                    messagebox.showinfo("成功", message)
                else:
                    messagebox.showerror("错误", message)
            except Exception as e:
                messagebox.showerror("错误", f"下载失败: {e}")
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_server(self, version_info):
        """下载服务端"""
        save_path = filedialog.asksaveasfilename(
            title="保存服务端文件",
            defaultextension=".jar",
            filetypes=[("JAR 文件", "*.jar"), ("所有文件", "*.*")],
            initialfile=f"{version_info['id']}_server.jar"
        )
        
        if save_path:
            def download_thread():
                try:
                    success, message = self.version_manager.download_server_version(version_info, save_path)
                    if success:
                        messagebox.showinfo("成功", message)
                    else:
                        messagebox.showerror("错误", message)
                except Exception as e:
                    messagebox.showerror("错误", f"下载失败: {e}")
            
            threading.Thread(target=download_thread, daemon=True).start()