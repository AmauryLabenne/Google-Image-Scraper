# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 13:01:02 2020

@author: OHyic
"""
# import selenium drivers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

# import helper libraries
import time
import urllib.request
from urllib.parse import urlparse
import os
import requests
import io
from PIL import Image
import re

# custom patch libraries
import patch


class GoogleImageScraper():
    def __init__(self, webdriver_path, image_path, search_key="cat", number_of_images=1, headless=True,
                 min_resolution=(0, 0), max_resolution=(1920, 1080), max_missed=10):
        # check parameter types
        image_path = os.path.join(image_path, search_key)
        if (type(number_of_images) != int):
            print("[Error] Number of images must be integer value.")
            return
        if not os.path.exists(image_path):
            print("[INFO] Image path not found. Creating a new folder.")
            os.makedirs(image_path)

        # check if chromedriver is installed
        if (not os.path.isfile(webdriver_path)):
            is_patched = patch.download_lastest_chromedriver()
            if (not is_patched):
                exit(
                    "[ERR] Please update the chromedriver.exe in the webdriver folder according to your chrome version:https://chromedriver.chromium.org/downloads")

        for i in range(1):
            try:
                # try going to www.google.com
                options = Options()
                if (headless):
                    options.add_argument('--headless')
                driver = webdriver.Chrome(webdriver_path, chrome_options=options)
                driver.set_window_size(1400, 1050)
                driver.get("https://www.google.com")
                driver.implicitly_wait(2)
                driver.find_element_by_xpath('// *[ @ id = "L2AGLb"] / div').click()
            except Exception as e:
                # update chromedriver
                pattern = '(\d+\.\d+\.\d+\.\d+)'
                version = list(set(re.findall(pattern, str(e))))[0]
                is_patched = patch.download_lastest_chromedriver(version)
                if (not is_patched):
                    exit(
                        "[ERR] Please update the chromedriver.exe in the webdriver folder according to your chrome version:https://chromedriver.chromium.org/downloads")

        self.driver = driver
        self.search_key = search_key
        self.number_of_images = number_of_images
        self.webdriver_path = webdriver_path
        self.image_path = image_path
        self.url = "https://www.google.com/search?q=%s&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947" % (
            search_key)
        self.headless = headless
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        self.max_missed = max_missed

    def find_image_urls(self):
        """
            This function search and return a list of image urls based on the search key.
            Example:
                google_image_scraper = GoogleImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls = google_image_scraper.find_image_urls()

        """
        print("[INFO] Gathering image links")
        image_urls = []
        count = 0
        missed_count = 0
        self.driver.get(self.url)
        time.sleep(3)
        indx = 1

        # Load all page with scrolldown
        for i in range(100) :
            self.driver.execute_script("window.scrollTo(100000,document.body.scrollHeight)")

        # wait for images to load
        time.sleep(3)

        # find all images on the page
        images = self.driver.find_elements_by_xpath("//img[@class='rg_i Q4LuWd']")



        image_urls = []
        for i, image in enumerate(images):
            # get the image URL
            image_url = image.get_attribute("src") or image.get_attribute("data-src")

            # make sure the image URL is not empty
            if image_url:
                image_urls.append(image_url)
                # # create a filename for the image
                # filename = f"{search_term}_{i}.jpg"
                #
                # # download the image and save it to disk
                # urllib.request.urlretrieve(image_url, filename)
                #
                # print(f"Downloaded {filename}")
            else:
                print("Skipping image due to missing URL")

        image_urls_sub = image_urls[0:min(self.number_of_images, len(image_urls))]


        self.driver.quit()
        print("[INFO] Google search ended")
        return image_urls_sub

    def save_images(self, image_urls, keep_filenames):
        print(keep_filenames)
        # save images into file directory
        """
            This function takes in an array of image urls and save it into the given image path/directory.
            Example:
                google_image_scraper = GoogleImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls=["https://example_1.jpg","https://example_2.jpg"]
                google_image_scraper.save_images(image_urls)

        """
        print("[INFO] Saving image, please wait...")
        for indx, image_url in enumerate(image_urls):
            try:
                print("[INFO] Image url:%s" % (image_url))
                search_string = ''.join(e for e in self.search_key if e.isalnum())
                image = requests.get(image_url, timeout=5)
                if image.status_code == 200:
                    with Image.open(io.BytesIO(image.content)) as image_from_web:
                        try:
                            if (keep_filenames):
                                # extact filename without extension from URL
                                o = urlparse(image_url)
                                image_url = o.scheme + "://" + o.netloc + o.path
                                name = os.path.splitext(os.path.basename(image_url))[0]
                                # join filename and extension
                                filename = "%s.%s" % (name, image_from_web.format.lower())
                            else:
                                filename = "%s%s.%s" % (search_string, str(indx), image_from_web.format.lower())

                            image_path = os.path.join(self.image_path, filename)
                            print(
                                f"[INFO] {self.search_key} \t {indx} \t Image saved at: {image_path}")
                            image_from_web.save(image_path)
                        except OSError:
                            rgb_im = image_from_web.convert('RGB')
                            rgb_im.save(image_path)
                        image_resolution = image_from_web.size
                        if image_resolution != None:
                            if image_resolution[0] < self.min_resolution[0] or image_resolution[1] < \
                                    self.min_resolution[1] or image_resolution[0] > self.max_resolution[0] or \
                                    image_resolution[1] > self.max_resolution[1]:
                                image_from_web.close()
                                os.remove(image_path)

                        image_from_web.close()
            except Exception as e:
                print("[ERROR] Download failed: ", e)
                pass
        print("--------------------------------------------------")
        print(
            "[INFO] Downloads completed. Please note that some photos were not downloaded as they were not in the correct format (e.g. jpg, jpeg, png)")
