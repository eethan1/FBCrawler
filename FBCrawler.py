#! /usr/bin/python3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import requests
import logging
from pprint import pprint,pformat
import atexit
import os.path

class FBPrivateGroupCrawler:
    def __init__(self, email,password,group_url,sortBy='CHRONOLOGICAL',headless=True,crashcb=logging.error,infocb=logging.info,debugcb=logging.debug,loglevel=logging.INFO):
        logging.basicConfig(level=loglevel)
        self.crashcb = crashcb
        self.infocb = infocb
        self.debugcb = debugcb

        self.username = email
        self.password = password
        self.groupURL = group_url
        self.sortBy = sortBy
        self.spanNum = 0

        self.latest = 0
        if os.path.isfile('timestamp.txt'):
            with open('timestamp.txt','r') as f:
                try:
                    self.latest = int(f.read())
                    self.infocb(f'Loading timestamp from file...{self.latest}')
                except:
                    self.latest = 0
                    logging.warn('Failed to load timestamp.txt, set it 0')

        self.targetURL = f'{group_url}?sorting_setting={self.sortBy}'
        self.firefoxOptions = webdriver.FirefoxOptions()
        if headless:
            self.firefoxOptions.set_headless()
        self.browser = webdriver.Firefox(firefox_options=self.firefoxOptions)

        self.browser.get(self.targetURL)
        self.infocb(f'Init FB private group crawler...')
        self.infocb(pformat({"Usernam":self.username,"targetURL":self.targetURL,"Headless":bool(headless)}))
        atexit.register(self._before_exit)

    def login(self):
        self.browser.get('https://www.facebook.com/login')
        try:
            submit = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@name="login"]'))
            )
        except:
            self.crashcb('Failed to Get Login element',exc_info=True)
            self.debugcb('Write latest page to ./latestpage.html')
            with open('./latestpage.html', 'w') as f:
                f.write(self.browser.page_source)
            exit(-1)
        username = self.browser.find_element_by_id('email')
        password = self.browser.find_element_by_id('pass')
        username.send_keys(self.username)
        password.send_keys(self.password)
        submit.click()
        if False:# TODO: check login success
            pass
        self.browser.get(self.targetURL)
        self.infocb(f'Login success')

    def spanMore(self):
        print(self.targetURL, self.browser.current_url)
        assert _find_sub_path(self.browser.current_url) == _find_sub_path(self.targetURL)
        try:
             WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,'//div[contains(@class,"userContent")]/div/span/span/a'))
            )
        except:
            self.crashcb('Failed to locate spanMore element',exc_info=True)
            self.debugcb('Write latest page to ./latestpage.html')
            with open('./latestpage.html', 'w') as f:
                f.write(self.browser.page_source)
            exit(-1)
        get_more = self.browser.find_elements_by_xpath('//div[contains(@class,"userContent")]/div/span/span/a')
        num = len(get_more) - 1
        print(f'Num of get_more: {num}')
        for i in range(num):
            self.spanNum += 1
            try:
                get_more[i].click()
                self.debugcb(f'span element {i}')
            except:
                self.debugcb(f'ignore failed span {i}')
                continue
        self.infocb(f'Span success')

    def processPost(self,cb=print):
        assert _find_sub_path(self.browser.current_url) == _find_sub_path(self.targetURL)
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,'//h5[contains(@class,"_7tae")]//a'))
            )
        except:
            self.crashcb('Failed to locate post element',exc_info=True)
            self.debugcb('Write latest page to ./latestpage.html')
            with open('./latestpage.html', 'w') as f:
                f.write(self.browser.page_source)
            exit(-1)
        names = self.browser.find_elements_by_xpath('//h5[contains(@class,"_7tae")]//a')[self.spanNum-1::-1]
        timestamps = self.browser.find_elements_by_xpath('//abbr[contains(@class,"_5ptz")]')[self.spanNum-1::-1]
        contents = self.browser.find_elements_by_xpath('//div[contains(@class,"_5pbx")]')[self.spanNum-1::-1]

        message=''
        latest = 0
        e = 0
        self.infocb('Success locate post, retrieving...')
        self.infocb(f'{len(names)},{len(timestamps)},{len(contents)}')
        for n,t,c in zip(names,timestamps, contents):
            name = n.get_attribute('title')
            post_time = int(t.get_attribute('data-utime'))
            if post_time > self.latest:
                self.latest = post_time
                e += 1
            else:
                self.debugcb('Oldest one found')
                self.debugcb(name)
                self.debugcb((datetime.fromtimestamp(post_time),datetime.fromtimestamp(latest)))
                continue
            date = datetime.fromtimestamp(post_time)
            content = c.text
            message = f'{name}\n{date}\n{content}\n{self.targetURL}'
            cb(message)
        self.infocb(f'latested: {self.latest}')
    def refresh(self):
        self.infocb(f'Refresh: {self.browser.current_url}')
        failed = True
        for _ in range(3):
            try:
                self.browser.refresh()
                failed = False
                break
            except TimeoutException as e:
                self.infocb(e.msg)
        if failed:
            raise TimeoutException('Try refresh 3 times failed')
                
    
    def _before_exit(self):
        self.infocb(f'Saving latest...{self.latest}')
        with open('timestamp.txt','w') as f:
            f.write(str(self.latest))
    def __del__(self):
        self.debugcb(f'__del__: latest: {self.latest}')
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
