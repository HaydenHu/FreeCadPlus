# -*- coding: utf-8 -*-
# ThreadedRod FeaturePython — parametric external thread for PartDesign

import FreeCAD as App
import Part
from FreeCAD import Vector
import math

METRIC_THREADS = {
    "M2":   (2.0,  0.40),  "M2.5": (2.5,  0.45),  "M3":   (3.0,  0.50),
    "M4":   (4.0,  0.70),  "M5":   (5.0,  0.80),  "M6":   (6.0,  1.00),
    "M8":   (8.0,  1.25),  "M10":  (10.0, 1.50),  "M12":  (12.0, 1.75),
    "M14":  (14.0, 2.00),  "M16":  (16.0, 2.00),  "M18":  (18.0, 2.50),
    "M20":  (20.0, 2.50),  "M22":  (22.0, 2.50),  "M24":  (24.0, 3.00),
    "M27":  (27.0, 3.00),  "M30":  (30.0, 3.50),  "M33":  (33.0, 3.50),
    "M36":  (36.0, 4.00),  "M39":  (39.0, 4.00),  "M42":  (42.0, 4.50),
    "M45":  (45.0, 4.50),  "M48":  (48.0, 5.00),  "M52":  (52.0, 5.00),
    "M56":  (56.0, 5.50),  "M60":  (60.0, 5.50),  "M64":  (64.0, 6.00),
    "M68":  (68.0, 6.00),
}


def get_cylindrical_face_info(face):
    surf = face.Surface
    if not hasattr(surf, 'Radius'):
        return None
    radius = surf.Radius
    center = surf.Center
    axis = surf.Axis.normalize()
    verts = [v.Point for v in face.Vertexes]
    if len(verts) < 2:
        return None
    projections = [axis.dot(v - center) for v in verts]
    min_p = min(projections)
    max_p = max(projections)
    height = max_p - min_p
    if height < 0.001:
        return None
    return {
        'radius': radius, 'axis': axis, 'height': height,
        'axis_start': center + axis * min_p,
        'axis_end': center + axis * max_p,
    }


def suggest_thread(radius):
    best_key = None
    best_diff = float('inf')
    for key, (nom_d, pitch) in METRIC_THREADS.items():
        diff = abs(nom_d / 2.0 - radius)
        if diff < best_diff:
            best_diff = diff
            best_key = key
    if best_diff < radius * 0.3:
        return best_key, best_diff
    return None, best_diff


def _get_thread_size_index(hole_obj, thread_type, nom_d, pitch):
    hole_obj.ThreadType = thread_type
    sizes = hole_obj.getEnumerationsOfProperty("ThreadSize")
    best = None
    best_score = float('inf')
    for s in sizes:
        sl = s.lower()
        if sl.startswith("m") and "x" in sl:
            try:
                parts = sl[1:].split("x")
                d = float(parts[0].strip())
                p = float(parts[1].strip())
                if abs(d - nom_d) < 0.02:
                    score = abs(p - pitch)
                    if score < best_score:
                        best_score = score
                        best = s
            except (ValueError, IndexError):
                continue
    if best:
        return sizes.index(best)
    return None


def build_cutter_body(doc, nom_diameter, pitch, thread_length, handedness):
    """Build a thread cutter body. Returns (name, body)."""
    cutter_radius = nom_diameter / 2.0 + max(pitch * 2, 5.0)
    body = doc.addObject("PartDesign::Body", "_ThreadCutterBody")
    body.Label = ""

    cyl = doc.addObject("PartDesign::AdditiveCylinder", "_CutterBase")
    cyl.Label = ""
    cyl.Radius = cutter_radius
    cyl.Height = thread_length
    cyl.Angle = 360
    body.addObject(cyl)
    doc.recompute()

    import Sketcher
    face_name = "Face2"
    for i, f in enumerate(cyl.Shape.Faces):
        try:
            d_info = f.distToShape(Part.Vertex(Vector(0, 0, thread_length)))
            if abs(d_info[0]) < 0.01:
                face_name = "Face{}".format(i + 1)
                break
        except Exception:
            continue

    sketch = doc.addObject("Sketcher::SketchObject", "_CutterSketch")
    sketch.Label = ""
    body.addObject(sketch)
    sketch.AttachmentSupport = (cyl, face_name)
    sketch.MapMode = "FlatFace"
    doc.recompute()

    geo_list = [Part.Circle()]
    geo_list[0].Radius = nom_diameter / 2.0
    sketch.addGeometry(geo_list, False)
    sketch.addConstraint(Sketcher.Constraint("Coincident", 0, 3, -1, 1))
    doc.recompute()

    hole = doc.addObject("PartDesign::Hole", "_CutterHole")
    hole.Label = ""
    body.addObject(hole)
    hole.Profile = sketch
    hole.Diameter = nom_diameter
    hole.Depth = thread_length + pitch * 1.5
    hole.DepthType = 0
    hole.DrillPoint = 0
    hole.Threaded = 1
    hole.ModelThread = 1
    hole.ThreadDepthType = 0
    hole.ThreadDirection = 1 if handedness else 0
    hole.ThreadClass = 0
    hole.HoleCutType = 0
    hole.Tapered = 0
    hole.Reversed = 0
    hole.Refine = True

    idx = _get_thread_size_index(hole, 1, nom_diameter, pitch)
    if idx is not None:
        hole.ThreadType = 1
        hole.ThreadSize = idx
    else:
        idx = _get_thread_size_index(hole, 2, nom_diameter, pitch)
        if idx is not None:
            hole.ThreadType = 2
            hole.ThreadSize = idx
        else:
            sizes_str = ", ".join(hole.getEnumerationsOfProperty("ThreadSize")[:10])
            raise RuntimeError(
                f"Cannot find matching thread size for M{nom_diameter:.0f}x{pitch:.2f}."
                f" Available: {sizes_str}")

    doc.recompute()
    return body.Name, body


