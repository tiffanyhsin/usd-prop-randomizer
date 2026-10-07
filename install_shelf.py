"""Drag this file into Maya's viewport to install USD Prop Randomizer."""
from pathlib import Path
import shutil
import sys


def install():
    import maya.cmds as cmds
    import maya.mel as mel

    if cmds.about(batch=True):
        raise RuntimeError("Run the installer in Maya's graphical interface.")
    source = Path(__file__).resolve().with_name("Randomizer.py")
    if not source.is_file():
        raise RuntimeError("Keep install_shelf.py and Randomizer.py in the same extracted folder.")
    shelf_top = mel.eval('$usdRandomizerShelfTop = $gShelfTopLevel')
    shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)
    if not shelf:
        raise RuntimeError("Select a Maya shelf before installing.")

    scripts = Path(cmds.internalVar(userScriptDir=True))
    scripts.mkdir(parents=True, exist_ok=True)
    destination = scripts / "Randomizer.py"
    if source != destination.resolve():
        if destination.exists():
            shutil.copy2(destination, scripts / "Randomizer.py.bak")
        shutil.copy2(source, destination)
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    tag = "usd_prop_randomizer/launcher"
    settings = dict(
        label="USD Prop Randomizer",
        annotation="Open USD Prop Randomizer: randomize USD prop scale and rotation",
        image="commandButton.png",
        imageOverlayLabel="USD Rand",
        sourceType="python",
        command="import Randomizer\nRandomizer.show()",
        docTag=tag,
    )
    button = None
    for child in cmds.shelfLayout(shelf, query=True, childArray=True) or []:
        if cmds.shelfButton(child, exists=True) and cmds.shelfButton(child, query=True, docTag=True) == tag:
            button = child
            break
    if button:
        cmds.shelfButton(button, edit=True, **settings)
    else:
        button = cmds.shelfButton(parent=shelf, **settings)
    shelf_path = str(Path(cmds.internalVar(userShelfDir=True)) / ("shelf_" + shelf.split("|")[-1]))
    saved = cmds.saveShelf(shelf, shelf_path)
    if not saved:
        cmds.warning("Button created, but the shelf could not be saved. Use Maya's Save All Shelves command.")
    cmds.confirmDialog(
        title="USD Prop Randomizer",
        message="Installed. Click USD Rand on the selected shelf.\nIf updating an already loaded tool, restart Maya first.",
        button=["OK"],
    )
    return button


def onMayaDroppedPythonFile(*args):
    install()


if __name__ == "__main__":
    install()
