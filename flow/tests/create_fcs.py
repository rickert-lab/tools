"""
create_fcs - create flow cytometry files for testing
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
DOI:        10.5281/zenodo.17298096
URL:        https://github.com/rickert-lab/tools
Version:    0.1
"""

import array
import os

import flowio as fio
import numpy as np

# set fixed random seed
np.random.seed(42)

# set parameters
cells = 100
channels = ["Chan_A", "Chan_B", "Chan_C", "Chan_D"]
files = 3
flow_path = r"./tests"

# write data
for i in range(files):
    cells_chans = np.asarray(
        np.random.rand(cells, len(channels)), dtype=np.float64
    )  # shape: (cells, channels)
    match i:
        case 1:
            channels.append("Chan_E")  # additional channel at last position, add column
            cells_chans = np.concatenate(
                (cells_chans, np.random.rand(cells_chans.shape[0], 1)), axis=1
            )
        case 2:
            channels[3] = "Chan_C"  # channel in wrong position, don't add column
        case _:
            pass
    flow_data = array.array("f", cells_chans.reshape(-1))  # flatten
    with open(
        os.path.abspath(os.path.join(flow_path, "test_" + str(i + 1) + ".fcs")),
        "wb",
    ) as data_file:
        fio.create_fcs(
            data_file,
            event_data=flow_data,
            channel_names=channels,
        )
