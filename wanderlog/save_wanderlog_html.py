import asyncio
from playwright.async_api import async_playwright
import os

async def save_page_html(url, output_file):
    """
    Save the fully rendered HTML content of a page using Playwright
    """
    print(f"🔍 Accessing URL: {url}")
    
    async with async_playwright() as p:
        # Launch browser with slower navigation to ensure content loads
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to the URL with a longer timeout
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("⏳ Page loaded, waiting for content to render...")
            
            # Wait for some time to ensure JavaScript execution
            await page.wait_for_timeout(5000)
            
            # Scroll down to load all content
            print("⏳ Scrolling to load all content...")
            for _ in range(5):  # Scroll multiple times to ensure all content loads
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)  # Wait between scrolls
            
            # Get the page content
            content = await page.content()
            
            # Save the HTML content to a file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ HTML content saved to {output_file}")
            
            # Take a screenshot for visual verification
            screenshot_file = output_file.replace('.html', '.png')
            await page.screenshot(path=screenshot_file, full_page=True)
            print(f"📸 Screenshot saved to {screenshot_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving page HTML: {str(e)}")
            return False
        
        finally:
            # Always close the browser
            await browser.close()

async def main():
    # URL to scrape
    url = "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong"
    
    # Create output directory if it doesn't exist
    os.makedirs('wanderlog', exist_ok=True)
    
    # Output file path
    output_file = os.path.join('wanderlog', 'hong_kong_bars.html')
    
    # Save the page HTML
    await save_page_html(url, output_file)

if __name__ == "__main__":
    asyncio.run(main())
