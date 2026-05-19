# -*- coding: utf-8 -*-
# FullChamfer task panel with edge selection

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui, QtCore
import pd_utils
import feature_chamfer
from i18n import tr


def _parse_selection():
    """Parse current selection into edges list."""
    edges = []
    for s in Gui.Selection.getSelectionEx():
        if not hasattr(s.Object, 'Shape'):
            continue
        obj = s.Object
        shape = obj.Shape
        body = pd_utils.find_body(obj)
        for sn in s.SubElementNames:
            if not sn.startswith('Edge'):
                continue
            try:
                idx = int(sn.replace('Edge', '')) - 1
                edge = shape.Edges[idx]
                min_l = pd_utils.get_min_adjacent_edge_length(edge, shape)
                edges.append({
                    'obj': obj, 'body': body, 'sub': sn,
                    'idx': idx, 'min_len': min_l, 'edge': edge,
                })
            except Exception:
                pass
    return edges


class ChamferTaskPanel:
    def __init__(self, feature_obj=None, edges=None):
        self.feature_obj = feature_obj
        self.edges = edges or []
        self._obs = None
        self.form = QtGui.QWidget()
        self._build_ui()

    def _build_ui(self):
        layout = QtGui.QVBoxLayout(self.form)

        title = tr("Edit FullChamfer") if self.feature_obj else tr("Full Chamfer")
        layout.addWidget(QtGui.QLabel(f"<b>{title}</b>"))
        layout.addSpacing(4)

        # Edge selection area
        sel_layout = QtGui.QHBoxLayout()
        sel_layout.addWidget(QtGui.QLabel(tr("Edges:")))
        self.edge_label = QtGui.QLabel("0 " + tr("edge(s)"))
        sel_layout.addWidget(self.edge_label)
        self.sel_btn = QtGui.QPushButton(tr("Select"))
        self.sel_btn.setCheckable(True)
        self.sel_btn.toggled.connect(self._on_sel_toggle)
        sel_layout.addWidget(self.sel_btn)
        layout.addLayout(sel_layout)

        # Edge details
        self.edge_info = QtGui.QLabel("")
        layout.addWidget(self.edge_info)

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

        self.method_label = QtGui.QLabel("")
        self.method_label.setTextFormat(QtCore.Qt.RichText)
        layout.addWidget(self.method_label)

        # Initial values
        if self.feature_obj:
            val = self.feature_obj.Size
            self.dist_spin.setValue(val.Value if hasattr(val, 'Value') else val)
            self._update_edges()
        elif self.edges:
            default_d = self._get_default_dist(
                self.edges[0]['edge'], self.edges[0]['obj'].Shape)[0]
            self.dist_spin.setValue(default_d)
            self._update_edges()

        self._update_hint()
        self.dist_spin.valueChanged.connect(lambda v: self._update_hint())

    def _on_sel_toggle(self, checked):
        if checked:
            Gui.Selection.clearSelection()
            self._obs = Gui.Selection.addObserver(self)
        else:
            self._stop_obs()
            self.edges = _parse_selection()
            self._update_edges()
            self._update_hint()
            if self.edges and not self.feature_obj:
                default_d, _ = self._get_default_dist(
                    self.edges[0]['edge'], self.edges[0]['obj'].Shape)
                self.dist_spin.setValue(default_d)

    def _stop_obs(self):
        if self._obs:
            try:
                Gui.Selection.removeObserver(self._obs)
            except Exception:
                pass
            self._obs = None

    def _update_edges(self):
        cnt = len(self.edges)
        self.edge_label.setText(f"{cnt} {tr('edge(s)')}")
        if self.edges:
            txt = ""
            for i, ed in enumerate(self.edges):
                is_circle = False
                try:
                    c = ed['edge'].Curve
                    is_circle = hasattr(c, 'Radius') and c.Radius > 0
                except Exception:
                    pass
                typ = tr("circle") if is_circle else tr("straight")
                txt += f"{ed['sub']} ({typ})  {tr('min adj len')} {ed['min_len']:.2f}\n"
            self.edge_info.setText(txt)
        else:
            self.edge_info.setText("")

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

    def addSelection(self, doc, obj, sub, pnt):
        if not sub or not sub.startswith("Edge"):
            return
        self.edges = _parse_selection()
        self._update_edges()
        self._update_hint()
        if self.edges and not self.feature_obj:
            default_d, _ = self._get_default_dist(
                self.edges[0]['edge'], self.edges[0]['obj'].Shape)
            self.dist_spin.setValue(default_d)

    def removeSelection(self, doc, obj, sub):
        if not sub or not sub.startswith("Edge"):
            return
        self.edges = _parse_selection()
        self._update_edges()
        self._update_hint()
        if self.edges and not self.feature_obj:
            default_d, _ = self._get_default_dist(
                self.edges[0]['edge'], self.edges[0]['obj'].Shape)
            self.dist_spin.setValue(default_d)

    def accept(self):
        self._stop_obs()
        if not self.feature_obj and not self.edges:
            self.edges = _parse_selection()
        size = self.dist_spin.value()
        Gui.Control.closeDialog()
        if self.feature_obj:
            self.feature_obj.Size = size
            self.feature_obj.Document.recompute()
        elif self.edges:
            _do_create_chamfer(self.edges, size)

    def reject(self):
        self._stop_obs()
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
