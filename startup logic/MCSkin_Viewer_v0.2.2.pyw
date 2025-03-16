# 项目名称：Minecraft Skin Viewer
# 本程序是一个基于PyQt5的Minecraft皮肤查看器，用于获取并显示Minecraft玩家的皮肤
# 作者：AutumnLeaves
# 版本：0.2.2
# 上一次修改时间：2025/3/11 13:40
# 上一次修改内容：
# - 添加提示文字

# 免责声明：本程序仅供学习和研究使用，不得用于商业用途。作者不对因使用本程序而导致的任何损失或损害承担责任。

import sys
import base64
import json
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QRegExpValidator, QBrush, QFont
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, QUrl, QRegExp
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtCore import QTimer

# 定义应用程序的全局样式表
style = """
/* 主窗口样式 */
QWidget {
    background-color: #1f1f1f;
}

/* 输入框样式 */
QLineEdit {
    background-color: #2f2f2f;
    font: 14px "微软雅黑";
    color: white;
    border: 2px solid #4f4f4f;
    border-radius: 8px;
    text-align: center;
}

/* 刷新按钮默认样式 */
QPushButton {
    background-color: #2f2f2f;
    font: 14px "微软雅黑";
    color: white;
    border: 2px solid #3f3f3f;
    border-radius: 16px;
}

/* 刷新按钮鼠标悬停样式 */
QPushButton:hover {
    background-color: #3f3f3f;
    border: 2px solid #4f4f4f;
}
"""

