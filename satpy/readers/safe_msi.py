#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2016-2017 Martin Raspaud

# Author(s):

#   Matias Takala  <matias.takala@fmi.fi>
#   Martin Raspaud <martin.raspaud@smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""SAFE MSI L1C reader.
"""

import logging
# import os
# import xml.etree.ElementTree as ET

import glymur
import numpy as np
# from osgeo import gdal
from xarray import DataArray
from dask.array import from_delayed
from dask import delayed

from satpy import CHUNK_SIZE
# from geotiepoints.geointerpolator import GeoInterpolator
from satpy.readers.file_handlers import BaseFileHandler

logger = logging.getLogger(__name__)


class SAFEMSIL1C(BaseFileHandler):

    def __init__(self, filename, filename_info, filetype_info):
        super(SAFEMSIL1C, self).__init__(filename, filename_info,
                                         filetype_info)

        self._start_time = filename_info['observation_time']
        self._end_time = None
        self._channel = filename_info['band_name']

    def get_dataset(self, key, info):
        """Load a dataset."""
        if self._channel != key.name:
            return

        logger.debug('Reading %s.', key.name)
        QUANTIFICATION_VALUE = 10000.
        jp2 = glymur.Jp2k(self.filename)
        bitdepth = 0
        for seg in jp2.codestream.segment:
            try:
                bitdepth = max(bitdepth, seg.bitdepth[0])
            except AttributeError:
                pass
        jp2.dtype = (np.uint8 if bitdepth <= 8 else np.uint16)
        data = from_delayed(delayed(jp2.read)(), jp2.shape, jp2.dtype)
        data = data.rechunk(CHUNK_SIZE) / QUANTIFICATION_VALUE * 100

        proj = DataArray(data, dims=['y', 'x'])
        proj.attrs = info.copy()
        proj.attrs['units'] = '%'
        return proj

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._start_time
