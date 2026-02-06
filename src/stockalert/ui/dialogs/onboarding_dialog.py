"""
Onboarding dialog for first-time users.

Shows a welcome message with setup steps for new users.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stockalert.i18n.translator import _


class OnboardingDialog(QDialog):
    """Welcome dialog for first-time users."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the onboarding dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(_("onboarding.title"))
        self.setFixedSize(520, 560)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Title
        title = QLabel(_("onboarding.title"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FF6A3D;")
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(_("onboarding.subtitle"))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888888; margin-bottom: 16px;")
        layout.addWidget(subtitle)

        # Steps container
        steps_container = QFrame()
        steps_container.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        steps_layout = QVBoxLayout(steps_container)
        steps_layout.setSpacing(16)

        # Step 1: Get API Key
        self._add_step(
            steps_layout,
            _("onboarding.step1_title"),
            _("onboarding.step1_desc"),
            "🔑"
        )

        # Step 2: Configure Settings
        self._add_step(
            steps_layout,
            _("onboarding.step2_title"),
            _("onboarding.step2_desc"),
            "⚙️"
        )

        # Step 3: Profile (for WhatsApp)
        self._add_step(
            steps_layout,
            _("onboarding.step3_title"),
            _("onboarding.step3_desc"),
            "👤"
        )

        # Step 4: Add Stocks
        self._add_step(
            steps_layout,
            _("onboarding.step4_title"),
            _("onboarding.step4_desc"),
            "📈"
        )

        layout.addWidget(steps_container)

        # Pro tip
        tip_frame = QFrame()
        tip_frame.setStyleSheet("""
            QFrame {
                background-color: #1a2a1a;
                border: 1px solid #2a4a2a;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        tip_layout = QVBoxLayout(tip_frame)
        tip_layout.setSpacing(4)

        tip_title = QLabel(_("onboarding.tip_title"))
        tip_title.setStyleSheet("color: #4CAF50; font-weight: bold;")
        tip_layout.addWidget(tip_title)

        tip_desc = QLabel(_("onboarding.tip_desc"))
        tip_desc.setWordWrap(True)
        tip_desc.setStyleSheet("color: #AAAAAA;")
        tip_layout.addWidget(tip_desc)

        layout.addWidget(tip_frame)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)

        skip_btn = QPushButton(_("onboarding.btn_skip"))
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #2A2A2A;
                color: #888888;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3A3A3A;
            }
        """)
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        btn_layout.addStretch()

        start_btn = QPushButton(_("onboarding.btn_get_started"))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF6A3D;
                color: white;
                border: none;
                padding: 12px 32px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #FF8A5D;
            }
        """)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self.accept)
        btn_layout.addWidget(start_btn)

        layout.addLayout(btn_layout)

    def _add_step(
        self,
        parent_layout: QVBoxLayout,
        title: str,
        description: str,
        icon: str
    ) -> None:
        """Add a step to the layout.

        Args:
            parent_layout: Layout to add step to
            title: Step title
            description: Step description
            icon: Emoji icon for the step
        """
        step_layout = QHBoxLayout()
        step_layout.setSpacing(12)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedWidth(32)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        step_layout.addWidget(icon_label)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        text_layout.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888;")
        text_layout.addWidget(desc_label)

        step_layout.addLayout(text_layout)
        parent_layout.addLayout(step_layout)
