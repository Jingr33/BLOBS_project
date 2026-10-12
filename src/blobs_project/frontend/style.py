from blobs_project import config

STYLE_SHEET = f"""
    QMainWindow, QWidget {{
        background: {config.BACKGROUND};
        color: {config.TEXT};
        font-family: {config.FONT_FAMILY};
    }}
    QFrame#panel {{
        background: {config.PANEL};
        border: 1px solid {config.PANEL_BORDER};
        border-radius: 12px;
    }}
    QFrame#regulation {{
        background: transparent;
        border: none;
    }}
    QFrame#regulation QLabel {{
        background: transparent;
        border: none;
    }}
    QDoubleSpinBox {{
        background: {config.BUTTON_BACKGROUND};
        border: 1px solid {config.BUTTON_BORDER};
        border-radius: 7px;
        padding: 6px 8px;
        color: {config.TEXT};
        font-weight: 600;
    }}
    QDoubleSpinBox:hover {{
        border-color: {config.CYAN};
    }}
    QDoubleSpinBox:focus {{
        border-color: {config.CYAN};
    }}
    QDoubleSpinBox:disabled {{
        background: {config.PANEL};
        border-color: {config.PANEL_BORDER};
        color: {config.MUTED};
    }}
    QLabel#eyebrow {{
        color: {config.CYAN};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#sectionTitle {{
        color: {config.CYAN};
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 3px;
    }}
    QLabel#title {{ font-size: 25px; font-weight: 700; }}
    QLabel#muted {{ color: {config.MUTED}; }}
    QLabel#profile {{ color: {config.MUTED}; font-size: 12px; }}
    QPushButton {{
        background: {config.BUTTON_BACKGROUND};
        border: 1px solid {config.BUTTON_BORDER};
        border-radius: 7px;
        padding: 9px 14px;
        color: {config.TEXT};
    }}
    QPushButton:hover {{
        background: {config.BUTTON_HOVER_BACKGROUND};
        border-color: {config.CYAN};
    }}
    QPushButton#primary {{
        background: {config.CYAN};
        color: {config.PRIMARY_TEXT};
        font-weight: 700;
        border: 0;
    }}
    QPushButton#danger {{
        background: {config.RED};
        color: {config.DANGER_TEXT};
        font-weight: 700;
        border: 0;
    }}
    QPushButton:disabled,
    QPushButton#primary:disabled,
    QPushButton#danger:disabled {{
        background: {config.PANEL};
        border: 1px solid {config.PANEL_BORDER};
        color: {config.MUTED};
        font-weight: 600;
    }}
    QPushButton#small {{ padding: 6px 10px; }}
    QPushButton#nav {{
        background: transparent;
        border: 1px solid {config.PANEL_BORDER};
        border-radius: 7px;
        padding: 7px 14px;
        color: {config.MUTED};
        font-weight: 600;
    }}
    QPushButton#nav:hover {{
        color: {config.TEXT};
        border-color: {config.CYAN};
    }}
    QPushButton#navActive {{
        background: {config.CYAN};
        border: 1px solid {config.CYAN};
        border-radius: 7px;
        padding: 7px 14px;
        color: {config.PRIMARY_TEXT};
        font-weight: 700;
    }}
"""
