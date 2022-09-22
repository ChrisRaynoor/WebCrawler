"""
## File structure
accident
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

from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib
import logging
import os

def set_logger(log_file_path):
    rt_logger = logging.getLogger()
    logFormatter = logging.Formatter("%(asctime)s %(message)s",
                                            "%m-%d %H:%M:%S")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rt_logger.addHandler(consoleHandler)
    
    fileHandler = logging.FileHandler(log_file_path)
    fileHandler.setFormatter(logFormatter)
    rt_logger.addHandler(fileHandler)


def main():
    # open base page
    driver = webdriver.Chrome()
    base_url = "https://www.msa.gov.cn/html/hxaq/sgjx/"
    driver.get(base_url)

    # get to "按事故类型分类"
    tmp_selector = "body > div.container > div.content.clear > div.left_nav > ul > li.left_nav_list.active > ul > li.nav_lv2_list.active > div"
    tmp_elem = driver.find_element(By.CSS_SELECTOR, tmp_selector)
    tmp_elem.click()
    # get accident type list
    accident_type_button_list_selector = "body > div.container > div.content.clear > div.left_nav > ul > li.left_nav_list.active > ul > li.nav_lv2_list.active > ul"
    pass

if __name__ == "__main__":
    main()