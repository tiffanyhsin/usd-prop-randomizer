import maya.cmds as cmds
import mayaUsd.ufe
import ufe
import maya.OpenMayaUI as omui
import random
import os
from shiboken6 import wrapInstance
from pxr import Usd, UsdGeom, Gf
from PySide6 import QtWidgets, QtCore

def load_usd(path: str) -> str:
    """Create a USD stage for a file. Returns the proxy shape."""
    cmds.loadPlugin("mayaUsdPlugin", quiet=True)
    name = os.path.splitext(os.path.basename(path))[0]
    transform = cmds.createNode("transform", name=name)
    shape = cmds.createNode("mayaUsdProxyShape", name=f"{name}Shape", parent=transform)
    cmds.setAttr(f"{shape}.filePath", path, type="string")
    cmds.connectAttr("time1.outTime", f"{shape}.time")
    match_up_axis(path, transform)
    return shape


def match_up_axis(path: str, transform: str) -> None:
    """Rotate the stage so its up axis matches Maya's."""
    stage = Usd.Stage.Open(path, Usd.Stage.LoadNone)
    usd_up = UsdGeom.GetStageUpAxis(stage).lower()
    maya_up = cmds.upAxis(query=True, axis=True)
    if usd_up != maya_up:
        cmds.setAttr(f"{transform}.rotateX", -90 if usd_up == "z" else 90)


def main(path: str) -> Usd.Stage:
    """Load a USD file and return its live stage."""
    shape = load_usd(path)
    return mayaUsd.ufe.getStage(cmds.ls(shape, long=True)[0])


# Get Maya's main window.
maya_window = wrapInstance(
    int(omui.MQtUtil.mainWindow()),
    QtWidgets.QMainWindow
)

# Create our tool with Maya as its parent.
usd_window = QtWidgets.QDialog(maya_window)
usd_window.setWindowFlag(
    QtCore.Qt.WindowType.WindowStaysOnTopHint, True
)


usd_window.setWindowTitle("USD Prop Randomizer")
usd_window.resize(560, 420)

# Create a vertical layout inside the window.
layout = QtWidgets.QVBoxLayout(usd_window)

# Create the file controls.
file_label = QtWidgets.QLabel("USD File:")
load_button = QtWidgets.QPushButton("Load USD")
file_input = QtWidgets.QLineEdit()
file_input.setReadOnly(True)
file_input.setPlaceholderText("Choose a USD file...")

browse_button = QtWidgets.QPushButton("Browse")

layout.addWidget(file_label)
layout.addWidget(file_input)
layout.addWidget(browse_button)
layout.addWidget(load_button)


# Create the controls.
name_label = QtWidgets.QLabel("Name contains:")
name_input = QtWidgets.QLineEdit()
name_input.setPlaceholderText("Example: plate")
select_button = QtWidgets.QPushButton("Select Matching Prims")

# Add the controls from top to bottom.
layout.addWidget(name_label)
layout.addWidget(name_input)
layout.addWidget(select_button)


# A horizontal row containing both panels.
panels_layout = QtWidgets.QHBoxLayout()
layout.addLayout(panels_layout)

# LEFT PANEL: Random Scale
scale_group = QtWidgets.QGroupBox("Random Scale")
scale_panel = QtWidgets.QVBoxLayout(scale_group)
panels_layout.addWidget(scale_group, 1)

min_scale = QtWidgets.QDoubleSpinBox()
min_scale.setRange(0.01, 10.0)
min_scale.setSingleStep(0.05)
min_scale.setValue(0.90)

max_scale = QtWidgets.QDoubleSpinBox()
max_scale.setRange(0.01, 10.0)
max_scale.setSingleStep(0.05)
max_scale.setValue(1.10)

scale_fields = QtWidgets.QFormLayout()
scale_fields.addRow("Minimum:", min_scale)
scale_fields.addRow("Maximum:", max_scale)
scale_panel.addLayout(scale_fields)

scale_panel.addStretch()

randomize_button = QtWidgets.QPushButton("Randomize Scale")
scale_panel.addWidget(randomize_button)


# Keep this initialization only once in your script.
randomize_history = []


# RIGHT PANEL: Random Rotation
rotation_group = QtWidgets.QGroupBox("Random Rotation")
rotation_panel = QtWidgets.QVBoxLayout(rotation_group)
space_layout = QtWidgets.QHBoxLayout()

space_label = QtWidgets.QLabel("Rotation Space:")
rotation_space = QtWidgets.QComboBox()
rotation_space.addItems(["Object", "World"])

