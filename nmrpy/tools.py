

#from traits.api import HasTraits, Instance, Enum, Range, List, Int, Array
import traits.api as traits
from traitsui.api import View, Item, CheckListEditor, TabularEditor, HGroup, UItem, TabularEditor, Group, Handler
from chaco.api import Plot, MultiArrayDataSource, ArrayPlotData
from chaco.tools.api import PanTool, ZoomTool, BetterZoom, DragTool, RangeSelection, LineInspector, RangeSelectionOverlay
from enable.component_editor import ComponentEditor
import numpy as np
from traitsui.tabular_adapter import TabularAdapter
from matplotlib import cm
from enable.api import KeySpec

class TC_Handler(Handler):

    #def ph_man_btn_changed(self, info):
    #    if info.initialized:
    #        print info
    #        info.ui.title += "*"

    #called when any trait attribute value is changed
    def setattr(self, info, object, name, value):
        #if object._manphasing and name != 'ph_man_btn':
        #    print name, value
        #    return

        Handler.setattr(self, info, object, name, value)
        #if name == 'ph_man_btn':
        #    if not object._manphasing:
        #        info.ph_man_btn.label = 'Manual'
        #    elif object._manphasing:
        #        info.ph_man_btn.label = 'Manual*'


        if name == 'ft_btn':
            if object.fid._ft:
                info.ft_btn.label = 'FT*'

    #def object__updated_changed(self, info):
    #    if info.initialized:
    #        info.ui.title += "*"


class MultiSelectAdapter(TabularAdapter):

    # Titles and column names for each column of a table.
    # In this example, each table has only one column.
    columns = [ ('index', 'myvalue') ]

    # Magically named trait which gives the display text of the column named
    # 'myvalue'. This is done using a Traits Property and its getter:
    myvalue_text = traits.Property
    # The getter for Property 'myvalue_text' simply takes the value of the
    # corresponding item in the list being displayed in this table.
    # A more complicated example could format the item before displaying it.
    def _get_myvalue_text(self):
        return self.item

class PhaseDragTool(DragTool):

    end_drag_on_leave = True
    # The mouse button that initiates the drag.
    drag_button = traits.Enum('left', 'right') #WTF?!?!?!?!
    p0 = 0.0
    p1 = 0.0
 
    def drag_start(self, event):
        self._start_xy = [event.x, event.y]
        event.handled = True
 
    def drag_end(self, event):
        plot = self.component
        plot._data_complex = plot._data
        self.p0 += self._p0
        self.p1 += self._p1
        event.handled = True
 
    def drag_leave(self, event):
        event.handled = True
 
    def drag_cancel(self, event):
        event.handled = True
 
    def dragging(self, event):
        plot = self.component
        plot._data = plot._data_complex.copy()
        self._current_xy = [event.x-self._start_xy[0], event.y-self._start_xy[1]]
        self._p0, self._p1 = [0.0, 0.0]
        if self.drag_button == 'left':
            self._p0 += 100.0*self._current_xy[1]/plot.height
            self._p1 += 100.0*self._current_xy[0]/plot.height
        if self.drag_button == 'right':
            self._p1 += self._current_xy[1]
        plot._data = plot._ps(plot._data, p0=self._p0, p1=self._p1)
        for i in range(len(plot._data)):
            plot.data.set_data('series%i'%(plot._data_selected[i]+1), np.real(plot._data[i]))
        plot.request_redraw()
        event.handled = True
 
    def normal_mouse_enter(self, event):
        event.handled = True
 
    def normal_mouse_leave(self, event):
        event.handled = True

class BlSelectTool(RangeSelection):
    bl_selections = traits.List()

    def normal_left_down(self, event):
        pass

    def selected_left_down(self, event):
        pass

    def selecting_right_up(self, event):
        self.bl_selections.append(self.selection)
        self.event_state = 'selected'


