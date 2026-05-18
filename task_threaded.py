# -*- coding: utf-8 -*-
# ThreadedRod task panel

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtGui
import pd_utils
import feature_threaded
from i18n import tr


def _parse_thread_sizes(sizes):
    result = []
    for s in sizes:
        sl = s.lower()
        if sl.startswith("m") and "x" in sl:
            try:
                parts = sl[1:].split("x")
                d = float(parts[0].strip())
                p = float(parts[1].strip())
                result.append((s, d, p))
            except (ValueError, IndexError):
                continue
    return sorted(result, key=lambda x: x[1])


def _get_coarse_fine_sizes():
    dummy_doc = None
    try:
        dummy_doc = App.newDocument("_ThreadTemp")
        dummy_body = dummy_doc.addObject("PartDesign::Body", "_TmpBody")
        dummy_cyl = dummy_doc.addObject("PartDesign::AdditiveCylinder", "_TmpCyl")
        dummy_cyl.Radius = 10
        dummy_cyl.Height = 10
        dummy_body.addObject(dummy_cyl)
        dummy_sk = dummy_doc.addObject("Sketcher::SketchObject", "_TmpSk")
        dummy_body.addObject(dummy_sk)
        dummy_sk.AttachmentSupport = (dummy_cyl, "Face2")
        dummy_sk.MapMode = "FlatFace"
        dummy_doc.recompute()
        dummy_hole = dummy_doc.addObject("PartDesign::Hole", "_TmpHole")
        dummy_body.addObject(dummy_hole)
        dummy_hole.Profile = dummy_sk
        dummy_hole.Threaded = 1
        dummy_hole.ThreadType = 1
        coarse_sizes = dummy_hole.getEnumerationsOfProperty("ThreadSize")
        dummy_hole.ThreadType = 2
        fine_sizes = dummy_hole.getEnumerationsOfProperty("ThreadSize")
        return _parse_thread_sizes(coarse_sizes), _parse_thread_sizes(fine_sizes)
    finally:
        if dummy_doc:
            try:
                App.closeDocument(dummy_doc.Name)
            except Exception:
                pass


