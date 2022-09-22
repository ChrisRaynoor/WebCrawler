#coding=utf-8
from selenium import webdriver

option = webdriver.ChromeOptions()
option.add_argument('headless')
driver = webdriver.Chrome(options=option)
driver.get('https://cloud.tencent.com/developer/article/1835029')
print(driver.title)
#最后关闭一下
driver.quit()