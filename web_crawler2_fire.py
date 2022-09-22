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
import tools
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
    "油船",
    "油轮",
    "化学品船",
    "集装箱",
    "液化气船"
]

# path settings
force_xl = True
save_root = "data2"
pdf_dir_name = "pdf"
text_dir_name = "text"
xlsx_path = "data2/result_all.xlsx"

# settings
context_expand = 8
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
base_url_fmt = "http://www.safehoo.com/Case/Case/Blaze/List_{}.shtml"
max_page_index = 52
# max_article_one_page = 30
# =====================================================================
# init mid var
pdf_dir = os.path.join(save_root, pdf_dir_name)
print(pdf_dir)
text_dir = os.path.join(save_root, text_dir_name)
print(text_dir)
keyword_regex = get_keyword_regex(word_list)
logger = logging.getLogger("mainlogger")
logger.setLevel(logging.DEBUG)
set_logger("webCrawler2.log", logger)

# init dir
if not os.path.exists(save_root):
    os.makedirs(save_root)
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)
if not os.path.exists(text_dir):
    os.makedirs(text_dir)

# # init .xlsx
# with xw.App(visible=False,add_book=False) as app:
#     if os.path.exists(xlsx_path):
#         wb = app.books.open(xlsx_path)
#         sht = wb.sheets[0]
#     else:
#         wb=app.books.add()
#         #创建一个sheet工作表
#         sht=wb.sheets['sheet1']
#         xl_header = ["标题","id","url","本地链接","","","关键词上下文"]
#         sht.range('A1').value = xl_header
#         wb.save(xlsx_path)

# open base page
option = webdriver.ChromeOptions()
# option.add_argument('--headless')
# option.add_argument('--disable-gpu')
option.add_argument('--user-agent=%s' % user_agent)
driver = webdriver.Chrome(options=option)


# continue from last
resume = True
resume_page_cnt = 25 # start from 1, reverse

strat_cnt = resume_page_cnt if resume else 1

# ===================
# tmp settings
art_slt = "#pagecontent"
doc_slt = "body > div.c970 > div.con_wen > div:nth-child(3) > div.con_pl > textarea"
type_matcher = tools.WordMatcher("文章|文档",0)
content_matcher = tools.WordMatcher(keyword_regex)
for i in range(strat_cnt, max_page_index+1):
    logger.info(f"processing page: {i}")
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

        try:
            @retry(tries = 5, delay=10)
            def tmpf():
                driver.get(base_url_fmt.format(i))
            tmpf()
            # get article cnt
            @retry(tries=5, delay=10)
            def tmpf2():
                # all article elements
                return len(driver.find_elements(By.CSS_SELECTOR, "body > div.c970 > div.lm2_k650 > div.childclass_content > li"))
            article_one_page = tmpf2()
        except Exception as e:
            logger.warning(f"critical error near processing: {base_url_fmt.format(i)}")
            continue

        for article_idx in range(article_one_page):
            # for one article
            # get used range
            used_range = sht.used_range
            cur_row = used_range.last_cell.row + 1
            try:
                @retry(tries = 5, delay=10)
                def tmpf():
                    # get type 文章art or 文档doc
                    text = driver.find_element(By.CSS_SELECTOR, f"body > div.c970 > div.lm2_k650 > div.childclass_content > li:nth-child({article_idx+1})").get_attribute("innerHTML")
                    type_str = type_matcher.get_n_context(text)[0]
                    title = driver.find_element(By.CSS_SELECTOR, f"body > div.c970 > div.lm2_k650 > div.childclass_content > li:nth-child({article_idx+1}) > a").get_attribute("title")
                    # click
                    driver.find_element(By.CSS_SELECTOR, f"body > div.c970 > div.lm2_k650 > div.childclass_content > li:nth-child({article_idx+1}) > a").click()
                    new_handle = driver.window_handles[-1]
                    driver.switch_to.window(new_handle)
                    return type_str, title
                type_str, title = tmpf()
                # logger.info(f"type_str {type_str}")
                sleep(randint(7,10))
                # common process
                @retry(tries=5, delay=10)
                def tmpf2():
                    page_url = driver.current_url
                    return page_url
                page_url = tmpf2()
                logger.info(f"processing page: {page_url}")
                # different process by type
                @retry(tries=5, delay=10)
                def tmpf3():
                    if type_str == "文章":
                        text = driver.find_element(By.CSS_SELECTOR, art_slt).get_attribute("innerHTML")
                    elif type_str == "文档":
                        text = driver.find_element(By.CSS_SELECTOR, doc_slt).get_attribute("innerHTML")
                    else:
                        logger.warning("无法解析的网页")
                        text = None
                    return text
                text = tmpf3()
                # common text match
                # if no match, add nothing to xl
                if text is not None:
                    res = content_matcher.get_all_context(text)
                    if res is not None and len(res)>0:
                        content_list = [title, "", page_url]
                        sht.range(f"A{cur_row}").value = content_list
                        sht.range(f"H{cur_row}").value = res
                        wb.save(xlsx_path)
                driver.close()
            except Exception as e:
                if page_url is not None:
                        logger.warning(f"Critical error near processing url: {page_url}, page_cnt(directly for resume): {i}, article_idx(not for resume): {article_idx}")
                logger.warning(traceback.format_exc())
                if page_url is None:
                    page_url = base_url_fmt.format(1)
                while not tools.is_ok_status(page_url):
                    sleep(10)
            finally:
                new_handle = driver.window_handles[0]
                driver.switch_to.window(new_handle)
                sleep(randint(3, 7))
        ## close
        wb.close()

            
    
# save
# 该save会强制覆盖

#如果资源不关闭，任然还是可以对工作簿进行操作
#后写入的内容需要重新保存
# sht.range('A6').value='我给了单元格A1一个值5'
#wb.save()  #后面的保存不需要传入文件

#关闭Excel程序,
# 如果不关闭资源，重复执行的话，则会生成一个默认的工作簿
driver.quit()