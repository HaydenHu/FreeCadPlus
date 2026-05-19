# FreeCadPlus - Chamfer, fillet, and threaded rod tools

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

# Clean up old toolbars
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

_INJECTED = False

def _inject(wb_name):
    global _INJECTED
    if _INJECTED or "PartDesign" not in wb_name:
        return
    from PySide import QtGui
    import FreeCADGui as Gui
    from i18n import tr
    # Inline mapping to avoid FreeCAD scoping issues
    injections = {
        "Part Design Dress-Up Features": {
            "PartDesign_Chamfer": ("PartDesign_FullChamfer", tr("Full Chamfer"), tr("Create a parametric full chamfer on selected edges")),
            "PartDesign_Fillet": ("PartDesign_FullFillet", tr("Full Fillet"), tr("Create a parametric full fillet on selected edges")),
        },
        "Part Design Modeling Features": {
            "PartDesign_Hole": ("PartDesign_ThreadedRod", tr("Threaded Rod"), tr("Create a parametric external thread on a cylinder")),
        },
    }
    try:
        mw = Gui.getMainWindow()
        for tb in mw.findChildren(QtGui.QToolBar):
            ttl = tb.windowTitle()
            if ttl not in injections:
                continue
            cmds = injections[ttl]
            for a in tb.actions():
                name = a.objectName()
                if name not in cmds:
                    continue
                btn = tb.widgetForAction(a)
                if btn is None:
                    continue
                our, txt, tip = cmds[name]
                menu = a.menu()
                if menu is None:
                    menu = QtGui.QMenu()
                    a.setMenu(menu)
                menu.setToolTipsVisible(True)
                menu.setStyleSheet("QMenu { icon-size: 24px; }")
                # Button layout
                btn.setPopupMode(QtGui.QToolButton.MenuButtonPopup)
                w = btn.iconSize().width()
                btn.setMinimumWidth(int(w * 1.8))
                btn.setStyleSheet(
                    "QToolButton { padding-right: 16px; } "
                    "QToolButton::menu-button { width: 16px; subcontrol-position: right; } "
                    "QToolButton::menu-arrow { width: 14px; height: 14px; margin-left: 1px; padding-right: 5px; }")
                if any(ma.text() == txt for ma in menu.actions()):
                    continue
                menu.addSeparator()
                import os as _os
                icon_dir = _os.path.join(FreeCAD.getUserAppDataDir(), "Mod", "FreeCadPlus", "Resources", "icons")
                icon_file = {"PartDesign_FullChamfer": "FullChamfer.svg", "PartDesign_FullFillet": "FullFillet.svg", "PartDesign_ThreadedRod": "ThreadedRod.svg"}[our]
                icon_path = _os.path.join(icon_dir, icon_file)
                act = menu.addAction(QtGui.QIcon(icon_path), txt) if _os.path.exists(icon_path) else menu.addAction(txt)
                act.setToolTip(tip)
                act.setStatusTip(tip)
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
