import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
import datetime
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import ElementClickInterceptedException

tm_start = time.time()
dt_now = datetime.datetime.now()
dt_date_str = dt_now.strftime("%Y/%m/%d %H:%M")
print(dt_date_str)

QUERY = ""  # search word
LIMIT_DL_NUM = 350  # limit number of download
SAVE_DIR = "output_scraping/biden"  # output path
FILE_NAME = ""  # file name
TIMEOUT = 60  # timeout for each access
ACCESS_WAIT = 1  # access interval
RETRY_NUM = 3  # the number of retry
DRIVER_PATH = "/usr/lib/chromium-browser/chromedriver"  # path to chromedriver.exe

# laanch Chrome with headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
# options.add_argument('--start-maximized')
options.add_argument("--start-fullscreen")
options.add_argument("--disable-plugins")
options.add_argument("--disable-extensions")
driver = webdriver.Chrome(DRIVER_PATH, options=options)

tm_driver = time.time()
print("WebDriver launched", f"{tm_driver - tm_start:.1f}s")
url = f"https://www.google.com/search?q={QUERY}&tbm=isch"
driver.get(url)
tm_geturl = time.time()
print("get Google image search page", f"{tm_geturl - tm_driver:.1f}s")

tmb_elems = driver.find_elements_by_css_selector("#islmp img")
tmb_alts = [tmb.get_attribute("alt") for tmb in tmb_elems]

count = len(tmb_alts) - tmb_alts.count("")
print(count)

while count < LIMIT_DL_NUM:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)

    tmb_elems = driver.find_elements_by_css_selector("#islmp img")
    tmb_alts = [tmb.get_attribute("alt") for tmb in tmb_elems]

    count = len(tmb_alts) - tmb_alts.count("")
    print(count)

imgframe_elem = driver.find_element_by_id("islsp")

os.makedirs(SAVE_DIR, exist_ok=True)

# make HTTP header
HTTP_HEADERS = {"User-Agent": driver.execute_script("return navigator.userAgent;")}
print(HTTP_HEADERS)

# download data extensions
IMG_EXTS = (".jpg", ".jpeg", ".png", ".gif")


def get_extension(url):
    url_lower = url.lower()
    for img_ext in IMG_EXTS:
        if img_ext in url_lower:
            extension = ".jpg" if img_ext == ".jpeg" else img_ext
            break
    else:
        extension = ""
    return extension


def download_image(url, path, loop):
    result = False
    for i in range(loop):
        try:
            r = requests.get(url, headers=HTTP_HEADERS, stream=True, timeout=10)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
        except requests.exceptions.SSLError:
            print("***** SSL error")
            break
        except requests.exceptions.RequestException as e:
            print(f"***** requests error({e}): {i + 1}/{RETRY_NUM}")
            time.sleep(1)
        else:
            result = True
            break
    return result


tm_thumbnails = time.time()
print("get thumbnail images", f"{tm_thumbnails - tm_geturl:.1f}s")

# download
EXCLUSION_URL = "https://lh3.googleusercontent.com/"  # exception
count = 0
url_list = []

for tmb_elem, tmb_alt in zip(tmb_elems, tmb_alts):

    if tmb_alt == "":
        continue

    print(f"{count}: {tmb_alt}")

    for i in range(RETRY_NUM):
        try:
            tmb_elem.click()
        except ElementClickInterceptedException:
            print(f"***** click error: {i + 1}/{RETRY_NUM}")
            driver.execute_script("arguments[0].scrollIntoView(true);", tmb_elem)
            time.sleep(1)
        else:
            break
    else:
        print("***** canceled")
        continue

    time.sleep(ACCESS_WAIT)

    alt = tmb_alt.replace("'", "\\'")
    try:
        img_elem = imgframe_elem.find_element_by_css_selector(f"img[alt='{alt}']")
    except NoSuchElementException:
        print("***** img element was not found")
        print("***** canceled")
        continue

    tmb_url = tmb_elem.get_attribute("src")

    for i in range(RETRY_NUM):
        url = img_elem.get_attribute("src")
        if EXCLUSION_URL in url:
            print("***** url exceptions")
            url = ""
            break
        elif url == tmb_url:
            print(f"***** url check: {i + 1}/{RETRY_NUM}")
            time.sleep(1)
            url = ""
        else:
            break

    if url == "":
        print("***** canceled")
        continue

    ext = get_extension(url)
    if ext == "":
        print(f"***** canceled since url does not contain extension")
        print(f"{url}")
        continue

    filename = f"{FILE_NAME}{count}{ext}"
    path = SAVE_DIR + "/" + filename
    result = download_image(url, path, RETRY_NUM)
    if result == False:
        print("***** canceled")
        continue
    url_list.append(f"{filename}: {url}")

    count += 1
    if count >= LIMIT_DL_NUM:
        break

tm_end = time.time()
print("download", f"{tm_end - tm_thumbnails:.1f}s")
print("------------------------------------")
total = tm_end - tm_start
total_str = f"total: {total:.1f}s({total/60:.2f}min)"
count_str = f"count: {count}"
print(total_str)
print(count_str)

path = SAVE_DIR + "/" + "_url.txt"
with open(path, "w", encoding="utf-8") as f:
    f.write(dt_date_str + "\n")
    f.write(total_str + "\n")
    f.write(count_str + "\n")
    f.write("\n".join(url_list))

driver.quit()
