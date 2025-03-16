import os
import sys
import random
from PyQt5.QtCore import Qt, QRectF, QEvent
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow

import configparser

# 读取配置文件
config = configparser.ConfigParser()
try:
    config.read('mclauncher.ini', encoding='utf-8')
except configparser.ParsingError as e:
    print(f"配置文件解析错误: {e}")
    sys.exit(1)

# 读取 Launcher 部分配置到字典
launcher_config = {
    'name': config.get('Launcher', 'name'),
    'version': config.get('Launcher', 'version'),
    'author': config.get('Launcher', 'author'),
    'width': config.getint('Launcher', 'width'),
    'height': config.getint('Launcher', 'height'),
    'radius': config.getint('Launcher', 'radius'),
    'icon_path': config.get('Launcher', 'icon_path'),
    'background_mode': config.get('Launcher', 'background_mode'),
    'background_path': config.get('Launcher', 'background_path'),
    'background_color': config.get('Launcher', 'background_color')
}
# 读取 Window 的配置到字典
window_config = {
    'close_icon_path': config.get('Window', 'close_icon_path'),
    'min_icon_path': config.get('Window', 'min_icon_path'),
    'set_icon_path': config.get('Window','set_icon_path'),
    'download_icon_path': config.get('Window', 'download_icon_path'),
    'back_icon_path': config.get('Window', 'back_icon_path')
}

name = launcher_config.get('name', 'Minecraft Launcher')  # 如果没有指定名称，默认为 'Minecraft Launcher'
version = launcher_config.get('version', 'Unknown Version')  # 如果没有指定版本，默认为 'Unknown Version'
author = launcher_config.get('author', 'AutumnLeaves')  # 如果没有指定作者，默认为 'Unknown'
description = name + ' ' + version + ' by ' + author  # 生成描述信息