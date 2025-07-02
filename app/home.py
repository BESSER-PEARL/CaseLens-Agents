from pathlib import Path

import streamlit as st


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text(encoding='utf-8')


def home():
    readme = read_markdown_file("app/HOME.md")
    st.markdown(readme)
