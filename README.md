# Age of the Ring
Work done for AOTR, related to installing and updating the mod. The code in this repository is not functional as it is missing various files and bits but rather serves as a transparency measure and for bug reports.

This repository contains three pieces of software

## The Installer
A simple piece of software that extract the aotr.zip next to it into the desired folder and move the cahfactions.ini into the rotwk folder to fix the bug

## The Patch Maker
This is used by the mod makers when they desire to make a release to make it compatible and easily searchable by the launcher. This simply makes a list of every file in a directory and create a copy replacing the name of the file with its path.

## The Launcher
The crown jewel, a simple GUI with backend which allows it to launch the mod with the CAH factions fix, provides links to the wiki, forums. An about section serving as a disclaimer, an uninstall button and an update button which queries the server for any changes and downloads files accordingly.
