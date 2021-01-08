#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''A class for simple parameter handling.

This class is also used as a basis for automated widget creation
by OpenPivGui.
'''

import os
import json
from numpy import save, load
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

example_user_function = '''
filelistbox = self.get_filelistbox()
properties  = self.p
import pandas as pd

def textbox(title='Title', text='Hello!'):
    from tkinter.scrolledtext import ScrolledText
    from tkinter.constants import END
    frame = tk.Tk()
    frame.title(title)
    textarea = ScrolledText(frame, height=10, width=80)
    textarea.insert(END, text)
    textarea.pack(fill='x', side='left', expand=True)
    textarea.focus()
    frame.mainloop()

try:
    index = filelistbox.curselection()[0]
except IndexError:
    messagebox.showerror(
        title="No vector file selected.",
        message="Please select a vector file " +
                "in the file list and run again."
    )
else:
    f = properties['fnames'][index]
    names=('x','y','v_x','v_y','var')
    df = pd.read_csv(f, sep='\t', header=None, names=names)
    print(df.describe())
    textbox(title='Statistics of {}'.format(f),
            text=df.describe()
    )
'''

class OpenPivParams():
    '''A class for convenient parameter handling.

    Widgets are automatically created based on the content of the
    variables in the dictionary OpenPivParams.default.

    The entries in OpenPivParams.default are assumed to follow this
    pattern:

    (str) key:
        [(int) index, 
         (str) type, 
         value,
         (tuple) hints,
         (str) label,
         (str) help]

    The index is used for sorting and grouping, because Python 
    dictionaries below version 3.7 do not preserve their order. A 
    corresponding input widged ist chosen based on the type string:

        None:                    no widget, no variable, but a rider
        boolean:                 checkbox
        str[]:                   listbox
        text:                    text area
        other (float, int, str): entry (if hints not None: option menu)

    A label is placed next to each input widget. The help string is
    displayed as a tooltip.

    The parameter value is directly accessible via indexing the base
    variable name. For example, if your OpenPivParams object variable
    name is »my_settings«, you can access a value by typing:

    my_settings[key] 

    This is a shortcut for my_settings.param[key]. To access other 
    fields, use my_settings.label[key], my_settings.help[key] and so on.
    '''

    def __init__(self):
        # hard coded location of the parameter file in the home dir:
        self.params_fname = os.path.expanduser('~' + os.sep +
                                               'open_piv_gui.json')
        self.session_file = os.path.expanduser(r'~' + os.sep +
                                                 'openpivgui_session.npy')
        # grouping and sorting based on an index:
        self.GENERAL = 1000
        self.PREPROC = 2000
        self.PIVPROC = 3000
        self.CALIBRATION = 5000
        self.VALIDATION = 6000
        self.POSTPROC = 7000
        self.PLOTTING = 8000
        self.LOGGING = 9000
        self.USER = 10000
        # remember the current file filter
        # (one of the comma separated values in ['navi_pattern']):
        self.navi_position = 0
        # these are the default parameters, basis for widget creation:
        self.default = {
            #########################################################
            # Place additional variables in the following sections. #
            # Widgets are created automatically. Don't care about   #
            # saving and restoring - new variables are included     #
            # automatically.                                        #
            #########################################################
            # general and image import
            'load':
                [1000,
                 None,        # type None: This will create a rider.
                 None,
                 None,
                 'Load Menu',
                 None],
            
            'analysis': # if set false, the analysis will be stopped and cleared
                [1005, 'dummy', True,
                None,
                None,
                None],
            
            'img_preproc':
                [1010, 'dummy', {},
                None,
                None,
                None],
            
            'loading_frame':
                [1015, 'labelframe', None,
                 None,
                 'Load Images/Movie',
                 None],
            
            'load_img_button':
                [1020, 'dummy', None,
                None,
                'Load Images',
                None],
            
            'img_list':
                [1022, 'str[]', [],
                None,
                'image list',
                None],
         
            'fnames':
                [1023,        # index, here: group GENERAL
                 'str[]',     # type
                 [],          # value
                 None,        # hint (used for option menu, if not None)
                 'filenames',  # label
                 None],       # help (tooltip)
            
            'sequence':
                [1030, 'str', '(1+2),(3+4)',
                 ('(1+2),(1+3)','(1+2),(2+3)', '(1+2),(3+4)'),
                 'sequence order',
                 'Select sequence order for evaluation.'],

            'skip':
                [1035, 'int', 1,
                 None,
                 'jump',
                 'Select sequence order jump for evaluation.' +
                 '\nEx: (1+(1+x)),(2+(2+x))'],
            
            'apply_frequence':
                [1040, 'dummy', None,
                None,
                'Apply Frequencing',
                None],
            
            'General':
                [1200, None, None,
                None,
                'General',
                None],
            
            'general_frame':
                [1215, 'labelframe', None,
                 None,
                 'General settings',
                 None],
            
            'warnings':
                [1220, 'bool', True, None,
                 'Enable popup warnings',
                 'Enable popup warning messages (recommended).'],
            
            'pop_up_info':
                [1225, 'bool', True, None,
                 'Enable popup info',
                 'Enable popup information messages (recommended).'],
            
            'save_on_exit':
                [1230, 'bool', True, None,
                 'save on exit',
                 'Save current settings and session to the Users folder when exiting.'],
            
           # 'open_on_start':
           #     [1235, 'bool', 'True', None,
           #      'open on start',
           #      'Open current settings and session from the Users folder when initializing GUI.'],
            
            'unbold_buttons':
                [1240, 'bool', True, 'bind2',
                 'unbold buttons',
                 'Set bolded text in buttons to normal.'],
            
            'preview_all':
                [1250, 'bool', False, None,
                 'preprocess images at all times (very slow)',
                 'Not recommended. Preprocess images with selected settings at all times.'],
            
            #'multicore_frame':
            #    [1230, 'sub_labelframe', None,
            #     None,
            #     'multicore settings',
            #     None],

            #'manual_select_cores':
            #    [1235, 'sub_bool', 'True', None,
            #     'manually select cores',
            #     'Manually select cores. ' +
            #     'If not selected, all available cores will be used.'],

            #'cores':
            #    [1240, 'sub_int', 1,
            #     (1, 2, 3, 4, 5, 6, 7, 8),
            #     'number of cores',
            #     'Select amount of cores to be used for PIV evaluations.'],

            'pandas_sub_frame':
                [1400, 'sub_labelframe', None,
                 None,
                 'Pandas',
                 None],

            'load_settings':
                [1410, 'sub_bool', True, None,
                 'settings for using pandas',
                 'Individual settings ' +
                 'for loading files using pandas.'],

            'skiprows':
                [1411, 'sub', '0', None,
                 'skip rows',
                 'Number of rows skipped at the beginning of the file.'],

            'decimal':
                [1412, 'sub', '.', None,
                 'decimal separator',
                 'Decimal separator for floating point numbers.'],

            'sep':
                [1413, 'sub', 'tab', (',', ';', 'space', 'tab'),
                 'column separator',
                 'Column separator.'],

            'header':
                [1414, 'sub_bool', False, None,
                 'read header',
                 'Read header. ' +
                 'If chosen, first line will be interpreted as the header.' +
                 'Otherwise first line will be replaced with header names' +
                 'specified in the text field below.'],

            'header_names':
                [1415, 'sub', 'x,y,vx,vy,val,sig2noise', None,
                 'specify header names',
                 'Specify comma separated list of column names.' +
                 'Example: x,y,vx,vy,sig2noise'],

            'save_sub_frame':
                [1500, 'sub_labelframe', None,
                 None,
                 'PIV save settings',
                 None],

            'image_plotting_sub_frame':
                [1600, 'sub_labelframe', None,
                 None,
                 'image plotting',
                 None],

            'matplot_intensity':
                [1610, 'sub_int', 255, None,
                 'reference intensity',
                 'Define a reference intensity for the plotting of images.'],
            
            # preprocessing
            'preproc1':
                [2000, None, None, None,
                 'Exclusions',
                 None],

            'exclusions_frame':
                [2005, 'labelframe', None,
                 None,
                 'Exclusions',
                 None],
            
            'roi-xmin':
                [2010, 'dummy2', '', None,
                 'x min',
                 "Define left side of region of interest."],
            
            'roi-xmax':
                [2011, 'dummy2', '', None,
                 'x max',
                 "Define right side of region of interest."],
            
            'roi-ymin':
                [2012, 'dummy2', '', None,
                 'y min',
                 "Define top of region of interest."],
            
            'roi-ymax':
                [2013, 'dummy2', '', None,
                 'y max',
                 "Define bottom of region of interest."],
            
            'masking_frame':
                [2020, 'dummy', None, None,
                 None,
                 None],
            
            'background_frame':
                [2025, 'dummy', None, None,
                 None,
                 None],

            'background_subtract':
                [2026, 'dummy', None, None,
                 None,
                 None],
            
            'background_type':
                [2030, 'sub', 'None', ('None', 
                                       'external (subtracted)',
                                       'external (multiplied)',
                                       'external (divided)',
                                       'global mean', 'minA - minB'),
                 'method',
                 'The algorithm used to generate the background which is subtracted ' +
                 'from the piv images. ' +
                 'Warning: »minA - minB« is still in development, so it may not perform '+
                 'to standard.'],

            'starting_frame':
                [2031, 'sub_int', 0, None,
                 'starting frame',
                 'Defining the starting frame of the background subtraction.'],

            'ending_frame':
                [2032, 'sub_int', 3, None,
                 'ending frame',
                 'Defining the ending frame of the background subtraction.'],
            
            'background_apply':
                [2035, 'dummy', None, None,
                 None,
                 None],
            
            'preproc2':
                [2100, None, None, None,
                 'Filters',
                 None],

            'filters_frame':
                [2105, 'labelframe', None,
                 None,
                 'Filters',
                 None],
            
            'preprocess-info':
                [2110, 'label', None, None,
                 'All images are normalized to [0,1] float, \npreprocessed, ' +
                 'and resized to [0, 255].',
                 None],

            'Invert_spacer':
                [2115, 'h-spacer', None,
                 None,
                 None,
                 None],

            'invert':
                [2120, 'bool', False, None,
                 'invert image',
                 'Invert image (see skimage invert()).'],

            'median_spacer':
                [2125, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'median_filter':
                [2130, 'bool', False, 'bind',
                 'median filter',
                 'Median filter'],
            
            'median_filter_size':
                [2135, 'int', 5, (3,4,5,6,7,9),
                 'filter size',
                 'Define the size of the median filter.'],
            
            'CLAHE_spacer':
                [2155, 'h-spacer', None,
                 None,
                 None,
                 None],

            'CLAHE':
                [2160, 'bool', True, 'bind',
                 'CLAHE filter',
                 'Contrast Limited Adaptive Histogram Equalization filter ' +
                 '(see skimage adapthist()).'],

            'CLAHE_auto_kernel':
                [2162, 'bool', True, None,
                 'automatic kernel sizing',
                 'Have the kernel automatically sized to 1/8 width and height of the image.'],

            'CLAHE_kernel':
                [2163, 'int', 20, None,
                 'kernel size',
                 'Defining the size of the kernel for CLAHE.'],
            
            'CLAHE_contrast':
                [2163, 'int', 1, None,
                 'contrast [1-100]',
                 'Values 1-100 with higher number producing higher contrast.'],

            'high_pass_filter_spacer':
                [2165, 'h-spacer', None, 
                 None,
                 None,
                 None],
            
            'high_pass_filter':
                [2170, 'bool', False, 'bind',
                 'Gaussian high pass filter',
                 'A simple subtracted Gaussian high pass filter.'],
            
            'hp_sigma':
                [2171, 'int', 7, None,
                 'sigma',
                 'Defining the sigma size of the subtracted gaussian filter in the ' + 
                 'high pass filter (positive ints only).'],

            'intensity_threshold_spacer':
                [2175, 'h-spacer', None,
                 None,
                 None,
                 None],

            'intensity_cap_filter':
                [2180, 'bool', False, 'bind',
                 'intensity capping',
                 'Simple global intesity cap filter. ' +
                 'Masked pixels are set to the mean pixel intensity.'],

            'ic_mult':
                [2181, 'float', 2, None,
                 'std multiplication',
                 'Multiply the standard deviation of the pixel intensities ' +
                 'to get a higher cap value.'],

            'intensity_clip_spacer':
                [2185, 'h-spacer', None,
                 None,
                 None,
                 None],

            'intensity_clip':
                [2190, 'bool', False, 'bind',
                 'intensity clip',
                 'Any intensity less than the threshold is set to zero.'],

            'intensity_clip_min':
                [2191, 'int', 20, None,
                 'min intensity',
                 'Any intensity less than the threshold is set to zero with respect to ' +
                 'the resized image inntensities.'],
            
            'wiener_spacer':
                [2195, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'wiener_filter':
                [2200, 'bool', False, 'bind',
                 'wiener filter',
                 'Wiener denoise filter'],
            
            'wiener_filter_size':
                [2210, 'int', 7, (5,7,9,11,15),
                 'filter kernel',
                 'Define the kernel size of the wiener denoise filter.'],
            
            'Gaussian_lp_spacer':
                [2215, 'h-spacer', None,
                 None,
                 None,
                 None],

            'gaussian_filter':
                [2220, 'bool', 'False', 'bind',
                 'Gaussian low pass filter',
                 'Standard Gaussian blurring filter (see scipy gaussian_filter()).'],

            'gf_sigma':
                [2231, 'int', 1, None,
                 'sigma',
                 'Defining the sigma size for gaussian blur filter.'],
            
            'apply_buttons_spacer':
                [2235, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'apply_preproc_buttons':
                [2240, 'dummy', None, None,
                 None,
                 None],

            # processing
            'piv':
                [3000, None, None, None,
                 'PIV',
                 None],
            
            'piv_frame':
                [3005, 'labelframe', None,
                 None,
                 'PIV settings/analyze',
                 None],

            'first_pass_sub_frame':
                [3010, 'sub_labelframe', None,
                 None,
                 'Pass 1',
                 None],
            
            'windowing_hint_label':
                [3015, 'dummy', None, None,
                None,
                None],
            
            'corr_window_1':
                [3020, 'dummy', 128, (256, 128, 64, 48, 32, 24, 16),
                 'interrogation window',
                 'Interrogation window for the first pass.'],

            'overlap_1':
                [3030, 'dummy', 64, (128, 64,  32, 24, 16, 12, 8),
                 'overlap',
                 'Size of the overlap of the first pass in pixels. The overlap will then be ' +
                 'calculated for the following passes.'],

            'other_pass_sub_frame':
                [3035, 'sub_labelframe', None,
                 None,
                 'Pass 2...5',
                 None],

            'pass_2':
                [3037, 'sub_bool2', True, None,
                 'pass 2',
                 'Enable a second pass in the FFT window deformation evaluation.'],

            'corr_window_2':
                [3040, 'sub_int2', 64, (128, 64, 48, 32, 24, 16),
                 'interrogation window',
                 'Interrogation window for the second pass.'],

            'pass_3_spacer':
                [3045, 'sub_h-spacer', None,
                 None,
                 None,
                 None],

            'pass_3':
                [3047, 'sub_bool2', True, None,
                 'pass 3',
                 'Enable a third pass in the FFT window deformation evaluation.'],

            'corr_window_3':
                [3050, 'sub_int2', 32, (128, 64, 48, 32, 24, 16),
                 'interrogation window',
                 'Interrogation window for the third pass.'],

            'pass_4_spacer':
                [3055, 'sub_h-spacer', None,
                 None,
                 None,
                 None],

            'pass_4':
                [3057, 'sub_bool2', False, None,
                 'pass 4',
                 'Enable a fourth pass in the FFT window deformation evaluation.'],

            'corr_window_4':
                [3060, 'sub_int2', 24, (128, 64, 48, 32, 24, 16),
                 'interrogation window',
                 'Interrogation window for the fourth pass.'],

            'pass_5_spacer':
                [3065, 'sub_h-spacer', None,
                 None,
                 None,
                 None],

            'pass_5':
                [3067, 'sub_bool2', False, None,
                 'pass 5',
                 'Enable a fifth pass in the FFT window deformation evaluation.'],

            'corr_window_5':
                [3370, 'sub_int2', 16, (128, 64, 48, 32, 24, 16),
                 'interrogation window',
                 'Interrogation window for the fifth pass.'],
            
            'deform_windows':
                [3065, 'bool', True, None,
                 'deform windows',
                 'Enable windows deformation during multi-pass evaluations.'],
            
            'corr_method':
                [3070, 'str', 'circular',
                 ('circular', 'linear'),
                 'correlation method',
                 'Correlation method. Circular is no padding and' +
                 'linear is zero padding.'],

            'subpixel_method':
                [3080, 'str', 'gaussian',
                 ('centroid', 'gaussian', 'parabolic'),
                 'subpixel method',
                 'Three point fit function for determining the subpixel position ' +
                 'of the correlation peak.'],
            
            'start_analysis':
                [3090, 'dummy', None, None,
                 None,
                 None],
            
            'analyze_frame_index':
                [3095, 'dummy', None, None, # None = all frames
                 None,
                 None],
            
            'algorithms':
                [3100, None, None, None,
                 'alg',
                 None],
            
            'alg_frame':
                [3105, 'labelframe', None,
                 None,
                 'Algorithms',
                 None],

            #'evaluation_method':
            #    [3010, 'string', 'FFT WinDef',
            #     ('Direct Correlation', 'FFT WinDef'),
            #     'evaluation method',
            #     'Direct Correlation: ' +
            #     'Direct correlation with extended size of the ' +
            #     'search area. \n' +
            #     'FFT WinDef: ' +
            #     'Fast Fourier Transforms with window deformation ' +
            #     '(recommended).'],
            
            'deformation_method':
                [3147, 'str', 'symmetric', ('symmetric', 'second image'),
                 'deformation method',
                 'Window deformation method. '+
                 '»symmetric« deforms both first and second images. '+
                 '\n»second image« deforms the second image only.'],
            
            'interpolation_order':
                [3148, 'int', 3, (0, 1, 2, 3, 4, 5),
                 'interpolation order',
                 'Interpolation oder of the spline window deformation. \n' +
                 '»0« yields zero order nearest interpolation \n' +
                 '»1« yields first order linear interpolation \n'
                 '»2« yields second order quadratic interpolation \n'
                 'and so on...'],
            
            'normalize_correlation':
                [3150, 'bool', False, None,
                 'normalize correlation',
                 'Normalize correlation.'],

            'flip_spacer':
                [3175, 'h-spacer', None,
                 None,
                 None,
                 None],

            'flip_u':
                [3180, 'bool', 'False', None,
                 'flip u-component',
                 'flip u-component array when saving RAW results.'],

            'flip_v':
                [3185, 'bool', 'False', None,
                 'flip v-component',
                 'flip v-component array when saving RAW results.'],

            'invert_spacer':
                [3190, 'h-spacer', None,
                 None,
                 None,
                 None],

            'invert_u':
                [3195, 'bool', 'False', None,
                 'invert u-component',
                 'Invert (negative) u-component when saving RAW results.'],

            'invert_v':
                [3196, 'bool', 'False', None,
                 'invert v-component',
                 'Invert (negative) v-component when saving RAW results.'],

            'swap_files_spacer':
                [3197, 'h-spacer', None,
                 None,
                 None,
                 None],

            'swap_files':
                [3198, 'bool', False, None,
                 'swap A/B files',
                 'Swap A/B files when analyzing.'],

            'windowing':
                [3200, None, None, None,
                 'Windowing',
                 None],

            'window_frame':
                [3205, 'labelframe', None,
                 None,
                 'Windowing',
                 None],

            #'search_area':
            #    [3110, 'int', 64, (16, 32, 64, 128, 256),
            #     'search area',
            #     'Size of square search area in pixel for ' +
            #     'Single-pass DCC method.'],

            # individual pass validations
            'validation':
                [3400, None, None, None,
                 'Validation',
                 None],

            'validation_frame':
                [3405, 'labelframe', None,
                 None,
                 'Validation',
                 None],

            'piv_sub_frame1':
                [3406, 'sub_labelframe', None,
                 None,
                 'pass 1 validation',
                 None],

            'fp_vld_global_threshold':
                [3410, 'sub_bool', False, 'bind',
                 'global threshold validation',
                 'Validate first pass based on set global ' +
                 'thresholds.'],

            'fp_MinU':
                [3411, 'sub_float', -100.0, None,
                 'min u',
                 'Minimum U allowable component.'],

            'fp_MaxU':
                [3412, 'sub_float', 100.0, None,
                 'max u',
                 'Maximum U allowable component.'],

            'fp_MinV':
                [3413, 'sub_float', -100.0, None,
                 'min v',
                 'Minimum V allowable component.'],

            'fp_MaxV':
                [3414, 'sub_float', 100.0, None,
                 'max v',
                 'Maximum V allowable component.'],
            
            'fp_median_spacer':
                [3425, 'sub_h-spacer', None,
                 None,
                 None,
                 None],
            
            'fp_local_med_threshold':
                [3430, 'sub_bool', True, 'bind',
                 'local median validation',
                 'Discard vector, if the absolute difference with ' +
                 'the local median is greater than the threshold. '],
            
            'fp_local_med':
                [3431, 'sub_float', 1.2, None,
                 'local median threshold',
                 'Local median absolute difference threshold.'],

            'fp_local_med_size':
                [3432, 'sub_int', 1, None,
                 'local median kernel',
                 'Local median filter kernel size.'],

            'piv_sub_frame2':
                [3440, 'sub_labelframe', None,
                 None,
                 'pass 2..5 validations',
                 None],
            
            'sp_vld_global_threshold':
                [3450, 'sub_bool', False, 'bind',
                 'global threshold validation',
                 'Validate first pass based on set global ' +
                 'thresholds.'],
            
            'sp_MinU':
                [3451, 'sub_float', -100.0, None,
                 'min u',
                 'Minimum U allowable component.'],

            'sp_MaxU':
                [3452, 'sub_float', 100.0, None,
                 'max u',
                 'Maximum U allowable component.'],

            'sp_MinV':
                [3453, 'sub_float', -100.0, None,
                 'min v',
                 'Minimum V allowable component.'],

            'sp_MaxV':
                [3454, 'sub_float', 100.0, None,
                 'max v',
                 'Maximum V allowable component.'],
            
            'sp_vld_global_set_first': 
                [3455, 'dummy', None, None,
                 'set to first pass',
                 'Set the settings of the global validation settings of passes ' + 
                 '2..5 validations to the same as the first pass.'],
            
            'sp_std_spacer':
                [3456, 'sub_h-spacer', None,
                 None,
                 None,
                 None],

            'sp_vld_std_threshold':
                [3460, 'sub_bool', False, 'bind',
                 'standard deviation validation',
                 'Remove vectors, if the the sum of the squared ' +
                 'vector components is larger than the threshold ' +
                 'times the standard deviation of the flow field.'],
            
            'sp_std_threshold':
                [3461, 'sub_float', 8.0, None,
                 'std threshold',
                 'Standard deviation threshold.'],

            'sp_median_spacer':
                [3465, 'sub_h-spacer', None,
                 None,
                 None,
                 None],
            
            'sp_local_med_validation':
                [3470, 'sub_bool', True, 'bind',
                 'local median validation',
                 'Discard vector, if the absolute difference with ' +
                 'the local median is greater than the threshold.'],
            
            'sp_local_med':
                [3471, 'sub_float', 1.2, None,
                 'local median threshold',
                 'Local median absolute difference threshold.'],

            'sp_local_med_size':
                [3472, 'sub_int', 1, None,
                 'local median kernel',
                 'Local median filter kernel size.'],
            
            'individual_pass_postprocessing':
                [3480, None, None, None,
                 'PostProcessing',
                 None],
            
            'piv_pass_postprocessing_frame':
                [3483, 'labelframe', None,
                 None,
                 'Postprocessing',
                 None],
            
            'piv_sub_frame3':
                [3485, 'sub_labelframe', None,
                 None,
                 'interpolation',
                 None],
            
            'pass_repl':
                [3490, 'sub_bool', True, 'bind',
                 'replace vectors',
                 'Replace vectors between each pass.'],
            
            'pass_repl_method':
                [3491, 'sub', 'localmean',
                 ('localmean', 'disk', 'distance'),
                 'replacement method',
                 'Each NaN element is replaced by a weighed average' +
                 'of neighbours. Localmean uses a square kernel, ' +
                 'disk a uniform circular kernel, and distance a ' +
                 'kernel with a weight that is proportional to the ' +
                 'distance.'],

            'pass_repl_iter':
                [3492, 'sub_int', 10, None,
                 'number of iterations',
                 'If there are adjacent NaN elements, iterative ' +
                 'replacement is needed.'],

            'pass_repl_kernel':
                [3493, 'sub_int', 2, None,
                 'kernel size',
                 'Diameter of the NaN interpolation kernel.'],

            'piv_sub_frame4':
                [3495, 'sub_labelframe', None,
                 None,
                 'Smoothing',
                 None],

            'smoothn_each_pass':
                [3500, 'sub_bool', True, 'bind',
                 'smoothen each pass',
                 'Smoothen each pass using openpiv.smoothn.'],

            'smoothn_first_more':
                [3501, 'sub_bool', False, None,
                 'double first pass strength',
                 'Double the smoothing strength on the first pass.'],

            'robust1':
                [3502, 'sub_bool', False, None,
                 'smoothen robust',
                 'Activate robust in smoothen (minimizes influence of outlying data).'],

            'smoothn_val1':
                [3503, 'sub_float', 1.0, None,
                 'smoothing strength',
                 'Strength of smoothen script. Higher scalar number produces ' +
                 'more smoothed data.'],
            
            # calibration
            'calib':
                [5000, None, None, None,
                 'Calibtration',
                 None],
            
            'calib_frame':
                [5005, 'labelframe', None, None,
                 'Calibrate',
                 None],
            
            'load/select_calib_button':
                [5010, 'dummy', None, None,
                 'Load calibtration image',
                 'Load a calibration image to aid in scailing/calibrating the ' +
                 'vector field.'],
            
            'reference_dist':
                [5015, 'float', 1, None,
                 'reference distance [px]',
                 'The reference distance, in pixels, between two points ' +
                 'on a reference image.'],
            
            'real_dist':
                [5020, 'float', 1, None,
                 'real distance [mm]',
                 'The real distance, n millimeters, between the two points selected '+
                 'in the selected reference distance.'],
            
            'time_step':
                [5030, 'float', 1000, None,
                 'time step [ms]',
                 'The time step, in milliseconds, between two images.'],
            
            'apply/clear_calib_button':
                [5040, 'dummy', None,
                 None,
                 None,
                 None], # hints are processed in the main GUI for now
            
            # validation/postprocessing
            'vld':
                [6000, None, None, None,
                 'PostProcessing1',
                 None],

            'vld_frame':
                [6005, 'labelframe', None,
                 None,
                 'Validate compoments',
                 None],

            'vld_global_thr':
                [6010, 'bool', False, 'bind',
                 'global threshold validation',
                 'Validate the data based on set global ' +
                 'thresholds.'],

            'set_glob_limits':
                [6011, 'dummy', None, None,
                 'Set velocity limits',
                 'Set the velocity limits from a scatter plot interactively.'],
            
            'MinU':
                [6012, 'float', -30.0, None,
                 'min u',
                 'Minimum U allowable component.'],

            'MaxU':
                [6013, 'float', 30.0, None,
                 'max u',
                 'Maximum U allowable component.'],

            'MinV':
                [6014, 'float', -30.0, None,
                 'min v',
                 'Minimum V allowable component.'],

            'MaxV':
                [6015, 'float', 30.0, None,
                 'max v',
                 'Maximum V allowable component.'],
            
            'apply_glob_val_first_pass':
                [6016, 'dummy', None, None,
                 'Apply to first pass',
                 'Apply the global validation settings to the first pass.'],
            
            'horizontal_spacer12':
                [6025, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'vld_global_std':
                [6030, 'bool', False, 'bind',
                 'standard deviation validation',
                 'Validate the data based on a multiple of the ' +
                 'standard deviation.'],

            'global_std_threshold':
                [6031, 'float', 5.0, None,
                 'std threshold',
                 'Remove vectors, if the the sum of the squared ' +
                 'vector components is larger than the threshold ' +
                 'times the standard deviation of the flow field.'],
            
            'horizontal_spacer13':
                [6035, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'vld_local_med':
                [6040, 'bool', True, 'bind',
                 'local median validation',
                 'Validate the data based on a local median ' +
                 'threshold.'],

            'local_median_threshold':
                [6041, 'float', 1.2, None,
                 'local median threshold',
                 'Discard vector, if the absolute difference with ' +
                 'the local median is greater than the threshold. '],
            
            'local_median_size':
                [6042, 'int', 1, None,
                 'local median kernel',
                 'Local median filter kernel size.'],
            
            'horizontal_spacer14':
                [6095, 'h-spacer', None,
                 None,
                 None,
                 None],

            'repl':
                [6100, 'bool', True, 'bind',
                 'replace outliers',
                 'Replace outliers.'],

            'repl_method':
                [6101, 'str', 'localmean',
                 ('localmean', 'disk', 'distance'),
                 'replacement method',
                 'Each NaN element is replaced by a weighed average' +
                 'of neighbours. Localmean uses a square kernel, ' +
                 'disk a uniform circular kernel, and distance a ' +
                 'kernel with a weight that is proportional to the ' +
                 'distance.'],

            'repl_iter':
                [6102, 'int', 10, None,
                 'number of iterations',
                 'If there are adjacent NaN elements, iterative ' +
                 'replacement is needed.'],

            'repl_kernel':
                [6103, 'int', 2, None,
                 'kernel size',
                 'Diameter of the weighting kernel.'],

            'apply_validation_current':
                [6110, 'dummy2', None, None,
                 'Apply to current frame',
                 'Apply all enabled algorithms to current frame'],
            
            'apply_validation_all':
                [6120, 'dummy2', None, None,
                 'Apply to all frames',
                 'Apply all enabled algorithms to all frames'],
            
            'mdfy':
                [7000, None, None, None,
                 'PostProcessing2',
                 None],
            
            'mdfy_frame':
                [7005, 'labelframe', None,
                 None,
                 'Modify compoments',
                 None],
            
            'offset_grid':
                [7010, 'bool', False, 'bind',
                 'offset grid',
                 'Offset the grid by + or - units.'],
            
            'offset_x':
                [7011, 'float', 0.0, None,
                 'offset x',
                 'Offset the grid by + or - units on the x-axis'],
            
            'offset_y':
                [7012, 'float', 0.0, None,
                 'offset y',
                 'Offset the grid by + or - units on the y-axis'],
            
            'mdfy_vec_spacer':
                [7015, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'modify_velocity':
                [7020, 'bool', False, 'bind',
                 'modify velocity components',
                 'Add or subtract velocities for each velocity component'],
            
            'modify_u':
                [7021, 'float', 0.0, None,
                 'u component',
                 'Add (+) or subtract (-) entered value from the u component ' +
                 'of the vector field.'],
            
            'modify_v':
                [7022, 'float', 0.0, None,
                 'v component',
                 'Add (+) or subtract (-) entered value from the v component ' +
                 'of the vector field.'],
            
            'smoothn_spacer':
                [7075, 'h-spacer', None,
                 None,
                 None,
                 None],
            
            'smoothn':
                [7080, 'bool', False, 'bind',
                 'smooth data',
                 'Smooth data using openpiv.smoothn.'],

            'robust':
                [7081, 'bool', False, None,
                 'robust smoothing',
                 'Activate robust in smoothn (minimizes influence of outlying data).'],

            'smoothn_val':
                [7082, 'float', 1.0, None,
                 'smoothing strength',
                 'Strength of the smooth script. Higher scalar number produces ' +
                 'more smoothned data.'],

            'average_spacer':
                [7085, 'h-spacer', None,
                 None,
                 None,
                 None],

            'average_results':
                [7090, 'bool', False, None,
                 'average results (not implemented yet)',
                 'Average all results in selected directory. ' +
                 'Results in a single file with averaged results.'],
            
            'apply_modify_components_current':
                [7100, 'dummy2', None, None,
                 'Apply to current frame',
                 'Apply all enabled algorithms to current frame'],
            
            'apply_modify_components_all':
                [7110, 'dummy2', None, None,
                 'Apply to all frames',
                 'Apply all enabled algorithms to all frames'],
            
            # plotting
            'plt':
                [8000, None, None, None,
                 'Plot',
                 None],
            
            'plt_frame':
                [8005, 'labelframe', None, 
                 None,
                 'Plotting',
                 None],
            
            'plot_type':
                [8010, 'str', 'vectors', ('vectors', 'contours', 
                                          'streamlines','histogram','profiles','scatter', 
                                          'line',
                                          #'bar', Failed testing (for Windows 10), simply locks GUI.
                                          'density'),
                 'plot type',
                 'Select how to plot velocity data.'],
            
            'plot_title':
                [8020, 'str', 'Title', None, 
                 'diagram title', 
                 'diagram title.'],
            
            #plot_derivatives':
            #   [8075, 'str', 'None', ('None', 'Vorticity'),
            #   'plot derivatives',
            #   'Plot derivatives of the vector map (for vectors, countours, and streamlines only).'],
            
            'streamline_density':
                [8095, 'str', '0.5, 1', None, 
                 'streamline density',
                 'streamline density. Can be one value (e.g. 1) or a couple' +
                 ' of values for a range (e.g. 0.5, 1).'],
            
            'integrate_dir':
                [8097, 'str', 'both', ('both', 'forward','backward'),
                 'streamline direction',
                 'Integrate the streamline in forward, backward or both ' +
                 'directions. default is both.'],
            
            'Statistics_frame':
                [8105, 'sub_labelframe', None, 
                 None,
                 'Statistics',
                 None],
            
            'u_data':
                [8110, 'sub', 'vx', None, 
                 'column name for u-component',
                 'column name for the u-velocity component.' +
                 ' If unknown watch labbook entry.'],
            
            'v_data':
                [8120, 'sub', 'vy', None, 
                 'column name for v-component',
                 'column name for v-velocity component.' +
                 ' If unknown watch labbook entry.' +
                 ' For histogram only the v-velocity component is needed.'],
            
            'plot_scaling': 
                [8130, 'sub', 'None', ('None','logx','logy','loglog'),
                 'axis scaling', 'scales the axes. logarithm scaling x-axis' +
                 ' --> logx; logarithm scaling y-axis --> logy; ' +
                 'logarithm scaling both axes --> loglog.'],
            
            'histogram_type':
                [8140, 'sub', 'bar', ('bar','barstacked','step','stepfilled'), 
                 'histogram type', 
                 'Choose histogram type. Only available for histogram' + 
                 'plot.'],
            
            'histogram_quantity':
                [8150, 'sub', 'v_x', ('v','v_x','v_y'),
                 'histogram quantity',
                 'The absolute value of the velocity (v) or its x- ' +
                 'or y-component (v_x or v_y).'], 
            
            'histogram_bins':
                [8160, 'sub', 20, None,
                 'histogram number of bins',
                 'Number of bins (bars) in the histogram.'],
            
            'profiles_orientation':
                [8170, 'sub', 'vertical', ('vertical','horizontal'),
                 'profiles orientation',
                 'Plot v_y over x (horizontal) or v_x over y (vertical).'],
            
            'profiles_jump':
                [8180, 'sub_int', 5, None, 
                 'profile density', 
                 'The amount of profile lines (minimum of 1).'],
            
            'plot_xlim':
                [8190, 'sub', '', None, 
                 'limits for the x-axis', 
                 'For implementation use (lower_limit, upper_limit).'],
            
            'plot_ylim':
                [8200, 'sub', '', None, 
                 'limits for the y-axis',
                 'For implementation use (lower_limit, upper_limit).'],
            
            'modify_plot_appearance':
                [8500, None, None, None,
                 'Plot',
                 None],
            
            'modify_plot_frame':
                [8503, 'labelframe', None, 
                 None,
                 'Modify Plot Appearance',
                 None],
            
            'vector_subframe':
                [8505, 'sub_labelframe', None, 
                 None,
                 'Vectors',
                 None],
            
            'vec_scale':
                [8510, 'sub_int', 100, None,
                 'vector scaling',
                 'Velocity as a fraction of the plot width, e.g.: ' +
                 'm/s per plot width. Large values result in shorter ' +
                 'vectors.'],
            
            'vec_width':
                [8520, 'sub_float', 0.0015, None,
                 'vector line width',
                 'Line width as a fraction of the plot width.'],
            
            #'autoscale_vec': # algorithm failed testong, was removed
            #    [8525, 'sub_bool', True, None,
            #     'autoscale vectors',
            #     'Autoscale vector width and scaling.'],
            
            'show_masked_vectors': # algorithm didn't work, temporarly disabled
                [8530, 'sub_bool', False, None,
                'show masked vectors',
                'If enabled, masked vectors are shown in the selected visuals.'],
            
            'invalid_color':
                [8535, 'dummy', 'red', None,
                 None,
                 'Choose the color of the vectors'],
            
            'valid_color':
                [8540, 'dummy', 'black', None,
                 None,
                 'Choose the color of the vectors'],
            
            'mask_vec_style':
                [8550, 'sub', 'x', ('x', '+', 'o', '.', '*', 's', 'D', 'H'),
                 'masked vector style',
                 'Define the style/visuals of masked vectors.'],
            
            'exclusion_plotting_sub_frame':
                [8600, 'sub_labelframe', None,
                 None,
                 'Exclusions',
                 None],
            
            'roi_border_width':
                [8610, 'sub_int', 1, (1, 2, 3, 4),
                 'ROI border width',
                 'Define the border width of the ROI exclusion zone.'],
            
            'roi_line_style':
                [8620, 'sub', '--', ('-', '--', '-.', ':'),
                 'ROI border line style',
                 'Define the border line style of the ROI exclusion zone.'],
            
            'roi_border':
                [8630, 'dummy2', 'yellow', None,
                 'ROI border color',
                 'Define the border color of the ROI exclusion zone.'],
            
            'mask_fill':
                [8640, 'dummy2', '#960000', None,
                 'mask fill color',
                 'Define the fill color of the object mask polygons.'],
            
            'mask_vec':
                [8650, 'dummy2', 'red', None,
                 'masked vector color',
                 'Define the color of masked vector visuals.'],
            
            'mask_alpha':
                [8660, 'sub_float', 0.5, None,
                 'mask transparency [0-1]',
                 'Define how transparent mask objects are where »0« is ' + 
                 'completley clear and »1« is completely opaque.'],
            
            'derived_subframe':
                [8700, 'sub_labelframe', None, 
                 None,
                 'Contours/color map',
                 None],
            
            'color_map':
                [8710, 'sub', 'viridis', ('viridis','jet','short rainbow',
                                          'long rainbow','seismic','autumn','binary'),
                 'Color map', 'Color map for streamline- and contour-plot.'],
            
            'velocity_color':
                [8730, 'sub', 'v', ('v', 'vx', 'vy'),
                 'set colorbar component to: ',
                 'Set colorbar to velocity components.'],
            
            'color_levels':
                [8740, 'sub', '30', None, 
                 'number of color levels',
                 'Select the number of color levels for contour plot.'],
            
            'vmin':
                [8750, 'sub', '', None, 
                 'min velocity for colormap',
                 'minimum velocity for colormap (contour plot).'],
            
            'vmax':
                [8760, 'sub', '', None, 
                 'max velocity for colormap',
                 'maximum velocity for colormap (contour plot).'],
            
            'statistics_subframe':
                [8800, 'sub_labelframe', None, 
                 None,
                 'Statistics',
                 None],
            
            'plot_grid':
                [8810, 'sub_bool', True, None, 
                 'grid', 
                 'adds a grid to the diagram.'],
            
            'plot_legend':
                [8820, 'sub_bool', True, None,
                 'legend', 
                 'adds a legend to the diagram.'],
            
            # lab-book
            'lab_book':
                [9000, None, None, None,
                 'Lab-Book',
                 None],

            'lab_book_content':
                [9010, 'text',
                 '',
                 None,
                 None,
                 None],
            
            'data_information':
                [9020, 'bool', False, None, 'log column information',
                 'shows column names, if you choose a file at the ' +
                 'right side.'],

            # user-function
            'user_func':
                [10000, None, None, None,
                 'User-Function',
                 None],

            'user_func_def':
                [10010, 'text',
                 example_user_function,
                 None,
                 None,
                 None],
        
        # exporting asci 2
            'export_1':
                [11000, None, None, None,
                 'Export_1',
                 None],
            
            'export_1_frame':
                [11005, 'labelframe', None, 
                 None,
                 'Export ASCI-II',
                 None],
                
            'asci2_delimiter':
                [11005, 'str', 'tab', ('tab', 'space', ',', ';'),
                 'delimiter',
                 'Delimiter to differentiate the columns of the vector components.'],
            
            'export_current_button':
                [11010, 'dummy', None, None,
                 'Export current frame',
                 'Export the currently selected frame in ASCI-II format.'],
            
            'export_all_button':
                [11020, 'dummy', None, None,
                 'Export all frame(s)',
                 'Export all frame(s) in ASCI-II format. Results in one file per frame.'],
        }

        # splitting the dictionary for more convenient access
        self.index = dict(zip(
            self.default.keys(),
            [val[0] for val in self.default.values()]))
        self.type = dict(zip(
            self.default.keys(),
            [val[1] for val in self.default.values()]))
        self.param = dict(zip(
            self.default.keys(),
            [val[2] for val in self.default.values()]))
        self.hint = dict(zip(
            self.default.keys(),
            [val[3] for val in self.default.values()]))
        self.label = dict(zip(
            self.default.keys(),
            [val[4] for val in self.default.values()]))
        self.help = dict(zip(
            self.default.keys(),
            [val[5] for val in self.default.values()]))

    def __getitem__(self, key):
        return(self.param[key])

    def __setitem__(self, key, value):
        self.param[key] = value

    def load_settings(self, fname):
        '''Read parameters from a JSON file.

        Args: 
            fname (str): Path of the settings file in JSON format.

        Reads only parameter values. Content of the fields index, 
        type, hint, label and help are always read from the default
        dictionary. The default dictionary may contain more entries
        than the JSON file (ensuring backwards compatibility).
        '''
        try:
            f = open(fname, 'r')
            p = json.load(f)
            f.close()
        except:
            print('File not found: ' + fname)
        else:
            for key in self.param:
                if key in p:
                    self.param[key] = p[key]
                    
    def load_session(self, fname):
        try:
            session = (load(fname, allow_pickle = True))
            return(session)
        except Exception as e:
            print('file not found: '+ fname)
            print('reason: ' +str(e))        

    def dump_settings(self, fname):
        '''Dump parameter values to a JSON file.

        Args:
            fname (str): A filename.

        Only the parameter values are saved. Other data like
        index, hint, label and help should only be defined in the
        default dictionary in this source code.'''
        try:
            f = open(fname, 'w')
            json.dump(self.param, f)
            f.close()
        except:
            print('Unable to save settings: ' + fname)
    
    def dump_session(self, fname, session_dict):
        '''Dump session to a npz file.

        Args:
            fname (str): A filename.

        All parameters and values in the session dictionary
        are saved here. Files are uncompressed, so large sessions (>5GB)
        may take up some space.'''
        try:
            #path = os.path.join(fname, 'openpivgui_session.npy')
            save(fname, session_dict)
        except Exception as e:
            print('Unable to save session: ' + fname +'\n'+path)
            print('Reason: ' + str(e))

    def generate_parameter_documentation(self, group=None):
        '''Return parameter labels and help as reStructuredText def list.

        Parameters
        ----------
        group : int
            Parameter group.
            (e.g. OpenPivParams.PIVPROC)

        Returns
        -------
        str : A reStructuredText definition list for documentation.
        '''
        s = ''
        for key in self.default:
            if (group < self.index[key] < group+1000
                and self.type[key] not in [
                    'labelframe', 
                    'sub_labelframe', 
                    'h-spacer', 
                    'sub_h-spacer',
                    'dummy'
                    ]):
                s = s + str(self.label[key]) + '\n' + \
                '    ' + str.replace(str(self.help[key]), '\n', '\n    ') + '\n\n'
        return(s)
