"""
## Steps
### General
对于一个事故详情页面：
    从正文借助关键词判断是否所需事故，标记优先级。高优先级后续分析pdf可参考
    下载pdf以便后续分析

pdf分析：
提取文字和表格文字，通过关键词爬取所需属性。
由于pdf中表述不一定统一，每个属性可以提取为：包含关键词的上下文。这样的上下文可能有多个，均可列出，最后人工提取。
如果发现高度规律，再进行自动提取。
    
### Detailed
Start at "按事故类型分类"
for: each accident type, 
    simulte click to load coresponding page
    while: "active" != "last".total
        get article list
        for: each article in article list
            get href
            jumpto href
            at new page:
            get body text. find keywords by regex. key words: 火灾、燃烧、火、爆炸、泄漏、渗漏 etc.
            get pdf links, download pdf
"""

from random import randint
from time import sleep
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from retry import retry
from retry.api import retry_call
import urllib.request
import logging
import os
import re
import xlwings as xw
import requests
# pdfminer
import pdfminer.high_level

def set_logger(log_file_path, logger):
    logFormatter = logging.Formatter("%(asctime)s %(message)s",
                                            "%m-%d %H:%M:%S")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    
    fileHandler = logging.FileHandler(log_file_path)
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

def get_keyword_regex(word_list):
    res = list()
    if not word_list:
        raise ValueError
    for word in word_list:
        if not word:
            continue
        res.append(f"{word}|")

    return "".join(res)[:-1]

# keword settings
word_list = [
    "起火",
    "火灾",
    "燃烧",
    "闪燃",
    "着火",
    "自燃",
    "爆燃",
    "爆炸",
    "溢油",
    "渗漏",
    "泄漏",
    "外漏",
    "外溢",
    "外泄",
]

# path settings
force_xl = True
save_root = "data"
pdf_dir_name = "pdf"
text_dir_name = "text"
xlsx_path = "data/result_all.xlsx"

# settings
context_expand = 7
active_slt = "#articleList > div > a.active"
next_slt = "#articleList > div > a.next"
last_slt = "#articleList > div > a.last"
# =====================================================================
# init mid var
pdf_dir = os.path.join(save_root, pdf_dir_name)
print(pdf_dir)
text_dir = os.path.join(save_root, text_dir_name)
print(text_dir)
# pdf_dir = "./data/dpf/"
# text_dir = "./data/text/"
keyword_regex = get_keyword_regex(word_list)
keyword_regex
logger = logging.getLogger("mainlogger")
logger.setLevel(logging.DEBUG)
set_logger("webCrawler.log", logger)

# init dir
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
if not os.path.exists(text_dir):
    os.makedirs(text_dir)

# init .xlsx
# open base page
option = webdriver.ChromeOptions()
# option.add_argument('headless')
# option.add_argument('disable-gpu')
# driver = webdriver.Chrome(options=option)
driver = webdriver.Chrome()
base_url = "https://www.msa.gov.cn/html/hxaq/sgjx/"
driver.get(base_url)

# get to "按事故类型分类"
# tmp_selector = "body > div.container > div.content.clear > div.left_nav > ul > li.left_nav_list.active > ul > li.nav_lv2_list.active > div"
# tmp_elem = driver.find_element(By.CSS_SELECTOR, tmp_selector)
# tmp_elem.click()
# get accident type list
accident_type_buttons_selector = "body > div.container > div.content.clear > div.left_nav > ul > li.left_nav_list.active > ul > li.nav_lv2_list.active > ul > li" 
accident_type_button_list = driver.find_elements(By.CSS_SELECTOR, accident_type_buttons_selector)
# for each type, jump to page
# ========================================================
# get to "火灾爆炸事故" for test
# driver.find_element(By.CSS_SELECTOR, "#hzbzsg").click()
# if True:
# ========================================================
# NOTE tmporarily siable following 6 lines for testing
print("traversing accident type")
# continue from last
resume = True
resume_accident_type_slt = "#cjsg" # css_slt
resume_article_list_page = '5' # str
accident_button_slt_list = [
    "#pzsg",
    "#gqsg",
    "#cjsg",
    "#cpsg",
    "#hzbzsg",
    "#fzsg",
    "#zcsg",
    "#qtsg",
]
if resume:
    accident_type_start_cnt = accident_button_slt_list.index(resume_accident_type_slt)
