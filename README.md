# Crawling Google Similar Images by Images

## Introduction

This is a simple script for searching and crawling images from Google by images on local disk

## Requirements

To use this script, you have to install "selenium" module of python, by `pip install selenium`
And Chrome driver is needed to provide a browser, just in [chromedriver directory](./chromedriver), you can also download a diffrent driver from [Google offical site](http://chromedriver.chromium.org/downloads)

## Usage

**NOTE**: This script just test on Linux device, but it should be work on other devices
1. First, prepare your images to be search, like the [example images](./example/base_images)
2. Make an images list, like [example images list](./example/search_images_list.txt), notice that all image paths in list must be absolute path, and you need to create your own image list (for linux, you can just run `find $(pwd)/example/base_images/ -type f > example/search_images_list.txt`)
3. For Linux user, run `python crawl_by_image.py -i example/search_images_list.txt -o example/images_out -j 2 -n 0 -x chromedriver/chromedriver_linux`, notice that if you are using Windows/MacOS, just replace `chromedriver/chromedrive_linux` to suitable Chrome driver
4. You can find search result images under "example/images_out/" directory, each search based image if named as "base_img.&lt;ext&gt;" under the same directory with other crawling images

## Parameters Explain

**--in_file/-i**: File list of search based images

**--out_path/-o**: Path of downloaded images to restore

**--jobs/-j**: Use Number of processes, if 0, means using main process only, its useful while want to debug program

**--num_of_images/-n**: Max number of images crawling per base image, 0 represent crawl as much similar images as possible

**--execution_path/-x**: Path of Chrome driver, default is "./chromedriver/chromedriver_linux", you need to change this parameter if not using Linux, or you want to have another chrome driver path

**--proxy_server/-p**: Proxy server for Chrome flag, no proxy using by default 