space_layout.addWidget(space_label)
space_layout.addWidget(rotation_space)

rotation_panel.addLayout(space_layout)
panels_layout.addWidget(rotation_group, 1)

rotation_x = QtWidgets.QCheckBox("X")
rotation_y = QtWidgets.QCheckBox("Y")
rotation_z = QtWidgets.QCheckBox("Z")
rotation_y.setChecked(True)

axis_layout = QtWidgets.QHBoxLayout()
axis_layout.addWidget(rotation_x)
axis_layout.addWidget(rotation_y)
axis_layout.addWidget(rotation_z)
rotation_panel.addLayout(axis_layout)

min_rotation = QtWidgets.QDoubleSpinBox()
min_rotation.setRange(-360.0, 360.0)
min_rotation.setValue(-15.0)
min_rotation.setSuffix("°")

max_rotation = QtWidgets.QDoubleSpinBox()
max_rotation.setRange(-360.0, 360.0)
max_rotation.setValue(15.0)
max_rotation.setSuffix("°")

rotation_fields = QtWidgets.QFormLayout()
rotation_fields.addRow("Minimum:", min_rotation)
rotation_fields.addRow("Maximum:", max_rotation)
rotation_panel.addLayout(rotation_fields)

rotation_panel.addStretch()

rotate_button = QtWidgets.QPushButton("Randomize Rotation")
rotation_panel.addWidget(rotate_button)

# Create the both button.
both_button = QtWidgets.QPushButton("Randomize Both")
both_button.setMinimumHeight(45)
layout.addWidget(both_button)

# Create the Undo button.
undo_button = QtWidgets.QPushButton("Undo Last Randomize")
layout.addWidget(undo_button)

# Store previous scale values for undo.
randomize_history = []

status_label = QtWidgets.QLabel("Ready. Load a USD file or use an open scene.")
status_label.setWordWrap(True)
layout.addWidget(status_label)

def browse_file():
    file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
        usd_window,
        "Choose a USD File",
        "",
        "USD Files (*.usd *.usda *.usdc)"
    )

    if file_path:
        file_input.setText(file_path)

def load_selected_file():
    # Read the path displayed by Browse.
    file_path = file_input.text().strip()

    if not file_path:
        print("Choose a USD file with Browse first.")
        return

    # Call the teacher's loading function.
    main(file_path)

browse_button.clicked.connect(browse_file)

# Define what happens when the button is clicked.
def select_matching():
    search_text = name_input.text().strip().lower()

    if not search_text:
        print("Please enter a name.")
        return

    # Find USD stage nodes already in Maya.
    shape_paths = cmds.ls(type="mayaUsdProxyShape", long=True)

    if not shape_paths:
        print("No USD stages found in Maya.")
        return

    count = 0
    selection = ufe.GlobalSelection.get()
    selection.clear()

    for shape_path in shape_paths:
        stage = mayaUsd.ufe.getStage(shape_path)

        if stage is None:
            continue

        matching_paths = []

        for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
            if search_text not in prim.GetName().lower():
                continue

            # Avoid matching both an object and its children.
            if any(
                prim.GetPath().HasPrefix(path)
                for path in matching_paths
            ):
                continue

            matching_paths.append(prim.GetPath())

            ufe_path = f"{shape_path},{prim.GetPath()}"

            # Turn the text address into a UFE path.
            path = ufe.PathString.path(ufe_path)

            # Get a selectable item for the existing USD prim.
            item = ufe.Hierarchy.createItem(path)

            if item is not None:
                selection.append(item)
                count += 1

        status_label.setText(f"Selected {count} matching objects.")

