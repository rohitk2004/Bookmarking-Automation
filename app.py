
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
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"⚠️ Failed to auto-install Playwright browsers: {e}")

# Configuration
st.set_page_config(page_title="Bookmarking Panel", page_icon="🚀", layout="wide")

# ==========================================
# CUSTOM CSS & STYLING (FLUSH LEFT FIX)
# ==========================================
# All HTML strings are flushed to the left to prevent Markdown code block detection

HERO_HTML = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2.5rem; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
<h1 style="color: white; margin: 0; font-size: 2.5rem; font-weight: 700;">🚀 Bookmarking Panel</h1>
<p style="color: rgba(255, 255, 255, 0.9); font-size: 1.2rem; margin: 0.5rem 0 0 0;">Free High-Authority Social Bookmarking Tool (2026 Edition)</p>
</div>
"""

SIDEBAR_HEADER_HTML = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; margin-bottom: 1.5rem; text-align: center;">
<h2 style="color: white; margin: 0; font-size: 1.5rem;">🔑 Platform Settings</h2>
<p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.85rem;">Configure your bookmarking platforms</p>
</div>
"""

SIDEBAR_QUICK_ACTIONS_HTML = """
<div style="background: rgba(103, 126, 234, 0.1); padding: 0.8rem; border-radius: 8px; margin-bottom: 1rem;">
<p style="color: white; margin: 0; font-size: 0.9rem; font-weight: 600;">⚡ Quick Actions</p>
</div>
"""

SIDEBAR_BROWSER_SETTINGS_HTML = """
<div style="background: rgba(67, 233, 123, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
<p style="color: white; margin: 0; font-size: 0.9rem; font-weight: 600;">⚡ Browser Settings</p>
</div>
"""

SIDEBAR_NOTE_HTML = """
<div style="background: rgba(255, 193, 7, 0.1); padding: 0.8rem; border-radius: 6px; margin-top: 0.5rem; border-left: 3px solid #ffc107;">
<p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.75rem;">
ℹ️ <strong>Note:</strong> Headful mode (default) is more reliable for Cloudflare-protected sites
</p>
</div>
"""

MAIN_HEADER_HTML = """
<div style="margin-bottom: 1rem;">
<h2 style="color: white; margin: 0; font-size: 1.8rem;">🎯 Submit Your Links</h2>
<p style="color: rgba(255, 255, 255, 0.7); margin: 0.5rem 0 0 0; font-size: 0.95rem;">Paste your URLs below and let our automation handle the rest</p>
</div>
"""

LINKS_CARD_HTML = """
<div style="background: linear-gradient(to bottom, rgba(103, 126, 234, 0.1), rgba(103, 126, 234, 0.05)); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(103, 126, 234, 0.3); margin-bottom: 1rem;">
<div style="display: flex; align-items: center; margin-bottom: 1rem;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 0.8rem; border-radius: 10px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">🔗</span>
</div>
<div>
<h3 style="color: white; margin: 0; font-size: 1.3rem;">Links to Bookmark</h3>
<p style="color: rgba(255, 255, 255, 0.6); margin: 0; font-size: 0.85rem;">Enter one URL per line</p>
</div>
</div>
</div>
"""

PRO_TIP_HTML = """
<div style="background: rgba(103, 126, 234, 0.08); padding: 1rem; border-radius: 8px; border-left: 3px solid #667eea; margin-top: 0.5rem;">
<p style="color: rgba(255, 255, 255, 0.8); margin: 0; font-size: 0.85rem;">
<strong style="color: #a8b3ff;">💡 Pro Tip:</strong> Make sure all URLs start with <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.4rem; border-radius: 3px;">https://</code> for best results
</p>
</div>
"""

CONTROLS_CARD_HTML = """
<div style="background: linear-gradient(to bottom, rgba(240, 147, 251, 0.1), rgba(245, 87, 108, 0.05)); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(240, 147, 251, 0.3); margin-bottom: 1rem;">
<div style="display: flex; align-items: center; margin-bottom: 1rem;">
<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 0.8rem; border-radius: 10px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">⚙️</span>
</div>
<div>
<h3 style="color: white; margin: 0; font-size: 1.3rem;">Controls</h3>
<p style="color: rgba(255, 255, 255, 0.6); margin: 0; font-size: 0.85rem;">Manage your submissions</p>
</div>
</div>
</div>
"""

