#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import urllib
import urllib2
import time
import re


__version__ "0.2"


class RapidWaiter(threading.Thread):
    USER_AGENT = "Mozilla/5.0"
    rx_link = re.compile(r"action=(?:\")(.*?)(?:\") method=\"post\"")
    rx_seconds = re.compile(r"var c=(\d*);")
    rx_minutes = re.compile(r"Or try again in about (\d*) minutes.")

    def __init__(self, url):
        super(RapidWaiter, self).__init__()
        self.url = url
        self.count = 0
        self.busy = False
        self.limit = False
        self.done = False

    def _open_url(self, data=None):
        request = urllib2.Request(url, data, {"User-Agent": self.USER_AGENT})
        try:
            response = urllib2.urlopen(request)
        except IOError:
            return None
        else:
            html = response.read()
            response.close()
            return html

    def _send_post(self, url):
        page = self._open_url(url)
        if page is None:
            return None
        next_url = rx_link.search(page).group(1)
        # dane które należy przesłać by dostać kolejną stronę
        data = urllib.urlencode({"dl.start": "Free"})
        next_page = open_url(next_url, data)
        return next_page

    def sleep(self, page, url):
        # próbuję wyciągnąć sekundy ze strony, jeśli limit pobierania
        # został przekroczony
        try:
            seconds = int(self.rx_seconds.search(page).group(1))
        except AttributeError:
            # przekroczony limit pobierania, próbuję wyciągnąć minuty
            try:
                minutes = int(self.rx_minutes.search(page).group(1))
            except AttributeError:
                # nie wyciągnąłem minut --> adres ip komputera już pobiera
                # inny plik
                if not self.busy:
                    self.busy = True
                self.count = 180
                time.sleep(180)
            else:
                if not self.limit:
                    self.limit = True
                self.count = minutes * 30
                time.sleep(minutes * 30)
        else:
            self.count = seconds
            time.sleep(seconds)
            self.done = True

    def run(self):
        while not self.done:
            page = self._send_post(self.url)
            if page is None:
                # TODO dopisac
                pass
            self.sleep(page, self.url)

    def wait(self):
        self.start()
    

class RapidDownloader(threading.Thread):
    
    def __init__(self, url):
        super(RapidDownloader, self).__init__()
        self.download_url = url

    def run(self):
        pass

    def download(self):
        self.start()

    def is_downloaded(self):
        pass
