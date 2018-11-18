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
from selenium.common.exceptions import UnexpectedAlertPresentException

urls = []

chrome_options = Options()
#chrome_options.add_argument("--headless") # Don't open browser window
driver = webdriver.Chrome(executable_path=os.path.abspath("/usr/lib/chromium-browser/chromedriver"), chrome_options=chrome_options)

driver.get('http://timetables.itsligo.ie:81/studentset.htm')

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[onchange="FilterStudentSets(swsform)"]'))) # Wait for element in form to load

gatheringURLs = True
continueOk = True
deptCount = 1
courseCount = 0

deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
deptSelect.select_by_index(deptCount) # Set the first department to get course count
courseSelect = Select(driver.find_element_by_name('identifier'))
totalCourses = len(courseSelect.options) # Get course count for department

while gatheringURLs and courseCount < totalCourses:
    continueOk = True

    try:
        deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
        deptSelect.select_by_index(deptCount)
    except NoSuchElementException:  # Tried to select a department that doesn't exists (all should be finished)
        print("No more departments")
        gatheringURLs = False

    try:
        courseSelect = Select(driver.find_element_by_name('identifier'))
        totalCourses = len(courseSelect.options)
        if courseCount > 0:
            courseSelect.deselect_by_index(courseCount - 1) # Deselect last course
        courseSelect.select_by_index(courseCount)
    except (NoSuchElementException, UnexpectedAlertPresentException) as e: # Tried to select a course that doesn't exist (move to next dept)
        print("No more courses")
        courseCount = 0
        deptCount+=1
        continueOk = False

    if continueOk:
        formatSelect = Select(driver.find_element_by_name('style'))
        formatSelect.select_by_index(1) # List format

        driver.find_element_by_css_selector('[onclick="getTimetable(swsform, \'student+set\')"]').click() # Click button to view timetable

        urls.append(driver.current_url)
        driver.execute_script("window.history.go(-1)") # Go back to timetable lookup
        courseCount+=1

    if courseCount == totalCourses:
        courseCount = 0
        deptCount+=1

print(urls)
