#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理器 - 负责游戏进程的生命周期管理
"""

import subprocess
import threading
import time
import os
import psutil  # 需要安装: pip install psutil

class ProcessManager:
    def __init__(self):
        self.process = None
        self.monitor_thread = None
        self.output_thread = None
        self.is_running = False
    
    def start_process(self, cmd, cwd=None, callback=None):
        """启动进程"""
        try:
            # 改进Windows进程启动
            if os.name == 'nt':  # Windows系统
                # 使用CREATE_NO_WINDOW标志避免弹出控制台窗口
                creationflags = subprocess.CREATE_NO_WINDOW
            else:
                creationflags = 0
            
            # 创建进程 - 改进参数处理
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=False,
                creationflags=creationflags,
                bufsize=1  # 行缓冲
            )
            
            self.is_running = True
            
            # 启动输出监控
            self.output_thread = threading.Thread(
                target=self._monitor_output, 
                args=(callback,),
                daemon=True
            )
            self.output_thread.start()
            
            # 启动进程监控
            self.monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self.monitor_thread.start()
            
            return True
            
        except Exception as e:
            if callback:
                callback(f"启动进程失败: {e}")
            return False
    
    def _monitor_output(self, callback):
        """监控进程输出"""
        if not self.process:
            return
        
        try:
            while self.is_running and self.process.poll() is None:
                try:
                    line = self.process.stdout.readline()
                    if line:
                        if callback:
                            callback(line.strip())
                    else:
                        # 短暂休眠避免CPU占用过高
                        time.sleep(0.1)
                except Exception:
                    break
        except Exception as e:
            if callback:
                callback(f"输出监控错误: {e}")
    
    def _monitor_process(self):
        """监控进程状态"""
        if not self.process:
            return
        
        try:
            # 等待进程结束
            return_code = self.process.wait()
            self.is_running = False
            
            # 可以在这里添加进程结束的回调
            print(f"进程已退出，返回码: {return_code}")
            
        except Exception as e:
            print(f"进程监控错误: {e}")
            self.is_running = False
    
    def terminate_process(self):
        """终止进程"""
        if self.process and self.process.poll() is None:
            try:
                # 先尝试正常终止
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 如果正常终止失败，强制终止
                try:
                    self.process.kill()
                except:
                    pass
            finally:
                self.is_running = False
    
    def is_process_running(self):
        """检查进程是否在运行"""
        if self.process and self.process.poll() is None:
            return True
        return False
    
    def get_process_id(self):
        """获取进程ID"""
        if self.process:
            return self.process.pid
        return None