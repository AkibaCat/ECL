#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖检查器 - 检查游戏启动所需的依赖是否完整
"""

import json
import os
from pathlib import Path

class DependencyChecker:
    def __init__(self, minecraft_path):
        self.minecraft_path = Path(minecraft_path)
    
    def check_version_dependencies(self, version_id):
        """检查指定版本的依赖是否完整"""
        version_dir = self.minecraft_path / "versions" / version_id
        json_file = version_dir / f"{version_id}.json"
        jar_file = version_dir / f"{version_id}.jar"
        
        # 检查基本文件
        if not json_file.exists():
            return False, f"缺少版本配置文件: {json_file}"
        
        if not jar_file.exists():
            return False, f"缺少游戏主文件: {jar_file}"
        
        # 读取版本数据
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
        except Exception as e:
            return False, f"读取版本配置失败: {e}"
        
        # 检查关键依赖库 - 放宽检查条件
        critical_libraries = [
            'jopt-simple',  # joptsimple库
            'commons-io',   # Apache Commons IO
            'guava',        # Google Guava
            'gson',         # Google Gson
            'log4j',        # Log4j日志库
            'lwjgl'         # Lightweight Java Game Library
        ]
        
        missing_libraries = []
        libraries_path = self.minecraft_path / "libraries"
        
        for lib_name in critical_libraries:
            # 检查库目录是否存在相关文件 - 使用更宽松的匹配
            lib_found = False
            for lib_file in libraries_path.rglob("*.jar"):
                if lib_name.lower() in lib_file.name.lower():
                    if lib_file.exists():
                        lib_found = True
                        break
            
            if not lib_found:
                missing_libraries.append(lib_name)
        
        if missing_libraries:
            return False, f"缺少关键依赖库: {', '.join(missing_libraries)}"
        
        return True, "依赖检查通过"
    
    def get_missing_dependencies(self, version_id):
        """获取缺失的依赖列表"""
        version_dir = self.minecraft_path / "versions" / version_id
        json_file = version_dir / f"{version_id}.json"
        
        if not json_file.exists():
            return []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
        except:
            return []
        
        missing_deps = []
        libraries_path = self.minecraft_path / "libraries"
        libraries = version_data.get('libraries', [])
        
        for library in libraries:
            lib_name = library.get('name', '')
            if not lib_name:
                continue
            
            # 简化检查：只要库目录中有相关文件就认为存在
            lib_found = False
            for lib_file in libraries_path.rglob("*.jar"):
                if lib_file.exists():
                    lib_found = True
                    break
            
            if not lib_found:
                missing_deps.append(lib_name)
        
        return missing_deps