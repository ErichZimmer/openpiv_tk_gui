import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as messagebox
import openpiv.tools as piv_tls

# A lot of optimization could be done in this file.


# check number of images, image types, and window sizing
def check_PIVprocessing(self, session):
    self.p = self
    self.session = session
    '''Error checking'''
    # making sure there are 2 or more files loaded
    message = 'Please select two or more image files and/or apply an image frequence.'
    if len(self.p['fnames']) < 1:
        if self.p['warnings']:
            messagebox.showwarning(title='Error Message',
                                   message=message)
        raise Exception(message)

    # checking for images
    message = "Please supply image files in 'bmp', 'tiff', 'tif', 'TIF', 'jpg', 'jpeg', 'png', 'pgm'."
    test = self.session['files_a'][0]
    ext = test.split('.')[-1]
    if ext not in ['bmp', 'tiff', 'tif', 'TIF', 'jpg', 'jpeg', 'png', 'pgm']:
        if self.p['warnings']:
            messagebox.showwarning(title='Error Message',
                                   message=message)
        raise Exception(message)

    # checking interrogation window sizes in an inefficent manner (for now)
    test = piv_tls.imread(test)
    message = ('Please lower your starting interrogation window size.')
    # making sure that the initial window is not too large
    xmin = self.p['img_preproc']['0'][0]
    xmax = self.p['img_preproc']['0'][1]
    ymin = self.p['img_preproc']['0'][2]
    ymax = self.p['img_preproc']['0'][3]
    try:
        if xmin and xmax and ymin and ymax != ('', ' '):
            test = test[int(ymin):int(ymax), int(xmin):int(xmax)]
    except: pass
    
    if ((test.shape[0] / self.p['corr_window_1']) < 2.5 or
             (test.shape[1] / self.p['corr_window_1']) < 2.5):
        if self.p['warnings']:
            messagebox.showwarning(title='Error Message',
                                   message=message)
        raise ValueError(message)
    # making sure each pass has a decreasing interrogation window
    Message = 'Plase make sure that the custom windowing is decreasing with each pass.'
    window = self.p['corr_window_1']
    for i in range(2, 6):
        if self.p['pass_%1d' % i]:
            if window >= self.p['corr_window_%1d' % i]:
                window = self.p['corr_window_%1d' % i]

            else:
                if self.p['warnings']:
                    messagebox.showwarning(title='Error Message',
                                           message=Message)
                raise ValueError(Message)
        else:
            break

def check_processing(self):  # check for threads
    self = self
    message = 'Please stop all threads/processes to start processing.'
    checker = 0
    # check if any threads are alive
    try:
        if self.processing_thread.is_alive():
            if self.p['warnings']:
                messagebox.showwarning(title='Error Message',
                                       message=message)
            checker += 1
    except:
        pass

    try:
        if self.postprocessing_thread.is_alive():
            if self.p['warnings']:
                messagebox.showwarning(title='Error Message',
                                       message=message)
            checker += 1
    except:
        pass
    # if a thread is alive, an error shall be raised
    if checker != 0:
        # raising errors did not work in try statement for some reason
        raise Exception(message)
