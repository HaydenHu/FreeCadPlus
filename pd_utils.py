# -*- coding: utf-8 -*-
# Shared utility functions for PartDesignTools

import Part


def find_body(obj):
    """查找特征所属的 PartDesign Body."""
    if obj.TypeId == 'PartDesign::Body':
        return obj
    for p in obj.InList:
        if p.TypeId == 'PartDesign::Body':
            return p
    try:
        g = obj.getParentGroup()
        if g and g.TypeId == 'PartDesign::Body':
            return g
    except Exception:
        pass
    return None


def get_tip(body):
    """获取 Body 的 Tip feature."""
    if hasattr(body, 'Tip') and body.Tip:
        return body.Tip
    for o in reversed(body.Group):
        if hasattr(o, 'Shape') and not o.Shape.isNull():
            return o
    return None


def get_adjacent_faces(edge, shape):
    """获取包含此边的所有面."""
    mid_p = (edge.FirstParameter + edge.LastParameter) / 2.0
    mid_pt = edge.valueAt(mid_p)
    faces = []
    for f in shape.Faces:
        try:
            d, _, _ = f.distToShape(Part.Vertex(mid_pt))
            if d < 1e-6:
                faces.append(f)
        except Exception:
            pass
    return faces


def edges_same(e1, e2, tol=1e-6):
    """判断两条边是否是同一条."""
    mid1 = (e1.FirstParameter + e1.LastParameter) / 2.0
    mid2 = (e2.FirstParameter + e2.LastParameter) / 2.0
    if e1.valueAt(mid1).distanceToPoint(e2.valueAt(mid2)) > tol:
        return False
    return abs(e1.Length - e2.Length) < tol


def get_min_adjacent_edge_length(selected_edge, shape):
    """获取选中边的最小邻边长."""
    min_len = float('inf')
    for face in get_adjacent_faces(selected_edge, shape):
        for other_edge in face.Edges:
            if edges_same(other_edge, selected_edge):
                continue
            L = other_edge.Length
            if L > 1e-7 and L < min_len:
                min_len = L
    return min_len if min_len != float('inf') else 0.0
