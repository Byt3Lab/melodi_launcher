"""
Icon helper: Renders crisp recolorable SVG icons from assets/icons/.
"""

import os
from PySide6.QtCore import Qt, QByteArray
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from app.utils.helpers import resource_path


def load_svg_pixmap(name: str, color: str = "#f1f5f9", size: int = 18) -> QPixmap:
    """Charge un SVG et le rend en QPixmap à la couleur et taille demandées."""
    path = resource_path(os.path.join("assets", "icons", f"{name}.svg"))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    if not os.path.exists(path):
        return pixmap

    with open(path, "r", encoding="utf-8") as f:
        svg_data = f.read().replace("currentColor", color)

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    return pixmap


def load_svg_icon(name: str, color: str = "#f1f5f9", size: int = 18) -> QIcon:
    """Retourne un QIcon SVG recoloré."""
    return QIcon(load_svg_pixmap(name, color=color, size=size))
