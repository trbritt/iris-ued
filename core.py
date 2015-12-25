# -*- coding: utf-8 -*-
#Basics
from __future__ import division
import numpy as n
import scipy.optimize as opt


# -----------------------------------------------------------------------------
#           HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def Gaussian(x, xc = 0, width_g = 0.1):
    """ Returns a Gaussian with maximal height of 1 (not area of 1)."""
    exponent = (-(x-xc)**2)/((2*width_g)**2)
    return n.exp(exponent)

def Lorentzian(x, xc = 0, width_l = 0.1):
    """ Returns a lorentzian with maximal height of 1 (not area of 1)."""
    core = ((width_l/2)**2)/( (x-xc)**2 + (width_l/2)**2 )
    return core
    
def pseudoVoigt(x, height, xc, width_g, width_l, constant = 0):
    """ Returns a pseudo Voigt profile centered at xc with weighting factor 1/2. """
    return height*(0.5*Gaussian(x, xc, width_g) + 0.5*Lorentzian(x, xc, width_l)) + constant
    
def biexp(x, a = 0, b = 0, c = 0, d = 0, e = 0, f = 0):
    """ Returns a biexponential of the form a*exp(-b*x) + c*exp(-d*x) + e"""
    return a*n.exp(-b*(x-f)) + c*n.exp(-d*(x-f)) + e

def bilor(x, center, amp1, amp2, width1, width2, const):
    """ Returns a Bilorentzian functions. """
    return amp1*Lorentzian(x, center, width1) + amp2*Lorentzian(x, center, width2) + const
    
# -----------------------------------------------------------------------------
#           I/O FUNCTIONS
# -----------------------------------------------------------------------------

def diffractionFileList(folder_path = 'C:\\' ):
    """
    returns a list of filenames corresponding to diffraction pictures
    """
    return
    
# -----------------------------------------------------------------------------
#           RADIAL CURVE CLASS
# -----------------------------------------------------------------------------