STATUS_MONITOR_HTML = """
<div style="background: linear-gradient(to right, rgba(67, 233, 123, 0.1), rgba(56, 249, 215, 0.05)); padding: 1rem; border-radius: 10px; border: 1px solid rgba(67, 233, 123, 0.3);">
<p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
<strong>📊 Status Monitor</strong>
</p>
</div>
"""

TIME_ESTIMATE_HTML = """
<div style="background: rgba(67, 233, 123, 0.08); padding: 0.8rem; border-radius: 8px; margin-top: 1rem;">
<p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.8rem; text-align: center;">
⏱️ Average: 30-60s per site
</p>
</div>
"""

STATS_1_HTML = """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
<h2 style="color: white; margin: 0; font-size: 2rem;">11+</h2>
<p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Platforms</p>
</div>
"""

STATS_2_HTML = """
<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
<h2 style="color: white; margin: 0; font-size: 2rem;">DA 40+</h2>
<p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Authority Sites</p>
</div>
"""

STATS_3_HTML = """
<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
<h2 style="color: white; margin: 0; font-size: 2rem;">100%</h2>
<p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Automated</p>
</div>
"""

STATS_4_HTML = """
<div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); padding: 1.5rem; border-radius: 10px; text-align: center;">
<h2 style="color: white; margin: 0; font-size: 2rem;">⚡</h2>
<p style="color: rgba(255, 255, 255, 0.8); margin: 0.5rem 0 0 0; font-size: 0.9rem;">Fast Index</p>
</div>
"""

WHY_USE_HTML = """
<div style="background: linear-gradient(135deg, rgba(31, 119, 180, 0.2) 0%, rgba(31, 119, 180, 0.05) 100%); padding: 2.5rem; border-radius: 15px; border: 1px solid rgba(31, 119, 180, 0.3); margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(31, 119, 180, 0.1);">
<div style="text-align: center; margin-bottom: 2rem;">
<h2 style="color: #4facfe; margin: 0; font-size: 2rem; font-weight: 700;">🎯 Why Use Social Bookmarking?</h2>
<div style="width: 60px; height: 4px; background: linear-gradient(90deg, #4facfe, #00f2fe); margin: 1rem auto; border-radius: 2px;"></div>
</div>
<p style="color: white; font-size: 1.15rem; line-height: 1.8; margin: 0 0 1.5rem 0; text-align: center;">
<strong style="color: #4facfe;">Welcome to the automated SEO toolkit.</strong> Social bookmarking remains a cornerstone of Off-Page SEO strategy. 
By submitting your URLs to high-authority bookmarking platforms, you create <strong style="color: #00f2fe;">"social signals"</strong> that help search 
engine crawlers discover and index your content faster.
</p>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-top: 2rem;">
<div style="text-align: center; padding: 1.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
<div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🚀</div>
<h4 style="color: #4facfe; margin: 0.5rem 0; font-size: 1.1rem;">Faster Indexing</h4>
<p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.85rem;">Get indexed by Google in hours, not days</p>
</div>
<div style="text-align: center; padding: 1.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
<div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
<h4 style="color: #4facfe; margin: 0.5rem 0; font-size: 1.1rem;">Better Rankings</h4>
<p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.85rem;">Build quality backlinks from DA 40+ sites</p>
</div>
<div style="text-align: center; padding: 1.5rem; background: rgba(255, 255, 255, 0.05); border-radius: 10px;">
<div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💰</div>
<h4 style="color: #4facfe; margin: 0.5rem 0; font-size: 1.1rem;">Save Time</h4>
<p style="color: rgba(255, 255, 255, 0.7); margin: 0; font-size: 0.85rem;">Automate manual 2-hour tasks to 5 minutes</p>
</div>
</div>
</div>
"""

