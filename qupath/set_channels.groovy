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
Version:    0.1

Hint:
Load and execute this script with QuPath's script editor window using
the "Run" (current image) or the "Run for project" (all images) command.
Add this script to your "User scripts" directory to make it available
for all projects opened in your current QuPath installation.
*/

// mandatory: set new rannge
BigDecimal minDisplay = 0.0
BigDecimal maxDisplay = 4095.0

// optional: set new names
def newChannels = []

// get image data
def imageData = getCurrentImageData()
def server = imageData.getServer()
def channels = server.getMetadata().getChannels()

// change channel display range
for (int c = 0; c < channels.size(); c++) {
    setChannelDisplayRange(c, minDisplay, maxDisplay)
}

// change channel names
if (newChannels.size() == channels.size()) {
    setChannelNames(newChannels.toArray(new String[0]))
}

// print channel names
def channelNames = channels.collect { '"' + it.getName() + '"' }.join(', ')
print 'CHANNELS:'
print '[' + channelNames + ']'