def randomize_selected():
    minimum = min_scale.value()
    maximum = max_scale.value()

    if minimum > maximum:
        print("Minimum must be less than or equal to maximum.")
        return

    selected_paths = cmds.ls(selection=True, ufeObjects=True)

    if not selected_paths:
        status_label.setText("Select some USD objects first.")
        return

    previous_scales = []

    for selected_path in selected_paths:
        if "," not in selected_path:
            continue

        shape_path, prim_path = selected_path.split(",", 1)
        stage = mayaUsd.ufe.getStage(shape_path)

        if stage is None:
            continue

        prim = stage.GetPrimAtPath(prim_path)

        if not prim or prim.IsInstanceProxy():
            continue

        xform = UsdGeom.Xformable(prim)

        if not xform:
            continue

        with Usd.EditContext(stage, stage.GetSessionLayer()):
            scale_op = xform.GetScaleOp("propRandomizer")

            if not scale_op:
                scale_op = xform.AddScaleOp(
                    opSuffix="propRandomizer"
                )

            # Remember the old value BEFORE changing it.
            old_value = scale_op.Get()

            if old_value is None:
                old_value = Gf.Vec3f(1.0, 1.0, 1.0)

            factor = random.uniform(minimum, maximum)
            scale_op.Set(Gf.Vec3f(factor, factor, factor))

            previous_scales.append(
                (stage, prim.GetPath(), old_value)
            )

    # Save one batch for this button click.
    if previous_scales:
        randomize_history.append(("scale", previous_scales))
        undo_button.setEnabled(True)

    status_label.setText(
        f"Randomized {len(previous_scales)} USD objects."
    )


def randomize_rotation():
    minimum = min_rotation.value()
    maximum = max_rotation.value()
    space = rotation_space.currentText()
    print("Rotation space:", space)

    if minimum > maximum:
        status_label.setText("Minimum angle must not exceed maximum.")
        return

    use_x = rotation_x.isChecked()
    use_y = rotation_y.isChecked()
    use_z = rotation_z.isChecked()

    if not any([use_x, use_y, use_z]):
        status_label.setText("Choose at least one rotation axis.")
        return

    selected_paths = cmds.ls(selection=True, ufeObjects=True)

    if not selected_paths:
        status_label.setText("Select some USD objects first.")
        return

    previous_rotations = []
    count = 0

    for selected_path in selected_paths:
        if "," not in selected_path:
            continue

        shape_path, prim_path = selected_path.split(",", 1)
        stage = mayaUsd.ufe.getStage(shape_path)

        if stage is None:
            continue

        prim = stage.GetPrimAtPath(prim_path)

        if not prim or prim.IsInstanceProxy():
            continue

        xform = UsdGeom.Xformable(prim)

        if not xform:
            continue

        with Usd.EditContext(stage, stage.GetSessionLayer()):
            rotation_op = xform.GetRotateXYZOp("propRandomizer")

            # Save the operation order for Undo.
            old_order = list(xform.GetXformOpOrderAttr().Get() or [])
            reset_stack = xform.GetResetXformStack()

            # Use a matrix operation for Object and World rotation.
            rotation_attr = prim.GetAttribute(
                "xformOp:transform:propRandomizerSpace"
            )

            if rotation_attr:
                rotation_op = UsdGeom.XformOp(rotation_attr)
            else:
                rotation_op = xform.AddTransformOp(
                    opSuffix="propRandomizerSpace"
                )

            old_value = rotation_op.Get()

            if old_value is None:
                old_value = Gf.Matrix4d(1.0)
            
            # Generate separate angles for each selected object.
            angle_x = random.uniform(minimum, maximum) if use_x else 0.0
            angle_y = random.uniform(minimum, maximum) if use_y else 0.0
            angle_z = random.uniform(minimum, maximum) if use_z else 0.0
            
            # Represent each axis rotation as a matrix.
            rotate_x = Gf.Matrix4d(1.0).SetRotate(
                Gf.Rotation(Gf.Vec3d(1, 0, 0), angle_x)
            )

            rotate_y = Gf.Matrix4d(1.0).SetRotate(
                Gf.Rotation(Gf.Vec3d(0, 1, 0), angle_y)
            )

            rotate_z = Gf.Matrix4d(1.0).SetRotate(
                Gf.Rotation(Gf.Vec3d(0, 0, 1), angle_z)
            )

            # Combine the rotations in X, then Y, then Z order.
            rotation_matrix = rotate_x * rotate_y * rotate_z
            # Get the object's existing transform operations.
            base_ops = []

            for op in xform.GetOrderedXformOps():
                # Exclude both versions of our tool's rotation.
                if str(op.GetOpName()) in (
                    "xformOp:rotateXYZ:propRandomizer",
                    "xformOp:transform:propRandomizerSpace"
                ):
                    continue

                base_ops.append(op)

            # Combine those operations into one local transform.
            local_matrix = Gf.Matrix4d(1.0)

            for op in base_ops:
                local_matrix = (
                    op.GetOpTransform(Usd.TimeCode.Default())
                    * local_matrix
                )

            # Get the USD parent's transform in stage space.
            cache = UsdGeom.XformCache()
            parent_matrix = Gf.Matrix4d(1.0)

            if not xform.GetResetXformStack():
                parent_matrix = cache.GetParentToWorldTransform(prim)

            # Get the Maya transform that holds the USD stage.
            proxy_parent = cmds.listRelatives(
                shape_path,
                parent=True,
                fullPath=True
            )[0]

            maya_values = cmds.xform(
                proxy_parent,
                query=True,
                worldSpace=True,
                matrix=True
            )

            maya_matrix = Gf.Matrix4d(*maya_values)

            # Combine the object's local, USD-parent, and Maya transforms.
            world_matrix = local_matrix * parent_matrix * maya_matrix
            
            if space == "Object":
                rotation_offset = rotation_matrix

            else:
                # A zero scale makes the conversion impossible.
                if abs(world_matrix.GetDeterminant()) < 1e-12:
                    status_label.setText(
                        "Cannot rotate an object with zero world scale."
                    )
                    continue

                # Find the object's origin in Maya world space.
                pivot = world_matrix.ExtractTranslation()

                move_to_origin = Gf.Matrix4d(1.0).SetTranslate(-pivot)
                move_back = Gf.Matrix4d(1.0).SetTranslate(pivot)

                # Rotate around this object's origin, not the scene origin.
                world_rotation = (
                    move_to_origin * rotation_matrix * move_back
                )

                # Convert the world rotation into a local USD offset.
                rotation_offset = (
                    world_matrix
                    * world_rotation
                    * world_matrix.GetInverse()
                )

            # Apply the Object/World rotation matrix.
            rotation_op.Set(rotation_offset)

            # Preserve the original transforms and add our offset.
            xform.SetXformOpOrder(
                base_ops + [rotation_op],
                reset_stack
            )

            # Save the previous matrix and operation order for Undo.
            previous_rotations.append(
                (stage, prim.GetPath(), old_value, old_order)
            )
            
        count += 1
        
    if previous_rotations:
        randomize_history.append(("rotation_matrix", previous_rotations))
        undo_button.setEnabled(True)
        
    status_label.setText(f"Rotated {count} USD objects.")