class DataPlotter(traits.HasTraits):
    plot = traits.Instance(Plot) #the attribute 'plot' of class DataPlotter is a trait that has to be an instance of the chaco class Plot.
    plot_data = traits.Instance(ArrayPlotData)
    data_index = traits.List(traits.Int)
    data_selected = traits.List(traits.Int)

    y_offset = traits.Range(0.0,20.0, value=0)
    x_offset = traits.Range(-10.0,10.0, value=0)
    y_scale = traits.Range(1e-3,2.0, value=1.0)
    x_range_up = traits.Float()
    x_range_dn = traits.Float()
    x_range_btn = traits.Button(label='Set range')

    reset_plot_btn = traits.Button(label='Reset plot')
    select_all_btn = traits.Button(label='All')
    select_none_btn = traits.Button(label='None')

    #processing
    lb = traits.Float(10.0)
    lb_btn = traits.Button(label='Apodisation')
    lb_plt_btn = traits.Button(label='Plot Apod.')
    zf_btn = traits.Button(label='Zero-fill')
    ft_btn = traits.Button(label='FT')

    ph_auto_btn = traits.Button(label='Auto: all')
    ph_auto_single_btn = traits.Button(label='Auto: selected')
    ph_man_btn = traits.Button(label='Manual')
    ph_global = traits.Bool(label='apply globally')
    _manphasing = False
    _bl_selecting = False 


    bl_cor_btn = traits.Button(label='BL correct')
    bl_sel_btn = traits.Button(label='Select points')

#    def _metadata_handler(self):                                                                                                
#        blah = self.index_datasource.metadata#.get('selections')
#        print blah


    def __init__(self, fid):
        super(DataPlotter, self).__init__()
        self.fid = fid
        data = fid.data
        self.data_index = range(len(data))
        if self.fid._ft:
            self.x = np.linspace(self.fid.params['sw_left'], fid.params['sw_left']-fid.params['sw'], len(self.fid.data[0]))#range(len(self.data[0]))
            self.plot_data = ArrayPlotData(x=self.x, *np.real(data)) #chaco class Plot require chaco class ArrayPlotData
            plot = Plot(self.plot_data, default_origin='bottom right', padding=[5, 0, 0, 35])
        else: 
            self.x = np.linspace(0, self.fid.params['at'], len(self.fid.data[0]))
            self.plot_data = ArrayPlotData(x=self.x, *np.real(data)) #chaco class Plot require chaco class ArrayPlotData
            plot = Plot(self.plot_data, default_origin='bottom left', padding=[5, 0, 0, 35])
        self.plot = plot
        self.plot_init()
        
    def plot_init(self, index=[0]):
        if self.fid._ft:
            self.plot.x_axis.title = 'ppm.'
        else:
            self.plot.x_axis.title = 'sec.'
        self.zoomtool = BetterZoom(self.plot, zoom_to_mouse=False, x_min_zoom_factor=1, zoom_factor=1.5)
        self.pantool = PanTool(self.plot)
        self.phase_dragtool = PhaseDragTool(self.plot)
        self.plot.tools.append(self.zoomtool)
        self.plot.tools.append(self.pantool)
        self.plot.y_axis.visible = False
        for i in index:
            self.plot.plot(('x', 'series%i'%(i+1)), type='line', line_width=0.5, color='black')[0]
        self.plot.request_redraw()
        self.old_y_scale = self.y_scale
        self.index_array = np.arange(len(self.fid.data))
        self.y_offsets = self.index_array * self.y_offset
        self.x_offsets = self.index_array * self.x_offset
        self.data_selected = index
        self.x_range_up = round(self.x[0], 3)
        self.x_range_dn = round(self.x[-1], 3)
        #this is necessary for phasing:
        self.plot._ps = self.fid.ps
        self.plot._data_complex = self.fid.data
        
