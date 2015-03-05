__author__ = 'stokesa6'

import gtk
import threading

from pages.machine_page import MachinePage
from pages.raster_page import RasterPage
from pages.topological_page import TopologicalPage
from pages.configuration_page import ConfigPage
from pages.population_page import PopulationView
import visualiser_modes
from pacman103.conf import config
import logging
logger = logging.getLogger(__name__)


class VisualiserMain(object):

    def __init__(self, dao, parent, start_simulation_method=None):
        #define the window
        self.received = False
        self.pages = None
        self.real_pages = list()
        self.main_menu = None
        self.run_menu_item = None
        self.dao = dao
        #holder for the different pages (hopefully for speed of represnetation)
        self.open_windows = list()
        self.vertex_to_page_mapping = dict()
        self.start_simulation_method = start_simulation_method
        #start making the main window
        self.window = self.set_up_main_window()
        self.add_menus()
        #add the pages
        self.create_pages(dao)
        #set current page to X
        self.pages.set_current_page(2)
        #display window
        self.window.show()
        self.parent = parent

    #initlise main window
    def set_up_main_window(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)
        window.set_border_width(10)
        window.set_default_size(500, 500)
        window.set_title("SpinnView")
        self.vbox = gtk.VBox(False, 2)
        self.vbox.show()
        window.add(self.vbox)
        self.accel = gtk.AccelGroup()
        window.add_accel_group(self.accel)
        return window

    #goes though the pages creating them as required
    def create_pages(self, dao):
        self.create_the_notebook_that_holds_pages()
        self.create_machine_static_page()
        #check that the vis has anything to visulise
        if (config.getboolean("Visualiser", "have_board") and
                config.getboolean("Recording", "send_live_spikes")):
            #create default pages
            self.handle_defaults_from_vertex()

            #create a configuration page for pops with record set
            configuration_page = ConfigPage(self.dao, self.open_windows, self.pages,
                                            self.vertex_to_page_mapping, self.real_pages)

        #create a population view if set to by default
        if config.getboolean("Visualiser", "view_population"):
            population_page = gtk.Frame("populations")
            population_page.show()
            pop_view = PopulationView(self.dao, self.open_windows, self, population_page)


        #set all pages to be visable
        for page_id in range(self.pages.get_n_pages()):
            page = self.pages.get_nth_page(page_id)
            page.show()


    def handle_defaults_from_vertex(self):
        '''
        goes though the vertexes and generates pages based off the default values
        '''
        raster_merged_vertexes = list()
        individual_vertexes = list()
        #locate all that can be combined as well as ones that cant
        for vertex in self.dao.vertices:
            if (vertex.visualiser_mode is not None and
                    vertex.visualiser_mode == visualiser_modes.RASTER):
                if (vertex.visualiser_raster_seperate is not None and
                        vertex.visualiser_raster_seperate):
                    if vertex.focus is not None and vertex.focus:
                        raster_page = RasterPage(self.dao, self.open_windows,
                                                 self.pages, None, self.real_pages,
                                                 vertex=vertex, merged=False)
                        #update tracker
                        self.vertex_to_page_mapping[vertex] = raster_page
                else:
                    raster_merged_vertexes.append(vertex)
                    vertex.visualiser_raster_seperate = False
            elif (vertex.visualiser_mode is not None and
                    vertex.visualiser_mode == visualiser_modes.TOPOLOGICAL):
                retina_page = TopologicalPage(self.dao, self.open_windows,
                                              self.pages, vertex, self.real_pages)
                #update tracker
                self.vertex_to_page_mapping[vertex] = retina_page


        #create the merged page
        if len(raster_merged_vertexes) > 0:
            raster_page = RasterPage(self.dao, self.open_windows,
                                     self.pages, raster_merged_vertexes,
                                     self.real_pages)
            #update tracker
            for vertex in raster_merged_vertexes:
                self.vertex_to_page_mapping[vertex] = raster_page


    def create_machine_static_page(self):
        '''
        creates the static machine page which comes as standard in the vis
        '''
        #create machine tab in the form of a table
        scope = config.get("Visualiser", "initial_scope")
        machine_page = MachinePage(self.dao, True, scope, self.open_windows,
                                   self.pages, self.real_pages)


    def create_the_notebook_that_holds_pages(self):
        '''
        sets up the original notebook for holding pages
        '''
        self.pages = gtk.Notebook()
        self.pages.show()
        self.pages.set_tab_pos(gtk.POS_TOP)
        self.vbox.pack_start(self.pages, True, True, 1)
        self.pages.show_tabs = True
        self.pages.show_border = True

    def add_menus(self):
        '''
        adds basic menus for the vis
        '''
        self.main_menu = gtk.MenuBar()
        self.vbox.pack_start(self.main_menu, False, False, 0)
        #add file menuitem
        file_menu_main = gtk.MenuItem("File")
        self.main_menu.append(file_menu_main)

        #add file submenu
        file_sub_menu = gtk.Menu()
        file_menu_main.set_submenu(file_sub_menu)
        #add file sub menu items
        new_item = gtk.ImageMenuItem(gtk.STOCK_NEW, self.accel)
        key, mod = gtk.accelerator_parse("<Control>N")
        new_item.add_accelerator("activate", self.accel,
                                 key, mod, gtk.ACCEL_VISIBLE)
        file_sub_menu.append(new_item)

        load_item = gtk.ImageMenuItem(gtk.STOCK_HARDDISK, self.accel)
        load_item.set_label("Load")
        key, mod = gtk.accelerator_parse("<Control>O")
        load_item.add_accelerator("activate", self.accel,
                                  key, mod, gtk.ACCEL_VISIBLE)
        file_sub_menu.append(load_item)

        sep = gtk.SeparatorMenuItem()
        file_sub_menu.append(sep)

        exit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT, self.accel)
        key, mod = gtk.accelerator_parse("<Control>Q")
        exit_item.add_accelerator("activate", self.accel,
                                  key, mod, gtk.ACCEL_VISIBLE)
        file_sub_menu.append(exit_item)
        exit_item.connect("activate", self.destroy)
        
        if self.start_simulation_method is not None:
            self.run_menu_item = gtk.MenuItem("Run Now!")
            self.main_menu.append(self.run_menu_item)
            self.run_menu_item.connect("activate", self.run_item_selected)
        

        #add option menu
        '''
        option_menu_main = gtk.MenuItem("Options")
        option_sub_menu = gtk.Menu()
        main_menu.add(option_menu_main)
        option_menu_main.set_submenu(option_sub_menu)

        core_option = gtk.CheckMenuItem("view machine in core mode")
        core_layout_option = gtk.CheckMenuItem("view cores in physical layout")
        population_view = gtk.CheckMenuItem("open population_view")
        option_sub_menu.add(core_option)
        option_sub_menu.add(core_layout_option)
        option_sub_menu.add(population_view)
        core_option.connect("activate", self.change_machine_layout, core_option)
        core_layout_option.connect("activate", self.change_core_layout, core_layout_option)
        population_view.connect("activate", self.add_population_view)
        '''

        self.main_menu.show_all()
        self.main_menu.show()
        
    def run_item_selected(self, widget):
        '''
        method to handle the clicking of the run now mode
        '''
        self.main_menu.remove(self.run_menu_item)
        start_thread = threading.Thread(target=self.start_simulation_method)
        start_thread.start()


    def change_core_layout(self, wigdit, option):
        '''
        changes the layout of the machine
        '''
        for page in self.pages:
            if isinstance(page, MachinePage):
                page.update_chip_layout(option)

    def add_population_view(self, widget):
        '''
        initlises a population window for showing heat maps
        '''
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)
        window.set_border_width(10)
        window.set_default_size(500, 500)
        window.set_title("SpinnView populations")
        population_window = PopulationView(self.dao, self.open_windows, self, window)
        self.open_windows.append(population_window)


    def change_machine_layout(self, widgit, option):
        '''
        method that updates machine setup
        '''
        for page in self.pages:
            if isinstance(page, MachinePage) and widgit.get_active():
                page.update_page(MachinePage.CORE_SCOPE)
            else:
                page.update_page(MachinePage.CHIP_SCOPE)

    def redraw_graphs(self, timer_tic):
        '''
        draws only graphgs that are currnetly visible
        and are either topolgoical or raster in either window or page form
        '''
        for page in self.real_pages:
            current_page_index = self.pages.get_current_page()
            if (page.page == self.pages.get_nth_page(current_page_index) and
                (isinstance(page, RasterPage) or
                 isinstance(page, TopologicalPage))):
                page.redraw(timer_tic)
        for window in self.open_windows:
            if(isinstance(window, RasterPage) or
               isinstance(window, TopologicalPage)):
                window.page.redraw(timer_tic)


    def delete_event(self, widget, event, data=None):
        '''
        method to kill the gui
        '''
        return False

    def destroy(self, widget, data=None):
        '''
        kill the gui
        '''
        for qui in self.open_windows:
            qui.destroy()
        self.window.destroy()
        gtk.main_quit()
        self.parent.stop()

    def main(self):
        '''
        default start method
        '''
        gtk.main()


    def spike_recieved(self, details):
        '''
        updated the corrapsonding page with the spike recieved from spinnaker
        '''
        if not self.received:
            print "receiving spikes"
            self.received = True
        #print "packet recieved from {}".format(details)
        #check that packet came from a real chip, if so, update raster and pop
        chip_x, chip_y = details['coords'][0], details['coords'][1]
        #locate which mask was used in the application
        mask = self.locate_mask(details['spike_word'])
        key_mask_combo = details['spike_word'] & mask

        #update the page which deals with this vertex
        for subedge in self.dao.inverseMap[key_mask_combo]:
            vertex = subedge.presubvertex.vertex
            if vertex in self.vertex_to_page_mapping.keys():
                updateable_page = self.vertex_to_page_mapping[vertex]
                updateable_page.recieved_spike(details)

    def cool_downer(self):
        '''
        helper method that allows population views to cool down over time

        for population_view in self.population_views:
            population_view.cool_down()
        '''
        pass


    def locate_mask(self, key):
        '''
        helper method to locate the mask used for a key
        '''
        for mask in self.dao.used_masks:
            key = key & mask
            if key in self.dao.used_masks[mask]:
                return mask
        return None

    def get_resets(self):
        resets= list()
        for page in self.real_pages:
            if isinstance(page, TopologicalPage):
                reset = page.get_reset()
                if reset is not None:
                    resets.append(reset)
        return resets

#test boot method
if __name__ == "__main__":
    hello = VisualiserMain(None)
    hello.main()