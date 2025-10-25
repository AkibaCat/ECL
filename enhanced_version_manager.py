#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版本管理器 - 实现真实的Minecraft版本下载功能
"""

import json
import os
import requests
import threading
from pathlib import Path
from urllib.parse import urljoin

class EnhancedVersionManager:
    def __init__(self, minecraft_path, progress_callback=None):
        self.minecraft_path = Path(minecraft_path)
        self.versions_path = self.minecraft_path / "versions"
        self.versions_path.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
    
    def get_version_manifest(self):
        """获取版本清单"""
        try:
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            response = requests.get(manifest_url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取版本清单失败: {e}")
    
    def get_available_versions(self, version_type=None):
        """获取可用的版本列表"""
        manifest = self.get_version_manifest()
        versions = []
        
        for version in manifest['versions']:
            if version_type and version['type'] != version_type:
                continue
            versions.append({
                'id': version['id'],
                'type': version['type'],
                'release_time': version['releaseTime'],
                'url': version['url']
            })
        
        return versions
    
    def get_local_versions(self):
        """获取本地已安装的版本"""
        versions = []
        for version_dir in self.versions_path.iterdir():
            if version_dir.is_dir():
                json_file = version_dir / f"{version_dir.name}.json"
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            version_data = json.load(f)
                            versions.append({
                                'id': version_data.get('id', version_dir.name),
                                'type': version_data.get('type', 'release'),
                                'release_time': version_data.get('releaseTime', ''),
                                'path': str(version_dir)
                            })
                    except Exception as e:
                        print(f"读取版本 {version_dir.name} 信息失败: {e}")
        return versions
    
    def download_version(self, version_id, progress_callback=None):
        """下载指定版本的Minecraft"""
        try:
            if progress_callback:
                progress_callback(f"开始下载版本 {version_id}", 0)
            
            # 获取版本清单
            manifest = self.get_version_manifest()
            
            # 查找指定版本
            version_info = None
            for version in manifest['versions']:
                if version['id'] == version_id:
                    version_info = version
                    break
            
            if not version_info:
                raise Exception(f"未找到版本 {version_id}")
            
            if progress_callback:
                progress_callback(f"获取版本信息", 10)
            
            # 下载版本JSON文件
            version_response = requests.get(version_info['url'])
            version_response.raise_for_status()
            version_data = version_response.json()
            
            # 创建版本目录
            version_dir = self.versions_path / version_id
            version_dir.mkdir(exist_ok=True)
            
            if progress_callback:
                progress_callback(f"保存版本配置", 20)
            
            # 保存版本JSON
            json_file = version_dir / f"{version_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2)
            
            # 下载客户端JAR文件
            client_url = version_data['downloads']['client']['url']
            client_jar = version_dir / f"{version_id}.jar"
            
            if progress_callback:
                progress_callback(f"下载游戏文件", 30)
            
            self._download_file_with_progress(client_url, client_jar, 
                                            lambda p: progress_callback(f"下载游戏文件", 30 + p * 0.4) if progress_callback else None)
            
            return version_data
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"下载失败: {e}", -1)
            raise Exception(f"下载版本 {version_id} 失败: {e}")
    
    def _download_file_with_progress(self, url, file_path, progress_callback=None):
        """带进度显示的文件下载"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress)
        
        if progress_callback:
            progress_callback(100)