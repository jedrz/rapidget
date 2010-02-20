#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import urllib2

import progbar


def download_file(url, file):
    """Pobiera plik, wyświetlajac aktualny stan pobierania w postaci
    progressbara.
    """
    outfile = open(file, "wb")
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
        # jeśli pobraliśmy cały plik
        if bytes == "":
            progressbar.update(filesize + step)
            sys.stdout.write("%s" % progressbar)
            clear.three()
            break
        i += step
        # uaktualnienie progressbara
        progressbar.update(i)
        sys.stdout.write("%s" % progressbar)
        clear.three()

    sys.stdout.write("\n")
    urlfile.close()
    outfile.close()
