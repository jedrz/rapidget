#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""W tym pliku są zdefiniowe klasy, które pomagają stworzyć pasek postępu.

Klasa ProgressBar zajmuje się stworzeniem paska postępu.
Argument przekazany do metody update informuje o stanie wykonanego do tej pory
zadania względem podanego wcześniej argumentu max przy tworzeniu obiektu.
Jeśli procent wykonanego zadania przekroczył pewien próg pasek zostaje
uaktualniany (nie ma niepotrzebnego narzutu obliczeniowego związanego z
mnożeniem i dzieleniem wielkich liczb oraz z działaniami na napisach).
Wypisanie obiektu klasy ProgressBar wypisze aktualny wygląd paska.

Funkcje cone, ctwo, cthree służą do czyszczenia ekranu cofając kursor do
początku linii.

Przed wypisywaniem tekstu wywołać najpierw funkcję cone.
Następnie przed każdym wypisaniem wywołać funkcję ctwo.
Po wypisaniu wywołać funkcję cthree.

Wygląd paska: 5% [###                      ]

Przykład:
import time
import progbar
total = 1000
p = progbar.ProgressBar(total)
progbar.cone()
for i in xrange(total + 1):
    progbar.ctwo()
    p.update(i)
    print p,
    progbar.cthree()
    time.sleep(0.01)
"""


import sys


class BaseError(Exception):
    """Bazowy wyjątek"""
    pass


class WidthError(BaseError):
    """Wyjątek ten jest rzucany kiedy parametr width jest
    nie większy niz 2"""
    pass


class AmountError(BaseError):
    """Wyjątek jest rzucany gdy parametr amount przekroczy wartość
    atrybutu max w obiekcie klasy ProgressBar.
    """
    pass


class ProgressBar(object):
    """Klasa tworzy pasek postępu z poprzedzającym go procentem
    wykonania zadania.
    """

    def __init__(self, max=50, width=40):
        """Parametr max określa maksymalną wartość przekazaną do metody
        update, zaś width to szerokość paska postępu.
        """
        self.bar = "[]"
        self.max = max
        if width > 2:
            self.width = width
        else:
            raise WidthError("width is not greater than 2")
        self.size = self.width - 2
        self.hashes = -1
        self.percent = -1
        self.update(0)

    def update(self, amount):
        """Parametr amount określa ile wypisać haszy względem zmiennej
        self.max.  Gdy amount == self.max zostanie wypełniony cały pasek.
        """
        if amount > self.max:
            raise AmountError("Amount is higher than max")
        hashes = amount * self.size / self.max
        percent = amount * 100 / self.max
        if hashes > self.hashes or percent > self.percent:
            self.hashes = hashes
            self.percent = percent
            self.bar = "{0:3}%  ".format(self.percent) + "[" + "#" \
                    * self.hashes + " " * (self.size - self.hashes) + "]"

    def __str__(self):
        """Metoda __str__ zostaje wywołana przy próbie wypisania
        obiektu. Zwraca ciąg znaków złożony z procentu
        wykonanego zadania oraz pasek postępu.
        """
        return self.bar


ESC = chr(27)


def cone():
    sys.stdout.write(ESC + "[s")

def ctwo():
    sys.stdout.write(ESC + "[2K" + ESC + "[u" + ESC + "[s")

def cthree():
    sys.stdout.flush()