def randomize_both():
    # Check both ranges before changing anything.
    if min_scale.value() > max_scale.value():
        status_label.setText("Minimum scale must not exceed maximum.")
        return

    if min_rotation.value() > max_rotation.value():
        status_label.setText("Minimum angle must not exceed maximum.")
        return

    if not any([
        rotation_x.isChecked(),
        rotation_y.isChecked(),
        rotation_z.isChecked()
    ]):
        status_label.setText("Choose at least one rotation axis.")
        return

    # Remember where this click's history starts.
    history_start = len(randomize_history)

    try:
        randomize_selected()
        randomize_rotation()
    finally:
        # Combine any saved actions from this click.
        actions = randomize_history[history_start:]

        if actions:
            del randomize_history[history_start:]
            randomize_history.append(("both", actions))
            undo_button.setEnabled(True)

    if len(actions) == 2:
        status_label.setText("Randomized scale and rotation.")

def undo_randomize():
    if not randomize_history:
        status_label.setText("Nothing to undo.")
        return

    action, saved_values = randomize_history.pop()

    # A combined action contains scale and rotation.
    if action == "both":
        actions = reversed(saved_values)
    else:
        actions = [(action, saved_values)]

    for action_type, previous_values in actions:
        for record in previous_values:
            stage, prim_path, old_value = record[:3]
            prim = stage.GetPrimAtPath(prim_path)

            if not prim:
                continue

            xform = UsdGeom.Xformable(prim)

            if not xform:
                continue

            with Usd.EditContext(stage, stage.GetSessionLayer()):
                if action_type == "rotation_matrix":
                    attribute = prim.GetAttribute(
                        "xformOp:transform:propRandomizerSpace"
                    )

                    if attribute:
                        attribute.Set(old_value)

                    # Restore which transform operations were active.
                    xform.GetXformOpOrderAttr().Set(record[3])

                elif action_type == "scale":
                    operation = xform.GetScaleOp("propRandomizer")

                    if operation:
                        operation.Set(old_value)

    undo_button.setEnabled(bool(randomize_history))
    status_label.setText("Undid last action.")

load_button.clicked.connect(load_selected_file)
select_button.clicked.connect(select_matching)
rotate_button.clicked.connect(randomize_rotation)
randomize_button.clicked.connect(randomize_selected)
both_button.clicked.connect(randomize_both)
undo_button.clicked.connect(undo_randomize)

usd_window.show()
  

