__author__ = 'stokesa6'
from pacman103.conf import config
from pacman103.core.utilities import packet_conversions
from visualiser.pages.abstract_page import AbstractPage
import math
import gtk
import cairo
import logging
from pacman103.front.common.external_device import ExternalDevice
logger = logging.getLogger(__name__)

class TopologicalPage(AbstractPage):
    RECTANGLE_SIZE = {'x': 1, 'y': 1}
    EXPOSURE_BAR_SIZE = 20
    EXPOSURE_BAR_LABEL_SIZE = 40
    EXPOSURE_BAR_SPACE_SIZE = 20
    LEGEND_SIZE = {'x': 40, 'y': 20}
    NO_BLOCKS_IN_EXPOSURE_PLOT = 200
    NO_LABELS = 10
    NO_COLOR_MAPPING_LABELS = 10
    pixmap = None


    def __init__(self, dao, windows, main_pages,
                 vertex_in_question, real_pages):
        super(TopologicalPage, self).__init__(dao, windows,
                                              main_pages, real_pages)

        #holds all the vertexes being recorded for spikes
        self.vertex_in_question = vertex_in_question

        if self.vertex_in_question.visualiser_reset_counters:
            self.data = dict()
            self.data['t'] = self.vertex_in_question.visualiser_reset_counter_period
            self.data['p'] = self
            self.data['pt'] = None
        else:
            self.data = None


        self.placement_fudge = None
        if getattr(self.vertex_in_question,
                   "get_packet_retina_coords", None) is None:
            self.NO_BLOCKS_IN_EXPOSURE_PLOT = \
                vertex_in_question.visualiser_no_colours
            self.NO_COLOR_MAPPING_LABELS = \
                vertex_in_question.visualiser_no_colours

        self.drawing_area = None
        self.objects_to_draw = dict()
        self.max_color_value = {'r': 1, 'g': 1, 'b': 1}
        self.min_color_value = {'r': 0, 'g': 0, 'b': 0}
        number_of_neurons = (self.vertex_in_question.subvertices[0].hi_atom -
                             self.vertex_in_question.subvertices[0].lo_atom)
        if (vertex_in_question.visualiser_2d_dimensions['x'] is None or
            vertex_in_question.visualiser_2d_dimensions['y'] is None):
                self.x_dim = int(math.sqrt(number_of_neurons))
                self.y_dim = int(math.sqrt(number_of_neurons))
                vertex_in_question.visualiser_2d_dimensions = {'x': self.x_dim, 'y': self.y_dim}
        else:
            self.x_dim = vertex_in_question.visualiser_2d_dimensions['x']
            self.y_dim = vertex_in_question.visualiser_2d_dimensions['y']

        #values for tracking color increases
        self.initial_value = 0
        self.max_seen_value = 50
        self.min_seen_value = 0
        self.needs_reseting = False
        self.spikes_that_need_processing = list()
        self.drawing = False

        #holders for determining if you need to redraw
        # everything, or just a section
        self.new_entries = list()
        self.redraw_everything = True

        self.exposure_bar_mapping = dict()


        #stores a offset needed for fading
        retina_drop_off_theshold = None
        if config.getboolean("Visualiser", "retina_plot_drop_off"):
            retina_drop_off_theshold = \
                config.get("Visualiser", "retina_plot_drop_off_value_per_sec")

        self.data_stores = []

       # print self.vertex_in_question
        label = self.vertex_in_question.label
        if label == None:
            label = "Unknown"

        #set name of page
        self.page = gtk.Frame("topological plot")
        main_pages.append_page(self.page,
                               gtk.Label("Topological Page of "
                                         "{}".format(vertex_in_question.label)))
        #generate plot area
        self.generate_plot()

        #generate objects to draw
        self.generate_objects()

        #generate the rectangles that represent the retina view
        self.generate_retina_view()


    def generate_objects(self):
        '''
        generates the drawable objects in an array
        '''
        max_y_pos = (self.y_dim * self.RECTANGLE_SIZE['y']) - self.LEGEND_SIZE['x']
        for x in range(self.x_dim):
            for y in range(self.y_dim):
                x_pos = (x * self.RECTANGLE_SIZE['x']) + self.LEGEND_SIZE['x']
                y_pos = y * self.RECTANGLE_SIZE['y']
                width = self.RECTANGLE_SIZE['x']
                height = self.RECTANGLE_SIZE['y']
                colour = self.initial_value
                y_pos = max_y_pos-self.LEGEND_SIZE['y']-y_pos
                key = "{}:{}".format(int(x), int(y))
                self.objects_to_draw[key] = {'x': int(x_pos),
                                             'y': int(y_pos),
                                             'w': int(width),
                                             'h': int(height),
                                             'c': colour}


    def generate_retina_view(self):
        '''
        generates the rectangles that represent the retina view and sets them to
        the colour black initially.

        NOTE the size is govenered by the neurons in the external device. (has
        to be a size shaped)
        '''
        height_of_screen = self.y_dim * self.RECTANGLE_SIZE['y']
        width_of_screen = self.x_dim * self.RECTANGLE_SIZE['x']
        ##add exposureBar
        width = width_of_screen + (self.EXPOSURE_BAR_SIZE +
                                   self.EXPOSURE_BAR_LABEL_SIZE +
                                   self.EXPOSURE_BAR_SPACE_SIZE)
        height = height_of_screen
        #add legends to screen
        width += self.LEGEND_SIZE['x']
        height += self.LEGEND_SIZE['y']

        #sets up the drawing area size
        self.drawing_area.set_size_request(int(width), int(height))

    def generate_plot(self):
        '''
        generates the initial drawing area and ties it into the page
        '''
        self.drawing_area = gtk.DrawingArea()
        self.drawing_area.connect("expose_event", self.expose)
        self.drawing_area.connect("size-allocate", self.size_allocate)
        self.page.add(self.drawing_area)
        self.page.show_all()


    def expose(self, widget, event):
        '''
        when the drawing area is exposed, redraw the rectangle
        '''
        #get drawing area writable object
        #print "started the expose"
        cr = widget.window.cairo_create()

        #check that entries havent fallen off the theshold
        if self.needs_reseting:
            #print "starting resetting"
            self.adjust_values_to_fit_in_range()

        #add the exposure bar
        self.add_exposure_bar(cr)

        #do legend
        self.add_exposure_legend(cr)

       # print "seen min is now {}".format(self.min_seen_value)

        #if self.redraw_everything:
        for drawable_object_key in self.objects_to_draw.keys():
            self.draw_object(cr, self.objects_to_draw[drawable_object_key])
        #else:
         #   for new_entry_key in self.new_entries:
          #      drawable_object = self.objects_to_draw[new_entry_key]
           #     self.draw_object(cr, drawable_object)
           # self.new_entries = list()

        #add axises
        self.add_x_y_axis_labels(cr)
       # print "finished the expose"
        self.drawing = False



    def adjust_values_to_fit_in_range(self):
        '''
        this method resets the color keys of the color mapper
        so that stuff can be adjusted to reflect changes in values
        '''
        #print "doing reset"
        self.needs_reseting = False
        self.redraw_everything = True
       # print "min value is {}".format(self.min_seen_value)
        if 0 != self.min_seen_value:
            diff = 0 - self.min_seen_value
            #print "diff is {}".format(diff)
            for drawable_key in self.objects_to_draw.keys():
                old_object = self.objects_to_draw[drawable_key]
                old_value = old_object['c']
                new_value = old_value + diff
                if new_value > self.max_seen_value:
                    self.set_max_seen_value(new_value)
                self.objects_to_draw[drawable_key] = {'x': old_object['x'],
                                                      'y': old_object['y'],
                                                      'w': old_object['w'],
                                                      'h': old_object['h'],
                                                      'c': new_value}
        if self.max_seen_value > 765:
            ratio = self.max_seen_value / 766.0
            #print "ratio is {} and max is {}".format(ratio, self.max_seen_value)
            self.max_seen_value = 0
            for drawable_key in self.objects_to_draw.keys():
                old_object = self.objects_to_draw[drawable_key]
                old_value = old_object['c']
                new_value = old_value / ratio
               # print "new value is {}".format(int(math.floor(new_value)))
                if new_value > self.max_seen_value:
                    self.set_max_seen_value(int(math.floor(new_value)))
                self.objects_to_draw[drawable_key] = {'x': old_object['x'],
                                                      'y': old_object['y'],
                                                      'w': old_object['w'],
                                                      'h': old_object['h'],
                                                      'c': int(new_value)}
      #  print "seen min is {}".format(self.min_seen_value)
        self.min_seen_value = 0
       # print "seen min is {}".format(self.min_seen_value)


    def draw_object(self, cr, drawable_object):
        '''
        draws an object onto the drawable writable object
        '''
        #set the color for the object
        value = drawable_object['c']
        color_to_draw = self.exposure_bar_mapping[value]

        cr.set_source_rgb(color_to_draw['r'],
                          color_to_draw['g'],
                          color_to_draw['b'])
        #create a rectangle for the object
        cr.rectangle(drawable_object['x'], drawable_object['y'],
                     drawable_object['w'], drawable_object['h'])
        cr.fill()

    def add_x_y_axis_labels(self, cr):
        height_of_screen = self.y_dim * self.RECTANGLE_SIZE['y']
        width_of_screen = self.x_dim * self.RECTANGLE_SIZE['x']
        y_position = math.floor(self.y_dim / self.NO_LABELS)
        x_position = math.floor(self.x_dim / self.NO_LABELS)
        #set axis font and color
        cr.set_source_rgb(0, 0, 0) # black
        cr.select_font_face("Purisa",
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)

        #do x axis
        for x_position_2 in range(self.NO_LABELS):
            x_loc = (x_position * x_position_2)
            object_key = "{}:{}".format(int(x_loc), 0)
            x_screen_pos = self.objects_to_draw[object_key]['x']
            y_screen_pos = height_of_screen + self.RECTANGLE_SIZE['y']
            cr.move_to(x_screen_pos, y_screen_pos)
            cr.show_text("{}".format(x_loc))

        #do y axis
        for y_position_2 in range(self.NO_LABELS):
            y_loc = (y_position * y_position_2)
            object_key = "{}:{}".format(0, int(y_loc))
            y_screen_pos = self.objects_to_draw[object_key]['y']
            cr.move_to(0, y_screen_pos)
            cr.show_text("{}".format(y_loc))

    def add_exposure_bar(self, cr):
        '''
        adds the exposure bar to the side of the window
        '''
        height_of_screen = self.y_dim * self.RECTANGLE_SIZE['y']
        width_of_screen = self.x_dim * self.RECTANGLE_SIZE['x']
        position_of_bar = width_of_screen + (self.EXPOSURE_BAR_SIZE +
                                             self.EXPOSURE_BAR_LABEL_SIZE +
                                             self.EXPOSURE_BAR_SPACE_SIZE)
        #set color of cr to black
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(position_of_bar, 0, self.EXPOSURE_BAR_SIZE,
                     height_of_screen)
        cr.fill()
        colors_to_use = 767
        #go though the bar adding a rectangle for each clolor shift
        #769
        self.placement_fudge = \
            math.floor(colors_to_use / self.NO_BLOCKS_IN_EXPOSURE_PLOT)
        for value in range(767):
            orignal_value = value
            r, g, b = 0.00000, 0.000000, 0.000000
            if value > 255:
                r = 1
                value -= 255
            else:
                bit = (1.0/255.0)
                r = ((1.0/255.0) * value)
                value = 0

            if value > 255:
                g = 1
                value -= 255
            else:
                g = ((1.0/255.0) * value)
                value = 0

            b = (1.0/255.0 * value)
            self.exposure_bar_mapping[orignal_value] = {'r': r, 'g': g, 'b': b}
            if orignal_value % self.placement_fudge == 0:
                cr.set_source_rgb(r, g, b)
                y = (height_of_screen -
                     ((height_of_screen / self.NO_BLOCKS_IN_EXPOSURE_PLOT)
                      * (orignal_value / self.placement_fudge )))
                cr.rectangle(position_of_bar, y, self.EXPOSURE_BAR_SIZE,
                             height_of_screen / self.NO_BLOCKS_IN_EXPOSURE_PLOT)
                cr.fill()

    def add_exposure_legend(self, cr):
        #ADD LEGEND
        height_of_screen = self.y_dim * self.RECTANGLE_SIZE['y']
        width_of_screen = self.x_dim * self.RECTANGLE_SIZE['x']
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Purisa",
                            cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        #put 10 labels to the colour mapping
        range_of_color_values = self.max_seen_value - self.min_seen_value
        per_setp = math.floor(range_of_color_values /
                              self.NO_COLOR_MAPPING_LABELS)
        for index in range(self.NO_COLOR_MAPPING_LABELS + 1):
            position = (per_setp * index) / self.placement_fudge
            y = (height_of_screen -
                (height_of_screen / self.NO_COLOR_MAPPING_LABELS) * index)
            x = (width_of_screen + self.EXPOSURE_BAR_SIZE +
                 (self.EXPOSURE_BAR_LABEL_SIZE / 2))
            cr.move_to(x, y)
            cr.show_text("{}".format(position))


    def size_allocate(self, widget, requisition):
        ''''
        when the size is allocated, redraw the drawing area
        '''
        #determine new size of a rectangle
        self.redraw_everything = True
        if len(self.objects_to_draw.keys()) != 0:
            width = requisition.width 
            height = requisition.height 
            x = (width - self.EXPOSURE_BAR_SIZE - self.EXPOSURE_BAR_LABEL_SIZE -
                self.EXPOSURE_BAR_SPACE_SIZE - self.LEGEND_SIZE['x'])
            x = math.floor(x / self.x_dim)
            y= math.floor((height - self.LEGEND_SIZE['y']) / self.y_dim)
            self.RECTANGLE_SIZE = {'x': x, 'y': y}
            #go through drawing objects updating new x,y width and height
            max_y_pos = self.y_dim * self.RECTANGLE_SIZE['y']
            for x in range(self.x_dim):
                for y in range(self.y_dim):
                    x_pos = (x * self.RECTANGLE_SIZE['x']) + self.LEGEND_SIZE['x']
                    y_pos = y * self.RECTANGLE_SIZE['y']
                    width = self.RECTANGLE_SIZE['x']
                    height = self.RECTANGLE_SIZE['y']
                    object_key = "{}:{}".format(x, y)
                    colour = self.objects_to_draw[object_key]['c']
                    y_pos = max_y_pos-self.LEGEND_SIZE['y']-y_pos
                    object_key = "{}:{}".format(int(x), int(y))
                    self.objects_to_draw[object_key] = {'x': int(x_pos),
                                                        'y': int(y_pos),
                                                        'w': int(width),
                                                        'h': int(height),
                                                        'c': colour}
            self.drawing_area.queue_draw()

    def redraw(self, timer_tic):
        '''
        method used by the main visualiser to promt this page to be redrawn
        '''
        if not self.drawing:
            self.drawing = True
            blocked_list = self.spikes_that_need_processing
            self.spikes_that_need_processing = list()
            for details in blocked_list:
                self.redraw_everything = False
                if getattr(self.vertex_in_question,
                           "get_packet_retina_coords", None) is not None:
                    x, y, spike_value = \
                        self.vertex_in_question.\
                            get_packet_retina_coords(details['spike_word'],
                                                     self.y_dim)
                else:
                    ##assuming its a normal pop with a topolgoical view, use x then y
                    x, y, spike_value = self.convert_normal_pop_spike_to_x_y(details['spike_word'])
                #translate spike value into a increase or decrease in color
                if spike_value != 1:
                    spike_value = -1

                #update the object
                object_key = "{}:{}".format(int(x), int(y))
                old_object = self.objects_to_draw[object_key]
                new_color = old_object['c'] + (spike_value * self.placement_fudge)
                #store it into min and maxes if needed
                if new_color < self.min_seen_value:
                    self.set_min_seen_value(new_color)
                if new_color > self.max_seen_value:
                    self.set_max_seen_value(new_color)

                new_object = {'x': old_object['x'],
                              'y': old_object['y'],
                              'w': old_object['w'],
                              'h': old_object['h'],
                              'c': new_color}
                #replace obect in drawable objects
                self.objects_to_draw[object_key] = new_object
                #track that this obejct needs redrawing
                self.new_entries.append(object_key)
            self.drawing_area.queue_draw()

    def recieved_spike(self, details):
        '''
        takes a spike detials and converts it into a update in the retina screen
        '''
        self.spikes_that_need_processing.append(details)

    def set_min_seen_value(self, new_value):
        '''
        this tracks the new min value until the next resetting of the color map
        '''
        if not self.needs_reseting:
            self.needs_reseting = True
        self.min_seen_value = new_value
       # print "newVal is {}, bool is set to {}".format(new_value, self.needs_reseting)


    def set_max_seen_value(self, new_value):
        '''
        this tracks the new max value until the next resetting of the color map
        '''
       # print "setting max to {}".format(new_value)
        if not self.needs_reseting:
            self.needs_reseting = True
        self.max_seen_value = new_value


    def convert_normal_pop_spike_to_x_y(self, spike_word):
        '''
        takes the spike_word (key) and converts it into a neuron id, for the vertex
        it then converts the neuron id into a x and y coord and adds one to the colour
        '''
        neuron_id = packet_conversions.get_nid_from_key(spike_word)
        x = packet_conversions.get_x_from_key(spike_word)
        y = packet_conversions.get_y_from_key(spike_word)
        p = packet_conversions.get_p_from_key(spike_word)
        subvert = self.locate_subvert(x, y, p)
        real_neuron_id = subvert.lo_atom + neuron_id
        x_coord = math.floor(real_neuron_id/self.y_dim)
        y_coord = real_neuron_id - (x_coord * self.y_dim)
        return x_coord, y_coord, 1

    def locate_subvert(self, x, y, p):
        '''
        given a x y and p, locates the subvert placed on that processor
        '''
        for placement in self.dao.placements:
            if (placement.processor.idx == (p+1) and
                placement.processor.chip.get_coords()[0] == x and
                placement.processor.chip.get_coords()[1] == y):
		
                return placement.subvertex
        return None

    def reset_values(self):
        for old_object_key in self.objects_to_draw.keys():
            old_object = self.objects_to_draw[old_object_key]
            new_object = {'x': old_object['x'],
                          'y': old_object['y'],
                          'w': old_object['w'],
                          'h': old_object['h'],
                          'c': 0}
            #replace obect in drawable objects
            self.objects_to_draw[old_object_key] = new_object

    def get_reset(self):
        if self.data is not None:
            return self.data
        else:
            return None

    def set_reset(self, data):
        self.data = data

