# -*- coding: utf-8 -*-
# FullChamfer FeaturePython — parametric chamfer for PartDesign

import FreeCAD as App
import Part
import pd_utils
from i18n import tr


def create_chamfer_cutter(shape, edge_idx, chamfer_dist):
    """构造倒角切割楔体."""
    edge = shape.Edges[edge_idx]
    d = chamfer_dist.Value if hasattr(chamfer_dist, 'Value') else chamfer_dist

    fp = edge.FirstParameter
    lp = edge.LastParameter
    v0 = edge.valueAt(fp)
    v1 = edge.valueAt(lp)
    if v0.distanceToPoint(v1) < 1e-6:
        v1 = edge.valueAt(fp + (lp - fp) / 2.0)

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
    ext = 0.1

    pts_start = [
        v0 - ev * ext,
        v0 + cut0 * (d + 2) - ev * ext,
        v0 + cut1 * (d + 2) - ev * ext,
    ]
    pts_end = [
        v1 + ev * ext,
        v1 + cut0 * (d + 2) + ev * ext,
        v1 + cut1 * (d + 2) + ev * ext,
    ]
    pts_all = pts_start + pts_end

    def mkface(ix):
        poly = Part.makePolygon([pts_all[i] for i in ix] + [pts_all[ix[0]]])
        return Part.Face(Part.Wire(poly))

    fs = [
        mkface([0, 1, 2]), mkface([3, 4, 5]),
        mkface([0, 1, 4, 3]), mkface([0, 2, 5, 3]),
        mkface([1, 2, 5, 4]),
    ]

    shell = Part.makeShell(fs)
    if shell.isNull():
        raise RuntimeError("Cannot create cutter shell")
    solid = Part.makeSolid(shell)
    if solid is None or solid.isNull():
        raise RuntimeError("Cannot create cutter solid")
    return solid


class FullChamfer:
    """FeaturePython Proxy for parametric full chamfer."""

    # Property name mapping: English -> Chinese
    _pn = {'Size': '尺寸', 'EdgeIndices': '边索引', 'BaseFeature': '基特征'}

    def __init__(self, obj, size=0.0, edge_indices=None, base_obj=None):
        # Properties MUST be added before setting Proxy
        if not hasattr(obj, '尺寸'):
            obj.addProperty('App::PropertyLength', '尺寸',
                tr('Chamfer'), tr('Chamfer distance'))
        if not hasattr(obj, '边索引'):
            obj.addProperty('App::PropertyIntegerList', '边索引',
                tr('Chamfer'), tr('Edge indices (0-based)'))
        if not hasattr(obj, '基特征'):
            obj.addProperty('App::PropertyLink', '基特征',
                tr('Chamfer'), tr('Reference to the base feature'))

        obj.Proxy = self
        obj.尺寸 = size
        if edge_indices:
            obj.边索引 = edge_indices
        if base_obj:
            obj.基特征 = base_obj

    def __str__(self):
        return "FullChamfer"

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

        size = obj.尺寸
        edge_indices = obj.边索引
        if size <= 0 or not edge_indices:
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

        if size < min_len:
            try:
                new_shape = base_shape.makeChamfer(size, size, edges)
                if not new_shape.isNull():
                    obj.Shape = new_shape
                    return
            except Exception:
                pass

        cutters = []
        for idx in edge_indices:
            cutter = create_chamfer_cutter(base_shape, idx, size)
            if cutter is None or cutter.isNull():
                raise RuntimeError(f"Edge {idx} cutter construction failed")
            cutters.append(cutter)

        combined = cutters[0]
        for c in cutters[1:]:
            combined = combined.fuse(c)
        result = base_shape.cut(combined)
        if result.isNull():
            raise RuntimeError("Chamfer boolean cut failed")
        obj.Shape = result.removeSplitter()

    def onChanged(self, obj, prop):
        pass


class ViewProviderFullChamfer:
    """ViewProvider for FullChamfer."""

    def __init__(self, vobj):
        vobj.Proxy = self

    def __str__(self):
        return "ViewProviderFullChamfer"

    def dumps(self):
        return None

    def loads(self, state):
        pass

    def getIcon(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'FullChamfer.svg')
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
        import task_chamfer
        import FreeCADGui as Gui
        panel = task_chamfer.ChamferTaskPanel(feature_obj=vobj.Object)
        Gui.Control.showDialog(panel)
        return True
