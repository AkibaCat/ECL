import os
import importlib
from PyQt5.QtWidgets import QApplication

# 存储已加载的绘制模块
draw_modules = {}

def setup_drawings(window):
    # 获取当前目录下所有.py文件
    py_files = [f for f in os.listdir(os.path.dirname(__file__)) 
               if f.endswith('.py') and f != '__init__.py']
    
    # 确保window模块被优先加载
    if 'window.py' in py_files:
        py_files.remove('window.py')
        py_files.insert(0, 'window.py')
    
    # 动态加载并初始化绘制模块
    for file_name in py_files:
        # 跳过__init__.py文件
        module_name = file_name[:-3]
        # 检查模块是否已经加载过
        if module_name not in draw_modules:
            # 动态导入模块
            try:
                # 使用importlib动态导入模块
                module = importlib.import_module(f'MCL.{module_name}')
                # 检查模块是否有setup方法
                if hasattr(module, 'setup'):
                    # 调用setup方法并获取绘制组件
                    draw_widget = module.setup(window)
                    # 检查是否有handle_click方法
                    if draw_widget:
                        # 如果模块有处理点击事件的方法，则连接信号
                        if hasattr(module, 'handle_click'):
                            # 连接鼠标点击事件到handle_click方法
                            draw_widget.mousePressEvent = lambda event, m=module: m.handle_click(event)
                        draw_modules[module_name] = draw_widget
            # 捕获导入错误并打印错误信息
            except Exception as e:
                print(f"Error loading {module_name}: {e}")

# 自动设置绘制内容
app = QApplication.instance()
if app:
    for window in app.topLevelWidgets():
        if window.__class__.__name__ == 'TransparentWindow':
            # 初始设置
            setup_drawings(window)