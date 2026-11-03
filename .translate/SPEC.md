# 中文翻译规范（MuJoCo 教程 notebook）

任务：把 `tutorial/*.ipynb` 里 **markdown cell** 的英文文案对等翻译成简体中文，输出到 `.translate/zh_src/<原文件名>.txt`。代码 cell 由脚本原样复制，不需要你处理。

## 输出文件格式（严格遵守，否则脚本会拒绝）

```
###CELL 0
第一格翻译内容……

###CELL 2
第三格翻译内容……
```

- 每个 cell 一段，起始行是 `###CELL <n>`，`<n>` 必须和 `.translate/en/<name>.txt` 里给出的编号**完全一致**。
- 源文件里出现的每一个编号都要出现，且只出现一次；不多不少，顺序一致。
- 块内容就是翻译后的 markdown 正文，段首段尾空行会被脚本裁掉，其余按原样使用。
- 不要在翻译里加"以下是翻译""注："之类的元话，不要加代码围栏把整段包起来。
- 文件用 UTF-8。

## 对等要求（这是翻译的质量标准）

1. **结构完全对应**：标题层级（`#`/`##`/`###`）、列表与缩进、表格行列、粗体/斜体、引用块、`---` 分隔线的数量与位置一一对应。表格只译单元格文字，列数不变。
2. **代码跨度与代码块不动**：单反引号包裹的 `` `mj_step` ``、`` `data.qpos` `` 原样保留；markdown 里的 ``` 围栏代码块**整块一字不改**（包括其中的英文注释、注释掉的示例）。
3. **链接**：URL、锚点原样不动；显示文本可译（如 `[docs]` → `[文档]`）。徽章图片语法 `![...](...)` 整行不动。
4. **不增不删**：不添加解释性补充，不省略原文句子，不合并段落。原文有的示例、类比、警告全部译出。语气保持原文的直接、口语化。
5. **数字、单位、公式、emoji、标点占位保持**；中英文之间加空格；中文句子里用全角标点（，。：；！？“”），但代码跨度内保持半角。
6. 保留英文不译的东西：MuJoCo、MJX、MJCF、JAX、Gymnasium、Colab、LQR、Riccati、PD、PID、IMU、GPU、CPU、API、XML、DoF 等专有名词与缩写；所有函数名、类名、XML 属性名、报错文本原文。

## 术语表（统一用这些译法，首次出现时用"中文（英文）"格式）

| 英文 | 译法 |
|---|---|
| model / `MjModel` | 模型；`MjModel` 保留 |
| state / `MjData` | 状态；`MjData` 保留 |
| blueprint / snapshot | 蓝图 / 快照（原文的比喻，照译） |
| body | 刚体（body） |
| geom | 几何体（geom） |
| joint | 关节（joint） |
| actuator | 执行器（actuator） |
| site | 标记点（site） |
| worldbody | `worldbody`（保留） |
| free joint | 自由关节（free joint） |
| slide / hinge joint | 滑动关节 / 旋转关节 |
| generalized coordinates | 广义坐标（`qpos`/`qvel`） |
| generalized velocity | 广义速度 |
| DoF | 自由度（DoF） |
| timestep | 仿真步长（timestep） |
| forward dynamics | 正向动力学 |
| inertia | 惯性 |
| damping / stiffness / frictionloss | 阻尼 / 刚度 / 摩擦损耗 |
| contact / collision | 接触 / 碰撞 |
| contact forces | 接触力 |
| solvers / constraint solver | 约束求解器 |
| Jacobian | 雅可比（Jacobian） |
| actuator transmission | 执行器传动（transmission） |
| impedance control | 阻抗控制 |
| operational space control | 操作空间控制 |
| task space | 任务空间 |
| inverse kinematics (IK) | 逆运动学（IK） |
| damped least squares | 阻尼最小二乘 |
| PD control / gains | PD 控制 / 增益 |
| swing-up | 起摆（swing-up） |
| hopper | 弹跳机器人（hopper） |
| trajectory | 轨迹 |
| domain randomization | 域随机化 |
| offscreen rendering / headless | 离屏渲染 / 无头模式 |
| viewer | 查看器（viewer） |
| camera | 相机 |
| sensor | 传感器 |
| ground truth | 真值 |
| Kalman filter | 卡尔曼滤波 |
| noise | 噪声 |
| state estimation | 状态估计 |
| environment / observation / action / reward | 环境 / 观测 / 动作 / 奖励 |
| episode | 回合（episode） |
| policy | 策略 |
| callback | 回调（callback） |
| checkpoint | 检查点 |
| MJX / `vmap` / JIT | 保留英文 |
| Menagerie | Menagerie（保留） |

## 自查（提交前）

- 编号齐全、无重复、无多余。
- 数一下原文和译文的 `#` 标题数、表格行数、`![]()`、`[]()` 是否一致。
- 每个 ``` 代码块逐字符与原文相同（含空行）。
- 中文正文里没混进未翻译的整句英文。
