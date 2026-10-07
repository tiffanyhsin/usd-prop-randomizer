# USD Prop Randomizer

## Problem and Intended User

Artists often reuse models such as grass, flowers, and bowls to build a scene.
When every copy has the same scale and rotation, the scene can look repetitive. Adjusting each object manually takes time.
USD Prop Randomizer is a PySide6 tool for layout and set-dressing artists working with USD scenes in Maya.
It helps artists find repeated props by name and add size and rotation variation without adjusting each object individually.

## Requirements

- Autodesk Maya 2027
- Maya USD plugin
- PySide6, included with Maya

## Install the Shelf Button

1. Download the repository using **Code > Download ZIP** and extract it.
2. Open Maya 2027 and select the shelf where you want the button.
3. Drag `install_shelf.py` from the extracted folder into Maya's viewport.
4. Click the new **USD Rand** shelf button to open the tool.

The installer copies `Randomizer.py` to Maya's user scripts directory and saves the shelf. Keep both Python files together when installing. Reinstalling updates this tool's existing button on the selected shelf instead of creating another one. Restart Maya after installing an updated version if the tool was already loaded.

If drag-and-drop does not work, run this in a **Python** tab of Maya's Script Editor, then choose `install_shelf.py` from the extracted folder:

```python
import runpy
import maya.cmds as cmds
files = cmds.fileDialog2(fileMode=1, caption="Choose install_shelf.py", fileFilter="Python files (*.py)")
if files:
    runpy.run_path(files[0], run_name="__main__")
```

### Open manually after installation

```python
import Randomizer
Randomizer.show()
```

Clicking the button again brings the same window forward. Closing and reopening it preserves the tool's undo history for the current Maya session.

### Uninstall

Remove the **USD Rand** button through Maya's Shelf Editor. To remove the installed script, locate Maya's user scripts directory with `cmds.internalVar(userScriptDir=True)` and delete only the installed `Randomizer.py`. Restart Maya.

## How to Use

### Load a Scene

Click **Browse** to choose a `.usd`, `.usda`, or `.usdc` file, then click **Load USD**.

If a USD scene is already open in Maya, skip this step. Each click on **Load USD** creates another stage.

### Select Props

Enter part of a prim’s name, such as `plate`, then click **Select Matching Prims**.


### Randomize Scale

Enter minimum and maximum scale multipliers, then click the scale panel’s randomize button.

For example, `0.9–1.1` produces sizes between 90% and 110% of the starting size. Each object receives one factor applied equally to X, Y, and Z to preserve its proportions.

### Randomize Rotation

Choose the rotation space, check the desired axes, and enter an angle range in degrees.

- **Object:** uses the object’s local axes.
- **World:** uses Maya’s world axes.

Click "Randomize Rotation" to rotate the selected objects. Objects rotate around their existing origins, so make sure each object’s origin is positioned where you want it to rotate.

### Randomize Both and Undo

**Randomize Both** applies the scale and rotation settings together.

The **Undo** button restores the previous randomization. A combined scale-and-rotation action takes one Undo click. Repeated Undo clicks step backward through the tool’s saved history.

## Test Scene

Tested in Maya 2027 using Pixar’s **Kitchen Set**, including selecting plate props by name and randomizing their transforms.

Download: https://openusd.org/release/dl_kitchen_set.html


## Limitations

- Intended for static USD props; animated transforms are not supported.
- Edits are authored in the USD session layer. The tool does not save or export the modified stage to a USD file.
- Undo applies only to actions recorded by this tool and is separate from Maya’s general undo history.
