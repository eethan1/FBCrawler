#! /usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import requests

class FBPrivateGroupCrawler:
    def __init__(self, email,password,group_url,sortBy='CHRONOLOGICAL',headless=True):
        self.firefoxOptions = webdriver.FirefoxOptions()
        if headless:
            self.firefoxOptions.set_headless()
        self.browser = webdriver.Firefox(firefox_options=self.firefoxOptions)
        self.username = email
        self.password = password
        self.groupURL = group_url
        self.sortBy = sortBy
        self.targetURL = f'{group_url}?sorting_setting={self.sortBy}'
        self.spanNum = 0
        self.browser.get(self.targetURL)
        self.latest = 0
    def login(self):
        self.browser.get('https://www.facebook.com/login')
        try:
            submit = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@name="login"]'))
            )
        except:
            print('Failed to Get Login element')
            exit(-1)
        username = self.browser.find_element_by_id('email')
        password = self.browser.find_element_by_id('pass')
        username.send_keys(self.username)
        password.send_keys(self.password)
        submit.click()
        if False:# TODO: check login success
            pass
        self.browser.get(self.targetURL)
    def spanMore(self):
        print(self.targetURL, self.browser.current_url)
        assert _find_sub_path(self.browser.current_url) == _find_sub_path(self.targetURL)
        try:
             WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,'//div[contains(@class,"userContent")]/div/span/span/a'))
            )
        except:
            print('failed')
            exit(-1)
        get_more = self.browser.find_elements_by_xpath('//div[contains(@class,"userContent")]/div/span/span/a')
        num = len(get_more) - 1
        print(f'Num of get_more: {num}')
        for i in range(num):
            self.spanNum += 1
            try:
                get_more[i].click()
            except:
                continue
        
    def processPost(self,cb=print):
        assert _find_sub_path(self.browser.current_url) == _find_sub_path(self.targetURL)
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,'//h5[contains(@class,"_7tae")]//a'))
            )
        except:
            print('Name not rendered')
            self.browser.quit()
            exit(-1)
        names = self.browser.find_elements_by_xpath('//h5[contains(@class,"_7tae")]//a')[self.spanNum-1::-1]
        timestamps = self.browser.find_elements_by_xpath('//abbr[contains(@class,"_5ptz")]')[self.spanNum-1::-1]
        contents = self.browser.find_elements_by_xpath('//div[contains(@class,"_5pbx")]')[self.spanNum-1::-1]

        message=''
        latest = 0
        e = 0
        print(len(names),len(timestamps),len(contents))
        for n,t,c in zip(names,timestamps, contents):
            name = n.get_attribute('title')
            post_time = int(t.get_attribute('data-utime'))
            if post_time > self.latest:
                self.latest = post_time
                e += 1
            else:
                print(datetime.fromtimestamp(post_time),datetime.fromtimestamp(latest))
                continue
            date = datetime.fromtimestamp(post_time)
            content = c.text
            message = f'{name}\n{date}\n{content}\n{self.targetURL}'
            cb(message)
    def refresh(self):
        print(f'Refresh: {self.browser.current_url}')
        self.browser.refresh()
    def __del__(self):
        self.browser.quit()
        
def _find_sub_path(url):
        p = url.find('/',0)
        if p == -1:
            return ''
        p = url.find('/',p)
        if p == -1:
            return ''
        p = url.find('/',p)
        if p == -1:
            return ''
        else:
            return url[p:]
