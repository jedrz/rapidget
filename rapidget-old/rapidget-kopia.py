#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO
# dodać pasek postępu
# dodać możliwośc wyboru katalogu do którego mają być zapisywane pliki

import sys
import os
import re
import urllib
import urllib2
import urlparse
import time


__author__ = "Łukasz Jędrzejewski"
__version__ = 0.1


USER_AGENT = "Mozilla/5.0"

rx_link = re.compile(r'action=(?:")(.*?)(?:") method="post"')
rx_seconds = re.compile(r'var c=(\d*);')
rx_minutes = re.compile(r'Or try again in about (\d*) minutes.')
rx_wait = re.compile(r'''Your IP address \d*.\d*.\d*.\d* is already 
        downloading a file.  Please wait until the download is completed''', 
        re.VERBOSE)

# czy ktoś pobiera pliki?
busy = False


def clearline():
    """Czyści linię i cofa kursor do początku bieżącej linii"""
    esc = chr(27)
    sys.stdout.write(esc + "[2K" + esc + "[u" + esc + "[s")


def sleep(count):
    """Wyświetla ile jeszcze musimy czekać na pobranie pliku.
    Czyści aktualną linię i w nią wpisuje napis.
    """
    esc = chr(27)
    sys.stdout.write(esc + "[s")
    while count >= 0:
        minutes = count / 60
        seconds = count - minutes * 60
        clearline()
        sys.stdout.write("Oczekuję na plik jeszcze %s minut, %s sekund" % \
                (minutes, seconds))
        sys.stdout.flush()
        count -= 1
        time.sleep(1)
    sys.stdout.write("\n")


def open_url(url, data=None, agent=USER_AGENT):
    """Otwiera url.

    Jeśli adres był niepoprawny funkcja zwraci None.

    Jeśli argument agent zostanie określony, będzie on wykorzystany
    w nagłówku żądania User-Agent.
    """

    if urlparse.urlparse(url)[0] == "http":
        # otwiera URL za pomocą urllib2
        request = urllib2.Request(url, data, {"User-Agent": agent})
        try:
            response = urllib2.urlopen(request)
        except IOError, ex:
            if hasattr(ex, 'reason'):
                print("Serwer jest niedostępny")
            elif hasattr(ex, 'code'):
                print("Strona nie istnieje")
            return None
        else:
            html = response.read()
            response.close()
            return html

    # zwraca None jeśli url nie jest poprawnym adresem
    return None
           

def send_post(url):
    """Wysyła zapytanie dl.start=Free do pierwszej strony,
    aby pobierać jako free user.  Zwraca otrzymaną stronę po wysłaniu
    zapytania.

    Wyświetla komunikaty, gdy:
     - serwer jest niedostępny
     - strona nie istnieje (błąd 404)
     - adres do pliku jest błędny (strona istnieje, ale nie można wydobyć
       adresu do pliku)
    """
    page = open_url(url)
    if page is None:
        return None
    try:
        next_url = rx_link.search(page).groups()[0]
    except AttributeError:
        print("Błędny adres do pliku: {0}".format(url))
        return None
    values = {"dl.start": "Free"}
    data = urllib.urlencode(values)
    next_page = open_url(next_url, data)
    return next_page


def wait(page, url):
    """Czeka odpowiednią ilość sekund dla danej strony.
    Zwraca True jeśli plik można już pobierać, w przeciwnym wypadku zwraca
    False.
    """
    try:
        seconds = int(rx_seconds.search(page).groups()[0])
    except AttributeError:
        try:
            minutes = int(rx_minutes.search(page).groups()[0])
        except AttributeError:
            global busy
            if not busy:
                print("Ktoś pobiera już pliki")
                busy = True
            else:
                print("Czekam dalej")
            sleep(900)
            return False
        else:
            sleep(minutes * 60)
            return True
    else:
        sleep(seconds)
        return True


def download(url):
    """Pobiera plik"""
    while True:
        next_page = send_post(url)
        # nieprawidłowa strona --> przerywam pobieranie
        if next_page is None:
            return
        # przerywam jeśli nikt nie pobiera z naszego adresu ip
        if wait(next_page, url):
            break
    file = url.split("/")[-1]
    file_url = rx_link.search(next_page).groups()[0]
    print("Pobieram plik")
    urllib.urlretrieve(file_url, file)
    print("Plik został pobrany")
    global busy
    busy = False


def main(urls):
    """Próbuje pobrać wszystkie pliki oprócz tych, które nie zawierają
    'rapidshare.com'."""
    print("Do pobrania {0} plików".format(len(urls)))
    for url in urls:
        if not "rapidshare.com" in url:
            print("Zły adres do Rapidshare: {0}".format(url))
        elif url.split("/")[-1] in os.listdir(os.getcwd()):
            print("Plik istnieje")
        else:
            download(url)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        s = "Podaj adresy do plików z Rapidshare oddzielone spacją\n"
        urls = raw_input(s)
        main(urls.split())
    else:
        main(sys.argv[1:])