TRUST_INDICATORS_HTML = """
<div style="background: linear-gradient(90deg, rgba(67, 233, 123, 0.1), rgba(56, 249, 215, 0.1)); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; text-align: center; border: 1px solid rgba(67, 233, 123, 0.2);">
<div style="display: flex; justify-content: space-around; align-items: center; flex-wrap: wrap; gap: 2rem;">
<div>
<div style="color: #43e97b; font-size: 2rem; font-weight: 700;">11+ Sites</div>
<div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">High DA Platforms</div>
</div>
<div>
<div style="color: #43e97b; font-size: 2rem; font-weight: 700;">100% Free</div>
<div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">No Hidden Costs</div>
</div>
<div>
<div style="color: #43e97b; font-size: 2rem; font-weight: 700;">⚡ Fast</div>
<div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">30-60s per site</div>
</div>
<div>
<div style="color: #43e97b; font-size: 2rem; font-weight: 700;">🔒 Safe</div>
<div style="color: rgba(255, 255, 255, 0.6); font-size: 0.9rem;">White-hat SEO</div>
</div>
</div>
</div>
"""

PREMIUM_FEATURES_HTML = """
<div style="background: linear-gradient(135deg, rgba(46, 204, 113, 0.2) 0%, rgba(46, 204, 113, 0.05) 100%); padding: 2.5rem; border-radius: 15px; border: 1px solid rgba(46, 204, 113, 0.3); margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(46, 204, 113, 0.1);">
<div style="text-align: center; margin-bottom: 2rem;">
<h2 style="color: #43e97b; margin: 0; font-size: 2rem; font-weight: 700;">⭐ Premium Features</h2>
<div style="width: 60px; height: 4px; background: linear-gradient(90deg, #43e97b, #38f9d7); margin: 1rem auto; border-radius: 2px;"></div>
</div>
<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem;">
<div style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #43e97b;">
<div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
<div style="background: linear-gradient(135deg, #43e97b, #38f9d7); padding: 0.6rem; border-radius: 8px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">🌐</span>
</div>
<h3 style="color: #43e97b; margin: 0; font-size: 1.2rem;">Multi-Platform Support</h3>
</div>
<p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-size: 0.95rem; line-height: 1.6;">
Submit to 11+ high-DA bookmarking sites simultaneously. Save hours of manual work with bulk submission.
</p>
</div>
<div style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #43e97b;">
<div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
<div style="background: linear-gradient(135deg, #43e97b, #38f9d7); padding: 0.6rem; border-radius: 8px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">🤖</span>
</div>
<h3 style="color: #43e97b; margin: 0; font-size: 1.2rem;">Smart Automation</h3>
</div>
<p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-size: 0.95rem; line-height: 1.6;">
Handles account selection, login, and form filling automatically. Zero manual intervention required.
</p>
</div>
<div style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #43e97b;">
<div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
<div style="background: linear-gradient(135deg, #43e97b, #38f9d7); padding: 0.6rem; border-radius: 8px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">📊</span>
</div>
<h3 style="color: #43e97b; margin: 0; font-size: 1.2rem;">Real-Time Monitoring</h3>
</div>
<p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-size: 0.95rem; line-height: 1.6;">
Track submission progress with live logs. Know exactly what's happening at every step.
</p>
</div>
<div style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px; border-left: 4px solid #43e97b;">
<div style="display: flex; align-items: center; margin-bottom: 0.8rem;">
<div style="background: linear-gradient(135deg, #43e97b, #38f9d7); padding: 0.6rem; border-radius: 8px; margin-right: 1rem;">
<span style="font-size: 1.5rem;">🎯</span>
</div>
<h3 style="color: #43e97b; margin: 0; font-size: 1.2rem;">SEO Optimized</h3>
</div>
<p style="margin: 0; color: rgba(255, 255, 255, 0.8); font-size: 0.95rem; line-height: 1.6;">
Creates powerful do-follow backlinks from authority sites for faster indexing and better rankings.
</p>
</div>
</div>
</div>
"""

