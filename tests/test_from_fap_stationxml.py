# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 17:58:47 2021

:copyright: 
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""

import unittest
from pathlib import Path
from mth5 import mth5

from mt_metadata.timeseries.stationxml import XMLInventoryMTExperiment
from mt_metadata.utils import STATIONXML_FAP

fn_path = Path(__file__).parent

class TestFAPMTH5(unittest.TestCase):
    """
    Test making an MTH5 file from a FAP filtered StationXML
    
    """
    
    def setUp(self):
        self.translator = XMLInventoryMTExperiment()
        self.experiment = self.translator.xml_to_mt(stationxml_fn=STATIONXML_FAP)
        
        self.fn = fn_path.joinpath("from_fap_stationxml.h5")
        if self.fn.exists():
            self.fn.unlink()

        self.m = mth5.MTH5()
        self.m.open_mth5(self.fn)
        self.m.from_experiment(self.experiment, 0)
        
    def test_groups(self):
        self.assertEqual(self.m.has_group("Survey"), True)
        self.assertEqual(self.m.has_group("Survey/Stations"), True)
        self.assertEqual(self.m.has_group("Survey/Stations/FL001"), True)
        self.assertEqual(self.m.has_group("Survey/Stations/FL001/a"), True)
        self.assertEqual(self.m.has_group("Survey/Stations/FL001/b"), True)
        self.assertEqual(self.m.has_group("Survey/Stations/FL001/a/hx"), True)
        self.assertEqual(self.m.has_group("Survey/Stations/FL001/b/hx"), True)
        
    def test_get_run(self):
        self.hx = self.m.get_channel("FL001", "a", "hx")
        def test_filters(self):
            s
            
        
