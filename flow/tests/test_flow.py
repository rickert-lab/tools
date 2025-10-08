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
Date:       2025-10-08
DOI:        10.5281/zenodo.17298096
URL:        https://github.com/rickert-lab/tools
Version:    0.2
"""

import array
import json
import os
import subprocess
import pytest

import flowio as fio
import numpy as np
import pandas as pd


def fail():
    raise SystemExit(1)


class TestCreateFCS:
    def test_fail(self):
        with pytest.raises(SystemExit):
            fail()

    def test_create_csv(self):
        subprocess.run(["python", os.path.abspath("./tests/create_csv.py")], check=True)
        # check output files
        for f in range(3):
            csv_path = os.path.abspath(
                os.path.join("./tests/test_" + str(f + 1) + ".csv")
            )
            assert os.path.exists(csv_path)
            if f == 0:
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
                        "area [μm²]": [
                            96.958463,
                            77.513282,
                            93.949894,
                            89.482735,
                            59.789998,
                        ],
                        "mean": [9.082659, 2.395619, 1.448949, 4.894528, 9.856505],
                    }
                )
                head_result = csv_frame.head()
                pd.testing.assert_frame_equal(head_result, head_expected)
            # cleanup
            os.remove(csv_path)

    def test_create_fcs(self):
        subprocess.run(["python", os.path.abspath("./tests/create_fcs.py")], check=True)
        # check output files
        for f in range(3):
            flow_path = os.path.abspath(
                os.path.join("./tests/test_" + str(f + 1) + ".fcs")
            )
            assert os.path.exists(flow_path)
            # read flow data headers
            flow_data = fio.FlowData(flow_path)
            assert flow_data.event_count == 100, "Cell count is not 100."
            flow_chans_result = [
                chan.get("pns") or chan["pnn"] for chan in flow_data.channels.values()
            ]
            match f:
                case 0:
                    flow_chans_expected = [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_D",
                    ]
                    assert flow_chans_result == flow_chans_expected
                case 1:
                    flow_chans_expected = [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_D",
                        "Chan_E",  # extra
                    ]

                    assert flow_chans_result == flow_chans_expected
                case 2:
                    flow_chans_expected = [
                        "Chan_A",
                        "Chan_B",
                        "Chan_C",
                        "Chan_C",  # wrong
                        "Chan_E",  # extra
                    ]
                    assert flow_chans_result == flow_chans_expected
                case _:
                    assert False
            # cleanup
            os.remove(
                os.path.abspath(os.path.join("./tests/test_" + str(f + 1) + ".fcs"))
            )

    def test_concat_fcs(self):
        # create temp files
        subprocess.run(["python", os.path.abspath("./tests/create_fcs.py")], check=True)
        # run concatenation
        concat_fcs_result = subprocess.run(
            ["python", os.path.abspath("concat_fcs.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ).stdout
        # check output file
        concat_path = os.path.abspath("./tests/tests_concat.fcs")
        assert os.path.exists(concat_path)
        # check terminal output
        with open(
            os.path.abspath("./tests/test_concat_fcs.txt"), "r", encoding="utf-8"
        ) as lf:
            concat_fcs_expected = lf.read()
        assert concat_fcs_result == concat_fcs_expected
        # cleanup
        for f in range(3):
            os.remove(
                os.path.abspath(os.path.join("./tests/test_" + str(f + 1) + ".fcs"))
            )  # flow_path
        os.remove(os.path.abspath("./tests/tests_concat.fcs"))

    def test_csv_to_fcs(self):
        # create temp files
        subprocess.run(["python", os.path.abspath("./tests/create_csv.py")], check=True)
        # run conversion
        subprocess.run(
            ["python", os.path.abspath("csv_to_fcs.py")],
            check=True,
        )
        for f in range(3):
            base_path = "./tests/test_" + str(f + 1)
            # check csv output
            csv_path = os.path.abspath(os.path.join(base_path + ".csv"))
            assert os.path.exists(csv_path)
            if f == 0:
                # check csv content
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
                        "area [μm²]": [
                            96.958463,
                            77.513282,
                            93.949894,
                            89.482735,
                            59.789998,
                        ],
                        "mean": [9.082659, 2.395619, 1.448949, 4.894528, 9.856505],
                    }
                )
                pd.testing.assert_frame_equal(csv_frame.head(), head_expected)
                # check json output
                json_path = os.path.abspath(os.path.join(base_path + "_annots.json"))
                assert os.path.exists(json_path)
                json_expected = {"tissue": {"stroma": 0, "tumor": 1}}
                with open(json_path, "r") as json_file:
                    json_result = json.load(json_file)
                assert json_result == json_expected
                # check fcs output
                fcs_path = os.path.abspath(os.path.join(base_path + "_annots.fcs"))
                assert os.path.exists(fcs_path)
                fcs_data = fio.FlowData(fcs_path)
                chans_result = [
                    chan.get("pns") or chan["pnn"]
                    for chan in fcs_data.channels.values()
                ]
                chans_expected = ["index", "tissue", "area [μm²]", "mean"]
                assert chans_result == chans_expected
                events_expected = array.array(
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
                events_result = fcs_data.events[:20]
                assert events_result == events_expected
                assert fcs_data.event_count == 100, "Cell count is not 100."
            # cleanup
            os.remove(os.path.abspath(base_path + ".csv"))
            os.remove(os.path.abspath(base_path + "_annots.csv"))
            os.remove(os.path.abspath(base_path + "_annots.json"))
            os.remove(os.path.abspath(base_path + "_annots.fcs"))

    def test_fcs_to_csv(self):
        # create temp files
        subprocess.run(["python", os.path.abspath("./tests/create_fcs.py")], check=True)
        # run conversion
        subprocess.run(
            ["python", os.path.abspath("fcs_to_csv.py")],
            check=True,
        )
        for f in range(3):
            base_path = "./tests/test_" + str(f + 1)
            # check csv output
            csv_path = os.path.abspath(os.path.join(base_path + ".csv"))
            assert os.path.exists(csv_path)
            if f == 0:
                # check csv content
                with open(csv_path, "r") as csv_file:
                    channels_expected = ["Chan_A", "Chan_B", "Chan_C", "Chan_D"]
                    channels_result = csv_file.readline().strip().split(",")
                    assert channels_result == channels_expected
                    events_expected = np.array(
                        [
                            [
                                3.745401203632354736e-01,
                                9.507142901420593262e-01,
                                7.319939136505126953e-01,
                                5.986585021018981934e-01,
                            ],
                            [
                                1.560186445713043213e-01,
                                1.559945195913314819e-01,
                                5.808361247181892395e-02,
                                8.661761283874511719e-01,
                            ],
                            [
                                6.011149883270263672e-01,
                                7.080726027488708496e-01,
                                2.058449387550354004e-02,
                                9.699098467826843262e-01,
                            ],
                            [
                                8.324426412582397461e-01,
                                2.123391181230545044e-01,
                                1.818249672651290894e-01,
                                1.834045052528381348e-01,
                            ],
                            [
                                3.042422533035278320e-01,
                                5.247564315795898438e-01,
                                4.319450259208679199e-01,
                                2.912291288375854492e-01,
                            ],
                        ]
                    )
                    events_result = np.loadtxt(csv_file, delimiter=",")
                    assert np.array_equal(events_result[:5, :], events_expected)
            # cleanup
            os.remove(os.path.abspath(base_path + ".fcs"))
            os.remove(os.path.abspath(base_path + ".csv"))
