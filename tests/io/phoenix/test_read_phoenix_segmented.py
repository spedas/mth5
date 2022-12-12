# -*- coding: utf-8 -*-
"""
Created on Fri Aug 19 16:39:30 2022

@author: jpeacock
"""

# =============================================================================
# Imports
# =============================================================================
import unittest
from pathlib import Path
from collections import OrderedDict

import numpy as np
from mth5.io.phoenix import open_phoenix

# =============================================================================


@unittest.skipIf(
    "peacock" not in str(Path(__file__).as_posix()),
    "Only local files, cannot test in GitActions",
)
class TestReadPhoenixContinuous(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.phx_obj = open_phoenix(
            r"c:\Users\jpeacock\OneDrive - DOI\mt\phoenix_example_data\Sample Data\10128_2021-04-27-032436\0\10128_608783F4_0_00000001.td_24k"
        )

        self.segment = self.phx_obj.read_segment()
        self.maxDiff = None

    def test_subheader(self):
        true_dict = {
            "channel_id": 0,
            "channel_type": "H",
            "elevation": 140.10263061523438,
            "gps_time_stamp": "2021-04-27T03:25:00+00:00",
            "header_length": 32,
            "instrument_serial_number": "10128",
            "instrument_type": "MTU-5C",
            "latitude": 43.69625473022461,
            "longitude": -79.39364624023438,
            "missing_count": 0,
            "n_samples": 48000,
            "sample_rate": 24000.0,
            "saturation_count": 0,
            "segment": 0,
            "segment_end_time": "2021-04-27T03:25:02+00:00",
            "segment_start_time": "2021-04-27T03:25:00+00:00",
            "value_max": 0.24964138865470886,
            "value_mean": -1.3566585039370693e-05,
            "value_min": 3.4028234663852886e38,
        }

        for key, original_value in true_dict.items():
            new_value = getattr(self.segment, key)
            with self.subTest("key"):
                if isinstance(original_value, (list)):
                    self.assertListEqual(original_value, new_value)
                elif isinstance(original_value, float):
                    self.assertAlmostEqual(original_value, new_value)
                else:
                    self.assertEqual(original_value, new_value)

    def test_attributes(self):
        true_dict = {
            "ad_plus_minus_range": 5.0,
            "attenuator_gain": 1.0,
            "base_dir": Path(
                "c:/Users/jpeacock/OneDrive - DOI/mt/phoenix_example_data/Sample Data/10128_2021-04-27-032436/0"
            ),
            "base_path": Path(
                "c:/Users/jpeacock/OneDrive - DOI/mt/phoenix_example_data/Sample Data/10128_2021-04-27-032436/0/10128_608783F4_0_00000001.td_24k"
            ),
            "battery_voltage_v": 12.475,
            "board_model_main": "BCM01",
            "board_model_revision": "",
            "bytes_per_sample": 4,
            "ch_board_model": "BCM01-I",
            "ch_board_serial": 200803,
            "ch_firmware": 65567,
            "channel_id": 0,
            "channel_main_gain": 4.0,
            "channel_map": {
                0: "hx",
                1: "hy",
                2: "hz",
                3: "ex",
                4: "ey",
                5: "h1",
                6: "h2",
                7: "h3",
            },
            "channel_type": "H",
            "data_footer": 0,
            "decimation_node_id": 0,
            "detected_channel_type": "H",
            "file_extension": ".td_24k",
            "file_name": "10128_608783F4_0_00000001.td_24k",
            "file_sequence": 1,
            "file_size": 2304512,
            "file_type": 2,
            "file_version": 2,
            "frag_period": 360,
            "frame_rollover_count": 0,
            "frame_size": 64,
            "frame_size_bytes": 64,
            "future1": 32,
            "future2": 0,
            "gps_elevation": 140.10263061523438,
            "gps_horizontal_accuracy": 17.512,
            "gps_lat": 43.69625473022461,
            "gps_long": -79.39364624023438,
            "gps_vertical_accuracy": 22.404,
            "hardware_configuration": (4, 3, 0, 0, 0, 9, 128, 0),
            "header_length": 128,
            "instrument_id": "10128",
            "instrument_serial_number": "10128",
            "instrument_type": "MTU-5C",
            "intrinsic_circuitry_gain": 1.0,
            "last_seq": 2,
            "lp_frequency": 10000,
            "max_samples": 576096,
            "max_signal": 2.0711588859558105,
            "min_signal": -2.0549893379211426,
            "missing_frames": 0,
            "preamp_gain": 1.0,
            "recording_id": 1619493876,
            "recording_start_time": "2021-04-26T20:24:36+00:00",
            "report_hw_sat": False,
            "sample_rate": 24000,
            "sample_rate_base": 24000,
            "sample_rate_exp": 0,
            "saturated_frames": 0,
            "seq": 1,
            "sequence_list": [
                Path(
                    "c:/Users/jpeacock/OneDrive - DOI/mt/phoenix_example_data/Sample Data/10128_2021-04-27-032436/0/10128_608783F4_0_00000001.td_24k"
                ),
                Path(
                    "c:/Users/jpeacock/OneDrive - DOI/mt/phoenix_example_data/Sample Data/10128_2021-04-27-032436/0/10128_608783F4_0_00000002.td_24k"
                ),
            ],
            "timing_flags": 55,
            "timing_sat_count": 7,
            "timing_stability": 201,
            "timing_status": (55, 7, 201),
            "total_circuitry_gain": 4.0,
            "total_selectable_gain": 4.0,
        }

        for key, original_value in true_dict.items():
            new_value = getattr(self.phx_obj, key)
            with self.subTest("key"):
                if isinstance(original_value, (list)):
                    self.assertListEqual(original_value, new_value)
                elif isinstance(original_value, float):
                    self.assertAlmostEqual(original_value, new_value)
                else:
                    self.assertEqual(original_value, new_value)

    def test_to_channel_ts(self):
        ch_ts = self.phx_obj.to_channel_ts()

        with self.subTest("Channel metadata"):
            ch_metadata = OrderedDict(
                [
                    ("channel_number", 0),
                    ("component", "hx"),
                    ("data_quality.rating.value", 0),
                    ("filter.applied", [False]),
                    ("filter.name", []),
                    ("location.elevation", 0.0),
                    ("location.latitude", 0.0),
                    ("location.longitude", 0.0),
                    ("measurement_azimuth", 0.0),
                    ("measurement_tilt", 0.0),
                    ("sample_rate", 24000.0),
                    ("sensor.id", None),
                    ("sensor.manufacturer", None),
                    ("sensor.type", None),
                    ("time_period.end", "2021-04-27T03:25:31.999958+00:00"),
                    ("time_period.start", "2021-04-27T03:25:30+00:00"),
                    ("type", "magnetic"),
                    ("units", None),
                ]
            )

            self.assertDictEqual(
                ch_ts.channel_metadata.to_dict(single=True), ch_metadata
            )

        with self.subTest("Channel Size"):
            self.assertEqual(48000, ch_ts.ts.size)
