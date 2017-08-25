import numpy as np


time_factors = {'Y': 365 * 24,
                'M': 30 * 24,
                'D': 24,
                'H': 1,
                'm': 1. / 60,
                's': 1. / 3600, }
tmpval = time_factors['s']
for nm in ['ms', 'us', 'ns', 'ps', 'fs', 'as']:
    tmpval *= 1e-3
    time_factors[nm] = tmpval
del tmpval


def _td2hour(td):
    dtn = td.dtype.name
    if not dtn.startswith('timedelta64'):
        raise Exception("Wrong data type for 'td2hour' function.")
    dtn = dtn[12:-1]  # This strips 'timedelta64[' and ']'
    return td.astype(int, subok=False) * time_factors[dtn]


class Date64(np.ndarray):
    def __new__(cls, data):
        if isinstance(data, str):
            data = np.datetime64(data)
        data = np.asarray(data)
        if not str(data.dtype).startswith('datetime64'):
            raise Exception('Unable to parse dates adequately to datetime64: %s' % data)
        obj = data.view(cls)
        return obj

    @property
    def year(self):
        return np.array(self.astype('datetime64[Y]').astype(int) + 1970)

    @property
    def month(self):
        return np.array(self.astype('datetime64[M]').astype(int) % 12 + 1)

    @property
    def day(self):
        return np.array((self.astype('datetime64[D]') -
                         self.astype('datetime64[M]') + 1).astype(int))

    @property
    def hour(self):
        return np.array(self.astype('datetime64[h]').astype(int) % 24)

    @property
    def minute(self):
        return np.array(self.astype('datetime64[m]').astype(int) % 60)

    @property
    def second(self):
        return np.array(self.astype('datetime64[s]').astype(int) % 60)

    @property
    def ISO(self):
        if (self.shape):
            out = zip(self.Year(), self.Month(), self.Day())
            iso = ['%04d-%02d-%02d' % each for each in out]
        else:
            iso = '%04d-%02d-%02d' % (self.Year(), self.Month(), self.Day())
        return iso

    def Export(self):
        return self

    @property
    def datetime(self, ):
        return np.array(self.astype('O', subok=False))

    def __array_finalize__(self, obj):
        if obj is None:
            return

    def mean(self, *args, **kwargs):
        dtp = self.dtype
        tmpdat = self.astype(int)
        val0 = tmpdat.min()
        tmpdat -= val0
        return (np.ndarray.mean(tmpdat, *args, **kwargs) + val0).astype(dtp)

    def diff(self, ):
        return np.diff(self.datetime)

    def diff_hours(self, ):
        return _td2hour(np.diff(self, ))
