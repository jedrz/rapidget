#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import urllib
import urllib2
import time


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
    """Czyści linię"""
    esc = chr(27)
    sys.stdout.write(esc + "[2K" + esc + "[u" + esc + "[s")


def sleep(count):
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
    headers = {"User-Agent": USER_AGENT}
    request = urllib2.Request(url, headers=headers)
    try:
        page = urllib2.urlopen(request)
        next_url = rx_link.search(page.read()).groups()[0]
    except AttributeError:
        print("Błędny adres do pliku: {0}".format(url))
        page.close()
        return None
    except IOError, ex:
        if hasattr(ex, 'reason'):
            print("Serwer jest niedostępny")
        elif hasattr(ex, 'code'):
            print("Strona nie istnieje")
        return None
    data = urllib.urlencode({"dl.start": "Free"})
    request = urllib2.Request(next_url, data, headers)
    next_page = urllib2.urlopen(request)
    html = next_page.read()
    next_page.close()
    return html


def wait(page, url):
    """Czeka odpowiednią ilość sekund dla danej strony"""
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
            download(url)
        else:
            sleep(minutes * 60)
    else:
        sleep(seconds)


def download(url):
    """Pobiera plik"""
    file = os.path.split(url)[1]
    if file in os.listdir(os.getcwd()):
        print("Plik istnieje")
        return
    next_page = send_post(url)
    if next_page is None:
        return
    wait(next_page, url)
    file_url = rx_link.search(next_page).groups()[0]
    print("Pobieram plik")
    urllib.urlretrieve(file_url, file)
    print("Plik został pobrany")
    global busy
    busy = False


def main(urls):
    """Próbuje pobrać wszystkie pliku oprócz tych, które nie zawierają
    'rapidshare.com'."""
    print("Do pobrania {0} plików".format(len(urls)))
    for url in urls:
        if not "rapidshare.com" in url:
            print("Zły adres do Rapidshare: {0}".format(url))
        else:
            download(url)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Usage: {0} <list of urls>".format(sys.argv[0]))
        sys.exit(1)
    main(sys.argv[1:])
