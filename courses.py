#!/usr/bin/python

import os
import selenium
import sys
import pymongo
import re
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException

def SetupDriver():
    print("Setting up Driver.")
    chrome_options = Options()
    #chrome_options.add_argument("--headless") # Don't open browser window
    driver = webdriver.Chrome(executable_path=os.path.abspath("/usr/lib/chromium-browser/chromedriver"), chrome_options=chrome_options)

    driver.get('http://timetables.itsligo.ie:81/studentset.htm')

    sys.stdout.write("Waiting for page to fully load...")
    sys.stdout.flush()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '[onchange="FilterStudentSets(swsform)"]'))) # Wait for element in form to load

    sys.stdout.write("\rWaiting for page to fully load... Done.\n")
    sys.stdout.flush()

    return driver

def GetCourseCode(driver):
    try:
        elem = driver.find_element_by_xpath("(/html/body/table/tbody/tr)[6]/td/table/tbody/tr")
        courseCode = elem.text.strip()[15:27].upper()
    except NoSuchElementException:
        return None

    return courseCode if re.match(r'SG_([A-Z]){5}_([A-Z])0([0-9])', courseCode) else None

def GetCourseYear(driver):
    try:
        elem = driver.find_element_by_xpath("(/html/body/table/tbody/tr)[6]/td/table/tbody/tr")
        text = elem.text.strip().upper()
        parts = text.split('/')
    except NoSuchElementException:
        return None

    return parts[2][1] if re.match(r'Y([1-9])', parts[2]) else None

def GetCourseLevel(driver, courseCode):
    return courseCode[11:12] if re.match(r'SG_([A-Z]){5}_([A-Z])0([0-9])', courseCode) else None

def SelectGeneralDropdowns(driver, timeframe):
    try:
        formatSelect = Select(driver.find_element_by_name('style'))
        formatSelect.select_by_index(1) # List format

        weeksSelect = Select(driver.find_element_by_name('weeks'))
        weeksSelect.select_by_index(2 if timeframe == 'sem1' else 3) # Semester1 or Semester2

        daysSelect = Select(driver.find_element_by_name('days'))
        daysSelect.select_by_index(0) # Mon-Fri

        periodsSelect = Select(driver.find_element_by_name('periods'))
        periodsSelect.select_by_index(0) # 9:00 - 18:00
    except NoSuchElementException:
        print("An Error Occurred")

def ConnectToDB():
    try:
        print("Attempting to connect to MongoDB...")
        mongo = pymongo.MongoClient("mongodb://localhost:27017/")
        mongo.server_info()
    except ConnectionFailure:
        print("Failed to connect to MongoDB. Please run MongoDB first and try again.")
        exit()
    print("Successfully connected to MongoDB.")
    return mongo

def GetDeptCourseTotal(driver, deptCount):
    deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
    deptSelect.select_by_index(deptCount) # Set the first department to get course count
    courseSelect = Select(driver.find_element_by_name('identifier'))
    return len(courseSelect.options) # Get course count for department

def SelectDepartment(driver, deptCount):
    try:
        deptSelect = Select(driver.find_element_by_css_selector('[onchange="FilterStudentSets(swsform)"]'))
        deptSelect.select_by_index(deptCount)
        currentDept = deptSelect.first_selected_option.text
    except NoSuchElementException:  # Tried to select a department that doesn't exists (all should be finished)
        print("No more departments.")
        return False
    return currentDept

def SelectCourse(driver, courseCount):
    try:
        courseSelect = Select(driver.find_element_by_name('identifier'))
        DeselectLastCourse(courseCount, courseSelect)
        courseSelect.select_by_index(courseCount)
        currentCourse = courseSelect.first_selected_option.text

        sys.stdout.write("Retrieving %s timetable..." %currentCourse)
        sys.stdout.flush()
    except (NoSuchElementException, UnexpectedAlertPresentException) as e: # Tried to select a course that doesn't exist (move to next dept)
        print("No more courses in department.")
        return False
    return currentCourse

def DeselectLastCourse(courseCount, courseSelect):
    if courseCount > 0:
        courseSelect.deselect_by_index(courseCount - 1) # Deselect last course

def GetTimetableURL(driver):
    driver.find_element_by_css_selector('[onclick="getTimetable(swsform, \'student+set\')"]').click() # Click button to view timetable
    return driver.current_url

def GoBack():
    driver.execute_script("window.history.go(-1)") # Go back to timetable lookup

def LogUrls(urls):
    if len(urls):
        print("All timetable URLs collected.")
        sys.stdout.write("\nSaving URLs to DB...")
        sys.stdout.flush()

        mydb = mongo["test_db"]
        mycol = mydb["timetables"]
        mycol.insert_many(urls)

        sys.stdout.write("\rSaving URLs to DB... Done.\n")
        sys.stdout.flush()
    else:
        print("No timetable URLs collected.")

urls = []
mongo = ConnectToDB()
driver = SetupDriver()

gatheringURLs = True
continueOk = True
deptCount = 16
courseCount = 35

totalCourses = GetDeptCourseTotal(driver, deptCount)

while gatheringURLs and courseCount < totalCourses:
    continueOk = True

    currentDept = SelectDepartment(driver, deptCount)
    if not currentDept:
        gatheringURLs = False
        break

    currentCourse = SelectCourse(driver, courseCount)
    if currentCourse:
        continueOk = True
    else:
        courseCount = 0
        deptCount += 1
        continue

    SelectGeneralDropdowns(driver, 'sem1')
    sem1URL = GetTimetableURL(driver)
    GoBack()
    SelectGeneralDropdowns(driver, 'sem2')
    sem2URL = GetTimetableURL(driver)
    courseCode = GetCourseCode(driver)
    courseYear = GetCourseYear(driver)
    courseLevel = GetCourseLevel(driver, courseCode)

    if continueOk:
        urls.append({ 'dept': currentDept, 'courseDetails': { 'course': currentCourse, 'courseCode': courseCode, 'courseYear': courseYear, 'courseLevel': courseLevel }, 'url': { 'semester1': sem1URL, 'semester2': sem2URL }, 'updatedAt': datetime.datetime.now() })

        GoBack()
        courseCount += 1

        sys.stdout.write("\rRetrieving %s timetable... Done.\n" %currentCourse)
        sys.stdout.flush()

    totalCourses = GetDeptCourseTotal(driver, deptCount)

    if courseCount == totalCourses:
        courseCount = 0
        deptCount += 1

# yearsAbrv = ['Y1', 'Y2', 'Y3', 'Y4']
#
# for url in urls:
#     courseName = url['course']
#     parts = courseName.split(' ')
#
#     for i in range(len(parts)):
#         part = parts[i].strip()
#         if part in yearsAbrv:
#             courseYear = part[1]
#         elif part.lower() == 'year':
#             courseYear = parts[i + 1].strip()
#
#     print(courseYear)


LogUrls(urls)

print("Finished.")
