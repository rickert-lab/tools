"""
csv_to_fcs - convert comma-separated value to flow cytometry files
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

import json
import fnmatch
import os

import flowio as fio
import pandas as pd

# check if tests are running
pytest_running = "PYTEST_CURRENT_TEST" in os.environ

# get csv file paths
csv_path = (
    os.path.abspath(r"./") if not pytest_running else os.path.abspath(r"./tests/")
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


# collect csv file names
csv_paths = sorted(
    get_files(path=os.path.abspath(csv_path), pat="*.csv", anti="*_annots.csv")
)
csv_paths_len = len(csv_paths)


print("\nConverting files:")
for count, csv_path in enumerate(csv_paths):
    print(
        f'{count + 1:>{len(str(csv_paths_len))}}/{csv_paths_len}: "{os.path.basename(csv_path)}"'
    )

    # read csv data
    csv_frame = pd.read_csv(
        csv_path,
        sep=r",",
        header="infer",
        engine="pyarrow",  # multithreading
        skip_blank_lines=True,
    )

    # write annotated csv file
    if pytest_running:
        with open(
            os.path.join(
                os.path.dirname(csv_path),
                os.path.splitext(os.path.basename(csv_path))[0] + "_annots.csv",
            ),
            "w",
        ) as csv_file:
            csv_frame.to_csv(
                csv_file, header=True, index=False
            )  # keep header, ignore Pandas' index

    # find non-numeric columns
    nonum_cols = [
        col
        for col in csv_frame.columns
        if not pd.api.types.is_numeric_dtype(csv_frame[col])  # use numeric annotations
    ]

    # convert non-numeric to categorical columns
    for nonum_col in nonum_cols:
        csv_frame[nonum_col] = csv_frame[nonum_col].astype("category")

    # write annotation JSON file
    annots = {}
    for nonum_col in nonum_cols:
        nonum_col_cats = csv_frame[nonum_col].cat.categories  # unique only
        csv_frame[nonum_col] = csv_frame[nonum_col].cat.codes  # replace all
        annots[nonum_col] = pd.Series(
            range(len(nonum_col_cats)), index=nonum_col_cats
        ).to_dict()  # preserve category order
    with open(
        os.path.join(
            os.path.dirname(csv_path),
            os.path.splitext(os.path.basename(csv_path))[0] + "_annots.json",
        ),
        "w",
    ) as annot_file:
        json.dump(annots, annot_file, indent=2)

    # write fcs file
    with open(
        os.path.join(
            os.path.dirname(csv_path),
            os.path.splitext(os.path.basename(csv_path))[0] + "_annots.fcs",
        ),
        "wb",
    ) as fcs_file:
        fio.create_fcs(
            fcs_file,
            event_data=csv_frame.to_numpy(
                dtype="float64"
            ).ravel(),  # cast to array.array('f,) in flowio
            channel_names=[col for col in csv_frame.columns],
        )
