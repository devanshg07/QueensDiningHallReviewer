from bs4 import BeautifulSoup
import re

def analyze_debug_file():
    """Analyze the saved HTML file to understand the page structure"""
    try:
        with open("page_debug.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("=== PAGE ANALYSIS ===")
        
        # Check page title
        title = soup.find('title')
        if title:
            print(f"Page Title: {title.text}")
        
        # Look for forms
        forms = soup.find_all('form')
        print(f"\nForms found: {len(forms)}")
        for i, form in enumerate(forms):
            print(f"Form {i+1}: ID='{form.get('id')}', Action='{form.get('action')}'")
        
        # Look for input fields
        inputs = soup.find_all('input')
        print(f"\nInput fields found: {len(inputs)}")
        for inp in inputs[:10]:  # Show first 10
            print(f"  Input: type='{inp.get('type')}', name='{inp.get('name')}', id='{inp.get('id')}'")
        
        # Look for select elements
        selects = soup.find_all('select')
        print(f"\nSelect dropdowns found: {len(selects)}")
        for select in selects:
            print(f"  Select: name='{select.get('name')}', id='{select.get('id')}'")
        
        # Look for buttons
        buttons = soup.find_all('button')
        print(f"\nButtons found: {len(buttons)}")
        for btn in buttons[:10]:
            print(f"  Button: text='{btn.text.strip()}', id='{btn.get('id')}'")
        
        # Look for dining hall related content
        dining_keywords = ['dining', 'hall', 'ban righ', 'jean royce', 'leonard', 'meal', 'menu']
        print(f"\nElements containing dining keywords:")
        for keyword in dining_keywords:
            elements = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
            for element in elements[:3]:  # Show first 3 matches per keyword
                if element.strip():
                    print(f"  '{keyword}': {element.strip()}")
        
        # Check for iframes (common for embedded content)
        iframes = soup.find_all('iframe')
        print(f"\nIframes found: {len(iframes)}")
        for iframe in iframes:
            print(f"  Iframe src: {iframe.get('src')}")
        
        # Look for JavaScript variables that might contain menu data
        scripts = soup.find_all('script')
        print(f"\nScripts found: {len(scripts)}")
        menu_script_patterns = ['menu', 'dining', 'food', 'meal']
        for script in scripts:
            if script.string:
                for pattern in menu_script_patterns:
                    if pattern in script.string.lower():
                        print(f"  Script contains '{pattern}': {script.string[:200]}...")
                        break
        
        return True
        
    except FileNotFoundError:
        print("page_debug.html not found. Please run the simple capture first.")
        return False
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return False

# Also let's check with requests
import requests

def check_with_requests():
    """Check the page with requests to see the actual content"""
    url = 'https://www.queensu.ca/food/eat-now/todays-menu'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("\n=== REQUEST CHECK ===")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        
        # Quick check for common patterns
        if 'dining' in response.text.lower():
            print("✓ 'dining' found in content")
        if 'menu' in response.text.lower():
            print("✓ 'menu' found in content")
        if 'form' in response.text.lower():
            print("✓ 'form' found in content")
            
        return True
    except Exception as e:
        print(f"Request failed: {e}")
        return False

if __name__ == "__main__":
    print("Analyzing the captured page...")
    analyze_debug_file()
    check_with_requests()