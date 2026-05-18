# FreeCADPlus

Parametric Chamfer, Fillet, and ThreadedRod addon for FreeCAD PartDesign.

## Install

```bash
cd "C:\Users\<user>\AppData\Roaming\FreeCAD\v1-2\Mod"
git clone git@github.com:HaydenHu/FreeCADPlus.git
```

Restart FreeCAD. The toolbar **FreeCadPlus** appears in the PartDesign workbench.

## Tools

| Tool | Description |
|------|-------------|
| Full Chamfer | Full chamfer on selected edges. Small distance uses OCCT chamfer; large distance uses boolean cut. |
| Full Fillet | Full fillet on selected edges. Small radius uses OCCT fillet; large radius uses boolean cut. |
| ThreadedRod | External thread on a cylindrical face. Supports ISO Metric Coarse/Fine or custom parameters. |

## Usage

1. Open a PartDesign Body, select edges or a cylindrical face.
2. Click the tool button in the **FreeCadPlus** toolbar.
3. Set parameters in the dialog and confirm.
4. Double-click the feature in the tree to edit parameters.
5. Parameters are also editable in the Data tab.

## Compatibility

FreeCAD 1.2+ / Windows / Linux / macOS

## License

MIT
