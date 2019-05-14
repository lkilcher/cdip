import urllib
import netCDF4 as nc4
import numpy as np
import requests
from lxml import html
from diskcache import Cache
import os
from .time import Date64


pkg_dir = os.path.dirname(os.path.realpath(__file__))
cache_dir = pkg_dir + '/.cache_data/'


def get_dirspec(id, time):

    time_string = time.astype('O').strftime('%Y%m%d%H%M')

    url = ('http://cdip.ucsd.edu/data_access/'
           'MEM_2dspectra.cdip?sp{:03d}01{}'.format(id, time_string))

    urlf = urllib.urlopen(url)
    dat = urlf.read()[6:-7]
    urlf.close()
    return np.fromstring(dat, sep=' ').reshape(64, -1)


def get_NDBCnum(cdip_metadata_link):
    page = requests.get(cdip_metadata_link)
    idx = page.content.find('NDBC')
    return int(page.content[idx + 5:idx + 10])


def load_hist_stations():

    info = requests.get('http://thredds.cdip.ucsd.edu/thredds/catalog/cdip/archive/catalog.html')
    tree = html.fromstring(info.content)

    rows = tree.getchildren()[1].getchildren()[2].getchildren()

    hist_stations = []
    for irow, row in enumerate(rows):
        try:
            t = row.getchildren()[0].getchildren()[1].getchildren()[0].text
        except:
            #print "NOTHING FOUND AT ROW {}".format(irow)
            continue
        if t.endswith('/'):
            # The first three numbers are the station ID.
            hist_stations.append(int(t[:3]))
    hist_stations = np.unique(hist_stations)
    return hist_stations


def load_realtime_stations():

    rtdat = nc4.Dataset(
        "http://thredds.cdip.ucsd.edu/thredds/dodsC/cdip/realtime/latest_3day.nc"
    )
    realtime_stations = np.sort([int(val.tostring()
                                     .rstrip(u'\x00').split('p')[0])
                                 for val in rtdat.variables['metaSiteLabel']])
    return realtime_stations


def _parse_deploy(deploy=None):
    if deploy is None:
        sufx = 'historic'
    elif deploy == 'realtime':
        sufx = 'rt'
    elif isinstance(deploy, str):
        sufx = 'd' + deploy
    else:
        sufx = 'd{:02d}'.format(deploy)
    return sufx


def get_thredd(station, deploy=None, cache_only=False):

    if cache_only:
        return CDIPbuoy(None, cache_id=(station, deploy))

    if deploy == 'realtime':
        url = ('http://thredds.cdip.ucsd.edu/thredds/'
               'dodsC/cdip/realtime/'
               '{st:03d}p1_{dep}.nc'.format(st=station,
                                            dep=_parse_deploy(deploy)))
    else:
        url = ('http://thredds.cdip.ucsd.edu/thredds/'
               'dodsC/cdip/archive/{st:03d}p1/'
               '{st:03d}p1_{dep}.nc'.format(st=station,
                                            dep=_parse_deploy(deploy)))

    nc = nc4.Dataset(url)
    return CDIPbuoy(nc)


def _cache_name(inval, deploy=None):
    if isinstance(inval, nc4.Dataset):
        tmpid = inval.id.split('_')
        return '{}.{}.cache'.format(tmpid[1], tmpid[2])
    return '{:03d}p1.{}.cache'.format(inval, _parse_deploy(deploy))


