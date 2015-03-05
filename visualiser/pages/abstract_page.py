__author__ = 'stokesa6'
import gtk
from pacman103.core import exceptions

class AbstractPage(object):
    def __init__(self, dao, windows, main_pages, real_pages):
        self.dao = dao
        self.windows = windows
        self.main_pages = main_pages
        self.real_pages = real_pages
        self.page = None
        self.real_pages.append(self)



    def recieved_spike(self, details):
        raise exceptions.VisuliserException("abstract page does not "
                                            "impliment this method")

    def reset_values(self):
        raise exceptions.VisuliserException("abstract page does not "
                                            "impliment this method")

