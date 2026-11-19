"""
Design System Tokens and QSS Stylesheet generator for MELODI Launcher (Dark & Light).
"""

from typing import Dict

DARK_TOKENS: Dict[str, str] = {
    "name": "dark",
    "bg_app": "#0b1120",
    "bg_sidebar": "#0f172a",
    "bg_surface": "#162032",
    "bg_surface_alt": "#1e293b",
    "bg_input": "#0b1120",
    "bg_console": "#070b14",
    "border": "#26334a",
    "border_focus": "#38bdf8",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent": "#38bdf8",
    "accent_hover": "#0ea5e9",
    "accent_text": "#082f49",
    "accent_soft": "rgba(56, 189, 248, 0.14)",
    "success": "#22c55e",
    "success_soft": "rgba(34, 197, 94, 0.16)",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "danger_soft": "rgba(239, 68, 68, 0.16)",
    "warning": "#f59e0b",
    "warning_soft": "rgba(245, 158, 11, 0.16)",
}

LIGHT_TOKENS: Dict[str, str] = {
    "name": "light",
    "bg_app": "#f1f5f9",
    "bg_sidebar": "#ffffff",
    "bg_surface": "#ffffff",
    "bg_surface_alt": "#f8fafc",
    "bg_input": "#ffffff",
    "bg_console": "#0f172a",
    "border": "#e2e8f0",
    "border_focus": "#0284c7",
    "text_primary": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "accent": "#0284c7",
    "accent_hover": "#0369a1",
    "accent_text": "#ffffff",
    "accent_soft": "rgba(2, 132, 199, 0.12)",
    "success": "#16a34a",
    "success_soft": "rgba(22, 163, 74, 0.14)",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "danger_soft": "rgba(220, 38, 38, 0.14)",
    "warning": "#d97706",
    "warning_soft": "rgba(217, 119, 6, 0.14)",
}


def get_tokens(theme_name: str = "dark") -> Dict[str, str]:
    return LIGHT_TOKENS if theme_name == "light" else DARK_TOKENS


def build_stylesheet(theme_name: str = "dark") -> str:
    t = get_tokens(theme_name)
    return f"""
    * {{
        font-family: "Inter", "Ubuntu", "Cantarell", "Segoe UI", sans-serif;
        font-size: 13px;
        color: {t["text_primary"]};
    }}

    QMainWindow, QDialog {{
        background-color: {t["bg_app"]};
    }}

    QWidget#CentralWidget, QWidget#PageContainer, QScrollArea, QWidget#ScrollContent {{
        background-color: {t["bg_app"]};
        border: none;
    }}

    /* Sidebar */
    QFrame#Sidebar {{
        background-color: {t["bg_sidebar"]};
        border-right: 1px solid {t["border"]};
    }}

    QLabel#BrandTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {t["text_primary"]};
        letter-spacing: 0.3px;
    }}

    QLabel#BrandSubtitle {{
        font-size: 11px;
        color: {t["text_muted"]};
    }}

    /* Page headers */
    QLabel#PageTitle {{
        font-size: 22px;
        font-weight: 700;
        color: {t["text_primary"]};
    }}

    QLabel#PageSubtitle {{
        font-size: 13px;
        color: {t["text_secondary"]};
    }}

    QLabel#SectionTitle {{
        font-size: 15px;
        font-weight: 600;
        color: {t["text_primary"]};
    }}

    QLabel#MutedText {{
        color: {t["text_secondary"]};
        font-size: 12px;
    }}

    /* Cards */
    QFrame#Card {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 10px;
    }}

    QFrame#CardElevated {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 12px;
    }}

    /* Nav Buttons */
    QPushButton[variant="nav"] {{
        background-color: transparent;
        color: {t["text_secondary"]};
        border: none;
        border-radius: 8px;
        padding: 9px 12px;
        text-align: left;
        font-weight: 500;
    }}
    QPushButton[variant="nav"]:hover {{
        background-color: {t["bg_surface_alt"]};
        color: {t["text_primary"]};
    }}
    QPushButton[variant="nav"][active="true"] {{
        background-color: {t["accent_soft"]};
        color: {t["accent"]};
        font-weight: 600;
    }}

    /* Primary Button */
    QPushButton[variant="primary"] {{
        background-color: {t["accent"]};
        color: {t["accent_text"]};
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {t["accent_hover"]};
    }}
    QPushButton[variant="primary"]:disabled {{
        background-color: {t["bg_surface_alt"]};
        color: {t["text_muted"]};
    }}

    /* Secondary Button */
    QPushButton[variant="secondary"] {{
        background-color: {t["bg_surface_alt"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 500;
    }}
    QPushButton[variant="secondary"]:hover {{
        border-color: {t["accent"]};
    }}
    QPushButton[variant="secondary"]:disabled {{
        color: {t["text_muted"]};
    }}

    /* Danger Button */
    QPushButton[variant="danger"] {{
        background-color: {t["danger_soft"]};
        color: {t["danger"]};
        border: 1px solid {t["danger"]};
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: {t["danger"]};
        color: #ffffff;
    }}
    QPushButton[variant="danger"]:disabled {{
        opacity: 0.5;
    }}

    /* Ghost / Icon Button */
    QPushButton[variant="ghost"] {{
        background-color: transparent;
        color: {t["text_secondary"]};
        border: none;
        border-radius: 6px;
        padding: 6px 10px;
    }}
    QPushButton[variant="ghost"]:hover {{
        background-color: {t["bg_surface_alt"]};
        color: {t["text_primary"]};
    }}

    /* Inputs */
    QLineEdit, QComboBox, QSpinBox {{
        background-color: {t["bg_input"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 7px 10px;
        min-height: 20px;
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {t["border_focus"]};
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {t["text_muted"]};
        background-color: {t["bg_surface_alt"]};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t["bg_surface"]};
        color: {t["text_primary"]};
        border: 1px solid {t["border"]};
        selection-background-color: {t["accent_soft"]};
        selection-color: {t["accent"]};
        outline: none;
    }}

    /* Checkboxes & Radio */
    QCheckBox, QRadioButton {{
        spacing: 8px;
        color: {t["text_primary"]};
        background: transparent;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 17px;
        height: 17px;
        border: 1px solid {t["border"]};
        background-color: {t["bg_input"]};
    }}
    QCheckBox::indicator {{
        border-radius: 4px;
    }}
    QRadioButton::indicator {{
        border-radius: 9px;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {t["accent"]};
        border-color: {t["accent"]};
    }}

    /* ProgressBar */
    QProgressBar {{
        background-color: {t["bg_surface_alt"]};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {t["accent"]};
        border-radius: 4px;
    }}

    /* Log Console */
    QPlainTextEdit#LogConsole {{
        background-color: {t["bg_console"]};
        color: #cbd5e1;
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 10px;
        font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
        font-size: 12px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {t["border"]};
        min-height: 24px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t["text_muted"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Menus */
    QMenu {{
        background-color: {t["bg_surface"]};
        border: 1px solid {t["border"]};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 7px 14px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background-color: {t["accent_soft"]};
        color: {t["accent"]};
    }}
    """
