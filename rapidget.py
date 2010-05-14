#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Skrypt służy do pobierania plików z rapidshare.com

Pobiera pliki jako Free User. Przechodzi przez wszyskie napotkane
strony, wyciągając informację o tym, ile sekund musimy czekać, dopóki nie
będziemy mogli pobrać pliku. Następnie odczekuje odpowiednią
ilość sekund.

Gdy nasz adres ip pobiera już plik, próbuje wznowić pobieranie po 1,5
minuty. Wykonuje tą czynność dopóki nie będziemy mogli pobrać pliku.

Gdy url jest nieprawidłowy lub strona nie istnieje lub plik znajduje się
w aktualnym katalogu wyświetli stosowny komunikat, a następnie przejdzie
do pobierania następnego pliku (oczywiście jeśli takowy będzie).

Użycie:
rapidget.py [opcje] link1 [link2..]
Opcje:
  -h, --help            wyświetla pomoc
  -p PATH, --path=PATH  Katalog do którego zapisać pliki
  -l LIST, --list=LIST  Plik z listą adresów

Skrypt można także uruchomić bez parametrów, wtedy linki podajemy oddzielone pojedynczą spacją.
"""


import sys
import os

from cli.console import main


if len(sys.argv) == 1:
    s = "Podaj adresy do plików z Rapidshare oddzielone spacją\n"
    urls = raw_input(s)
    main(urls.split())
    if os.name in ("nt", "ce"):
        raw_input()
else:
    main(sargs=sys.argv)
