# FreeCadPlus - Chamfer, fillet, and threaded rod tools
# Injects directly into the PartDesign workbench toolbar via parameter system.

import FreeCAD
import FreeCADGui

import Commands

if "PartDesign_FullChamfer" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_FullChamfer", Commands.cmdFullChamfer())
if "PartDesign_FullFillet" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_FullFillet", Commands.cmdFullFillet())
if "PartDesign_ThreadedRod" not in FreeCADGui.listCommands():
    FreeCADGui.addCommand("PartDesign_ThreadedRod", Commands.cmdThreadedRod())

class FreeCADPlusWorkbench:
    pass

# Register toolbar into PartDesign workbench via parameter system
pd_toolbars = FreeCAD.ParamGet(
    "User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar")

# Clean up old toolbar names
for g in pd_toolbars.GetGroups():
    tb = pd_toolbars.GetGroup(g)
    n = tb.GetString("Name")
    if n in ("PartDesignTools", "PartDesign Tools"):
        for s in list(tb.GetStrings()):
            tb.RemString(s)
        pd_toolbars.RemGroup(g)
        break

cmds = [
    "PartDesign_FullChamfer",
    "PartDesign_FullFillet",
    "PartDesign_ThreadedRod",
]
tbname = "FreeCadPlus"

# Check if toolbar already exists
found = False
for g in pd_toolbars.GetGroups():
    tb = pd_toolbars.GetGroup(g)
    if tb.GetString("Name") == tbname:
        for cmd in cmds:
            if tb.GetString(cmd) == "":
                tb.SetString(cmd, "FreeCADPlus")
        found = True
        break

if not found:
    tb = pd_toolbars.GetGroup("FreeCADPlus")
    tb.SetString("Name", tbname)
    for cmd in cmds:
        tb.SetString(cmd, "FreeCADPlus")
    tb.SetBool("Active", 1)

FreeCAD.Console.PrintMessage("FreeCADPlus: toolbar registered in PartDesign\n")
