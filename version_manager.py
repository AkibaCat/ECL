#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本管理器 - 负责Minecraft版本的管理和下载
"""

import json
import os
import requests
from pathlib import Path

class VersionManager:
    def __init__(self, minecraft_path):
        self.minecraft_path = Path(minecraft_path)
        self.versions_path = self.minecraft_path / "versions"
        self.versions_path.mkdir(parents=True, exist_ok=True)
    
    def get_available_versions(self):
        """获取本地可用的版本列表"""
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
    
    def download_version(self, version_id):
        """下载指定版本的Minecraft"""
        try:
            # 获取版本清单
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            response = requests.get(manifest_url)
            manifest = response.json()
            
            # 查找指定版本
            version_info = None
            for version in manifest['versions']:
                if version['id'] == version_id:
                    version_info = version
                    break
            
            if not version_info:
                raise Exception(f"未找到版本 {version_id}")
            
            # 下载版本JSON文件
            version_response = requests.get(version_info['url'])
            version_data = version_response.json()
            
            # 创建版本目录
            version_dir = self.versions_path / version_id
            version_dir.mkdir(exist_ok=True)
            
            # 保存版本JSON
            json_file = version_dir / f"{version_id}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2)
            
            # 下载客户端JAR文件
            client_url = version_data['downloads']['client']['url']
            client_jar = version_dir / f"{version_id}.jar"
            self._download_file(client_url, client_jar)
            
            return True
            
        except Exception as e:
            print(f"下载版本 {version_id} 失败: {e}")
            return False
    
    def _download_file(self, url, file_path):
        """下载文件"""
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # 可以在这里添加进度回调
        
        print(f"下载完成: {file_path.name}")