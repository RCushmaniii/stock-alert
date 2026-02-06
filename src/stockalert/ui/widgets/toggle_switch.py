"""
Modern toggle switch widget for PyQt6.

A styled QCheckBox that looks like an iOS/Android toggle switch.
"""

from __future__ import annotations

from PyQt6.QtCore import QPropertyAnimation, QRect, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QCheckBox, QWidget


class ToggleSwitch(QCheckBox):
    """A modern toggle switch widget.

    Displays as a sliding toggle instead of a checkbox.
    Can show labels on either side (e.g., "USD" / "MXN").
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        left_label: str = "",
        right_label: str = "",
        track_color_off: str = "#555555",
        track_color_on: str = "#4CAF50",
        thumb_color: str = "#FFFFFF",
    ) -> None:
        """Initialize the toggle switch.

        Args:
            parent: Parent widget
            left_label: Label shown on the left (when unchecked)
            right_label: Label shown on the right (when checked)
            track_color_off: Background color when unchecked
            track_color_on: Background color when checked
            thumb_color: Color of the sliding thumb
        """
        super().__init__(parent)

        self._left_label = left_label
        self._right_label = right_label
        self._track_color_off = QColor(track_color_off)
        self._track_color_on = QColor(track_color_on)
        self._thumb_color = QColor(thumb_color)

        # Animation for smooth sliding
        self._thumb_position = 0.0
        self._animation = QPropertyAnimation(self, b"thumbPosition", self)
        self._animation.setDuration(150)

        # Connect state change to animation
        self.stateChanged.connect(self._on_state_changed)

        # Set size
        self.setFixedSize(60, 28)

        # Hide default checkbox appearance
        self.setStyleSheet("QCheckBox::indicator { width: 0; height: 0; }")

    def _on_state_changed(self, state: int) -> None:
        """Handle state change with animation."""
        self._animation.stop()
        self._animation.setStartValue(self._thumb_position)
        self._animation.setEndValue(1.0 if state else 0.0)
        self._animation.start()

    @pyqtProperty(float)
    def thumbPosition(self) -> float:
        """Get the current thumb position (0.0 to 1.0)."""
        return self._thumb_position

    @thumbPosition.setter
    def thumbPosition(self, value: float) -> None:
        """Set the thumb position and trigger repaint."""
        self._thumb_position = value
        self.update()

    def paintEvent(self, event) -> None:
        """Custom paint for toggle appearance."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dimensions
        width = self.width()
        height = self.height()
        track_height = 22
        track_radius = track_height // 2
        thumb_diameter = 18
        thumb_margin = (track_height - thumb_diameter) // 2

        # Track position (centered vertically)
        track_y = (height - track_height) // 2

        # Interpolate track color
        ratio = self._thumb_position
        track_color = QColor(
            int(self._track_color_off.red() + ratio * (self._track_color_on.red() - self._track_color_off.red())),
            int(self._track_color_off.green() + ratio * (self._track_color_on.green() - self._track_color_off.green())),
            int(self._track_color_off.blue() + ratio * (self._track_color_on.blue() - self._track_color_off.blue())),
        )

        # Draw track
        track_path = QPainterPath()
        track_rect = QRect(0, track_y, width, track_height)
        track_path.addRoundedRect(track_rect, track_radius, track_radius)
        painter.fillPath(track_path, track_color)

        # Calculate thumb position
        thumb_travel = width - thumb_diameter - (thumb_margin * 2)
        thumb_x = thumb_margin + int(self._thumb_position * thumb_travel)
        thumb_y = track_y + thumb_margin

        # Draw thumb
        thumb_path = QPainterPath()
        thumb_path.addEllipse(thumb_x, thumb_y, thumb_diameter, thumb_diameter)
        painter.fillPath(thumb_path, self._thumb_color)

        # Draw labels if provided
        if self._left_label or self._right_label:
            painter.setPen(QColor("#AAAAAA" if self._thumb_position > 0.5 else "#FFFFFF"))
            font = painter.font()
            font.setPointSize(8)
            font.setBold(True)
            painter.setFont(font)

            # Left label (visible when off)
            if self._left_label:
                left_rect = QRect(thumb_diameter + 4, track_y, width // 2 - 4, track_height)
                painter.drawText(left_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._left_label)

            # Right label (visible when on)
            painter.setPen(QColor("#FFFFFF" if self._thumb_position > 0.5 else "#AAAAAA"))
            if self._right_label:
                right_rect = QRect(4, track_y, width - thumb_diameter - 8, track_height)
                painter.drawText(right_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self._right_label)

        painter.end()

    def sizeHint(self):
        """Return the preferred size."""
        from PyQt6.QtCore import QSize
        return QSize(60, 28)

    def setLeftLabel(self, label: str) -> None:
        """Set the left label."""
        self._left_label = label
        self.update()

    def setRightLabel(self, label: str) -> None:
        """Set the right label."""
        self._right_label = label
        self.update()


class LabeledToggle(QWidget):
    """A toggle switch with external labels on both sides."""

    def __init__(
        self,
        parent: QWidget | None = None,
        left_label: str = "Off",
        right_label: str = "On",
    ) -> None:
        """Initialize labeled toggle.

        Args:
            parent: Parent widget
            left_label: Label on the left side
            right_label: Label on the right side
        """
        super().__init__(parent)

        from PyQt6.QtWidgets import QHBoxLayout, QLabel

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._left_label = QLabel(left_label)
        self._left_label.setStyleSheet("font-weight: bold; color: #888888;")

        self._toggle = ToggleSwitch()

        self._right_label = QLabel(right_label)
        self._right_label.setStyleSheet("font-weight: bold; color: #888888;")

        layout.addWidget(self._left_label)
        layout.addWidget(self._toggle)
        layout.addWidget(self._right_label)

        # Update label colors on toggle
        self._toggle.stateChanged.connect(self._update_label_colors)
        self._update_label_colors(self._toggle.isChecked())

    def _update_label_colors(self, checked: bool) -> None:
        """Update label colors based on toggle state."""
        if checked:
            self._left_label.setStyleSheet("font-weight: normal; color: #888888;")
            self._right_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        else:
            self._left_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
            self._right_label.setStyleSheet("font-weight: normal; color: #888888;")

    def isChecked(self) -> bool:
        """Get toggle state."""
        return self._toggle.isChecked()

    def setChecked(self, checked: bool) -> None:
        """Set toggle state."""
        self._toggle.setChecked(checked)

    @property
    def toggle(self) -> ToggleSwitch:
        """Get the underlying toggle widget."""
        return self._toggle

    def setLeftText(self, text: str) -> None:
        """Set left label text."""
        self._left_label.setText(text)

    def setRightText(self, text: str) -> None:
        """Set right label text."""
        self._right_label.setText(text)
