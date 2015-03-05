__author__ = 'stokesa6'
import gtk
import gtk.gdk
import math
import logging
logger = logging.getLogger(__name__)
from visualiser.pages.abstract_page import AbstractPage

class PopulationView(AbstractPage):

    def __init__(self, dao, open_windows, parent, window, main_pages, real_pages):
        super(PopulationView, self).__init__(dao, open_windows, main_pages,real_pages)
        self.parent = parent
        self.window = window
        self.window.connect("delete_event", self.delete_event)
        self.modded_buttons = dict()
        self.populations = dict()
        open_windows.append(self.window)
        self.default_color = None
        self.create_populations(dao)
        self.window.show()
        self.window.show_all()
        self.window.queue_draw()

    #method to kill the gui
    def delete_event(self, widget, event, data=None):
        return False


    #creates a collection of populations
    def create_populations(self, dao):
        #get pops from dao
        populations = dao.get_vertices()
        #calulate the dimensions of th table to hold the pops
        number_of_verts = len(populations)
        dimension = int(math.ceil(math.sqrt(number_of_verts)))
        if (dimension == 1 and number_of_verts > 1) or dimension == 0:
            dimension = 2
        pop_table = gtk.Table(dimension, dimension)
        self.window.add(pop_table)
        pop_table.show()
        #add each pop to table
        pop_id = 0
        self.default_color = gtk.gdk.Color("#e6e6fa")
        for pop in populations:
            button = gtk.Button("{}".format(pop.label))
           # button = gtk.ColorButton(self.default_color)
           # button.set_title("{}".format(pop.label))


            style = button.get_style().copy()
            style.bg[gtk.STATE_NORMAL] = self.default_color
            button.set_style(style)
            button.show()
            y = int(math.floor(pop_id / dimension))
            x = int(pop_id - (y * dimension))
            pop_table.attach(button, x, x+1, y, y+1)
            self.populations[pop] = button
            pop_id += 1
        pop_table.show_all()


    #recieved a packet from spinnaker, need to
    def recieved_spike(self, details):
        coords = details['coords']
        processors = self.dao.machine.get_chip(coords[0], coords[1]).processors
        core = None
        for processor in processors:
            if processor.idx == coords[2] + 100:
                core = processor
        population = core.placement.subvertex.vertex
        button = self.populations[population]

        if button in self.modded_buttons.keys():
            self.modded_buttons[button] += 1
        else:
            self.modded_buttons[button] = 1

        value_to_add = self.modded_buttons[button]


        current_color = self.default_color
        #do red first
        if current_color.red + value_to_add >= 65535:
            value_to_add -= (65535 - current_color.red)
            current_color.red = 65535
        else:
            current_color.red += value_to_add
            value_to_add = 0

        #do green next
        if current_color.green + value_to_add >= 65535:
            value_to_add -= (65535 - current_color.green)
            current_color.green = 65535
        else:
            current_color.green += value_to_add
            value_to_add = 0

        #do blue last
        if current_color.blue + value_to_add >= 65535:
            value_to_add -= (65535 - current_color.blue)
            current_color.blue = 65535
        else:
            current_color.blue += value_to_add
            value_to_add = 0

        style = button.get_style().copy()
        style.bg[gtk.STATE_NORMAL] = current_color
        button.set_style(style)
        button.show()

    def cool_down(self):
        print "here"
        for key in self.modded_buttons:
            button = self.populations[key]
            self.modded_buttons[key] -= 1
            valueToAdd = self.modded_buttons
            if valueToAdd == 0:
                del self.modded_buttons[key]
            map = button.get_colormap()
            current_color = self.default_color

            #do red first
            if current_color.red + value_to_add >= 65535:
                value_to_add -= (65535 - current_color.red)
                current_color.red = 65535
            else:
                current_color.red += value_to_add
                value_to_add = 0

            #do green next
            if current_color.green + value_to_add >= 65535:
                value_to_add -= (65535 - current_color.green)
                current_color.green = 65535
            else:
                current_color.green += value_to_add
                value_to_add = 0

            #do blue last
            if current_color.blue + value_to_add >= 65535:
                value_to_add -= (65535 - current_color.blue)
                current_color.blue = 65535
            else:
                current_color.blue += value_to_add
                value_to_add = 0

            style = button.get_style().copy()
            style.bg[gtk.STATE_NORMAL] = current_color
            button.set_style(style)
            button.show()
            button.queue_draw()








