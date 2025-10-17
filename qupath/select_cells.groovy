/*
select_cells - select cells using different criteria
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
Date:       2025-10-17
DOI:        10.5281/zenodo.17298096
URL:        https://github.com/rickert-lab/tools
Version:    0.1

Hint:
Load this script with QuPath's script editor and select the sections to execute and
run the highlighted code with "Run selected code". Selected cells will always show,
even if you have hidden all detections (toggle with key 'D', fill with key 'F').
Add this script to your "User scripts" directory to make it available
for all projects opened in your current QuPath installation.
*/

// select cells by parent (annotation) names
def selectCellsByParentNames(parentNames) {
    def cells = getCellObjects().findAll {
        def parent = it.getParent()
        def parentStr = parent?.toString()
        parentNames.any { parentStr?.startsWith(it) }
    }
    selectObjects(cells)
    print('Selected ' + cells.size() + ' cells from parents: ' + parentNames + '.')
}
resetSelection()
selectCellsByParentNames(['Annotation (Tumor)'])  // Tumor cells

// select cells by class (classification) names
def selectCellsByClassNames(classNames) {
    def cells = getCellObjects().findAll {
        classNames.contains(it.getPathClass()?.toString())
    }
    selectObjects(cells)
    print('Selected ' + cells.size() + ' cells from classes: ' + classNames + '.')
}
resetSelection()
selectCellsByClassNames(['CD3+: CD4+', 'CD3+: CD8+'])  // T cells

// select cells by their names
def selectCellsByNames(names) {
    def cells = getCellObjects().findAll {
        names.contains(it.getName())
    }
    selectObjects(cells)
    print('Selected ' + cells.size() + ' cells with names: ' + names + '.')
}
resetSelection()
selectCellsByNames(['Cluster 1', 'Cluster 2', 'Cluster 3'])  // clustered cells

// select cells by their area range
def selectCellsByAreaRange(areaRange) {
    def cells = getCellObjects()
    if (cells.isEmpty()) {
        print('No cells found.')
        return
    }
    def measurementName = cells.first().getMeasurementList().getMeasurementNames().find { it.startsWith('Cell: Area') }
    def unit = measurementName?.replaceFirst('Cell: Area ', '') ?: 'µm^2'
    def minArea = areaRange[0]
    def maxArea = areaRange.size() > 1 ? areaRange[1] : cells.collect { measurement(it, measurementName) }.max()
    def selectedCells = cells.findAll {
        def area = measurement(it, measurementName)
        area >= minArea && area <= maxArea
    }
    selectObjects(selectedCells)
    print('Selected ' + selectedCells.size() + ' cells with area between ' +
           minArea + ' and ' + String.format('%.1f', maxArea) + ' ' + unit + '.')
}
resetSelection()
selectCellsByAreaRange([0])  // all cells (no lower or upper limit)
