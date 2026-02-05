"""
Custom QProxyStyle for StockAlert.

Provides properly sized spinbox arrows that work with both light and dark themes.
This is the Qt-recommended approach for customizing widget sub-controls.
"""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import QProxyStyle, QStyle, QStyleOption, QStyleOptionComplex, QWidget


class StockAlertStyle(QProxyStyle):
    """Custom proxy style with properly sized spinbox/combobox arrows."""

    def __init__(self, base_style: str = "Fusion") -> None:
        """Initialize with Fusion as base style for consistent cross-platform look."""
        super().__init__(base_style)
        self._arrow_color_light = QColor("#333333")
        self._arrow_color_dark = QColor("#FFFFFF")
        self._is_dark_theme = True

    def set_dark_theme(self, is_dark: bool) -> None:
        """Set whether dark theme is active."""
        self._is_dark_theme = is_dark

    def subControlRect(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        subControl: QStyle.SubControl,
        widget: QWidget | None = None,
    ) -> QRect:
        """Override sub-control rectangles for spinbox buttons."""
        rect = super().subControlRect(control, option, subControl, widget)

        if control == QStyle.ComplexControl.CC_SpinBox:
            button_width = 28
            button_height = rect.height() // 2

            if subControl == QStyle.SubControl.SC_SpinBoxUp:
                rect = QRect(
                    option.rect.width() - button_width,
                    0,
                    button_width,
                    button_height,
                )
            elif subControl == QStyle.SubControl.SC_SpinBoxDown:
                rect = QRect(
                    option.rect.width() - button_width,
                    button_height,
                    button_width,
                    button_height,
                )
            elif subControl == QStyle.SubControl.SC_SpinBoxEditField:
                rect = QRect(
                    0,
                    0,
                    option.rect.width() - button_width,
                    option.rect.height(),
                )

        return rect

    def drawComplexControl(
        self,
        control: QStyle.ComplexControl,
        option: QStyleOptionComplex,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        """Draw complex controls with custom arrows."""
        if control == QStyle.ComplexControl.CC_SpinBox:
            # Draw the base spinbox (edit field)
            super().drawComplexControl(control, option, painter, widget)

            # Draw custom arrows on top
            arrow_color = self._arrow_color_dark if self._is_dark_theme else self._arrow_color_light

            # Get button rectangles
            up_rect = self.subControlRect(control, option, QStyle.SubControl.SC_SpinBoxUp, widget)
            down_rect = self.subControlRect(control, option, QStyle.SubControl.SC_SpinBoxDown, widget)

            # Draw up arrow
            self._draw_arrow(painter, up_rect, arrow_color, up=True)

            # Draw down arrow
            self._draw_arrow(painter, down_rect, arrow_color, up=False)
        else:
            super().drawComplexControl(control, option, painter, widget)

    def _draw_arrow(
        self, painter: QPainter, rect: QRect, color: QColor, up: bool
    ) -> None:
        """Draw a triangular arrow in the given rectangle."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Arrow dimensions
        arrow_width = 10
        arrow_height = 6

        # Center the arrow in the button
        center_x = rect.center().x()
        center_y = rect.center().y()

        # Create arrow points
        if up:
            points = [
                (center_x, center_y - arrow_height // 2),
                (center_x - arrow_width // 2, center_y + arrow_height // 2),
                (center_x + arrow_width // 2, center_y + arrow_height // 2),
            ]
        else:
            points = [
                (center_x, center_y + arrow_height // 2),
                (center_x - arrow_width // 2, center_y - arrow_height // 2),
                (center_x + arrow_width // 2, center_y - arrow_height // 2),
            ]

        # Draw filled triangle
        from PyQt6.QtGui import QPolygon
        from PyQt6.QtCore import QPoint

        polygon = QPolygon([QPoint(int(x), int(y)) for x, y in points])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPolygon(polygon)

        painter.restore()

    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: QWidget | None = None,
    ) -> None:
        """Draw primitive elements with custom styling."""
        # Skip default arrow drawing for spinbox - we handle it in drawComplexControl
        if element in (
            QStyle.PrimitiveElement.PE_IndicatorSpinUp,
            QStyle.PrimitiveElement.PE_IndicatorSpinDown,
        ):
            # Don't draw - we draw custom arrows in drawComplexControl
            return

        super().drawPrimitive(element, option, painter, widget)
