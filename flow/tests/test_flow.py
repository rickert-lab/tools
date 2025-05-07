"""
test_flow - tests for flow repository
Copyright (C) 2025 The Regents of the University of Colorado

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

Author:     Christian Rickert <christian.rickert@cuanschutz.edu>
Date:       2025-05-07
Version:    0.1
"""

import array
import json
import os
import subprocess
import pytest

import flowio as fio
import pandas as pd


def fail():
    raise SystemExit(1)


class TestCreateFCS:
    def test_fail(self):
        with pytest.raises(SystemExit):
            fail()

    def test_create_csv(self):
        subprocess.run(["python", os.path.abspath("./tests/create_csv.py")], check=True)
        # check output file
        csv_path = os.path.abspath("./tests/test.csv")
        assert os.path.exists(csv_path)
        # read csv data
        csv_frame = pd.read_csv(
            csv_path,
            sep=r",",
            header="infer",
            engine="pyarrow",  # multithreading
            skip_blank_lines=True,
        )
        head_expected = pd.DataFrame(
            {
                "index": [0, 1, 2, 3, 4],
                "tissue": ["stroma", "tumor", "stroma", "stroma", "stroma"],
                "area": [96.958463, 77.513282, 93.949894, 89.482735, 59.789998],
                "mean": [9.082659, 2.395619, 1.448949, 4.894528, 9.856505],
            }
        )
        pd.testing.assert_frame_equal(csv_frame.head(), head_expected)
        # cleanup
        os.remove(os.path.abspath("./tests/test.csv"))

    def test_create_fcs(self):
        subprocess.run(["python", os.path.abspath("./tests/create_fcs.py")], check=True)
        # check output files
        for file in range(3):
            flow_path = os.path.abspath(
                os.path.join("./tests/test_" + str(file + 1) + ".fcs")
            )
            assert os.path.exists(flow_path)
            # read flow data headers
            flow_data = fio.FlowData(flow_path)
            assert flow_data.event_count == 100, "Cell count is not 100."
            flow_chans = [chan["PnN"] for chan in flow_data.channels.values()]
            match file:
                case 0:
                    assert flow_chans == [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_D",
                    ]
                case 1:
                    assert flow_chans == [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_D",
                        "Chan_E",  # extra
                    ]
                case 2:
                    assert flow_chans == [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_C",  # wrong
                        "Chan_E",  # extra
                    ]
                case _:
                    assert False
            # cleanup
            os.remove(
                os.path.abspath(os.path.join("./tests/test_" + str(file + 1) + ".fcs"))
            )

    def test_csv_to_fcs(self):
        # create temp file
        subprocess.run(["python", os.path.abspath("./tests/create_csv.py")], check=True)
        # run conversion
        subprocess.run(
            ["python", os.path.abspath("csv_to_fcs.py")],
            check=True,
        )
        # check csv output
        csv_path = os.path.abspath("./tests/test_annots.csv")
        assert os.path.exists(csv_path)
        csv_frame = pd.read_csv(
            csv_path,
            sep=r",",
            header="infer",
            engine="pyarrow",  # multithreading
            skip_blank_lines=True,
        )
        head_expected = pd.DataFrame(
            {
                "index": [0, 1, 2, 3, 4],
                "tissue": ["stroma", "tumor", "stroma", "stroma", "stroma"],
                "area": [96.958463, 77.513282, 93.949894, 89.482735, 59.789998],
                "mean": [9.082659, 2.395619, 1.448949, 4.894528, 9.856505],
            }
        )
        pd.testing.assert_frame_equal(csv_frame.head(), head_expected)
        # check json output
        json_path = os.path.abspath("./tests/test_annots.json")
        assert os.path.exists(json_path)
        expected_json = {"tissue": {"stroma": 0, "tumor": 1}}
        with open(json_path, "r") as json_file:
            result_json = json.load(json_file)
        assert result_json == expected_json
        # check fcs output
        fcs_path = os.path.abspath(os.path.join("./tests/test_annots.fcs"))
        assert os.path.exists(fcs_path)
        fcs_data = fio.FlowData(fcs_path)
        expected_chans = ["index", "tissue", "area", "mean"]
        assert [chan["PnN"] for chan in fcs_data.channels.values()] == expected_chans
        expected_events = array.array(
            "f",
            [
                0.0,
                0.0,
                96.95846557617188,
                9.082658767700195,
                1.0,
                1.0,
                77.5132827758789,
                2.3956189155578613,
                2.0,
                0.0,
                93.94989776611328,
                1.4489487409591675,
                3.0,
                0.0,
                89.48273468017578,
                4.894527435302734,
                4.0,
                0.0,
                59.78999710083008,
                9.856504440307617,
            ],
        )
        assert fcs_data.events[:20] == expected_events
        assert fcs_data.event_count == 100, "Cell count is not 100."
        os.remove(os.path.abspath("./tests/test.csv"))
        os.remove(os.path.abspath("./tests/test_annots.csv"))
        os.remove(os.path.abspath("./tests/test_annots.json"))
        os.remove(os.path.abspath("./tests/test_annots.fcs"))

    def test_concat_fcs(self):
        # create temp files
        subprocess.run(["python", os.path.abspath("./tests/create_fcs.py")], check=True)
        # run concatenation
        concat_fcs_result = subprocess.run(
            ["python", os.path.abspath("concat_fcs.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # check output file
        concat_path = os.path.abspath("./tests/tests_concat.fcs")
        assert os.path.exists(concat_path)
        # check terminal output
        with open(
            os.path.abspath("./tests/test_concat_fcs.txt"), "r", encoding="utf-8"
        ) as lf:
            concat_fcs_expected = lf.read()
        assert concat_fcs_result.stdout == concat_fcs_expected
        for file in range(3):
            os.remove(
                os.path.abspath(os.path.join("./tests/test_" + str(file + 1) + ".fcs"))
            )  # flow_path
        os.remove(os.path.abspath("./tests/tests_concat.fcs"))
