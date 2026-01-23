
import antigravity as ag
import random
import asyncio
import os
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
import sys

# Fix for Windows asyncio loop with Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Global internal for reuse if needed, though we will create fresh for robustness
USERNAME = ""
PASSWORD = ""

def setup_credentials(user, pwd):
    global USERNAME, PASSWORD
    USERNAME = user
    PASSWORD = pwd

async def run_batch_submission(urls, site_configs, headless=False, progress_callback=None):
    """
    Runs the bot for a list of URLs across multiple sites.
    site_configs: list of dicts -> [{'url': '...', 'username': '...', 'password': '...'}, ...]
    """
    print("🚀 Launching Antigravity Bot Batch...")
    
    # Launch Browser
    browser = await ag.launch(headless=headless)
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    
    try:
        total_steps = len(urls) * len(site_configs)
        global_step = 0
        
        for site_idx, site in enumerate(site_configs):
            site_url = site['url']
            username = site['username']
            password = site['password']
            
            # Clean base URL for display
            display_name = site_url.replace("https://www.", "").replace("http://", "").split("/")[0]

            print(f"🌍 Starting submission for site: {display_name}")
            
            # Open a new page for each site to ensure fresh state or just clear cookies if preferred
            # Reusing context but new page
            page = await context.new_page()
            
            try:
                # --- LOGIN ---
                if progress_callback: progress_callback(global_step, total_steps, f"Authenticating on {display_name}...")
                
                login_url = f"{site_url.rstrip('/')}/login"
                submit_url = f"{site_url.rstrip('/')}/submit"
                
                await page.goto(login_url)
                
                # Check if actually on login page or already logged in
                try:
                    await page.wait_for_selector("input[name='username']", timeout=5000)
                    should_login = True
                except:
                    should_login = False
                    
                if should_login:
                    print(f"🔒 Logging in to {display_name}...")
                    await page.fill("input[name='username']", username)
                    await page.fill("input[name='password']", password)
                    await page.click("button[type='submit'], input[type='submit'], .btn-primary")
                    
                    # Wait for navigation to dashboard or home
                    try:
                        await page.wait_for_url("**/user/**", timeout=15000)
                    except Exception:
                        await asyncio.sleep(3)
                        
                    print("✅ Login assumed successful.")
                
                # --- PROCESS URLS ---
                for i, target_url in enumerate(urls):
                    global_step += 1
                    local_step = i + 1
                    
                    if progress_callback: progress_callback(global_step, total_steps, f"[{display_name}] Processing: {target_url}")
                    
                    try:
                        # Phase 1: URL
                        step_description = f"Navigating to Submit Page ({display_name})"
                        print(f"🔗 [{local_step}/{len(urls)}] {step_description}...")
                        await page.goto(submit_url)
                        
                        # Wait for potential Cloudflare or browser check
                        step_description = "Waiting for Network Idle"
                        try:
                            await page.wait_for_load_state('networkidle', timeout=15000)
                        except Exception:
                            print("⚠️ Network idle timed out, continuing anyway...")
                        
                        # Check for Login Redirect (Robust Check)
                        is_login_page = "login" in page.url
                        if not is_login_page:
                            try:
                                 # Quick check if username field is present
                                 await page.wait_for_selector("input[name='username']", state="visible", timeout=2000)
                                 is_login_page = True
                            except: pass
        
                        if is_login_page:
                            step_description = "Re-authenticating"
                            print("🔒 Session lost. Re-logging...")
                            # wait for full load
                            await page.wait_for_selector("input[name='username']", timeout=10000)
                            await page.fill("input[name='username']", username)
                            await page.fill("input[name='password']", password)
                            await page.click("button[type='submit'], .btn-primary")
                            
                            step_description = "Waiting for Post-Login Redirect"
                            try:
                                # Wait for either /user/* OR just not being on /login
                                await page.wait_for_url(lambda u: "login" not in u and "submit" not in u, timeout=15000)
                            except:
                                print("⚠️ Login redirect wait timed out, proceeding to force navigation...")
                            
                            print("✅ Re-logged in (assumed). Navigating back to submit...")
                            step_description = "Navigating to Submit Page (Retry)"
                            await page.goto(submit_url)
                        
                        # Step 1: Input URL
                        step_description = "Waiting for URL Input Field (#checkUrl)"
                        await page.wait_for_selector("#checkUrl", state='visible', timeout=15000)
                        await page.fill('#checkUrl', target_url)
                        
                        # Click Continue and Wait for Phase 2
                        step_description = "Clicking Continue and Waiting for Form"
                        print("➡️ Clicking Continue...")
                        
                        form_visible = False
                        for attempt in range(3):
                            if await page.locator(".checkUrl").count() > 0:
                                 await page.click('.checkUrl')
                            else:
                                 await page.click('input[value="Continue"]')
                            
                            try:
                                # Short wait to see if it worked
                                await page.wait_for_selector('#articleTitle', state='visible', timeout=8000)
                                form_visible = True
                                break
                            except PlaywrightTimeoutError:
                                print(f"⚠️ Attempt {attempt+1}: Form didn't appear. Retrying click...")
                                await asyncio.sleep(2)
                        
                        if not form_visible:
                            # Capture screenshot for debug
                            try:
                                safe_name = "".join([c for c in target_url if c.isalnum()])[:20]
                                await page.screenshot(path=f"debug_fail_{safe_name}.png")
                            except: pass
                            raise Exception("Failed to reveal Level 2 form after multiple clicks")
                        
                        print("✅ Article Details form visible.")

                        # Phase 2: Details
                        step_description = "Filling Article Details"
                        
                        # Use the URL itself as the title and description
                        title = target_url
                        await page.fill('#articleTitle', title)

                        # Category - attempt to select 'News' by label or value
                        try:
                            # Try selecting by label "News" first, then value if known (often '4' was news before)
                            await page.select_option('#category', label='News')
                        except:
                            try:
                                # Fallback to index if label fails (finding 'News' usually in top 5)
                                # Assuming previous index 4 was News, checking if that persists
                                await page.select_option('#category', index=4)
                            except:
                                # Last resort fallback
                                await page.select_option('#category', index=1)

                        # Description - Use the URL repeated to ensure it meets any length requirements
                        desc = f"{target_url} - {target_url}"
                        await page.fill('#description', desc)
                        
                        # Tags - Use domain keyword
                        try:
                            domain_keyword = target_url.split('/')[2].replace('www.', '').split('.')[0]
                            await page.fill('#tags', domain_keyword)
                        except: pass
                        
                        # Submit Phase 2
                        step_description = "Saving Details"
                        print("💾 Saving Details...")
                        await page.click('.saveChanges')

                        # Phase 3: Final Submit - New Page / Section
                        step_description = "Waiting for Final Submit Button"
                        print("⏳ Waiting for Final Submit Button...")
                        await page.wait_for_selector('#submit', state='visible', timeout=30000)
                        
                        # Submitting
                        step_description = "Clicking Final Submit"
                        await page.click('#submit')
                        print("✅ Clicked Final Submit")
                        
                        # Wait for success confirmation or navigation
                        step_description = "Waiting for Success Confirmation"
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        print(f"🎉 Successfully Submitted: {target_url}")

                    except PlaywrightTimeoutError as e:
                        print(f"TIMEOUT during: {step_description}")
                        # Try to screenshot
                        try:
                            safe_name = "".join([c for c in target_url if c.isalnum()])[:20]
                            await page.screenshot(path=f"timeout_{safe_name}.png")
                            print(f"📸 Screenshot saved to timeout_{safe_name}.png")
                            
                            # Debug Page Content
                            title = await page.title()
                            content = await page.content()
                            print(f"📄 Page Title: {title}")
                            print(f"📄 Page Content Snippet: {content[:500]}...")
                        except: pass
                        
                        if progress_callback: progress_callback(global_step, total_steps, f"⚠️ Timeout during **{step_description}**, skipping...")
                    except Exception as e:
                        print(f"Error on {target_url}: {e}")
                        if progress_callback: progress_callback(global_step, total_steps, f"❌ Error: {str(e)}")
            
            except Exception as e:
                print(f"❌ Error during site session for {display_name}: {e}")
            finally:
                await page.close()

    finally:
        await browser.close()
        print("Bot session ended.")

if __name__ == "__main__":
    # Test execution
    test_urls = [
        "https://curtiscenter.math.ucla.edu/wp-content/uploads/ninja-forms/76/1/Official-Apps-Guide4.pdf",
    ]
    
    # Example Config
    test_configs = [{
        "url": "https://www.abookmarking.com",
        "username": os.getenv("BOOKMARK_USER", "jetski_tester_02"),
        "password": os.getenv("BOOKMARK_PASS", "TesterPassword123!")
    }]
    
    # print("Running in HEADFUL mode for debugging...")
    ag.run(run_batch_submission(test_urls, test_configs, headless=True))