else:
    accident_type_start_cnt = 0

for i in range(accident_type_start_cnt, len(accident_type_button_list)):
    accident_type_button_selector = accident_button_slt_list[i]
    if resume:
        logger.warning(f"resuming to: {accident_button_slt_list[i]}")
    @retry(tries = 5, delay=10)
    def tmpf():
        driver.find_element(By.CSS_SELECTOR, accident_type_button_selector).click()
    tmpf()
    # NOTE bellow: for one accident type, if program fails, try to restart by giving it a different base page
    # traverse by "next"
    # resume, jump to certain article list page
    # @retry(tries = 5, delay=10)
    # def is_resume_page():
    #     if not resume:
    #         return True
    #     active = driver.find_element(By.CSS_SELECTOR, active_slt).get_attribute("innerHTML")
    #     if resume_article_list_page == active: # if at page
    #         logger.warning(f"Reach resume page{resume_article_list_page}")
    #         return True
    #     # if not
    #     logger.info(f"resuming, jumpto resume: {active}/{resume_article_list_page}")
    #     driver.find_element(By.CSS_SELECTOR, next_slt).click()
    #     return False
    # while True:
    #     sleep(5)
    #     if is_resume_page():
    #         break
    @retry(tries=5, delay=10)
    def to_resume():
        if not resume:
            return
        action = webdriver.ActionChains(driver)
        driver.find_element(By.CSS_SELECTOR, "#pagInput").click()
        action.send_keys(resume_article_list_page)
        action.perform()
        driver.find_element(By.CSS_SELECTOR, "#articleList > div > input.btn.btn-fault").click()
        logger.warning(f"resuming to page {resume_article_list_page}")
    to_resume()
    flag_resume_first = True
    # pirnt resume info line to xl
    if resume:
        with xw.App(visible=False,add_book=False) as app:
            if os.path.exists(xlsx_path):
                wb = app.books.open(xlsx_path)
                sht = wb.sheets[0]
            else:
                wb=app.books.add()
                #创建一个sheet工作表
                sht=wb.sheets['sheet1']
                xl_header = ["标题","id","url","本地链接","","","关键词上下文"]
                sht.range('A1').value = xl_header
                wb.save(xlsx_path)
            resume = False # when all resume work done
            used_range = sht.used_range
            cur_row = used_range.last_cell.row + 1
            sht.range(f"G{cur_row}").value = "Breakpoint Resume, mind possible duplicate entries"
            wb.save(xlsx_path)
    while True:
        # do
        with xw.App(visible=False,add_book=False) as app:
            if os.path.exists(xlsx_path):
                wb = app.books.open(xlsx_path)
                sht = wb.sheets[0]
            else:
                wb=app.books.add()
                #创建一个sheet工作表
                sht=wb.sheets['sheet1']
                xl_header = ["标题","id","url","本地链接","","","关键词上下文"]
                sht.range('A1').value = xl_header
                wb.save(xlsx_path)
            tmp_slt = "#articleList > ul > li"
            num_articles_on_page = len(retry_call(driver.find_elements,[By.CSS_SELECTOR, tmp_slt], tries = 5, delay=10))
            for j in range(num_articles_on_page):
                try:
                    # =================================================
                    # on one accident
                    tmp_slt = f"#articleList > ul > li:nth-child({j+1}) > a"
                    # to new page
                    @retry(tries = 5, delay=10)
                    def tmpf():
                        driver.find_element(By.CSS_SELECTOR, tmp_slt).click()
                        new_handle = driver.window_handles[-1]
                        driver.switch_to.window(new_handle)
                    tmpf()
                    # sleep for load
                    sleep(5)
                    # get title
                    title_slt = "#title"
                    @retry(tries = 5, delay=10)
                    def tmpf():
                        return driver.find_element(By.CSS_SELECTOR, title_slt).get_attribute("innerHTML")
                    title = tmpf()
                    # get body. Only css_selecotr #ch_p can make sure that element be located
                    body_slt = "#ch_p"
                    @retry(tries = 5, delay=10)
                    def tmpf():
                        return driver.find_element(By.CSS_SELECTOR, body_slt).get_attribute("innerHTML")
                    body = tmpf()
                    page_url = driver.current_url
                    id = re.search(r"[^/]+(?!.*/)", page_url).group()[:-5] # url's part as id
                    logger.info(f"working on accident id: {id}")
                    content = body
                    # get pdf link from body
                    link_list = list()
                    while True:
                        result = re.search(r'(href=")(.*?pdf)', content)
                        if result is None:
                            break
                        link = result.group(2)
                        logger.info(f"get pdf link: {link}")
                        link_list.append(link)
                        content = content[result.end():]
                    # xl ----
                    # get used range
                    used_range = sht.used_range
                    cur_row = used_range.last_cell.row + 1
                    # define xl data
                    xl_data_row = [title, id, page_url]
                    # write to pdf
                    sht.range(f"A{cur_row}").value = xl_data_row

                    # download. might get multiple pdf
                    # NOTE need to create hyperlink
                    save_path_list = list() # used to convert to text
                    for cnt, link in enumerate(link_list):
                        # get pdf name
                        pdf_filename = re.search(r"[^/]+(?!.*/)", link).group()
                        if pdf_filename is None:
                            continue
                        save_path = os.path.join(pdf_dir, pdf_filename)
                        save_path_list.append(save_path)
                        path_in_xl = os.path.join(pdf_dir_name, pdf_filename)
                        # download
                        logger.info(f"downloading from {link} to {save_path}")
                        urllib.request.urlretrieve(link, save_path)
                        # add relative path to xl 
                        sht.range(f"{chr(ord('D')+ cnt)}{cur_row}").add_hyperlink(path_in_xl)
                    # get keyword context
                    context_list = list()
                    # create .txt to save result
                    with open(os.path.join(text_dir, f"{id}.txt"), "ab") as text_fp:
                        # match keyword in body and save
                        text_fp.write(body.encode("utf-8"))
                        all_matches = re.finditer(keyword_regex, body)
                        text_length = len(body)
                        for match_elem in all_matches:
                            xl_data_row.append(body[max(match_elem.start()-context_expand, 0):min(match_elem.end()+context_expand, text_length)])
                        # match and save in pdf
                        got_text = False
                        for tmp_path in save_path_list:
                            logger.info(f"processing file: {tmp_path}")
                            if not tmp_path.endswith("pdf"):
                                logger.info("process failed")
                                continue
                            text = pdfminer.high_level.extract_text(tmp_path)
                            if text:
                                got_text = True
                            # add to .txt
                            text_fp.write(text.encode("utf-8"))
                            # match keywords
                            all_matches = re.finditer(keyword_regex, text)
                            # add to xl
                            text_length = len(text)
                            for match_elem in all_matches:
                                context_list.append(text[max(match_elem.start()-context_expand, 0):min(match_elem.end()+context_expand, text_length)])
                    # if no text from pdf
                    if not got_text:
                        sht.range(f"G{cur_row}").value = "无法解析的报告"
                    # save context to xl
                    sht.range(f"H{cur_row}").value = context_list
                    wb.save(xlsx_path)
                    # close tag
                    driver.close() 
                    # end ---
                    # NOTE of file structure:
                    # data
                    # -.xlsx
                    # -pdf/
                    # -text/
                    # =================================================
                except Exception as e:
                    if page_url is not None:
                        logger.warning(f"Critical error near processing url: {page_url}, accident_type: {accident_button_slt_list[i]}")
                    logger.warning(traceback.format_exc())
                    # if 403 forbidden, sleep longer
                    while True:
                        res = requests.get(base_url)
                        if res.status_code == 200:
                            logger.warning(f"Access granted. Resume")
                            break
                        if res.status_code == 403:
                            logger.warning(f"403!!!!!!!!!!!!!. Sleeping")
                            sleep(600)
                        else:
                            sleep(10)
                finally:
                    new_handle = driver.window_handles[0]
                    driver.switch_to.window(new_handle)
                    sleep(randint(3, 7))  
        # while, by next
        @retry(tries = 5, delay=10)
        def is_last():
            total = driver.find_element(By.CSS_SELECTOR, last_slt).get_attribute("total")
            active = driver.find_element(By.CSS_SELECTOR, active_slt).get_attribute("innerHTML")
            if total == active: # if last
                return True
            # if not
            logger.info(f"page done: {active}/{total}")
            driver.find_element(By.CSS_SELECTOR, next_slt).click()
            return False
        if is_last():
            break
            
    
# save
# 该save会强制覆盖
driver.quit()