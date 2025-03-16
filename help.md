**每个新的事件文件，需要遵循以下格式：**
```python
from PyQt5.QtWidgets import QWidget # 导入必要的模块
class Handler(QWidget): # 事件处理器
    def event (self, event): # 事件处理函数
        # 在这里处理事件
    def event2 (self, event): # 事件处理函数
        # 可以添加更多的事件处理函数
def setup(parent): # 事件处理器的初始化函数
    handler = Handler(parent) # 创建事件处理器的实例
    Handler.event = event(parent) # 将事件处理函数绑定到处理器上
    Handler.event2 = event2(parent) # 可以添加更多的事件处理函数
    return handler # 返回事件处理器的实例
```