class RadialCurve(object):
    """
    This class represents any radially averaged diffraction pattern or fit.
    """
    def __init__(self, xdata, ydata, name = '', color = 'b'):
        
        self.xdata = xdata
        self.ydata = ydata
        self.name = name
        #Plotting attributes
        self.color = color
    
    def plot(self, axes, **kwargs):
        """ Plots the pattern in the axes specified """
        axes.plot(self.xdata, self.ydata, '.-', color = self.color, label = self.name, **kwargs)
       
        #Plot parameters
        axes.set_xlim(self.xdata.min(), self.xdata.max())  #Set xlim and ylim on the first pattern args[0].
        axes.set_ylim(self.ydata.min(), self.ydata.max())
        axes.set_aspect('auto')
        axes.set_title('Diffraction pattern')
        axes.set_xlabel('radius (px)')
        axes.set_ylabel('Intensity')
        axes.legend( loc = 'upper right', numpoints = 1)
    
    def __sub__(self, pattern):
        """ Definition of the subtraction operator. """ 
        #Interpolate values so that substraction makes sense
        return RadialCurve(self.xdata, self.ydata - n.interp(self.xdata, pattern.xdata, pattern.ydata), name = self.name, color = self.color)

    def cutoff(self, cutoff = [0,0]):
        """ Cuts off a part of the pattern"""
        cutoff_index = n.argmin(n.abs(self.xdata - cutoff[0]))
        return RadialCurve(self.xdata[cutoff_index::], self.ydata[cutoff_index::], name = 'Cutoff ' + self.name, color = self.color)

    def prototypeInelasticBGSubstract(self, points = list(), chunk_size = 5):
        """ 
        Following Vance's inelastic background substraction method. We assume that the data has been corrected for diffuse scattering by substrate 
        (e.g. silicon nitride substrate for VO2 samples)
        
        In order to determine the shape of the background, we use a list of points selected by the user as 'diffraction feature'. These diffraction features are fit with 
        a pseudo-Voigt + constant. Concatenating this constant for multiple diffraction features, we can get a 'stair-steps' description of the background. We then smooth this
        data to get a nice background.
        
        Parameters
        ----------
        xdata, ydata : ndarrays, shape (N,)
        
        points : list of array-like
        """
        
        #Determine data chunks based on user-input points
        xfeatures = n.asarray(points)[:,0]      #Only consider x-position of the diffraction feature
        xchunks, ychunks= list(), list()
        for feature in xfeatures:
            #Find where in xdata is the feature
            ind = n.argmin(n.abs(self.xdata - feature))
            chunk_ind = n.arange(ind - chunk_size, ind + chunk_size + 1)    #Add 1 to stop parameter because chunk = [start, stop)
            xchunks.append(self.xdata[chunk_ind])
            ychunks.append(self.ydata[chunk_ind])
        
        #Fit a pseudo-Voigt + constant for each xchunk and save constant
        voigt_parameters = list()
        constants = list()
        for xchunk, ychunk in zip(xchunks, ychunks):
            temp_ychunk = ychunk - ychunk.min()         #Trick to get a better fit: remove most of the offset
            parameter_guesses = [temp_ychunk.max(), (xchunk.max()-xchunk.min())/2 + xchunk.min(), 0.1, 0.1, 0]
            opt_parameters = opt.curve_fit(pseudoVoigt, xchunk, ychunk, p0 = parameter_guesses)[0]
            voigt_parameters.append(opt_parameters)
            constants.append(opt_parameters[-1]*n.ones_like(xchunk) + ychunk.min())    # constant is the last parameter in the definition of pseudoVoigt
        
        #Extend constants to x-values outside xchunks
        constant_background = n.asarray(constants).flatten()
        x_background = n.asarray(xchunks).flatten()
        background = RadialCurve(self.xdata,n.interp(self.xdata, x_background, constant_background),'background')
        
        #Create diagnostics Voigt profiles
        profiles = list()
        for index, params in enumerate(voigt_parameters):
            profiles.append( RadialCurve(self.xdata,pseudoVoigt(self.xdata, params[0], params[1], params[2], params[3], params[4]),'peak'+str(index)) ) 
    
        #TODO: smooth background data
        return background, profiles

    def inelasticBG(self, points = list(), fit = 'biexp'):
        """
        Inelastic scattering background substraction.
        
        Parameters
        ----------
        patterns : list of lists of the form [xdata, ydata, name]
        
        points : list of lists of the form [x,y]
        
        fit : string
            Function to use as fit. Allowed values are 'biexp' and 'bilor'
        """
        #Preliminaries
        function = bilor if fit == 'bilor' else biexp
        
        #Create x arrays for the points 
        points = n.array(points, dtype = n.float) 
        x = points[:,0]
        
        #Create guess 
        guesses = {'biexp': (self.ydata.max()/2, 1/50.0, self.ydata.max()/2, 1/150.0, self.ydata.min(), self.xdata.min()), 
                   'bilor':  (self.xdata.min(), self.ydata.max()/1.5, self.ydata.max()/2.0, 50.0, 150.0, self.ydata.min())}
        
        #Interpolate the values of the patterns at the x points
        y = n.interp(x, self.xdata, self.ydata)
        
        #Fit with guesses if optimization does not converge
        try:
            optimal_parameters, parameters_covariance = opt.curve_fit(function, x, y, p0 = guesses[fit]) 
        except(RuntimeError):
            print 'Runtime error'
            optimal_parameters = guesses[fit]
    
        #Create inelastic background function 
        a,b,c,d,e,f = optimal_parameters
        new_fit = function(self.xdata, a, b, c, d, e, f)
        
        return RadialCurve(self.xdata, new_fit, 'IBG ' + self.name)


# -----------------------------------------------------------------------------
#           FIND CENTER OF DIFFRACTION PATTERN
# -----------------------------------------------------------------------------

