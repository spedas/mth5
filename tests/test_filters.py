# -*- coding: utf-8 -*-
"""
Created on Tue May 11 10:35:30 2021

:copyright: 
    Jared Peacock (jpeacock@usgs.gov)

:license: MIT

"""
# =============================================================================
# Imports
# =============================================================================
import unittest
from pathlib import Path
import numpy as np

from mth5 import mth5
from mt_metadata.timeseries.filters import PoleZeroFilter

fn_path = Path(__file__).parent
# =============================================================================
mth5.helpers.close_open_files()

class TestFilters(unittest.TestCase):
    """
    Test filters to make sure get out what is put in
    """
    
    def setUp(self):
        self.fn = fn_path.joinpath("filter_test.h5")
        self.m_obj = mth5.MTH5()
        self.m_obj.open_mth5(self.fn, "w")
        self.filter_group = self.m_obj.filters_group
        
        self.zpk = PoleZeroFilter()
        self.zpk.units_in = "counts"
        self.zpk.units_out = "mv"
        self.zpk.name = "ftest"
        self.zpk.poles = np.array([1 + 2j, 0, 1 - 2j])
        self.zpk.zeros = np.array([10 - 1j, 10 + 1j])
        
        self.zpk_group = self.filter_group.add_filter(self.zpk)
        
    def test_zpk_in(self):
        
        self.assertIn("ftest", self.filter_group.zpk_group.groups_list)
        
    def test_zpk_name(self):
        self.assertEqual(self.zpk_group.attrs["name"], self.zpk.name)
        
    def test_zpk_units_in(self):
        self.assertEqual(self.zpk_group.attrs["units_in"], self.zpk.units_in)
        
    def test_zpk_units_out(self):
        self.assertEqual(self.zpk_group.attrs["units_out"], self.zpk.units_out)
        
    def test_zpk_poles(self):
        self.assertTrue(np.allclose(self.zpk_group["poles"]["real"][()],
                                    self.zpk.poles.real))
        self.assertTrue(np.allclose(self.zpk_group["poles"]["imag"][()],
                                    self.zpk.poles.imag))
        
    def test_zpk_zeros(self):
        self.assertTrue(np.allclose(self.zpk_group["zeros"]["real"][()],
                                    self.zpk.zeros.real))
        self.assertTrue(np.allclose(self.zpk_group["zeros"]["imag"][()],
                                    self.zpk.zeros.imag))
        
    def test_zpk_out(self):
        new_zpk = self.filter_group.to_filter_object(self.zpk.name)
        
        self.assertTrue(new_zpk == self.zpk)
        

    def tearDown(self):
        self.m_obj.close_mth5()
        self.fn.unlink()
