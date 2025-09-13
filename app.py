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
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Navigate to the page
        url = 'https://www.queensu.ca/food/eat-now/todays-menu'
        print("Loading page...")
        driver.get(url)
        
        # STEP 0: HANDLE THE POPUP/COOKIE CONSENT
        print("Checking for popup...")
        time.sleep(2)  # Wait for popup to appear
        
        # Try to find and click common consent buttons
        consent_selectors = [
            "button#acceptCookies",
            "button.accept-cookies",
            "button.cookie-accept",
            "button.btn-accept",
            "button.agree-button",
            "button[aria-label*='accept']",
            "button[aria-label*='agree']",
            "button:contains('Accept')",
            "button:contains('Agree')",
            "button:contains('OK')",
            "button:contains('Okay')",
        ]
        
        popup_closed = False
        for selector in consent_selectors:
            try:
                # Try CSS selector first
                consent_button = driver.find_element(By.CSS_SELECTOR, selector)
                if consent_button.is_displayed():
                    consent_button.click()
                    print("Closed popup/consent dialog")
                    popup_closed = True
                    break
            except:
                continue
        
        # If CSS selectors didn't work, try XPath for text content
        if not popup_closed:
            xpath_selectors = [
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Agree')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Okay')]",
                "//button[contains(text(), 'I agree')]",
                "//button[contains(., 'Accept')]",
            ]
            
            for xpath in xpath_selectors:
                try:
                    consent_button = driver.find_element(By.XPATH, xpath)
                    if consent_button.is_displayed():
                        consent_button.click()
                        print("Closed popup/consent dialog using XPath")
                        popup_closed = True
                        break
                except:
                    continue
        
        if not popup_closed:
            print("No popup found or couldn't close it - proceeding anyway")
        
        time.sleep(1)  # Wait for popup to disappear
        
        # Wait for page content to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu-filter"))
        )
        time.sleep(2)  # Additional time for JavaScript to fully load
        
        # STEP 1: SELECT DINING HALL (this makes dates appear)
        print("Selecting dining hall...")
        # Find all dining hall options
        hall_options = driver.find_elements(By.CSS_SELECTOR, ".dining-hall-options label, .dining-hall-options input, [data-hall-option]")
        
        # If no options found with those selectors, try more general approach
        if not hall_options:
            hall_options = driver.find_elements(By.CSS_SELECTOR, "input[type='radio'][name*='hall'], label[for*='hall']")
        
        # Click the correct dining hall
        hall_found = False
        for option in hall_options:
            option_text = option.text.strip() or option.get_attribute("value") or option.get_attribute("id") or ""
            if dining_hall.lower() in option_text.lower():
                option.click()
                print(f"Selected dining hall: {dining_hall}")
                hall_found = True
                break
        
        if not hall_found:
            print(f"Dining hall '{dining_hall}' not found. Available options:")
            for option in hall_options:
                option_text = option.text.strip() or option.get_attribute("value") or option.get_attribute("id") or "N/A"
                if option_text and option_text != "N/A":
                    print(f" - {option_text}")
            return []
        
        time.sleep(2)  # Wait for date options to appear
        
        # STEP 2: SELECT DAY (this makes meals appear)
        print("Selecting day...")
        # Wait for day options to become available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".day-selector button, [data-day-selector] button, button[data-day]"))
        )
        
        # Find day selection buttons
        day_buttons = driver.find_elements(By.CSS_SELECTOR, ".day-selector button, [data-day-selector] button, button[data-day]")
        
        # Click the correct day
        day_found = False
        for button in day_buttons:
            if day in button.text:
                button.click()
                print(f"Selected day: {day}")
                day_found = True
                break
        
        if not day_found:
            print(f"Day '{day}' not found. Available options:")
            for button in day_buttons:
                print(f" - {button.text}")
            return []
        
        time.sleep(2)  # Wait for meal options to appear
        
        # STEP 3: SELECT MEAL (this makes food items appear)
        print("Selecting meal...")
        # Wait for meal options to become available
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".meal-selector button, [data-meal-selector] button, button[data-meal]"))
        )
        
        # Find meal selection buttons
        meal_buttons = driver.find_elements(By.CSS_SELECTOR, ".meal-selector button, [data-meal-selector] button, button[data-meal]")
        
        # Click the correct meal
        meal_found = False
        for button in meal_buttons:
            if meal in button.text:
                button.click()
                print(f"Selected meal: {meal}")
                meal_found = True
                break
        
        if not meal_found:
            print(f"Meal '{meal}' not found. Available options:")
            for button in meal_buttons:
                print(f" - {button.text}")
            return []
        
        time.sleep(3)  # Wait for menu items to load
        
        # STEP 4: EXTRACT MENU ITEMS
        print("Extracting menu items...")
        # Wait for menu items to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menu-item"))
        )
        
        menu_items = driver.find_elements(By.CLASS_NAME, "menu-item")
        
        # If no menu items found with that class, try other common selectors
        if not menu_items:
            menu_items = driver.find_elements(By.CSS_SELECTOR, ".food-item, .menu-list li, [data-menu-item]")
        
        # Print the results
        print(f"\n--- {dining_hall} - {day} - {meal} ---")
        for item in menu_items:
            print(f"- {item.text}")
            
        return [item.text for item in menu_items]
        
    except TimeoutException:
        print("Page took too long to load. Please check your internet connection.")
        return []
    except NoSuchElementException as e:
        print(f"Could not find an element: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []
        
    finally:
        driver.quit()

# Example usage
if __name__ == "__main__":
    # You can change these parameters as needed
    dining_hall = "Ban Righ Hall"
    day = "Fri, Sep 12"
    meal = "Lunch"
    
    menu_items = scrape_queens_dining_menu(dining_hall, day, meal)
    
    if not menu_items:
        print("\nNo menu items found. This could be because:")
        print("1. The dining hall is closed on that day/meal")
        print("2. The website structure has changed")
        print("3. There was a connection issue")
        print("4. The selected options weren't available in the expected order")
        print("5. The popup wasn't properly dismissed")