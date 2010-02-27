#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
from optparse import OptionParser

from core import rapid
from cli import progbar


def _sleep(count, delete=False):
    """Wyświetla ile jeszcze musimy czekać na pobranie pliku.
    Czyści aktualną linię i w nią wpisuje napis.
    """
    progbar.cone()
    while count >= 0:
        minutes = count / 60
        seconds = count - minutes * 60
        progbar.ctwo()
        sys.stdout.write("Oczekuję na plik jeszcze {0} minut, "
                "{1} sekund".format(minutes, seconds))
        progbar.cthree()
        count -= 1
        time.sleep(1)
    # wyczyść aktualną linię
    if delete:
        progbar.ctwo()
    else:
        print("")


def download(url, path, filename):
    """Pobiera plik, korzysta z RapidWaiter i RapidDownloader"""
    waiter = rapid.RapidWaiter(url)
    waiter.wait()
    limit = busy = False
    while not waiter.done:
        if waiter.limit and not limit:
            print("Przekroczyłeś limit pobierania")
            limit = True
        if waiter.busy and not busy:
            print("Twój adres ip pobiera już pliki")
            busy = True
        if waiter.count > 0:
            if waiter.busy or waiter.limit:
                _sleep(waiter.count, True)
            else:
                _sleep(waiter.count)
        elif waiter.count == 0:
            time.sleep(0.3)
    print("Pobieram plik: {0}".format(filename))
    downloader = rapid.RapidDownloader(waiter.download_url, \
            os.path.join(path, filename))
    downloader.download()
    # poczekaj aż plik zostanie otwarty
    while downloader.filesize == 0:
        time.sleep(1)
    progressbar = progbar.ProgressBar(downloader.filesize)
    progbar.cone()
    print(progressbar)
    while not downloader.is_downloaded():
        progressbar.update(downloader.current_pos)
        progbar.ctwo()
        sys.stdout.write("{0}".format(progressbar))
        progbar.cthree()
    progressbar.update(downloader.filesize)
    progbar.ctwo()
    sys.stdout.write("{0}".format(progressbar))
    progbar.cthree()
    print("Plik został pobrany")


def main(urls=[], sargs=sys.argv):
    """Próbuje pobrać wszystkie pliki oprócz tych, które nie zawierają
    'rapidshare.com' lub istnieją w aktualnym katalogu.

    Tworzy obiekt klasy OptionParser i dodaje opcje:
     - wyboru katalogu do zapisu plików
     - wyboru pliku z listą linków
    """
    parser = OptionParser(usage="Usage: %prog [options] [links]")
    parser.add_option("-p", "--path", help="Gdzie zapisac pliki", \
            default=os.getcwd())
    parser.add_option("-l", "--list", help="Lista adresow")
    (options, args) = parser.parse_args(sargs)
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
            try:
                download(url, options.path, filename)
            except KeyboardInterrupt:
                sys.exit()
        if i != len(args) - 1:
            print("")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        s = "Podaj adresy do plików z Rapidshare oddzielone spacją\n"
        urls = raw_input(s)
        main(urls.split())
        if os.name in ("nt", "ce"):
            raw_input()
    else:
        main()
