#Hacking Alexa's voice recordings
#Code Project article by Michael Haephrati
#haephrati@gmail.com
#
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from credentials import Credentials
from argparse import ArgumentParser
from time import sleep
import re
import os 
import uuid
import requests
import logging
from time import strptime
from datetime import datetime, timedelta, date
import traceback


logger = logging.getLogger("alexa")
formatter = logging.Formatter("%(asctime)s;%(levelname)s    %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler(filename="alexa.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class WindowsInhibitor:
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):
        import ctypes
        print("Preventing Windows from going to sleep.")
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS | \
            WindowsInhibitor.ES_SYSTEM_REQUIRED)

    def uninhibit(self):
        import ctypes
        print("Allowing Windows to go to sleep.")
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS)


def enable_downloads(driver, download_dir):
    driver.command_executor._commands["send_command"] = (
        "POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 
    'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    command_result = driver.execute("send_command", params)


def every_downloads_chrome(driver):
    # waits for download to complete
    if not driver.current_url.startswith("chrome://downloads"):
        driver.get("chrome://downloads/")
    return driver.execute_script("""
        var items = downloads.Manager.get().items_;
        if (items.every(e => e.state === "COMPLETE"))
            return items.map(e => e.fileUrl || e.file_url);
        """)


def init_driver():
    logger.info("Starting chromedriver")
    chrome_options = Options()
    # use local data directory
    # headless mode can't be enabled since then amazon shows captcha
    chrome_options.add_argument("user-data-dir=selenium") 
    chrome_options.add_argument("start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument('--disable-gpu')  
    chrome_options.add_argument('--remote-debugging-port=4444')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--mute-audio")
    path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.isdir(os.path.join(path, 'audios')):
        os.mkdir(os.path.join(path, 'audios'))
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": os.path.join(path, 'audios'),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    try:
        driver = webdriver.Chrome(
            executable_path=ChromeDriverManager().install(), 
            options=chrome_options, service_log_path='NUL')
    except ValueError:
        logger.critical("Error opening Chrome. Chrome is not installed?")
        exit(1)
    driver.implicitly_wait(10)
    # set downloads directory to audios folder
    enable_downloads(driver, os.path.join(path, 'audios'))
    return driver


def amazon_login(driver, date_from, date_to):
    driver.implicitly_wait(5)
    logger.info("GET https://alexa.amazon.com/spa/index.html")
    # get main page
    driver.get('https://alexa.amazon.com/spa/index.html')
    sleep(4)
    url = driver.current_url
    # if amazon asks for signin, it will redirect to a page with signin in url
    if 'signin' in url:
        logger.info("Got login page: logging in...")
        # find email field
        # WebDriverWait waits until elements appear on the page
        # so it prevents script from failing in case page is still being loaded
        # Also if script fails to find the elements (which should not happen
        # but happens if your internet connection fails)
        # it is possible to catch TimeOutError and loop the script, so it will
        # repeat.
        check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'ap_email')))
        email_field = driver.find_element_by_id('ap_email')
        email_field.clear()
        # type email
        email_field.send_keys(Credentials.email)
        check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'ap_password')))
        # find password field
        password_field = driver.find_element_by_id('ap_password')
        password_field.clear()
        # type password
        password_field.send_keys(Credentials.password)
        # find submit button, submit
        check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'signInSubmit')))
        submit = driver.find_element_by_id('signInSubmit')
        submit.click()
    # get history page
    driver.get('https://www.amazon.com/hz/mycd/myx#/home/alexaPrivacy/'
               'activityHistory&all')
    sleep(4)
    # amazon can give second auth page, so repeat the same as above
    if 'signin' in driver.current_url:
        logger.info("Got confirmation login page: logging in...")
        try:
            check_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, 'ap_email')))
            email_field = driver.find_element_by_id('ap_email')
            email_field.clear()
            email_field.send_keys(Credentials.email)
            check_field = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, 'continue')))
            submit = driver.find_element_by_id('continue')
            submit.click()
            sleep(1)
        except:
            pass
        check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'ap_password')))
        password_field = driver.find_element_by_id('ap_password')
        password_field.clear()
        password_field.send_keys(Credentials.password)
        check_field = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, 'signInSubmit')))
        submit = driver.find_element_by_id('signInSubmit')
        submit.click()
        sleep(3)
        logger.info("GET https://www.amazon.com/hz/mycd/myx#/home/alexaPrivacy/"
                   "activityHistory&all")
        # get history page again
        driver.get('https://www.amazon.com/hz/mycd/myx#/home/alexaPrivacy/'
                   'activityHistory&all')
    # find selector which allows to select Date Range 
    check = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "a-dropdown-prompt")))
    history = driver.find_elements_by_class_name('a-dropdown-prompt')
    history[0].click()
    check = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "a-dropdown-link")))
    # click 'All History'
    all_hist = driver.find_elements_by_class_name('a-dropdown-link')
    for link in all_hist:
        if date_from and date_to:
            if 'Custom' in link.text:
                link.click()
                from_d = driver.find_element_by_id('startDateId')
                from_d.clear()
                from_d.send_keys('11/03/2019')
                sleep(1)
                to_d = driver.find_element_by_id('endDateId')
                to_d.clear()
                to_d.send_keys('11/05/2019')
                subm = driver.find_element_by_id('submit')
                subm.click()
        elif 'All' in link.text:
            link.click()


