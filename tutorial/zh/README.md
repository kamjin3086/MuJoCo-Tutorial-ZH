# 中文版教程

这里是对应 `../` 里 13 个英文 notebook 的简体中文版：markdown 全部翻译，**代码 cell 与原文逐字节一致**（由脚本原样复制，未做任何修改），notebook 内不含输出结果。

翻译范围之外的东西保持英文：代码、代码块、行内代码、公式、URL、Colab 徽章、`MjModel`/`mj_step` 这类 API 名与专有名词。

用法和英文版完全相同，kernel 选 `mujoco`：

```powershell
.\..\..\lab.cmd tutorial\zh\00_what_is_mujoco.ipynb
```

## 想改译法或重新生成

译文正文在 `.translate/zh_src/<名字>.txt`（每个 `###CELL n` 对应一个 markdown cell）。改完后在仓库根目录跑：

```powershell
.\.venv\Scripts\python.exe .translate\build.py build   # 重新合成 tutorial\zh\*.ipynb
.\.venv\Scripts\python.exe .translate\build.py check   # 校验：代码一致、代码块/URL/标题/表格行数对等
```

翻译规范与术语表在 `.translate\SPEC.md`。
