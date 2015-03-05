__author__ = 'stokesa6'
import math
import gtk
import pygtk
import logging
logger = logging.getLogger(__name__)
pygtk.require('2.0')
from visualiser.pages.chip_page import ChipPage

class MachinePage(gtk.Bin):

    CHIP_SCOPE = "chip"
    CORE_SCOPE = "core"

    def __init__(self, dao, static, scope, windows, main_pages, real_pages):
        self.real_pages = real_pages
        self.windows = windows
        self.main_pages = main_pages
        self.current_button_right_clicked = None
        self.button_mapping = dict()
        self.dao = dao
        self.chips_with_views = dict()
        self.machine_table = None
        self.x_dim = None
        self.y_dim = None
        button_mapping = dict()
        if static:
            self.page = gtk.Frame("machine static")
        else:
            self.page = gtk.Frame("machine")

        main_pages.append_page(self.page,
                               gtk.Label("machine static"))
        self.create_machine_page_content(scope)
        if not static:
            pass

     #creates the machien table with edges and cores
    def create_machine_page_content(self, scope):
        #set out table so that it sues double the reuqirements for edges
        self.x_dim = (self.dao.machine.x_dim*2) +1
        self.y_dim = (self.dao.machine.y_dim*2) +1
        self.machine_table = gtk.Table(self.x_dim, self.y_dim, True)
        self.machine_table.set_col_spacings(0)
        self.machine_table.set_row_spacings(0)
        self.page.add(self.machine_table)
        self.machine_table.show()
        #set up buttons to represent cores
        self.set_up_chips_in_machine(scope)
        #add the edges
        self.add_edges()

    #updates page with new machine layout
    def update_page(self, scope):
        for key in self.button_mapping.keys():
            button = self.button_mapping[key][2]
            self.machine_table.remove(button)
        self.button_mapping = dict()
        self.set_up_chips_in_machine(scope)
        self.machine_table.queue_draw()

    #sets up all the chips in the machine view from the dao (uses buttons)
    def set_up_chips_in_machine(self, scope):
        x_dim = self.dao.machine.x_dim
        y_dim = self.dao.machine.y_dim
        for x in range(x_dim):
            for y in range(y_dim):

                column_y = self.correct_y_pos(y, self.y_dim)
                column_x = self.correct_x_pos(x)

                if scope == MachinePage.CHIP_SCOPE:
                    button = gtk.Button("({},{})".format(x, y))
                    #check if button represents a valid chip
                    self.check_button_state(button, x, y)
                    #attach button to table
                    self.machine_table.attach(button, column_x, column_x+1,
                                              column_y, column_y+1)
                    #create right click menu
                    menu = self.create_right_click_menu()
                    #add the coords into the hash so we cna track which chip is being considered
                    self.button_mapping[menu] = [x, y, button]
                    # connect the listener for the button
                    button.connect_object("event", self.button_press, menu)
                else:
                    if self.dao.machine.chip_exists_at(x, y):
                        core_table = gtk.Table(4, 4, False)
                        core_table.show()

                        self.machine_table.attach(core_table, column_x, column_x+1,
                                                  column_y, column_y+1)
                        core_ids = [4,12,13,5,0,8,9,1,16,None,None,17,6,14,15,7,2,10,11,3]
                        count = 0
                        for core_id in core_ids:
                            if core_id is None:
                                count += 1
                            else:
                                button = gtk.Button("({})".format(core_id))
                                button.show()
                                button.set_sensitive(False)
                                y = int(math.floor(count / 4))
                                x = int(count - (y * 4))
                                core_table.attach(button, x, x+1, y, y+1)
                                self.button_mapping[x+y+core_ids[count]] = button
                                button.connect("enter-notify-event", self.population_data, [x,y,core_ids[count]] )
                                count += 1

    def population_data(self, widgit, coords):
        print


    def correct_y_pos(self, machine_y, table_size):
        return (table_size) - (machine_y * 2) - 2

    def correct_x_pos(self, machine_x):
        return  (machine_x * 2) + 1

    # creates the menu used in right clicks
    def create_right_click_menu(self):
        menu = gtk.Menu()
        menu.show()
        tab_menu_item = gtk.MenuItem("chip view in new tab")
        tab_menu_item.show()
        tab_menu_item.connect("activate", self.menuitem_response,
                              "tab")
        window_menu_item = gtk.MenuItem("chip view in new window")
        window_menu_item.connect("activate", self.menuitem_response,
                                 "win")
        window_menu_item.show()
        menu.append(tab_menu_item)
        menu.append(window_menu_item)
        return menu

    # handles the response from the right clicked menu
    def menuitem_response(self, widget, type):
        chip_coords = self.button_mapping[self.current_button_right_clicked]
        self.chips_with_views[chip_coords[0]+chip_coords[1]] = ChipPage
        if type == "win":
            ChipPage(self.dao, chip_coords, self.windows)
        elif type == "tab":
            ChipPage(self.dao, chip_coords, self.windows, self.main_pages)


    #handles the clicking of a chip button (either set up right click menu or
    # opens up chip view in new window
    def button_press(self, widget, event):
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 3:
            self.current_button_right_clicked = widget
            widget.popup(None, None, None, event.button, event.time)
            return True
        if event.type == gtk.gdk.BUTTON_PRESS and event.button == 1:
            chip_coords = self.button_mapping[widget]
            self.chips_with_views[chip_coords[0]+chip_coords[1]] = ChipPage
            core_window = ChipPage(self.dao, chip_coords, self.windows)
        return False


    #checks the state of the chip being repsented in the dao, if not real, then
    #turn to blakc and disable the button
    def check_button_state(self, button, x, y):
        if self.dao.machine.chip_exists_at(x, y):
            button.show()
        else:
            map = button.get_colormap()
            color = map.alloc_color("black")
            style = button.get_style().copy()
            button.set_sensitive(False)

            style.bg[gtk.STATE_NORMAL] = color
            button.set_style(style)
            button.show()

    #handles edge placement in the table
    def add_edges(self):
        x_dim = self.dao.machine.x_dim
        y_dim = self.dao.machine.y_dim
        adjustments = ({'x':1, 'y':0}, {'x':1, 'y':1}, {'x':1, 'y':0},
                       {'x':-1, 'y':0}, {'x':-1, 'y':-1}, {'x':0, 'y':-1})
                         #E        NE      N        W        SW       S
        height = self.machine_table.get_row_spacing(0)
        width = self.machine_table.get_col_spacing(0)
        for x in range(x_dim):
            for y in range(y_dim):
                if self.dao.machine.chip_exists_at(x, y):
                    index = 0
                    for connection in self.dao.machine.get_chip(x, y).router.neighbourlist:
                        height = self.machine_table.get_row_spacing(0)
                        width = self.machine_table.get_col_spacing(0)
                        #calculate edge position
                        column_y = self.correct_y_pos(y, self.y_dim) + adjustments[index]['y']
                        column_x = self.correct_x_pos(x) + adjustments[index]['x']
                        #attach in correct position
                        if connection is not None:
                            if index == 0 : #E, W
                                 self.machine_table.attach(gtk.Label("-"), column_x, column_x+1, column_y, column_y+1)
                            if index == 1 : #ne sw
                                self.machine_table.attach(gtk.Label("/"), column_x, column_x+1, column_y-2, column_y-1)
                            if index == 2 : #N s
                                self.machine_table.attach(gtk.Label("|"), column_x-1, column_x, column_y-1, column_y)
                           # if index == 3: #E, W
                             #   print "{},{} = {}, {}".format(x,y,column_x-1,column_y
                             #  self.machine_table.attach(gtk.Label("---"), column_x-2, column_x-1, column_y, column_y+1)
                          #  if index == 4: #ne sw
                           #     self.machine_table.attach(gtk.Label("/"), column_x-1, column_x, column_y-1, column_y)
                          #  if index == 5: #N s
                             #   self.machine_table.attach(gtk.Label("|"), column_x, column_x+1, column_y-1, column_y)
                        index +=1
        self.machine_table.show_all()

    def update_chip_layout(self, option):
        for chip_view_key in self.chips_with_views.keys():
            chip_view = self.chips_with_views[chip_view_key]
            chip_view.update(chip_view, option)