def parse_page(driver):
    links = []
    # links will contain all links harvested from one page
    check = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                                                   (By.CLASS_NAME, "mainBox")))
    boxes = driver.find_elements_by_class_name('mainBox')
    # mainBox corresponds to each element with audio recording
    for box in boxes:
        # if there is no voice, element can be detected by its class and skipped
        non_voice = box.find_elements_by_class_name('nonVoiceUtteranceMessage')
        if non_voice:
            logger.info('Non-voice file. Skipped.')
            continue
        non_text = box.find_elements_by_class_name('textInfo')
        if non_text:
            if 'No text stored' in non_text[0].text:
                logger.info("Non-voice file. Skipped.")
                continue
        # else we can find audio element and extract its data
        check = WebDriverWait(driver, 30).until(EC.presence_of_element_located(
                                                       (By.TAG_NAME, "audio")))
        audio_el = box.find_elements_by_tag_name('audio')
        for audio in audio_el:
            try:
                attr = audio.get_attribute('id')
                # we extract ID attribute which then becomes a part of the link.
                # ID approximately looks like this (can vary):
                # audio-Vox:1.0/2019/10/27/21/1d2110cb8eb54f3cb6
                # here 2019/10/27/21 is the date, and the whole ID is being
                # added to the link to download said audio recording.

                # Additional info is stored in element with class summaryCss.
                # If there is no additional info then the element will be named
                # as 'audio could not be understood'.
                get_name = box.find_elements_by_class_name('summaryCss')
                if not get_name:
                    get_name = 'Audio could not be understood'
                else:
                    get_name = get_name[0].text
                # subInfo element contains date and device data which we extract
                check = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "subInfo")))
                subinfo = box.find_elements_by_class_name('subInfo')
                time = subinfo[0].text
                # extracting date from ID attribute, since it is easier.
                get_date = re.findall(r'\/(\d+\/\d+\/\d+\/\d+)\/', attr)
                try:
                    # replace slashes to -.
                    get_date = get_date[0].strip().replace('/', '-')
                except IndexError:
                    try:
                        # in case there is no date in the attribute
                        # (which should not happen anymore)
                        # we extract date from subInfo element and turn it
                        # into normal, easy for sorting date, e.g 2019/10/11.
                        get_date = re.findall(
                            r'On\s(.*?)\s(\d{1,2})\,\s(\d{4})', time)
                        month = get_date[0][0]
                        new = month[0].upper() + month[1:3].lower()
                        month = strptime(new,'%b').tm_mon
                        get_date = f"{get_date[0][2]}-{month}-{get_date[0][1]}"
                    except IndexError:
                        get_date = re.findall(r'(.*?)\sat', time)
                        day = get_date[0]
                        if 'Yesterday' in day:
                            day = datetime.now() - timedelta(days=1)
                            day = str(day.day)
                        elif 'Today' in day:
                            day = str(datetime.now().day)
                        day = day if len(day) == 2 else '0'+day
                        curr_month = str(datetime.now().month)
                        curr_month = curr_month if len(
                                            curr_month) == 2 else '0'+curr_month
                        curr_year = datetime.now().year
                        get_date = f"{curr_year}-{curr_month}-{day}"
                # Extract exact time and device
                find_p0 = time.find('at')
                find_p1 = time.find('on')
                get_time = time[find_p0+2:find_p1-1].replace(':', '-')
                device = time[find_p1:]
                get_name = get_name
                # Form element name
                name = f"{get_date} {get_time} {get_name} {device}"
                # Strip all dangerous symbols from the name.
                # Dangerous symbols are symbols which Windows can not accept
                name = re.sub(r'[^\w\-\(\) ]+', '', name)
                # Allow maximum 3 duplicates
                # if there is such element already, 
                # (1)+n will be added to its name.
                for link in links:
                    if name == link[1]:
                        name += ' (1)'
                        break
                dup = 1
                while dup <= 3:
                    for link in links:
                        if name == link[1]:
                            name = name.replace(f"({dup})", f"({dup+1})")
                    dup += 1
                print("_"*80)
                logger.info(f"Found: {attr}\n{name}")
                # check if recording already exists on the disk
                if not os.path.isfile(os.path.join('audios', name+'.wav')):
                    if not '/' in attr:
                        # if ID is incorrect at all, we play the file
                        # and try to extract the link generated by amazon itself
                        logger.info(
                            "ID attribute was not found. Playing the file.")
                        play_icon = box.find_elements_by_class_name(
                                                                   'playButton')
                        get_onclick = play_icon[0].get_attribute('onclick')
                        driver.execute_script(get_onclick)
                        sleep(8)
                        get_source = box.find_elements_by_tag_name('source')
                        src = get_source[0].get_attribute('src')
                        # if we had success, link is appended to links
                        if 'https' in src:
                            links.append([src, name])
                        else:
                            logger.critical(
                                   "Link was not found after playing the file. "
                                   "Item skipped.")
                    else:
                        # If audio ID is valid, we replace audio with id
                        # and append it to the link.
                        # From now we can download it.
                        if attr.replace('audio-', ''):
                            attr = attr.replace('audio-', 'id=')
                            links.append([
                            'https://www.amazon.com/hz/mycd/playOption?'+attr,
                            name])
                else:
                    logger.info(f"File exists; passing: {name}.wav")
            except Exception:
                logger.critical(traceback.format_exc())
                logger.critical("Item failed; passing")
                continue
    return links


