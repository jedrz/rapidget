#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading


class KThread(threading.Thread):
    """Bazowa klasa z możliwością zatrzymania wątku"""

    def __init__(self):
        super(KThread, self).__init__()
        self.end_thread = False

    def stop(self):
        self.end_thread = True
