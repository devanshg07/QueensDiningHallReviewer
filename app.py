from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def scrape_queens_dining_menu(dining_hall, day, meal):
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Initialize the driver
    driver = webdriver.Chrome(options=options)
    
    try:
        # Navigate to the page
        url = 'https://www.queensu.ca/food/eat-now/todays-menu'
        print("Loading Queens University dining menu...")
        driver.get(url)
        
        # Wait for page to load completely
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu-filter"))
        )
        time.sleep(2)
        
        print("Page loaded successfully")
        
        # STEP 1: SELECT DINING HALL
        print(f"Selecting dining hall: {dining_hall}")
        
        # Find all dining hall radio buttons
        hall_options = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][name='dining_hall']")
        hall_labels = driver.find_elements(By.CSS_SELECTOR, "label[for^='edit-dining-hall']")
        
        hall_found = False
        for i, option in enumerate(hall_options):
            label = hall_labels[i] if i < len(hall_labels) else None
            label_text = label.text.strip() if label else ""
            
            if dining_hall.lower() in label_text.lower():
                # Scroll into view and click the label (more reliable than clicking input)
                driver.execute_script("arguments[0].scrollIntoView();", label)
                label.click()
                print(f"Selected: {label_text}")
                hall_found = True
                break
        
        if not hall_found:
            print("Available dining halls:")
            for label in hall_labels:
                print(f" - {label.text.strip()}")
            return []
        
        time.sleep(2)  # Wait for date options to load
        
        # STEP 2: SELECT DATE
        print(f"Selecting date: {day}")
        
        # Find date buttons (they're actually anchor tags with role='button')
        date_buttons = driver.find_elements(By.CSS_SELECTOR, "a.menu-filter__day[role='button']")
        
        date_found = False
        for button in date_buttons:
            if day in button.text:
                driver.execute_script("arguments[0].scrollIntoView();", button)
                button.click()
                print(f"Selected date: {button.text}")
                date_found = True
                break
        
        if not date_found:
            print("Available dates:")
            for button in date_buttons:
                print(f" - {button.text}")
            return []
        
        time.sleep(2)  # Wait for meal options to load
        
        # STEP 3: SELECT MEAL
        print(f"Selecting meal: {meal}")
        
        # Find meal buttons (also anchor tags with role='button')
        meal_buttons = driver.find_elements(By.CSS_SELECTOR, "a.menu-filter__meal[role='button']")
        
        meal_found = False
        for button in meal_buttons:
            if meal.lower() in button.text.lower():
                driver.execute_script("arguments[0].scrollIntoView();", button)
                button.click()
                print(f"Selected meal: {button.text}")
                meal_found = True
                break
        
        if not meal_found:
            print("Available meals:")
            for button in meal_buttons:
                print(f" - {button.text}")
            return []
        
        time.sleep(3)  # Wait for menu to load
        
        # STEP 4: EXTRACT MENU ITEMS
        print("Extracting menu items...")
        
        # Find menu sections (stations)
        menu_sections = driver.find_elements(By.CSS_SELECTOR, ".menu-section")
        menu_data = []
        
        if menu_sections:
            for section in menu_sections:
                try:
                    # Get section title
                    section_title = section.find_element(By.CSS_SELECTOR, ".menu-section__title").text
                    print(f"\n{section_title}:")
                    
                    # Get menu items in this section
                    menu_items = section.find_elements(By.CSS_SELECTOR, ".menu-item")
                    
                    for item in menu_items:
                        try:
                            item_name = item.find_element(By.CSS_SELECTOR, ".menu-item__name").text
                            menu_data.append(f"{section_title}: {item_name}")
                            print(f"  - {item_name}")
                        except:
                            # Try alternative selector if the first one fails
                            item_name = item.text.strip()
                            if item_name:
                                menu_data.append(f"{section_title}: {item_name}")
                                print(f"  - {item_name}")
                except:
                    continue
        else:
            # Fallback: try to find any menu items
            print("No menu sections found, trying fallback...")
            menu_items = driver.find_elements(By.CSS_SELECTOR, ".menu-item, .field--name-field-menu-items")
            for item in menu_items:
                item_text = item.text.strip()
                if item_text:
                    menu_data.append(item_text)
                    print(f"- {item_text}")
        
        return menu_data
        
    except TimeoutException:
        print("Page took too long to load. Please check your internet connection.")
        return []
    except NoSuchElementException as e:
        print(f"Could not find an element: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return []
        
    finally:
        driver.quit()

def get_available_options():
    """Function to check what options are available on the site"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get('https://www.queensu.ca/food/eat-now/todays-menu')
        time.sleep(3)
        
        print("=== AVAILABLE DINING HALLS ===")
        hall_labels = driver.find_elements(By.CSS_SELECTOR, "label[for^='edit-dining-hall']")
        for label in hall_labels:
            print(f"- {label.text.strip()}")
        
        print("\n=== AVAILABLE DATES ===")
        date_buttons = driver.find_elements(By.CSS_SELECTOR, "a.menu-filter__day[role='button']")
        for button in date_buttons[:5]:  # Show first 5 dates
            print(f"- {button.text}")
        
        print("\n=== AVAILABLE MEALS ===")
        meal_buttons = driver.find_elements(By.CSS_SELECTOR, "a.menu-filter__meal[role='button']")
        for button in meal_buttons:
            print(f"- {button.text}")
            
    finally:
        driver.quit()

# Example usage
if __name__ == "__main__":
    # First, check what options are available
    print("Checking available options on the site...")
    get_available_options()
    
    print("\n" + "="*50)
    
    # Then try to scrape with specific selections
    # Note: Use exact names as shown in the available options
    dining_hall = "Ban Righ Hall"  # Make sure this matches exactly
    day = "Fri, Sep 13"  # Use a date that's actually available
    meal = "Lunch"  # Use exact meal name
    
    print(f"Scraping menu for: {dining_hall} - {day} - {meal}")
    menu_items = scrape_queens_dining_menu(dining_hall, day, meal)
    
    if menu_items:
        print(f"\n✅ Success! Retrieved {len(menu_items)} menu items:")
        for item in menu_items:
            print(f"  {item}")
    else:
        print("\n❌ No menu items found. Possible reasons:")
        print("   - The dining hall might be closed on that day")
        print("   - The meal might not be served")
        print("   - Check the exact spelling of options using the available options above")
        print("   - Try a different date or meal")