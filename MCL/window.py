from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget

class WindowHandler(QWidget):
    def draggable_events(window): # 窗口可拖动事件
        """
        为窗口添加可拖动事件
        :param window: 要添加拖动事件的窗口对象
        :return: 添加事件后的窗口对象
        """
        def mousePressEvent(self, event):
            """
            鼠标按下事件处理函数，当鼠标在窗口上方 32px 内按下时，标记窗口可拖动
            :param self: 窗口对象
            :param event: 鼠标事件
            """
            if event.y() <= 32:
                # 标记窗口可拖动
                self.draggable = True
                # 记录鼠标相对于窗口的偏移量
                self.offset = event.pos()

        def mouseMoveEvent(self, event):
            """
            鼠标移动事件处理函数，当窗口可拖动时，根据鼠标移动量移动窗口
            :param self: 窗口对象
            :param event: 鼠标事件
            """
            if self.draggable:
                # 计算窗口的新位置并移动窗口
                self.move(self.pos() + event.pos() - self.offset)

        def mouseReleaseEvent(self, event):
            """
            鼠标释放事件处理函数，释放鼠标后标记窗口不可拖动
            :param self: 窗口对象
            :param event: 鼠标事件
            """
            # 标记窗口不可拖动
            self.draggable = False
        # 动态绑定鼠标按下事件处理函数到窗口对象
        window.mousePressEvent = mousePressEvent.__get__(window, type(window))
        # 动态绑定鼠标移动事件处理函数到窗口对象
        window.mouseMoveEvent = mouseMoveEvent.__get__(window, type(window))
        # 动态绑定鼠标释放事件处理函数到窗口对象
        window.mouseReleaseEvent = mouseReleaseEvent.__get__(window, type(window))
        return window

def setup(parent):
    handler = WindowHandler(parent)
    # 自动为父窗口添加拖动功能
    WindowHandler.draggable_events(parent)
    return handler
