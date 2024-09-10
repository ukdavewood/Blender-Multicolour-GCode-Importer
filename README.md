# MultiColour - Blender-GCode-Importer

![A 3D render of a low-poly Thinker statue](/images/low_poly_thinker.png)
<sup>*Lowest Poly The Thinker* model by [LXO on Printables.com](https://www.printables.com/model/1165-lowest-poly-the-thinker)</sup>

## About

MultiColour Blender GCode Importer is substantial enhancement to kmnunleys simple plug-in that translates printer GCode into Bezier curve paths in Blender, and creates a simulated multicolour timelapse of the print.

## Example timelapses
[Timelapse Demo](https://youtu.be/28RHWP2CYZw?si=LybDFLo7hO7BbCez)


## Installation
To install the plugin, download the repository. Then go to Preferences > Addons and click the Install button. Find the multicolour_gcode_importer.py file from the repository and click install.

## Usage
To import a GCode file to Blender, simply go to File > Import and select the Multicolour GCode option. In the new file browser window, find and select the .gcode file you would ike to import, then click 'Import Gcode'

## FAQ
**How long do models take to import?**<br>
This depends heavily on the computer you are running on, but imports can take anywhere from just a couple seconds to several minutes depening on the size and complexity of the model that is being imported.

**How do I give the imported paths thickness?**<br>
These options can be found in the Properties area (bottom right panel in the default layout) when a path is selected. Under the 'Object Data Properties' tab there is a 'Geometry' dropdown. Under this dropdown, the two most useful values are 'Extrusion' and 'Bevel'. Adjust these values until the desired look of the model has been reached.

## Planned Features


## Troubleshooting
If you are experiencing issues with the plugin, feel free to open an issue and I'll respond when i can.


Like kmnunley's work?
[Buy me a coffee!](https://www.buymeacoffee.com/kmnunley) :coffee:
