# -*- coding: utf-8 -*-
# Simple i18n module for FreeCadPlus

import FreeCAD as App

_zh = {
    "Full Chamfer": "完全倒角",
    "Create a parametric full chamfer on selected edges": "对选中边创建参数化完全倒角",
    "Full Fillet": "完全圆角",
    "Create a parametric full fillet on selected edges": "对选中边创建参数化完全圆角",
    "Threaded Rod": "螺丝柱",
    "Create a parametric external thread on a cylinder": "在圆柱面上创建参数化外螺纹",
    "Selected": "已选中",
    "edge(s)": "条边",
    "Chamfer distance (mm):": "倒角距离 (mm):",
    "Fillet radius (mm):": "圆角半径 (mm):",
    "OCCT chamfer": "OCCT 倒角算法",
    "Boolean cut (full chamfer)": "布尔切割 (完全倒角)",
    "Chamfer failed": "倒角失败",
    "Fillet failed": "圆角失败",
    "Thread failed": "螺纹失败",
    "Standard:": "标准:",
    "Custom": "自定义",
    "Size:": "规格:",
    "Nominal dia. (mm):": "公称外径 (mm):",
    "Pitch (mm):": "螺距 (mm):",
    "Thread length (mm):": "螺纹长度 (mm):",
    "Start offset (mm):": "起始偏移 (mm):",
    "Direction:": "旋向:",
    "Right-hand (standard)": "右旋 (标准)",
    "Left-hand": "左旋",
    "No cylinder face selected": "未选中圆柱面",
    "Edit FullChamfer": "编辑完全倒角",
    "Edit FullFillet": "编辑完全圆角",
    "Edit ThreadedRod": "编辑螺丝柱",
    "Edge parameters:": "边参数:",
    "circle": "圆边",
    "straight": "直边",
    "default": "默认",
    "min adj len": "最小邻边长",
    "FullChamfer": "完全倒角",
    "FullFillet": "完全圆角",
    "ThreadedRod": "螺丝柱",
    "Radius:": "半径:",
    "Height:": "高度:",
    "Threaded Rod": "螺丝柱",
}


def _is_chinese():
    try:
        loc = App.getLocale()
        return loc and loc.lower().startswith("zh")
    except Exception:
        return False


def tr(text):
    if _is_chinese() and text in _zh:
        return _zh[text]
    return text
