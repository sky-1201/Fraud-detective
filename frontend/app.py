# frontend/app.py
import streamlit as st

# 绝对不要带 frontend. 前缀！
from config import APP_TITLE, APP_ICON
from components.dashboard import render_radar_dashboard
from components.chat_stream import render_investigation_panel

# 1. 页面基础设置 (必须在所有 st 命令之前调用)
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# 2. 初始化全局 Session State
if 'selected_suspect' not in st.session_state:
    st.session_state['selected_suspect'] = ""

# 3. 页面标题
st.title(APP_TITLE)
st.markdown("---")

# 4. 组装微服务 UI 组件
col1, col2 = st.columns([1, 1.2])

with col1:
    render_radar_dashboard()

with col2:
    render_investigation_panel()