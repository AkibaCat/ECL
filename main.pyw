import MCL # 导入自定义的MCL模块
from config import *  # 导入配置文件中的配置项
width = launcher_config['width']  # 获取窗口宽度
height = launcher_config['height']  # 获取窗口高度

class TransparentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 设置窗口大小
        self.resize(width, height)
        # 设置窗口无边框
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 设置窗口透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 初始化MCL模块
        MCL.setup_drawings(self)

print("Autumn Minecraft Launcher is running...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TransparentWindow()
    window.show()
    window.update()  # 强制更新窗口
    sys.exit(app.exec_())
