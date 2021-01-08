#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''Pre Processing for OpenPIVGui.'''

from skimage import exposure, filters, util
from scipy.ndimage.filters import gaussian_filter, median_filter
from scipy.signal.signaltools import wiener as wiener_filter
import openpiv.preprocess as piv_pre
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

'''Pre Processing chain for image arrays.

Parameters
----------
params : openpivgui.OpenPivParams
    Parameter object.
'''


def gen_background(self, image1=None, image2=None):
    self.p = self
    images = self.p['fnames'][self.p['starting_frame']: self.p['ending_frame']]
    # This needs more testing. It creates artifacts in the correlation for images not selected in the background.
    if self.p['background_type'] == 'global min':
        background = piv_tls.imread(self.p['fnames'][self.p['starting_frame']])
        maximum = background.max()
        background = background / maximum
        background *= 255
        for im in images:
            # the original image is already included, so skip it in the for loop
            if im == self.p['fnames'][self.p['starting_frame']]:
                pass
            else:
                image = piv_tls.imread(im)
                maximum = image.max()
                image = image / maximum
                image *= 255
                background = np.min(np.array([background, image]), axis=0)
        return(background)

    elif self.p['background_type'] == 'global mean':
        images = self.p['fnames'][self.p['starting_frame']
            : self.p['ending_frame']]
        background = piv_tls.imread(self.p['fnames'][self.p['starting_frame']])
        maximum = background.max()
        background = background / maximum
        background *= 255
        for im in images:
            # the original image is already included, so skip it in the for loop
            if im == self.p['fnames'][self.p['starting_frame']]:
                pass
            else:
                image = piv_tls.imread(im)
                maximum = image.max()
                image = image / maximum
                image *= 255
                background += image
        background /= (self.p['ending_frame'] - self.p['starting_frame'])
        return(background)

    elif self.p['background_type'] == 'minA - minB':
        # normalize image1 and image2 intensities to [0,255]
        maximum1 = image1.max()
        maximum2 = image2.max()
        image1 = image1 / maximum1
        image2 = image2 / maximum2
        image1 *= 255
        image2 *= 255
        background = np.min(np.array([image2, image1]), axis=0)
        return(background)

    else:
        print('Background algorithm not implemented.')


def process_images(img,  
                   preproc = True,
                   do_background = False,
                   background = None,
                   roi_xmin = '',
                   roi_xmax = '',
                   roi_ymin = '',
                   roi_ymax = '',
                   invert = False,
                   median_filt = False,
                   median_kernel = 20,
                   CLAHE = False,
                   CLAHE_auto_kernel = True,
                   CLAHE_kernel = 20,
                   CLAHE_clip = 1,
                   high_pass = False,
                   hp_sigma = 5,
                   intensity_cap = False,
                   ic_mult = 2,
                   wiener_filt = False,
                   wiener_size = 5,
                   gaussian_filt = False,
                   gf_sigma = 2,
                   intensity_clip = False,
                   intensity_clip_min = 15,
        ):
    
    '''Starting the pre-processing chain'''
    # normalize image to [0, 1] float
    maximum = img.max()
    img = img / maximum
    
    # resize intensities to [0, 255]
    resize = 255
    
    if preproc:
        if invert == True:
            img = util.invert(img)

        if do_background:
            try:
                img *= 255
                img -= background
                img[img<0] = 0 # values less than zero are set to zero
                img = img / 255
            except:
                print('Could not subtract background. Ignoring background subtraction.')

        if roi_xmin and roi_xmax and roi_ymin and roi_ymax != ('', ' '):
            try:
                xmin=int(roi_xmin)
                xmax=int(roi_xmax)
                ymin=int(roi_ymin)
                ymax=int(roi_ymax)
                img = img[ymin:ymax,xmin:xmax]  
            except:
                print('invalid value in roi, ignoring filter.')
        if median_filt == True:
            img = median_filter(img, size = median_kernel)
            
        if CLAHE == True:
            if CLAHE_auto_kernel:
                kernel = None
            else:
                kernel = CLAHE_kernel
            if CLAHE_clip < 1:
                clip_limit = 0.01
            elif CLAHE_clip > 100:
                clip_limit = 1
            else:
                clip_limit = CLAHE_clip/100
            img = exposure.equalize_adapthist(img, 
                                              kernel_size = kernel, 
                                              clip_limit  = clip_limit,
                                              nbins       = 256)

        if high_pass == True:
            low_pass = gaussian_filter(img, sigma = hp_sigma)
            img -= low_pass

        # simple intensity capping
        if intensity_cap == True:
            upper_limit = np.mean(img) + ic_mult * img.std()
            img[img > upper_limit] = upper_limit

        # simple intensity clipping
        if intensity_clip == True:
            img *= resize
            lower_limit = intensity_clip_min
            img[img < lower_limit] = 0
            img /= resize
        
        # wiener low pass filter
        if wiener_filt == True:
            img = wiener_filter(img, (wiener_size, wiener_size))
            
        # gausian low pass with gausian kernel
        if gaussian_filt == True:
            img = gaussian_filter(img, sigma = gf_sigma)

    img[img < 0] = 0
    return(np.uint8(img * resize))
