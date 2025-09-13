from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from datetime import datetime
import time
import json

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
        # Wait for cookie popup to appear
        cookie_popup = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "QUURcookieDisclosureDiv"))
        )
        
        # Try to find and click accept button
        accept_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Agree') or contains(@aria-label, 'accept')]")
        
        for button in accept_buttons:
            if button.is_displayed():
                driver.execute_script("arguments[0].click();", button)
                print("Cookie popup accepted")
                time.sleep(1)
                return True
                
    except Exception as e:
        print(f"No cookie popup found or couldn't close it: {e}")
    
    return False

def extract_detailed_menu(driver):
    """Extract detailed menu information"""
    print("Extracting menu information...")
    
    menu_data = {
        'stations': [],
        'express_meals': [],
        'regular_menu': []
    }
    
    try:
        # Get all text content first
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = body_text.split('\n')
        
        # Look for menu items (lines with calories or food keywords)
        food_keywords = ['chicken', 'tofu', 'rice', 'vegetable', 'salad', 'soup', 'pasta', 'beef', 'fish', 'potato', 'cheese']
        
        for line in lines:
            line = line.strip()
            if line and ('cal' in line.lower() or any(keyword in line.lower() for keyword in food_keywords)):
                item_data = parse_food_item(line)
                if item_data:
                    if 'express' in line.lower() or 'cash' in line.lower():
                        menu_data['express_meals'].append(item_data)
                    else:
                        menu_data['regular_menu'].append(item_data)
        
        # Also look for station headers
        station_keywords = ['entree', 'vegan', 'breakfast', 'lunch', 'dinner', 'meal', 'station']
        for line in lines:
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in station_keywords) and len(line) < 50:
                menu_data['stations'].append(line)
                
    except Exception as e:
        print(f"Error extracting menu: {e}")
    
    return menu_data

def parse_food_item(text):
    """Parse food item text into structured data"""
    try:
        # Clean the text
        text = text.replace('*', '').replace('®', '').strip()
        
        # Extract calories
        calories = None
        if '(' in text and 'cal' in text:
            calorie_part = text.split('(')[1].split(')')[0]
            if 'cal' in calorie_part:
                try:
                    calories = int(''.join(filter(str.isdigit, calorie_part.split('cal')[0])))
                except:
                    calories = calorie_part.split('cal')[0].strip()
        
        # Extract name (remove calorie part)
        name = text
        if '(' in text and 'cal' in text:
            name = text.split('(')[0].strip()
        
        # Extract description (anything after commas or special chars)
        description = None
        if ',' in text and len(text) > len(name) + 10:
            description = text[text.find(name) + len(name):].strip()
            if description.startswith(','):
                description = description[1:].strip()
            if description and '(' in description and 'cal' in description:
                description = description.split('(')[0].strip()
        
        return {
            'name': name,
            'calories': calories,
            'description': description,
            'full_text': text
        }
        
    except:
        return None

def click_element_safely(driver, element_type, value):
    """Safely click an element with multiple strategies"""
    try:
        # Try different selectors
        selectors = [
            f"//*[contains(text(), '{value}')]",
            f"//*[contains(@aria-label, '{value}')]",
            f"//*[contains(@value, '{value}')]",
            f"//*[contains(@class, '{value.lower().replace(' ', '-')}')]",
            f"//*[contains(@id, '{value.lower().replace(' ', '-')}')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        driver.execute_script("arguments[0].scrollIntoView();", element)
                        time.sleep(0.5)
                        driver.execute_script("arguments[0].click();", element)
                        print(f"Clicked {element_type}: {value}")
                        time.sleep(2)
                        return True
            except:
                continue
                
    except Exception as e:
        print(f"Could not click {element_type}: {e}")
    
    return False

def scrape_complete_menu(dining_hall, day, meal):
    """Scrape the complete menu with detailed information"""
    driver = None
    try:
        driver = setup_stealth_driver()
        
        print(f"Loading {dining_hall} menu for {day} - {meal}...")
        driver.get("https://www.queensu.ca/food/eat-now/todays-menu")
        time.sleep(3)
        
        # Handle cookie popup first
        handle_cookie_popup(driver)
        time.sleep(2)
        
        # Select dining hall
        print("Selecting dining hall...")
        if not click_element_safely(driver, "dining hall", dining_hall):
            print(f"Could not find dining hall: {dining_hall}")
            # Take screenshot to see what's available
            driver.save_screenshot("available_options.png")
            print("Screenshot saved to available_options.png")
            return {"error": f"Dining hall '{dining_hall}' not found"}
        
        # Select date
        print("Selecting date...")
        date_part = day.split(',')[1].strip() if ',' in day else day
        if not click_element_safely(driver, "date", date_part):
            print(f"Could not find date: {date_part}")
        
        # Select meal
        print("Selecting meal...")
        if not click_element_safely(driver, "meal", meal):
            print(f"Could not find meal: {meal}")
        
        # Wait for menu to load
        time.sleep(3)
        
        # Extract detailed menu
        menu_data = extract_detailed_menu(driver)
        
        # Take screenshot
        driver.save_screenshot("final_menu.png")
        
        return {
            'success': True,
            'dining_hall': dining_hall,
            'date': day,
            'meal': meal,
            'menu': menu_data,
            'screenshot': 'final_menu.png'
        }
        
    except Exception as e:
        return {"error": f"Scraping error: {str(e)}"}
    finally:
        if driver:
            driver.quit()

def print_detailed_menu(menu_result):
    """Print the menu in a detailed, organized way"""
    if 'error' in menu_result:
        print(f"❌ Error: {menu_result['error']}")
        return
    
    print(f"\n🍽️  {menu_result['dining_hall']} - {menu_result['date']} - {menu_result['meal']}")
    print("=" * 70)
    
    menu_data = menu_result['menu']
    
    # Print Express Meals
    if menu_data['express_meals']:
        print("\n🚀 EXPRESS MEALS:")
        print("-" * 40)
        for item in menu_data['express_meals']:
            calories = f" ({item['calories']} cal)" if item['calories'] else ""
            print(f"• {item['name']}{calories}")
            if item['description']:
                print(f"  📝 {item['description']}")
    
    # Print Regular Menu
    if menu_data['regular_menu']:
        print(f"\n📋 MAIN MENU:")
        print("-" * 40)
        for item in menu_data['regular_menu']:
            calories = f" ({item['calories']} cal)" if item['calories'] else ""
            print(f"• {item['name']}{calories}")
            if item['description']:
                print(f"  📝 {item['description']}")
    
    print(f"\n📊 Total items found: {len(menu_data['express_meals']) + len(menu_data['regular_menu'])}")
    print(f"📷 Screenshot saved to: {menu_result.get('screenshot', 'N/A')}")

# Main execution
if __name__ == "__main__":
    # Use current real date
    current_date = datetime.now().strftime("%a, %b %d")  # e.g., "Fri, Sep 13"
    
    print("Queens University Detailed Menu Scraper")
    print("=" * 50)
    
    # Get user input
    dining_hall = input("Enter dining hall (e.g., 'Ban Righ Hall', 'Leonard Hall'): ").strip() or "Leonard Hall"
    meal = input("Enter meal (Breakfast/Lunch/Dinner): ").strip() or "Lunch"
    
    print(f"\nScraping {dining_hall} for {current_date} - {meal}...")
    
    result = scrape_complete_menu(dining_hall, current_date, meal)
    print_detailed_menu(result)
    
    # Save raw data to JSON file
    if 'menu' in result:
        with open('detailed_menu_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n💾 Raw data saved to 'detailed_menu_data.json'")