class ThreadedRodTaskPanel:
    def __init__(self, feature_obj=None, face_info=None):
        self.feature_obj = feature_obj
        self.face_info = face_info
        self.coarse_parsed = []
        self.fine_parsed = []
        self.form = QtGui.QWidget()
        self._build_ui()

    def _build_ui(self):
        try:
            self.coarse_parsed, self.fine_parsed = _get_coarse_fine_sizes()
        except Exception:
            self.coarse_parsed, self.fine_parsed = [], []

        layout = QtGui.QVBoxLayout(self.form)

        if self.feature_obj:
            layout.addWidget(QtGui.QLabel(f"<b>{tr('Edit ThreadedRod')}</b>"))
        elif self.face_info:
            layout.addWidget(QtGui.QLabel(
                f"<b>{tr('Threaded Rod')}</b><br>"
                f"{tr('Radius:')} {self.face_info['radius']:.3f} mm<br>"
                f"{tr('Height:')} {self.face_info['height']:.3f} mm"))
        else:
            layout.addWidget(QtGui.QLabel(
                f"<b>{tr('Threaded Rod')}</b><br>"
                f"<span style='color:#cc8800;'>{tr('No cylinder face selected')}</span>"))

        layout.addSpacing(8)

        t = QtGui.QHBoxLayout()
        t.addWidget(QtGui.QLabel(tr("Standard:")))
        self.type_combo = QtGui.QComboBox()
        self.type_combo.addItem(tr("Custom"))
        self.type_combo.addItem("ISO Metric Coarse")
        self.type_combo.addItem("ISO Metric Fine")
        t.addWidget(self.type_combo)
        t.addStretch()
        layout.addLayout(t)

        s = QtGui.QHBoxLayout()
        self.size_label = QtGui.QLabel(tr("Size:"))
        s.addWidget(self.size_label)
        self.size_combo = QtGui.QComboBox()
        self.size_combo.setMinimumWidth(200)
        s.addWidget(self.size_combo)
        s.addStretch()
        layout.addLayout(s)

        self.custom_widget = QtGui.QWidget()
        cl = QtGui.QVBoxLayout()
        cl.setContentsMargins(0, 0, 0, 0)

        d = QtGui.QHBoxLayout()
        d.addWidget(QtGui.QLabel(tr("Nominal dia. (mm):")))
        self.diam_spin = QtGui.QDoubleSpinBox()
        self.diam_spin.setRange(1.0, 300.0)
        self.diam_spin.setDecimals(3)
        self.diam_spin.setSingleStep(0.5)
        d.addWidget(self.diam_spin)
        cl.addLayout(d)

        p = QtGui.QHBoxLayout()
        p.addWidget(QtGui.QLabel(tr("Pitch (mm):")))
        self.pitch_spin = QtGui.QDoubleSpinBox()
        self.pitch_spin.setRange(0.1, 20.0)
        self.pitch_spin.setDecimals(2)
        self.pitch_spin.setSingleStep(0.05)
        p.addWidget(self.pitch_spin)
        cl.addLayout(p)

        self.custom_widget.setLayout(cl)
        layout.addWidget(self.custom_widget)

        l = QtGui.QHBoxLayout()
        l.addWidget(QtGui.QLabel(tr("Thread length (mm):")))
        self.len_spin = QtGui.QDoubleSpinBox()
        self.len_spin.setRange(0.1, 9999.0)
        self.len_spin.setDecimals(2)
        self.len_spin.setSingleStep(1.0)
        l.addWidget(self.len_spin)
        layout.addLayout(l)

        o = QtGui.QHBoxLayout()
        o.addWidget(QtGui.QLabel(tr("Start offset (mm):")))
        self.offset_spin = QtGui.QDoubleSpinBox()
        self.offset_spin.setRange(-9999.0, 9999.0)
        self.offset_spin.setDecimals(2)
        self.offset_spin.setSingleStep(1.0)
        o.addWidget(self.offset_spin)
        layout.addLayout(o)

        h = QtGui.QHBoxLayout()
        h.addWidget(QtGui.QLabel(tr("Direction:")))
        self.handed_combo = QtGui.QComboBox()
        self.handed_combo.addItem(tr("Right-hand (standard)"))
        self.handed_combo.addItem(tr("Left-hand"))
        h.addWidget(self.handed_combo)
        h.addStretch()
        layout.addLayout(h)

        layout.addSpacing(8)

        self._setup_initial_values()

        def on_type_changed(idx):
            if idx == 0:
                self.size_label.setVisible(False)
                self.size_combo.setVisible(False)
                self.custom_widget.setVisible(True)
            elif idx == 1:
                self.size_label.setVisible(True)
                self.size_combo.setVisible(True)
                self.custom_widget.setVisible(False)
                self._set_size_combo(self.coarse_parsed)
            elif idx == 2:
                self.size_label.setVisible(True)
                self.size_combo.setVisible(True)
                self.custom_widget.setVisible(False)
                self._set_size_combo(self.fine_parsed)

        self.type_combo.currentIndexChanged.connect(on_type_changed)

    def _set_size_combo(self, parsed_list, select_d=None):
        self.size_combo.clear()
        for s, d, p in parsed_list:
            self.size_combo.addItem(f"M{d:.0f}\u00d7{p:.2f} (D={d}mm, P={p}mm)")
        if select_d is not None and len(parsed_list) > 0:
            best_i = 0
            best_diff = float('inf')
            for i, (s, d, p) in enumerate(parsed_list):
                diff = abs(d - select_d)
                if diff < best_diff:
                    best_diff = diff
                    best_i = i
            self.size_combo.setCurrentIndex(best_i)

    def _setup_initial_values(self):
        if self.feature_obj:
            obj = self.feature_obj
            nd = obj.NominalDiameter
            pt = obj.Pitch
            self.diam_spin.setValue(nd.Value if hasattr(nd, 'Value') else nd)
            self.pitch_spin.setValue(pt.Value if hasattr(pt, 'Value') else pt)
            tl = obj.ThreadLength
            self.len_spin.setValue(tl.Value if hasattr(tl, 'Value') else tl)
            so = obj.StartOffset
            self.offset_spin.setValue(so.Value if hasattr(so, 'Value') else so)
            self.handed_combo.setCurrentIndex(1 if obj.LeftHanded else 0)

            matched = False
            for i, (s, d, p) in enumerate(self.coarse_parsed):
                nd_v = nd.Value if hasattr(nd, 'Value') else nd
                pt_v = pt.Value if hasattr(pt, 'Value') else pt
                if abs(d - nd_v) < 0.02 and abs(p - pt_v) < 0.02:
                    self.type_combo.setCurrentIndex(1)
                    self._set_size_combo(self.coarse_parsed, d)
                    matched = True
                    break
            if not matched:
                for i, (s, d, p) in enumerate(self.fine_parsed):
                    nd_v = nd.Value if hasattr(nd, 'Value') else nd
                    pt_v = pt.Value if hasattr(pt, 'Value') else pt
                    if abs(d - nd_v) < 0.02 and abs(p - pt_v) < 0.02:
                        self.type_combo.setCurrentIndex(2)
                        self._set_size_combo(self.fine_parsed, d)
                        matched = True
                        break
            if not matched:
                self.type_combo.setCurrentIndex(0)
                self.size_label.setVisible(False)
                self.size_combo.setVisible(False)
                self.custom_widget.setVisible(True)
            return

        if self.face_info:
            radius = self.face_info['radius']
            height = self.face_info['height']
            suggested_d = radius * 2.0
            self.diam_spin.setValue(suggested_d)
            self.len_spin.setValue(height)
            suggested_key, _ = feature_threaded.suggest_thread(radius)
            if suggested_key:
                suggested_d = feature_threaded.METRIC_THREADS[suggested_key][0]
            self.type_combo.setCurrentIndex(1)
            self._set_size_combo(self.coarse_parsed, suggested_d)
            self.custom_widget.setVisible(False)
        else:
            self.diam_spin.setValue(6.0)
            self.pitch_spin.setValue(1.0)
            self.len_spin.setValue(10.0)
            self.type_combo.setCurrentIndex(0)
            self.size_label.setVisible(False)
            self.size_combo.setVisible(False)
            self.custom_widget.setVisible(True)

    def _get_params(self):
        type_idx = self.type_combo.currentIndex()
        if type_idx == 0:
            nom_diameter = self.diam_spin.value()
            pitch = self.pitch_spin.value()
        elif type_idx == 1:
            _, nom_diameter, pitch = self.coarse_parsed[self.size_combo.currentIndex()]
        else:
            _, nom_diameter, pitch = self.fine_parsed[self.size_combo.currentIndex()]
        return {
            'nom_diameter': nom_diameter,
            'pitch': pitch,
            'thread_length': self.len_spin.value(),
            'start_offset': self.offset_spin.value(),
            'left_handed': (self.handed_combo.currentIndex() == 1),
        }

    def accept(self):
        Gui.Control.closeDialog()
        params = self._get_params()
        if self.feature_obj:
            obj = self.feature_obj
            obj.NominalDiameter = params['nom_diameter']
            obj.Pitch = params['pitch']
            obj.ThreadLength = params['thread_length']
            obj.StartOffset = params['start_offset']
            obj.LeftHanded = params['left_handed']
            obj.Document.recompute()
        elif self.face_info:
            _do_create_threaded(self.face_info, params)

    def reject(self):
        Gui.Control.closeDialog()


