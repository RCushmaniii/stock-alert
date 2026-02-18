"""Generate stock_alert.ico from stock_trend.svg using PyQt6 + Pillow.

One-time script to create a multi-size Windows ICO file from the SVG branding icon.
Run: python generate_ico.py
"""

import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication
from PIL import Image

SVG_PATH = Path("src/stockalert/ui/assets/stock_trend.svg")
ICO_PATH = Path("stock_alert.ico")
SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> int:
    app = QApplication(sys.argv)

    if not SVG_PATH.exists():
        print(f"SVG not found: {SVG_PATH}")
        return 1

    renderer = QSvgRenderer(str(SVG_PATH))
    if not renderer.isValid():
        print("Failed to load SVG")
        return 1

    pil_images = []
    for size in SIZES:
        # Render SVG to QImage
        qimage = QImage(QSize(size, size), QImage.Format.Format_ARGB32)
        qimage.fill(Qt.GlobalColor.transparent)
        painter = QPainter(qimage)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()

        # Convert QImage (ARGB32) to PIL Image (RGBA)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(width * height * 4)
        raw = bytes(ptr)

        pil_img = Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
        pil_images.append(pil_img)
        print(f"  Rendered {size}x{size}")

    # Save as multi-size ICO
    pil_images[-1].save(
        str(ICO_PATH),
        format="ICO",
        append_images=pil_images[:-1],
        sizes=[(s, s) for s in SIZES],
    )
    print(f"Saved {ICO_PATH} with sizes: {SIZES}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
