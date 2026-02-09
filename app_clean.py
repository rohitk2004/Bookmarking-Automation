
import streamlit as st
import asyncio
import os
import traceback
from bot import run_batch_submission, setup_credentials
import threading
import sys

# Fix for Windows asyncio loop with Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ensure Playwright Browsers are Installed (Critical for Streamlit Cloud)
if sys.platform != "win32":
    try:
        import subprocess
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), ".playwright")
        print(f"Installing Playwright browsers to {os.environ['PLAYWRIGHT_BROWSERS_PATH']}...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"⚠️ Failed to auto-install Playwright browsers: {e}")

# Configuration
st.set_page_config(page_title="Bookmarking Panel", page_icon="🚀", layout="wide")

# Hero Section
st.markdown("""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2.5rem; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
    <h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">🚀 Bookmarking Panel</h1>
    <p style="color: rgba(255, 255, 255, 0.9); font-size: 1.2rem; margin: 0.5rem 0 0 0;">Free High-Authority Social Bookmarking Tool (2026 Edition)</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 1.5rem;">🔑 Platform Settings</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">Configure your bookmarking platforms</p>
    </div>
    """, unsafe_allow_html=True)
    
    default_user = "jetski_tester_02"
    default_pass = "TesterPassword123!"
    
    supported_sites = [
        "https://www.abookmarking.com",
        "https://www.social-bookmarkingsites.com",
        "https://www.pbookmarking.com",
        "https://www.freebookmarkingsite.com",
        "https://www.free-socialbookmarking.com",
        "https://www.newsocialbookmarkingsite.com",
        "https://www.bookmarkingfree.com",
        "https://www.rbookmarking.com",
        "https://www.ybookmarking.com",
        "https://www.fastbookmarkings.com/",
        "http://www.letsdobookmark.com/"
    ]
    
    site_settings = {}
    
    st.markdown("""
    <div style="background: rgba(103, 126, 234, 0.1); padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem;">
        <p style="color: white; margin: 0; font-size: 0.9rem; font-weight: 600;">⚡ Quick Actions</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("✅ Select All", use_container_width=True):
            for i in range(len(supported_sites)):
                st.session_state[f"enable_{i}"] = True
            st.rerun()
            
    with col_q2:
        if st.button("❌ Clear All", use_container_width=True):
            for i in range(len(supported_sites)):
                st.session_state[f"enable_{i}"] = False
            st.rerun()
    
    st.divider()

    
    for i, site_url in enumerate(supported_sites):
        domain_display = site_url.replace("https://www.", "").replace("http://", "").split("/")[0]
        
        key_name = f"enable_{i}"
        if key_name not in st.session_state:
             st.session_state[key_name] = True if i == 0 else False
             
        is_checked = st.session_state[key_name]
        
        with st.expander(f"{i+1}. {domain_display}", expanded=is_checked):
            enabled = st.checkbox(f"Enable", key=key_name)
            user = st.text_input(f"Username", value=default_user, key=f"user_{i}")
            pwd = st.text_input(f"Password", value=default_pass, type="password", key=f"pass_{i}")
            
            site_settings[site_url] = {
                "enabled": enabled,
                "username": user,
                "password": pwd
            }

    st.divider()
    
    st.markdown("""
    <div style="background: rgba(67, 233, 123, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
        <p style="color: white; margin: 0; font-size: 0.9rem; font-weight: 600;">⚡ Browser Settings</p>
    </div>
    """, unsafe_allow_html=True)
    
    headless = st.checkbox("🖥️ Headless Mode (Background)", value=False, help="Run browser in background without UI")
    
    st.markdown("""
    <div style="background: rgba(255, 193, 7, 0.1); padding: 0.8rem; border-radius: 6px; margin-top: 0.5rem; border-left: 3px solid #ffc107;">
        <p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.75rem;">
            ℹ️ <strong>Note:</strong> Headful mode (default) is more reliable for Cloudflare-protected sites
        </p>
    </div>
    """, unsafe_allow_html=True)


# Main Interface
st.markdown("""
<div style="margin-bottom: 1rem;">
    <h2 style="color: white; margin: 0; font-size: 1.8rem;">🎯 Submit Your Links</h2>
    <p style="color: rgba(255, 255, 255, 0.7); margin: 0.5rem 0 0 0; font-size: 0.95rem;">Paste your URLs below and let our automation handle the rest</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    <div style="background: linear-gradient(to bottom, rgba(103, 126, 234, 0.1), rgba(103, 126, 234, 0.05)); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(103, 126, 234, 0.3); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 0.8rem; border-radius: 10px; margin-right: 1rem;">
                <span style="font-size: 1.5rem;">🔗</span>
            </div>
            <div>
                <h3 style="color: white; margin: 0; font-size: 1.3rem;">Links to Bookmark</h3>
                <p style="color: rgba(255, 255, 255, 0.6); margin: 0; font-size: 0.85rem;">Enter one URL per line</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    links_input = st.text_area(
        "URLs", 
        height=250, 
        placeholder="https://example.com/page1\nhttps://example.com/page2\nhttps://mysite.com/blog-post\n...",
        label_visibility="collapsed"
    )
    
    st.markdown("""
    <div style="background: rgba(103, 126, 234, 0.08); padding: 1rem; border-radius: 8px; border-left: 3px solid #667eea; margin-top: 0.5rem;">
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0; font-size: 0.85rem;">
            <strong style="color: #a8b3ff;">💡 Pro Tip:</strong> Make sure all URLs start with <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.4rem; border-radius: 3px;">https://</code> for best results
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(to bottom, rgba(240, 147, 251, 0.1), rgba(245, 87, 108, 0.05)); 
                padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(240, 147, 251, 0.3); margin-bottom: 1rem;">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                        padding: 0.8rem; border-radius: 10px; margin-right: 1rem;">
                <span style="font-size: 1.5rem;">⚙️</span>
            </div>
            <div>
                <h3 style="color: white; margin: 0; font-size: 1.3rem;">Controls</h3>
                <p style="color: rgba(255, 255, 255, 0.6); margin: 0; font-size: 0.85rem;">Manage your submissions</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    start_btn = st.button("🚀 Start Submission", type="primary", use_container_width=True)
    stop_btn = st.button("🛑 Stop / Clear", type="secondary", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(to right, rgba(67, 233, 123, 0.1), rgba(56, 249, 215, 0.05)); 
                padding: 1rem; border-radius: 10px; border: 1px solid rgba(67, 233, 123, 0.3);">
        <p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
            <strong>📊 Status Monitor</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    status_log = st.empty()
    progress_bar = st.progress(0)
    
    st.markdown("""
    <div style="background: rgba(67, 233, 123, 0.08); padding: 0.8rem; border-radius: 8px; margin-top: 1rem;">
        <p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.8rem; text-align: center;">
            ⏱️ Average: 30-60s per site
        </p>
    </div>
    """, unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)

# Stats Row
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 2rem;">11+</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Platforms</p>
    </div>
    """, unsafe_allow_html=True)

with col_stat2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 2rem;">DA 40+</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Authority Sites</p>
    </div>
    """, unsafe_allow_html=True)

with col_stat3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 2rem;">100%</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Automated</p>
    </div>
    """, unsafe_allow_html=True)

with col_stat4:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
        <h2 style="color: white; margin: 0; font-size: 2rem;">⚡</h2>
        <p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Fast Index</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Backend Logic Integration
if start_btn:
    site_configs = []
    
    for site_url, settings in site_settings.items():
        if settings["enabled"]:
            if not settings["username"] or not settings["password"]:
                st.toast(f"⚠️ Skipping {site_url}: Missing credentials!", icon="⚠️")
            else:
                site_configs.append({
                    "url": site_url,
                    "username": settings["username"],
                    "password": settings["password"]
                })
            
    if not site_configs:
        st.error("Please enable at least one site and provide credentials!")
    else:
        urls = [url.strip() for url in links_input.split('\n') if url.strip()]
        
        if not urls:
            st.warning("No URLs provided.")
        else:
            status_log.write(f"Preparing to submit {len(urls)} links to {len(site_configs)} sites...")
            
            try:
                log_container = st.container()
                
                async def run_process():
                    def update_progress(current, total, message):
                        progress_bar.progress(current / total)
                        status_log.write(f"**[{current}/{total}]** {message}")

                    is_headless = headless
                    if sys.platform != "win32":
                         is_headless = True
                         st.toast("☁️ Cloud Environment detected: Forcing Headless Mode", icon="ℹ️")

                    await run_batch_submission(
                        urls=urls, 
                        site_configs=site_configs,
                        headless=is_headless,
                        progress_callback=update_progress
                    )
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(run_process())
                finally:
                    loop.close()
                
                st.success("Batch Submission Cycle Complete!")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.code(traceback.format_exc())

if stop_btn:
    st.rerun()
