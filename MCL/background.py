from config import *  # 导入配置文件中的配置项
print("背景文件已被加载")

class BackgroundHandler(QWidget): # 背景处理器
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置背景组件大小与父窗口一致
        self.setFixedSize(parent.size())
        # 监听父窗口大小变化
        parent.installEventFilter(self)
    
    def eventFilter(self, obj, event): # 监听父窗口大小变化
        if obj == self.parent() and event.type() == QEvent.Resize:
            self.setFixedSize(self.parent().size())
            self.update()  # 触发重绘
        return super().eventFilter(obj, event)
    
    def paintEvent(self, event):
        self.background_image(event) # 调用绘制背景的方法
        self.description(event) # 调用绘制文字的方法

    def background_image(self, event): # 绘制背景
        """绘制背景，根据是否有背景图片决定绘制图片或纯色背景"""
        width = launcher_config['width']
        height = launcher_config['height']
        radius = launcher_config['radius']
        mode = launcher_config['background_mode']

        # 检查背景图片文件夹
        background_folder = launcher_config['background_path'].strip('"')
        # 检查背景图片模式
        mode = int(mode)
        # 背景图片模式为1(随机图片模式)
        if mode == 1:
            # 检查是否有图片
            print("背景为随机图片")
            if os.path.exists(background_folder):
                images = [f for f in os.listdir(background_folder) if os.path.isfile(os.path.join(background_folder, f))]
                if images:
                    # 随机选择一张图片来绘制
                    image_path = os.path.join(background_folder, random.choice(images))
                    pixmap = QPixmap(image_path).scaled(width, height, Qt.KeepAspectRatioByExpanding)
                    painter = QPainter(self)
                    painter.setRenderHint(QPainter.Antialiasing)
                    path = QPainterPath()
                    rect = QRectF(0, 0, width, height)
                    path.addRoundedRect(rect, radius, radius)
                    painter.setClipPath(path)
                    # 计算图片在窗口的居中位置
                    x = (width - pixmap.width()) // 2
                    y = (height - pixmap.height()) // 2
                    # 绘制图片到窗口中心位置
                    painter.drawPixmap(x, y, pixmap)
                    # 添加描边
                    painter.setPen(QColor("#4f4f4f"))
                    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)
            return
        """绘制纯色背景，根据是否有背景图片决定绘制图片或纯色背景"""
        print("背景为纯色背景")
        # 获取背景颜色字段内容
        radius = launcher_config['radius']
        bg_color = launcher_config['background_color'].strip('"')

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        rect = QRectF(self.rect())
        # 绘制圆角背景，颜色为 bg_color
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, QColor(bg_color))
        # 添加描边
        painter.setPen(QColor("#4f4f4f"))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), radius, radius)

    def description(self, event): # 绘制文字
        """
        在窗口绘制 mclauncher.ini 的 description 内容
        :param self: 窗口对象
        :param event: 绘制事件
        """

        # 配置文字的字体和颜色
        painter = QPainter(self)
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        painter.setPen(QColor("#efefef"))
        
        # 计算文字绘制的位置
        x = launcher_config['radius'] // 2
        y = self.height() - launcher_config['radius'] // 2
        painter.drawText(x, y, description)

def setup(parent):
    background = BackgroundHandler(parent)
    return background
    