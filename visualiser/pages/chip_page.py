__author__ = 'stokesa6'
import gtk
import math
import logging
logger = logging.getLogger(__name__)

class ChipPage(gtk.Bin):

    LOGICAL_VIEW = 0
    PHYSICAL_VIEW = 1

    def __init__(self, dao, coords, windows, chip_pages=None):
        core_table = None
        self.coords = coords
        self.dao = dao
        #trakcer for subpop highlighting
        self.core_buttons = dict()

        if chip_pages is None: # needs to be in its own window and add its own tabs
            chip_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
            #add a
            windows.append(chip_window)
            chip_window.connect("delete_event", self.delete_event)
            chip_window.set_border_width(10)
            chip_window.set_default_size(100, 100)
            chip_window.set_title("SpinnView Chip ({},{}) "
                                   "view".format(coords[0], coords[1]))

            chip_window.show()
            #add notebook for tabs of routing, cores,
            chip_pages = gtk.Notebook()
            chip_window.add(chip_pages)
            self.initilise_nootbook(chip_pages)
            core_table = gtk.Table(4, 5, True)
            core_table.show()
            chip_pages.append_page(core_table, gtk.Label("cores"))

        else: # is in a page of some other window's tabs
            chip_page = gtk.Frame("")
            chip_page.show()
            chip_pages.append_page(chip_page,
                                   gtk.Label("chip({},{})".format(coords[0],
                                                                  coords[1])))
            # still needs its own tabs in a nested fashion
            chip_pages = gtk.Notebook()
            chip_page.add(chip_pages)
            self.initilise_nootbook(chip_pages)
            chip_page = gtk.Frame("cores")
            chip_page.show()
            chip_pages.append_page(chip_page, gtk.Label("cores".format(coords[0],
                                                                       coords[1])))
            core_table = gtk.Table(4, 3, True)
            chip_page.add(core_table)
        core_table.show()
        self.update_table(core_table, coords, dao, ChipPage.LOGICAL_VIEW)
        #create a routing page which contains routing entries
        routing_page = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        routing_page.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        routing_page.show()
        chip_pages.append_page(routing_page, gtk.Label("routing entries"))
        self.update_routing_table_page(dao, routing_page, coords)

    # repeater method for initilising a nootbook
    def initilise_nootbook(self, chip_pages):
        chip_pages.show()
        chip_pages.show_tabs = True
        chip_pages.show_border = True
        chip_pages.set_tab_pos(gtk.POS_TOP)

    #method to kill#  the gui
    def delete_event(self, widget, event, data=None):
        return False

    #creates a table of routing entries
    def update_routing_table_page(self, dao, routing_page, coords):
        entires_table = gtk.Table(7, 1001, False)

        entires_table.show()
        routing_page.add_with_viewport(entires_table)
        chip_router = dao.machine.get_chip(coords[0], coords[1]).router
        position = 1
        index_label = gtk.Label("Index  ")
        key_label = gtk.Label("Key (Hex)  ")
        mask_label = gtk.Label("Mask (Hex)  ")
        route_label = gtk.Label("Route (Hex)  ")
        source_label = gtk.Label("Src. Core  ")
        core_label = gtk.Label("-> [Cores][Links]")

        entires_table.attach(index_label, 0, 1, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        entires_table.attach(key_label, 1, 2, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        entires_table.attach(mask_label, 2, 3, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        entires_table.attach(route_label, 3, 4, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        entires_table.attach(source_label, 4, 5, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        entires_table.attach(core_label, 5, 6, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        for router_key in chip_router.cam.keys():
            index_label = gtk.Label("{}".format(position -1))
            key = int(chip_router.cam[router_key][0].key)
            mask = int(chip_router.cam[router_key][0].mask)
            route = int(chip_router.cam[router_key][0].route)
            core_id = "(%d, %d, %d)" % ((key>>24&0xFF),(key>>16&0xFF),(key>>11&0xFF)+1)
            route_txt = self.expandRouteValue(route)
            key_label = gtk.Label("{}".format(self.uint32ToHexString(key)))
            mask_label = gtk.Label("{}".format(self.uint32ToHexString(mask)))
            route_label = gtk.Label("{}".format(self.uint32ToHexString(route)))
            source_label = gtk.Label("{}".format(core_id))
            core_label = gtk.Label("{}".format(route_txt))

            entires_table.attach(index_label, 0, 1, position, position + 1, xoptions=gtk.SHRINK)
            entires_table.attach(key_label, 1, 2, position, position + 1, xoptions=gtk.SHRINK)
            entires_table.attach(mask_label, 2, 3, position, position + 1, xoptions=gtk.SHRINK)
            entires_table.attach(route_label, 3, 4, position, position + 1, xoptions=gtk.SHRINK)
            entires_table.attach(source_label, 4, 5, position, position + 1, xoptions=gtk.SHRINK)
            entires_table.attach(core_label, 5, 6, position, position + 1, xoptions=gtk.SHRINK)
            position += 1


        entires_table.show()
        entires_table.show_all()


    def uint32ToHexString(self, number):
        """
        Convert a 32-bit unsigned number into a hex string.
        """
        bottom = number & 0xFFFF
        top    = (number >> 16) & 0xFFFF
        hexString = "%4.0X%4.0X" %(top, bottom)
        return hexString

    def expandRouteValue(self, routeValue):
        """
        Convert a 32-bit route word into a string which lists the target cores and
        links.
        """
        linksValue     = routeValue & 0x3F
        processorValue = (routeValue >> 6)
        # Convert processor targets to readable values:
        routeString = "["
        first = True
        for i in range(16):
            proc = processorValue & 0b1
            if proc != 0:
                if first:
                    routeString += "%d" % i
                    first = False
                else:
                    routeString += ", %d" % i
            processorValue = processorValue >> 1
        routeString += "] ["
        # Convert link targets to readable values:
        linkLabels = {0:'E', 1:'NE', 2:'N', \
                      3:'W', 4: 'SW', 5:'S'}

        first = True
        for i in range(6):
            link = linksValue & 0b1
            if link != 0:
                if first:
                    routeString += "%s" % linkLabels[i]
                    first = False
                else:
                    routeString += ", %s" % linkLabels[i]
            linksValue = linksValue >> 1
        routeString += "]"

        return routeString


    # updates the table with core layout
    #TODO needs to have tied into dao with sub population on chip
    def update_table(self, core_table, coords, dao, view):
        if(view == ChipPage.PHYSICAL_VIEW):
            core_ids = [4,12,13,5,0,8,9,1,16,None,None,17,6,14,15,7,2,10,11,3]
            count = 0
            for core_id in core_ids:
                if core_id is None:
                    count += 1
                else:
                    button = gtk.Button("({})".format(core_id))
                    processor = dao.machine.get_chip(coords[0], coords[1]).processors[core_id]
                    if processor.placement is not None:
                        subvert = processor.placement.subvertex

                        button.set_tooltip_text("id : {}. \n {} to " \
                                                "{}.".format(subvert.vertex.label,
                                                            subvert.lo_atom,
                                                            subvert.hi_atom))
                    else:
                        button.set_tooltip_text("this core does not contain any atoms")
                    button.show()
                    button.set_sensitive(False)
                    y = int(math.floor(count / 4))
                    x = int(count - (y * 4))
                    core_table.attach(button, x, x+1, y, y+1)
                    self.core_buttons[core_ids[count]] = button
                    count += 1
        else:
            for core_id in range(19):
                button = gtk.Button("({})".format(core_id))
                if(core_id >= 16 or core_id == 0):
                    button.set_tooltip_text("this core is not avilable for use in pacman103")
                else:
                    processor = dao.machine.get_chip(coords[0], coords[1]).get_processor(core_id+1)
                    found = False
                    for placement in dao.placements:
                        if placement.processor.to_string() == processor.to_string():
                            subvert = placement.subvertex

                            button.set_tooltip_text("id : {}. \n  {} to " \
                                                    "{}.".format(subvert.vertex.label,
                                                                subvert.lo_atom,
                                                                subvert.hi_atom))
                            found = True
                    if not found:
                        button.set_tooltip_text("this core does not contain any atoms")
                button.show()
                button.set_sensitive(False)
                y = int(math.floor(core_id / 4))
                x = int(core_id - (y * 4))
                core_table.attach(button, x, x+1, y, y+1)
                self.core_buttons[core_id] = button

    def update(self, option):
        for button_key in self.core_buttons.keys():
            button = self.core_buttons[button_key]
            self.core_table.remove(button)
        print "options is {}".format(option)
        if option:
            self.update_table(self.core_table, self.coords,
                              self.dao, ChipPage.LOGICAL_VIEW)
        else:
            self.update_table(self.core_table, self.coords,
                              self.dao, ChipPage.PHYSICAL_VIEW)
