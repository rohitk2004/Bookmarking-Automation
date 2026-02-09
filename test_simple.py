import streamlit as st

st.set_page_config(page_title="Test", layout="wide")

st.markdown("""
<div style="background: red; padding: 2rem; color: white;">
    <h1>Test HTML</h1>
</div>
""", unsafe_allow_html=True)

st.write("If you see a red box above, HTML is working!")