def _do_create_threaded(face_info, params):
    doc = App.ActiveDocument
    if not doc:
        return
    source_obj = face_info['obj']
    face_name = face_info['face_name']
    body = pd_utils.find_body(source_obj)

    doc.openTransaction("Threaded Rod")
    try:
        # Create cutter body FIRST (before FeaturePython, outside recompute chain)
        cutter_name, cutter_body = feature_threaded.build_cutter_body(
            doc, params['nom_diameter'], params['pitch'],
            params['thread_length'], params['left_handed'])
        cutter_body.Visibility = False
        for o in cutter_body.Group:
            o.Visibility = False

        # Create FeaturePython
        if body:
            fp_obj = body.newObject('PartDesign::FeaturePython', 'ThreadedRod')
            source_obj.Visibility = False
        else:
            fp_obj = doc.addObject('PartDesign::FeaturePython', 'ThreadedRod')
        feature_threaded.ThreadedRod(fp_obj,
            nom_diameter=params['nom_diameter'],
            pitch=params['pitch'],
            thread_length=params['thread_length'],
            left_handed=params['left_handed'],
            start_offset=params['start_offset'],
            source_obj=source_obj, face_name=face_name)
        fp_obj._CutterBodyName = cutter_name
        feature_threaded.ViewProviderThreadedRod(fp_obj.ViewObject)
        doc.recompute()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(fp_obj)
        doc.commitTransaction()
        App.Console.PrintMessage(
            f"ThreadedRod: M{params['nom_diameter']:.0f}x{params['pitch']:.2f}, "
            f"length={params['thread_length']:.2f} mm\n")
    except Exception as e:
        doc.abortTransaction()
        QtGui.QMessageBox.critical(None, tr("Thread failed"), str(e))