def fCenter(xg, yg, rg, im, scalefactor = 20):
    """
    Finds the center of a diffraction pattern based on an initial guess of the center.
    
    Parameters
    ----------
    xg, yg, rg : ints
        Guesses for the (x,y) position of the center, and the radius
    im : ndarray, shape (N,N)
        ndarray of a TIFF image
    
    Returns
    -------
    optimized center and peak position
    
    See also
    --------
    Scipy.optimize.fmin - Minimize a function using the downhill simplex algorithm
    """
    
    #find maximum intensity
    xgscaled, ygscaled, rgscaled = n.array([xg,yg,rg])/scalefactor
    c1 = lambda x: circ(x[0],x[1],x[2],im)
    xcenter, ycenter, rcenter = n.array(\
        opt.minimize(c1,[xgscaled,ygscaled,rgscaled],\
        method = 'Nelder-Mead').x)*scalefactor
    rcenter = rg    
    return xcenter, ycenter, rcenter

def circ(xg, yg, rg, im, scalefactor = 20):

    """
    Sums the intensity over a circle of given radius and center position
    on an image.
    
    Parameters
    ----------
    xg, yg, rg : ints
        The (x,y) position of the center, and the radius
    im : ndarray, shape (N,N)
        ndarray of a TIFF image
    
    Returns
    -------
    Total intensity at pixels on the given circle. 
    
    """
     #image size
    s = im.shape[0]
    xgscaled, ygscaled, rgscaled = n.array([xg,yg,rg])*scalefactor
    xMat, yMat = n.meshgrid(n.linspace(1, s, s),n.linspace(1, s, s))
    # find coords on circle and sum intensity
    
    residual = (xMat-xgscaled)**2+(yMat-ygscaled)**2-rgscaled**2
    xvals, yvals = n.where(((residual < 10) & (yMat > 550)))
    ftemp = n.mean(im[xvals, yvals])
    
    return 1/ftemp

# -----------------------------------------------------------------------------
#               RADIAL AVERAGING
# -----------------------------------------------------------------------------

def radialAverage(image, name, center = [562,549]):
    """
    This function returns a radially-averaged pattern computed from a TIFF image.
    
    Parameters
    ----------
    image : list of ndarrays, shape(N,N)
        List of images that have the same shape and share the same center.
    center : array-like, shape (2,)
        [x,y] coordinates of the center (in pixels)
    beamblock_rectangle : list, shape (2,)
        Two corners of the rectangle, in the form [ [x0,y0], [x1,y1] ]  
    Returns
    -------
    [[radius1, pattern1, name1], [radius2, pattern2, name2], ... ], : list of ndarrays, shapes (M,), and an ID string
    """
    
    #Get shape
    im_shape = image.shape
    #Preliminaries
    xc, yc = center     #Center coordinates
    x = n.linspace(0, im_shape[0], im_shape[0])
    y = n.linspace(0, im_shape[1], im_shape[1])
    
    #Create meshgrid and compute radial positions of the data
    X, Y = n.meshgrid(x,y)
    R = n.around(n.sqrt( (X - xc)**2 + (Y - yc)**2 ), decimals = 0)
    
    #Flatten arrays
    intensity = image.flatten()
    radius = R.flatten()
    
    #Sort by increasing radius
    intensity = intensity[n.argsort(radius)]
    radius = n.around(radius, decimals = 0)
    
    #Average intensity values for equal radii
    unique_radii = n.unique(radius)
    accumulation = n.zeros_like(unique_radii)
    bincount =  n.ones_like(unique_radii)
    
    #loop over image
    for (i,j), value in n.ndenumerate(image):
      
        #Ignore top half image (where the beamblock is)
        if i < center[0]:
            continue

        r = R[i,j]
        #bin
        ind = n.where(unique_radii==r)
        #increment
        accumulation[ind] += value
        bincount[ind] += 1
        
        #Return normalized radial average
    return RadialCurve(unique_radii, n.divide(accumulation,bincount), name + ' radial average')