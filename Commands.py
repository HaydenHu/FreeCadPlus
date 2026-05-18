# -*- coding: utf-8 -*-
# Commands — entry points for the PartDesign Tools toolbar

import FreeCAD as App
import FreeCADGui as Gui
import pd_utils
import task_chamfer
import task_fillet
import task_threaded
import feature_threaded


class cmdFullChamfer:
    """Command: Full Chamfer on selected edges."""

    def GetResources(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'FullChamfer.svg')
        return {
            'Pixmap': path if os.path.exists(path) else '',
            'MenuText': 'Full Chamfer',
            'ToolTip': 'Create a parametric full chamfer on selected edges',
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            return
        sel = Gui.Selection.getSelectionEx()
        edges = []
        for s in sel:
            if not hasattr(s.Object, 'Shape'):
                continue
            obj = s.Object
            shape = obj.Shape
            body = pd_utils.find_body(obj)
            for sn in s.SubElementNames:
                if sn.startswith('Edge'):
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
        panel = task_chamfer.ChamferTaskPanel(edges=edges)
        Gui.Control.showDialog(panel)


class cmdFullFillet:
    """Command: Full Fillet on selected edges."""

    def GetResources(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'FullFillet.svg')
        return {
            'Pixmap': path if os.path.exists(path) else '',
            'MenuText': 'Full Fillet',
            'ToolTip': 'Create a parametric full fillet on selected edges',
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            return
        sel = Gui.Selection.getSelectionEx()
        edges = []
        for s in sel:
            if not hasattr(s.Object, 'Shape'):
                continue
            obj = s.Object
            shape = obj.Shape
            body = pd_utils.find_body(obj)
            for sn in s.SubElementNames:
                if sn.startswith('Edge'):
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
        panel = task_fillet.FilletTaskPanel(edges=edges)
        Gui.Control.showDialog(panel)


class cmdThreadedRod:
    """Command: Threaded Rod on selected cylindrical face."""

    def GetResources(self):
        import os
        path = os.path.join(os.path.dirname(__file__),
            'Resources', 'icons', 'ThreadedRod.svg')
        return {
            'Pixmap': path if os.path.exists(path) else '',
            'MenuText': 'Threaded Rod',
            'ToolTip': 'Create a parametric external thread on a cylinder',
        }

    def IsActive(self):
        return App.ActiveDocument is not None

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            return
        sel = Gui.Selection.getSelectionEx()
        face_info = None
        for s in sel:
            if not hasattr(s.Object, 'Shape'):
                continue
            for sn in s.SubElementNames:
                if sn.startswith('Face'):
                    try:
                        f = s.Object.Shape.getElement(sn)
                        info = feature_threaded.get_cylindrical_face_info(f)
                        if info:
                            face_info = info
                            face_info['face_name'] = sn
                            face_info['obj'] = s.Object
                            break
                    except Exception:
                        pass
            if face_info:
                break
        panel = task_threaded.ThreadedRodTaskPanel(face_info=face_info)
        Gui.Control.showDialog(panel)
