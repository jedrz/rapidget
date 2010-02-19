#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO
# dodać możliwośc wyboru katalogu do którego mają być zapisywane pliki
# napisać oddzielny moduł do pobierania plików, np. PythonWget
# dodać kolorki
# przepisać wszystko na klasy

"""Skrypt służy do pobierania plików z rapidshare.com

Pobiera pliki jako Free User. Przechodzi przez wszyskie napotkane
strony, wyciągając informację o tym, ile sekund musimy czekać, dopóki nie
będziemy mogli pobrać pliku. Następnie odczekuje odpowiednią
ilość sekund.

Gdy nasz adres ip pobiera już plik, próbuje wznowić pobieranie po 15
minutach. Wykonuje tą czynność dopóki nie będziemy mogli pobrać pliku.

Gdy url jest nieprawidłowy lub strona nie istnieje lub plik znajduje się
w aktualnym katalogu wyświetli stosowny komunikat, a następnie przejdzie
do pobierania następnego pliku (oczywiście jeśli takowy będzie).
Kiedy wystąpią inne błędy skrypt przerwie działanie. Wtedy możesz
wysłać autorowi raport błędu (adres w zmiennej __author__)

Używanie:
Adresy do plików pobiera z linii poleceń, np.
 rapidget.py link1 link2 link3
Lub ze standardowego wejścia (linki oddzielone spacją).
"""


import sys
import os
import re
import urllib
import urllib2
import urlparse
import time

import progbar


__author__ = "Łukasz Jędrzejewski <lukasz892@gmail.com>"
__version__ = "0.1"


USER_AGENT = "Mozilla/5.0"

# wyrażenia regularne
rx_link = re.compile(r'action=(?:")(.*?)(?:") method="post"')
rx_seconds = re.compile(r'var c=(\d*);')
rx_minutes = re.compile(r'Or try again in about (\d*) minutes.')

# czy ktoś pobiera pliki?
busy = False


def sleep(count):
    """Wyświetla ile jeszcze musimy czekać na pobranie pliku.
    Czyści aktualną linię i w nią wpisuje napis.
    """
    clear = progbar.ClearScreen()
    clear.one()
    while count >= 0:
        minutes = count / 60
        seconds = count - minutes * 60
        clear.two()
        sys.stdout.write("Oczekuję na plik jeszcze %s minut, %s sekund" % \
                (minutes, seconds))
        clear.three()
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
            if hasattr(ex, "reason"):
                print("Serwer jest niedostępny")
            elif hasattr(ex, "code"):
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
    # próbuję wyciągnąć sekundy ze strony, jeśli limit pobierania
    # został przekroczony
    try:
        seconds = int(rx_seconds.search(page).groups()[0])
    except AttributeError:
        # przekroczony limit pobierania, próbuję wyciągnąć minuty
        try:
            minutes = int(rx_minutes.search(page).groups()[0])
        except AttributeError:
            # nie wyciągnąłem minut --> adres ip komputera już pobiera
            # inny plik
            global busy
            if not busy:
                print("Twój adres ip pobiera już pliki")
                busy = True
            else:
                print("Czekam dalej")
            sleep(900)
            return False
        else:
            print("Przekroczyłeś limit pobierania")
            sleep(minutes * 60)
            return False
    else:
        sleep(seconds + 2)
        return True


def download_file(url, filename):
    """Pobiera plik, wyświetlajac aktualny stan pobierania w postaci
    progressbara.
    """
    outfile = open(filename, "wb")
    urlfile = urllib2.urlopen(url)
    filesize = int(urlfile.headers.get("Content-Length"))

    # ile bajtów pobieram pobieram w każdym obiegu pętli
    step = 1024

    progressbar = progbar.ProgressBar(filesize + step, 50)
    clear = progbar.ClearScreen()

    clear.one()
    i = 0
    while True:
        bytes = urlfile.read(step)
        outfile.write(bytes)
        clear.two()
        if bytes == "":
            progressbar.update(filesize + step)
            sys.stdout.write("%s" % (progressbar))
            clear.three()
            break
        i += step
        progressbar.update(i)
        sys.stdout.write("%s" % (progressbar))
        clear.three()

    sys.stdout.write("\n")
    urlfile.close()
    outfile.close()


def download(url):
    """Steruje procesem pobierania pliku"""
    while True:
        next_page = send_post(url)
        # nieprawidłowa strona --> przerywam pobieranie
        if next_page is None:
            return
        # przerywam jeśli nikt nie pobiera z naszego adresu ip
        result = wait(next_page, url)
        if result:
            break
    filename = url.split("/")[-1]
    url = rx_link.search(next_page).groups()[0]
    print("Pobieram plik: {0}".format(filename))
    #urllib.urlretrieve(file_url, file)
    download_file(url, filename)
    print("Plik został pobrany")
    global busy
    busy = False


def main(urls):
    """Próbuje pobrać wszystkie pliki oprócz tych, które nie zawierają
    'rapidshare.com' lub istnieją w aktualnym katalogu."""
    print("Do pobrania {0} plików".format(len(urls)))
    for url in urls:
        filename = url.split("/")[-1]
        if not "rapidshare.com" in url:
            print("Zły adres do Rapidshare: {0}".format(url))
        elif filename in os.listdir(os.getcwd()):
            print("{0} istnieje".format(filename))
        else:
            download(url)
    print("Skończyłem pobieranie wszyskich plików")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        s = "Podaj adresy do plików z Rapidshare oddzielone spacją\n"
        urls = raw_input(s)
        main(urls.split())
        if os.name in ("nt", "ce"):
            raw_input()
    else:
        main(sys.argv[1:])
