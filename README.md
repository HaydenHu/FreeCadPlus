# FreeCadPlus

FreeCAD PartDesign 功能增强插件 / Parametric chamfer, fillet, and threaded rod addon.

## 安装 / Install

```bash
cd FreeCAD Mod 目录  # e.g. C:\Users\<user>\AppData\Roaming\FreeCAD\v1-2\Mod
git clone git@github.com:HaydenHu/FreeCadPlus.git
```

重启 FreeCAD，PartDesign 工作台工具栏出现 **FreeCadPlus** 分组。

Restart FreeCAD. The **FreeCadPlus** toolbar appears in the PartDesign workbench.

## 工具 / Tools

| 工具 / Tool | 说明 / Description |
|-------------|---------------------|
| Full Chamfer / 完全倒角 | 选中边倒角。小距离用 OCCT 算法；大距离（完全覆盖）用布尔切割。 |
| Full Fillet / 完全圆角 | 选中边圆角。小半径用 OCCT 算法；大半径（完全覆盖）用布尔切割。 |
| ThreadedRod / 螺丝柱 | 在圆柱面上生成外螺纹。支持 ISO 公制粗牙/细牙或自定义参数。 |

## 使用 / Usage

1. 打开 PartDesign Body，选中一条或多条边（或一个圆柱面）。
2. 点击 **FreeCadPlus** 工具栏上的按钮。
3. 在对话框中设置参数，确认执行。
4. 在树中双击特征可重新编辑参数。
5. 也可在 Data 选项卡中直接修改属性值。

---

1. Open a PartDesign Body, select edges or a cylindrical face.
2. Click a tool in the **FreeCadPlus** toolbar.
3. Set parameters in the dialog and confirm.
4. Double-click the feature in the tree to edit parameters.
5. Properties are also editable in the Data tab.

## 兼容 / Compatibility

FreeCAD 1.2+ / Windows / Linux / macOS

## 许可 / License

MIT