def fetch(driver, item):
    attempt = 0  
    # this is counter which allows to retry fetching in case of fail.
    while True:
        link = item[0]
        name = item[1]
        # extract cookies from webdriver to be able to use requests.
        cookies = driver.get_cookies()
        s = requests.Session()
        # set useragent.
        s.headers = {'User-Agent': 
        ('Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36')
        }
        c = [s.cookies.set(c['name'], c['value']) for c in cookies]
        while True:
            try:
                logger.info(f"GET {link}")
                r = s.get(link)
                break
            except requests.exceptions.RequestException as e:
                # if Internet connection fails, it will be looped until success.
                logger.critical(e)
                logger.info("Retrying...")
                sleep(5)
                continue
        logger.info(r.status_code)
        if r.status_code == 200:
            # if amazon gives 200, it means link is valid.
            if len(r.content) > 1:
                # if content is more than 1 byte, save it:
                with open(
                          os.path.join('audios', name+'.wav'), 'wb'
                         ) as file:
                    file.write(r.content)
                logger.info(f"Download complete: {name}")
                break
            else:
                # in other case link will be written to the txt file.
                logger.critical("Response content is 0 bytes.")
                with open('failed_links.txt', 'a+') as file:
                    file.write(link+'\n')
                logger.info("Written the link to the 'failed_links.txt' file.")
                break
        else:
            logger.critical(f"Response code: {r.status_code}")
            # if response code is not 200, something is wrong with the link
            # or with server. Retrying 5 times and moving on.
            if attempt <= 5:
                logger.info(f"Retrying. Attempt #{attempt}")
                sleep(10)
                attempt += 1
                continue
            else:
                logger.critical(r.content)
                logger.critical(f"All attempts to download failed. "
                                 "Written response to the log.")
                break


