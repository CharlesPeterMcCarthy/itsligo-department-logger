import os
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

chrome_options = Options()
driver = webdriver.Chrome(executable_path=os.path.abspath("/usr/lib/chromium-browser/chromedriver"), chrome_options=chrome_options)

driver.get('http://timetables.itsligo.ie:81/studentset.htm')

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[onchange="FilterStudentSets(swsform)"]')))

try:
    deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
    deptSelect.select_by_index(3)
except NoSuchElementException:
    print("No more departments")

try:
    courseSelect = Select(driver.find_element_by_name('identifier'))
    courseSelect.select_by_index(31)
except NoSuchElementException:
    print("No more course")

formatSelect = Select(driver.find_element_by_name('style'))
formatSelect.select_by_index(1)

driver.find_element_by_css_selector('[onclick="getTimetable(swsform, \'student+set\')"]').click()
