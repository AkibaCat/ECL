#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源下载器 - 负责游戏资源的下载和管理
"""

import hashlib
import json
import os
import requests
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urljoin

class AssetDownloader:
    def __init__(self, minecraft_path, progress_callback=None, max_workers=8):
        self.minecraft_path = Path(minecraft_path)
        self.assets_path = self.minecraft_path / "assets"
        self.assets_path.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.max_workers = max_workers  # 最大线程数
        self.download_queue = queue.Queue()
        self.downloaded_count = 0
        self.total_count = 0
        self.lock = threading.Lock()
    
    def check_assets_integrity(self, version_data, progress_callback=None):
        """检查游戏资源完整性"""
        try:
            if progress_callback:
                progress_callback("开始检查游戏资源完整性", 0)
            
            assets_index = version_data.get('assetIndex', {})
            assets_id = assets_index.get('id', '')
            
            if not assets_id:
                return True, "版本没有资源索引，跳过资源检查"
            
            # 检查资源索引文件是否存在
            index_path = self.assets_path / "indexes" / f"{assets_id}.json"
            if not index_path.exists():
                return False, f"资源索引文件不存在: {index_path}"
            
            # 读取资源索引
            with open(index_path, 'r', encoding='utf-8') as f:
                assets_index_data = json.load(f)
            
            # 检查资源文件
            objects = assets_index_data.get('objects', {})
            total = len(objects)
            missing_files = []
            corrupted_files = []
            checked = 0
            
            if progress_callback:
                progress_callback(f"检查 {total} 个资源文件", 10)
            
            for asset_name, asset_info in objects.items():
                hash_value = asset_info['hash']
                size = asset_info.get('size', 0)
                
                asset_path = self.assets_path / "objects" / hash_value[:2] / hash_value
                
                # 检查文件是否存在
                if not asset_path.exists():
                    missing_files.append(asset_name)
                else:
                    # 检查文件完整性（哈希值）
                    file_hash = self._get_file_hash(asset_path)
                    if file_hash != hash_value:
                        corrupted_files.append(asset_name)
                
                checked += 1
                progress = 10 + (checked / total) * 90
                
                if progress_callback and checked % 100 == 0:  # 每100个文件更新一次进度
                    progress_callback(f"检查资源文件 ({checked}/{total})", progress)
            
            # 生成检查结果
            if missing_files and corrupted_files:
                result = f"资源不完整: 缺失 {len(missing_files)} 个文件, 损坏 {len(corrupted_files)} 个文件"
                return False, result
            elif missing_files:
                result = f"资源不完整: 缺失 {len(missing_files)} 个文件"
                return False, result
            elif corrupted_files:
                result = f"资源不完整: 损坏 {len(corrupted_files)} 个文件"
                return False, result
            else:
                if progress_callback:
                    progress_callback("资源完整性检查通过", 100)
                return True, f"所有 {total} 个资源文件完整"
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"资源检查失败: {e}", -1)
            return False, f"资源检查失败: {e}"
    
    def download_assets(self, version_data, progress_callback=None):
        """下载游戏资源 - 多线程版本"""
        try:
            if progress_callback:
                progress_callback("开始下载游戏资源", 0)
            
            assets_index = version_data.get('assetIndex', {})
            assets_url = assets_index.get('url', '')
            assets_id = assets_index.get('id', '')
            
            if not assets_url:
                raise Exception("未找到资源索引URL")
            
            # 下载资源索引
            index_path = self.assets_path / "indexes" / f"{assets_id}.json"
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            if progress_callback:
                progress_callback("下载资源索引", 10)
            
            response = requests.get(assets_url)
            response.raise_for_status()
            assets_index_data = response.json()
            
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(assets_index_data, f, indent=2)
            
            # 准备多线程下载资源文件
            objects = assets_index_data.get('objects', {})
            total_files = len(objects)
            self.total_count = total_files
            self.downloaded_count = 0
            
            if progress_callback:
                progress_callback(f"扫描 {total_files} 个资源文件", 20)
            
            # 创建需要下载的文件列表
            download_tasks = []
            existing_files = 0
            corrupted_files = 0
            
            for asset_name, asset_info in objects.items():
                hash_value = asset_info['hash']
                size = asset_info.get('size', 0)
                
                asset_path = self.assets_path / "objects" / hash_value[:2] / hash_value
                asset_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 检查文件是否需要下载
                if asset_path.exists():
                    # 验证文件完整性
                    current_hash = self._get_file_hash(asset_path)
                    if current_hash == hash_value:
                        existing_files += 1
                        continue  # 文件已存在且完整，跳过下载
                    else:
                        corrupted_files += 1
                        # 文件存在但损坏，需要重新下载
                        print(f"文件损坏，重新下载: {asset_path.name}")
                else:
                    # 文件不存在，需要下载
                    pass
                
                url = f"https://resources.download.minecraft.net/{hash_value[:2]}/{hash_value}"
                download_tasks.append((url, asset_path, hash_value))
            
            # 统计信息
            need_download_count = len(download_tasks)
            
            if progress_callback:
                progress_callback(f"跳过 {existing_files} 个已存在文件，需要下载 {need_download_count} 个文件", 30)
            
            if not download_tasks:
                if progress_callback:
                    if corrupted_files > 0:
                        progress_callback(f"所有资源文件已存在（{existing_files}个完整，{corrupted_files}个损坏已修复）", 100)
                    else:
                        progress_callback(f"所有 {total_files} 个资源文件已存在且完整", 100)
                return True
            
            # 使用线程池并行下载
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有下载任务
                future_to_task = {
                    executor.submit(self._download_file_threaded, url, file_path, hash_value): (url, file_path, hash_value)
                    for url, file_path, hash_value in download_tasks
                }
                
                # 处理完成的任务
                completed_count = 0
                for future in as_completed(future_to_task):
                    url, file_path, hash_value = future_to_task[future]
                    try:
                        result = future.result()
                        if result:
                            with self.lock:
                                completed_count += 1
                                self.downloaded_count = existing_files + completed_count
                                progress = 30 + (completed_count / need_download_count) * 70
                                
                                if progress_callback:
                                    if completed_count % 5 == 0 or completed_count == need_download_count:  # 每5个文件或完成时更新进度
                                        progress_callback(f"下载进度 ({completed_count}/{need_download_count}) - 总计 ({self.downloaded_count}/{total_files})", progress)
                    except Exception as e:
                        print(f"下载失败 {url}: {e}")
                        # 记录错误但继续处理其他文件
            
            if progress_callback:
                final_existing = existing_files + (need_download_count - completed_count)
                progress_callback(f"下载完成！已存在: {final_existing}个, 本次下载: {completed_count}个, 失败: {need_download_count - completed_count}个", 100)
            
            return completed_count == need_download_count
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"资源下载失败: {e}", -1)
            raise Exception(f"下载资源失败: {e}")
    
    def _download_file_threaded(self, url, file_path, expected_hash=None):
        """线程安全的文件下载方法"""
        try:
            # 检查文件是否已存在且完整
            if file_path.exists() and expected_hash:
                current_hash = self._get_file_hash(file_path)
                if current_hash == expected_hash:
                    return True
            
            # 下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 创建临时文件
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 验证文件完整性
            if expected_hash:
                downloaded_hash = self._get_file_hash(temp_path)
                if downloaded_hash != expected_hash:
                    os.remove(temp_path)
                    raise Exception(f"文件哈希值不匹配: 期望 {expected_hash}, 实际 {downloaded_hash}")
            
            # 重命名临时文件为正式文件
            os.replace(temp_path, file_path)
            return True
            
        except Exception as e:
            # 清理临时文件
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
    
    def _get_file_hash(self, file_path):
        """计算文件SHA1哈希值"""
        hasher = hashlib.sha1()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _download_file(self, url, file_path):
        """单线程下载文件（保持兼容性）"""
        return self._download_file_threaded(url, file_path)