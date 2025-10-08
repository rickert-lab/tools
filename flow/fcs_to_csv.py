"""
fcs_to_csv - convert flow cytometry to comma-separated value files
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

import os
import fnmatch

import flowio as fio
import numpy as np


def get_files(path="", pat="*", anti="", recurse=False):
    """Iterate through all files in a directory structure and
       return a list of matching files.

    Keyword arguments:
    path -- the path to a directory containing files (default "")
    pat -- string pattern that needs to be part of the file name (default "None")
    anti -- string pattern that may not be part of the file name (default "None")
    recurse -- boolen that allows the function to work recursively (default "False")
    """
    file_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            file = os.path.join(root, file)
            if fnmatch.fnmatch(file, pat) and not fnmatch.fnmatch(file, anti):
                file_list.append(file)
        if not recurse:
            break  # from `os.walk()`
    return file_list


def get_name(channel):
    """Get channel label from flowio channel dictionary.
    Try to retrieve the optional long name first and
    if that fails try to get the short name.

    Keyword arguments:
    channels - the flowio channel dictionary
    """
    return (
        channel.get("pns") or channel["pnn"]
    )  # 'pns' value must be True, i.e. it must differ from "", None, False


# check if tests are running
pytest_running = "PYTEST_CURRENT_TEST" in os.environ

# get fcs file paths
fcs_path = (
    os.path.abspath(r"./") if not pytest_running else os.path.abspath(r"./tests/")
)

# collect fcs file names
fcs_paths = sorted(get_files(path=os.path.abspath(fcs_path), pat="*.fcs", anti=""))
fcs_paths_len = len(fcs_paths)

print("\nConverting files:")
for count, fcs_path in enumerate(fcs_paths):
    print(
        f'{count + 1:>{len(str(fcs_paths_len))}}/{fcs_paths_len}: "{os.path.basename(fcs_path)}"'
    )

    # read fcs data
    fcs_data = fio.FlowData(fcs_path)
    fcs_chans = [get_name(chan) for chan in fcs_data.channels.values()]

    # reshape fcs data
    fcs_events = np.reshape(
        np.asarray(fcs_data.events, dtype=np.dtype(fcs_data.events.typecode)),
        (fcs_data.event_count, fcs_data.channel_count),
    )

    # write csv data
    with open(
        os.path.join(
            os.path.dirname(fcs_path),
            os.path.splitext(os.path.basename(fcs_path))[0] + ".csv",
        ),
        "w",
    ) as csv_file:
        np.savetxt(
            csv_file, fcs_events, delimiter=",", header=",".join(fcs_chans), comments=""
        )
