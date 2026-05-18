# FreeCadPlus - Chamfer, fillet, and threaded rod tools

import FreeCAD
import FreeCADGui
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
        # Only ThreadedRod in standalone toolbar (Chamfer/Fillet are dropdowns)
        if tb.GetString("PartDesign_ThreadedRod") == "":
            tb.SetString("PartDesign_ThreadedRod", "FreeCadPlus")
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
    try:
        mw = Gui.getMainWindow()
        for tb in mw.findChildren(QtGui.QToolBar):
            if tb.windowTitle() != "Part Design Dress-Up Features":
                continue
            for a in tb.actions():
                name = a.objectName()
                if name in ("PartDesign_Chamfer", "PartDesign_Fillet"):
                    btn = tb.widgetForAction(a)
                    if btn is None:
                        continue
                    our_cmd = ("PartDesign_FullChamfer" if name == "PartDesign_Chamfer"
                               else "PartDesign_FullFillet")
                    if btn.menu() is None:
                        menu = QtGui.QMenu(btn)
                        btn.setMenu(menu)
                        btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
                    menu = btn.menu()
                    if menu:
                        menu.addSeparator()
                        ci = Gui.getCommand(our_cmd).getInfo()
                        act = menu.addAction(ci["MenuText"])
                        act.setToolTip(ci.get("ToolTip", ""))
                        act.triggered.connect(lambda c=False, cmd=our_cmd: Gui.runCommand(cmd))
            break
    except Exception as e:
        import FreeCAD
        FreeCAD.Console.PrintWarning(f"FreeCadPlus: {e}\n")


try:
    mw = FreeCADGui.getMainWindow()
    sig = getattr(mw, "workbenchActivated", None)
    if sig is not None:
        sig.connect(_inject_into_partdesign)
except Exception:
    pass
