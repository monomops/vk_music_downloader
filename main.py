# -*- encoding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
import pickle
import time
import sys
import os
import hashlib
from urllib.parse import urlparse
from urllib.request import urlretrieve
import platform
from config import *
logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


def vk_login(driver):
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)
    except:
        login = driver.find_element_by_id("email")
        login.send_keys(VK_LOGIN)

        password = driver.find_element_by_id("pass")
        password.send_keys(VK_PASS)

        login_button = driver.find_element_by_id("login_button")
        login_button.click()

        # Wait until urls changes
        WebDriverWait(driver, 10).until(lambda driver: driver.current_url != VK_LOGIN_URL)

    driver.get("https://vk.com/login")

    # Try to find smth with id `profile_photo_link` -> suppose to be successfully logged in
    try:
        driver.find_element_by_id("profile_photo_link")
        logger.info("Logged in as: %s " % driver.find_element_by_class_name('page_name').text)
        pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb+"))
    except NoSuchElementException:
        logger.error("Error during logging procedure") & sys.exit()


def main():
    logger.info("Launching chrome...")
    # Create folder
    if not os.path.exists(MUSIC_PATH):
        logger.error("Bad music folder") & sys.exit()

    if platform.system() == "Windows":
        driver = webdriver.Chrome('chromedriver/chromedriver.exe')
    else:
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(800, 600))
        display.start()
        driver = webdriver.Chrome('chromedriver/chromedriver')
    driver.get("https://vk.com/login")
    vk_login(driver)

    for friend in VK_FRIENDS:
        driver.get("https://vk.com/%s" % friend)
        try:
            audio_url = driver.find_element_by_id("profile_audios")\
                .find_element_by_class_name('module_header').get_attribute('href')
        except NoSuchElementException:
            logger.error("Friend %s has his music closed" % friend)
            continue
        logger.info("Processing friend %s" % friend)
        driver.get(audio_url)

        # Scroll page to bottom up to real end
        start_count = len(driver.find_elements_by_class_name("audio_row"))
        while True:
            count = len(driver.find_elements_by_class_name("audio_row"))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            try:
                WebDriverWait(driver, DEFAULT_DELAY).until(
                    lambda driver: len(driver.find_elements_by_class_name("audio_row")) > start_count)
            except TimeoutException:
                break
            start_count = count

        logger.info("Found %d tracks" % len(driver.find_elements_by_class_name("audio_row")))
        time.sleep(2)
        for audio in driver.find_elements_by_class_name("audio_row"):
            # Get audio row closer to screen
            driver.execute_script("arguments[0].scrollIntoView(false);", audio)
            audio_play = audio.find_element_by_class_name("_audio_play")
            # Click on it
            try:
                WebDriverWait(driver, DEFAULT_DELAY).until(EC.presence_of_element_located((By.ID, audio_play.get_attribute('id'))))
            except TimeoutException:
                continue
            audio_play.click()

            # Collect info
            try:
                WebDriverWait(driver, DEFAULT_DELAY).until(
                    lambda driver: len(driver.execute_script("return getAudioPlayer()._impl._currentAudioEl.src")) > 0)
                raw_url = driver.execute_script("return getAudioPlayer()._impl._currentAudioEl.src")
            except TimeoutException:
                continue

            url = urlparse(raw_url)
            singer = audio.find_element_by_class_name("audio_performer").text
            song = audio.find_element_by_class_name("audio_title_inner").text
            song_name = "%s :: %s - %s" % (friend, singer, song)
            file_name = hashlib.md5(song_name.encode('utf-8')).hexdigest()
            file_url = "%s://%s%s" % (url.scheme, url.netloc, url.path)
            # Processing the following
            logger.info("Download %s, save as %s" % (file_url, file_name))
            file_dir = "%s/%s" % (MUSIC_PATH, friend)
            # Create folder
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
            # Download song
            file_path = "%s/%s.mp3" % (file_dir, file_name)
            if not os.path.exists(file_path):
                urlretrieve(file_url, file_path)

    driver.close()
    if platform.system() != "Windows":
        display.stop()

if __name__ == "__main__":
    main()