class CDIPbuoy(object):

    def __init__(self, ncdf, cache_id=False):
        self.ncdf = ncdf
        if ncdf is None and cache_id:
            self._data_cache = Cache(cache_dir + _cache_name(*cache_id))
            return
        self._data_cache = Cache(cache_dir + _cache_name(ncdf), tag_index=True)
        for ky in self.ncdf.variables:
            if ky.endswith('Time') and ky not in self._data_cache:
                tmp = Date64(ncdf.variables[ky][:].astype('datetime64[s]'))
                self._data_cache.set(ky, tmp)
        self.NDBC_num = get_NDBCnum(self.ncdf.metadata_link)

    def __getattr__(self, name):
        name = unicode(name)
        if name in self._data_cache:
            return self._data_cache[name]
        if name in self.variables:
            self._data_cache[name] = self.variables[name][:]
            return self._data_cache[name]
        raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__, name))

    def keys(self, ):
        return self.ncdf.variables.keys()

    @property
    def variables(self, ):
        return self.ncdf.variables

    def spec_moment(self, arr=None, n=0):
        df = np.diff(self.waveFrequencyBounds, ).T
        f = self.waveFrequency[None, :]
        spec = self.waveEnergyDensity
        if arr is None:
            return (f ** n * spec * df).sum(-1)
        return (arr * f ** n * spec * df).sum(-1)

    @property
    def id(self, ):
        return int(self.ncdf.metadata_link.rsplit('/', 1)[-1][:3])

    def get_dirspec(self, idx):
        return DirSpec(get_dirspec(self.id, self.waveTime[idx]),
                       freq=self.waveFrequency)


class DirSpec(object):

    def __init__(self, spec, freq, angle=None, time=None):

        if angle is None:
            dang = 2 * np.pi / spec.shape[-1]
            angle = np.arange(dang / 2, 2 * np.pi, dang)
        self.angle = angle
        self.freq = freq
        self.spec = spec
        self.time = time

    def __getitem__(self, sub):
        if not isinstance(sub, tuple):
            sub = (sub, slice(None))
        return DirSpec(self.spec[sub], self.freq[sub[0]], self.angle[sub[1]])

    @property
    def wrapped(self, ):
        return np.concatenate((self.spec, self.spec[..., :1]), axis=-1)

    @property
    def angle_wrapped(self, ):
        return np.hstack((self.angle, self.angle[:1] + 2 * np.pi))


class TimeDirSpec(DirSpec):

    def __init__(self, spec, time, freq, angle=None):
        DirSpec.__init__(self, spec, freq, angle)
        self.time = time

    def __getitem__(self, sub):
        subs_ = [slice(None), ] * 3
        if isinstance(sub, tuple):
            for idx, s in enumerate(sub):
                subs_[idx] = s
        else:
            subs_ = [sub] + subs_[1:]
        if isinstance(subs_[0], int):
            return DirSpec(self.spec[subs_],
                           self.freq[subs_[1]],
                           self.angle[subs_[2]],
                           time=self.time[subs_[0]])
        else:
            return TimeDirSpec(self.spec[subs_], self.time[subs_[0]],
                               self.freq[subs_[1]], self.angle[subs_[2]])


def calc_resourcematrix(buoy, Hs_edges, Tp_edges):
    time = Date64(np.arange(buoy.waveTime[0].astype('datetime64[M]'),
                            buoy.waveTime[-1].astype('datetime64[M]'), ))
    hs = buoy.ncdf.variables['waveHs'][:]
    tp = buoy.ncdf.variables['waveTp'][:]
    # Pad the edges with 0 and inf
    Tp_edges = np.pad(Tp_edges,
                      pad_width=(int(Tp_edges[0] > 0), int(Tp_edges[-1] != np.inf)),
                      mode='constant', constant_values=(0, np.inf))
    Hs_edges = np.pad(Hs_edges,
                      pad_width=(int(Hs_edges[0] > 0), int(Hs_edges[-1] != np.inf)),
                      mode='constant', constant_values=(0, np.inf))
    matout = np.zeros((len(time), len(Hs_edges) - 1, len(Tp_edges) - 1, ))
    num_hours = np.zeros(len(time), dtype=np.uint16)
    for itime, t in enumerate(time):
        year = int(str(t)[:4])
        month = int(str(t)[5:])
        ind = (buoy.waveTime.year == year) & (buoy.waveTime.month == month)
        h, xedg, yedg = np.histogram2d(hs[ind], tp[ind], [Hs_edges, Tp_edges, ])
        matout[itime] = h * 0.5
        # This is the number of hours at a given resource level.
        if month in [1, 3, 5, 7, 8, 10, 12]:
            dt = 31 * 24
        elif month == 2:
            dt = (np.datetime64('{}-03-01T00'.format(year)) -
                  np.datetime64('{}-02-01T00'.format(year))).astype(np.uint16)
        else:
            dt = 30 * 24
        num_hours[itime] = dt
        #return matout, time, num_hours
    return matout, time, num_hours
