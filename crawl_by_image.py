#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 cbwces <sknyqbcbw@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import sys
import time
import math
import argparse
import shutil
import imghdr
import requests
import base64
from multiprocessing import Pool

import selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def load_image_path_list(in_file):

    with open(in_file, "r") as f:
        image_path_list = f.read().strip().split("\n")
    return image_path_list

def browser_initialize(driver_path, proxy_server):

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--proxy-server=" + proxy_server)
    browser = webdriver.Chrome(executable_path=driver_path, chrome_options=chrome_options)
    return browser

def chunker_list(image_list, jobs):

    return list(image_list[i::jobs] for i in range(jobs))

def create_sub_directory_by_image(image_path, out_path, prefix):

    ext = image_path.split('.')[-1]
    new_dir = os.path.join(out_path, prefix)
    os.makedirs(new_dir, exist_ok=True)
    shutil.copy(image_path, os.path.join(new_dir, "base_img." + ext))
    return new_dir

def query_image_search_page(browser, image_path):

    browser.get("https://www.google.com/imghp?hl=en&authuser=0&ogbl")
    browser.find_element_by_xpath('//*[@id="sbtc"]/div/div[3]/div[2]/span').click()
    browser.find_element_by_xpath('//*[@id="dRSWfb"]/div/a').click()
    w = WebDriverWait(browser, 15)
    elem = w.until(EC.presence_of_element_located((By.XPATH, '//*[@id="awyMjb"]')))
    elem.send_keys(image_path)
    time.sleep(1)
    search_by_this_image_elements = browser.find_elements_by_xpath('//*[@id="rso"]/div[2]/div/div[2]/g-section-with-header/div[1]/title-with-lhs-icon/a/div[2]')
    return search_by_this_image_elements

def wait_and_click(browser, xpath, exception_element='//*[@id="islmp"]/div/div[1]/div/div[2]/span'):

    try:
        w = WebDriverWait(browser, 15)
        elem = w.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        elem.click()
    except Exception as e:
        wait_and_click(browser, exception_element)
    return True

def google_full_search(browser, search_similar_images_elems, num_of_images=math.inf):

    if len(search_similar_images_elems) == 0:
        return []
    search_similar_images_elems[0].click()
    time.sleep(1)
    elem = browser.find_element_by_tag_name("body")
    print('Scraping links')

    wait_and_click(browser, '//div[@data-ri="0"]')
    time.sleep(1)

    links = []
    count = 1

    last_scroll = 0
    scroll_patience = 0

    while count <= num_of_images:
        try:
            xpath = '//div[@id="islsp"]//div[@class="v4dQwb"]'
            div_box = browser.find_element(By.XPATH, xpath)

            xpath = '//img[@class="n3VNCb"]'
            img = div_box.find_element(By.XPATH, xpath)

            xpath = '//div[@class="k7O2sd"]'
            loading_bar = div_box.find_element(By.XPATH, xpath)

            # Wait for image to load. If not it will display base64 code.
            while str(loading_bar.get_attribute('style')) != 'display: none;':
                time.sleep(0.1)

            src = img.get_attribute('src')

            if src is not None:
                links.append(src)
                print('%d: %s' % (count, src))
                count += 1

        except StaleElementReferenceException:
            # print('[Expected Exception - StaleElementReferenceException]')
            pass
        except Exception as e:
            print('[Exception occurred while collecting links from google_full] {}'.format(e))

        scroll = browser.execute_script("return window.pageYOffset;")
        if scroll == last_scroll:
            scroll_patience += 1
        else:
            scroll_patience = 0
            last_scroll = scroll

        if scroll_patience >= 30:
            break

        elem.send_keys(Keys.RIGHT)

    links = list(dict.fromkeys(links))
    return links

def download_images_by_urls(links, num_of_images, out_path):

    def base64_to_object(src):
        header, encoded = str(src).split(',', 1)
        data = base64.decodebytes(bytes(encoded, encoding='utf-8'))
        return data

    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    def save_object_to_file(object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    def validate_image(path):
        ext = imghdr.what(path)
        if ext == 'jpeg':
            ext = 'jpg'
        return ext  # returns None if not valid

    total = len(links)
    success_count = 0

    if num_of_images == 0:
        num_of_images = total

    for index, link in enumerate(links):
        if success_count >= num_of_images:
            break

        try:
            print('Downloading {} / {}'.format(success_count + 1, num_of_images))

            if str(link).startswith('data:image/jpeg;base64'):
                response = base64_to_object(link)
                ext = 'jpg'
                is_base64 = True
            elif str(link).startswith('data:image/png;base64'):
                response = base64_to_object(link)
                ext = 'png'
                is_base64 = True
            else:
                response = requests.get(link, stream=True)
                ext = get_extension_from_link(link)
                is_base64 = False

            path = os.path.join(out_path, str(index) + "." + ext)
            save_object_to_file(response, path, is_base64=is_base64)

            success_count += 1
            del response

            ext2 = validate_image(path)
            if ext2 is None:
                print('Unreadable file - {}'.format(link))
                os.remove(path)
                success_count -= 1
            else:
                if ext != ext2:
                    path2 = os.path.join(out_path, str(index) + '.' + ext2)
                    os.rename(path, path2)
                    print('Renamed extension {} -> {}'.format(ext, ext2))

        except Exception as e:
            print('Download failed - ', e)
            continue

def crawl(image_list, num_of_images, out_path, nth_worker, driver_path, proxy_server):

    browser = browser_initialize(driver_path, proxy_server)
    for nth_in_list, image_path in enumerate(image_list):
        output_subdir = create_sub_directory_by_image(image_path, out_path, str(nth_worker) + "_" + str(nth_in_list))
        search_similar_images_elems = query_image_search_page(browser, image_path)
        links = google_full_search(browser, search_similar_images_elems, math.inf if num_of_images == 0 else 2 * num_of_images)
        download_images_by_urls(links, num_of_images, output_subdir)
    browser.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Search Image by Image')
    parser.add_argument("--in_file", "-i", required=True, type=str, help="File list of search based images")
    parser.add_argument("--out_path", "-o", required=True, type=str, help="Path of downloaded images")
    parser.add_argument("--jobs", "-j", default=4, type=int, help="Number of jobs, 0 represent using main process only")
    parser.add_argument("--num_of_images", "-n", default=0, type=int, help="Max number of images download per base image, 0 represent crawl as much as possible")
    parser.add_argument("--execution_path", "-x", default="chromedriver/chromedriver_linux", type=str, help="Path of Chrome driver")
    parser.add_argument("--proxy_server", "-p", default="", type=str, help="Proxy server for Chrome flag")
    args = parser.parse_args()

    os.makedirs(args.out_path, exist_ok=True)
    image_list = load_image_path_list(args.in_file)
    if args.jobs == 0:
        crawl(image_list, args.num_of_images, args.out_path, 0, args.execution_path, args.proxy_server)
    else:
        image_list_chunked = chunker_list(image_list, args.jobs)
        task_args = [(image_list_per_chunk, args.num_of_images, args.out_path, i, args.execution_path, args.proxy_server) for image_list_per_chunk, i in zip(image_list_chunked, range(args.jobs))]
        pool = Pool(args.jobs)
        for p in range(args.jobs):
            pool.apply_async(crawl, args=task_args[p])
        pool.close()
        pool.join()
