from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import time
import sys

def setup_driver():
    """Set up Chrome driver with optimal options"""
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    
    # Try to initialize driver with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            driver = webdriver.Chrome(options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f"Attempt {attempt + 1} failed to initialize driver: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2)

def scrape_queens_dining_menu_simple():
    """Simplified version that just captures the page content for debugging"""
    try:
        driver = setup_driver()
        
        # Navigate to the page
        url = 'https://www.queensu.ca/food/eat-now/todays-menu'
        print("Loading Queens University dining menu...")
        driver.get(url)
        
        # Wait a reasonable time and capture page source
        time.sleep(5)
        
        # Save page source to file for debugging
        page_source = driver.page_source
        with open("page_debug.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Page source saved to page_debug.html")
        
        # Try to find basic elements
        print("Looking for key elements...")
        
        # Check if page loaded
        if "queensu" not in driver.page_source.lower():
            print("Page didn't load properly")
            return False
        
        # Look for dining hall options
        try:
            halls = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'], label, [role='button'], a, button")
            print(f"Found {len(halls)} potential interactive elements")
            
            # Print first few to see what we're working with
            for i, element in enumerate(halls[:10]):
                try:
                    text = element.text.strip()
                    if text:
                        print(f"Element {i}: {element.tag_name} - '{text}'")
                except:
                    continue
                    
        except Exception as e:
            print(f"Error examining elements: {e}")
        
        # Take screenshot for visual debugging
        driver.save_screenshot("page_screenshot.png")
        print("Screenshot saved to page_screenshot.png")
        
        return True
        
    except WebDriverException as e:
        print(f"WebDriver error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass

def interactive_debug():
    """Interactive debugging to figure out the site structure"""
    try:
        driver = setup_driver()
        driver.get('https://www.queensu.ca/food/eat-now/todays-menu')
        
        print("Page loaded. Press Enter to continue...")
        input()  # Pause for user to inspect
        
        # Let user interact manually
        print("You can now interact with the browser manually.")
        print("When you're done, press Enter in this console to continue...")
        input()
        
        # Capture final state
        with open("interactive_debug.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("interactive_screenshot.png")
        print("Debug files saved.")
        
    except Exception as e:
        print(f"Error during interactive debug: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Simple page capture (recommended first step)")
    print("2. Interactive debugging (opens browser for manual inspection)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "2":
        interactive_debug()
    else:
        success = scrape_queens_dining_menu_simple()
        if success:
            print("\nNext steps:")
            print("1. Open page_debug.html in a browser to see what was captured")
            print("2. Check page_screenshot.png to see visual state")
            print("3. Examine the console output for element information")
            print("4. Based on this, we can create the proper selectors")
        else:
            print("Failed to capture page. This suggests:")
            print("- Network issues")
            print("- Chrome driver compatibility problems")
            print("- Website blocking automated access")