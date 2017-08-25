from datetime import datetime as dt
import numpy as np
import calendar
import urllib
import netCDF4


def find_nearest(array, value):
    # Find nearest value in numpy array
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def getUnixTimestamp(humanTime, dateFormat):
    # Convert to unix timestamp
    unixTimestamp = int(calendar.timegm(dt.strptime(humanTime,
                                                    dateFormat).timetuple()))
    return unixTimestamp


def getHumanTimestamp(unixTimestamp, dateFormat):
    # Convert to human readable timestamp
    humanTimestamp = dt.utcfromtimestamp(int(unixTimestamp)).strftime(dateFormat)
    return humanTimestamp


def get_dirspec(station, time):

    
    url = ('http://cdip.ucsd.edu/data_access/'
           'MEM_2dspectra.cdip?sp{}01{}'.format(stn, neardate))

    data = urllib.urlopen(url)
    readdata = data.read()
    datas = readdata.split("\n")
    return datas
    
if __name__ == '__main__':
    stn = '071'
    startdate = "10/17/2012 16:00"
    
    urlarc = 'http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/archive/' + stn + 'p1/' + stn + 'p1_historic.nc'

    nc = netCDF4.Dataset(urlarc)
    timevar = nc.variables['waveTime'][:]

    data = get_dirspec(stn, time)
