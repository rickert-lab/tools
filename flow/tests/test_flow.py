"""
`test_flow` - tests for flow repository
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
Date:       2025-03-14
Version:    0.1
"""

import os
import subprocess
import pytest

import flowio as fio


def fail():
    raise SystemExit(1)


class TestCreateFCS:
    def test_fail(self):
        with pytest.raises(SystemExit):
            fail()

    def test_create_fcs(self):
        subprocess.run(["python", os.path.abspath("create_fcs.py")], check=True)
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

    def test_concat_fcs(self):
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

    def test_cleanup(self):
        for file in range(3):
            os.remove(
                os.path.abspath(os.path.join("./tests/test_" + str(file + 1) + ".fcs"))
            )  # flow_path
        os.remove(os.path.abspath("./tests/tests_concat.fcs"))  # concat_path
