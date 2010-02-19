#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Moduł ten tworzy pasek postępu.
Klasa ProgressBar zajmuje się stworzeniem paska postępu.
Argument przekazany do metody update informuje o stanie wykonanego do tej pory
zadania względem podanego wcześniej argumentu max przy tworzeniu obiektu.
Jeśli procent wykonanego zadania przekroczył pewien próg pasek zostaje
uaktualniany (nie ma niepotrzebnego narzutu obliczeniowego związanego z
mnożeniem i dzieleniem wielkich liczb.

Wygląd paska: 5% [###                      ]

Przykład:
import time
import progbar
total = 1000
p = progbar.ProgressBar(total)
c = progbar.ClearScreen()
c.one()
for i in xrange(total + 1):
    c.two()
    p.update(i)
    print p,
    c.three()
    time.sleep(0.01)
"""


import sys


__author__ = "Łukasz Jędrzejewski <lukasz892@gmail.com>"


class WidthError(Exception):
    """Wyjątek ten jest rzucany kiedy parametr width jest
    nie większy niz 2"""
    pass


class AmountError(Exception):
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
        update.
        """
        self.bar = "[]"
        self.max = max
        if width > 2:
            self.width = width
        else:
            raise(WidthError("width is not greater than 2"))
        self.size = self.width - 2
        self.hashes = -1
        self.percent = -1
        self.update(0)

    def update(self, amount):
        """Parametr amount określa ile wypisać haszy względem zmiennej
        self.max.  Gdy amount == self.max zostanie wypełniony cały pasek.
        """
        if amount > self.max:
            raise(AmountError("Amount is greater than max"))
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


class ClearScreen(object):
    """Klasa czyści ekran cofając kursor do początku linii.

    Przed wypisywaniem tekstu wywołać najpierw metodę one.
    Następnie przed każdym wypisaniem wywołać medotę two.
    Po wypisaniu wywołać metodę three.

    Przykład:
    c = ClearScreen()
    c.one()
    while True:
        c.two()
        sys.stdout.write("Ta linia będzie ciągle wypisywana")
        c.three()
    """

    def __init__(self):
        self.esc = chr(27)

    def one(self):
        sys.stdout.write(self.esc + "[s")

    def two(self):
        sys.stdout.write(self.esc + "[2K" + self.esc + "[u" + self.esc + "[s")

    def three(self):
        sys.stdout.flush()


if __name__ == "__main__":
    import time
    total = 1000
    p = ProgressBar(total)
    c = ClearScreen()
    c.one()
    for i in xrange(total + 1):
        c.two()
        p.update(i)
        print p,
        c.three()
        time.sleep(0.01)
