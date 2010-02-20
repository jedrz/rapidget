#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TODO
# dodać kolorki
# przepisać co trzeba na klasy

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
from optparse import OptionParser

from progbar import ClearScreen
from download import download_file


__author__ = "Łukasz Jędrzejewski <lukasz892@gmail.com>"
__version__ = "0.1.6"


USER_AGENT = "Mozilla/5.0"

# wyrażenia regularne
rx_link = re.compile(r'action=(?:")(.*?)(?:") method="post"')
rx_seconds = re.compile(r'var c=(\d*);')
rx_minutes = re.compile(r'Or try again in about (\d*) minutes.')


def sleep(count, delete=False):
    """Wyświetla ile jeszcze musimy czekać na pobranie pliku.
    Czyści aktualną linię i w nią wpisuje napis.
    """
    clear = ClearScreen()
    clear.one()
    while count >= 0:
        minutes = count / 60
        seconds = count - minutes * 60
        clear.two()
        sys.stdout.write("Oczekuję na plik jeszcze %s minut, %s sekund" %
                (minutes, seconds))
        clear.three()
        count -= 1
        time.sleep(1)
    # wyczyść aktualną linię
    if delete:
        clear.two()
    else:
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
        except IOError as ex:
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


def wait(page, url, busy, limit):
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
            if not busy:
                print("Twój adres ip pobiera już pliki")
                busy = True
            #sleep(900)
            #sleep(90, True)
            sleep(180, True)
            return (False, busy, limit)
        else:
            if not limit:
                print("Przekroczyłeś limit pobierania")
                limit = True
            #sleep(minutes * 60)
            sleep(minutes * 30, True)
            return (False, busy, limit)
    else:
        sleep(seconds)
        return (True, busy, limit)


def download(url, path, filename=""):
    """Steruje procesem pobierania pliku"""
    # ktoś pobiera pliki, informacja o zajętym ip wyświetlona
    busy = limit = False
    while True:
        next_page = send_post(url)
        # nieprawidłowa strona --> przerywam pobieranie
        if next_page is None:
            return
        # przerywam jeśli nikt nie pobiera z naszego adresu ip
        (result, busy, limit) = wait(next_page, url, busy, limit)
        if result:
            break
    if not filename:
        filename = os.path.split(url)[1]
    print("Pobieram plik: {0}".format(filename))
    url = rx_link.search(next_page).groups()[0]
    #urllib.urlretrieve(file_url, file)
    download_file(url, os.path.join(path, filename))
    print("Plik został pobrany")


def main(urls=[]):
    """Próbuje pobrać wszystkie pliki oprócz tych, które nie zawierają
    'rapidshare.com' lub istnieją w aktualnym katalogu.

    Tworzy obiekt klasy OptionParser i dodaje opcje:
     - wyboru katalogu do zapisu plików
     - wyboru pliku z listą linków
    """
    parser = OptionParser(usage="Usage: %prog [options] [links]")
    parser.add_option("-p", "--path", help="Gdzie zapisac pliki",
            default=os.getcwd())
    parser.add_option("-l", "--list", help="Lista adresow")
    (options, args) = parser.parse_args()
    if not os.path.isdir(options.path):
        print("Podany katalog do zapisu plików nie istnieje")
        sys.exit(1)
    if options.list:
        try:
            f = open(options.list)
        except IOError:
            print("Plik z linkami nie istnieje")
            sys.exit(1)
        else:
            args = [url.strip() for url in f]
            f.close()
    args = urls or args
    print("Do pobrania: {0} plików\n".format(len(args)))
    for i, url in enumerate(args):
        # usunięcie slasha, gdy znajduję się na końcu urla
        if url.endswith("/"):
            url = url[:-1]
        # usunięcie rozszerzenia .html gdy adres je zawiera
        if url.endswith(".html"):
            url = url[:-len(".html")]
        filename = os.path.split(url)[1]
        if not "rapidshare.com" in url:
            print("Zły adres do Rapidshare: {0}".format(url))
        elif os.path.isfile(os.path.join(options.path, filename)):
            print("{0} istnieje".format(filename))
        else:
            download(url, options.path, filename)
        if i != len(args) - 1:
            print("")
    #print("Skończyłem pobieranie wszystkich plików")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        s = "Podaj adresy do plików z Rapidshare oddzielone spacją\n"
        urls = raw_input(s)
        main(urls.split())
        if os.name in ("nt", "ce"):
            raw_input()
    else:
        main()
