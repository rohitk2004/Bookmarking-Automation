
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
# Ensure Playwright Browsers are Installed (Critical for Streamlit Cloud)
try:
    import subprocess
    # force location to be within user directory to avoid permission issues
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), ".playwright")
    
    # Just install chromium
    print(f"Installing Playwright browsers to {os.environ['PLAYWRIGHT_BROWSERS_PATH']}...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
except Exception as e:
    print(f"⚠️ Failed to auto-install Playwright browsers: {e}")

# Configuration
st.set_page_config(page_title="Antigravity Bookmarker", page_icon="🚀", layout="wide")

st.title("🚀 Antigravity Bookmarking Panel")
st.markdown("Automated 3-Phase Submission Bot (Playwright)")

# Sidebar for Credentials
with st.sidebar:
    st.header("🔑 Credentials & Sites")
    
    # Defaults
    default_user = "jetski_tester_02"
    default_pass = "TesterPassword123!"
    
    # List of all supported sites
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
    
    # Store settings for each site
    site_settings = {}
    
    st.markdown("### Quick Actions")
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        if st.button("Select All", use_container_width=True):
            for i in range(len(supported_sites)):
                st.session_state[f"enable_{i}"] = True
            st.rerun()
            
    with col_q2:
        if st.button("Deselect All", use_container_width=True):
            for i in range(len(supported_sites)):
                st.session_state[f"enable_{i}"] = False
            st.rerun()
    
    st.divider()
    
    for i, site_url in enumerate(supported_sites):
        domain_display = site_url.replace("https://www.", "").replace("http://", "").split("/")[0]
        
        # Determine if enabled
        # Streamlit best practice: if key is in session state, 'value' arg is ignored or causes warning if modified
        # We initialized keys in the Quick Actions, so we just rely on key presence
        
        # Ensure key exists with default if not present
        key_name = f"enable_{i}"
        if key_name not in st.session_state:
             st.session_state[key_name] = True if i == 0 else False
             
        is_checked = st.session_state[key_name]
        
        with st.expander(f"{i+1}. {domain_display}", expanded=is_checked):
            # Unique keys for widget stability
            # Do NOT pass 'value' if using 'key' and manipulating state elsewhere
            enabled = st.checkbox(f"Enable", key=key_name)
            user = st.text_input(f"Username", value=default_user, key=f"user_{i}")
            pwd = st.text_input(f"Password", value=default_pass, type="password", key=f"pass_{i}")
            
            site_settings[site_url] = {
                "enabled": enabled,
                "username": user,
                "password": pwd
            }

    st.divider()
    
    # Default to False (Headful) as it is more reliable against Cloudflare
    headless = st.checkbox("Headless Mode", value=False, help="Run browser in background")

# Main Interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🔗 Links to Bookmark")
    links_input = st.text_area("Paste URLs here (one per line)", height=300, placeholder="http://example.com\nhttp://mysite.com/post1\n...")

with col2:
    st.subheader("⚙️ Controls")
    start_btn = st.button("🚀 Start Submission", type="primary", use_container_width=True)
    stop_btn = st.button("🛑 Stop / Clear", type="secondary", use_container_width=True)
    
    st.info("Status updates will appear below.")
    status_log = st.empty()
    progress_bar = st.progress(0)

# Backend Logic Integration
if start_btn:
    # 1. Build Site Configs from Dynamic Settings
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
            
            # Run the async bot in a way that Streamlit allows
            try:
                # Create a placeholder for logs
                log_container = st.container()
                
                async def run_process():
                    # Progress callback to update UI
                    def update_progress(current, total, message):
                        progress_bar.progress(current / total)
                        status_log.write(f"**[{current}/{total}]** {message}")

                    await run_batch_submission(
                        urls=urls, 
                        site_configs=site_configs,
                        headless=headless,
                        progress_callback=update_progress
                    )
                
                # Robust asyncio handling for Streamlit/Windows
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
