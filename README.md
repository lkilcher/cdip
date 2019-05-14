This is a Python library for accessing wave data on cdip.ucsd.edu servers.

Install
=======

To install this tool: downloading/clone the repo, to a folder that is in your python path (i.e., the files should be in `<some-folder-in-python-path>/cdip/`). 

Install the requirements with pip:

    pip install -r requirements.txt
    
Usage
=====

Then, you can use the tool by doing:

    import cdip
    dat = cdip.get_thredd(134)  # This example gets data from CDIP buoy #34

Here, `dat` is a data-object wrapper around a NetCDF file that is hosted on CDIP's servers. The NetCDF variables that are in the file are in `dat.variables`. The wrapper also uses caching to store data locally (see below).

You can view the names of the available variables by doing `dat.variables.keys()`. You can then view a variables metadata (e.g., `'waveEnergyDensity'`)by doing:

    >>> dat.variables['waveEnergyDensity']
    <class 'netCDF4._netCDF4.Variable'>
    float32 waveEnergyDensity(waveTime, waveFrequency)
        long_name: band energy density
        units: meter^2 second
        _FillValue: -999.99
        standard_name: sea_surface_wave_variance_spectral_density
        coordinates: metaStationLatitude metaStationLongitude
        grid_mapping: metaGridMapping
        valid_min: 0.0
        ancillary_variables: waveFlagPrimary waveFrequencyFlagPrimary waveFlagSecondary waveFrequencyFlagSecondary
        ncei_name: WAVE ENERGY - SPECTRAL VALUE
    unlimited dimensions: 
    current shape = (208252, 64)
    filling off

To actually pull the data over the network, do:

    spec_array = dat.variables['waveEnergyDensity'][:]
    
This will pull the entire array over, which will take some time, and will eat some disk space in the `.cache_data/` folder. Note, however, that this is only the frequency spectrum. If you want the *frequency-direction* spectrum, you'll need to do:

    dirspec = dat.get_dirspec(0)
    
Note here `get_dirspec` only works for a single time (in this case the first time-step in the data object). This is because the entire directional spectrum is very large, and it would take a long time to pull all of that data over the network.

Caching
=======

This tool utilizes the DiskCache libary to store data locally after you've pulled it over the network. This data is stored in the `.cache_data/` folder. The tool always check is a variable is present in the cache before querying the server. It does not check whether there is new data available. This means that you need to clear the cache to update the data. Delete the files/folder in that folder to clear the cache.