def main():
    ap = ArgumentParser()
    ap.add_argument(
        "-f", "--date_from", required=False, 
        help=("Seek starting from date MM/DD/YYYY.")
    )
    ap.add_argument(
        "-t", "--date_to", required=False,
        help=("Seek until date MM/DD/YYYY.")
    )
    args = vars(ap.parse_args())
    if args["date_from"] and not args["date_to"]:
        args["date_to"] = str(datetime.now().month) +'/'+ str(datetime.now(
                                        ).day) +'/'+ str(datetime.now().year)
    if args["date_to"] and not args["date_from"]:
        logger.critical("You haven't specified beginning date. Use -f option.")
        exit(1)

    sys_sleep = None
    sys_sleep = WindowsInhibitor()
    logger.info("System inhibited.")
    sys_sleep.inhibit()
    
    # start chromedriver
    driver = init_driver()

    while True:
        try:
            # login
            amazon_login(driver, args["date_from"], args["date_to"])
            break
        except TimeoutException:
            # catch broken connection
            logger.critical("Timeout exception. No internet connection? "
                            "Retrying...")
            sleep(10)
            continue

    # after few attempts will reset the page
    failed_page_attempt = 0
    while True:
        logger.info("Parsing links...")
        driver.implicitly_wait(2)

        try:
            # parse current page for audios
            links = parse_page(driver)
            # reset fail counter on each success
            failed_page_attempt = 0
        except TimeoutException:
            # catch broken connection
            logger.critical(traceback.format_exc())
            if failed_page_attempt <= 3:
                logger.critical("No Internet connection? Retrying...")
                logger.critical(f"Attempt #{failed_page_attempt}/3")
                sleep(5)
                failed_page_attempt += 1
                continue
            else:
                failed_page_attempt = 0
                logger.critical("Trying to re-render page...")
                driver.execute_script('getPreviousPageItems()')
                sleep(5)
                driver.execute_script('getNextPageItems()')
                continue

        logger.info(f"Total files to download: {len(links)}")

        for item in links:
            # download parsed items
            fetch(driver, item)

        # find the 'Next' button, which moves to the next page.
        failed_button_attempt = 0
        while True:
            try:
                check_btn = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.ID, 'nextButton')))
                failed_button_attempt = 0
                break
            except TimeoutException:
                if failed_button_attempt <= 3:
                    logger.critical(
                            "Timeout exception: next button was not found. "
                            "No Internet connection? Waiting and retrying...")
                    logger.critical(f"Attempt #{failed_button_attempt}/3")
                    sleep(10)
                    failed_button_attempt += 1
                    continue
                else:
                    failed_button_attempt = 0
                    logger.critical("Trying to re-render page...")
                    driver.execute_script('getPreviousPageItems()')
                    sleep(5)
                    driver.execute_script('getNextPageItems()')
                    continue
        nextbtn = driver.find_element_by_id('nextButton').get_attribute('class')
        if 'navigationAvailable' in nextbtn:
            # if button is active, click it.
            driver.implicitly_wait(10)
            while True:
                try:
                    logger.info("Next page...")
                    driver.find_element_by_id('nextButton').click()
                    break
                except:
                    logger.critical("Unable to click the next button. "
                                    "Waiting and retrying...")
                    sleep(10)
                    continue
            continue
        else:
            # if button is inactive, this means it is the last page.
            # script is done here.
            break
    driver.close()
    driver.quit()
    if args['date_from']:
        logger.info('All done. Press Enter to exit.')
        i = input()
    else:
        logger.info("All done. Exit.")
    logger.info("System uninhibited.")
    sys_sleep.uninhibit()


if __name__ == '__main__':
	main()