# 项目名称：Minecraft版本查看器
# 本程序用于获取Minecraft版本列表，并提供下载功能
# 作者：AutumnLeaves
# 版本：25w11d
# 上一次的修改时间：2025/3/16 12:56
# 上一次的修改内容：
# - 添加版本数量显示

# 免责声明：本程序仅供学习和研究使用，不得用于商业用途。作者不对因使用本程序而导致的任何损失或损害承担责任

import sys
import requests
import datetime
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QVBoxLayout, QWidget, QTabWidget, QListWidgetItem, QDialog, QLabel, QVBoxLayout, QPushButton,  QFileDialog, QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor
import json
from pathlib import Path

class VersionDetailDialog(QDialog):
    def __init__(self, version_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle('版本详情')
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        # 添加版本信息展示
        self.name_label = QLabel(f"版本名称: {version_info['id']}")
        
        # 转换时间为北京时间
        release_time = datetime.datetime.strptime(version_info['releaseTime'], "%Y-%m-%dT%H:%M:%S%z")
        beijing_time = release_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M")
        
        self.time_label = QLabel(f"发布时间: {formatted_time}")
        self.type_label = QLabel(f"版本类型: {version_info['type']}")
        
        layout.addWidget(self.name_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.type_label)
        
        # 添加版本信息按钮
        self.info_button = QPushButton('版本信息')
        self.info_button.clicked.connect(lambda: self.open_wiki(version_info['id'], version_info['type']))
        layout.addWidget(self.info_button)
        
        # 添加下载按钮
        self.client_button = QPushButton('下载客户端')
        self.client_button.clicked.connect(lambda: self.download_client(version_info))
        layout.addWidget(self.client_button)
        self.server_button = QPushButton('下载服务端')
        self.server_button.clicked.connect(lambda: self.download_server(version_info))
        layout.addWidget(self.server_button)
        
        self.setLayout(layout)

    def open_wiki(self, version_id, version_type):
        """打开Minecraft Wiki页面"""
        import webbrowser
        if version_type == "release":
            url = f"https://zh.minecraft.wiki/w/Java版{version_id}"
        else:
            url = f"https://zh.minecraft.wiki/w/{version_id}"
        webbrowser.open(url)
    
    def download_client(self, version_info):
        """下载客户端文件"""
        try:
            # 获取版本详情
            version_url = version_info['url']
            response = requests.get(version_url)
            response.raise_for_status()
            version_details = response.json()
    
            # 获取下载链接
            download_url = version_details['downloads']['client']['url']
            
            # 创建下载目录
            download_dir = Path(".minecraft/versions") / version_info['id']
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建进度对话框
            progress = QProgressDialog("正在下载客户端...", "取消", 0, 100, self)
            progress.setWindowTitle("下载进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()
            
            # 下载文件
            file_path = download_dir / f"{version_info['id']}.jar"
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if progress.wasCanceled():
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress.setValue(int(100 * downloaded_size / total_size))
            
            # 保存API的URL内容
            api_file_path = download_dir / f"{version_info['id']}.json"
            with open(api_file_path, 'w', encoding='utf-8') as f:
                json.dump(version_details, f, indent=4)
            
            if not progress.wasCanceled():
                # 使用QMessageBox显示下载完成信息
                QMessageBox.information(self, "下载完成", 
                                     f"客户端 {version_info['id']} 下载成功")
                print(f"下载成功: {file_path}")

        # 捕获异常并显示错误信息
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "下载失败", f"下载失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "发生错误", f"发生错误: {e}")

    def download_server(self, version_info):
        """下载服务端文件"""
        try:
            # 获取版本详情
            version_url = version_info['url']
            response = requests.get(version_url)
            response.raise_for_status()
            version_details = response.json()
    
            # 获取下载链接
            download_url = version_details['downloads']['server']['url']
            
            # 让用户选择保存位置
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存服务端文件",
                f"{version_info['id']}.jar",
                "JAR 文件 (*.jar)"
            )
            
            if not save_path:  # 用户取消选择
                return

            # 创建进度对话框
            progress = QProgressDialog("正在下载服务端...", "取消", 0, 100, self)
            progress.setWindowTitle("下载进度")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.show()

            # 下载文件
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if progress.wasCanceled():
                            break
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress.setValue(int(100 * downloaded_size / total_size))

            if not progress.wasCanceled():
                # 使用QMessageBox显示下载完成信息
                QMessageBox.information(self, "下载完成", 
                                     f"服务端 {version_info['id']} 下载成功")
                print(f"下载成功: {save_path}")

        # 捕获异常并显示错误信息
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "下载失败", f"下载失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "发生错误", f"发生错误: {e}")

class VersionWindow(QMainWindow):
    def __init__(self):
        """初始化窗口"""
        super().__init__()
        self.setWindowTitle('Minecraft版本列表')
        self.setMinimumSize(880, 550)
        self.setGeometry(300, 300, 600, 500)
        
        # 创建标签页容器
        self.tabs = QTabWidget()
        
        # 创建不同分类的列表控件
        self.category_lists = {
            'release': QListWidget(),
            'snapshot': QListWidget(),
            'fool': QListWidget(),
            'ancient': QListWidget()
        }
        
        # 添加标签页
        for category, widget in self.category_lists.items():
            tab = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(widget)
            tab.setLayout(layout)
            self.tabs.addTab(tab, self.get_category_label(category))
        
        # 设置中心部件
        self.setCentralWidget(self.tabs)
        self.load_versions()

    def get_category_label(self, category):
        """根据分类获取标签"""
        labels = {
            'release': '正式版',
            'snapshot': '预览版',
            'fool': '愚人节版',
            'ancient': '远古版',
        }
        # 获取当前分类的版本数量
        count = self.category_lists[category].count() // 2  # 除以2因为每个版本后有一个分割线
        return f"{labels.get(category, '其他')} ({count})"

    def get_cache_path(self):
        """获取缓存文件路径"""
        cache_dir = Path.home() / ".amcl_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / "version_cache.json"

    def load_versions(self):
        """加载版本数据"""
        try:
            # 尝试从缓存加载
            cache_path = self.get_cache_path()
            if cache_path.exists():
                cache_time = cache_path.stat().st_mtime
                # 如果缓存时间在1小时内，使用缓存
                if time.time() - cache_time < 3600:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.process_versions(data)
                        return

            # 从API获取数据
            mojangapi = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest.json')
            bmclapi = requests.get('https://bmclapi2.bangbang93.com/mc/game/version_manifest.json')
            response = bmclapi if bmclapi.status_code == 200 else mojangapi
            response.raise_for_status()
            data = response.json()

            # 保存到缓存
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)

            self.process_versions(data)

        except requests.exceptions.RequestException as e:
            print(f"获取版本数据失败: {e}")
        except Exception as e:
            print(f"处理版本数据失败: {e}")

    def process_versions(self, data):
        """处理版本数据"""
        for version_manifest in data['versions']:
            release_time = version_manifest['releaseTime']
            utc_time = datetime.datetime.strptime(release_time, "%Y-%m-%dT%H:%M:%S%z")
            # 判断是否为特殊愚人节版本ID
            fool_version_ids = {"3d shareware v1.34","1.RV-Pre1","15w14a","22w13oneblockatatime","23w13a_or_b","24w14potato"}
            is_special_fool_version = version_manifest['id'] in fool_version_ids
            # 4/1 自动视作愚人节版
            is_fool_version = utc_time.month == 4 and utc_time.day == 1
            
            # 根据版本类型分类（正式版、预览版、愚人节版、远古版），优先分类愚人节版防止被误判为预览版
            category = 'fool' if is_fool_version or is_special_fool_version else \
                       'release' if version_manifest['type'] == 'release' else \
                       'snapshot' if version_manifest['type'] == 'snapshot' else \
                       'ancient'
            
            if category in self.category_lists:
                # 将UTC时间转换为北京时间
                beijing_time = utc_time.astimezone(datetime.timezone(datetime.timedelta(hours=8)))
                formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M")
                item_text = f"{version_manifest['id']}\n{formatted_time}"

                # 创建分割线
                separator = QListWidgetItem()
                separator.setFlags(Qt.NoItemFlags)  # 使分割线不可选择
                separator.setBackground(QColor(200, 200, 200))  # 设置分割线颜色
                separator.setSizeHint(QSize(0, 1))  # 设置分割线高度为1像素
                
                # 添加版本信息和分割线
                self.category_lists[category].addItem(item_text)
                self.category_lists[category].addItem(separator)
        
        # 为每个列表添加点击事件
        for category, widget in self.category_lists.items():
            widget.itemClicked.connect(self.show_version_detail)

        for category in self.category_lists:
            self.tabs.setTabText(
                list(self.category_lists.keys()).index(category),
                self.get_category_label(category)
            )
        
    def show_version_detail(self, item):
        """显示版本详细信息"""
        version_id = item.text().split('\n')[0]  # 获取版本ID
        
        # 从缓存中查找版本信息
        cache_path = self.get_cache_path()
        if cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for version in data['versions']:
                    if version['id'] == version_id:
                        # 显示详情对话框
                        dialog = VersionDetailDialog(version, self)
                        dialog.exec_()
                        break

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VersionWindow()
    window.show()
    sys.exit(app.exec_())