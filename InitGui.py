# FreeCadPlus - Chamfer, fillet, and threaded rod tools

import FreeCAD
import FreeCADGui
from PySide import QtGui, QtCore
import Commands

# Register all three commands globally
if "PartDesign_FullChamfer" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_FullChamfer", Commands.cmdFullChamfer())
if "PartDesign_FullFillet" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_FullFillet", Commands.cmdFullFillet())
if "PartDesign_ThreadedRod" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_ThreadedRod", Commands.cmdThreadedRod())

class FreeCADPlusWorkbench:
    pass

# Register ThreadedRod as a standalone toolbar button
cmds = [
    "PartDesign_FullChamfer",
    "PartDesign_FullFillet",
    "PartDesign_ThreadedRod",
]
tbname = "FreeCadPlus"

pd_toolbars = FreeCAD.ParamGet(
    "User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar")

# Clean old entries
for g in pd_toolbars.GetGroups():
    tb = pd_toolbars.GetGroup(g)
    n = tb.GetString("Name")
    if n in ("PartDesignTools", "PartDesign Tools", "FreeCAD+", "FreeCadPlus"):
        for s in list(tb.GetStrings()):
            tb.RemString(s)
        pd_toolbars.RemGroup(g)
        break

# Register standalone toolbar with ThreadedRod only
found = False
for g in pd_toolbars.GetGroups():
    tb = pd_toolbars.GetGroup(g)
    if tb.GetString("Name") == tbname:
        for cmd in cmds:
            if tb.GetString(cmd) == "":
                tb.SetString(cmd, "FreeCadPlus")
        found = True
        break
if not found:
    tb = pd_toolbars.GetGroup("FreeCadPlus")
    tb.SetString("Name", tbname)
    tb.SetString("PartDesign_ThreadedRod", "FreeCadPlus")
    tb.SetBool("Active", 1)


# Hook into PartDesign workbench to add dropdown menus
_INJECTED = False

def _find_tool_button(toolbar, cmd_internal):
    """Find QToolButton for a command in the toolbar."""
    import FreeCAD
    for a in toolbar.actions():
        if a.objectName() == cmd_internal:
            w = toolbar.widgetForAction(a)
            FreeCAD.Console.PrintMessage(f"FreeCadPlus: found button for {cmd_internal}, widget={w}\n")
            return w
    FreeCAD.Console.PrintMessage(f"FreeCadPlus: no action named {cmd_internal}\n")
    return None


def _add_dropdown(toolbar, builtin_cmd, our_cmd):
    """Add a dropdown menu to a built-in toolbar button."""
    from PySide import QtGui
    import FreeCADGui
    btn = _find_tool_button(toolbar, builtin_cmd)
    if btn is None:
        return False

    menu = btn.menu()
    if menu is None:
        menu = QtGui.QMenu(btn)
        btn.setMenu(menu)
        btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)

    # Skip if already added
    for a in menu.actions():
        if a.objectName() == our_cmd:
            return True

    menu.addSeparator()
    cmd = FreeCADGui.getCommand(our_cmd)
    info = cmd.getInfo()
    action = menu.addAction(info["MenuText"])
    action.setToolTip(info.get("ToolTip", ""))
    action.setObjectName(our_cmd)
    action.triggered.connect(lambda checked=False, c=our_cmd: FreeCADGui.runCommand(c))
    return True


def _do_inject():
    global _INJECTED
    if _INJECTED:
        return
    from PySide import QtGui
    import FreeCADGui
    try:
        mw = FreeCADGui.getMainWindow()
        found_tb = False
        for tb in mw.findChildren(QtGui.QToolBar):
            title = tb.windowTitle()
            FreeCAD.Console.PrintMessage(f"FreeCadPlus: found toolbar '{title}'\n")
            if not title or "Part" not in title:
                continue
            found_tb = True
            # Print all actions for debugging
            for a in tb.actions():
                if a.objectName():
                    FreeCAD.Console.PrintMessage(f"  action: {a.objectName()} text='{a.text()}'\n")
            r1 = _add_dropdown(tb, "PartDesign_Chamfer", "PartDesign_FullChamfer")
            r2 = _add_dropdown(tb, "PartDesign_Fillet", "PartDesign_FullFillet")
            FreeCAD.Console.PrintMessage(f"FreeCadPlus: Chamfer={r1} Fillet={r2}\n")
            break
        if not found_tb:
            FreeCAD.Console.PrintWarning("FreeCadPlus: no PartDesign toolbar found\n")
        _INJECTED = True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"FreeCadPlus: injection failed: {e}\n")


def _inject_into_partdesign(wb_name):
    import FreeCAD
    FreeCAD.Console.PrintMessage(f"FreeCadPlus: workbench activated: {wb_name}\n")
    if "PartDesign" not in wb_name:
        return
    from PySide import QtCore
    QtCore.QTimer.singleShot(500, _do_inject)


try:
    mw = FreeCADGui.getMainWindow()
    sig = getattr(mw, "workbenchActivated", None)
    if sig is not None:
        sig.connect(_inject_into_partdesign)
except Exception:
    pass
