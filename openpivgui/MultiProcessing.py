#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Parallel Processing of PIV images.'''

from openpivgui.PreProcessing import gen_background, process_images
from openpivgui.open_piv_gui_tools import _round, coords_to_xymask

import multiprocessing
import numpy as np
import time
import openpiv.smoothn as piv_smt
import openpiv.scaling as piv_scl
import openpiv.filters as piv_flt
import openpiv.validation as piv_vld
import openpiv.windef as piv_wdf
import openpiv.pyprocess as piv_prc
import openpiv.preprocess as piv_pre
import openpiv.tools as piv_tls
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


class MultiProcessing(piv_tls.Multiprocesser):
    '''Parallel processing, based on the corrresponding OpenPIV class.

    Do not run from the interactive shell or within IDLE! Details at:
    https://docs.python.org/3.6/library/multiprocessing.html#using-a-pool-of-workers

    Parameters
    ----------
    params : OpenPivParams
        A parameter object.
    '''

    def __init__(self, params, session):
        '''Standard initialization method.

        For separating GUI and PIV code, the output filenames are
        generated here and not in OpenPivGui. In this way, this object
        might also be useful independently from OpenPivGui.
        '''
        self.parameter = params
        self.session = session
        
        # generate background if needed
        if self.parameter['background_subtract'] == True and self.parameter['background_type'] != 'minA - minB':
            self.background = gen_background(self.parameter)
        else:
            self.background = None
            
        self.files_a = self.session['files_a']
        self.files_b = self.session['files_b']

        if self.parameter['swap_files']:
            self.files_a, self.files_b = self.files_b, self.files_a
                                                               
        self.n_files = len(self.files_a)
        self.results = []
    
    
    
    def get_num_frames(self):
        '''Return the amount of image pairs that will be processed.
        
        Returns:
            int: The number of image pairs to be processed'''
        return(len(self.files_a))
    
    
    
    def _run(self, func, n_cpus=1):
        # create a list of tasks to be executed.
        image_pairs = [
            (file_a, file_b, i)
            for file_a, file_b, i in zip(
                self.files_a, self.files_b, range(self.n_files)
            )
        ]

        # for debugging purposes always use n_cpus = 1,
        # since it is difficult to debug multiprocessing stuff.
        if n_cpus > 1:
            pool = multiprocessing.Pool(processes=n_cpus)
            res = pool.map(func, image_pairs)
        else:
            for image_pair in image_pairs:
                func(image_pair)
                
    def process(self, args):
        '''Process chain as configured in the GUI.

        Parameters
        ----------
        args : tuple
            Tuple as expected by the inherited run method:
            file_a (str) -- image file a
            file_b (str) -- image file b
            counter (int) -- index pointing to an element of the filename list
        '''
        file_a, file_b, counter = args
        frame_a = piv_tls.imread(file_a)
        frame_b = piv_tls.imread(file_b)

        # Smoothning script borrowed from openpiv.windef
        s = self.parameter['smoothn_val1']

        def smoothn(u, s):
            s = s
            u, _, _, _ = piv_smt.smoothn(
                u, s=s, isrobust=self.parameter['robust1'])
            return(u)

        if self.parameter['analysis'] != True:
            raise Exception('Cancled analysis via exception')
                
        # preprocessing
        print('\nPre-pocessing frame: {}'.format(counter))
        #if self.parameter['background_subtract'] == True and self.parameter['background_type'] == 'minA - minB':
        #    self.background = gen_background(self.parameter, frame_a, frame_b)
        self.background = None
        roi_xmin = self.parameter['img_preproc'][f'{counter}'][0]
        roi_xmax = self.parameter['img_preproc'][f'{counter}'][1]
        roi_ymin = self.parameter['img_preproc'][f'{counter}'][2]
        roi_ymax = self.parameter['img_preproc'][f'{counter}'][3]
        frame_a = frame_a.astype(np.int32)
        frame_a = process_images(frame_a, 
                                 preproc            = True,
                                 roi_xmin           = roi_xmin,
                                 roi_xmax           = roi_xmax,
                                 roi_ymin           = roi_ymin,
                                 roi_ymax           = roi_ymax,
                                 do_background      = False,
                                 background         = self.background,
                                 invert             = self.parameter['invert'],
                                 median_filt        = self.parameter['median_filter'],
                                 median_kernel      = self.parameter['median_filter_size'],
                                 CLAHE              = self.parameter['CLAHE'],
                                 CLAHE_auto_kernel  = self.parameter['CLAHE_auto_kernel'],
                                 CLAHE_kernel       = self.parameter['CLAHE_kernel'],
                                 CLAHE_clip         = self.parameter['CLAHE_contrast'],
                                 high_pass          = self.parameter['high_pass_filter'],
                                 hp_sigma           = self.parameter['hp_sigma'],
                                 intensity_cap      = self.parameter['intensity_cap_filter'],
                                 ic_mult            = self.parameter['ic_mult'],
                                 intensity_clip     = self.parameter['intensity_clip'],
                                 intensity_clip_min = self.parameter['intensity_clip_min'],
                                 wiener_filt        = self.parameter['wiener_filter'],
                                 wiener_size        = self.parameter['wiener_filter_size'],
                                 gaussian_filt      = self.parameter['gaussian_filter'],
                                 gf_sigma           = self.parameter['gf_sigma'])  
            
        frame_b = frame_b.astype(np.int32)
        frame_b = process_images(frame_b, 
                                 preproc            = True,
                                 roi_xmin           = roi_xmin,
                                 roi_xmax           = roi_xmax,
                                 roi_ymin           = roi_ymin,
                                 roi_ymax           = roi_ymax,
                                 do_background      = False,
                                 background         = self.background,
                                 invert             = self.parameter['invert'],
                                 median_filt        = self.parameter['median_filter'],
                                 median_kernel      = self.parameter['median_filter_size'],
                                 CLAHE              = self.parameter['CLAHE'],
                                 CLAHE_auto_kernel  = self.parameter['CLAHE_auto_kernel'],
                                 CLAHE_kernel       = self.parameter['CLAHE_kernel'],
                                 CLAHE_clip         = self.parameter['CLAHE_contrast'],
                                 high_pass          = self.parameter['high_pass_filter'],
                                 hp_sigma           = self.parameter['hp_sigma'],
                                 intensity_cap      = self.parameter['intensity_cap_filter'],
                                 ic_mult            = self.parameter['ic_mult'],
                                 intensity_clip     = self.parameter['intensity_clip'],
                                 intensity_clip_min = self.parameter['intensity_clip_min'],
                                 wiener_filt        = self.parameter['wiener_filter'],
                                 wiener_size        = self.parameter['wiener_filter_size'],
                                 gaussian_filt      = self.parameter['gaussian_filter'],
                                 gf_sigma           = self.parameter['gf_sigma'])   
        passes = 1
        # setup custom windowing
        corr_window   = self.parameter['corr_window_1']
        overlap       = self.parameter['overlap_1']
        for i in range(2, 6):
            if self.parameter['pass_%1d' % i]:
                passes += 1
            else:
                break;
        overlap_percent = overlap / corr_window
        sizeX = corr_window
        
        print('Evaluating frame: {}'.format(counter))
        # evaluation first pass
        start = time.time() 
        x, y, u, v = pivware.firstpass(
            frame_a, frame_b,
            window_size = corr_window,
            overlap = overlap,
            subpixel_method = self.parameter['subpixel_method'],
            correlation_method = self.parameter['corr_method'],
            normalized_correlation = self.parameter['normalize_correlation'])
        
        # validating first pass
        mask = np.full_like(x, 0)
        if self.parameter['fp_vld_global_threshold']:
            u, v, Mask = piv_vld.global_val(
                u, v,
                u_thresholds=(self.parameter['fp_MinU'], self.parameter['fp_MaxU']),
                v_thresholds=(self.parameter['fp_MinV'], self.parameter['fp_MaxV']))
            mask += Mask # consolidate effects of mask
            
        if self.parameter['fp_local_med']:
            u, v, Mask = piv_vld.local_median_val(
                u, v,
                u_threshold = self.parameter['fp_local_med'],
                v_threshold = self.parameter['fp_local_med'],
                size        = self.parameter['fp_local_med_size'])
            mask += Mask
            
        if self.parameter['pass_repl']:
            u, v = piv_flt.replace_outliers(
                    u, v,
                    method      = self.parameter['pass_repl_method'],
                    max_iter    = self.parameter['pass_repl_iter'],
                    kernel_size = self.parameter['pass_repl_kernel'])
        print('Validated pass 1 for frame: {}'.format(counter)) 

        # smoothning  before deformation if 'each pass' is selected
        if self.parameter['smoothn_each_pass']:
            if self.parameter['smoothn_first_more']:
                s *=2
            u = smoothn(u, s); v = smoothn(v, s) 
            print('Smoothned pass 1 for frame: {}'.format(counter))
            s = self.parameter['smoothn_val1']

        print('Finished pass 1 for frame: {}'.format(counter))
        print("window size: "   + str(corr_window))
        print('overlap: '       + str(overlap), '\n')  

        # evaluation of all other passes
        if passes != 1:
            iterations = passes - 1
            for i in range(2, passes + 1):
                if self.parameter['analysis'] != True:
                    raise Exception('Cancled analysis via exception')
                # setting up the windowing of each pass
                corr_window = self.parameter['corr_window_%1d' % i]
                overlap = int(corr_window * overlap_percent)
                sizeX = corr_window
                    
                x, y, u, v = pivware.multipass(
                    frame_a.astype(np.int32), frame_b.astype(np.int32),
                    corr_window,
                    overlap,
                    passes, # number of iterations
                    i, # current iteration
                    x, y, u, v,
                    correlation_method     = self.parameter['corr_method'],
                    normalized_correlation = self.parameter['normalize_correlation'],
                    subpixel_method        = self.parameter['subpixel_method'],
                    deform_windows         = self.parameter['deform_windows'],
                    deformation_method     = self.parameter['deformation_method'],
                    interpolation_order    = self.parameter['interpolation_order'],
                    deformation_degree     = 3)
                
                # validate other passes
                mask = np.full_like(x, 0)
                if self.parameter['sp_vld_global_threshold']:
                    u, v, Mask = piv_vld.global_val(
                        u, v,
                        u_thresholds=(self.parameter['sp_MinU'], self.parameter['sp_MaxU']),
                        v_thresholds=(self.parameter['sp_MinV'], self.parameter['sp_MaxV']))
                    mask += Mask # consolidate effects of mask
                
                if self.parameter['sp_vld_global_threshold']:
                    u, v, Mask = piv_vld.global_std(
                        u, v, 
                        std_threshold=self.parameter['sp_std_threshold'])
                    mask += Mask
                    
                if self.parameter['sp_local_med_validation']:
                    u, v, Mask = piv_vld.local_median_val(
                        u, v,
                        u_threshold = self.parameter['sp_local_med'],
                        v_threshold = self.parameter['sp_local_med'],
                        size        = self.parameter['sp_local_med_size'])  
                    mask += Mask
                
                if self.parameter['pass_repl']:
                    u, v = piv_flt.replace_outliers(
                        u, v,
                        method      = self.parameter['pass_repl_method'],
                        max_iter    = self.parameter['pass_repl_iter'],
                        kernel_size = self.parameter['pass_repl_kernel'])
                print('Validated pass {} of frame: {}'.format(i,counter))             
                           
                # smoothning each individual pass if 'each pass' is selected
                if self.parameter['smoothn_each_pass']:
                    u = smoothn(u, s); v = smoothn(v, s) 
                    print('Smoothned pass {} for frame: {}'.format(i,counter))
                
                print('Finished pass {} for frame: {}'.format(i,counter))
                print("window size: "   + str(corr_window))
                print('overlap: '       + str(overlap), '\n')
                iterations -= 1
                
        typevector = mask
        
        if self.parameter['analysis'] != True:
            raise Exception('Cancled analysis via exception')
            
        if self.parameter['flip_u']:
            u = np.flipud(u)

        if self.parameter['flip_v']:
            v = np.flipud(v)

        if self.parameter['invert_u']:
            u *= -1

        if self.parameter['invert_v']:
            v *= -1
        
        # get vectors in the right direction
        v *= -1
        
        # applying mask(s)
        if len(self.parameter['img_preproc'][f'{counter}'][4]) > 0:
            object_masks = self.parameter['img_preproc'][f'{counter}'][4]
            xymask = coords_to_xymask(x, y, object_masks)
            u = np.ma.masked_array(u, xymask)
            v = np.ma.masked_array(v, xymask) 
            
        end = time.time() 
        
        # save data to dictionary.
        self.session['results'][f'{counter}'] = [
            [roi_xmin, roi_xmax, roi_ymin, roi_ymax], # store roi
            corr_window, # store final interrogation window size 
            x, y, u, v, typevector, 
            self.parameter['img_preproc'][f'{counter}'][4],# mask coords for display
            1] # scaling factor
        
        print('Processed frame: {}'.format(counter))
        
        # additional information of evaluation
        sizeY = sizeX
        sizeX = ((int(frame_a.shape[0] - sizeX) // (sizeX - (sizeX * overlap_percent))) + 1)
        sizeY = ((int(frame_a.shape[1] - sizeY) // (sizeY - (sizeY * overlap_percent))) + 1)
        time_per_vec = _round((((end - start) * 1000) / ((sizeX * sizeY) - 1)), 3)
        print('Process time: {} second(s)'.format((_round((end - start), 3))))
        print('Number of vectors: {}'.format(int((sizeX * sizeY) - 1)))
        print('Time per vector: {} millisecond(s)'.format(time_per_vec))
        
        
        
import scipy.ndimage as scn
from scipy.interpolate import RectBivariateSpline
from skimage.util import invert 

class pivware():    
    def firstpass(
        frame_a, frame_b,
        search_area_size = 128,
        window_size = 64,
        overlap = 32,
        subpixel_method = 'gaussian',
        correlation_method = 'linear',
        normalized_correlation = True):
        if correlation_method == 'linear':
            normalized_correlation = True
            
        u, v, s2n = piv_prc.extended_search_area_piv(
            frame_a, frame_b,
            search_area_size = window_size,
            window_size = window_size,
            overlap = overlap,
            subpixel_method = subpixel_method,
            correlation_method = correlation_method,
            normalized_correlation = normalized_correlation,
            sig2noise_method = 'peak2peak',
            width = 2)

        shapes = np.array(
            piv_prc.get_field_shape(
                frame_a.shape,
                    window_size,
                    overlap))
        
        u = u.reshape(shapes)
        v = v.reshape(shapes)
       # s2n = s2n.reshape(shapes)

        x, y = piv_prc.get_coordinates(frame_a.shape,
                                       window_size,
                                       overlap)
        return x, y, u, v
    
    
    
    def multipass(
        frame_a,frame_b,
        window_size,
        overlap,
        iterations,
        current_iteration,
        x_old, y_old, u_old, v_old,
        correlation_method = "circular",
        normalized_correlation = False,
        subpixel_method = "gaussian",
        deform_windows = True,
        deformation_method = "symmetric",
        deformation_degree = 3,
        interpolation_order = 3):
        """
        A slighly modified version of the original multipass_window_deform
        algorithm. For more information on the algorithm, please refer to 
        the windef file located in the OpenPIV package. For copyright information,
        please check the OpenPIV GitHub repository.
        """

        x, y = piv_wdf.get_coordinates(
            frame_a.shape,
            window_size,
            overlap)
        
        y_old = y_old[:, 0]
        x_old = x_old[0, :]
        y_int = y[:, 0]
        x_int = x[0, :]      

        # interpolating the displacements from the old grid onto the new grid
        # y befor x because of numpy works row major
        ip = RectBivariateSpline(y_old, x_old, u_old.filled(0.))
        u_pre = ip(y_int, x_int)

        ip2 = RectBivariateSpline(y_old, x_old, v_old.filled(0.))
        v_pre = ip2(y_int, x_int)

        if deform_windows:
            if deformation_method == "symmetric":
                # this one is doing the image deformation (see above)
                x_new, y_new, ut, vt = piv_wdf.create_deformation_field(
                    frame_a, x, y, u_pre, v_pre,
                    kx = interpolation_order,
                    ky = interpolation_order)
                
                frame_a = scn.map_coordinates(
                    frame_a, ((y_new - vt / 2, x_new - ut / 2)),
                    order = deformation_degree, mode = 'nearest')
                frame_b = scn.map_coordinates(
                    frame_b, ((y_new + vt / 2, x_new + ut / 2)),
                    order = deformation_degree, mode = 'nearest')
                
            elif deformation_method == "second image":
                frame_b = piv_wdf.deform_windows(
                    frame_b, x, y, u_pre, -v_pre,
                    interpolation_order = deformation_degree,
                    kx = interpolation_order,
                    ky = interpolation_order)
            else:
                raise Exception("Deformation method is not valid.")
                
        if correlation_method == 'linear': # avoids confision and horrible results
            normalized_correlation = True
            
        # so we use here default circular not normalized correlation:
        u, v, s2n = piv_prc.extended_search_area_piv(
            frame_a,
            frame_b,
            window_size = window_size,
            overlap = overlap,
            correlation_method = correlation_method,
            normalized_correlation = normalized_correlation,
            subpixel_method = subpixel_method,
            width = 2,
            sig2noise_method = 'peak2peak'
            
        )

        shapes = np.array(
            piv_prc.get_field_shape(
                frame_a.shape,
                window_size,
                overlap))
        
        u = u.reshape(shapes)
        v = v.reshape(shapes)

        # adding or averaging the recent displacment on to the displacment of the previous pass
        if deform_windows:
            u += u_pre
            v += v_pre
            
        else:
            u = (u + u_pre) / 2
            v = (v + v_pre) / 2
        
        # applying blank mask
        u = np.ma.masked_array(u, np.ma.nomask)
        v = np.ma.masked_array(v, np.ma.nomask) 
            
        return x, y, u, v 

    def ensemble_firstpass(
        frame_a,frame_b,
        window_size,
        overlap,
        iterations = 1,
        current_iteration = 1,
        correlation_method = "circular",
        normalized_correlation = False):
        
        aa = piv_prc.moving_window_array(frame_a, window_size, overlap)
        bb = piv_prc.moving_window_array(frame_b, window_size, overlap)
    
        corr = piv_prc.fft_correlate_images(
            aa, bb,
            correlation_method = correlation_method,
            normalized_correlation = normalized_correlation)
        
        return corr

            