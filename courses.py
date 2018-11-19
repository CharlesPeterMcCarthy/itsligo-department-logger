import os
import selenium
import sys
import pymongo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException

try:
    print("Attempting to connect to MongoDB...")
    mongo = pymongo.MongoClient("mongodb://localhost:27017/")
    mongo.server_info()
except ConnectionFailure:
    print("Failed to connect to MongoDB. Please run MongoDB first and try again.")
    exit()
print("Successfully connected to MongoDB.")


urls = []

chrome_options = Options()
#chrome_options.add_argument("--headless") # Don't open browser window
driver = webdriver.Chrome(executable_path=os.path.abspath("/usr/lib/chromium-browser/chromedriver"), chrome_options=chrome_options)

driver.get('http://timetables.itsligo.ie:81/studentset.htm')

WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[onchange="FilterStudentSets(swsform)"]'))) # Wait for element in form to load

gatheringURLs = True
continueOk = True
deptCount = 16
courseCount = 30

deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
deptSelect.select_by_index(deptCount) # Set the first department to get course count
courseSelect = Select(driver.find_element_by_name('identifier'))
totalCourses = len(courseSelect.options) # Get course count for department

while gatheringURLs and courseCount < totalCourses:
    continueOk = True

    try:
        deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
        deptSelect.select_by_index(deptCount)
        currentDept = deptSelect.first_selected_option.text
    except NoSuchElementException:  # Tried to select a department that doesn't exists (all should be finished)
        print("No more departments.")
        gatheringURLs = False
        break

    try:
        courseSelect = Select(driver.find_element_by_name('identifier'))
        totalCourses = len(courseSelect.options)
        if courseCount > 0:
            courseSelect.deselect_by_index(courseCount - 1) # Deselect last course
        courseSelect.select_by_index(courseCount)
        currentCourse = courseSelect.first_selected_option.text

        sys.stdout.write("Retrieving %s timetable..." %currentCourse)
        sys.stdout.flush()
    except (NoSuchElementException, UnexpectedAlertPresentException) as e: # Tried to select a course that doesn't exist (move to next dept)
        print("No more courses")
        courseCount = 0
        deptCount+=1
        continueOk = False

    if continueOk:
        formatSelect = Select(driver.find_element_by_name('style'))
        formatSelect.select_by_index(1) # List format

        driver.find_element_by_css_selector('[onclick="getTimetable(swsform, \'student+set\')"]').click() # Click button to view timetable

        urls.append({'dept': currentDept, 'course': currentCourse, 'url': driver.current_url})
        driver.execute_script("window.history.go(-1)") # Go back to timetable lookup
        courseCount+=1

        sys.stdout.write("\rRetrieving %s timetable... Done.\n" %currentCourse)
        sys.stdout.flush()
    if courseCount == totalCourses:
        courseCount = 0
        deptCount+=1

if len(urls):
    print("All timetable URLs collected.")
    print("Saving URLs to database.")
    mydb = mongo["test_db"]
    mycol = mydb["timetables"]
    mycol.insert_many(urls)
else:
    print("No timetable URLs collected.")

print("Finished.")