HOW_IT_WORKS_HTML = """
<div style="background: linear-gradient(135deg, rgba(103, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.05) 100%); padding: 2.5rem; border-radius: 15px; border: 1px solid rgba(103, 126, 234, 0.3); margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(103, 126, 234, 0.1);">
<div style="text-align: center; margin-bottom: 1.5rem;">
<h2 style="color: #a8b3ff; margin: 0; font-size: 2rem; font-weight: 700;">📋 How It Works</h2>
<div style="width: 60px; height: 4px; background: linear-gradient(90deg, #667eea, #764ba2); margin: 1rem auto; border-radius: 2px;"></div>
<p style="color: rgba(255, 255, 255, 0.6); font-size: 0.95rem; margin: 0.5rem 0 0 0;">Simple 4-step process to boost your SEO</p>
</div>
<div style="color: white; max-width: 800px; margin: 0 auto;">
<div style="display: flex; align-items: start; margin-bottom: 2rem; background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem; margin-right: 1.5rem; flex-shrink: 0;">1</div>
<div>
<h3 style="color: #a8b3ff; margin: 0 0 0.5rem 0; font-size: 1.3rem;">📝 Enter Your URLs</h3>
<p style="color: rgba(255, 255, 255, 0.85); margin: 0; line-height: 1.6;">
Paste your links in the text area (one per line). Make sure they start with <code style="background: rgba(0,0,0,0.3); padding: 0.2rem 0.5rem; border-radius: 4px;">https://</code>
</p>
</div>
</div>
<div style="display: flex; align-items: start; margin-bottom: 2rem; background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem; margin-right: 1.5rem; flex-shrink: 0;">2</div>
<div>
<h3 style="color: #a8b3ff; margin: 0 0 0.5rem 0; font-size: 1.3rem;">⚙️ Select Platforms</h3>
<p style="color: rgba(255, 255, 255, 0.85); margin: 0; line-height: 1.6;">
Choose bookmarking sites from the sidebar. Use "Select All" for maximum reach or pick specific high-DA platforms.
</p>
</div>
</div>
<div style="display: flex; align-items: start; margin-bottom: 2rem; background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem; margin-right: 1.5rem; flex-shrink: 0;">3</div>
<div>
<h3 style="color: #a8b3ff; margin: 0 0 0.5rem 0; font-size: 1.3rem;">🚀 Start Automation</h3>
<p style="color: rgba(255, 255, 255, 0.85); margin: 0; line-height: 1.6;">
Click "Start Submission" and watch the magic happen. Monitor real-time progress in the status panel.
</p>
</div>
</div>
<div style="display: flex; align-items: start; background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 12px;">
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.5rem; margin-right: 1.5rem; flex-shrink: 0;">4</div>
<div>
<h3 style="color: #a8b3ff; margin: 0 0 0.5rem 0; font-size: 1.3rem;">✅ Verify & Index</h3>
<p style="color: rgba(255, 255, 255, 0.85); margin: 0; line-height: 1.6;">
Once complete, use Google Search Console or an instant indexer to notify search engines about your new backlinks.
</p>
</div>
</div>
</div>
</div>
"""

FAQ_HTML = """
<div style="background: linear-gradient(135deg, rgba(240, 147, 251, 0.15) 0%, rgba(245, 87, 108, 0.05) 100%); padding: 2.5rem; border-radius: 15px; border: 1px solid rgba(240, 147, 251, 0.3); margin-bottom: 2rem;">
<div style="text-align: center; margin-bottom: 2rem;">
<h2 style="color: #f093fb; margin: 0; font-size: 2rem; font-weight: 700;">❓ Frequently Asked Questions</h2>
<div style="width: 60px; height: 4px; background: linear-gradient(90deg, #f093fb, #f5576c); margin: 1rem auto; border-radius: 2px;"></div>
</div>
<div style="max-width: 900px; margin: 0 auto;">
<details style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; cursor: pointer;">
<summary style="color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer;">🤔 Is this tool completely free?</summary>
<p style="color: rgba(255, 255, 255, 0.8); margin: 1rem 0 0 0; line-height: 1.6;">
Yes! This tool is 100% free with no hidden costs. All 11+ bookmarking platforms can be used without any charges.
</p>
</details>
<details style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; cursor: pointer;">
<summary style="color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer;">⏱️ How long does it take?</summary>
<p style="color: rgba(255, 255, 255, 0.8); margin: 1rem 0 0 0; line-height: 1.6;">
On average, each site takes 30-60 seconds to process. For all 11 sites, expect around 10-15 minutes total.
</p>
</details>
<details style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; cursor: pointer;">
<summary style="color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer;">🔒 Is it safe for my website?</summary>
<p style="color: rgba(255, 255, 255, 0.8); margin: 1rem 0 0 0; line-height: 1.6;">
Absolutely! This is white-hat SEO. We only submit to legitimate, high-authority bookmarking sites that Google recognizes.
</p>
</details>
<details style="background: rgba(255, 255, 255, 0.05); padding: 1.5rem; border-radius: 10px; cursor: pointer;">
<summary style="color: white; font-size: 1.1rem; font-weight: 600; cursor: pointer;">📈 Will this improve my rankings?</summary>
<p style="color: rgba(255, 255, 255, 0.8); margin: 1rem 0 0 0; line-height: 1.6;">
Social bookmarking helps with faster indexing and creates quality backlinks. While not a magic bullet, it's an important part of a comprehensive SEO strategy.
</p>
</details>
</div>
</div>
"""

