# -*- coding: utf-8 -*-
"""
.. module:: timeseries
   :synopsis: Deal with MT time series

:copyright:
    Jared Peacock (jpeacock@usgs.gov)
    
:license: 
    MIT
"""

# ==============================================================================
# Imports
# ==============================================================================
import logging
import inspect

import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import pyplot as plt

from mth5 import metadata
from mth5.utils.mttime import MTime
from mth5.utils.exceptions import MTTSError

# make a dictionary of available metadata classes
meta_classes = dict(inspect.getmembers(metadata, inspect.isclass))
# ==============================================================================

# ==============================================================================
class MTTS:
    """
    
    .. note:: Assumes equally spaced samples from the start time.
    
    The time series is stored in an :class:`xarray.Dataset` that has 
    coordinates of time and is a 1-D array labeled 'data'
    
    The time coordinate is made from the start time, sample rate and 
    number of samples.  Currently, End time is a derived property and 
    cannot be set. 
    
    
    MT time series object is based on xarray and :class:`mth5.metadata`

    """

    def __init__(self, channel_type, data=None, channel_metadata=None, **kwargs):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # get correct metadata class
        try:
            self.metadata = meta_classes[channel_type.capitalize()]()
        except KeyError:
            msg = (
                "Channel type is undefined, must be [ electric | "
                + "magnetic | auxiliary ]"
            )
            self.logger.error(msg)
            raise ValueError(msg)

        if channel_metadata is not None:
            if isinstance(channel_metadata, type(self.metadata)):
                self.metadata.from_dict(channel_metadata.to_dict())
                self.logger.debug(
                    "Loading from metadata class {0}".format(type(self.metadata))
                )
            elif isinstance(channel_metadata, dict):
                self.metadata.from_dict(channel_metadata)
                self.logger.debug("Loading from metadata dict")

            else:
                msg = "input metadata must be type {0} or dict, not {1}".format(
                    type(self.metadata), type(channel_metadata)
                )
                self.logger.error(msg)
                raise MTTSError(msg)

        self._ts = xr.DataArray([1], coords=[("time", [1])])
        self.update_xarray_metadata()

        if data is not None:
            self.ts = data

        for key in list(kwargs.keys()):
            setattr(self, key, kwargs[key])

    def __str__(self):
        return self.ts.__str__()

    def __repr__(self):
        return self.ts.__repr__()

    ###-------------------------------------------------------------
    ## make sure some attributes have the correct data type
    # make sure that the time series is a pandas data frame
    @property
    def ts(self):
        return self._ts

    @ts.setter
    def ts(self, ts_arr):
        """
        if setting ts with a pandas data frame, make sure the data is in a
        column name 'data'
        """
        if isinstance(ts_arr, np.ndarray):
            dt = self._make_dt_coordinates(self.start, self.sample_rate, ts_arr.size)
            self._ts = xr.DataArray(ts_arr, coords=[("time", dt)])
            self.update_xarray_metadata()

        elif isinstance(ts_arr, pd.core.frame.DataFrame):
            if isinstance(ts_arr.index[0], pd._libs.tslibs.timestamps.Timestamp):
                sr = 1./(ts_arr.index.freq.nanos / 1E9)
                dt = self._make_dt_coordinates(
                    ts_arr.index[0].isoformat(), sr, ts_arr["data"].size
                )
            else:
                dt = self._make_dt_coordinates(
                    self.start, self.sample_rate, ts_arr["data"].size
                )
            try:
                self._ts = xr.DataArray(ts_arr["data"], coords=[("time", dt)])

            except AttributeError:
                msg = (
                    "Data frame needs to have a column named `data` "
                    + "where the time series data is stored"
                )
                self.logger.error(msg)
                raise MTTSError(msg)

        elif isinstance(ts_arr, xr.DataArray):
            # TODO: need to validate the input xarray
            self._ts = ts_arr
            meta_dict = dict([(k, v) for k, v in ts_arr.attrs.items()])
            self.metadata.from_dict({self.metadata.type: meta_dict})

        else:
            msg = (
                "Data type {0} not supported".format(type(ts_arr))
                + ", ts needs to be a numpy.ndarray, pandas DataFrame, "
                + "or xarray.DataArray."
            )
            raise MTTSError(msg)

    def update_xarray_metadata(self):
        """
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        self.logger.debug("Updating xarray attributes")

        self.metadata.time_period.start = self.start.iso_no_tz
        self.metadata.time_period.end = self.end.iso_no_tz
        self.metadata.sample_rate = self.sample_rate

        self._ts.attrs.update(self.metadata.to_dict()[self.metadata._class_name])

    @property
    def component(self):
        """ component """
        return self.metadata.component
    
    @component.setter
    def component(self, comp):
        """ set component in metadata and carry through """
        if self.metadata.type == 'electric':
            if comp[0] != 'e':
                msg = ("The current timeseries is an electric channel. "
                       "Cannot change channel type, create a new MTTS object.")
                self.logger.error(msg)
                raise MTTSError(msg)
                
        elif self.metadata.type == 'magnetic':
            if comp[0] not in ['h', 'b']:
                msg = ("The current timeseries is a magnetic channel. "
                       "Cannot change channel type, create a new MTTS object.")
                self.logger.error(msg)
                raise MTTSError(msg)
                
        if self.metadata.type == 'auxiliary':
            if comp[0] in ['e', 'h', 'b']:
                msg = ("The current timeseries is an auxiliary channel. "
                       "Cannot change channel type, create a new MTTS object.")
                self.logger.error(msg)
                raise MTTSError(msg)
                
        self.metadata.component = comp
        self.update_xarray_metadata()
        
    # --> number of samples just to make sure there is consistency
    @property
    def n_samples(self):
        """number of samples"""
        return int(self.ts.size)

    @n_samples.setter
    def n_samples(self, n_samples):
        """number of samples (int)"""
        self.logger.warning(
            "Cannot set the number of samples. Use `MTTS.resample` or `get_slice`"
        )

    def _check_for_index(self):
        """
        check to see if there is an index in the time series
        """
        if len(self._ts) > 1:
            return True
        else:
            return False

    # --> sample rate
    @property
    def sample_rate(self):
        """sample rate in samples/second"""
        if self._check_for_index():
            sr = 1e9 / self._ts.coords.indexes["time"][0].freq.nanos
        else:
            self.logger.debug("Data has not been set yet, sample rate is from metadata")
            sr = self.metadata.sample_rate
            if sr is None:
                sr = 0.0
        return np.round(sr, 0)

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """
        sample rate in samples/second

        type float
        """
        self.metadata.sample_rate = sample_rate
        self.logger.warning(
            "Setting MTTS.metadata.sample_rate. "
            + "If you want to change the time series sample"
            + " rate use method `resample`."
        )

    ## set time and set index
    @property
    def start(self):
        """MTime object"""
        if self._check_for_index():
            return MTime(self._ts.coords.indexes["time"][0].isoformat())
        else:
            self.logger.debug(
                "Data not set yet, pulling start time from "
                + "metadata.time_period.start"
            )
            return MTime(self.metadata.time_period.start)

    @start.setter
    def start(self, start_time):
        """
        start time of time series in UTC given in some format or a datetime
        object.

        Resets epoch seconds if the new value is not equivalent to previous
        value.

        Resets how the ts data frame is indexed, setting the starting time to
        the new start time.
        """

        if not isinstance(start_time, MTime):
            start_time = MTime(start_time)

        self.metadata.time_period.start = start_time.iso_str
        if self._check_for_index():
            if start_time == MTime(self.ts.coords.indexes["time"][0].isoformat()):
                return
            else:
                new_dt = self._make_dt_coordinates(
                    start_time, self.sample_rate, self.n_samples
                )
                self.ts.coords["time"] = new_dt

        # make a time series that the data can be indexed by
        else:
            self.logger.warning("No data, just updating metadata start")

    @property
    def end(self):
        """MTime object"""
        if self._check_for_index():
            return MTime(self._ts.coords.indexes["time"][-1].isoformat())
        else:
            self.logger.debug(
                "Data not set yet, pulling end time from " + "metadata.time_period.end"
            )
            return MTime(self.metadata.time_period.end)

    @end.setter
    def end(self, end_time):
        """
        end time of time series in UTC given in some format or a datetime
        object.

        Resets epoch seconds if the new value is not equivalent to previous
        value.

        Resets how the ts data frame is indexed, setting the starting time to
        the new start time.
        """
        self.logger.warning(
            "Cannot set `end`. If you want a slice, then " + "use get_slice method"
        )

    def _make_dt_coordinates(self, start_time, sample_rate, n_samples):
        """
        get the date time index from the data

        :param start_time: start time in time format
        :type start_time: string
        """
        if len(self.ts) == 0:
            return

        if sample_rate in [0, None]:
            msg = (
                f"Need to input a valid sample rate. Not {sample_rate}, "
                + "returning a time index assuming a sample rate of 1"
            )
            self.logger.warning(msg)
            sample_rate = 1

        if start_time is None:
            msg = (
                f"Need to input a valid sample rate. Not {start_time}, "
                + "returning a time index with start time of "
                + "1980-01-01T00:00:00"
            )
            self.logger.warning(msg)
            start_time = "1980-01-01T00:00:00"

        if n_samples < 1:
            msg = f"Need to input a valid n_samples. Not {n_samples}"
            self.logger.error(msg)
            raise ValueError(msg)

        if not isinstance(start_time, MTime):
            start_time = MTime(start_time)

        dt_freq = "{0:.0f}N".format(1.0e9 / (sample_rate))

        dt_index = pd.date_range(
            start=start_time.iso_str.split("+", 1)[0], periods=n_samples, freq=dt_freq
        )

        return dt_index

    def get_slice(self, start, end):
        """
        Get a slice from the time series given a start and end time.
        
        Looks for >= start & <= end
        
        Uses loc to be exact with milliseconds
        
        :param start: DESCRIPTION
        :type start: TYPE
        :param end: DESCRIPTION
        :type end: TYPE
        :return: DESCRIPTION
        :rtype: TYPE

        """

        if not isinstance(start, MTime):
            start = MTime(start)
        if not isinstance(end, MTime):
            end = MTime(end)

        new_ts = self.ts.loc[
            (self.ts.indexes["time"] >= start.iso_no_tz)
            & (self.ts.indexes["time"] <= end.iso_no_tz)
        ]
        new_ts.attrs["time_period.start"] = new_ts.coords.indexes["time"][0].isoformat()
        new_ts.attrs["time_period.end"] = new_ts.coords.indexes["time"][-1].isoformat()

        return new_ts

    # decimate data
    def resample(self, dec_factor=1, inplace=False):
        """
        decimate the data by using scipy.signal.decimate

        :param dec_factor: decimation factor
        :type dec_factor: int

        * refills ts.data with decimated data and replaces sample_rate

        """

        new_dt_freq = "{0:.0f}N".format(1e9 / (self.sample_rate / dec_factor))

        new_ts = self.ts.resample(time=new_dt_freq).nearest(tolerance=new_dt_freq)
        new_ts.attrs["sample_rate"] = self.sample_rate / dec_factor
        self.metadata.sample_rate = new_ts.attrs["sample_rate"]

        if inplace:
            self.ts = new_ts

        else:
            new_ts.attrs.update(self.metadata.to_dict()[self.metadata._class_name])
            # return new_ts
            return MTTS(self.metadata.type, data=new_ts, metadata=self.metadata)


# =============================================================================
# run container
# =============================================================================
class RunTS:
    """
    holds all run ts in one aligned array
    
    components --> {'ex': ex_xarray, 'ey': ey_xarray}
    
    """

    def __init__(self, array_list=None, run_metadata=None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.metadata = metadata.Run()
        self._dataset = xr.Dataset()

        if run_metadata is not None:
            self.metadata.from_dict(run_metadata)

        if array_list is not None:
            self.dataset = array_list

    def _validate_array_list(self, array_list):
        """ check to make sure all entries are a :class:`MTTS` object"""

        if not isinstance(array_list, (tuple, list)):
            msg = f"array_list must be a list or tuple, not {type(array_list)}"
            self.logger.error(msg)
            raise TypeError(msg)

        for index, item in enumerate(array_list):
            if not isinstance(item, MTTS):
                msg = f"array entry {index} must be MTTS object not {type(item)}"
                self.logger.error(msg)
                raise TypeError(msg)

        return [x.ts for x in array_list]

    @property
    def summarize_metadata(self):
        """
        
        Get a summary of all the metadata
        
        :return: DESCRIPTION
        :rtype: TYPE

        """
        meta_dict = {}
        for comp in self.dataset.data_vars:
            for mkey, mvalue in self.dataset[comp].attrs.items():
                meta_dict[f"{comp}.{mkey}"] = mvalue

        return meta_dict

    def set_dataset(self, array_list, align_type="outer"):
        """
        
        :param array_list: list of xarrays
        :type array_list: list of :class:`mth5.timeseries.MTTS` objects
        :param align_type: how the different times will be aligned
            * ’outer’: use the union of object indexes
            * ’inner’: use the intersection of object indexes
            * ’left’: use indexes from the first object with each dimension
            * ’right’: use indexes from the last object with each dimension
            * ’exact’: instead of aligning, raise ValueError when indexes to
            be aligned are not equal
            * ’override’: if indexes are of same size, rewrite indexes to
            be those of the first object with that dimension. Indexes for
            the same dimension must have the same size in all objects.
        :type align_type: string

        """
        x_array_list = self._validate_array_list(array_list)

        # first need to align the time series.
        x_array_list = xr.align(*x_array_list, join=align_type)

        # input as a dictionary
        xdict = dict([(x.component.lower(), x) for x in x_array_list])
        self._dataset = xr.Dataset(xdict)

        self._dataset.attrs.update(self.metadata.to_dict()["run"])

    @property
    def dataset(self):
        return self._dataset

    @dataset.setter
    def dataset(self, array_list):
        msg = (
            "Data will be aligned using the min and max time. "
            "If that is not correct use set_dataset and change the alignment type."
        )
        self.logger.info(msg)
        self.set_dataset(array_list)

    @property
    def start(self):
        return MTime(self.dataset.coords["time"].to_index()[0].isoformat())

    @property
    def end(self):
        return MTime(self.dataset.coords["time"].to_index()[-1].isoformat())

    @property
    def sample_rate(self):
        return 1e9 / self.dataset.coords["time"].to_index().freq.n
    
    @property
    def ex(self):
        """ EX """
        if 'ex' in self.channels:
            return MTTS('electric', self.dataset['ex'])
        self.logger.info(f"Could not find EX in current run. {self.channels}")
        return None
        
    @property
    def ey(self):
        """ EY """
        if 'ey' in self.channels:
            return MTTS('electric', self.dataset['ey'])
        self.logger.info(f"Could not find EY in current run. {self.channels}")
        return None
    
    @property
    def hx(self):
        """ HX """
        if 'hx' in self.channels:
            return MTTS('magnetic', self.dataset['hx'])
        self.logger.info(f"Could not find HX in current run. {self.channels}")
        return None
    
    @property
    def hy(self):
        """ HY """
        if 'hy' in self.channels:
            return MTTS('magnetic', self.dataset['hy'])
        self.logger.info(f"Could not find HY in current run. {self.channels}")
        return None
    
    @property
    def hz(self):
        """ HZ """
        if 'hz' in self.channels:
            return MTTS('magnetic', self.dataset['hz'])
        self.logger.info(f"Could not find HX in current run. {self.channels}")
        return None
    
    @property
    def temperature(self):
        """ temperature """
        if 'temperature' in self.channels:
            return MTTS('auxiliary', self.dataset['temperature'])
        self.logger.info(f"Could not find temperature in current run. {self.channels}")
        return None
    
    @property
    def channels(self):
        return [cc for cc in list(self.dataset.data_vars)]
    
    def plot(self):
        """
        
        plot the time series probably slow for large data sets
        
        :return: DESCRIPTION
        :rtype: TYPE

        """

        n_channels = len(self.channels)
        
        fig = plt.figure()
        fig.subplots_adjust(hspace=0)
        ax1 = fig.add_subplot(n_channels, 1, 1)
        self.dataset[self.channels[0]].plot()
        ax_list = [ax1]
        for ii, comp in enumerate(self.channels[1:], 2):
            ax = plt.subplot(n_channels, 1, ii, sharex=ax1)
            self.dataset[comp].plot()
            ax_list.append(ax)
            
        for ax in ax_list:
            ax.grid(which='major', color=(.65, .65, .65), ls='--', lw=.75)
            ax.grid(which='minor', color=(.85, .85, .85), ls='--', lw=.5)
            ax.set_axisbelow(True)