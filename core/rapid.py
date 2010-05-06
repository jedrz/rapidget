#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import urllib
import urllib2
import time
import re


class RapidBase(threading.Thread):
    """Bazowa klasa z możliwością zatrzymania wątku"""

    def __init__(self):
        super(RapidBase, self).__init__()
        self.end_thread = False

    def stop(self):
        self.end_thread = True
    

class RapidWaiter(RapidBase):
    """Klasa do oczekiwania na pobieranie"""

    USER_AGENT = "Mozilla/5.0"
    _rx_link = re.compile(r"action=(?:\")(.*?)(?:\") method=\"post\"")
    _rx_seconds = re.compile(r"var c=(\d*);")
    _rx_minutes = re.compile(r"Or try again in about (\d*) minutes.")
    _rx_overloaded = re.compile(r"Please try again in (\d*) minutes? or become")

    def __init__(self, url):
        super(RapidWaiter, self).__init__()
        self.url = url
        self.download_url = ""
        # ile sekund należy poczekać
        self.count = 0
        # adres ip zajęty
        self.busy = False
        # przekroczony limit pobierania
        self.limit = False
        # rapidshare przeciążony
        self.overloaded = False
        # można pobierać
        self.done = False

    def _open_url(self, url, data=None):
        """Otwiera url i zwraca źródło"""
        request = urllib2.Request(url, data, {"User-Agent": self.USER_AGENT})
        response = urllib2.urlopen(request)
        html = response.read()
        response.close()
        return html

    def send_post(self):
        """Wysyła zapytanie, zwraca kolejną stronę"""
        page = self._open_url(self.url)
        next_url = self._rx_link.search(page).group(1)
        # dane które należy przesłać by dostać kolejną stronę
        data = urllib.urlencode({"dl.start": "Free"})
        next_page = self._open_url(next_url, data)
        return next_page

    def _sleep(self):
        """Oczekuje pewną liczbę sekund lub przerywa po zatrzymaniu wątku"""
        while not self.end_thread and self.count > 0:
            time.sleep(1)
            self.count -= 1

    def sleep(self, page):
        """Oczekuje odpowiednią ilość sekund w zależności od uzyskanej
        strony"""
        # próbuję wyciągnąć sekundy ze strony
        try:
            seconds = int(self._rx_seconds.search(page).group(1))
        except AttributeError:
            # przekroczony limit pobierania, próbuję wyciągnąć minuty
            try:
                minutes = int(self._rx_minutes.search(page).group(1))
            except AttributeError:
                # sprawdzam czy rapidshare przeciążony
                try:
                    minutes = int(self._rx_overloaded.search(page).group(1))
                except AttributeError:
                    # adres ip komputera już pobiera inny plik
                    self.busy = True
                    self.count = 180
                    self._sleep()
                    self.busy = False
                else:
                    self.overloaded = True
                    self.count = minutes * 60
                    self._sleep()
                    self.overloaded = False
            else:
                self.limit = True
                self.count = minutes * 30
                self._sleep()
                self.limit = False
        else:
            self.count = seconds
            self._sleep()
            self.done = True

    def run(self):
        """Oczekuje do momentu uzyskania adresu do pliku"""
        page = ""
        while not (self.done or self.end_thread):
            page = self.send_post()
            self.sleep(page)
        try:
            self.download_url = self._rx_link.search(page).group(1)
        except AttributeError:
            pass

    def wait(self):
        """Metoda do uruchomienia oczekiwania"""
        self.start()
    

class RapidDownloader(RapidBase):
    """Klasa służy do pobierania dowolnych plików,
    korzystając z wątków"""

    STEP = 1024 * 64 # ile bajtów pobieram w każdym obiegu pętli
    
    def __init__(self, url, path):
        super(RapidDownloader, self).__init__()
        # bezpośredni adres do pobrania pliku
        self.download_url = url
        # ścieżka do zapisu pliku (z nazwą pliku)
        self.path = path
        # rozmiar pliku
        self.filesize = 0
        # ile bajtów pobrano
        self.current_pos = 0

    def run(self):
        """Pobiera plik z wykorzystaniem wątków"""
        outfile = open(self.path, "wb")
        urlfile = urllib2.urlopen(self.download_url)
        self.filesize = int(urlfile.headers.get("Content-Length"))
        while not self.end_thread:
            bytes = urlfile.read(self.STEP)
            outfile.write(bytes)
            if bytes == "":
                # plik pobrany
                break
            self.current_pos += len(bytes)
        urlfile.close()
        outfile.close()

    def download(self):
        """Metoda do uruchomienia pobierania"""
        self.start()

    def is_downloaded(self):
        """Czy plik został pobrany"""
        return self.current_pos == self.filesize
