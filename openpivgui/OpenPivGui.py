#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''A simple GUI for OpenPIV.'''

import openpivgui.vec_plot as vec_plot
from openpivgui.open_piv_gui_tools import (str2list, str2dict, get_dim, _round,
    add_disp_roi, add_disp_mask, save)
from openpivgui.ErrorChecker import check_PIVprocessing, check_processing
from openpivgui.PostProcessing import ValidateResults, ModifyResults
from openpivgui.PreProcessing import gen_background, process_images
from openpivgui.MultiProcessing import MultiProcessing
from openpivgui.CreateToolTip import CreateToolTip
from openpivgui.OpenPivParams import OpenPivParams
from openpiv.preprocess import mask_coordinates
from matplotlib.figure import Figure as Fig
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk)
from matplotlib.widgets import RectangleSelector, PolygonSelector
import matplotlib.pyplot as plt
import matplotlib.path as Path
import openpiv.tools as piv_tls
import pandas as pd
import pickle
import numpy as np
from PIL import ImageDraw, Image
from skimage import measure
from tkinter import colorchooser
from datetime import datetime
import threading
import shutil
import webbrowser
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
import tkinter.filedialog as filedialog
import tkinter as tk
import inspect
import json
import math
import sys
import re
import os

__version__ = '0.1.4'

