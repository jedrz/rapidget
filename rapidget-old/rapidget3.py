#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import urllib
import urllib2
import urlparse
import time
import gzip
from StringIO import StringIO


USER_AGENT = "Mozilla/5.0"

rx_link = re.compile(r'action=(?:")(.*?)(?:") method="post"')
rx_seconds = re.compile(r'var c=(\d*);')
rx_minutes = re.compile(r'Or try again in about (\d*) minutes.')
rx_wait = re.compile(r'''Your IP address \d*.\d*.\d*.\d* is already 
        downloading a file.  Please wait until the download is completed''', 
        re.VERBOSE)

# czy ktoś pobiera pliki?
busy = False

_params = {}
_next_params = {}


def clearline():
    """Czyści linię"""
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


class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):

    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(
            req.get_full_url(), code, msg, headers, fp)
        result.status = code
        return result

"""
def open_url(url, etag=None, lastmodified=None, agent=USER_AGENT):
    request = urllib2.Request(url)
    request.add_header('User-Agent', agent)
    if lastmodified:
        request.add_header('If-Modified-Since', lastmodified)
    if etag:
        request.add_header('If-None-Match', etag)
    #request.add_header('Accept-encoding', 'gzip')
    opener = urllib2.build_opener(DefaultErrorHandler())
    return opener.open(request)
"""


def open_anything(source, etag=None, lastmodified=None, data=None, agent=USER_AGENT):
    """URL, nazwa pliku lub łańcuch znaków --> strumień

    Funkcja ta pozwala tworzyć parsery, które przyjmują jakieś źródło wejścia
    (URL, ścieżkę do pliku lokalnego lub gdzieś w sieci lub dane w postaci łańcucha znaków),
    a następnie zaznajamia się z nim w odpowiedni sposób. Zwracany obiekt będzie
    posiadał wszystkie podstawowe metody czytania wejścia (read, readline, readlines).
    Ponadto korzystamy z .close(), gdy obiekt już nam nie będzie potrzebny.

    Kiedy zostanie podany argument etag, zostanie on wykorzystany jako wartość
    nagłówka żądania URL-a If-None-Match.

    Jeśli argument lastmodified zostanie podany, musi być on formie
    łańcucha znaków określającego czas i datę w GMT.
    Data i czas sformatowana w tym łańcuchu zostanie wykorzystana
    jako wartość nagłówka żądania If-Modified-Since.

    Jeśli argument agent zostanie określony, będzie on wykorzystany
    w nagłówku żądania User-Agent.
    """

    if hasattr(source, "read"):
        return source

    if source == '-':
        return sys.stdin

    if urlparse.urlparse(source)[0] == "http":
        # otwiera URL za pomocą urllib2
        request = urllib2.Request(source, data)
        request.add_header("User-Agent", agent)
        if lastmodified:
            request.add_header("If-Modified-Since", lastmodified)
        if etag:
            request.add_header("If-None-Match", etag)
        request.add_header("Accept-encoding", "gzip")
        opener = urllib2.build_opener(DefaultErrorHandler())
        return opener.open(request)
    
    # próbuje otworzyć za pomocą wbudowanej funkcji open (jeśli source to nazwa pliku)
    try:
        return open(source)
    except (IOError, OSError):
        pass

    # traktuje source jak łańcuch znaków
    return StringIO(str(source))


def fetch(source, etag=None, lastmodified=None, data=None, agent=USER_AGENT):
    """Pobiera dane z URL, pliku, strumienia lub łańcucha znaków"""
    result = {}
    f = open_anything(source, etag, lastmodified, data, agent)
    result["data"] = f.read()
    if hasattr(f, 'headers'):
        # zapisuje ETag, jeśli go wysłał do nas serwer
        result["etag"] = f.headers.get("ETag")
        # zapisuje nagłówek Last-Modified, jeśli został do nas wysłany
        result["lastmodified"] = f.headers.get("Last-Modified")
        if f.headers.get("content-encoding") == "gzip":
            # odkompresowuje otrzymane dane, ponieważ są one zakompresowane jako gzip
            result["data"] = gzip.GzipFile(fileobj=StringIO(result["data"])).read()
    if hasattr(f, "url"):
        result["url"] = f.url
        # zakładam, że serwer wysłał kod statusu 200
        result["status"] = 200
    # jeśli kod statusu był inny niż 200 zmieniam go
    if hasattr(f, "status"):
        result["status"] = f.status
    f.close()
    return result
    

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
    global _params
    if _params:
        params = fetch(url, _params["etag"], _params["lastmodified"])
    else:
        params = fetch(url)
    _params = params
    if not params.has_key("url"):
        print("Podany adres nie jest niepoprawny: {0}".format(url))
        return None
    if params["status"] == 404:
        print("Podana strona nie istnieje: {0}".format(url))
        return None
    try:
        next_url = rx_link.search(params["data"]).groups()[0]
    except AttributeError:
        print("Błędny adres do pliku: {0}".format(url))
        return None
    data = urllib.urlencode({"dl.start": "Free"})
    if _next_params:
        next_params = fetch(next_url, _next_params["etag"], 
                _next_params["lastmodified"], data)
    else:
        next_params = fetch(next_url, data=data)
    _next_params = next_params
    return next_params["data"]

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
    """


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
    file = url.split("/")[-1]
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
