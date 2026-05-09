"""
Skaner Momentum — AI-wspomagana analiza techniczna akcji
=========================================================

Punkt wejścia aplikacji Streamlit.

Uruchamianie:
    streamlit run streamlit_app.py
"""

from app.ui.main_view import render_app


def main() -> None:
    """Bootstrap aplikacji Streamlit."""
    render_app()


if __name__ == "__main__":
    main()
