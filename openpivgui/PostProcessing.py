#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Post Processing for OpenPIVGui.'''

from openpivgui.open_piv_gui_tools import create_save_vec_fname, save
import openpiv.smoothn as piv_smt
import openpiv.filters as piv_flt
import openpiv.validation as piv_vld
import openpiv.tools as piv_tls
import numpy as np
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


def ValidateResults(parameter, u, v, tp):
    mask = tp  
    
    '''if s2n(self):
        u, v, Mask = piv_vld.sig2noise_val(
            u, v, s2n,
            threshold=self.p['sig2noise_threshold'])'''
        
    if parameter['vld_global_thr']:
        u, v, Mask = piv_vld.global_val(
            u, v,
            u_thresholds=(parameter['MinU'], parameter['MaxU']),
            v_thresholds=(parameter['MinV'], parameter['MaxV']))
        mask += Mask # consolidate effects of mask
                
    if parameter['vld_global_std']:
        u, v, Mask = piv_vld.global_std(
            u, v, 
            std_threshold=parameter['global_std_threshold'])
        mask += Mask
                    
    if parameter['vld_local_med']:
        u, v, Mask = piv_vld.local_median_val(
            u, v,
            u_threshold = parameter['local_median_threshold'],
            v_threshold = parameter['local_median_threshold'],
            size        = parameter['local_median_size'])  
        mask += Mask
                
    if parameter['repl']:
        u, v = piv_flt.replace_outliers(
            u, v,
            method      = parameter['repl_method'],
            max_iter    = parameter['repl_iter'],
            kernel_size = parameter['repl_kernel'])
        
    return u, v, mask



def ModifyResults(parameter, x, y, u, v):
    
    if parameter['offset_grid']:
        x_off = parameter['offset_x']
        y_off = parameter['offset_y']
    else:
        x_off = 0
        y_off = 0
        
    if parameter['modify_velocity']:
        u_mod = parameter['modify_u']
        v_mod = parameter['modify_v']
    else:
        u_mod = 0
        v_mod = 0
        
    if parameter['smoothn']:
        u, _, _, _ = piv_smt.smoothn(
            u, s = parameter['smoothn_val'],
            isrobust = parameter['robust'])
        
        v, _, _, _ = piv_smt.smoothn(
            v, s = parameter['smoothn_val'],
            isrobust = parameter['robust'])
        
        return x_off, y_off, u_mod, v_mod, u, v
        