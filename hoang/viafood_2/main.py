# main.py
import streamlit as st
from ui.streamlit_app import StreamlitUI

def main():
    """Hàm chính khởi chạy ứng dụng"""
    ui = StreamlitUI()
    ui.render_sidebar()
    ui.render_main_content()

if __name__ == "__main__":
    main()