__licence__ = '''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

__email__ = 'vennemann@fh-muenster.de'


class OpenPivGui(tk.Tk):
    '''OpenPIV GUI

    Usage:

    1. Press »File« and then »Import files« or »Import directory«. 
       Either select some image pairs (Ctrl + Shift) or a directory
       that contains image files.

    2. Click on the links in the file-list on the right to inspect
       the images.

    3. Walk through the drop-down-menues »General«, »Preprocessing«,
       and »Analysis« and edit the parameters. 

    4. Press the »start processing« butten (bottom left), to 
       start the processing chain.

    5. Inspect the results by clicking on the links in the file-list.
       Use the »Plot« drop-down menu for changing the plot parameters.

    6. Use the »back« and »forward« buttons to go back to the images,
       in case you want to repeat the evaluation.

    7. For post-processing, use the »back« and »forward« buttons« 
       to list the vector files. Modify the Post-Processing
       parameters and hit the »start post-processing« button.

    See also:

    https://github.com/OpenPIV/openpiv_tk_gui
   '''

    def __init__(self):
        '''Standard initialization method.'''
        print('Initializing GUI')
        self.VERSION = __version__
        self.TITLE = 'OpenPIV 0.23.4, GUI version'
        tk.Tk.__init__(self)
        self.path = os.path.dirname(
            os.path.abspath(__file__))  # path of gui folder
        self.icon_path = os.path.join(
            self.path, 'res/icon.png')  # path for image or icon
        # convert .png into a usable icon photo
        self.iconphoto(False, tk.PhotoImage(file=self.icon_path))
        self.title(self.TITLE + ' ' + self.VERSION)
        # handle for user closing GUI through window manager
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        # the parameter object
        self.p = OpenPivParams()
        self.p.load_settings(self.p.params_fname)
        # background variable for widget data:
        self.tkvars = {}
        # handle for settings frames on riders
        self.set_frame = []
        # handle for ttk widgets that have state changes
        self.ttk_widgets = {}
        # handle for text-area objects
        self.ta = []
        # handle for list-boxes
        self.lb = None
        # handle for masks
        self.mask_counter = 0
        self.object_mask = []
        # handle for frame widths
        self.frame_width = 250
        # widgets and others
        print('Initializing widgets')
        # handle for background color
        self.b_color = self.cget('bg')
        self.toggle = 'a'
        self.index = 0
        self.create_session()
        # padding settings
        self.padx = 9
        self.pady = 2
        self.sub_padx = 3
        self.sub_pady = 2
        # button widths
        self.large_button_width = 25
        self.small_button_width = 11
        self.__init_widgets()
        self.reset_params(do_menu = False)
        self.overlap_percent = 0.5
        self.set_windowing(0)
        self.update_widget_state()
        self.ttk_widgets['show_masked_vectors'].config(state = 'disabled')
        mem = False
        # attempt to load first image
        try:
            self.show(self.session['files_' + self.toggle][0])
            mem = True
        except:
            mem = False # no images loaded/no frequencing applied
        if mem != True:
            self.update_widget_state2(state = 'disabled')
        self.log(timestamp=True, text='--------------------------------' +
                                      '\nTkinter OpenPIV session started.')
        self.log(text='OpenPivGui version: ' + self.VERSION)
        print('Initialized GUI, ready for processing')

        
        
    def start_processing(self, frame = None):
        '''Wrapper function to start processing in a separate thread.'''
        try:
            self.get_settings()
            check_processing(self)  # simple error checking.
            check_PIVprocessing(self.p, self.session)
            self.processing_thread = threading.Thread(target=self.processing)
            if frame != None:
                self.process_channel = [self.session['files_a'][frame],
                                        self.session['files_b'][frame]]
            self.p['analyze_frame_index'] = frame
            self.processing_thread.start()
        except Exception as e:
            print('PIV evaluation thread stopped. ' + str(e))
            

            
    def processing(self):
        try: # if an error occurs, GUI will not lock up
            self.disable_widgets(exclude_tab = 4)
            self.ttk_widgets['clear_results'].config(state = 'normal',
                                                    text = 'Stop analysis',
                                                    command = self.stop_analysis)
            self.p['analysis'] = True
            self.log(timestamp=True,
                     text='-----------------------------' +
                     '\nPre processing finished.',
                     group=self.p.PREPROC)
            '''Start the processing chain.
            This is the place to implement additional function calls.
            '''
            # parallel PIV evaluation:
            print('Starting evaluation.')
            self.progressbar.start()
            self.get_settings()
            mp = MultiProcessing(self.p, self.session)

            # keep number of cores in check
            if os.cpu_count() == 0:  # if there are no cored available, then raise exception
                raise Exception('Warning: no available threads to process in.')

            #if self.p['manual_select_cores']:  # multiprocessing disabled until results are  properly eppended to dict.
            #    cpu_count = self.p['cores']
            #else:
            #    cpu_count = os.cpu_count()

            #if "idlelib" in sys.modules:
            #    self.log('Running as a child of IDLE: ' +
            #             'Deactivated multiprocessing.')
            #    cpu_count = 1

            #if cpu_count >= os.cpu_count():
            #    raise Exception('Please lower the amount of cores ' +
            #                    'or deselect >manually select cores<.')
            
            cpu_count = 1
            print('Cores left: {} of {}.'.format(
                (os.cpu_count() - cpu_count), os.cpu_count()))
            
            
            if self.p['analyze_frame_index'] != None:
                number_of_frames = 1
                self.process_type.config(text = f'Processing frame {self.index}')
                mp.process(args = (self.process_channel[0],
                                   self.process_channel[1],
                                   self.p['analyze_frame_index']))
                text = f'Processed frame {self.index}'
                
            else:
                number_of_frames = mp.get_num_frames()
                self.process_type.config(text = f'Processing {number_of_frames} frames(s)')
                mp._run(func = mp.process, n_cpus = cpu_count)
                
                text = f'Processed {number_of_frames} frames(s)'

            # update file list with result vector files:
            self.log(timestamp=True,
                     text='\nPIV evaluation finished.',
                     group=self.p.PIVPROC)

            self.progressbar.stop()
            self.enable_widgets()
            self.ttk_widgets['clear_results']['command'] = self.clear_results
            self.ttk_widgets['clear_results'].config(text = 'Clear all results')
            self.process_type.config(text = text)
           #self.show(self.session['files_' + self.toggle][self.index])
            
        except Exception as e:
            print('PIV evaluation thread stopped. ' + str(e))
            self.progressbar.stop()
            self.enable_widgets()
            #self.clear_results(update_plot = False)
            self.ttk_widgets['clear_results']['command'] = self.clear_results
            self.ttk_widgets['clear_results'].config(text = 'Clear all results')
            self.process_type.config(text = 'Failed to process frame(s)')
                

                
    def start_postprocessing1(self, index = None):
        '''Wrapper function to start processing in a separate thread.'''
        try:
            check_processing(self)
            self.postprocessing_thread1 = threading.Thread(
                target=self.postprocessing1)
            
            if index == None:
                self.validate_frame = None
            else:
                self.validate_frame = self.session['results'][f'{self.index}']
                
            self.postprocessing_thread1.start()
        except Exception as e:
            print('Stopping current processing thread \nReason: ' + str(e))

            
            
    def postprocessing1(self):
        try:
            #self.process_type.config(text = 'Processing {} PIV result(s)'.format(len(self.p['fnames'])))
            self.get_settings()
            
            if self.validate_frame != None:
                print('Validating frame ' + str(self.index))
                results = self.session['results'][f'{self.index}']
                _, _, _ = ValidateResults(self.p, 
                                           u = results[4], 
                                           v = results[5], 
                                           tp = results[6])
               # results += [u_val, v_val, tp_val]
            
            else:
                print('Validating all frames')
                for i in range(len(self.session['files_a'])):
                    results = self.session['results'][f'{i}']
                    _, _, _ = ValidateResults(
                        self.p, 
                        u = results[4], 
                        v = results[5], 
                        tp = results[6]
                    )
                    #results += [u_val, v_val, tp_val]
                    print(f'Finished validating frame {i}')
                
            # log validation parameters
            if (self.p['vld_global_std'] or
                self.p['vld_global_thr'] or
                self.p['vld_local_med'] or
                self.p['repl']):
                self.log(timestamp=True,
                         text='\nValidation finished.',
                         group=self.p.VALIDATION)
            print('Finished validation(s)')
        except Exception as e:
            print('Stopping current processing thread \nReason: ' + str(e))
            
            

    def start_postprocessing2(self, index = None):
        '''Wrapper function to start processing in a separate thread.'''
        try:
            check_processing(self)
            self.postprocessing_thread2 = threading.Thread(
                target = self.postprocessing2)
            
            if index == None:
                self.derive_frame = None
            else:
                self.derive_frame = self.session['results'][f'{self.index}']
                
            self.postprocessing_thread2.start()
        except Exception as e:
            print('Stopping current processing thread \nReason: ' + str(e))

            
            
    def postprocessing2(self):
        try:
            #self.process_type.config(text = 'Processing {} PIV result(s)'.format(len(self.p['fnames'])))
            self.get_settings()
            
            if self.derive_frame != None:
                print('Deriving/modifying frame ' + str(self.index))
                results = self.session['results'][f'{self.index}']
                u, v, tp = ValidateResults(self.p, 
                                           u = results[4], 
                                           v = results[5], 
                                           tp = results[6])
                #results += [u, v, tp]
            
            else:
                for i in range(int(self.session['frame_num']) + 1):
                    results = self.session['results'][f'{i}']
                    x_off, y_off, u_mod, v_mod, u_smth, v_smth, = ModifyResults(
                        self.p, 
                        x = results[2],
                        y = results[3],
                        u = results[4], 
                        v = results[5], 
                    )
                   # results += [x_off, y_off, u_mod, v_mod]
            
                    if (self.p['smoothn']):
                        #results += [u_smth, v_smth]
                        pass

            if (self.p['smoothn'] or
                self.p['average_results']):
                self.log(timestamp=True,
                         text='\nModifying components finished.',
                         group=self.p.POSTPROC)
            print('Finished postprocessing.')

            #self.process_type.config(text = 'Processed {} PIV result(s)'.format(len(self.p['fnames'])))
        except Exception as e:
            print('Stopping current processing thread \nReason: ' + str(e))
            

    def __init_widgets(self):
        '''Creates a widget for each variable in a parameter object.'''
        self.__init_buttons()
        f = ttk.Frame(self)
        f.pack(side='left',
               fill='both',
               expand='True')
        # holds riders for parameters
        self.__init_notebook(f)
        # plotting area
        self.__init_fig_canvas(f)
        # variable widgets:
        for key in sorted(self.p.index, key=self.p.index.get):
            if self.p.type[key] == 'dummy':
                pass
            elif self.p.type[key] == 'dummy2':
                pass
            elif self.p.type[key] == 'bool':
                self.__init_checkbutton(key)
            elif self.p.type[key] == 'str[]':
                self.__init_listbox(key)
            elif self.p.type[key] == 'text':
                self.__init_text_area(key)
            elif self.p.type[key] == 'labelframe':
                self.__init_labelframe(key)
            elif self.p.type[key] == 'label':
                self.__init_label(key)
            elif self.p.type[key] == 'h-spacer':
                self.__init_horizontal_spacer(key)
            elif self.p.type[key] == 'sub_bool':
                self.__init_sub_checkbutton(key)
            elif self.p.type[key] == 'sub_bool2':
                self.__init_sub_checkbutton2(key)
            elif self.p.type[key] == 'sub_button2':
                self.__init_sub_button2(key) 
            elif self.p.type[key] == 'sub_labelframe':
                self.__init_sub_labelframe(key)
            elif self.p.type[key] == 'sub_h-spacer':
                self.__init_sub_horizontal_spacer(key)
            elif self.p.type[key] is None:
                self.__add_tab(key)
            else:
                self.__init_entry(key)

            # create widgets that are not in OpenPivParams
            if self.p.index[key] == 1020:
                self.__init_load_img_button(key)
            elif self.p.index[key] == 1040:
                self.__init_apply_frequence_button(key)
            elif self.p.index[key] == 2010:
                self.__init_ROI()
            elif self.p.index[key] == 2020:
                self.__init_mask()
            elif self.p.index[key] == 2025:
                self.__init_background()
            elif self.p.index[key] == 2035:
                self.__init_background_apply()
            elif self.p.index[key] == 2240:
                self.__init_apply_preproc()
            elif self.p.index[key] == 3015:
                self.__init_windowing_hint()
            elif self.p.index[key] == 3090:
                self.__init_analyze_buttons()
            elif self.p.index[key] == 3455:
                self.__init_val_set_first_pass()
            elif self.p.index[key] == 5010:
                self.__init_load_calibration_button() # load and select reference distance
            elif self.p.index[key] == 5040:
                self.__init_apply_calibration_button() # clear or apply buttons
            elif self.p.index[key] == 6011:
                self.__init_set_vel_limits_button()
            elif self.p.index[key] == 6016:
                self.__init_apply_glob_val_first_pass_button()
            elif self.p.index[key] == 6110:
                self.__init_apply_validation_button()
            elif self.p.index[key] == 7110:
                self.__init_apply_modify_compon_button()
            elif self.p.index[key] == 8530:
                self.__init_vec_colorpicker(key)
            elif self.p.index[key] == 8630:
                self.__init_exclusions_preferences()
            elif self.p.index[key] == 11010:
                self.__init_export_ASCI2()
                

    def __init_fig_canvas(self, mother_frame):
        '''Creates a plotting area for matplotlib.

        Parameters
        ----------
        mother_frame : ttk.Frame
            A frame to place the canvas in.
        '''
        self.fig = Fig()
        self.fig_frame = ttk.Frame(mother_frame)
        self.fig_frame.pack(side='left',
                            fill='both',
                            expand='True')
        self.fig_canvas = FigureCanvasTkAgg(
            self.fig, master=self.fig_frame)
        self.fig_canvas.draw()
        self.fig_canvas.get_tk_widget().pack(
            side='left',
            fill='x',
            expand='True')
        
        self.fig_toolbar = NavigationToolbar2Tk(self.fig_canvas,
                                           self.fig_frame)
        remove = [2,3,4]
        for i in remove:
            self.fig_toolbar.children['!button%1d' % i].pack_forget()
            
        self.fig_toolbar.update()
        ttk.Button(self.fig_frame, 
                   text = '% invalid vectors', 
                   command = self.calculate_invalid_vectors).pack(side = 'left')   
        
        self.fig_canvas._tkcanvas.pack(side='top',
                                       fill='both',
                                       expand='True')
        self.fig_canvas.mpl_connect("key_press_event",
                                    lambda: key_press_handler(event,
                                                              self.fig_canvas,
                                                              self.fig_toolbar))

    def __fig_toolbar_key_pressed(self, event):
        '''Handles matplotlib toolbar events.'''
        key_press_handler(event,
                          self.fig_canvas,
                          self.fig_toolbar)

    def __init_notebook(self, mother_frame):
        '''The notebook is the root widget for tabs or riders.'''
        style = ttk.Style()
        style.configure('lefttab.TNotebook', tabposition='es')
        style.layout('TNotebook.Tab', [])
        self.nb = ttk.Notebook(mother_frame, 
                               style = 'lefttab.TNotebook',
                               width=self.frame_width)
        
        self.nb.pack(side='right',
                     fill='y',
                     expand='False')

    def __add_tab(self, key):
        '''Add an additional rider to the notebook.'''
        self.set_frame.append(ttk.Frame(self.nb))
        self.nb.add(self.set_frame[-1], 
                    text='')

    def __init_buttons(self):
        '''Add buttons and bind them to methods.'''
        f = ttk.Frame(self)
        files = ttk.Menubutton(f, text='File')
        options = tk.Menu(files, tearoff=0)
        files.config(menu = options)
        submenu = tk.Menu(options, tearoff=0)
        submenu.add_command(label = 'images',
                            command = lambda: self.selection(0))
        submenu.add_command(label = 'settings',
                            command = self.load_settings)
        submenu.add_command(label = 'session',
                            command = self.load_session)
        options.add_cascade(label='Load', menu=submenu)
        options.add_separator()
        submenu = tk.Menu(options, tearoff = 0)
        submenu.add_command(label='settings', command = lambda: self.p.dump_settings(
            filedialog.asksaveasfilename(
                title = 'Settings Manager',
                defaultextension = '.json',
                filetypes = [('json', '*.json'), ]
            )))
        submenu.add_command(label='session', command = lambda: self.p.dump_session(
            filedialog.asksaveasfilename(
                title = 'Session Manager',
                defaultextension = '.npy',
                filetypes = [('npy', '*.npy'), ]),
            session_dict = self.session))
        options.add_cascade(label='Save', menu=submenu)
        options.add_separator()
        submenu = tk.Menu(options, tearoff=0)
        submenu.add_command(label='ASCI-II', command = lambda: self.selection(16))
        #submenu.add_command(label='TecPlot')
        #submenu.add_command(label='ParaView')
        options.add_cascade(label='Export', menu=submenu)
        options.add_separator()
        submenu = tk.Menu(options, tearoff=0)
        submenu.add_command(label='settings', command = self.reset_params)
        submenu.add_command(label='session', command = self.reset_session)
        options.add_cascade(label='Reset', menu=submenu)
        options.add_separator()

        options.add_command(label='Exit', command=self.destroy)
        files.pack(side='left', fill='x')

        general = ttk.Menubutton(f, text='General')
        options = tk.Menu(general, tearoff=0)
        general.config(menu=options)
        options.add_command(label='General settings',
                             command=lambda: self.selection(1))
        general.pack(side='left', fill='x')
        
        preproc = ttk.Menubutton(f, text='Pre-processing')
        options = tk.Menu(preproc, tearoff=0)
        preproc.config(menu=options)
        options.add_command(label='Exclusions',
                             command=lambda: self.selection(2))
        options.add_command(label='Filters',
                             command=lambda: self.selection(3))
        preproc.pack(side='left', fill='x')

        piv = ttk.Menubutton(f, text='Analysis')
        options = tk.Menu(piv, tearoff=0)
        piv.config(menu=options)
        submenu = tk.Menu(options, tearoff=0)
        options.add_command(label='PIV settings/analyze',
                             command=lambda: self.selection(4))
        submenu.add_command(label='Algorithms',
                             command=lambda: self.selection(5))
        submenu.add_command(label='Validation',
                             command=lambda: self.selection(7))
        submenu.add_command(label='Postprocessing',
                             command=lambda: self.selection(8))
        options.add_cascade(label='Advanced', menu=submenu)
        piv.pack(side='left', fill='x')
        
        calibrate = ttk.Menubutton(f, text='Calibration')
        options = tk.Menu(calibrate, tearoff=0)
        calibrate.config(menu=options)
        options.add_command(label='Calibration',
                             command=lambda: self.selection(9))
        calibrate.pack(side='left', fill='x')
        
        postproc = ttk.Menubutton(f, text='Post processing')
        options = tk.Menu(postproc, tearoff=0)
        postproc.config(menu=options)
        options.add_command(label='Validate components',
                             command=lambda: self.selection(10))
        options.add_command(label='Modify components',
                             command=lambda: self.selection(11))
        postproc.pack(side='left', fill='x')

        plot = ttk.Menubutton(f, text='Plotting')
        options = tk.Menu(plot, tearoff=0)
        plot.config(menu=options)
        options.add_command(
            label='Plotting', command=lambda: self.selection(12))
        options.add_command(
            label='Modify plot appearance', command=lambda: self.selection(13))
        plot.pack(side='left', fill='x')

        u_func = ttk.Menubutton(f, text='User function')
        options = tk.Menu(u_func, tearoff=0)
        u_func.config(menu=options)
        options.add_command(label='Show user function',
                             command=lambda: self.selection(15))
        options.add_command(label='Execute user function',
                             command=self.user_function)
        u_func.pack(side='left', fill='x')

        lab_func = ttk.Menubutton(f, text='Lab book')
        options = tk.Menu(lab_func, tearoff=0)
        lab_func.config(menu=options)
        options.add_command(label='Show lab book',
                             command=lambda: self.selection(14))
        lab_func.pack(side='left', fill='x')

        usage_func = ttk.Menubutton(f, text='Usage')
        options = tk.Menu(usage_func, tearoff=0)
        usage_func.config(menu=options)
        options.add_command(label='Usage',
                             command=lambda: messagebox.showinfo(
                                 title='Help',
                                 message=inspect.cleandoc(
                                     OpenPivGui.__doc__)))
        usage_func.pack(side='left', fill='x')

        web_func = ttk.Menubutton(f, text='Web')
        options = tk.Menu(web_func, tearoff=0)
        web_func.config(menu=options)
        options.add_command(label='Web', command=self.readme)
        web_func.pack(side='left', fill='x')

        f.pack(side='top', fill='x')

        
        
    def selection(self, num):
        self.nb.select(num)

        
        
    def calculate_invalid_vectors(self):
        try:
            self.get_settings()
            data = self.data
            
            for i in list(data.columns.values):
                data[i] = data[i].astype(float)
            data = data.to_numpy().astype(np.float)

            try:
                invalid = data[:, 4].astype('bool')

            except:
                invalid = np.asarray([True for i in range(len(data))])
                print('No typevectors found')
                
            invalid = np.count_nonzero(invalid)
            percent = _round(((invalid / len(data[:, 0])) * 100), 4)
            message = ('Percent invalid vectors for result index {}: {}%'.format(self.index, percent))
            
            if self.p['pop_up_info']:
                messagebox.showinfo(title = 'Statistics',
                                    message = message)
            print(message)

        except Exception as e:
            print('Could not read file for calculating percent of invalid vectors.')
            print('Reason: '+str(e))
            
            
            
    def disable_widgets(self, exclude_tab = None):
        print('Disabling widgets...')
        for tabs in range (0, self.nb.index('end')):
            if exclude_tab != None and tabs != exclude_tab:
                self.nb.tab(tabs, state='disabled')
                
        for key in self.ttk_widgets:
            self.ttk_widgets[key].config(state = 'disabled')
        self.lb.config(state='disabled')
    
    
    
    def enable_widgets(self):
        print('Enabling widgets...')
        for tabs in range (0, self.nb.index('end')):
            self.nb.tab(tabs, state='normal')
            
        for key in self.ttk_widgets:
            self.ttk_widgets[key].config(state = 'normal')
        self.lb.config(state='normal')
        self.set_windowing(0)
        self.update_widget_state()
        self.ttk_widgets['show_masked_vectors'].config(state = 'disabled')
            
            
            
    def user_function(self):
        '''Executes user function.'''
        self.get_settings()
        exec(self.p['user_func_def'])

        
        
    def reset_params(self, do_menu = True):
        '''Reset parameters to default values.'''
        if do_menu:
            answer = messagebox.askyesno(
                title='Settings Manager',
                message='Reset all parameters to default values?')
        else:
            answer = True
        if answer == True:
            self.p = OpenPivParams()
            self.set_settings()
            #self.set_windowing(0)
            print('Allocating memory for frames..')
            for i in range(len(self.session['frames_b'])):
                self.p['img_preproc'][f'{i}'] = [
                    '', '',
                    '', '',
                    [],
                    'None',
                    ''
                ]
                self.session['results'][f'{i}'] = []
                
            self.index = 0
            self.toggle = 'a'
            self.p['fnames'] = self.session['frames_a']
            self.tkvars['fnames'].set(self.p['fnames'])
            
            if len(self.session['files_a']) != 0:
                self.num_of_frames.config(text = '0/{}'.format(self.session['frame_num']))
                self.show(self.session['files_' + self.toggle][self.index])
                
            print('Allocated space for {} image(s)'.format(len(self.session['frames_b'])))
            print('Frequencing applied')
    
    
    
    def reset_session(self):
        '''Reset session'''
        answer = messagebox.askyesno(
            title='Session Manager',
            message='Reset/clear current session?')
        
        if answer == True:
            self.create_session()
            self.get_settings()
            
            
            
    def readme(self):
        '''Opens https://github.com/OpenPIV/openpiv_tk_gui.'''
        webbrowser.open('https://github.com/OpenPIV/openpiv_tk_gui')

        
        
    def delete_files(self):
        '''Delete files currently listed in the file list.'''
        answer = messagebox.askyesno(
            title='Delete files',
            message='Are you sure you want to delete selected files?')
        if answer == True:
            files = self.p['fnames'][:]
            for f in files:
                os.remove(f)
            self.navigate('back')

            
            
    def move_files(self):
        '''Move files to a new place.'''
        files = self.p['fnames'][:]
        dir = filedialog.askdirectory(mustexist=False)
        if len(dir) > 0:
            if not os.path.exists(dir):
                os.mkdir(dir)
            for src in files:
                dst = dir + os.path.sep + os.path.basename(src)
                shutil.move(src, dst)

                
                
    def load_settings(self):
        '''Load settings from a JSON file.'''
        settings = filedialog.askopenfilename(
            title = 'Settings Manager',
            defaultextension = '.json',
            filetypes = [('json', '*.json'), ])
        if len(settings) > 0:
            self.p.load_settings(settings)
            self.set_settings()
            self.set_windowing(0)

    def load_pandas(self, fname):
        '''Load files in a pandas data frame.

        On the rider named General, the parameters for loading
        the data frames can be specified.
        No parameters have to be set for image processing. 

        Parameters
        ----------
        fname : 
            A filename.

        Returns
        -------
        pandas.DataFrame :
            In case of an error, the errormessage is returned (str).
        '''
        sep = self.p['sep']
        if sep == 'tab':
            sep = '\t'
        if sep == 'space':
            sep = ' '

        ext = fname.split('.')[-1]
        if ext in ['txt', 'dat', 'jvc', 'vec', 'csv']:
            if self.p['load_settings'] == True:
                if self.p['header'] == True:
                    data = pd.read_csv(fname,
                                       decimal=self.p['decimal'],
                                       skiprows=int(self.p['skiprows']),
                                       sep=sep)
                elif self.p['header'] == False:
                    data = pd.read_csv(fname,
                                       decimal=self.p['decimal'],
                                       skiprows=int(self.p['skiprows']),
                                       sep=sep,
                                       header=0,
                                       names=self.p['header_names'].split(','))
            else:
                data = pd.read_csv(fname,
                                   decimal=',',
                                   skiprows=0,
                                   sep='\t',
                                   names=['x', 'y', 'vx', 'vy', 'sig2noise'])
        else:
            data = 'File could not be read. Possibly it is an image file.'
        return(data)

    '''~~~~~~~~~~~~~~~~~~~~~~~listbox~~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_listbox(self, key):
        '''Creates an interactive list of filenames.

        Parameters
        ----------
        key : str
            Key of a settings object.
        '''
        # root widget
        if key != 'img_list':
            f = ttk.Frame(self)
            width = 25
            side = 'bottom'
            padx = 0
            pady = 0  
        else:
            f = ttk.Frame(self.lf)
            width = 50
            side = None
            padx = 5
            pady = 20
            F = ttk.Frame(f)
            ttk.Label(F, text='Image list').pack(
                side='left', anchor = 'nw')
            
            ttk.Label(F, text='            '+
                              'Number of images:').pack(
                side='left')
            
            F2 = ttk.Frame(F)
            self.num_of_files = ttk.Label(F2, 
                text=self.session['file_num']) 
            self.num_of_files.pack(side='right')
            F2.pack(side='right')
            F.pack(fill = 'x')
        f.pack(side=side,
               fill='both',
               expand='True',
               padx = padx,
               pady=pady)
        
        # scrolling
        if key != 'img_list':
            sby = ttk.Scrollbar(f, orient="vertical")
            sby.pack(side='right', fill='y')
            self.lb = tk.Listbox(f, yscrollcommand=sby.set)
            sby.config(command=self.lb.yview)
            self.lb['width'] = width
        else:
            sbx = ttk.Scrollbar(f, orient="horizontal")
            sbx.pack(side='top', fill='x')
            sby = ttk.Scrollbar(f, orient="vertical")
            sby.pack(side='right', fill='y')
            
            self.lb = tk.Listbox(f, yscrollcommand=sbx.set)
            self.lb = tk.Listbox(f, yscrollcommand=sby.set)
            sbx.config(command=self.lb.xview)
            sby.config(command=self.lb.yview)
            self.lb['width'] = width

        # background variable
        self.tkvars.update({key: tk.StringVar()})
        #self.tkvars[key].set(self.p[key])
        self.lb['listvariable'] = self.tkvars[key]
        try:
            self.tkvars[key].set(self.session[key])
        except: # no images stored
            pass

        # interaction and others
        if key != 'img_list':
            self.lb.bind('<<ListboxSelect>>', self.__listbox_selection_changed)
            self.lb.pack(side='top', fill='y', expand='True')
            
            # navigation buttons
            F = ttk.Frame(f)
            self.ttk_widgets['toggle_frames_button'] = ttk.Button(F,
                text='Toggle A/B',
                command=self.toggle_frames,
                width = 24)
            
            self.ttk_widgets['toggle_frames_button'].pack(
                side='left', fill='x')
            F.pack()
            
            #tools/info
            f = ttk.Frame(f)
            f.pack(fill = 'x')
            lf = tk.LabelFrame(f, text='tools')
            lf.pack(side = 'bottom', fill = 'x')
            lf.config(borderwidth=2, height = 300, relief='groove')
            
            # number of files
            f = ttk.Frame(lf)
            ttk.Label(f, text=' frame: ').pack(side = 'left')
            self.num_of_frames = ttk.Label(f,
                text=self.session['frame_num'])
            self.num_of_frames.pack(side = 'right')
            f.pack()
            
            # current point
            f = ttk.Frame(lf)
            ttk.Label(f, text = 'current point:').pack(side = 'left', padx = 10)
            f.pack(fill = 'x')
            f = ttk.Frame(lf)
            
            f1 = ttk.Frame(f)
            self.point_x = ttk.Label(f, text = 'x: N/A')
            self.point_x.pack()
            f1.pack(side = 'left')
            
            f1 = ttk.Frame(f)
            self.point_y = ttk.Label(f1, text = 'y: N/A')
            self.point_y.pack()
            f1.pack(side = 'left')
            f.pack(side = 'left', padx = 10)
            
            f = ttk.Frame(lf)
            f1 = ttk.Frame(f)
            self.point_u = ttk.Label(f, text = 'u: N/A')
            self.point_u.pack()
            f1.pack(side = 'left')
            
            f1 = ttk.Frame(f)
            self.point_v = ttk.Label(f1, text = 'v: N/A')
            self.point_v.pack()
            f1.pack(side = 'left')
            f.pack(side = 'right', padx = 10)
            
            # current point
            '''fl = ttk.Frame(lf)
            f = ttk.Frame(fl)
            ttk.Label(f, text = 'current frame:').pack(side = 'left', padx = 10)
            f.pack(side = 'left')
            fl.pack(fill = 'x', side = 'bottom')'''
            '''f = ttk.Frame(lf)
            
            f1 = ttk.Frame(f)
            self.mean_v = ttk.Label(f, text = 'mean u: N/A')
            self.mean_v.pack()
            f1.pack(side = 'left')
            
            f1 = ttk.Frame(f)
            self.mean_u = ttk.Label(f1, text = 'mean v: N/A')
            self.mean_u.pack()
            f1.pack(side = 'left')
            f.pack(side = 'bottom', padx = 10)'''
            
        else:
            self.lb.bind('<<ListboxSelect>>', self.__listbox2_selection_changed)
            self.lb.pack(side='top', fill='y', expand='True')
        
        
    def change_xy_current(self, event):
        if event.inaxes is not None:
            x, y = event.inaxes.transData.inverted().transform((event.x, event.y))
            self.point_x.config(text = f'x: {int(_round(x, 0))}')
            self.point_y.config(text = f'y: {int(_round(y, 0))}')
    
    
    def change_xy_curremt_results(self, event):
        if event.inaxes is not None:
            results = self.session['results'][f'{self.index}'][0]
            if results[0] and results[1] and results[2] and results[3] != ('', ' '):
                xmin = results[0]
                xmax = results[1]
                ymin = results[2]
                ymax = results[3]
                if x > xmin and x < xmax and y > ymin and y < ymax:
                    x, y = event.inaxes.transData.inverted().transform((event.x, event.y))
                    x = int(np.floor(x / self.session['results'][1]))
                    y = int(np.floor(y / self.session['results'][1]))
                    self.point_x.config(text = f'x: {x}')
                    self.point_y.config(text = f'y: {y}')
            else:
                x, y = event.inaxes.transData.inverted().transform((event.x, event.y))
                self.point_x.config(text = f'x: {int(_round(x, 0))}')
                self.point_y.config(text = f'y: {int(_round(y, 0))}')
            
            
            
    def __listbox_selection_changed(self, event):
        '''Handles selection change events of the file listbox.'''
        try:
            self.index = event.widget.curselection()[0]
        except IndexError:
            pass  # nothing selected
        else:
            self.get_settings()
            self.num_of_frames.config(text = (str(self.index)+'/'+str(self.session['frame_num'])))
            
            if len(self.object_mask) > 0:
                self.mask_clear(update_plot = False)
                print('Clearing mask(s) \Reason: moved to a different frame')
            if self.p['preview_all']:
                self.show(self.session['files_' + self.toggle][self.index], preview = True)
            else:
                self.show(self.session['files_' + self.toggle][self.index], preview = False)
                
            if self.p['data_information'] == True:
                self.show_informations(self.session['files_' + self.toggle][self.index])
                
                
                
    def __listbox2_selection_changed(self, event):
        '''Handles selection change events of the file listbox.'''
        try:
            index = event.widget.curselection()[0]
        except IndexError:
            pass  # nothing selected
        else:
            self.get_settings()
            self.show(self.p['img_list'][index], preproc = False, perform_check = False)
            
            
            
    def get_filelistbox(self):
        '''Return a handle to the file list widget.

        Returns
        -------
        tkinter.Listbox
            A handle to the listbox widget holding the filenames
        '''
        return(self.lb)
    
    def toggle_frames(self):
        if self.toggle == 'a':
            self.toggle = 'b'
        else:
            self.toggle = 'a'
        self.p['fnames']=list(self.session['frames_' + self.toggle])
        self.tkvars['fnames'].set(self.p['fnames'])
        self.show(self.session['files_' + self.toggle][self.index])
        print('Toggled to ' + self.toggle + ' frames')

        
    
    '''~~~~~~~~~~~~~~~~~~~~~~~textbox~~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_text_area(self, key):
        '''Init a text area, here used as a lab-book, for example.

        The content is saved automatically to the parameter object,
        when the mouse leaves the text area.'''
        self.ta.append(tk.Text(self.set_frame[-1], undo=True))
        ta = self.ta[-1]
        ta.pack()
        ta.bind('<Leave>',
                (lambda _: self.__get_text(key, ta)))
        ttk.Button(self.set_frame[-1],
                   text='clear',
                   command=lambda: ta.delete(
            '1.0', tk.END)
        ).pack(fill='x')
        ttk.Button(self.set_frame[-1],
                   text='undo',
                   command=lambda: ta.edit_undo()
                   ).pack(fill='x')
        ttk.Button(self.set_frame[-1],
                   text='redo',
                   command=lambda: ta.edit_redo()
                   ).pack(fill='x')

    def __get_text(self, key, text_area):
        '''Get text from text_area and copy it to parameter object.'''
        self.p[key] = text_area.get('1.0', tk.END)
    
    '''~~~~~~~~~~~~~~~~~~~~frames/widgets~~~~~~~~~~~~~~~~~~~'''
    def __init_labelframe(self, key):
        '''Add a label frame for widgets.'''
        f = ttk.Frame(self.set_frame[-1])
        self.pane = ttk.Panedwindow(f, orient='vertical', width=self.frame_width, height=680)
        self.lf = tk.LabelFrame(self.pane, text=self.p.label[key])
        self.lf.config(borderwidth=2, width=self.frame_width, height=680, relief='groove')
        self.pane.add(self.lf)
        self.pane.pack(side='left', fill='both')
        f.pack(fill='both')

    def __init_sub_labelframe(self, key):
        '''Add a label frame for widgets.'''
        self.sub_lf = tk.LabelFrame(self.lf, text=self.p.label[key])
        self.sub_lf.config(borderwidth=2, width=self.frame_width, relief='groove')
        self.sub_lf.pack(fill='both', pady=4, padx=4)
        
    def __init_horizontal_spacer(self, key):
        '''Add a horizontal spacer line for widgets.'''
        f = ttk.Frame(self.lf)
        hs = ttk.Separator(f)
        hs.pack(fill='x')
        f.pack(fill='both', pady=4)

    def __init_sub_horizontal_spacer(self, key):
        '''Add a horizontal spacer line for widgets'''
        f = ttk.Frame(self.sub_lf)
        hs = ttk.Separator(f)
        hs.pack(fill='x')
        f.pack(fill='both', pady=4)

    def __init_label(self, key):
        f = ttk.Frame(self.lf)
        label1 = ttk.Label(f,
                           text=self.p.label[key])
        label1.pack(side='left')
        f.pack()
        
    def roi_widgets(self, frame, key, label, label2, padx, pady):
        F = ttk.Frame(frame)
        self.ttk_widgets[label] = ttk.Label(F, text = label2)
        self.tkvars.update({key: tk.StringVar()})
        self.ttk_widgets[key] = ttk.Entry(F, width=8, justify = 'center')
        self.ttk_widgets[key]['textvariable'] = self.tkvars[key]
        self.ttk_widgets[label].pack()
        self.ttk_widgets[key].pack()
        F.pack(side='left', padx=padx, pady=pady)
    
    def __init_entry(self, key):
        '''Creates a label and an entry in a frame.

        A corresponding tk background textvariable is also crated. An 
        option menu is created instead of en entry, if a hint is given
        in the parameter object. The help string in the parameter object
        is used for creating a tooltip.

        Parameter
        ---------
        key : str
            Key of a parameter obj.
        '''
        # sub label frames
        if(self.p.type[key] == 'sub_int' or
            self.p.type[key] == 'sub_int2' or
            self.p.type[key] == 'sub_float' or
            self.p.type[key] == 'sub'):
            f = ttk.Frame(self.sub_lf)
            f.pack(fill='x')
            
            if self.p.type[key] != 'sub_int2':
                self.ttk_widgets[key + '_label'] = ttk.Label(f, text=self.p.label[key])
                CreateToolTip(self.ttk_widgets[key + '_label'], self.p.help[key])
                self.ttk_widgets[key + '_label'].pack(side='left', padx = self.sub_padx, pady = self.sub_pady)
                side = 'right'
            else:
                side = 'left'
            if self.p.type[key] == 'sub_int':
                self.tkvars.update({key: tk.IntVar()})
            elif self.p.type[key] == 'sub_int2':
                self.windowing_vars[key] = tk.IntVar()
                self.tkvars.update({key: self.windowing_vars[key]})
            elif self.p.type[key] == 'sub_float':
                self.tkvars.update({key: tk.DoubleVar()})
            elif self.p.type[key] == 'sub':
                self.tkvars.update({key: tk.StringVar()})
                
            if self.p.hint[key] is not None:
                if self.p.type[key] != 'sub_int2':
                    self.ttk_widgets[key] = ttk.OptionMenu(f,
                                      self.tkvars[key],
                                      self.p[key],
                                      *self.p.hint[key])
                else:
                    self.ttk_widgets[key] = ttk.Combobox(f,
                                      textvariable = self.tkvars[key],
                                      width = 8, justify = 'center')
                    self.ttk_widgets[key]['values'] = self.p.hint[key]
                    
            else:
                self.ttk_widgets[key] = ttk.Entry(f, width=10, justify = 'center')
                self.ttk_widgets[key]['textvariable'] = self.tkvars[key]
            CreateToolTip(self.ttk_widgets[key], self.p.help[key])
            self.ttk_widgets[key].pack(side=side, padx = self.sub_padx, pady = self.sub_pady)
            if self.p.type[key] == 'sub_int2':
                self.ttk_widgets[key + '_label'] = ttk.Label(f, 
                    text = '= {} '.format(
                        int(_round(self.overlap_percent * self.p[key], 0))))
                self.ttk_widgets[key + '_label'].pack(side = 'right', padx=34)
                self.generateOnChange(self.ttk_widgets[key])
                self.ttk_widgets[key].bind('<<Change>>', self.find_overlap)
                self.ttk_widgets[key].bind('<FocusOut>', self.find_overlap)
        else:
            f = ttk.Frame(self.lf)
            f.pack(fill='x')
            self.ttk_widgets[key + '_label'] = ttk.Label(f, text=self.p.label[key])
            CreateToolTip(self.ttk_widgets[key + '_label'], self.p.help[key])
            self.ttk_widgets[key + '_label'].pack(side='left', padx = self.padx, pady = self.pady)
            
            if self.p.type[key] == 'int':
                self.tkvars.update({key: tk.IntVar()})
            elif self.p.type[key] == 'float':
                self.tkvars.update({key: tk.DoubleVar()})
            else:
                self.tkvars.update({key: tk.StringVar()})
                
            if self.p.hint[key] is not None:
                self.ttk_widgets[key] = ttk.OptionMenu(f,
                                      self.tkvars[key],
                                      self.p[key],
                                      *self.p.hint[key])
            else:
                self.ttk_widgets[key] = ttk.Entry(f, width=10, justify = 'center')
                self.ttk_widgets[key]['textvariable'] = self.tkvars[key]
            CreateToolTip(self.ttk_widgets[key], self.p.help[key])
            self.ttk_widgets[key].pack(side='right', padx = self.padx, pady = self.pady)

    def __init_checkbutton(self, key):
        '''Create a checkbutton with label and tooltip.'''
        f = ttk.Frame(self.lf)
        f.pack(fill='x', padx = self.padx, pady = self.pady)
        self.tkvars.update({key: tk.BooleanVar()})
        self.tkvars[key].set(bool(self.p[key]))
        self.ttk_widgets[key] = ttk.Checkbutton(f)
        self.ttk_widgets[key]['variable'] = self.tkvars[key]
        self.ttk_widgets[key]['onvalue'] = True
        self.ttk_widgets[key]['offvalue'] = False
        self.ttk_widgets[key]['text'] = self.p.label[key]
        CreateToolTip(self.ttk_widgets[key], self.p.help[key])
        self.ttk_widgets[key].pack(side='left')
        if self.p.hint[key] == 'bind2': # for use of updating button font/bold
            self.ttk_widgets[key]['command'] = self.update_buttons
        elif self.p.hint[key] == 'bind':
            self.ttk_widgets[key]['command'] = self.update_widget_state

    def __init_sub_checkbutton(self, key):
        '''Create a checkbutton with label and tooltip.'''
        f = ttk.Frame(self.sub_lf)
        f.pack(fill='x',padx = self.sub_padx, pady = self.sub_pady)
        self.tkvars.update({key: tk.BooleanVar()})
        self.tkvars[key].set(bool(self.p[key]))
        self.ttk_widgets[key] = ttk.Checkbutton(f)
        self.ttk_widgets[key]['variable'] = self.tkvars[key]
        self.ttk_widgets[key]['onvalue'] = True
        self.ttk_widgets[key]['offvalue'] = False
        self.ttk_widgets[key]['text'] = self.p.label[key]
        CreateToolTip(self.ttk_widgets[key], self.p.help[key])
        self.ttk_widgets[key].pack(side='left')
        if self.p.hint[key] == 'bind':
            self.ttk_widgets[key]['command'] = self.update_widget_state

    def __init_sub_checkbutton2(self, key):
        '''Create a checkbutton with label and tooltip.'''
        f = ttk.Frame(self.sub_lf)
        f.pack(fill='x',padx = self.sub_padx, pady = self.sub_pady)
        self.windowing_vars[key] = tk.BooleanVar()
        self.tkvars.update({key: self.windowing_vars[key]})
      # self.windowing_vars[key].trace('w', self.set_windowing)
        self.tkvars[key].set(bool(self.p[key]))
        self.ttk_widgets[key] = ttk.Checkbutton(f)
        self.ttk_widgets[key]['variable'] = self.tkvars[key]
        self.ttk_widgets[key]['onvalue'] = True
        self.ttk_widgets[key]['offvalue'] = False
        self.ttk_widgets[key]['text'] = self.p.label[key]
        CreateToolTip(self.ttk_widgets[key], self.p.help[key])
        self.ttk_widgets[key].pack(side='left')
       # self.ttk_widgets[key].bind() # lets try binding before modifieng the GUI to use .trace()
        self.ttk_widgets[key]['command'] = lambda: self.set_windowing(0)

        
        
    def __init_exclusions_preferences(self):
        whitespace = '                   '
        keys = ['roi_border', 'mask_fill', 'mask_vec'] 
        command = [self.roi_border_colorpicker,
                   self.mask_fill_colorpicker,
                   self.mask_vec_colorpicker]
        i = 0
        for key in keys:
            f = ttk.Frame(self.sub_lf)
            l = ttk.Label(f, text=self.p.label[key])
            CreateToolTip(l, self.p.help[key])
            l.pack(side='left', padx=self.sub_padx, pady=self.sub_pady)
            self.ttk_widgets[key] = tk.Button(f,
                                       text = whitespace,
                                       bg = self.p[key],
                                       relief = 'groove',
                                       command = command[i])
            self.ttk_widgets[key].pack(side='right', padx = self.sub_padx, pady = self.sub_pady)
            CreateToolTip(self.ttk_widgets[key], self.p.help[key])
            f.pack(fill='x')
            i+=1
        
        
        
    def __init_vec_colorpicker(self, key):
        whitespace = '                   '
        f = ttk.Frame(self.sub_lf)
        l = ttk.Label(f, text='invalid vector color')
        CreateToolTip(l, self.p.help[key])
        l.pack(side='left', padx = self.sub_padx, pady = self.sub_pady)
        self.invalid_color = tk.Button(f,
                                       text=whitespace,
                                       bg=self.p['invalid_color'],
                                       relief='groove',
                                       command=self.invalid_colorpicker)
        self.invalid_color.pack(side='right', padx = self.sub_padx, pady = self.sub_pady)
        f.pack(fill='x')

        f = ttk.Frame(self.sub_lf)
        l = ttk.Label(f, text='valid vector color')
        CreateToolTip(l, self.p.help[key])
        l.pack(side='left', padx = self.sub_padx, pady = self.sub_pady)
        self.valid_color = tk.Button(f,
                                     text=whitespace,
                                     bg=self.p['valid_color'],
                                     relief='groove',
                                     command=self.valid_colorpicker)
        self.valid_color.pack(side='right', padx = self.sub_padx, pady = self.sub_pady)
        f.pack(fill='x') 
        
        
        
    def roi_border_colorpicker(self):
        self.p['roi_border'] = colorchooser.askcolor()[1]
        self.ttk_widgets['roi_border'].config(bg=self.p['roi_border'])
        
        
        
    def mask_fill_colorpicker(self):
        self.p['mask_fill'] = colorchooser.askcolor()[1]
        self.ttk_widgets['mask_fill'].config(bg=self.p['mask_fill'])
        
        
        
    def mask_vec_colorpicker(self):
        self.p['mask_vec'] = colorchooser.askcolor()[1]
        self.ttk_widgets['mask_vec'].config(bg=self.p['mask_vec'])
        
        
        
    def invalid_colorpicker(self):
        self.p['invalid_color'] = colorchooser.askcolor()[1]
        self.invalid_color.config(bg=self.p['invalid_color'])

        
        
    def valid_colorpicker(self):
        self.p['valid_color'] = colorchooser.askcolor()[1]
        self.valid_color.config(bg=self.p['valid_color'])
    
    
    
    '''~~~~~~~~~~~~~~~~~~~~~loading images~~~~~~~~~~~~~~~~~~'''
    def update_buttons(self):
        self.get_settings()
        buttons = ['load_img_button', 'apply_roi',
                   'mask_apply_current', 'mask_apply_all',
                   'background_apply', 'analyze_current', 'analyze_all']
        if self.p['unbold_buttons']:
            self.bold_apply = 'h12.TButton'
        else:
            self.bold_apply = 'b12.TButton'
        for key in buttons:
            self.ttk_widgets[key].configure(style = self.bold_apply)    
        
        
        
    def __init_load_img_button(self, key):
        style = ttk.Style()
        style.configure('h12.TButton', font = ('Helvetica', 12))
        style.configure('b12.TButton', font = ('Helvetica', 12, 'bold'))
        if self.p['unbold_buttons']:
            self.bold_apply = 'h12.TButton'
        else:
            self.bold_apply = 'b12.TButton'
        f = ttk.Frame(self.lf)
        f.pack(fill = 'x')
        self.ttk_widgets['load_img_button'] = ttk.Button(f,
                                              text='Load Images',
                                              command=self.select_image_files,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['load_img_button'].pack(side='top', pady = 15)
        
        
        
    def __init_apply_frequence_button(self, key):
        f = ttk.Frame(self.lf)
        f.pack(fill = 'x')
        self.ttk_widgets['apply_frequence_button'] = ttk.Button(f,
                                              text='Apply Frequencing',
                                              command=self.apply_frequencing,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['apply_frequence_button'].pack(side='top', pady=15)

        
        
    def apply_frequencing(self):
        # custom image sequence with (1),(1+[x]) or (1+[1+x]),(2+[2+x]) or ((1+[1+x]),(3+[3+x]))
        print('Applying frequencing...')
        self.get_settings()
        if self.p['sequence'] == '(1+2),(1+3)':
            self.session['files_a'] = self.session['img_list'][0]
            self.session['files_b'] = self.session['img_list'][self.p['skip']::1]
            # making sure files_a is the same length as files_b
            self.session['files_a'] = []
            for i in range(len(self.session['files_b'])):
                self.session['files_a'].append(self.session['img_list'][0])
        else:
            if self.p['sequence'] == '(1+2),(2+3)':
                step = 1
            else:
                step = 2
            self.session['files_a'] = self.session['img_list'][0::step]
            self.session['files_b'] = self.session['img_list'][self.p['skip']::step]
            # making sure files_a is the same length as files_b
            diff = len(self.session['files_a'])-len(self.session['files_b'])
            if diff != 0:
                for i in range(diff):
                    self.session['files_a'].pop(len(self.session['files_b']))
        print('Number of a files: ' + str(len(self.session['files_a'])))
        print('Number of b files: ' + str(len(self.session['files_b'])))
        # set listbox names
        self.session['frames_a'] = []
        self.session['frames_b'] = []
        for i in range(len(self.session['files_a'])):
            self.session['frames_a'].append('Frame '+str(str(i).zfill(math.ceil(
                                                    math.log10(len(self.session['files_a'])))))+'A')
            self.session['frames_b'].append('Frame '+str(str(i).zfill(math.ceil(
                                                    math.log10(len(self.session['files_b'])))))+'B')
            self.p['img_preproc'][f'{i}'] = [
                    '', '', # ROI
                    '', '',
                    [], # mask
                    'None', # background removal
                    '' # background image path if needed
                ]
            self.session['results'][f'{i}'] = []
        self.update_widget_state2(state = 'normal')
        self.toggle = 'a'
        self.p['fnames'] = list(self.session['frames_a'])
        self.tkvars['fnames'].set(self.p['fnames'])
        self.num_of_frames.config(text=str(len(self.p['fnames'])))
        self.session['frame_num'] = str(len(self.session['frames_a']) - 1)
        self.num_of_frames.config(text = '0/{}'.format(self.session['frame_num']))
        self.index = 0
        self.show(self.session['files_' + self.toggle][0])
        print('Allocated space for {} frames(s)'.format(len(self.session['frames_b'])))
        print('Frequencing applied')
        
        
        
    '''~~~~~~~~~~~~~~~~~~~~~~~ROI~~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_ROI(self):
        f = ttk.Frame(self.lf)
        f.pack(fill='x')
        sub_lf = tk.LabelFrame(f, text='Region of interest')
        sub_lf.config(borderwidth=2, width=self.frame_width, relief='groove')
        sub_lf.pack(fill='both', pady=4, padx=4)
        f = ttk.Frame(sub_lf)
        self.roi_status_frame = tk.Frame(f)
        self.ttk_widgets['roi_status'] = tk.Label(self.roi_status_frame, 
                                                text = 'ROI inactive')
        self.ttk_widgets['roi_status'].pack(anchor='n', fill='x', padx = 10, pady = 3)
        self.roi_status_frame.pack(fill='x', padx=4, pady=4)
        self.ttk_widgets['select_roi'] = ttk.Button(f,
                                              text='Select ROI',
                                              command=self.roi_select,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['select_roi'].pack(side='left', padx=2)
        self.ttk_widgets['clear_roi'] = ttk.Button(f,
                                              text='Clear ROI',
                                              command=self.roi_clear,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['clear_roi'].pack(side='right', padx=2)
        f.pack(fill='x')
        f = ttk.Frame(sub_lf)
        self.ttk_widgets['apply_roi'] = ttk.Button(f,
                                              text='Apply to all frames',
                                              command=self.roi_apply,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['apply_roi'].pack(side='bottom', padx=2, pady=2)
        f.pack(fill='x')
        padx = 2
        pady = 2
        f = ttk.Frame(sub_lf)
        f.pack(fill='x', pady=0)
        keys = [['roi-xmin', 'roi-xmin_label', 'x'], ['roi-ymin', 'roi-xmax_label', 'y'],
                ['roi-xmax', 'roi-ymin_label', 'width'], ['roi-ymax', 'roi-ymax_label', 'height']]
        for i in range(4):
            self.roi_widgets(f, keys[i][0], keys[i][1], keys[i][2], padx, pady)
    
    
    
    def roi_select(self):
        self.disable_widgets(exclude_tab = 2)
        self.initialize_roi_interact()
    
    
    
    def roi_apply(self):
        self.get_settings()
        if self.p['roi-xmin'] and self.p['roi-xmax'] and self.p['roi-ymin'] and self.p['roi-ymax'] != ('', ' '):
            self.ttk_widgets['roi_status'].config(bg = 'lime', text = 'ROI active')
            self.roi_status_frame.config(bg = 'lime')   
        for i in range(len(self.session['frames_a'])):
            self.p['img_preproc'][f'{i}'][0] = self.p['roi-xmin']
            self.p['img_preproc'][f'{i}'][1] = self.p['roi-xmax']
            self.p['img_preproc'][f'{i}'][2] = self.p['roi-ymin']
            self.p['img_preproc'][f'{i}'][3] = self.p['roi-ymax']
        self.show(self.session['files_' + self.toggle][self.index])
            
            
            
    def roi_clear(self, force_update = False):
        self.tkvars['roi-xmin'].set('')
        self.tkvars['roi-xmax'].set('')
        self.tkvars['roi-ymin'].set('')
        self.tkvars['roi-ymax'].set('')
        if force_update:
            self.show(self.session['files_' + self.toggle][self.index], 
                      show_roi = False, ignore_blank = True)
        self.ttk_widgets['roi_status'].config(bg = self.b_color, text = '')
        self.roi_status_frame.config(bg = self.b_color)  
    
    
    
    def initialize_roi_interact(self):
        self.toggle_selector = RectangleSelector(self.ax, 
                                                 self.onselect_roi,
                                                 drawtype='box',
                                                 button=[1],
                                                 rectprops = dict(facecolor=self.p['roi_border'], 
                                                                  edgecolor=self.p['roi_border'], 
                                                                  alpha=0.4, 
                                                                  fill=False))
        self.roi_rect = self.fig_canvas.mpl_connect('key_press_event', self.toggle_selector)
        plt.show()
    
    
    
    def onselect_roi(self, eclick, erelease):
        "eclick and erelease are matplotlib events at press and release."
        x1 = int(_round(eclick.xdata, 0))
        y1 = int(_round(eclick.ydata, 0))
        x2 = int(_round(erelease.xdata, 0))
        y2 = int(_round(erelease.ydata, 0))
        print('startposition: (%f, %f)' % (x1, y1))
        print('endposition  : (%f, %f)' % (x2, y2))
        self.tkvars['roi-xmin'].set(x1)
        self.tkvars['roi-xmax'].set(x2)
        self.tkvars['roi-ymin'].set(y1)
        self.tkvars['roi-ymax'].set(y2)
        self.terminate_roi_interact()
        self.toggle_selector.set_active(False)
            
            
            
    def terminate_roi_interact(self):
        self.disconnect(self.roi_rect)
        self.enable_widgets()
        print('Exited roi')
        
        
        
    '''~~~~~~~~~~~~~~~~~~~~~~~masking~~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_mask(self):
        f = ttk.Frame(self.lf)
        f.pack(fill='x')
        sub_lf = tk.LabelFrame(f, text='Object masking')
        sub_lf.config(borderwidth = 2, width=self.frame_width, relief='groove')
        sub_lf.pack(fill='both', pady = 4, padx = 4)
        f = ttk.Frame(sub_lf)
        self.mask_status_frame = tk.Frame(f)
        self.ttk_widgets['mask_status'] = tk.Label(self.mask_status_frame, 
                                                text = 'Masking inactive')
        self.ttk_widgets['mask_status'].pack(anchor = 'n', fill = 'x', padx = 10, pady = 3)
        self.mask_status_frame.pack(fill='x', padx = 4, pady = 4)
        self.ttk_widgets['mask_select'] = ttk.Button(f,
                                              text = 'Select mask',
                                              command=self.mask_select,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['mask_select'].pack(side='left', padx=2, pady=2)
        self.ttk_widgets['mask_clear'] = ttk.Button(f,
                                              text='Clear mask',
                                              command=self.mask_clear,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['mask_clear'].pack(side='right', padx=2, pady=2)
        f.pack(fill='x')
        f = ttk.Frame(sub_lf)
        self.ttk_widgets['mask_save'] = ttk.Button(f,
                                              text='Save mask',
                                              command=self.mask_save,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['mask_save'].pack(side='left', padx=2)
        self.ttk_widgets['mask_load'] = ttk.Button(f,
                                              text='Load mask',
                                              command=self.mask_load,
                                              style = 'h12.TButton',
                                              width=self.small_button_width)
        self.ttk_widgets['mask_load'].pack(side='right', padx=2)
        f.pack(fill='x')
        f = ttk.Frame(sub_lf)
        self.ttk_widgets['mask_load_applied'] = ttk.Button(f,
                                              text='Load applied mask',
                                              command=self.mask_load_applied,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['mask_load_applied'].pack(padx=2, pady=2)
        f.pack(fill='x')
        f = ttk.Frame(sub_lf)
        self.ttk_widgets['mask_apply_current'] = ttk.Button(f,
                                              text='Apply to current frame',
                                              command=self.apply_mask_current,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['mask_apply_current'].pack(padx=2, pady=2)
        f.pack(fill='x')
        f = ttk.Frame(sub_lf)
        self.ttk_widgets['mask_apply_all'] = ttk.Button(f,
                                              text='Apply to all frames',
                                              command=self.apply_mask_all,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['mask_apply_all'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
    
    
    
    def mask_select(self):
        self.initialize_mask_interact()
        self.disable_widgets(exclude_tab = 2)
    
    
    
    def initialize_mask_interact(self):
        self.mask_selector = PolygonSelector(
            self.ax, 
            self.onselect_mask,
            lineprops = dict(
                color='darkred',
                linestyle='-',
                linewidth=2, 
                alpha=0.9),
            markerprops = dict(
                marker='o',
                markersize=1, 
                mec='red', 
                mfc='red', 
                alpha=0.9),
                vertex_select_radius = 10)
        self.mask_poly = self.fig_canvas.mpl_connect('key_press_event', self.mask_selector)
        plt.show()
     
    
    
    def onselect_mask(self, verts):
        "eclick and erelease are matplotlib events at press and release."
        
        #verts.append(verts[0])
        self.object_mask.append(verts)
        self.mask_counter += 1
        self.terminate_mask_interact()
        self.mask_selector.set_active(False)
        self.ttk_widgets['mask_status'].config(bg = self.b_color, 
            text = '{} mask(s) selected'.format(self.mask_counter))
        print('Exiting masking \nReason: clicked starting vertex')
        
        
        
    def mask_clear(self, update_plot = True):
        self.ttk_widgets['mask_select'].config(state='normal')
        self.mask_counter = 0
        self.object_mask = []
        if update_plot:
            self.show(self.session['files_' + self.toggle][self.index], show_mask = False)
        self.ttk_widgets['mask_select'].config(state = 'normal')
        self.mask_status_frame.config(bg = self.b_color)
        self.ttk_widgets['mask_status'].config(bg = self.b_color,
            text = '{} mask(s) selected'.format(self.mask_counter))
        self.ttk_widgets['mask_save'].config(state = 'disabled')
    
    
    
    def mask_clear_all(self):
        self.mask_clear(update_plot = False)
        for i in range(len(self.session['frames_a'])):
            self.p['img_preproc']['{}'.format(i)][4] = self.object_mask
        self.show(self.session['files_' + self.toggle][self.index])
        
        
        
    def mask_save(self):
        directory = filedialog.asksaveasfilename(title = 'Mask Manager',
                                                 defaultextension = '.tif',
                                                 filetypes = ((".tif","*.tif"),))
        if len(directory) > 0:
            if len(self.object_mask) > 0:
                mask_img = np.zeros(piv_tls.imread(self.session['files_a'][0]).shape) 
                mask_img = Image.fromarray(mask_img)
                draw = ImageDraw.Draw(mask_img)
                for i in range(len(self.object_mask)):
                    draw.polygon(self.object_mask[i],
                        fill='white')
                mask_img = np.array(mask_img).astype(np.uint8)
                mask_img[mask_img > 100] = 255
                piv_tls.imsave(str(directory), mask_img)
    
    
    def mask_load_applied(self):
        if len(self.p['img_preproc']['{}'.format(self.index)][4]) > 0:
            self.object_mask = self.p['img_preproc']['{}'.format(self.index)][4]
            self.mask_counter = len(self.object_mask)
            self.ttk_widgets['mask_status'].config(
                bg = self.b_color,
                text = '{} mask(s) selected'.format(self.mask_counter))
            self.ttk_widgets['mask_select'].config(state = 'normal')
            self.ttk_widgets['mask_save'].config(state = 'normal')
        else:
            print('No mask(s) applied to current frame')

            
                
    def mask_load(self):
        print('Use Ctrl + Shift to select multiple files. \n' +
              'Selecting one mask file will load the mask, but not apply it. \n' +
              'Selecting multiple mask files will automatically apply a mask to each frame.')
        files = filedialog.askopenfilenames(title = 'Mask Manager',
                                            multiple=True, 
                                            filetypes = ((".tif","*.tif"),))
        if len(files) > 0:
            if(len(files)) == 1:
                self.mask_clear(update_plot = False)
                masks = piv_tls.imread(files[0])
                masks = measure.find_contours(masks, 0.001)
                for mask in masks:
                    mask_coords = []
                    #mask = measure.approximate_polygon(mask, tolerance=1.5)
                    for i in range(len(mask)):
                        mask_coords.append((mask[:, 1][i], mask[:, 0][i]))
                    self.object_mask.append(mask_coords)
                self.ttk_widgets['mask_save'].config(state = 'normal')
                self.mask_counter = len(self.object_mask)
                self.ttk_widgets['mask_status'].config(text = f'{self.mask_counter} mask(s) loaded')
                self.ttk_widgets['mask_save'].config(state = 'normal')
                print('Loaded mask file')
            else:
                for i in range(len(files)):
                    if i <= (len(self.session['files_a']) - 1):
                        masks = piv_tls.imread(files[i])
                        masks = measure.find_contours(masks, 0.001)
                        mask_objects = []
                        for mask in masks:
                            mask_coords = []
                            #mask = measure.approximate_polygon(mask, tolerance=1.5)
                            for k in range(len(mask)):
                                mask_coords.append((mask[:,1][k], mask[:,0][k]))
                            mask_objects.append(mask_coords)
                        self.p['img_preproc'][f'{i}'][4] = mask_objects
                    else:
                        break;
                    
                self.show(self.session['files_' + self.toggle][self.index]) 
                
                print('Applied mask(s) to each frame')
            
            
            
    def apply_mask_current(self):
        if len(self.object_mask) == 0:
            clear = messagebox.askyesno(title = 'Mask Manager',
                    message = 'Do you want to clear mask(s) for the current frame?')
            if clear:
                self.p['img_preproc']['{}'.format(self.index)][4] = self.object_mask
                self.mask_counter = 0
                 
                text = ('Cleared all mask(s) from current frame')
            else: text = ''
        else:
            self.p['img_preproc']['{}'.format(self.index)][4] = self.object_mask
            if len(self.object_mask) != 0:
                self.ttk_widgets['mask_select'].config(state = 'disabled')
            self.mask_counter = 0
            self.object_mask = []
            
            text = ('Cleared stored mask \nReason: Applied mask to frame')
        self.ttk_widgets['mask_save'].config(state = 'disabled') 
        self.show(self.session['files_' + self.toggle][self.index])
        print(text)

        
        
    def apply_mask_all(self):        
        if len(self.object_mask) == 0:
            clear = messagebox.askyesno(title = 'Mask Manager',
                    message = 'Do you want to clear masks for all frames?')
            if clear:
                for i in range(len(self.session['frames_a'])):
                    self.p['img_preproc'][f'{i}'][4] = self.object_mask
                self.mask_counter = 0
                print('Cleared all masks')
        else:
            print('Applying mask to all frames..')
            for i in range(len(self.session['frames_a'])):
                self.p['img_preproc'][f'{i}'][4] = self.object_mask
            print('Applied mask to all frames')
            self.ttk_widgets['mask_select'].config(state = 'disabled')
            self.object_mask = []
            self.mask_counter = 0
            
            print('Cleared stored mask(s) \nReason: Applied mask to all frames')
        self.ttk_widgets['mask_save'].config(state = 'disabled')     
        self.show(self.session['files_' + self.toggle][self.index])
            
            
            
    def terminate_mask_interact(self):
        self.disconnect(self.mask_poly)
        self.enable_widgets()
        
        
        
    '''~~~~~~~~~~~~~~~~~~~~~preprocessing~~~~~~~~~~~~~~~~~~~'''
    def __init_apply_preproc(self):
        f = ttk.Frame(self.lf)
        f.pack(fill='x')
        F = ttk.Frame(f)
        self.ttk_widgets['preview_preproc_current'] = ttk.Button(F,
                                              text='Preview current frame',
                                              command= self.preview_current_frame,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['preview_preproc_current'].pack(padx=2, pady=2)
        F.pack(fill='x')
        F = ttk.Frame(f)
    
    
    
    def __init_background(self):
        f = ttk.Frame(self.lf)
        f.pack(fill='x')
        self.sub_lf = tk.LabelFrame(f, text='Background removal')
        self.sub_lf.config(borderwidth=2, width=self.frame_width, relief='groove')
        self.sub_lf.pack(fill='both', pady=2, padx=2)
        f = ttk.Frame(self.sub_lf)
        f.pack()
        self.background_status_frame = tk.Frame(f)
        self.ttk_widgets['background_status'] = tk.Label(self.background_status_frame, 
                                                text = 'Background inactive')
        self.ttk_widgets['background_status'].pack(anchor='n', fill='x', padx = 10, pady = 3)
        self.background_status_frame.pack(fill='x', padx = 5, pady = 3)
        F = ttk.Frame(f)
        self.ttk_widgets['background_load'] = ttk.Button(F,
                                              text = 'Load background image(s)',
                                              command = self.load_background_img,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['background_load'].pack(padx=4, pady=2)
        F.pack(fill='x')
        F = ttk.Frame(f)
        self.ttk_widgets['background_clear'] = ttk.Button(F,
                                              text = 'Clear background image(s)',
                                              command = self.clear_background_img,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['background_clear'].pack(padx=4, pady=2)
        F.pack(fill='x')

        
        
    def preview_current_frame(self):
        self.show(self.session['files_' + self.toggle][self.index], preview = True)
        
        
        
    def __init_background_apply(self):
        F = ttk.Frame(self.sub_lf)
        self.ttk_widgets['background_apply'] = ttk.Button(F,
                                              text='Apply to all frames',
                                              command = self.apply_background_all,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['background_apply'].pack(padx=4, pady=2)
        F.pack(fill='x')
            
            
            
    def load_background_img(self):
        files = filedialog.askopenfilenames(multiple=True, 
                                            filetypes = (
                                            (".bmp","*.bmp"),
                                            (".jpeg","*.jpeg"),
                                            (".jpg","*.jpg"),
                                            (".pgm","*.pgm"),
                                            (".png","*.png"),
                                            (".tif","*.tif")))
        if len(files) > 0:
            if len(files) == 1:
                for i in range(len(self.session['files_a'])):
                        self.p['img_preproc'][f'{i}'][6] = files[0]
            else:
                for i in range(len(files)):
                    if i < len(self.session['files_a']):
                        self.p['img_preproc'][f'{i}'][6] = files[i]
                    else:
                        break;
            self.ttk_widgets['background_clear'].config(
                text = 'Clear background image(s)')
            print('Loaded background image(s)')
    
    
    
    def clear_background_img(self):
        self.get_settings()
        for i in range(len(self.session['files_a'])):
            self.p['img_preproc'][f'{i}'][6] = ''
            print('Finished frame: {}'.format(i))
        self.ttk_widgets['background_clear'].config(
            text = 'Cleared image list')
        print('Cleared all stored background images')
    
    
    
    def apply_background_all(self):
        self.get_settings()
        for i in range(len(self.session['files_a'])):
            self.p['img_preproc'][f'{i}'][5] = self.p['background_type']
            print('Finished frame: {}'.format(i))
                
        if self.p['background_type'] in ['global mean', 
                                         'minA - minB']:
            self.background_status_frame.config(bg = 'lime')
            self.ttk_widgets['background_status'].config(text = 'Background active',
                                                         bg = 'lime')
        elif(self.p['background_type'] in ['external (subtracted)',
                                           'external (multiplied)',
                                           'external (divided)']):
            if len(self.p['img_preproc'][f'{self.index}'][6]) > 2:
                self.background_status_frame.config(bg = 'lime')
                self.ttk_widgets['background_status'].config(text = 'Background active',
                                                             bg = 'lime') 
            else:
                self.background_status_frame.config(bg = self.b_color)
                self.ttk_widgets['background_status'].config(text = 'Background inactive',
                                                         bg = self.b_color)
        else:
            self.background_status_frame.config(bg = self.b_color)
            self.ttk_widgets['background_status'].config(text = 'Background inactive',
                                                         bg = self.b_color)
        print('Applied background removal settings to all frames')
        
        
        
            
    '''~~~~~~~~~~~~~~~~~~~windowing/PIV~~~~~~~~~~~~~~~~~~~~~'''
    def __init_windowing_hint(self):
        padx = 3
        pady = 2
        f = ttk.Frame(self.sub_lf)
        F = ttk.Frame(f)
        self.ttk_widgets['interr_label'] = ttk.Label(F,
            text=' interrogation window [px]')
        self.ttk_widgets['interr_label'].pack(side='left')
        self.ttk_widgets['overlap_label'] = ttk.Label(F,
                  text='overlap [px]  ')
        self.ttk_widgets['overlap_label'].pack(side='right')
        F.pack(fill='x')
        F = ttk.Frame(f)
        keys = [['corr_window_1', 'left'], 
                ['overlap_1', 'right']]
        self.windowing_vars = {}
        for key in keys:
            self.windowing_vars[key[0]] = tk.IntVar()
            self.windowing_vars[key[0]].set(self.p[key[0]])
            self.tkvars.update({key[0]: self.windowing_vars[key[0]]})
            self.ttk_widgets[key[0]] = ttk.Combobox(F,
                                      textvariable = self.tkvars[key[0]],
                                      width = 8, justify = 'center')
            self.ttk_widgets[key[0]]['values'] = self.p.hint[key[0]]
            CreateToolTip(self.ttk_widgets[key[0]], self.p.help[key[0]])
            self.ttk_widgets[key[0]].pack(side=key[1], padx=padx + 2, pady=pady)
            self.generateOnChange(self.ttk_widgets[key[0]])
            self.ttk_widgets[key[0]].bind('<<Change>>', self.find_percentage)
            self.ttk_widgets[key[0]].bind('<FocusOut>', self.find_percentage)
        F.pack(fill='x')
        F = ttk.Frame(f)
        self.overlap_percent = self.p['overlap_1']/self.p['corr_window_1']
        self.ttk_widgets['overlap_label'] = ttk.Label(F, 
            text = '= {}%'.format(int(_round(self.overlap_percent * 100))))
        self.ttk_widgets['overlap_label'].pack(side = 'right',padx=30)
        F.pack(fill='x', side='bottom')
        f.pack(fill='x')
    
    
    
    def __init_analyze_buttons(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['analyze_current'] = ttk.Button(f,
                                              text='Analyze current frame',
                                              command= lambda: self.start_processing(self.index),
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['analyze_current'].pack(padx=2, pady=2)
        f.pack(fill='x')
        f = ttk.Frame(self.lf)
        self.ttk_widgets['analyze_all'] = ttk.Button(f,
                                              text='Analyze all frames',
                                              command=self.start_processing,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['analyze_all'].pack(padx=2, pady=2)
        f.pack(fill='x')
        f = ttk.Frame(self.lf)
        self.ttk_widgets['clear_results'] = ttk.Button(f,
                                              text='Clear all results',
                                              command=self.clear_results,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['clear_results'].pack(padx=2, pady=2)
        f.pack(fill='x')
        self.progressbar = ttk.Progressbar(f,
                                           orient = 'horizontal',
                                           length = 200, 
                                           mode = 'indeterminate')
        self.progressbar.pack()
        
        self.process_type = ttk.Label(f, text = ' ')
        self.process_type.pack() 
        
        
        
    def stop_analysis(self, clear = True):
        self.p['analysis'] = False
        self.get_settings()
        
        
        
    def find_percentage(self, a):
        self.get_settings()
        self.overlap_percent = self.p['overlap_1']/self.p['corr_window_1']
        self.ttk_widgets['overlap_label'].config(
            text = '= {}%'.format(int(_round(self.overlap_percent * 100))))
    
    
    
    def find_overlap(self, a):
        self.get_settings()
        self.set_windowing(0)
        for i in range(2, 6):
            self.ttk_widgets[f'corr_window_{i}' + '_label'].config(
                text = '= {} '.format(
                    int(_round(self.overlap_percent * self.p[f'corr_window_{i}'], 0))))
    
    
    
    def set_windowing(self, a):
        self.get_settings()
        for i in range(2, 6):
            try:
                self.ttk_widgets[f'corr_window_{i}'].config(state = 'disabled')
                self.ttk_widgets[f'corr_window_{i}' + '_label'].config(state = 'disabled')
                self.tkvars[f'corr_window_{i}'].set(self.p[f'corr_window_{i}'])
            except:
                pass # wighet is not created yet 
        for i in range(2, 6):
            if self.p[f'pass_{i}']:
                try:
                    self.ttk_widgets[f'corr_window_{i}'].config(state = 'normal')
                    self.ttk_widgets[f'corr_window_{i}' + '_label'].config(state = 'normal')
                    self.tkvars[f'corr_window_{i}'].set(self.p[f'corr_window_{i}'])
                except:
                    pass # widget is not created yet
            else:
                break;
    
    
    
    def __init_val_set_first_pass(self):
        f = ttk.Frame(self.sub_lf)
        self.ttk_widgets['set_glob_val_first'] = ttk.Button(f,
                                              text='Set to first pass',
                                              command=self.set_first,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['set_glob_val_first'].pack(padx=2, pady=2)
        f.pack(fill='x')
        
        
        
    def set_first(self):
        self.get_settings()
        self.tkvars['sp_MinU'].set(self.p['fp_MinU'])
        self.tkvars['sp_MinV'].set(self.p['fp_MinV'])
        self.tkvars['sp_MaxU'].set(self.p['fp_MaxU'])
        self.tkvars['sp_MaxV'].set(self.p['fp_MaxV'])
                
                
                
    '''~~~~~~~~~~~~~~~~~~~~Calibration~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_load_calibration_button(self, key=None):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['load_calib_img_button'] = ttk.Button(f,
                                              text='Load calibration image',
                                              command=self.calibration_load,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['load_calib_img_button'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
        f = ttk.Frame(self.lf)
        self.ttk_widgets['sel_ref_distance_button'] = ttk.Button(f,
                                              text='Select reference distance',
                                              command=self.calibration_ref_dist,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['sel_ref_distance_button'].pack(padx=2, pady=2)
        f.pack(fill='x')

        
        
    def __init_apply_calibration_button(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['clear_calib_img_button'] = ttk.Button(f,
                                              text='Clear calibrations',
                                              command=self.calibration_clear,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['clear_calib_img_button'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
        f = ttk.Frame(self.lf)
        self.ttk_widgets['apply_calib_button'] = ttk.Button(f,
                                              text='Apply to all frames',
                                              command=self.calibration_apply_all,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['apply_calib_button'].pack(padx=2, pady=2)
        f.pack(fill='x')
        
        
        
    def calibration_load(self):
        calibration_image = filedialog.askopenfilenames(multiple=True, 
                                                        filetypes = (
                                                        (".bmp","*.bmp"),
                                                        (".jpeg","*.jpeg"),
                                                        (".jpg","*.jpg"),
                                                        (".pgm","*.pgm"),
                                                        (".png","*.png"),
                                                        (".tif","*.tif")))
        if len(calibration_image) > 0:
            if len(calibration_image) == 1:
                self.show(calibration_image[0], 
                              preproc=False)
            else:
                self.get_settings()
                warning = 'Please select only one calibration image.'
                if self.p['warnings']:
                    messagebox.showwarning(title='Error Message',
                                   message=warning)
                print(warning)
    
    
    
    def calibration_ref_dist(self):
        self.disable_widgets(exclude_tab = self.nb.index('current'))
        self.xy_coords = self.fig_canvas.mpl_connect('button_press_event', 
                                                      self.get_calib_coords)
        self.coord_counter = 0
        self.coords = []
        
        
    def get_calib_coords(self, event):
        if event.inaxes is not None:
            x, y = event.inaxes.transData.inverted().transform((event.x, event.y))
            self.coords.append((int(_round(x, 0)), int(_round(y, 0))))
            self.ax.plot(x, y, '.', color = 'red')
            self.fig.canvas.draw()
            print('Selected poimt at ' + str(self.coords[self.coord_counter]))
            self.coord_counter += 1
            if self.coord_counter == 2:
                self.disconnect(self.xy_coords)
                self.enable_widgets()
                self.ttk_widgets['mask_save'].config(state = 'disabled')
                print('Exiting interactive calibration')
                delx = (self.coords[1][0] - self.coords[0][0]) ** 2
                dely = (self.coords[1][1] - self.coords[0][1]) ** 2
                self.p['reference_dist'] = _round((delx + dely) ** 0.5, 4)
                self.tkvars['reference_dist'].set(self.p['reference_dist'])
                print('Set reference distance')
    
    
    
    def calibration_clear(self):
        self.disable_widgets(exclude_tab = self.nb.index('current'))
        self.coords = []
        self.coord_counter = 0
        self.p['reference_dist'] = 1
        self.tkvars['reference_dist'].set(self.p['reference_dist'])
        self.p['real_dist'] = 1
        self.tkvars['real_dist'].set(self.p['real_dist'])
        self.p['time_step'] = 1000
        self.tkvars['time_step'].set(self.p['time_step'])
        self.enable_widgets()
        print('Cleared scaling parameters')
    
    
    
    def calibration_apply_all(self):
        try: # protects gui from permenantly being disabed
            self.get_settings()
            self.disable_widgets(exclude_tab = self.nb.index('current'))
            scaling = self.p['reference_dist'] / self.p['real_dist']
            print(f'Scaling: {scaling}')
            scale = scaling / (self.p['time_step'] / 1000)
            print(f'Scaling with dt: {scale}')
            for i in range(len(self.session['files_a'])):
                self.session['results'][f'{i}'][8] = scale
            self.enable_widgets()
            print('Applied scaling to all frames')
        except:
            self.enable_widgets()
    
    
    
    '''~~~~~~~~~~~~~~~~~~~~Validation~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_set_vel_limits_button(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['set_vel_limits'] = ttk.Button(f,
                                              text='Set velocity limits',
                                              command = self.initialize_vel_interact,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['set_vel_limits'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
    
    
    def __init_apply_glob_val_first_pass_button(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['apply_glov_val_first_pass'] = ttk.Button(f,
                                              text='Apply to first pass',
                                              #command = ,
                                              style = 'h12.TButton',
                                              width=self.large_button_width)
        self.ttk_widgets['apply_glov_val_first_pass'].pack(padx=2, pady=2)
        f.pack(fill='x')
        
        
    
    def __init_apply_validation_button(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['validate_current'] = ttk.Button(f,
                                              text='Apply to current frame',
                                              command = lambda: self.start_postprocessing1(index = True),
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['validate_current'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
        f = ttk.Frame(self.lf)
        self.ttk_widgets['validate_all'] = ttk.Button(f,
                                              text='Apply to all frames',
                                              command = self.start_postprocessing1,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['validate_all'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
    
        
        
        
    def initialize_vel_interact(self):
        if len(self.session['results'][f'{self.index}']) > 1:
            self.disable_widgets(exclude_tab = self.nb.index('current'))
            self.get_settings()
            self.fig.clear()
            self.ax = self.fig.add_axes([0,0,1,1])
            vec_plot.scatter(self.data, self.fig, self.ax)
            self.fig.canvas.draw()
            self.toggle_selector = RectangleSelector(self.ax, 
                                                     self.onselect_vel_limit,
                                                     drawtype='box',
                                                     button=[1],
                                                     rectprops = dict(facecolor='k', 
                                                                      edgecolor='k', 
                                                                      alpha=1, 
                                                                      fill=False))
            self.roi_rect = self.fig_canvas.mpl_connect('key_press_event', self.toggle_selector)
            #plt.show()
        else:
            self.enable_widgets()
            print('No results found')
    
    
    
    def onselect_vel_limit(self, eclick, erelease):
        "eclick and erelease are matplotlib events at press and release."
        x1 = (_round(eclick.xdata, 3))
        y1 = (_round(eclick.ydata, 3))
        x2 = (_round(erelease.xdata, 3))
        y2 = (_round(erelease.ydata, 3))
        print('startposition: (%f, %f)' % (x1, y1))
        print('endposition  : (%f, %f)' % (x2, y2))
        self.tkvars['MinU'].set(x1)
        self.tkvars['MaxU'].set(y1)
        self.tkvars['MinV'].set(x2)
        self.tkvars['MaxV'].set(y2)
        self.terminate_vel_interact()
        self.toggle_selector.set_active(False)
            
            
            
    def terminate_vel_interact(self):
        self.disconnect(self.roi_rect)
        self.enable_widgets()
        self.show(self.session['files_' + self.toggle][self.index])
        print('Exited interactive velocity limits')
    
    
    '''~~~~~~~~~~~~~~~~~~~~Modify Comp.~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_apply_modify_compon_button(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['modify_current'] = ttk.Button(f,
                                              text='Apply to current frame',
                                              command = lambda: self.start_postprocessing2(index = True),
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['modify_current'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
        f = ttk.Frame(self.lf)
        self.ttk_widgets['modify_all'] = ttk.Button(f,
                                              text='Apply to all frames',
                                              command=self.start_postprocessing2,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['modify_all'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
    
    
    '''~~~~~~~~~~~~~~~~~~~~Exporting~~~~~~~~~~~~~~~~~~~~~~'''
    def __init_export_ASCI2(self):
        f = ttk.Frame(self.lf)
        self.ttk_widgets['export_ACII2_current'] = ttk.Button(f,
                                              text=self.p.label['export_current_button'],
                                              command = lambda: self.export_asci2(index = True),
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['export_ACII2_current'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
        f = ttk.Frame(self.lf)
        self.ttk_widgets['export_ACII2_all'] = ttk.Button(f,
                                              text=self.p.label['export_all_button'],
                                              command=self.export_asci2,
                                              style = self.bold_apply,
                                              width=self.large_button_width)
        self.ttk_widgets['export_ACII2_all'].pack(padx=2, pady=2)
        f.pack(fill='x')
    
    
    def export_asci2(self, index = None):
        self.get_settings()
        dirr = filedialog.askdirectory()
        if len(dirr) > 1:
            if index != None:
                results = self.session['results'][f'{self.index}']
                x = results[2] / results[8]
                y = results[3] / results[8]
                u = results[4] / results[8]
                v = results[5] / results[8]
                tp = results[6]
                delimiter = self.p['separator']
                if self.p['asci2_delimiter'] == 'tab':
                    delimiter = '\t'
                elif self.p['asci2_delimiter'] == 'space':
                    delimiter = ' '
                else:
                    delimiter = self.p['asci2_delimiter']
                filename = os.path.join(dirr, str(str(self.index).zfill(math.ceil(
                                                    math.log10(len(self.session['files_a']))))))
                save(x, y, u, v, tp, filename = filename, delimiter = delimiter)
            else:
                for i in range(len(self.session['results'])):
                    results = self.session['results'][f'{i}']
                    if results > 2:
                        x = results[2] / results[8]
                        y = results[3] / results[8]
                        u = results[4] / results[8]
                        v = results[5] / results[8]
                        tp = results[6]
                        if self.p['asci2_delimiter'] == 'tab':
                            delimiter = '\t'
                        elif self.p['asci2_delimiter'] == 'space':
                            delimiter = ' '
                        else:
                            delimiter = self.p['asci2_delimiter']
                        filename = os.path.join(dirr, 'frame: ' + str(str(i).zfill(math.ceil(
                                                        math.log10(len(self.session['files_a']))))))
                        save(x, y, u, v, tp, filename = filename, delimiter = delimiter)
                    else:
                        break;
                    
    
    def generateOnChange(self, obj):
        # idea from https://stackoverflow.com/questions/3876229/how-to-run-a-code-whenever-a-tkinter-widget-value-changes
        obj.tk.eval('''
            proc widget_proxy {widget widget_command args} {

                # call the real tk widget command with the real args
                set result [uplevel [linsert $args 0 $widget_command]]

                # generate the event for certain types of commands
                if {([lindex $args 0] in {insert replace delete}) ||
                    ([lrange $args 0 2] == {mark set insert}) || 
                    ([lrange $args 0 1] == {xview moveto}) ||
                    ([lrange $args 0 1] == {xview scroll}) ||
                    ([lrange $args 0 1] == {yview moveto}) ||
                    ([lrange $args 0 1] == {yview scroll})} {

                    event generate  $widget <<Change>> -when tail
                }

                # return the result from the real widget command
                return $result
            }
            ''')
        obj.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy {widget} _{widget}
        '''.format(widget=str(obj)))
        
        
        
    def disconnect(self, connected):
        self.fig_canvas.mpl_disconnect(connected)
    
    
    
    def update_widget_state(self):
        widgets = {}
        widgets = {
                   'median_filter':[
                       'median_filter_size'
                   ],
                   'CLAHE':[
                       'CLAHE_auto_kernel', 
                       'CLAHE_kernel',
                       'CLAHE_contrast'
                   ],
                   'high_pass_filter':[
                       'hp_sigma'
                   ],
                   'intensity_cap_filter':[
                       'ic_mult'
                   ],
                   'intensity_clip':[
                       'intensity_clip_min'
                   ],
                   'wiener_filter':[
                       'wiener_filter_size'
                   ],
                   'gaussian_filter':[
                       'gf_sigma'
                   ],
                   'fp_local_med_threshold':[
                       'fp_local_med',
                       'fp_local_med_size',
                   ],
                   'fp_vld_global_threshold':[
                       'fp_MinU',
                       'fp_MaxU',
                       'fp_MinV',
                       'fp_MaxV',
                   ],
                   'sp_local_med_validation':[
                       'sp_local_med',
                       'sp_local_med_size',
                   ],
                   'sp_vld_std_threshold':[
                       'sp_std_threshold'
                   ],
                   'sp_vld_global_threshold':[
                       'sp_MinU',
                       'sp_MaxU',
                       'sp_MinV',
                       'sp_MaxV',
                   ],
                   'pass_repl':[
                       'pass_repl_method',
                       'pass_repl_iter',
                       'pass_repl_kernel'
                   ],
                   'smoothn_each_pass':[
                       'smoothn_first_more',
                       'robust1',
                       'smoothn_val1'
                   ],
                    'vld_global_thr':[
                       'MinU',
                       'MaxU',
                       'MinV',
                       'MaxV',
                   ],
                   'vld_global_std':[
                       'global_std_threshold'
                   ],
                   'vld_local_med':[
                       'local_median_threshold',
                       'local_median_size'
                   ],
                   'repl':[
                       'repl_method',
                       'repl_iter',
                       'repl_kernel',
                   ],
                   'smoothn':[
                       'robust',
                       'smoothn_val',
                   ],
                   'offset_grid':[
                       'offset_x',
                       'offset_y',
                   ],
                   'modify_velocity':[
                       'modify_u',
                       'modify_v',
                   ]}
        
        self.get_settings()
        for key, keys in widgets.items():
            if self.p[key] == True:       
                for i in range(len(keys)):
                    self.ttk_widgets[keys[i]].config(state = 'normal') 
                    try:
                         self.ttk_widgets[keys[i]+ '_label'].config(state = 'normal')
                    except: pass # no label
                    if key == 'sp_vld_global_threshold':
                        self.ttk_widgets['set_glob_val_first'].config(state = 'normal')
                    elif key == 'vld_global_thr':
                        self.ttk_widgets['set_vel_limits'].config(state = 'normal')
                        self.ttk_widgets['apply_glov_val_first_pass'].config(state = 'normal')
            else:
                for i in range(len(keys)):
                    self.ttk_widgets[keys[i]].config(state = 'disabled')
                    try:
                         self.ttk_widgets[keys[i]+ '_label'].config(state = 'disabled')
                    except: pass # no label
                    if key == 'sp_vld_global_threshold':
                        self.ttk_widgets['set_glob_val_first'].config(state = 'disabled')
                    elif key == 'vld_global_thr':
                        self.ttk_widgets['set_vel_limits'].config(state = 'disabled')
                        self.ttk_widgets['apply_glov_val_first_pass'].config(state = 'disabled')
                        
                        
                        
    def update_widget_state2(self, state = 'normal', _type = 0, apply = True):
        if _type == 0:
            if apply == True:
                self.ttk_widgets['apply_frequence_button'].config(state = state)
            self.ttk_widgets['toggle_frames_button'].config(state = state)
            self.lb.config(state = state)    
            self.ttk_widgets['select_roi'].config(state = state)
            self.ttk_widgets['clear_roi'].config(state = state)
            self.ttk_widgets['apply_roi'].config(state = state)
            self.ttk_widgets['mask_select'].config(state = state)
            self.ttk_widgets['mask_clear'].config(state = state)
            self.ttk_widgets['mask_save'].config(state = state)
            self.ttk_widgets['mask_load'].config(state = state)
            self.ttk_widgets['mask_load_applied'].config(state = state)
            self.ttk_widgets['mask_apply_current'].config(state = state)
            self.ttk_widgets['mask_apply_all'].config(state = state)
            self.ttk_widgets['background_load'].config(state = state)
            self.ttk_widgets['background_clear'].config(state = state)
            self.ttk_widgets['background_apply'].config(state = state)
            self.ttk_widgets['preview_preproc_current'].config(state = state)
            self.ttk_widgets['analyze_current'].config(state = state)
            self.ttk_widgets['analyze_all'].config(state = state)
            self.ttk_widgets['clear_results'].config(state = state)
            self.ttk_widgets['load_calib_img_button'].config(state = state)
            self.ttk_widgets['sel_ref_distance_button'].config(state = state)
            self.ttk_widgets['clear_calib_img_button'].config(state = state)
            self.ttk_widgets['apply_calib_button'].config(state = state)
            self.ttk_widgets['validate_current'].config(state = state)
            self.ttk_widgets['validate_all'].config(state = state)
            self.ttk_widgets['modify_current'].config(state = state)
            self.ttk_widgets['modify_all'].config(state = state)
        elif _type == 1:
            self.ttk_widgets['select_roi'].config(state = state)
            self.ttk_widgets['clear_roi'].config(state = state)
            self.ttk_widgets['apply_roi'].config(state = state)
            self.ttk_widgets['mask_select'].config(state = state)
            self.ttk_widgets['mask_clear'].config(state = state)
            self.ttk_widgets['mask_save'].config(state = state)
            self.ttk_widgets['mask_load'].config(state = state)
            self.ttk_widgets['mask_load_applied'].config(state = state)
            self.ttk_widgets['mask_apply_current'].config(state = state)
            self.ttk_widgets['mask_apply_all'].config(state = state)
            self.ttk_widgets['background_load'].config(state = state)
            self.ttk_widgets['background_clear'].config(state = state)
            self.ttk_widgets['background_apply'].config(state = state)
            self.ttk_widgets['preview_preproc_current'].config(state = state)
        
        
    def check_exclusion(self, ignore_blank = False):
        self.get_settings()
        try:
            xmin = self.p['img_preproc']['{}'.format(self.index)][0]
            xmax = self.p['img_preproc']['{}'.format(self.index)][1]
            ymin = self.p['img_preproc']['{}'.format(self.index)][2]
            ymax = self.p['img_preproc']['{}'.format(self.index)][3]
            
            if xmin and xmax and ymin and ymax != ('', ' '):
                self.ttk_widgets['roi_status'].config(bg = 'lime', text = 'ROI active')
                self.roi_status_frame.config(bg = 'lime')  
            else:
                self.roi_status_frame.config(bg = self.b_color) 
                self.ttk_widgets['roi_status'].config(bg = self.b_color,
                                                      text = 'ROI inactive')
                
            if self.p['roi-xmin'] and self.p['roi-ymin'] and self.p['roi-xmax'] and self.p['roi-ymax'] == ('', ' '):
                #and ignore_blank != True:
                print('Setting ROI widgets to selected ROI of image')
                self.tkvars['roi-xmin'].set(xmin)
                self.tkvars['roi-ymin'].set(ymin)
                self.tkvars['roi-xmax'].set(xmax)
                self.tkvars['roi-ymax'].set(ymax)
                self.ttk_widgets['roi_status'].config(bg = 'lime', text = 'ROI active')
                self.roi_status_frame.config(bg = 'lime') 
        except Exception as e:
            print('Could not check ROI status \nReason: '+str(e))
            
        if len(self.session['results'][f'{self.index}']) == 0:
            self.update_widget_state2(state = 'normal', _type = 1)   
            
        if len(self.p['img_preproc']['{}'.format(self.index)][4]) > 0:
            self.mask_status_frame.config(bg = 'lime')
            self.ttk_widgets['mask_status'].config(bg = 'lime', text = 'Mask active')
            self.ttk_widgets['mask_select'].config(state = 'disabled')
        else:
            self.mask_status_frame.config(bg = self.b_color)
            self.ttk_widgets['mask_status'].config(bg = self.b_color, text = 'Mask inactive'.format(self.mask_counter))
            self.ttk_widgets['mask_select'].config(state = 'normal')
            
        if len(self.object_mask) == 0:
            self.ttk_widgets['mask_save'].config(state = 'disabled')
        else:
            self.ttk_widgets['mask_save'].config(state = 'normal')
            
        if len(self.session['results'][f'{self.index}']) > 0:
            self.update_widget_state2(state = 'disabled', _type = 1)
        
        if self.p['img_preproc'][f'{self.index}'][5] in [
                'global mean', 
                'minA - minB']:
            self.background_status_frame.config(bg = 'lime')
            self.ttk_widgets['background_status'].config(text = 'Background active',
                                                         bg = 'lime')
            
        elif(self.p['img_preproc'][f'{self.index}'][5] in [
                'external (subtracted)',
                'external (multiplied)',
                'external (divided)']):
            if len(self.p['img_preproc'][f'{self.index}'][6]) > 2:
                self.background_status_frame.config(bg = 'lime')
                self.ttk_widgets['background_status'].config(text = 'Background active',
                                                             bg = 'lime')  
            else:
                self.background_status_frame.config(bg = self.b_color)
                self.ttk_widgets['background_status'].config(text = 'Background inactive',
                                                         bg = self.b_color)
        else:
            self.background_status_frame.config(bg = self.b_color)
            self.ttk_widgets['background_status'].config(text = 'Background inactive',
                                                         bg = self.b_color)
        
        self.ttk_widgets['show_masked_vectors'].config(state = 'disabled')

            
            
    def log(self, columninformation=None, timestamp=False, text=None,
            group=None):
        ''' Add an entry to the lab-book.

        The first initialized text-area is assumed to be the lab-book.
        It is internally accessible by self.ta[0].

        Parameters
        ----------
        timestamp : bool
            Print current time.
            Pattern: yyyy-mm-dd hh:mm:ss.
            (default: False)
        text : str
            Print a text, a linebreak is appended. 
            (default None)
        group : int
            Print group of parameters.
            (e.g. OpenPivParams.PIVPROC)
        columninformation : list
            Print column information of the selected file.

        Example
        -------
        log(text='processing parameters:', 
            group=OpenPivParams.POSTPROC)
        '''
        if text is not None:
            self.ta[0].insert(tk.END, text + '\n')
        if timestamp:
            td = datetime.today()
            s = '-'.join((str(td.year), str(td.month), str(td.day))) + \
                ' ' + \
                ':'.join((str(td.hour), str(td.minute), str(td.second)))
            self.log(text=s)
        if group is not None:
            self.log(text='Parameters:')
            for key in self.p.param:
                key_type = self.p.type[key]
                if key_type not in ['labelframe', 'sub_labelframe', 'h-spacer',
                                    'sub_h-spacer', 'post_button', 'dummy']:
                    if group < self.p.index[key] < group+1000:
                        s = key + ': ' + str(self.p[key])
                        self.log(text=s)
        if columninformation is not None:
            self.ta[0].insert(tk.END, str(columninformation) + '\n')

            
            
    def show_informations(self, fname):
        ''' Shows the column names of the chosen file in the labbook.

        Parameters
        ----------
        fname : str
            A filename.
        '''
        data = self.load_pandas(fname)
        if isinstance(data, str) == True:
            self.log(text=data)
        else:
            self.log(columninformation=list(data.columns.values))

            
            
    def get_settings(self):
        '''Copy widget variables to the parameter object.'''
        for key in self.tkvars:
            if self.p.type[key] == 'str[]':
                try:
                    self.p[key] = str2list(self.tkvars[key].get())
                except Exception as e:
                    print(str(e))
            else:
                try:
                    self.p[key] = self.tkvars[key].get()
                except Exception as e:
                    print(str(e))
        self.__get_text('lab_book_content', self.ta[0])
        self.__get_text('user_func_def', self.ta[1])
    
    
    
    def create_session(self):
        self.session = {}
        self.session['img_list'] = []
        self.session['files_a'] = []
        self.session['files_b'] = []
        self.session['frames_a'] = []
        self.session['frames_b'] = []
        self.session['results'] = {}
        self.session['file_num'] = 'N/A'
        self.session['frame_num'] = 'N/A'
        try:
            self.num_of_frames.config(text = self.session['frame_num'])
            self.num_of_files.config(text = self.session['file_num'])
            self.toggle = 'a'
            self.p['fnames'] = self.session['frames_a']
            self.tkvars['fnames'].set(self.p['fnames'])
            self.p['img_list'] = self.session['img_list']
            self.tkvars['img_list'].set(self.p['img_list'])
            self.update_widget_state2(state = 'disabled')   
        except: pass # widgets not created yet
       
        
        
    def load_session(self, _type = None):
        if _type == None:
            file = filedialog.askopenfilename(title = 'Session Manager',
                                              defaultextension = '.npy',
                                              filetypes = [('npy', '*.npy'), ])
        else:
            file = self.p.session_file
            
        if len(file) > 0:
            session = (np.load(file, allow_pickle = True))
            self.create_session()
            
            self.session['img_list'] = session.item().get('img_list')
            self.session['files_a'] = session.item().get('files_a')
            self.session['files_b'] = session.item().get('files_b')
            self.session['frames_a'] = session.item().get('frames_a')
            self.session['frames_b'] = session.item().get('frames_b')
            self.session['results'] = dict(session.item().get('results'))
            
            if len(self.session['files_a']) > 0:
                self.session['file_num'] = str(len(self.session['img_list']))
                self.session['frame_num'] = str(len(self.session['files_a']) - 1)
            else:
                self.session['file_num'] = 'N/A'
                self.session['frame_num'] = 'N/A'
            self.num_of_frames.config(text = self.session['frame_num'])
            self.num_of_files.config(text = self.session['file_num'])
            
            self.toggle = 'a'
            self.p['fnames'] = self.session['frames_a']
            self.tkvars['fnames'].set(self.p['fnames'])
            self.p['img_list'] = self.session['img_list']
            self.tkvars['img_list'].set(self.p['img_list'])
            
            if len(self.session['files_a']) == 0 and len(self.session['img_list']) == 0:
                self.update_widget_state2(state = 'disabled')
                
            elif len(self.session['files_a']) == 0 and len(self.session['img_list']) != 0:
                self.update_widget_state2(state = 'disabled')
                self.ttk_widgets['apply_frequence_button'].config(state = 'normal')
                
            elif len(self.session['files_a']) != 0:
                self.update_widget_state2(state = 'normal')
            
        
        
        
    def set_settings(self):
        '''Copy values of the parameter object to widget variables.'''
        for key in self.tkvars:
            if key not in ('img_list', 'fnames'):
                try:
                    self.tkvars[key].set(self.p[key])
                except Exception as e: # if an error occurs, shorten the output
                    print(str(e))
        self.ta[0].delete('1.0', tk.END)
        self.ta[0].insert('1.0', self.p['lab_book_content'])
        self.ta[1].delete('1.0', tk.END)
        self.ta[1].insert('1.0', self.p['user_func_def'])
        self.num_of_frames.config(text=self.session['frame_num'])
        self.num_of_files.config(text=self.session['file_num'])
        
    
    
    def clear_results(self, update_plot = True):
        self.session['results'] = {}
        for i in range(len(self.session['files_a'])):
            self.session['results'][f'{i}'] = []
        
        if update_plot:
            self.show(self.session['files_' + self.toggle][self.index])
        print('Cleared results for all frames')
            
            
            
    def select_image_files(self):
        '''Show a file dialog to select one or more filenames.'''
        print('Use Ctrl + Shift to select multiple files.')
        files = filedialog.askopenfilenames(multiple=True, filetypes = ((".bmp","*.bmp"),
                                                                        (".jpeg","*.jpeg"),
                                                                        (".jpg","*.jpg"),
                                                                        (".pgm","*.pgm"),
                                                                        (".png","*.png"),
                                                                        (".tif","*.tif"),
                                                                        ("all files","*.*")))
        if len(files) > 0:
            if len(files)==1:
                self.get_settings()
                warning = 'Please import two or more images.'
                if self.p['warnings']:
                    messagebox.showwarning(title='Error Message',
                                   message=warning)
                print(warning)
            else:
                self.create_session()
                
                self.p['img_list'] = list(files)
                self.session['img_list'] = self.p['img_list']
                self.tkvars['img_list'].set(self.p['img_list'])
                self.session['file_num'] = str(len(files))
                self.session['frame_num'] = 'N/A'
                self.num_of_files.config(text = str(self.session['file_num']))
                self.num_of_frames.config(text = self.session['frame_num'])
                self.xy_connect = self.fig_canvas.mpl_connect('motion_notify_event', 
                                                      self.change_xy_current)
                self.update_widget_state2(state = 'disabled', apply = False)
                self.ttk_widgets['apply_frequence_button'].config(state = 'normal')
                self.show(self.p['img_list'][0], preproc = False, perform_check = False)
        
        
        
    def show(self, fname, preview = False, preproc = True, show_roi = True, 
             show_mask = True, perform_check = True, ignore_blank = False):
        '''Display a file.

        This method distinguishes vector data (file extensions
        txt, dat, jvc,vec and csv) and images (all other file extensions).

        Parameters
        ----------
        fname : str
            A filename.
        '''
        self.get_settings()
        self.fig.clear()
        self.ax = self.fig.add_axes([0,0,1,1])
        if perform_check:
            self.check_exclusion(ignore_blank = ignore_blank)
        
        try:
            if len(self.session['results'][f'{self.index}']) > 0:
                results = self.session['results']['{}'.format(self.index)]
                try:
                    x = results[2] + int(results[0][0])
                    y = results[3] + int(results[0][2])
                except: # no roi selected
                    x = results[2]
                    y = results[3]
                
                
                data = np.vstack([m.ravel() for m in [x,
                                                      y,
                                                      results[4],
                                                      results[5],
                                                      results[6],
                                                     ]]).T
                self.data = pd.DataFrame(data, columns = ['x', 
                                                          'y', 
                                                          'vx', 
                                                          'vy', 
                                                          'tp',
                                                         ])
                show_results = True 
            else:
                show_results = False
        except Exception as e: 
            show_results = False
            
        if show_results == True and len(self.session['results'][f'{self.index}']) > 0:
            raw_img = piv_tls.imread(self.session['files_{}'.format(self.toggle)][self.index])
            xmin = results[0][0]
            xmax = results[0][1]
            ymin = results[0][2]
            ymax = results[0][3]
            img = self.process_disp_img(
                    img = raw_img,
                    axes = self.ax,
                    roi_coords = [
                    xmin,
                    xmax,
                    ymin,
                    ymax,
                ], 
                mask_coords = results[7],
                show_mask = False,
                show_roi = True
            )
            
            if self.p['plot_type'] == 'vectors':
                vec_plot.vector(
                    self.data,
                    self.fig,
                    self.ax,
                    image = img,
                    mask_coords = results[7],
                    interr_win = results[1],
                    scale = self.p['vec_scale'],
                    width = self.p['vec_width'],
                    valid_color = self.p['valid_color'],
                    invalid_color = self.p['invalid_color'],
                    show_mask_vecs = False,
                    mask_vec_style = self.p['mask_vec_style'],
                    mask_vec_color = self.p['mask_vec'],
                    disp_mask_color = self.p['mask_fill'],
                    disp_mask_alpha = self.p['mask_alpha']
                )
            elif self.p['plot_type'] == 'contours':
                vec_plot.contour(
                    self.data,
                    self.p,
                    self.fig,
                    self.ax,
                    image = img,
                    mask_coords = results[7],
                    interr_win = results[1],
                    scale = self.p['vec_scale'],
                    width = self.p['vec_width'],
                    valid_color = self.p['valid_color'],
                    invalid_color = self.p['invalid_color'],
                    show_mask_vecs = False,
                    mask_vec_style = self.p['mask_vec_style'],
                    mask_vec_color = self.p['mask_vec'],
                    disp_mask_color = self.p['mask_fill'],
                    )
            elif self.p['plot_type'] == 'profiles':
                vec_plot.profiles(self.data, self.p,
                                  self.fig,
                                  orientation=self.p['profiles_orientation']
                                  )
            elif self.p['plot_type'] == 'scatter':
                vec_plot.scatter(self.data,
                                 self.fig
                                 )
            elif self.p['plot_type'] == 'streamlines':
                vec_plot.streamlines(self.data,
                                     self.p,
                                     self.fig)
            else:
                vec_plot.pandas_plot(self.data,
                                     self.p,
                                     self.fig)
            try:           
                if xmin and xmax and ymin and ymax != ('', ' '):
                    add_disp_roi(self.ax,
                                 int(xmin), int(ymin), int(xmax), int(ymax),
                                 linewidth = self.p['roi_border_width'],
                                 edgecolor = self.p['roi_border'],
                                 linestyle = self.p['roi_line_style'])
            except Exception as e:
                print('Ignoring roi exclusion objects \nReason: ' + str(e))
        else:
            self.show_img(fname, axes = self.ax, preview = preview,
                          preproc = preproc, show_roi = show_roi, show_mask = show_mask)
        self.fig.canvas.draw()

        
        
    def show_img(self, fname, axes, preview = False, preproc=True,
                 show_roi = True, show_mask = True):
        '''Display an image.

        Parameters
        ----------
        fname : str
            Pathname of an image file.
        '''
        img = piv_tls.imread(fname)
        print('\nimage data type: {}'.format(img.dtype))
        if 'int' not in str(img.dtype):
            print('Warning: For PIV processing, ' +
                  'image will be normalized and converted to uint8. ' +
                  'This may cause a loss of precision.')
            
        print('Processing image')
        img = img.astype(np.int32)
        if preproc:
            img = self.process_disp_img(
                img = img,
                axes = axes,
                roi_coords = [
                    self.p['img_preproc']['{}'.format(self.index)][0],
                    self.p['img_preproc']['{}'.format(self.index)][1],
                    self.p['img_preproc']['{}'.format(self.index)][2],
                    self.p['img_preproc']['{}'.format(self.index)][3],
                ], 
                mask_coords = self.p['img_preproc']['{}'.format(self.index)][4],
                preview = preview, preproc = preproc, show_roi = show_roi, show_mask = show_mask
            )
        else:
            img = process_images(img, preproc = False)
        print('Processed image')
        
        axes.matshow(img, cmap=plt.cm.Greys_r,
                        vmax=self.p['matplot_intensity'])
        axes.xaxis.set_major_formatter(plt.NullFormatter())
        axes.yaxis.set_major_formatter(plt.NullFormatter())
        axes.set_xticks([])
        axes.set_yticks([])
        self.fig.canvas.draw()
    
    
    
    def process_disp_img(self, 
                         img,
                         axes,
                         roi_coords,
                         mask_coords, 
                         preview = False,
                         preproc = True,
                         show_roi = True, 
                         show_mask = True):
        
        img = img
        raw_img = process_images(img, preproc = False)
        raw_img = raw_img.astype(np.uint8)
        
        if preproc:
            # generate background if needed
            '''if self.p['background_subtract'] == True and self.p['background_type'] != 'minA - minB':
                background = gen_background(self.p)

            elif self.p['background_subtract'] == True and self.p['background_type'] == 'minA - minB':
                if fname == self.p['fnames'][-1]:
                    img2 = self.p['fnames'][-2]
                    img2 = piv_tls.imread(img2)
                    background = gen_background(self.p, img2, img)
                else:
                    img2 = self.p['fnames'][self.index + 1]
                    img2 = piv_tls.imread(img2)
                    background = gen_background(self.p, img, img2)
            else:
                background = None'''
                
            if len(roi_coords) > 1:
                xmin = roi_coords[0]
                xmax = roi_coords[1]
                ymin = roi_coords[2]
                ymax = roi_coords[3]
            
            else:
                xmin = ''
                xmax = ''
                ymin = ''
                ymax = ''
            if preview:
                img = process_images(img, 
                                     preproc=preproc,
                                     roi_xmin = xmin,
                                     roi_xmax = xmax,
                                     roi_ymin = ymin,
                                     roi_ymax = ymax,
                                     do_background          = False,
                                     background             = None,
                                     invert                 = self.p['invert'],
                                     median_filt            = self.p['median_filter'],
                                     median_kernel          = self.p['median_filter_size'],
                                     CLAHE                  = self.p['CLAHE'],
                                     CLAHE_auto_kernel      = self.p['CLAHE_auto_kernel'],
                                     CLAHE_kernel           = self.p['CLAHE_kernel'],
                                     CLAHE_clip             = self.p['CLAHE_contrast'],
                                     high_pass              = self.p['high_pass_filter'],
                                     hp_sigma               = self.p['hp_sigma'],
                                     intensity_cap          = self.p['intensity_cap_filter'],
                                     ic_mult                = self.p['ic_mult'],
                                     intensity_clip         = self.p['intensity_clip'],
                                     intensity_clip_min     = self.p['intensity_clip_min'],
                                     wiener_filt            = self.p['wiener_filter'],
                                     wiener_size            = self.p['wiener_filter_size'],
                                     gaussian_filt          = self.p['gaussian_filter'],
                                     gf_sigma               = self.p['gf_sigma'])
            else:
                img = process_images(img, 
                                     preproc=preproc,
                                     roi_xmin = xmin,
                                     roi_xmax = xmax,
                                     roi_ymin = ymin,
                                     roi_ymax = ymax,
                                     do_background          = False,
                                     background             = None,
                                     invert                 = self.p['invert'],
                                     median_filt            = False,
                                     CLAHE                  = False,
                                     high_pass              = False,
                                     intensity_cap          = False,
                                     intensity_clip         = False,
                                     wiener_filt            = False,
                                     gaussian_filt          = False)
            
            img = img.astype(np.uint8)
            #try:
            if 1 == 1:
                if xmin and xmax and ymin and ymax != ('', ' '):
                    if show_roi:
                        xmin = int(xmin)
                        xmax = int(xmax)
                        ymin = int(ymin)
                        ymax = int(ymax)

                        raw_img[ymin:ymax, xmin:xmax] = img
                        img = raw_img 
                        add_disp_roi(axes, 
                                     xmin, ymin, xmax, ymax,
                                     linewidth = self.p['roi_border_width'],
                                     edgecolor = self.p['roi_border'],
                                     linestyle = self.p['roi_line_style'])
                if show_mask:
                    add_disp_mask(axes, mask_coords,
                                  color = self.p['mask_fill'],
                                  alpha = self.p['mask_alpha'])
            #except Exception as e:
            #    print('Ignoring image exclusion preview \nReason: '+str(e))

        else:
            img = raw_img
        return(img)
            
    
                        
    def destroy(self):
        '''Destroy the OpenPIV GUI.

        Settings are automatically saved.
        '''
        if messagebox.askyesno('Exit Manager', 'Are you sure you want to exit?'):
            
            self.get_settings()
            if self.p['save_on_exit']:
                print('Saving settings and session')
                self.p.dump_settings(self.p.params_fname)
                self.p.dump_session(self.p.session_file, self.session)
            tk.Tk.quit(self)
            tk.Tk.destroy(self)
            # sometimes the GUI closes, but the main thread still runs
            print('Destorying main thread')
            sys.exit()
            print('Destoryed main thread.') # This should not execute if the thread is destroyed. 
                                            # Could cause possible issue in the future.

if __name__ == '__main__':
    openPivGui = OpenPivGui()
    openPivGui.geometry("1200x710") # a good starting size for the GUI
    openPivGui.mainloop()
