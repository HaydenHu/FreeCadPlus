# -*- coding: utf-8 -*-
# FullChamfer task panel

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
import pd_utils
import feature_chamfer
from i18n import tr


class ChamferTaskPanel:
    def __init__(self, feature_obj=None, edges=None):
        self.feature_obj = feature_obj
        self.edges = edges or []
        self.form = QtGui.QWidget()
        self._build_ui()

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        title = tr("Edit FullChamfer") if self.feature_obj else tr("Full Chamfer")
        layout.addWidget(QtGui.QLabel(
            f"<b>{title}</b><br>{tr('Selected')} {len(self.edges)} {tr('edge(s)')}"))

        layout.addSpacing(8)

        r = QtGui.QHBoxLayout()
        r.addWidget(QtGui.QLabel(tr("Chamfer distance (mm):")))
        self.dist_spin = QtGui.QDoubleSpinBox()
        self.dist_spin.setRange(0.001, 99999.0)
        self.dist_spin.setDecimals(4)
        self.dist_spin.setSingleStep(0.1)
        r.addWidget(self.dist_spin)
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
                txt += (f"  Edge {i+1} ({typ}): "
                        f"{tr('min adj len')} {ed['min_len']:.4f} mm\n")
            layout.addWidget(QtGui.QLabel(txt))

        layout.addSpacing(4)

        self.method_label = QtGui.QLabel("")
        self.method_label.setTextFormat(QtCore.Qt.RichText)
        layout.addWidget(self.method_label)

        if self.feature_obj:
            val = self.feature_obj.Size
            self.dist_spin.setValue(val.Value if hasattr(val, 'Value') else val)
        elif self.edges:
            default_d = self._get_default_dist(
                self.edges[0]['edge'], self.edges[0]['obj'].Shape)[0]
            self.dist_spin.setValue(default_d)

        self._update_hint()
        self.dist_spin.valueChanged.connect(lambda v: self._update_hint())

    def _get_default_dist(self, edge, shape):
        try:
            c = edge.Curve
            if hasattr(c, 'Radius') and c.Radius > 0:
                return c.Radius, True
        except Exception:
            pass
        return pd_utils.get_min_adjacent_edge_length(edge, shape), False

    def _update_hint(self):
        d = self.dist_spin.value()
        if self.edges:
            ml = min(ed['min_len'] for ed in self.edges)
            self.method_label.setText(
                f"<span style='color:#228833;'>{tr('OCCT chamfer')}</span>" if d < ml
                else f"<span style='color:#cc8800;'>{tr('Boolean cut (full chamfer)')}</span>")

    def accept(self):
        Gui.Control.closeDialog()
        size = self.dist_spin.value()
        if self.feature_obj:
            self.feature_obj.Size = size
            self.feature_obj.Document.recompute()
        elif self.edges:
            _do_create_chamfer(self.edges, size)

    def reject(self):
        Gui.Control.closeDialog()


def _do_create_chamfer(edges, size):
    doc = App.ActiveDocument
    if not doc:
        return
    edge_objs = edges
    body = edge_objs[0]['body']
    base_obj = edge_objs[0]['obj']
    edge_indices = [ed['idx'] for ed in edge_objs]

    doc.openTransaction("Full Chamfer")
    try:
        if body:
            fp_obj = body.newObject('PartDesign::FeaturePython', 'FullChamfer')
            base_obj.Visibility = False
        else:
            fp_obj = doc.addObject('PartDesign::FeaturePython', 'FullChamfer')
        feature_chamfer.FullChamfer(
            fp_obj, size=size, edge_indices=edge_indices, base_obj=base_obj)
        feature_chamfer.ViewProviderFullChamfer(fp_obj.ViewObject)
        doc.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(fp_obj)
        if body:
            try:
                Gui.ActiveDocument.ActiveView.setActiveObject('pdbody', body)
            except Exception:
                pass
        doc.commitTransaction()
        App.Console.PrintMessage(
            f"FullChamfer: {len(edge_indices)} edges, size: {size:.4f} mm\n")
    except Exception as e:
        doc.abortTransaction()
        QtGui.QMessageBox.critical(None, tr("Chamfer failed"), str(e))
