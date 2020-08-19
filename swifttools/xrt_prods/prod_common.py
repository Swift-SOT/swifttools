# The variable that indicates if a parameter is required
classReqPar = {'lc': 'lc',
             'spec': 'spec',
             'psf': 'dopsf',
             'enh': 'doenh',
             'xastrom': 'doxastrom',
             'image': 'image'
             }


# Conversion from the short-form normally used to reference them, so a
# full name for printing
longProdName = {'lc': 'light curve',
                'spec': 'spectrum',
                'psf': 'standard position',
                'enh': 'enhanced position',
                'xastrom': 'astrometric position',
                'image': 'image'}

# Conversion from the long name used by the Python interface, to my
# abbrevations
longToShort = {'LightCurve': 'lc',
               'Spectrum': 'spec',
               'StandardPos': 'psf',
               'EnhancedPos': 'enh',
               'AstromPos': 'xastrom',
               'Image': 'image'}

# Conversion from my abbreviations to those used by the Python
# interface.               
shortToLong = {'lc': 'LightCurve',
               'spec': 'Spectrum',
               'psf': 'StandardPos',
               'enh': 'EnhancedPos',
               'xastrom': 'AstromPos',
               'image': 'Image'}

# downloadFormats lists supported download formats:
downloadFormats = ('zip', 'tar', 'tar.gz')

