# -*- coding: utf-8 -*-
# FullFillet task panel

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui
import pd_utils
import feature_fillet
from i18n import tr


class FilletTaskPanel:
    def __init__(self, feature_obj=None, edges=None):
        self.feature_obj = feature_obj
        self.edges = edges or []
        self.form = QtGui.QWidget()
        self._build_ui()

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        title = tr("Edit FullFillet") if self.feature_obj else tr("Full Fillet")
        layout.addWidget(QtGui.QLabel(
            f"<b>{title}</b><br>{tr('Selected')} {len(self.edges)} {tr('edge(s)')}"))

        layout.addSpacing(8)

        r = QtGui.QHBoxLayout()
        r.addWidget(QtGui.QLabel(tr("Fillet radius (mm):")))
        self.radius_spin = QtGui.QDoubleSpinBox()
        self.radius_spin.setRange(0.001, 99999.0)
        self.radius_spin.setDecimals(4)
        self.radius_spin.setSingleStep(0.1)
        r.addWidget(self.radius_spin)
        layout.addLayout(r)

        layout.addSpacing(4)

        if self.edges:
            txt = tr("Edge parameters:") + "\n"
            for i, ed in enumerate(self.edges):
                is_circle = False
                try:
                    c = ed['edge'].Curve
                    is_circle = hasattr(c, 'Radius') and c.Radius > 0
                except Exception:
                    pass
                typ = tr("circle") if is_circle else tr("straight")
                def_r, _ = self._get_default_radius(ed['edge'], ed['obj'].Shape)
                txt += (f"  Edge {i+1} ({typ}): "
                        f"{tr('default')} {def_r:.4f} mm  "
                        f"{tr('min adj len')} {ed['min_len']:.4f} mm\n")
            layout.addWidget(QtGui.QLabel(txt))

        if self.feature_obj:
            val = self.feature_obj.Radius
            self.radius_spin.setValue(val.Value if hasattr(val, 'Value') else val)
        elif self.edges:
            default_r, _ = self._get_default_radius(
                self.edges[0]['edge'], self.edges[0]['obj'].Shape)
            self.radius_spin.setValue(default_r)

    def _get_default_radius(self, edge, shape):
        try:
            c = edge.Curve
            if hasattr(c, 'Radius') and c.Radius > 0:
                return c.Radius, True
        except Exception:
            pass
        return pd_utils.get_min_adjacent_edge_length(edge, shape), False

    def accept(self):
        Gui.Control.closeDialog()
        radius = self.radius_spin.value()
        if self.feature_obj:
            self.feature_obj.Radius = radius
            self.feature_obj.Document.recompute()
        elif self.edges:
            _do_create_fillet(self.edges, radius)

    def reject(self):
        Gui.Control.closeDialog()


def _do_create_fillet(edges, radius):
    doc = App.ActiveDocument
    if not doc:
        return
    edge_objs = edges
    body = edge_objs[0]['body']
    base_obj = edge_objs[0]['obj']
    edge_indices = [ed['idx'] for ed in edge_objs]

    doc.openTransaction("Full Fillet")
    try:
        if body:
            fp_obj = body.newObject('PartDesign::FeaturePython', 'FullFillet')
            base_obj.Visibility = False
        else:
            fp_obj = doc.addObject('PartDesign::FeaturePython', 'FullFillet')
        feature_fillet.FullFillet(
            fp_obj, radius=radius, edge_indices=edge_indices, base_obj=base_obj)
        feature_fillet.ViewProviderFullFillet(fp_obj.ViewObject)
        doc.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(fp_obj)
        doc.commitTransaction()
        App.Console.PrintMessage(
            f"FullFillet: {len(edge_indices)} edges, radius: {radius:.4f} mm\n")
    except Exception as e:
        doc.abortTransaction()
        QtGui.QMessageBox.critical(None, tr("Fillet failed"), str(e))
