import time
import os
import sys
from textwrap import dedent
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

START_PAGE = 4558
LIMIT = 20000
WIPO_URL = "https://www3.wipo.int/madrid/monitor/en/"
DOWNLOAD_DIR = "downloads"
PROXY = "54.166.160.180:80"
RETRY_COUNT = 3


cur_page_index = 1

def wait_until_images_loaded(driver, timeout=60):
    """Waits for all images & background images to load."""
    driver.set_script_timeout(timeout)
    driver.execute_async_script(dedent('''
        // Function to extract URL from CSS 'url()' function
        function extractCSSURL(text) {
            var url_str = text.replace(/.*url\((.*)\).*/, '$1');
            // If the URL is enclosed with double quotes
            if (url_str[0] === '"') {
                return JSON.parse(url_str);
            }
            // If the URL is enclosed with single quotes
            if (url_str[0] === "'") {
                return JSON.parse(
                    url_str
                        .replace(/'/g, '__DOUBLE__QUOTE__HERE__')
                        .replace(/"/g, "'")
                        .replace(/__DOUBLE__QUOTE__HERE__/g, '"')
                );
            }
            // Return the URL as is
            return url_str;
        }
        // Function to create a promise that resolves when the image is loaded
        function imageResolved(url) {
            return new Promise(function (resolve) {
                var img = new Image();
                img.onload = function () {
                    resolve(url);
                };
                img.src = url;
                // If the image is already loaded, resolve the promise immediately
                if (img.complete) {
                    resolve(url);
                }
            });
        }
        // The last argument is expected to be a callback function
        var callback = arguments[arguments.length - 1];
        
        Promise.all([
            // Get all img tags, create a promise for each one
            ...Array.from([...document.querySelectorAll('img[src]')].filter((img) => img.src.includes("/jsp/data.jsp")), img => imageResolved(img.src)),
        ])
        .then(function () { 
            console.log('image load done')
            // Call the callback function when all promises are resolved
            callback(arguments); 
        });
        return undefined;
    '''))

def scrap_wipo(start_page, limit):
    global cur_page_index
    # load first page
    dir_path = os.path.dirname(os.path.realpath(__file__))
    options = Options()
    options.proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        "socksVersion": 5,
        'httpProxy': PROXY,
        'sslProxy': PROXY,
        "socksProxy": PROXY,
        'noProxy':''})
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", f"{dir_path}\\{DOWNLOAD_DIR}")
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")
    driver = webdriver.Firefox(options=options)
    driver.get(WIPO_URL)
    wait = WebDriverWait(driver, 30)
    search_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@id='AUTO_input']")))
    search_input.send_keys(Keys.ENTER)

    # set row count 100
    select_rowcount = Select(wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@id='rowCount1']"))))
    select_rowcount.select_by_value('100')

    # set Reg Date decending
    th_regdate = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[@id='gridForsearch_pane_RD']")))
    th_regdate.click()

    # wait for table is started to load
    wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@id='rowCount1']")))

    # set Reg Date ascending
    th_regdate = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[@id='gridForsearch_pane_RD']")))
    th_regdate.click()

    # wait for table is started to load
    wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@id='rowCount1']")))

    # get page count
    div_pagecount = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='pageCount']")))
    total_pagecount = int(div_pagecount.get_attribute('innerHTML').replace('/','').replace(',', '').replace(' ', ''))
    print(total_pagecount)


    page_num = start_page
    while page_num < start_page + limit and page_num <= total_pagecount:
        cur_page_index = page_num
        # set page number
        page_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@id='skipValue1']")))
        page_input.clear()
        page_input.send_keys(f"{page_num}" + Keys.ENTER)

        # wait for table is started to load
        wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@id='rowCount1']")))

        # wait all images are loaded
        wait_until_images_loaded(driver)

        # download data to html
        span_download = wait.until(EC.presence_of_element_located((By.XPATH, "//span[text()='download']")))
        a_download = span_download.find_element(By.XPATH, '..')
        a_download.click()
        a_download_html = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@id='download_link_html']")))
        a_download_html.click()
        print(page_num, 'done')
        page_num += 1
    driver.close()

if __name__ == '__main__':
    cur_page_index = START_PAGE

    repeat_index = 0
    while True:


        try:
            old_page_index = cur_page_index
            scrap_wipo(cur_page_index, LIMIT)
        except Exception as e:
            print(f'{cur_page_index} except{str(e)}')

        if old_page_index == cur_page_index:
            repeat_index += 1
        else:
            repeat_index = 0
        if repeat_index > RETRY_COUNT:
            break
    print('all done')