#        my_plot = self.plot.plots["plot0"][0]
#        # Set up the trait handler for the selection       
#        self.index_datasource = my_plot.index
#        self.index_datasource.on_trait_change(self._metadata_handler,
#                                         "metadata_changed")
        

    def _x_range_btn_fired(self):
        if self.x_range_up < self.x_range_dn:
            xr = self.x_range_up
            self.x_range_up = self.x_range_dn
            self.x_range_dn = xr
        self.set_x_range(up=self.x_range_up, dn=self.x_range_dn)
        self.plot.request_redraw()

    def set_x_range(self, up=x_range_up, dn=x_range_dn):
        if self.fid._ft:
            self.plot.index_range.high = up
            self.plot.index_range.low = dn
        else:
            self.plot.index_range.high = dn
            self.plot.index_range.low = up
        pass

    def _y_scale_changed(self):
        self.set_y_scale(scale=self.y_scale)

    def set_y_scale(self, scale=y_scale):
        self.plot.value_range.high /= scale/self.old_y_scale
        self.plot.request_redraw()
        self.old_y_scale = scale

    def reset_plot(self):
        self.x_offset, self.y_offset = 0, 0
        self.y_scale = 1.0
        if self.fid._ft:
            self.plot.index_range.low, self.plot.index_range.high = [self.x[-1], self.x[0]]
        else:
            self.plot.index_range.low, self.plot.index_range.high = [self.x[0], self.x[-1]]
        self.plot.value_range.low = self.plot.data.arrays['series%i'%(self.data_selected[0]+1)].min()
        self.plot.value_range.high = self.plot.data.arrays['series%i'%(self.data_selected[0]+1)].max()
        #add pan resetting

    def _reset_plot_btn_fired(self):
        print 'resetting plot...'
        self.reset_plot()

    def _select_all_btn_fired(self):
        self.data_selected = range(len(self.fid.data))

    def _select_none_btn_fired(self):
        self.data_selected = []

    def set_plot_offset(self, x=None, y=None):
        if x==None and y==None:
            pass

        self.old_x_offsets = self.x_offsets
        self.old_y_offsets = self.y_offsets
        self.x_offsets = self.index_array * x
        self.y_offsets = self.index_array * y
        for i in np.arange(len(self.plot.plots)):
            self.plot.plots['plot%i'%i][0].position = [self.x_offsets[i], self.y_offsets[i]]
        self.plot.request_redraw()

    def _y_offset_changed(self):
        self.set_plot_offset(x=self.x_offset, y=self.y_offset)

    def _x_offset_changed(self):
        self.set_plot_offset(x=self.x_offset, y=self.y_offset)

    #for some mysterious reason, selecting new data to plot doesn't retain the plot offsets even if you set them explicitly
    def _data_selected_changed(self):
        #check if we're in manphasing mode
        if self._manphasing:
            self.end_man_phasing()

        self.plot.delplot(*self.plot.plots)
        self.plot.request_redraw()
        for i in self.data_selected:
            self.plot.plot(('x', 'series%i'%(i+1)), type='line', line_width=0.5, color='black', position=[self.x_offsets[i], self.y_offsets[i]]) #FIX: this isn't working
        #self.reset_plot() # this is due to the fact that the plot automatically resets anyway
        
    #processing buttons

    #plot the current apodisation function based on lb, and do apodisation
    #=================================================
    def _lb_plt_btn_fired(self):
        if self.fid._ft:
            return
        if 'lb1' in self.plot.plots:
        #if 'lb1' in self.plot_data.arrays:
            #self.plot_data.del_data('lb1')
            self.plot.delplot('lb1')
            self.plot.request_redraw()
            return
        self.plot_lb()

    def plot_lb(self):
        if self.fid._ft:
            return
        lb_data = self.fid.data[self.data_selected[0]]
        lb_plt = np.exp(-np.pi*np.arange(len(lb_data))*(self.lb/self.fid.params['sw_hz'])) * lb_data[0]
        self.plot_data.set_data('lb1', np.real(lb_plt))
        self.plot.plot(('x', 'lb1'), type='line', name='lb1', line_width=1, color='blue')[0]
        self.plot.request_redraw()

    def _lb_changed(self):
        if self.fid._ft:
            return
        lb_data = self.fid.data[self.data_selected[0]]
        lb_plt = np.exp(-np.pi*np.arange(len(lb_data))*(self.lb/self.fid.params['sw_hz'])) * lb_data[0]
        self.plot_data.set_data('lb1', np.real(lb_plt))

    def _lb_btn_fired(self):
        if self.fid._ft:
            return
        self.fid.emhz(self.lb)
        self.update_plot_data_from_fid()
    #=================================================

    def _zf_btn_fired(self):
        if self.fid._ft:
            return
        if 'lb1' in self.plot.plots:
            self.plot.delplot('lb1')
        self.fid.zf()
        self.update_plot_data_from_fid()

    def _ft_btn_fired(self):
        if 'lb1' in self.plot.plots:
            self.plot.delplot('lb1')
        if self.fid._ft:
            return
        self.fid.ft()
        self.update_plot_data_from_fid()
        self.plot = Plot(self.plot_data, default_origin='bottom right', padding=[5, 0, 0, 35])
        self.plot_init(index=self.data_selected)
        self.reset_plot()

    def _ph_auto_btn_fired(self):
        if not self.fid._ft:
            return
        self.fid.phase_auto(discard_imaginary=False)
        self.update_plot_data_from_fid()

    def _ph_auto_single_btn_fired(self):
        if not self.fid._ft:
            return
        for i in self.data_selected:
            self.fid._phase_area_single(i)
        self.update_plot_data_from_fid()

    def _ph_man_btn_fired(self):
        if not self.fid._ft:
            return
        if not self._manphasing:
            self._manphasing = True
            self.change_plot_colour(colour='red')
            self.disable_plot_tools()
            self.plot._data_selected = self.data_selected
            self.plot._data_complex = self.fid.data[np.array(self.data_selected)]
            self.plot.tools.append(PhaseDragTool(self.plot))
        elif self._manphasing:
            self.end_man_phasing()

    def end_man_phasing(self):
        self._manphasing = False
        self.change_plot_colour(colour='black')
        if self.ph_global:
            self.fid.data = self.fid.ps(self.fid.data, p0=self.plot.tools[0].p0, p1=self.plot.tools[0].p1)
            self.update_plot_data_from_fid()
        else:    
            for i, j in zip(self.plot._data_selected, self.plot._data_complex):
                self.fid.data[i] = j 
        self.disable_plot_tools()
        self.enable_plot_tools()


    def remove_extra_overlays(self):
        self.plot.overlays = [self.plot.overlays[0]]

    def disable_plot_tools(self):
        self.plot.tools = []

    def enable_plot_tools(self):
        self.plot.tools.append(self.zoomtool)
        self.plot.tools.append(self.pantool)

    def change_plot_colour(self, colour='black'):
        for plot in self.plot.plots:
            self.plot.plots[plot][0].color = colour

    def _bl_sel_btn_fired(self):
        if not self.fid._ft:
            return
        if self._bl_selecting:
            self.end_bl_select()
        else:
            self._bl_selecting = True
            self.plot.plot(('x', 'series%i'%(self.data_selected[0]+1)), name='bl_plot', type='scatter', alpha=0.5, line_width=0, selection_line_width=0, marker_size=2, selection_marker_size=2, selection_color='red', color='black')[0]
            #self.change_plot_colour(colour='red')
            self.disable_plot_tools()
            self.plot.tools.append(BlSelectTool(self.plot.plots['plot0'][0],
                                            left_button_selects=True,
                                            metadata_name='selections',
                                            append_key=KeySpec(None, 'control')))
            self.plot.overlays.append(RangeSelectionOverlay(component=self.plot.plots['bl_plot'][0],
                                            metadata_name='selections',
                                            axis='index',
                                            fill_color="blue"))
            self.plot.overlays.append(LineInspector(component=self.plot,
                                                 axis='index_x',
                                                 inspect_mode="indexed",
                                                 write_metadata=True,
                                                 color="blue"))

    def end_bl_select(self):
        self._bl_selecting = False
        self._bl_ranges = self.plot.tools[0].bl_selections
        self._bl_indices = []
        for i, j   in self._bl_ranges:
            print i, j
            self._bl_indices.append((i < self.x) * (self.x < j))
        self.fid.bl_points = np.where(sum(self._bl_indices, 0)==1)[0]
        self.plot.delplot('bl_plot')
        self.plot.request_redraw()
        self.remove_extra_overlays()
        self.disable_plot_tools()
        self.enable_plot_tools()

    def _bl_cor_btn_fired(self):
        if not self.fid._ft:
            return
        if self._bl_selecting:
            self.end_bl_select()
        self.fid.bl_fit() 
        self.update_plot_data_from_fid() 

    def update_plot_data_from_fid(self, index=None):
        if self.fid._ft:
            self.x = np.linspace(self.fid.params['sw_left'], self.fid.params['sw_left']-self.fid.params['sw'], len(self.fid.data[0]))
        else:
            self.x = np.linspace(0, self.fid.params['at'], len(self.fid.data[0]))
        self.plot_data.set_data('x', self.x)
        if index == None:
            for i in self.index_array:
                self.plot_data.set_data("series%i"%(i+1), np.real(self.fid.data[i]))
        else:
            self.plot_data.set_data("series%i"%(index+1), np.real(self.fid.data[index]))
        self.plot.request_redraw()


    def default_traits_view(self):
        traits_view = View(Group(
                                Group(
                                    Item('data_index',
                                          editor     = TabularEditor(
                                                           show_titles  = False,
                                                           selected     = 'data_selected',
                                                           editable     = False,
                                                           multi_select = True,
                                                           adapter      = MultiSelectAdapter()),
                                    width=0.02, show_label=False, has_focus=True),
                                    Item(   'plot',
                                            editor=ComponentEditor(),
                                            show_label=False),
                                            padding=0,
                                            show_border=False,
                                            orientation='horizontal'),
                                Group(
                                    Group(
                                        Group(
                                            Item('select_all_btn', show_label=False),
                                            Item('select_none_btn', show_label=False),
                                            Item('reset_plot_btn', show_label=False),
                                            orientation='vertical'),
                                        Group(
                                            Item('y_offset'),
                                            Item('x_offset'),
                                            Item('y_scale', show_label=True),
                                            Group(
                                            Item('x_range_btn', show_label=False),
                                            Item('x_range_up', show_label=False),
                                            Item('x_range_dn', show_label=False), orientation='horizontal'),
                                            orientation='vertical'), orientation='horizontal', show_border=True, label='Plotting'),
                                    Group(
                                        Group(
                                            Item('lb', show_label=False, format_str='%.2f Hz'),
                                            Item('lb_btn', show_label=False),
                                            Item('lb_plt_btn', show_label=False),
                                            orientation='horizontal'),
                                            Group(
                                            Item('zf_btn', show_label=False),
                                            Item('ft_btn', show_label=False),
                                            orientation='horizontal'),
                                        Group(
                                            Item('bl_cor_btn', show_label=False),
                                            Item('bl_sel_btn', show_label=False),
                                            orientation='horizontal',
                                            show_border=True,
                                            label='Baseline correction'),
                                        Group(
                                            Item('ph_auto_btn', show_label=False),
                                            Item('ph_auto_single_btn', show_label=False),
                                            Item('ph_man_btn', show_label=False),
                                            Item('ph_global', show_label=True),
                                            orientation='horizontal',
                                            show_border=True,
                                            label='Phase correction'),
                                            show_border=True, label='Processing'),
                                        show_border=True,
                                    orientation='horizontal')
                                        ),
                            width=1.0,
                            height=0.8,
                            resizable=True,
                            handler=TC_Handler(),
                            title='NMRPy')
        return traits_view



#class MainWindow(traits.HasTraits):
#    data_plotter = traits.Instance(DataPlotter,())
#
#    traits_view = View(
#                        Item('data_plotter', show_label=False),
#                        width=200, height=400, resizable=True, title='blah')
#    def __init__(self, fid):
#        super(MainWindow,self).__init__()
#        self.data_plotter = DataPlotter(fid)


if __name__ == "__main__":
    print 'This module has to be imported as a submodule of nmrpy'
    pass
