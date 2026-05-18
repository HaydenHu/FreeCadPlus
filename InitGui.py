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
def _inject_into_partdesign(wb_name):
    if "PartDesign" not in wb_name:
        return
    from PySide import QtGui
    import FreeCADGui as Gui
    import FreeCAD
    try:
        mw = Gui.getMainWindow()
        for tb in mw.findChildren(QtGui.QToolBar):
            title = tb.windowTitle()
            FreeCAD.Console.PrintMessage(f"DBG toolbar: '{title}', actions={tb.actions()}\n")
            if not title or "Part" not in title:
                continue
            for a in tb.actions():
                FreeCAD.Console.PrintMessage(f"DBG action: name='{a.objectName()}' text='{a.text()}'\n")
            break
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"FreeCadPlus: {e}\n")


try:
    mw = FreeCADGui.getMainWindow()
    sig = getattr(mw, "workbenchActivated", None)
    if sig is not None:
        sig.connect(_inject_into_partdesign)
except Exception:
    pass
