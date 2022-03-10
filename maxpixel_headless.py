﻿from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import parse_qs
import urllib.parse as urlparse
from urllib.request import urlopen, Request, urlretrieve
from datetime import datetime
import csv
import os
import re
import copy
import time
import sys
import requests
import shutil
import pathlib
import cgi
import glob


DIR = os.path.dirname(os.path.abspath(__file__))
print(DIR)

txtFile = {}
filename = dirname = ''
hasLogin = False

FOLDER = 'maxpixel'

DRIVER_PATH = os.path.join(DIR, "chromedriver.exe")


FIRST_PAGE = int(sys.argv[1]) if len(sys.argv) > 1 else 1
LAST_PAGE = int(sys.argv[2]) if len(sys.argv) > 2 else 7520
# login page
""" USERNAME_SELECTOR = "//input[@id='edit-name']"
PASSWORD_SELECTOR = "//input[@id='edit-pass']"
SIGNIN_SELECTOR = "//button[@id='edit-submit']"
username = "Yankee"
password = "23579691" """

# list page
AELEMENTS_SELECTOR = "//div[@id='photo_grid']//a"
#LAST_AELEMENT_SELECTOR = "//div[@class='img-grid animated-grid']/div[contains(@class,'reveal') and not(contains(@class,'pubspace'))][30]/a"

# detail page
#THUMBNAIL_SELECTOR = "//div[@id='photo-pins']/img"
#ID_SELECTOR = "//figure[contains(@class,'wp-block-image')]/img"
TITLE_SELECTOR = "//h1"
#DESC_SELECTOR = "//strong[text()='Description']/following-sibling::em"
TAG_SELECTOR = "//div[@class='inside']/p[text()[contains(.,'tag')]]"
CATEGORY_SELECTOR = "//table[@id='details']//th[text()='Category']/following-sibling::td"
CC_SELECTOR = "//div[@style='margin:20px 0 10px;padding:15px 20px;background:#f7f8fa;line-height:1.5']"
#AUTHOR_SELECTOR = "//h3//a[contains(@href,'/photographer')]"
#SOURCE_SELECTOR = "//div[contains(text(),'Source')]"
#DATE_PUBLISHED_SELECTOR = "//strong[text()='UPLOADED: ']//parent::p"
#SIZE_SELECTOR = "//div[@id='detail_content']/div[1]"
# FILE_TYPE_SELECTOR = "//div[@style=\"margin-top:5px; background-image:url('http://res.publicdomainfiles.com/i/dloption.png'); background-repeat:no-repeat;\"]/div[@style='border:1px solid #c9c9c9; float:right; margin-left:5px; width:318px; background-color:#FFFFFF;'][1]//div[@style='font-family:Arial; font-size:11px; padding-left:5px;'][last()]"
DOWNLOAD_SELECTOR = "//div[@class='right']/div[@class='download_menu']/span"
DOWNLOAD2a_SELECTOR = "//div[@class='right']//div[@class='bubble se']//td[text()='SVG']//input"
DOWNLOAD2b_SELECTOR = "//div[@class='right']//div[@class='bubble se']//tr[last()]//input"
DOWNLOAD3_SELECTOR = "//div[@class='right']//div[contains(@class,'bubble')]//input[@value='View']"

def getDateString():
    now = datetime.now()
    print("now =", now)
    # dd/mm/YY H:M:S
    return now.strftime("%Y.%m.%d_%H.%M.%S")


