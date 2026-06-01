"""
Точка входа для запуска Desktop клиента (Flet).
"""
import flet as ft
import os
import sys

# Корректное определение пути к ассетам для EXE (через sys._MEIPASS) и для разработки
if hasattr(sys, "_MEIPASS"):
    assets_dir = os.path.join(sys._MEIPASS, "assets")
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")

from src.interfaces.desktop_client import main

if __name__ == "__main__":
    ft.run(main, assets_dir=assets_dir)
