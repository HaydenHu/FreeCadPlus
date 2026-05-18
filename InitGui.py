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

# Register FreeCadPlus toolbar in PartDesign
pd_toolbars = FreeCAD.ParamGet(
    "User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar")

for g in pd_toolbars.GetGroups():
    tb = pd_toolbars.GetGroup(g)
    n = tb.GetString("Name")
    if n in ("PartDesignTools", "PartDesign Tools", "FreeCAD+", "FreeCadPlus"):
        for s in list(tb.GetStrings()):
            tb.RemString(s)
        pd_toolbars.RemGroup(g)
        break

# Only ThreadedRod in standalone toolbar
tb = pd_toolbars.GetGroup("FreeCadPlus")
tb.SetString("Name", "FreeCadPlus")
tb.SetString("PartDesign_ThreadedRod", "FreeCadPlus")
tb.SetBool("Active", 1)

# Inject FullChamfer/FullFillet as dropdowns under built-in Chamfer/Fillet
_INJECTED = False

def _inject(wb_name):
    global _INJECTED
    if _INJECTED or "PartDesign" not in wb_name:
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
                if name not in ("PartDesign_Chamfer", "PartDesign_Fillet"):
                    continue
                btn = tb.widgetForAction(a)
                if btn is None:
                    continue
                our = ("PartDesign_FullChamfer" if name == "PartDesign_Chamfer"
                       else "PartDesign_FullFillet")
                txt = "Full Chamfer" if name == "PartDesign_Chamfer" else "Full Fillet"
                tip = ("Create a parametric full chamfer on selected edges" if name == "PartDesign_Chamfer"
                       else "Create a parametric full fillet on selected edges")
                # Add menu to action if not already present
                menu = a.menu()
                if menu is None:
                    menu = QtGui.QMenu()
                    a.setMenu(menu)
                # Set button to show dropdown arrow, enlarge click area
                btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
                w = btn.iconSize().width()
                btn.setMinimumWidth(w + 40)
                btn.setStyleSheet(
                    "QToolButton { padding-left: 2px; padding-right: 4px; } "
                    "QToolButton::menu-button { width: 24px; subcontrol-position: right; } "
                    "QToolButton::menu-arrow { width: 12px; height: 12px; }")
                # Skip if already added
                if any(ma.text() == txt for ma in menu.actions()):
                    continue
                menu.addSeparator()
                act = menu.addAction(txt)
                act.setToolTip(tip)
                act.triggered.connect(lambda c=False, cmd=our: Gui.runCommand(cmd))
        _INJECTED = True
    except Exception as e:
        FreeCAD.Console.PrintWarning(f"FreeCadPlus: {e}\n")

try:
    mw = FreeCADGui.getMainWindow()
    sig = getattr(mw, "workbenchActivated", None)
    if sig is not None:
        sig.connect(_inject)
except Exception:
    pass

FreeCAD.Console.PrintMessage("FreeCadPlus: toolbar registered\n")