FOOTER_HTML = """
<div style="background: linear-gradient(135deg, rgba(103, 126, 234, 0.1), rgba(118, 75, 162, 0.1)); padding: 2rem; border-radius: 12px; text-align: center; margin-top: 3rem;">
<p style="color: rgba(255, 255, 255, 0.6); margin: 0; font-size: 0.9rem;">
Made with ❤️ for SEO Professionals | © 2026 Bookmarking Panel
</p>
<p style="color: rgba(255, 255, 255, 0.4); margin: 0.5rem 0 0 0; font-size: 0.8rem;">
🚀 Automate your SEO • 📈 Boost your rankings • ⚡ Save time
</p>
</div>
"""

# Apply Global Styling for details element
st.markdown("""
<style>
details > summary {
    list-style: none;
}
details > summary::-webkit-details-marker {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# Hero Section
st.markdown(HERO_HTML, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(SIDEBAR_HEADER_HTML, unsafe_allow_html=True)
    
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
    
    st.markdown(SIDEBAR_QUICK_ACTIONS_HTML, unsafe_allow_html=True)
    
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
    
    st.markdown(SIDEBAR_BROWSER_SETTINGS_HTML, unsafe_allow_html=True)
    
    headless = st.checkbox("🖥️ Headless Mode (Background)", value=False, help="Run browser in background without UI")
    
    st.markdown(SIDEBAR_NOTE_HTML, unsafe_allow_html=True)


# Main Interface
st.markdown(MAIN_HEADER_HTML, unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(LINKS_CARD_HTML, unsafe_allow_html=True)
    
    links_input = st.text_area(
        "URLs", 
        height=250, 
        placeholder="https://example.com/page1\nhttps://example.com/page2\nhttps://mysite.com/blog-post\n...",
        label_visibility="collapsed"
    )
    
    st.markdown(PRO_TIP_HTML, unsafe_allow_html=True)

with col2:
    st.markdown(CONTROLS_CARD_HTML, unsafe_allow_html=True)
    
    start_btn = st.button("🚀 Start Submission", type="primary", use_container_width=True)
    stop_btn = st.button("🛑 Stop / Clear", type="secondary", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown(STATUS_MONITOR_HTML, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    status_log = st.empty()
    progress_bar = st.progress(0)
    
    st.markdown(TIME_ESTIMATE_HTML, unsafe_allow_html=True)


st.markdown("<br>", unsafe_allow_html=True)

# Stats Row
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    st.markdown(STATS_1_HTML, unsafe_allow_html=True)

with col_stat2:
    st.markdown(STATS_2_HTML, unsafe_allow_html=True)

with col_stat3:
    st.markdown(STATS_3_HTML, unsafe_allow_html=True)

with col_stat4:
    st.markdown(STATS_4_HTML, unsafe_allow_html=True)

st.divider()

# Informational Sections
st.markdown(WHY_USE_HTML, unsafe_allow_html=True)
st.markdown(TRUST_INDICATORS_HTML, unsafe_allow_html=True)
st.markdown(PREMIUM_FEATURES_HTML, unsafe_allow_html=True)
st.markdown(HOW_IT_WORKS_HTML, unsafe_allow_html=True)
st.markdown(FAQ_HTML, unsafe_allow_html=True)
st.markdown(FOOTER_HTML, unsafe_allow_html=True)

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
