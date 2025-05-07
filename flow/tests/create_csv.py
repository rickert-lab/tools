"""
create_csv - create comma-separated value files for testing
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

import os
import pandas as pd
import numpy as np

# set fixed random seed
np.random.seed(42)

# set parameters
cells = 100
csv_path = r"./tests"

# write data
csv_data = {
    "index": np.arange(cells, dtype=np.int32),
    "tissue": np.random.choice(["stroma", "tumor"], size=cells),
    "area": np.random.rand(cells) * 100,  # random floats between 0 and 1000
    "mean": np.random.rand(cells) * 10,  # random floats between 0 and 10
}
csv_frame = pd.DataFrame(csv_data)
with open(os.path.abspath(os.path.join(csv_path, "test.csv")), "w") as csv_file:
    csv_frame.to_csv(
        csv_file, header=True, index=False
    )  # keep header, ignore Pandas' index
