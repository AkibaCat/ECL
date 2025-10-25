#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
库文件管理器 - 负责游戏依赖库的管理
"""

import json
import os
import platform
import requests
import threading
from pathlib import Path
from urllib.parse import urljoin

class LibraryManager:
    def __init__(self, minecraft_path, progress_callback=None):
        self.minecraft_path = Path(minecraft_path)
        self.libraries_path = self.minecraft_path / "libraries"
        self.libraries_path.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
    
    def download_libraries(self, version_data, progress_callback=None):
        """下载游戏依赖库"""
        try:
            if progress_callback:
                progress_callback("开始下载依赖库", 0)
            
            libraries = version_data.get('libraries', [])
            libraries_to_download = []
            
            # 筛选需要下载的库
            for library in libraries:
                if self._should_download_library(library):
                    libraries_to_download.append(library)
            
            total = len(libraries_to_download)
            downloaded = 0
            
            for library in libraries_to_download:
                # 获取库信息
                library_info = self._get_library_info(library)
                if not library_info:
                    continue
                
                library_path = library_info.get('path', '')
                library_url = library_info.get('url', '')
                
                if not library_path or not library_url:
                    continue
                
                target_path = self.libraries_path / library_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not target_path.exists():
                    if progress_callback:
                        progress_callback(f"下载库文件: {library_path.split('/')[-1]}", 
                                        (downloaded / total) * 100)
                    
                    self._download_file(library_url, target_path)
                
                downloaded += 1
            
            if progress_callback:
                progress_callback("依赖库下载完成", 100)
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"依赖库下载失败: {e}", -1)
            raise Exception(f"下载依赖库失败: {e}")
    
    def _get_library_info(self, library):
        """获取库的下载信息"""
        # 优先使用artifact下载信息
        artifact_info = library.get('downloads', {}).get('artifact', {})
        if artifact_info:
            return artifact_info
        
        # 检查是否有classifiers（新版Minecraft使用）
        classifiers = library.get('downloads', {}).get('classifiers', {})
        if classifiers:
            # 根据平台选择合适的classifier
            system_os = platform.system().lower()
            system_arch = platform.machine().lower()
            
            # 优先选择natives相关的库
            if system_os == 'windows':
                if 'natives-windows' in classifiers:
                    return classifiers['natives-windows']
                elif 'natives-windows-64' in classifiers and '64' in system_arch:
                    return classifiers['natives-windows-64']
                elif 'natives-windows-32' in classifiers and '32' in system_arch:
                    return classifiers['natives-windows-32']
            
            # 如果没有特定平台的库，使用第一个可用的库
            for classifier_name, classifier_info in classifiers.items():
                if classifier_info:
                    return classifier_info
        
        # 如果没有artifact信息，尝试从name字段解析Maven坐标
        name = library.get('name', '')
        if name:
            # 解析Maven坐标: group:artifact:version[:classifier][@extension]
            parts = name.split(':')
            if len(parts) >= 3:
                group = parts[0].replace('.', '/')
                artifact = parts[1]
                version = parts[2]
                classifier = parts[3] if len(parts) > 3 else ''
                extension = parts[4] if len(parts) > 4 else 'jar'
                
                # 构建路径和URL
                filename = f"{artifact}-{version}"
                if classifier:
                    filename += f"-{classifier}"
                filename += f".{extension}"
                
                path = f"{group}/{artifact}/{version}/{filename}"
                url = f"https://libraries.minecraft.net/{path}"
                
                return {'path': path, 'url': url}
        
        return None
    
    def get_classpath(self, version_data, game_directory):
        """构建完整的类路径"""
        classpath = []
        libraries_path = Path(game_directory) / "libraries"
        version_path = Path(game_directory) / "versions" / version_data['id']
        
        # 添加版本JAR文件
        version_jar = version_path / f"{version_data['id']}.jar"
        if version_jar.exists():
            classpath.append(str(version_jar))
        
        # 添加依赖库文件
        libraries = version_data.get('libraries', [])
        for library in libraries:
            if not self._should_download_library(library):
                continue
            
            library_info = self._get_library_info(library)
            if library_info:
                library_path = library_info.get('path', '')
                if library_path:
                    library_file = libraries_path / library_path
                    if library_file.exists():
                        classpath.append(str(library_file))
        
        # 检查是否包含关键库（如Mojang日志库）
        has_mojang_libs = any('com/mojang' in path for path in classpath)
        if not has_mojang_libs:
            # 使用print替代log_message，因为LibraryManager没有日志功能
            print("警告: 未找到Mojang核心库，尝试下载缺失的库...")
            # 强制重新下载所有库
            self.download_libraries(version_data)
            # 重新构建类路径
            classpath = self._rebuild_classpath(version_data, game_directory)
        
        # 检查类路径是否为空
        if not classpath:
            raise Exception("类路径为空，请先下载依赖库")
        
        return classpath
    
    def _rebuild_classpath(self, version_data, game_directory):
        """重新构建类路径"""
        classpath = []
        libraries_path = Path(game_directory) / "libraries"
        version_path = Path(game_directory) / "versions" / version_data['id']
        
        # 添加版本JAR文件
        version_jar = version_path / f"{version_data['id']}.jar"
        if version_jar.exists():
            classpath.append(str(version_jar))
        
        # 添加依赖库文件
        libraries = version_data.get('libraries', [])
        for library in libraries:
            if not self._should_download_library(library):
                continue
            
            library_info = self._get_library_info(library)
            if library_info:
                library_path = library_info.get('path', '')
                if library_path:
                    library_file = libraries_path / library_path
                    if library_file.exists():
                        classpath.append(str(library_file))
        
        return classpath
    
    def _should_download_library(self, library):
        """检查是否需要下载该库"""
        rules = library.get('rules', [])
        if not rules:
            return True
        
        # 检查操作系统规则
        system_os = platform.system().lower()
        allow = True
        
        for rule in rules:
            action = rule.get('action', 'allow')
            os_info = rule.get('os', {})
            os_name = os_info.get('name', '').lower()
            os_arch = os_info.get('arch', '').lower()
            
            # 检查操作系统
            if os_name:
                if os_name == system_os:
                    if action == 'allow':
                        allow = True
                    else:
                        allow = False
                else:
                    if action == 'allow':
                        allow = False
                    else:
                        allow = True
            
            # 检查架构
            if os_arch:
                system_arch = platform.machine().lower()
                if os_arch != system_arch:
                    if action == 'allow':
                        allow = False
                    else:
                        allow = True
        
        return allow
    
    def _download_file(self, url, file_path):
        """下载文件"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        print(f"下载完成: {file_path.name}")