def initListCSV(page):
    global filename, dirname, DIR, FOLDER
    listFile = f"list_{page}.csv"
    print('creating '+f'{listFile}...')
    filename = os.path.join(
        DIR, f"{FOLDER}/csv/{listFile}")
    # print(filename)
    dirname = os.path.dirname(filename)
    print('dirname:')
    print(dirname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def getTxt(variable, default_value=0):
    global DIR, FOLDER, txtFile
    tempPath = os.path.join(DIR, f"{FOLDER}/{x}/{variable}.txt")
    tempFolderPath = os.path.dirname(tempPath)
    tempFile = pathlib.Path(tempPath)

    if not os.path.exists(tempFolderPath):
        os.makedirs(tempFolderPath)

    if tempFile.exists():
        fileContent = open(tempPath, 'r')
        string = fileContent.readline()
        if string.isdigit():
            txtFile[variable] = int(string)
            return txtFile[variable]

    return saveTxt(variable, default_value)


def saveTxt(variable, number):
    global DIR, FOLDER, txtFile
    tempPath = os.path.join(DIR, f"{FOLDER}/{x}/{variable}.txt")
    tempFolderPath = os.path.dirname(tempPath)
    tempFile = pathlib.Path(tempPath)

    if not os.path.exists(tempFolderPath):
        os.makedirs(tempFolderPath)

    fileContent = open(tempPath, 'w')
    fileContent.write(str(number))

    txtFile[variable] = int(number)
    return txtFile[variable]


def selectCatch(driver, selector, type='text', multiple=False):
    try:
        if multiple:
            elements = driver.find_elements_by_xpath(selector)
            elementList = []
            for element in elements:
                elementList.append(getSelect(element, type))

            return elementList
        else:
            element = driver.find_element_by_xpath(selector)

        return getSelect(element, type)

    except NoSuchElementException:
        print('no such element:')
        print(selector)
        return ''


def getSelect(element, type='text'):
    if type == 'text':
        return element.text
    return element.get_attribute(type)


def makeScreenshot(driverTemp, height=1500, width=1092):
    driverTemp.set_window_size(width, height)
    dt = getDateString()
    saveScreenshotPath = os.path.join(DIR, f"{FOLDER}/screenshot/{dt}.png")
    if not os.path.exists(os.path.dirname(saveScreenshotPath)):
        os.makedirs(os.path.dirname(saveScreenshotPath))
    driverTemp.save_screenshot(saveScreenshotPath)


def checkPageFine(driverTemp, selector, isRestartDriver=False, sec=3, sleep=0):
    # fix for special situations like lightbox
    driverTemp.set_window_size(1500, 1500)
    try:
        element = WebDriverWait(driverTemp, sec).until(
            EC.presence_of_element_located(
                (By.XPATH, selector))
        )
        print(f"checked {selector} exists! Proceeding...")

        return True
    except TimeoutException:
        print(
            f"TimeoutException on selecting {selector}! resetting session and retry the page...")
        if (sleep > 0):
            print('sleeping.....')
            time.sleep(5)
            print('waking up.....')
        if isRestartDriver:
            driverTemp = restartDriver(driverTemp)
        return False


def saveErrorDownloadLog(page, order, detailUrl):
    logPath = os.path.join(DIR, f"{FOLDER}/error.log")
    logFile = pathlib.Path(logPath)
    if logFile.exists():
        with open(logPath, 'a') as file:
            file.write(f'{page};{order};{detailUrl}\n')
    else:
        with open(logPath, 'w') as file:
            file.write(f'{page};{order};{detailUrl}\n')


def getPage(driverTemp, url):
    global x, txtFile
    print('calling:')
    print(url)
    while True:
        try:
            driverTemp.get(url)
            break
        except TimeoutException as e:
            saveErrorDownloadLog(x, txtFile[y], url)
            driverTemp.delete_all_cookies()
            print("Page load Timeout. Deleting cookies and retrying...")


def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
    staleElement = True
    while staleElement:
        try:
            wait = WebDriverWait(driverTemp, wait_time)
            element = wait.until(
                EC.element_to_be_clickable((By.XPATH, selector)))

            if mouse_simulation:
                ActionChains(driverTemp).move_to_element(
                    element).click(element).perform()
            else:
                driverTemp.execute_script("arguments[0].click();", element)

            staleElement = False
            return True
        except StaleElementReferenceException:
            print('StaleElementReferenceException, retrying...')
            staleElement = True
        except TimeoutException:
            print('TimeoutException... element not found')
            return False
        except ElementClickInterceptedException as e:
            print(
                'ElementClickInterceptedException... element was overlayed by another element..')
            print(e)
            return False


def restartDriver(driverTemp, timeoutTemp=40):
    global hasLogin

    if driverTemp is not None:
        driverTemp.delete_all_cookies()
        driverTemp.quit()

    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    # chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1320,1080")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('log-level=2')

    d = DesiredCapabilities.CHROME
    d['loggingPrefs'] = {'browser': 'ALL'}

    driverTemp = webdriver.Chrome(
        options=chrome_options, executable_path=DRIVER_PATH, desired_capabilities=d)
    driverTemp.set_page_load_timeout(timeoutTemp)
    driverTemp.delete_all_cookies()

    if hasLogin:
        driverTemp = login(driverTemp)

    return driverTemp


def login(driverTemp):
    global USERNAME_SELECTOR, PASSWORD_SELECTOR, SIGNIN_SELECTOR, username, password
    getPage(driverTemp, 'https://www.rawpixel.com/user/login')

    emailElement = driverTemp.find_element_by_xpath(USERNAME_SELECTOR)
    passwordElement = driverTemp.find_element_by_xpath(PASSWORD_SELECTOR)

    emailElement.send_keys(username)
    passwordElement.send_keys(password)

    clickCatch(driverTemp, SIGNIN_SELECTOR)

    print('clicked login')

    return driverTemp

def isURLValid(URL):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return (re.match(regex, URL) is not None)


# if is virtual, the requests object will be returned, else the actual url
def getRealRequest(URL, isVirtual=True, isStream=False):
    global driver

    if (isURLValid(URL) is not True):
        return ''

    if isVirtual:
        # Open the url image, set stream to True, this will return the stream content.

        r = requests.get(URL, stream=isStream, headers={
                         'User-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A5370a Safari/604.1'})
        if (URL != r.url):
            print('real url after redirection')
            print(r.url)
        return r
    else:
        driver.get(URL)
        return driver.current_url


# dependent: getRealRequest,isURLvalid
# y is the counter, default is nothing
# row is to append current row
def downloadFromURL(URL, dirname, row=[], y=-1, isServerDecidesFilename=False):
    global x, txtFile, ToDLFileName
    if (isURLValid(URL) is not True):
        print('URL is not valid')
        row.append('')
        row.append('')
        row.append('')
        return False
    try:
        r = getRealRequest(URL, True, True)
        print('downloading image...')

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True

            fileName = ToDLFileName
            print('filename')
            print(fileName) 
            """ if isServerDecidesFilename:
                # server decides filename again...
                remotefile = urlopen(r.url)
                blah = remotefile.info()['Content-Disposition']
                value, params = cgi.parse_header(blah)
                fileName = params["filename"]
                print('server decided filename')
                print(fileName)
            else:
                # filename is there
                a = urlparse.urlparse(r.url)
                fileName = os.path.basename(a.path)
                # get parameter
                #fileName = urlparse.parse_qs(a.query)['image'][0]
                print('filename')
                print(fileName) """

            # Open a local file with wb ( write binary ) permission.
            with open(os.path.join(dirname, fileName), 'wb') as f:
                shutil.copyfileobj(r.raw, f)

            print('Image sucessfully Downloaded: ',
                  os.path.join(dirname, fileName))

            row.append(r.url)
            row.append(fileName)
            row.append(getDateString())
        else:
            print('Image Couldn\'t be retreived')
            saveErrorDownloadLog(x, txtFile['y'], URL)
            row.append('')
            row.append('')
            row.append('')
    except OSError as e:
        saveErrorDownloadLog(x, txtFile['y'], URL)
        print(e)


def getSubstringBetween(text, left, right):
    try:
        return re.search(f'{left}(.+?){right}', text).group(1)
    except AttributeError:
        return ''
        
def clickCatch(driverTemp, selector, wait_time=5, mouse_simulation=False):
    staleElement = True
    while staleElement:
        try:
            wait = WebDriverWait(driverTemp, wait_time)
            element = wait.until(
                EC.element_to_be_clickable((By.XPATH, selector)))

            if mouse_simulation:
                ActionChains(driverTemp).move_to_element(
                    element).click(element).perform()
            else:
                # element.click()
                driverTemp.execute_script("arguments[0].click();", element)

            staleElement = False
            return True
        except StaleElementReferenceException:
            print('StaleElementReferenceException, retrying...')
            staleElement = True
        except TimeoutException:
            print('TimeoutException... element not found')
            return False
        except ElementClickInterceptedException as e:
            print(
                'ElementClickInterceptedException... element was overlayed by another element..')
            print(e)
            return False


x = FIRST_PAGE
#txtFile['x'] = 1
txtFile['y'] = 0

driver = None
driver = restartDriver(driver)
# while txtFile['x'] < LAST_PAGE+1:
while x < LAST_PAGE+1:
    #getTxt('x', 1)
    getTxt('y')
    """ getPage(
        driver, f"https://www.maxpixel.net/?page={txtFile['x']}") """
    getPage(
        driver, f"https://www.maxpixel.net/?page={x}")

    # need to make screenshot to scrape the last items...
    #makeScreenshot(driver)

    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

    if checkPageFine(driver, AELEMENTS_SELECTOR) == False:
        continue

    detailUrls = selectCatch(driver, AELEMENTS_SELECTOR, 'href', True)

    print('len of detailUrls')
    print(len(detailUrls))

    if txtFile['y'] < len(detailUrls):
        initListCSV(x)
        isCSVExists = os.path.exists(filename)
        with open(filename, 'a', encoding="utf-8", newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not isCSVExists:
                writer.writerow(['detailUrl', 'title', 'tags', 'category', 'cc',
                                 'fileURL', 'fileName', 'date_downloaded'])
            while txtFile['y'] < len(detailUrls):

                print('txtFile')
                print(txtFile)

                row = [detailUrls[txtFile['y']]]

                getPage(driver, detailUrls[txtFile['y']])

                title = selectCatch(driver, TITLE_SELECTOR)
                print('title')
                print(title)
                row.append(title)

                tags = selectCatch(driver, TAG_SELECTOR)
                print('tags')
                print(tags)
                tags = getSubstringBetween(tags, ': ', '\.')
                print('tags')
                print(tags)
                row.append(tags)

                cat = selectCatch(driver, CATEGORY_SELECTOR)
                print('cat')
                print(cat)
                row.append(cat)

                cc = selectCatch(driver, CC_SELECTOR)
                print('cc')
                print(cc)
                row.append(cc)

                # triggering page for image download from browser
                clickCatch(driver, DOWNLOAD_SELECTOR)
                
                makeScreenshot(driver)
                ToDLFileName = selectCatch(driver, DOWNLOAD2a_SELECTOR,'value')
                if ToDLFileName == '':
                    ToDLFileName = selectCatch(driver, DOWNLOAD2b_SELECTOR,'value')
                print('ToDLFileName')
                print(ToDLFileName)

                fileID = getSubstringBetween(ToDLFileName, '-', '\.')
                print('fileID')
                print(fileID)

                downloadFromURL(f'http://dl.maxpixel.freegreatpicture.com/?f={ToDLFileName}&pid={fileID}', f'{dirname}\\{x}', row)

                writer.writerow(row)
                saveTxt('y', txtFile['y']+1)

    if len(detailUrls) > 0:
        #saveTxt('x', txtFile['x']+1)
        x += 1
        saveTxt('y', 0)
