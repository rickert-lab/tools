"""
concat_fcs - concatenate flow cytometry files
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
import fnmatch
import math
import os
import sys
import warnings

import flowio as fio
import numpy as np

from datetime import datetime

# check if tests are running
pytest_running = "PYTEST_CURRENT_TEST" in os.environ

# get flow file paths
flow_path = (
    os.path.abspath(r"./") if not pytest_running else os.path.abspath(r"./tests/")
)
time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
concat_path = os.path.join(
    flow_path if not pytest_running else r"./tests",
    f"{os.path.basename(flow_path)}{'_' + time_stamp + '_' if not pytest_running else '_'}concat.fcs",
)


def cons_idxs(flow_chans, consens_chans):
    """Return the indices of all flow channels matchting the consensus channels by index and name.

    Keyword arguments:
    flow_chans -- FlowIO channel dictionary
    consens_chans -- consensus channel dictionary
    """
    return sorted(
        [
            int(pos) - 1
            for pos, chan in flow_chans.items()
            if int(pos) in consens_chans and get_name(chan) == consens_chans[int(pos)]
        ]
    )


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
    return channel.get("PnS", channel["PnN"])


def min_warning(message, category, filename, lineno, line=None):
    return f"\n{category.__name__}: {message}\n"


# set warning parameters
warnings.formatwarning = min_warning  # category and message
warnings.simplefilter("always", UserWarning)  # do repeat


# collect channels from flow data
flow_paths = sorted(
    get_files(path=os.path.abspath(flow_path), pat="*.fcs", anti="*_concat.fcs")
)
flow_paths_len = len(flow_paths)
if flow_paths_len:
    print("Checking channels:")
    consens_chans = {}
    for count, flow_path in enumerate(flow_paths):
        # print progress
        if not (count + 1) % 100 or count == 0 or (count + 1) == flow_paths_len:
            print(f"{count + 1}", end="", flush=True)
        else:
            print(".", end="", flush=True)

        # read flow data headers
        flow_data = fio.FlowData(flow_path, only_text=True)
        flow_chans = flow_data.channels

        # track consensus channels
        consens_chans.update(  # pos: {'N', 'PnN', 'PnS'}
            dict(
                sorted(
                    {
                        int(pos): {"N": 0, **chan}
                        for pos, chan in flow_chans.items()
                        if get_name(chan)
                        not in [get_name(cons) for cons in consens_chans.values()]
                    }.items()
                )
            )
        )
        # check names at positions
        for pos, chan in flow_chans.items():
            pos = int(pos)
            if pos in consens_chans and get_name(consens_chans[pos]) == get_name(chan):
                consens_chans[pos]["N"] += 1  # matching label at same position
            else:
                warnings.warn(
                    f'"{os.path.basename(flow_path)}" @{pos} = "{chan["PnN"]}"\n'
                    f'"{get_name(consens_chans[pos])}" (consensus) => "{get_name(chan)}" (non-consensus)'
                )

    # remove non-consensus channels
    nonsens_chans = {  # pos: 'PnS'|'PnN'
        pos: chan.get("PnS", chan["PnN"])
        for pos, chan in consens_chans.items()
        if chan["N"] < flow_paths_len
    }
    print(f"\nRemoving channels:\n{nonsens_chans}")
    consens_chans = {  # pos: 'PnS'|'PnN'
        pos: chan.get("PnS", chan["PnN"])
        for pos, chan in consens_chans.items()
        if get_name(chan) not in nonsens_chans.values()
    }
    print(f"\nKeeping channels:\n{consens_chans}")
    consens_count = len(consens_chans)

    # confirm processing
    if nonsens_chans:
        response = (
            "y"
            if pytest_running
            else input("\nPlease confirm concatenation [Y/n]: ").strip().lower()
        )
        if response and response != "y":
            sys.exit(0)  # quit without error

    # process flow data
    print("\nConcatenating events:")
    concat_events = None  # array.array
    for count, flow_path in enumerate(flow_paths):
        # read flow data
        flow_data = fio.FlowData(flow_path)
        print(
            f'{count + 1:>{len(str(flow_paths_len))}}/{flow_paths_len}: "{flow_data.name}"'
        )
        flow_chans = flow_data.channels
        flow_events = flow_data.events  # 1-D array.array of type 'f'

        # limit flow events to consensus channels (by order and count)
        if not consens_chans == flow_chans:
            # reshape to 2-D NumPy array of original type
            flow_events = np.reshape(
                np.asarray(flow_data.events, dtype=np.dtype(flow_data.events.typecode)),
                (flow_data.event_count, flow_data.channel_count),
            )
            assert np.array_equal(
                flow_data.events[: flow_data.channel_count], flow_events[0]
            ), "First cell differs after transformation."
            assert np.array_equal(
                flow_data.events[-flow_data.channel_count :], flow_events[-1]
            ), "Last cell differs after transformation."

            # remove non-consensus channels from 2-D NumPy array
            flow_idxs = cons_idxs(flow_chans, consens_chans)
            flow_events = flow_events[:, flow_idxs]  # matching labels at same positions
            assert consens_chans == dict(
                sorted(
                    {
                        int(pos): chan.get("PnS", chan["PnN"])
                        for pos, chan in flow_chans.items()
                        if int(pos) - 1 in flow_idxs
                    }.items()
                )
            ), "Channels do not match consensus."

            # flatten to 1-D array.array of type 'f'
            flow_events = array.array("f", flow_events.reshape(-1))
            assert (
                flow_data.event_count * flow_data.channel_count
                - flow_data.event_count * (flow_data.channel_count - consens_count)
                == len(flow_events)
            ), "Cells missing after transformation."

        # concatenate events
        if not concat_events:
            concat_events = array.array(flow_data.events.typecode)  # empty
        concat_events[len(concat_events) :] = flow_events  # .extend(flow_events)

    event_count = len(concat_events) / consens_count
    print(f"{event_count:,} events in {consens_count:,} channels\n")

    # write concatenated flow data
    print("Writing events:")
    with open(
        os.path.abspath(concat_path),
        "wb",
    ) as concat_file:
        fio.create_fcs(
            concat_file,
            event_data=concat_events,  # cast to array.array('f,) in flowio
            channel_names=[chan for chan in consens_chans.values()],
        )

    # check concatenated flow data
    concat_data = fio.FlowData(os.path.abspath(concat_path), only_text=True)
    print(
        f'"{concat_data.name}"\n'
        f"{math.ceil(concat_data.file_size):,} B on disk\n"
        f"{concat_data.event_count:,} events in {concat_data.channel_count:,} channels\n"
    )
    assert event_count == concat_data.event_count, "Event count differs after writing."
    assert consens_count == concat_data.channel_count, (
        "Channel count differs after writing."
    )
    assert concat_data.file_size > 0, "Concatenated file does not contain any data."
else:
    print("No files found.")
