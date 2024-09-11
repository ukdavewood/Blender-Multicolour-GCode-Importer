# MultiColour - Blender-GCode-Importer

![Youtube Thumbnail](/images/YoutubeThumbnail.png)


## About

MultiColour Blender GCode Importer is an enhancement to kmnunleys  plug-in that translates Bambu Studio Generated printer GCode into Bezier curve paths in Blender, and creates a simulated multicolour timelapse of the print.

## Example timelapses
https://youtu.be/28RHWP2CYZw?si=LybDFLo7hO7BbCez


## Installation
To install the plugin, download the repository. Then go to Preferences > Addons and click the Install button. Find the multicolour_gcode_importer.py file from the repository and click install.

## Usage
To import a BambuStuduo GCode file to Blender, simply go to File > Import and select the Multicolour GCode option. In the new file browser window, find and select the .gcode file you would ike to import, then click 'Import Gcode'

Don't forget switch to Materials or Render view to see the colours.

A scaled down similation of the flush waste is also included in the timelapse.

The importer also creates simulated head movement that can be tied to an animation of a real printer - see youtube demo for an example.

The importer also has the ability to add time values to the key frames - so that for example a clock can be animated alongside the timelapse.

See this video for a basic demo of the use of the plugin   https://youtu.be/4Nely6-mx40

## FAQ
**How long do models take to import?**<br>
This depends heavily on the computer you are running on, but imports can take anywhere from just a couple seconds to several minutes depening on the size and complexity of the model that is being imported.



## Planned Features
1. Improved more realistic head movement to match real timelapses
2. Improved visualisation of purge waste
3. Provide some parameters to control the way the timelapses are created.
4. handle Arc movements

## Troubleshooting
If you are experiencing issues with the plugin, feel free to open an issue and I'll respond when i can.
Info about the Addin will also be tracked here
https://forum.bambulab.com/t/blender-multicolour-bambustudio-gcode-importer/97948 


## Credits

This Importer is based on an plugin created ny Kevin Nunley.

Like kmnunley's work?
[Buy him a coffee!](https://www.buymeacoffee.com/kmnunley) :coffee:
