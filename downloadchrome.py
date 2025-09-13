from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument("--headless")

# Automatically finds the right ChromeDriver
driver = webdriver.Chrome(options=options)