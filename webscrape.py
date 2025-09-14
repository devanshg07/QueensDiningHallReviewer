from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from datetime import datetime
import time
import json
import re

def setup_stealth_driver():
    """Set up Chrome driver with stealth settings"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    
    return driver

def handle_cookie_popup(driver):
    """Handle the cookie consent popup"""
    print("Checking for cookie popup...")
    try:
        # Try multiple selectors for cookie popup
        cookie_selectors = [
            "//div[contains(@id, 'cookie')]",
            "//div[contains(@class, 'cookie')]",
            "//div[contains(@id, 'QUURcookie')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Agree')]",
            "//button[contains(@aria-label, 'accept')]"
        ]
        
        for selector in cookie_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].click();", element)
                        print("Cookie popup handled")
                        time.sleep(1)
                        return True
            except:
                continue
                
    except Exception as e:
        print(f"Cookie handling: {e}")
    
    return False

def make_selection(driver, element_type, value):
    """Make a selection on the page (dining hall, date, or meal)"""
    print(f"Selecting {element_type}: {value}")
    
    # Map element types to their container classes
    container_classes = {
        'dining_hall': 'diningHallBtn',
        'date': 'selDate',
        'meal': 'mealPeriod'
    }
    
    try:
        # Try to find the element by text content
        xpath = f"//*[contains(text(), '{value}') and not(ancestor::*[contains(@style, 'display: none')])]"
        elements = driver.find_elements(By.XPATH, xpath)
        
        for element in elements:
            if element.is_displayed() and element.text.strip() == value:
                driver.execute_script("arguments[0].scrollIntoView();", element)
                driver.execute_script("arguments[0].click();", element)
                print(f"✓ Selected {element_type}: {value}")
                time.sleep(2)
                return True
        
        # If not found by exact text, try partial match
        xpath_partial = f"//*[contains(text(), '{value}')]"
        elements_partial = driver.find_elements(By.XPATH, xpath_partial)
        
        for element in elements_partial:
            if element.is_displayed() and value in element.text:
                driver.execute_script("arguments[0].scrollIntoView();", element)
                driver.execute_script("arguments[0].click();", element)
                print(f"✓ Selected {element_type} (partial match): {value}")
                time.sleep(2)
                return True
                
    except Exception as e:
        print(f"Error selecting {element_type}: {e}")
    
    print(f"✗ Could not find {element_type}: {value}")
    return False

def wait_for_menu_load(driver):
    """Wait for the menu content to load after selections"""
    print("Waiting for menu to load...")
    
    # Wait for menu container to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu-container"))
        )
        return True
    except:
        pass
    
    # Wait for menu items to appear
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu-item"))
        )
        return True
    except:
        pass
    
    # Wait for any content that looks like a menu
    try:
        WebDriverWait(driver, 10).until(
            lambda d: any(keyword in d.page_source.lower() for keyword in ['menu', 'cal', 'entree', 'vegan'])
        )
        return True
    except:
        pass
    
    print("Menu content did not load as expected")
    return False

def extract_menu_content(driver):
    """Extract the actual menu content after selections"""
    print("Extracting menu content...")
    
    menu_data = {
        'stations': [],
        'items': [],
        'express_meals': [],
        'nutritional_info': []
    }
    
    try:
        # Look for menu containers
        menu_containers = driver.find_elements(By.XPATH, "//*[contains(@class, 'menu') or contains(@class, 'station') or contains(@class, 'item')]")
        
        # Get all text content from the page
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in body_text.split('\n') if line.strip()]
        
        # Filter for menu content (remove navigation, headers, etc.)
        menu_lines = []
        in_menu_section = False
        
        for line in lines:
            # Start capturing when we hit menu-related content
            if any(keyword in line.lower() for keyword in ['scheduled menu', 'express meals', 'entree', 'vegan', 'breakfast', 'lunch', 'dinner', 'cal']):
                in_menu_section = True
            
            # Stop capturing when we hit footer content
            if any(keyword in line.lower() for keyword in ['queen\'s university', 'copyright', 'privacy', 'tel:', 'footer']):
                in_menu_section = False
            
            if in_menu_section and line and len(line) > 3:
                menu_lines.append(line)
        
        # Process menu lines to extract structured data
        current_station = ""
        for line in menu_lines:
            # Detect station headers
            if any(keyword in line.lower() for keyword in ['express meals', 'true balance', 'vegan meal', 'all day breakfast', 'entrees', 'station']):
                current_station = line
                if current_station not in menu_data['stations']:
                    menu_data['stations'].append(current_station)
                continue
            
            # Skip lines that are probably not food items
            if len(line) < 5 or any(keyword in line.lower() for keyword in ['select dining', 'pick a day', 'pick a meal', 'remember to']):
                continue
            
            # Extract food items with calories
            item_data = parse_food_item(line, current_station)
            if item_data:
                if 'express' in current_station.lower() or 'cash' in line.lower():
                    menu_data['express_meals'].append(item_data)
                else:
                    menu_data['items'].append(item_data)
        
        # Also try to find items by specific selectors
        try:
            menu_items = driver.find_elements(By.CLASS_NAME, "menu-item")
            for item in menu_items:
                text = item.text.strip()
                if text:
                    item_data = parse_food_item(text, current_station)
                    if item_data:
                        menu_data['items'].append(item_data)
        except:
            pass
            
    except Exception as e:
        print(f"Error extracting menu content: {e}")
    
    return menu_data

def parse_food_item(text, station=""):
    """Parse food item text into structured data"""
    try:
        # Clean the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Skip if it's too short or doesn't look like a food item
        if len(text) < 5 or any(keyword in text.lower() for keyword in ['select', 'pick', 'remember', 'note:', 'tenders']):
            return None
        
        # Extract calories
        calories = None
        calorie_match = re.search(r'\((\d+)\s*cal\)', text.lower())
        if calorie_match:
            calories = int(calorie_match.group(1))
        
        # Extract name (remove calorie part and other non-food text)
        name = text
        if calorie_match:
            name = text.replace(calorie_match.group(0), '').strip()
        
        # Extract description (ingredients after the main name)
        description = None
        if ',' in name and len(name) > 20:
            parts = name.split(',', 1)
            name = parts[0].strip()
            description = parts[1].strip()
        
        # Extract dietary tags
        dietary_tags = []
        tags = ['vegan', 'vegetarian', 'gluten-free', 'dairy-free', 'organic', 'local', 'halal']
        for tag in tags:
            if tag in text.lower():
                dietary_tags.append(tag)
        
        return {
            'name': name,
            'calories': calories,
            'description': description,
            'station': station,
            'dietary_tags': dietary_tags,
            'full_text': text
        }
        
    except Exception as e:
        print(f"Error parsing food item: {e}")
        return None

def scrape_actual_menu(dining_hall, date, meal):
    """Scrape the actual menu content after making selections"""
    driver = None
    try:
        driver = setup_stealth_driver()
        
        print(f"Loading menu for {dining_hall} - {date} - {meal}...")
        driver.get("https://www.queensu.ca/food/eat-now/todays-menu")
        time.sleep(3)
        
        # Handle cookie popup
        handle_cookie_popup(driver)
        time.sleep(2)
        
        # Make selections in order
        if not make_selection(driver, "dining_hall", dining_hall):
            return {"error": f"Could not select dining hall: {dining_hall}"}
        
        if not make_selection(driver, "date", date):
            return {"error": f"Could not select date: {date}"}
        
        if not make_selection(driver, "meal", meal):
            return {"error": f"Could not select meal: {meal}"}
        
        # Wait for menu to load
        if not wait_for_menu_load(driver):
            print("Menu didn't load automatically, trying to proceed...")
        
        # Take screenshot to see current state
        driver.save_screenshot("menu_loaded.png")
        print("Screenshot saved: menu_loaded.png")
        
        # Extract menu content
        menu_data = extract_menu_content(driver)
        
        return {
            'success': True,
            'dining_hall': dining_hall,
            'date': date,
            'meal': meal,
            'menu_data': menu_data,
            'screenshot': 'menu_loaded.png'
        }
        
    except Exception as e:
        return {"error": f"Scraping error: {str(e)}"}
    finally:
        if driver:
            driver.quit()

def print_menu_results(result):
    """Print the menu results in a clean format"""
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print(f"\n{'='*80}")
    print(f"🍽️  MENU FOR: {result['dining_hall']} - {result['date']} - {result['meal']}")
    print(f"{'='*80}")
    
    menu_data = result['menu_data']
    
    # Print Express Meals
    if menu_data['express_meals']:
        print(f"\n🚀 EXPRESS MEALS:")
        print("-" * 50)
        for item in menu_data['express_meals']:
            calories = f" ({item['calories']} cal)" if item['calories'] else ""
            print(f"• {item['name']}{calories}")
            if item['description']:
                print(f"  📝 {item['description']}")
            if item['dietary_tags']:
                print(f"  🏷️  {', '.join(item['dietary_tags'])}")
    
    # Print Regular Menu Items by Station
    if menu_data['items']:
        # Group items by station
        stations = {}
        for item in menu_data['items']:
            station = item.get('station', 'Other')
            if station not in stations:
                stations[station] = []
            stations[station].append(item)
        
        for station, items in stations.items():
            print(f"\n🏷️  {station.upper()}:")
            print("-" * 50)
            for item in items:
                calories = f" ({item['calories']} cal)" if item['calories'] else ""
                print(f"• {item['name']}{calories}")
                if item['description']:
                    print(f"  📝 {item['description']}")
                if item['dietary_tags']:
                    print(f"  🏷️  {', '.join(item['dietary_tags'])}")
    
    # Print summary
    print(f"\n📊 SUMMARY:")
    print("-" * 50)
    print(f"• Express meals: {len(menu_data['express_meals'])}")
    print(f"• Regular items: {len(menu_data['items'])}")
    print(f"• Stations: {len(menu_data['stations'])}")
    print(f"• Screenshot: {result.get('screenshot', 'N/A')}")

# Main execution
if __name__ == "__main__":
    # Use current real date
    current_date = datetime.now().strftime("%a, %b %d")  # e.g., "Sat, Sep 13"
    
    print("🚀 QUEENS UNIVERSITY MENU SCRAPER")
    print("=" * 50)
    
    dining_hall = input("Enter dining hall (e.g., 'Leonard Hall'): ").strip() or "Leonard Hall"
    meal = input("Enter meal (Breakfast/Lunch/Dinner): ").strip() or "Dinner"
    
    print(f"\nScraping {dining_hall} for {current_date} - {meal}...")
    
    result = scrape_actual_menu(dining_hall, current_date, meal)
    print_menu_results(result)
    
    # Save data to JSON
    if 'menu_data' in result:
        with open('actual_menu_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Data saved to 'actual_menu_data.json'")