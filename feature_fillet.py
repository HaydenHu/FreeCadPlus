# -*- coding: utf-8 -*-
# FullFillet FeaturePython — parametric fillet for PartDesign

import FreeCAD as App
import Part
import math
import pd_utils
from i18n import tr


def create_fillet_cutter(shape, edge_idx, fillet_radius):
    """构造圆角切割体——截面+extrude 双向拉伸."""
    edge = shape.Edges[edge_idx]
    r = fillet_radius.Value if hasattr(fillet_radius, 'Value') else fillet_radius

    fp = edge.FirstParameter
    lp = edge.LastParameter
    v0 = edge.valueAt(fp)
    v1 = edge.valueAt(lp)
    if v0.distanceToPoint(v1) < 1e-6:
        v1 = edge.valueAt(fp + (lp - fp) / 2.0)
    el = (v1 - v0).Length

    mid_p = (fp + lp) / 2.0
    ev = edge.tangentAt(mid_p)
    ev.normalize()

    adj_faces = pd_utils.get_adjacent_faces(edge, shape)
    normals = []
    for f in adj_faces:
        n = f.normalAt(0.5, 0.5)
        normals.append(n)

    if len(normals) < 2:
        raise RuntimeError("Edge requires at least two adjacent faces")

    n0, n1 = normals[0], normals[1]
    for i, (n, f) in enumerate([(n0, adj_faces[0]), (n1, adj_faces[1])]):
        cntr = f.CenterOfMass
        if n.dot(cntr - v0) < 0:
            normals[i] = -n
    n0, n1 = normals[0], normals[1]

    cut0 = -n0
    cut1 = -n1

    x_dir = cut0 - ev * cut0.dot(ev)
    x_dir.normalize()
    y_dir = cut1 - ev * cut1.dot(ev)
    y_dir.normalize()

    def pt(a, b):
        return v0 + x_dir * a + y_dir * b

    mid_angle = 5 * math.pi / 4
    mid_pt_arc = pt(r + r * math.cos(mid_angle), r + r * math.sin(mid_angle))
    arc = Part.Arc(pt(r, 0), mid_pt_arc, pt(0, r))

    w_edges = [
        Part.makeLine(pt(0, 0), pt(r, 0)),
        arc.toShape(),
        Part.makeLine(pt(0, r), pt(0, 0)),
    ]

    wire = Part.Wire(w_edges)
    face = Part.Face(wire)
    if face.isNull():
        raise RuntimeError("Cannot create cutter face")

    # Check if edge is curved (circular) → use pipe sweep, otherwise straight extrude
    try:
        c = edge.Curve
        is_circ = hasattr(c, 'Radius') and c.Radius > 0
    except Exception:
        is_circ = False

    if is_circ:
        path = Part.Wire([edge])
        section_wire = Part.Wire(w_edges)
        try:
            builder = Part.BRepOffsetAPI.MakePipeShell(path)
            builder.add(section_wire, False, True)
            builder.build()
            pipe = builder.shape()
            if pipe and not pipe.isNull():
                solid = Part.makeSolid(pipe) if pipe.ShapeType != 'Solid' else pipe
                if solid and not solid.isNull():
                    return solid.removeSplitter()
        except Exception as e:
            App.Console.PrintWarning(f"FullFillet makePipeShell failed: {e}\n")
        # fallback to straight extrusion
        sweep = face.extrude(ev * el)
        return sweep


class FullFillet:
    """FeaturePython Proxy for parametric full fillet."""

    def __init__(self, obj, radius=0.0, edge_indices=None, base_obj=None):
        # Properties MUST be added before setting Proxy
        if not hasattr(obj, '半径'):
            obj.addProperty('App::PropertyLength', '半径',
                tr('Fillet'), tr('Fillet radius'))
        if not hasattr(obj, '边索引'):
            obj.addProperty('App::PropertyIntegerList', '边索引',
                tr('Fillet'), tr('Edge indices (0-based)'))
        if not hasattr(obj, '基特征'):
            obj.addProperty('App::PropertyLink', '基特征',
                tr('Fillet'), tr('Reference to the base feature'))

        obj.Proxy = self
        obj.半径 = radius
        if edge_indices:
            obj.边索引 = edge_indices
        if base_obj:
            obj.基特征 = base_obj

    def __str__(self):
        return "FullFillet"

    def dumps(self):
        return None

    def loads(self, state):
        pass

    def execute(self, obj):
        if obj.基特征 is None:
            return
        base_feat = obj.基特征
        if not hasattr(base_feat, 'Shape') or base_feat.Shape.isNull():
            return

        radius = obj.半径
        edge_indices = obj.边索引
        if radius <= 0 or not edge_indices:
            return

        base_shape = base_feat.Shape
        edges = []
        for idx in edge_indices:
            if 0 <= idx < len(base_shape.Edges):
                edges.append(base_shape.Edges[idx])
        if not edges:
            return

        min_len = min(pd_utils.get_min_adjacent_edge_length(e, base_shape)
                      for e in edges)
        if radius <= min_len:
            try:
                new_shape = base_shape.makeFillet(radius, edges)
                if not new_shape.isNull():
                    obj.Shape = new_shape
                    return
            except Exception:
                pass

        cutters = []
        for idx in edge_indices:
            cutter = create_fillet_cutter(base_shape, idx, radius)
            if cutter is None or cutter.isNull():
                raise RuntimeError(f"Edge {idx} cutter construction failed")
            cutters.append(cutter)

        combined = cutters[0]
        for c in cutters[1:]:
            combined = combined.fuse(c)
        result = base_shape.cut(combined)
        if result.isNull():
            raise RuntimeError("Fillet boolean cut failed")
        obj.Shape = result.removeSplitter()

    def onChanged(self, obj, prop):
        pass


class ViewProviderFullFillet:
    """ViewProvider for FullFillet."""

    def __init__(self, vobj):
        vobj.Proxy = self

    def __str__(self):
        return "ViewProviderFullFillet"

    def dumps(self):
        return None

    def loads(self, state):
        pass

    def getIcon(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'FullFillet.svg')
        if os.path.exists(path):
            return path
        return ''

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
        import task_fillet
        import FreeCADGui as Gui
        panel = task_fillet.FilletTaskPanel(feature_obj=vobj.Object)
        Gui.Control.showDialog(panel)
        return True
