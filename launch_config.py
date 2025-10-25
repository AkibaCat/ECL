#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动配置 - 管理启动参数和设置
"""

import json
import os
import subprocess
from pathlib import Path

class LaunchConfig:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path.home() / ".tcl" / "config.json"
        
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        default_config = {
            'memory': 2048,
            'resolution': '854x480',
            'game_directory': str(Path.home() / "AppData" / "Roaming" / ".minecraft"),
            'java_path': '',
            'last_version': '',
            'window_width': 800,
            'window_height': 600,
            'username': 'Player'
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置，用户配置覆盖默认配置
                    default_config.update(user_config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        return self.save_config()
    
    def get_java_path(self):
        """获取Java路径"""
        java_path = self.get('java_path')
        if java_path and os.path.exists(java_path):
            return java_path
        
        # 自动检测Java
        return self._auto_detect_java()
    
    def _auto_detect_java(self):
        """自动检测Java安装路径"""
        # 检查环境变量
        java_home = os.environ.get('JAVA_HOME')
        if java_home:
            java_exe = Path(java_home) / "bin" / "java.exe"
            if java_exe.exists():
                self.set('java_path', str(java_exe))
                return str(java_exe)
        
        # 检查系统路径 - 改进的检测方法
        try:
            # 使用更可靠的Java检测方法
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0:
                # 如果java命令可用，获取完整路径
                result = subprocess.run(['where', 'java'], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    java_path = result.stdout.split('\n')[0].strip()
                    self.set('java_path', java_path)
                    return java_path
        except:
            pass
        
        # 检查常见安装路径 - 扩展更多路径
        common_paths = [
            r"C:\Program Files\Java\jre*\bin\java.exe",
            r"C:\Program Files\Java\jdk*\bin\java.exe",
            r"C:\Program Files (x86)\Java\jre*\bin\java.exe",
            r"C:\Program Files\Eclipse Adoptium\jdk-*\bin\java.exe",
            r"C:\Program Files\BellSoft\LibericaJDK-*\bin\java.exe",
            r"C:\Program Files\Microsoft\jdk-*\bin\java.exe",
            r"C:\Program Files\Amazon Corretto\jdk*\bin\java.exe",
            r"C:\Program Files\Zulu\zulu-*\bin\java.exe",
            r"C:\Users\*\AppData\Local\Packages\Microsoft.4297127D64EC6_*\LocalCache\local\runtime\java-runtime-*\bin\java.exe"
        ]
        
        import glob
        for path_pattern in common_paths:
            matches = glob.glob(path_pattern)
            if matches:
                # 选择最新版本的Java
                java_path = sorted(matches, reverse=True)[0]
                self.set('java_path', java_path)
                return java_path
        
        return None
    
    def get_launch_arguments(self, version_data, version_id, game_directory):
        """获取启动参数"""
        args = []
        java_path = self.get_java_path()
        
        if not java_path:
            raise Exception("未找到Java运行时环境")
        
        # JVM参数
        memory = self.get('memory', 2048)
        args.extend([
            java_path,
            f"-Xmx{memory}M",
            f"-Xms{memory}M",
            "-Djava.library.path=natives",
            "-cp", self._build_classpath(version_data, game_directory)
        ])
        
        # 主类
        main_class = version_data.get('mainClass', 'net.minecraft.client.main.Main')
        args.append(main_class)
        
        # 游戏参数
        game_args = {
            '--version': version_id,
            '--gameDir': game_directory,
            '--assetsDir': str(Path(game_directory) / "assets"),
            '--assetIndex': version_data.get('assets', ''),
            '--uuid': '00000000-0000-0000-0000-000000000000',
            '--accessToken': '0',
            '--userType': 'mojang',
            '--versionType': 'release',
            '--username': self.get('username', 'Player'),
            '--width': '854',
            '--height': '480'
        }
        
        for key, value in game_args.items():
            if value:
                args.extend([key, str(value)])
        
        return args
    
    def _build_classpath(self, version_data, game_directory):
        """构建类路径"""
        from library_manager import LibraryManager
        
        library_manager = LibraryManager(game_directory)
        classpath = library_manager.get_classpath(version_data, game_directory)
        
        if not classpath:
            raise Exception("未找到任何库文件，请先下载依赖库")
        
        # 确保所有路径都是绝对路径且格式正确
        absolute_classpath = []
        for path in classpath:
            if not os.path.isabs(path):
                # 如果是相对路径，转换为绝对路径
                abs_path = os.path.abspath(path)
                absolute_classpath.append(abs_path)
            else:
                absolute_classpath.append(path)
        
        # 验证所有路径都存在
        missing_files = []
        for path in absolute_classpath:
            if not os.path.exists(path):
                missing_files.append(path)
        
        if missing_files:
            raise Exception(f"类路径文件不存在: {', '.join(missing_files)}")
        
        # Windows使用分号分隔类路径
        return ";".join(absolute_classpath)
    
    def _should_download_library(self, library):
        """检查是否需要该库（简化版本）"""
        import platform
        rules = library.get('rules', [])
        if not rules:
            return True
        
        system_os = platform.system().lower()
        for rule in rules:
            os_info = rule.get('os', {})
            os_name = os_info.get('name', '').lower()
            if os_name and os_name != system_os:
                return False
        
        return True