class ThreadedRod:
    """FeaturePython Proxy for parametric threaded rod."""

    def __init__(self, obj, nom_diameter=6.0, pitch=1.0, thread_length=10.0,
                 left_handed=False, start_offset=0.0,
                 source_obj=None, face_name=None):
        if not hasattr(obj, 'NominalDiameter'):
            obj.addProperty('App::PropertyLength', 'NominalDiameter',
                'Thread', 'Nominal thread diameter')
        if not hasattr(obj, 'Pitch'):
            obj.addProperty('App::PropertyLength', 'Pitch',
                'Thread', 'Thread pitch')
        if not hasattr(obj, 'ThreadLength'):
            obj.addProperty('App::PropertyLength', 'ThreadLength',
                'Thread', 'Thread length')
        if not hasattr(obj, 'LeftHanded'):
            obj.addProperty('App::PropertyBool', 'LeftHanded',
                'Thread', 'Left-handed thread')
        if not hasattr(obj, 'StartOffset'):
            obj.addProperty('App::PropertyFloat', 'StartOffset',
                'Thread', 'Start offset. Negative = inward')
        if not hasattr(obj, 'BaseCylinder'):
            obj.addProperty('App::PropertyLink', 'BaseCylinder',
                'Thread', 'Object with cylindrical face')
        if not hasattr(obj, 'CylinderFace'):
            obj.addProperty('App::PropertyString', 'CylinderFace',
                'Thread', 'Cylindrical face name')
        if not hasattr(obj, '_CutterBodyName'):
            obj.addProperty('App::PropertyString', '_CutterBodyName',
                'Internal', 'Cutter body')._CutterBodyName = ''

        obj.Proxy = self
        obj.NominalDiameter = nom_diameter
        obj.Pitch = pitch
        obj.ThreadLength = thread_length
        obj.LeftHanded = left_handed
        obj.StartOffset = start_offset
        if source_obj:
            obj.BaseCylinder = source_obj
        if face_name:
            obj.CylinderFace = face_name
        obj._CutterBodyName = ''

    def __str__(self):
        return "ThreadedRod"

    def dumps(self):
        return None

    def loads(self, state):
        pass

    def execute(self, obj):
        if obj.BaseCylinder is None or not obj.CylinderFace:
            return

        source_obj = obj.BaseCylinder
        if not hasattr(source_obj, 'Shape'):
            return

        try:
            face = source_obj.Shape.getElement(obj.CylinderFace)
        except Exception:
            return

        cyl_info = get_cylindrical_face_info(face)
        if not cyl_info:
            return

        doc = obj.Document
        nom_d = obj.NominalDiameter
        pitch = obj.Pitch
        thread_length = obj.ThreadLength
        start_offset = obj.StartOffset

        # Get or create cutter body ONCE (creation already happened in task panel)
        existing_name = obj._CutterBodyName
        cutter_body = doc.getObject(existing_name) if existing_name else None

        if cutter_body is None:
            obj._CutterBodyName = ''
            return

        # Position the cutter body
        axis = cyl_info['axis']
        start_pt = cyl_info['axis_start']
        z_axis = Vector(0, 0, 1)

        placement = App.Placement()
        placement.Base = start_pt + axis * start_offset

        if abs(axis.dot(z_axis) - 1.0) > 1e-7:
            rot_axis = z_axis.cross(axis)
            if rot_axis.Length > 1e-7:
                rot_axis.normalize()
                ang = math.acos(z_axis.dot(axis))
                placement.Rotation = App.Rotation(rot_axis, math.degrees(ang))

        twist = App.Rotation(axis, 37.5)
        placement.Rotation = twist.multiply(placement.Rotation)
        cutter_body.Placement = placement

        # Boolean cut with the source object's shape
        result_shape = source_obj.Shape.cut(cutter_body.Shape)
        if result_shape is None or result_shape.isNull():
            raise RuntimeError("Boolean cut failed. Check thread diameter.")

        obj.Shape = result_shape
        obj.Label = f"ThreadedRod_M{nom_d:.0f}x{pitch:.2f}"

    def onChanged(self, obj, prop):
        pass


class ViewProviderThreadedRod:
    def __init__(self, vobj):
        vobj.Proxy = self

    def __str__(self):
        return "ViewProviderThreadedRod"

    def dumps(self):
        return None

    def loads(self, state):
        pass

    def getIcon(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'ThreadedRod.svg')
        return path if os.path.exists(path) else ''

    def attach(self, vobj):
        self.Object = vobj.Object

    def claimChildren(self):
        return []

    def onDelete(self, vobj, subelements):
        return True

    def doubleClicked(self, vobj):
        self.edit(vobj)
        return True

    def edit(self, vobj):
        import task_threaded
        import FreeCADGui as Gui
        panel = task_threaded.ThreadedRodTaskPanel(feature_obj=vobj.Object)
        Gui.Control.showDialog(panel)
        return True
