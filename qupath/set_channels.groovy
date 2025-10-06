/*
set_channels - set channel display ranges and names
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
Date:       2025-10-06
Version:    0.2

Hint:
Load and execute this script with QuPath's script editor window using
the "Run" (current image) or the "Run for project" (all images) command.
Add this script to your "User scripts" directory to make it available
for all projects opened in your current QuPath installation.
*/

// mandatory: set new rannge
BigDecimal minDisplay = 0.0
BigDecimal maxDisplay = 4095.0

// optional: show specific channels (fuzzy search)
showChannels = ['all']

// optional: set new names
def newChannels = []

// get image data
def imageData = getCurrentImageData()
def viewer = getCurrentViewer()
def display = viewer.getImageDisplay()
def server = imageData.getServer()
def channels = server.getMetadata().getChannels()
def selectedChannels = channels.findAll {
    channel -> showChannels.any {
        substring -> channel.getName().toLowerCase().contains(substring.toLowerCase())
    }
}

// hide all channels (avoid timing issues)
availableDisplayChannels = display.availableChannels()
display.selectedChannels.setAll(display.availableChannels())
display.selectedChannels.clear()

// change channel display range
activeChannels = []
for (int c = 0; c < channels.size(); c++) {
    if (selectedChannels.contains(channels[c])) {
        activeChannels << channels[c]
    }
    setChannelDisplayRange(c, minDisplay, maxDisplay)
}

// show all active channels
if (showChannels.any { it.toLowerCase() == 'all' }) {
    display.selectedChannels.setAll(availableDisplayChannels)
    } else {
    def displayChannels = availableDisplayChannels.findAll {
        displayChannel ->
            def displayName = displayChannel.toString()
            selectedChannels*.getName().any {
                selectedName -> selectedName.contains(displayName.split(" \\(")[0])
            }
    }
    display.selectedChannels.setAll(displayChannels)
}
viewer.repaintEntireImage()

// change channel names
if (newChannels.size() == channels.size()) {
    setChannelNames(newChannels.toArray(new String[0]))
}

// print channel names
def channelNames = channels.collect { '"' + it.getName() + '"' }.join(', ')
print 'CHANNELS:'
print '[' + channelNames + ']'