class SkinWindow(QWidget):
    """
    Minecraft 皮肤查看器主窗口类
    功能：
    - 通过玩家ID获取并显示Minecraft皮肤
    - 支持拖拽移动窗口
    - 支持复制皮肤URL到剪贴板
    """
    def __init__(self):
        """
        初始化皮肤查看器窗口
        设置窗口属性、创建UI组件、初始化网络管理器
        """
        super().__init__()
        # 窗口初始化设置
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setFixedSize(256, 416)
        self.setStyleSheet(style)
        
        # 网络管理器初始化
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_network_finished)
        
        # 皮肤图片处理参数
        self.crop_rect = (8, 8, 8, 8)  # 皮肤头部裁剪区域
        self.crop_rect_2 = (40, 8, 8, 8)  # 皮肤身体裁剪区域
        self.paint_pos = (65, 97, 128, 128)  # 皮肤绘制位置和大小
        
        # 创建并配置输入框
        self.input_field = QLineEdit(self)
        self.input_field.setGeometry(32, 304, 192, 32)
        self.input_field.setAlignment(Qt.AlignCenter)
        reg_exp = QRegExp("[a-zA-Z0-9_]{0,16}")
        validator = QRegExpValidator(reg_exp, self.input_field)
        self.input_field.setValidator(validator)
        self.input_field.returnPressed.connect(self.on_refresh_clicked)
        
        # 创建并配置刷新按钮
        self.refresh_button = QPushButton("刷新", self)
        button_x = (self.width() - 64) // 2
        button_y = self.input_field.y() + self.input_field.height() + 16
        self.refresh_button.setGeometry(button_x, button_y, 64, 32)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        
        # 窗口拖拽相关变量
        self.drag_start_position = None
        self.window_start_position = None
        
        # 创建并配置关闭按钮
        svg_code = '<svg t="1741017719583" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2743" width="128" height="128"><path d="M807.538939 256.459755a20.897959 20.897959 0 0 1 0 29.549714L571.099429 522.44898l236.43951 236.43951a20.897959 20.897959 0 0 1 0 29.549714l-29.549715 29.549714a20.897959 20.897959 0 0 1-29.549714 0L512 581.548408 275.56049 817.987918a20.897959 20.897959 0 0 1-29.549714 0l-29.549715-29.549714a20.897959 20.897959 0 0 1 0-29.549714L452.900571 522.44898 216.461061 286.009469a20.897959 20.897959 0 0 1 0-29.549714l29.549715-29.549714a20.897959 20.897959 0 0 1 29.549714 0L512 463.349551l236.43951-236.43951a20.897959 20.897959 0 0 1 29.549714 0l29.549715 29.549714z" fill="#ffffff" p-id="2744"></path></svg>'
        self.close_button = QSvgWidget(self)
        self.close_button.load(svg_code.encode())
        close_button_size = 20
        self.close_button.setGeometry(self.width() - close_button_size - 10, 7, close_button_size, close_button_size)
        self.close_button.mousePressEvent = self.on_close_button_clicked
        
        # 复制提示相关变量
        self.show_copied_text = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.hide_copied_text)

    def on_close_button_clicked(self, event):
        """
        处理关闭按钮的点击事件
        :param event: 鼠标点击事件
        """
        # 检查是否为左键点击
        if event.button() == Qt.LeftButton:
            # 关闭窗口
            self.close()

    def on_refresh_clicked(self):
        """
        处理刷新按钮的点击事件或输入框的回车事件
        """
        # 重置 UUID、Value、解码后的 Value 和皮肤 URL
        self.uuid = None
        self.value = None
        self.value_decode = None
        self.skin_url = None
        # 检查是否存在 pixmap 对象
        if hasattr(self, 'pixmap'):
            # 清空 pixmap 对象
            self.pixmap = QPixmap()
            # 更新窗口显示
            self.update()
            # 重绘窗口
            self.repaint()
        # 获取输入框中的文本
        self.name = self.input_field.text()
        # 构建请求 UUID 的 URL
        uuid_url = QUrl(f"https://api.mojang.com/users/profiles/minecraft/{self.name}")
        # 创建网络请求对象
        request = QNetworkRequest(uuid_url)
        # 断开之前的网络请求完成信号连接
        self.network_manager.finished.disconnect()
        # 重新连接网络请求完成信号到处理函数
        self.network_manager.finished.connect(self.on_network_finished)
        # 发送网络请求
        self.network_manager.get(request)

    def on_network_finished(self, reply):
        """
        处理网络请求完成事件
        :param reply: 网络响应对象
        """
        # 获取响应的 URL
        url = reply.url().toString()
        # 打印响应的 URL
        print(f"收到响应的 URL: {url}")
        # 检查是否为请求 UUID 的响应
        if "https://api.mojang.com/users/profiles/minecraft/" in url:
            # 检查响应是否成功
            if reply.error() == QNetworkReply.NoError:
                # 解析响应数据为 JSON 格式
                data = json.loads(reply.readAll().data().decode())
                # 打印获取 UUID 的响应数据
                print(f"获取 UUID 的响应数据: {data}")
                # 获取 UUID
                self.uuid = data.get('id')
                # 检查是否成功获取 UUID
                if self.uuid:
                    # 构建请求 Value 的 URL
                    value_url = QUrl(f"https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid}")
                    # 打印请求 Value 的 URL
                    print(f"请求 Value 的 URL: {value_url.toString()}")
                    # 创建网络请求对象
                    request = QNetworkRequest(value_url)
                    # 发送网络请求
                    self.network_manager.get(request)
            else:
                # 打印获取 UUID 失败的错误信息
                print(f"获取 UUID 失败: {reply.errorString()}")
        # 检查是否为请求 Value 的响应
        elif "https://sessionserver.mojang.com/session/minecraft/profile/" in url:
            # 检查响应是否成功
            if reply.error() == QNetworkReply.NoError:
                # 解析响应数据为 JSON 格式
                data = json.loads(reply.readAll().data().decode())
                # 打印获取 Value 的响应数据
                print(f"获取 Value 的响应数据: {data}")
                # 获取响应数据中的 properties 列表
                properties = data.get('properties', [])
                # 遍历 properties 列表
                for prop in properties:
                    # 检查是否为 textures 属性
                    if prop.get('name') == 'textures':
                        # 获取 textures 属性的值
                        self.value = prop.get('value')
                        # 检查是否成功获取 textures 属性的值
                        if self.value:
                            # 对 textures 属性的值进行 Base64 解码
                            self.value_decode = base64.b64decode(self.value).decode()
                            # 打印解码后的 Value
                            print(f"解码后的 Value: {self.value_decode}")
                            # 解析解码后的 Value 为 JSON 格式
                            textures = json.loads(self.value_decode).get('textures', {})
                            # 获取 SKIN 纹理信息
                            skin = textures.get('SKIN', {})
                            # 获取皮肤的 URL
                            self.skin_url = skin.get('url')
                            # 检查是否成功获取皮肤的 URL
                            if self.skin_url:
                                # 构建请求皮肤图片的 URL
                                url = QUrl(self.skin_url)
                                # 打印请求图片的 URL
                                print(f"请求图片的 URL: {url.toString()}")
                                # 创建网络请求对象
                                request = QNetworkRequest(url)
                                # 断开之前的网络请求完成信号连接
                                self.network_manager.finished.disconnect(self.on_network_finished)
                                # 连接网络请求完成信号到处理图片下载完成的函数
                                self.network_manager.finished.connect(self.on_image_downloaded)
                                # 发送网络请求
                                self.network_manager.get(request)
                            # 跳出循环
                            break
            else:
                # 打印获取 Value 失败的错误信息
                print(f"获取 Value 失败: {reply.errorString()}")
        # 释放网络响应对象
        reply.deleteLater()

    def on_image_downloaded(self, reply):
        """处理图片下载完成事件"""
        if reply.error() == QNetworkReply.NoError:
            self.pixmap = QPixmap()
            self.pixmap.loadFromData(reply.readAll())
            self.update()
        else:
            # 打印图片下载失败的错误信息
            print(f"图片下载失败: {reply.errorString()}")
        reply.deleteLater()

    def paintEvent(self, event):
        """处理窗口绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制圆角矩形填充，作为背景
        pen = QPen(QColor("#4f4f4f"), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 16, 16)
        painter.setBrush(QBrush(QColor("#1f1f1f")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)
        
        # 绘制分隔线
        painter.setPen(QPen(QColor("#4f4f4f"), 2))
        painter.drawLine(0, 32, 256, 32)

        # 绘制标题文本
        font = QFont("微软雅黑", 14)
        painter.setFont(font)
        painter.setPen(QColor(Qt.white))
        painter.drawText(10, 25, "MC Skin")

        # 绘制提示文本
        font = QFont("微软雅黑", 10)
        painter.setFont(font)
        painter.setPen(QColor("#ffff00"))
        painter.drawText(10, 55, "右键点击头像复制皮肤链接")

        # 检查是否存在 pixmap 对象且不为空
        if hasattr(self, 'pixmap') and not self.pixmap.isNull():
            cropped_pixmap = self.pixmap.copy(*self.crop_rect)
            painter.drawPixmap(*self.paint_pos, cropped_pixmap)
            cropped_pixmap_2 = self.pixmap.copy(*self.crop_rect_2)
            painter.drawPixmap(self.paint_pos[0] - 8, self.paint_pos[1] - 8, self.paint_pos[2] + 16, self.paint_pos[3] + 16, cropped_pixmap_2)

        # 检查是否显示复制提示文本
        if self.show_copied_text:
            font = QFont("微软雅黑", 12)
            painter.setFont(font)
            painter.setPen(QColor(Qt.white))
            text = "已复制皮肤链接"
            text_width = painter.fontMetrics().width(text)
            text_x = self.paint_pos[0] + (self.paint_pos[2] - text_width) // 2
            text_y = self.paint_pos[1] + self.paint_pos[3] + 32
            painter.drawText(text_x, text_y, text)

    def mousePressEvent(self, event):
        """处理鼠标按下事件, 用于实现窗口的拖拽功能以及复制链接功能"""
        if event.button() == Qt.LeftButton: # 左键点击
            if event.pos().y() <= 32:
                self.drag_start_position = event.globalPos()
                self.window_start_position = self.pos()
        elif event.button() == Qt.RightButton: # 右键点击
            if hasattr(self, 'pixmap') and not self.pixmap.isNull():
                if self.skin_url:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(self.skin_url)
                    self.show_copied_text = True
                    self.update()
                    self.timer.start(1000)

    def hide_copied_text(self):
        """隐藏复制提示文本"""
        self.show_copied_text = False
        self.update()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if self.drag_start_position and self.window_start_position:
            delta = event.globalPos() - self.drag_start_position
            self.move(self.window_start_position + delta)

    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件"""
        self.drag_start_position = None

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SkinWindow()
    window.show()
    sys.exit(app.exec_())