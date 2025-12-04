/*
classify_cells - classify complex phenotypes with QuPath
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
Date:       2025-12-03
DOI:        10.5281/zenodo.17298096
URL:        https://github.com/rickert-lab/tools
Version:    0.1

Hint:
Load and execute this script with QuPath's script editor window using
the "Run" (current image) or the "Run for project" (all images) command.
Add this script to your "User scripts" directory to make it available
for all projects opened in your current QuPath installation.
*/

/*
Setting up variables and functions for the script: nothing to do here!
*/

// set variables used for classification
def unclassifiedClassName = 'Unclassified'  // create manually and set white
def waitTime = 1000  // increase value [ms] if screen redraw is too slow

// select cells by class (classification) names
def selectCellsByClassNames(classNames) {
    def cells = getCellObjects().findAll {
        classNames.contains(it.getPathClass()?.toString())
    }
    selectObjects(cells)
    print('Selected ' + cells.size() + ' cells from classes: ' + classNames + '.')
}

// get cells that are currently not selected (inverted selection)
def getCellsNotSelected() {
    def selectedCells = getSelectedObjects().findAll { it.isCell() }
    def cellsNotSelected = getCellObjects().findAll { !selectedCells.contains(it) }
    return cellsNotSelected
}

// set selected cells to a specific class (classification) name
def setSelectedCellsToClass(className) {
    getSelectedObjects().each {
        it.setPathClass(getPathClass(className))
    }
    fireHierarchyUpdate()
}

/*
Phenotyping begins here: iterate through cell types sequentially.

This approach works like a phenotyping sieve, where classified cells
don't make it into the consecutive rounds of phenotyping:
1. Start with well-defined and/or rare phenotypes:
   the marker expressions must be robust and exclusive.
2. Follow up with single-marker phenotypes:
   the marker expression should be robust, but can be challenging.
3. Finally add background phenotypes:
   the marker expression can be abundant and might overlap.
*/

// begin: set all cells to the unclassified class
selectCells()
setSelectedCellsToClass(unclassifiedClassName)
def classifiedCells = null  // empty array to store cells

// first step: classify for phenotype combination 1 (chan1+: chan2-)
selectCellsByClassNames([unclassifiedClassName])
runObjectClassifier('pheno_combo1')  // classify all cells

// all other steps: classify for phenotype 2 (chan3+)
selectCellsByClassNames(['Unclassified',     // e.g. left over from previous step
                         'chan1+: chan2+',   // e.g. conflicting combination
                         'chan1-: chan2+',   // e.g. excluded combination
                         'chan1-: chan2-'])  // e.g. unremarkable combination
classifiedCells = getCellsNotSelected()  // remember classified cells
removeObjects(classifiedCells)  // temporarily remove classified cells
runObjectClassifier('pheno_single2')  // classify unclassified cells
addObjects(classifiedCells)  // add classified cells back

/*  copy template (lines enclosed by block comment markers)
selectCellsByClassNames(['Unclassified', 'Negative marker', 'Excluded marker'])
classifiedCells = getCellsNotSelected()
removeObjects(classifiedCells)
runObjectClassifier('phenoN')
addObjects(classifiedCells)
*/

// end: set remaining unwanted classes to unclassified
selectCellsByClassNames(['chan3-'])
setSelectedCellsToClass(unclassifiedClassName)

/*
Cleaning up hierarchy and selection after phenotyping.
*/

// make sure all cells are located in their parent annotations
// may throw a `java.util.ConcurrentModificationException' if
// the hierarchy is changed before the screen redraw completed
Thread.sleep(waitTime)
resolveHierarchy()

// clear selection to show cell classification colors
resetSelection()
