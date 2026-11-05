# 打印机器人 → MuJoCo 仿真：建模准备清单

## 0. 文档说明

| 项目 | 内容 |
|------|------|
| **适用对象** | 已有实体样机（3D 打印结构 + 舵机），准备在 MuJoCo 中建立可用模型的人 |
| **解决什么** | 把 CAD / 打印件 / 舵机布置图转成**可信**的 MJCF 模型，并给出开工前的输入清单与验收方法 |
| **前置阅读** | [中文教程 06 MJCF 建模](tutorial/zh/06_xml_modeling.ipynb)、[04 执行器与控制](tutorial/zh/04_control.ipynb) |
| **不在范围内** | 纯仿真入门（小球/单摆请读教程）、步态算法实现、RL 训练细节 |
| **版本标注** | 文中"实测"结论基于 MuJoCo 3.17.0（2026-11 验证）；升级大版本后建议重跑 §9 的验证脚本 |

这种"从实体样机反推仿真"的流程，业界一般归入 digital twin / sim-to-real 准备，与本仓库教程那种 XML 字符串起步的入门路径是两条不同的线。可参考的成体系实现：[mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie)（真实机器人模型的组织方式）、[mujoco_playground](https://playground.mujoco.org/assets/playground_technical_report.pdf)（官方 RL 环境流程）。

> **贯穿全文的一条原则**：MuJoCo 极少报错，参数错时它通常只是给出一个看起来合理的错误结果。因此本文档强调"可验证的判据"，而不是"看起来能跑"。

---

## 1. 开工前应确定的 5 项

以下未确定前不建议开始写 XML，返工概率很高：

1. **可动件数量与舵机数量**（决定自由度 `nv`）
2. 每个舵机的**型号与供电电压**（决定扭矩上限，进而决定可驱动的构件尺寸）
3. **脚底材料**与**地面材料**（爬行任务的成败约九成取决于接触与摩擦）
4. **"动作成功"的数值定义**（前进速度、稳定性、打滑率上限）
5. **先开环验证还是直接强化学习**（建议顺序见 §13）

---

## 2. 输入数据清单

| # | 内容 | 必需度 | 状态 |
|---|------|--------|------|
| 1 | 关节表（§5）：每个舵机的轴线方向、原点、机械行程、正方向 | ★★★ | ☐ |
| 2 | 零件质量表（§4）：含舵机、电池、线材及其真实位置 | ★★★ | ☐ |
| 3 | STL：每个可动件一个，已减面、已确认水密 | ★★★ | ☐ |
| 4 | 舵机型号 + 失速扭矩 + 转速 + 电压 | ★★ | ☐ |
| 5 | 脚底材料 / 地面材料（或标注"待标定"） | ★★ | ☐ |
| 6 | 验收判据（§11）+ 所需传感器清单（§8） | ★★ | ☐ |
| 7 | 机体系约定（哪轴朝前、哪轴朝上）与构件父子关系 | ★ | ☐ |

第 1–3 项缺任何一项都无法开始建模；第 4–5 项可先用估计值，但必须在 §11 中登记为待标定项。

---

## 3. 几何准备（打印件 → mesh）

- **每个可动件单独一个 STL**（机身 / 大腿 / 小腿 / 脚分开导出），固定件可合并。STEP 亦可，需先转 STL。
- **单位 mm → m**：STL 常按毫米导出，未换算会使模型大 1000 倍，重力相对变小，表现为动作"又慢又飘"，且**不会报错**。换算后应在查看器中测量高度，与实测尺寸一致。
- **水密且法线朝外**：否则由 mass 推导的惯量会算错（Blender / MeshLab 检查 solid geometry）。
- **减面至数千三角面**：打印件的齿纹、倒角、螺孔对动力学无影响，只增加计算量。
- **接触面用 primitive 而非打印网格**：脚底建议使用 `sphere` / `capsule`，接触稳定、计算快，也更接近真实情况（实际脚底仅少数凸点接触）。外观 mesh 可另挂一个 geom 并设 `contype="0" conaffinity="0"` 使其不参与碰撞。

---

## 4. 零件质量表（模板）

| 零件 | 质量 g | 质心位置（相对本刚体原点） | 数据来源 |
|------|--------|---------------------------|----------|
| 机身 | | | 打印机耗材克数 |
| 大腿 ×N | | | |
| 小腿 ×N | | | |
| 脚 ×N | | | |
| 舵机 ×N | | | 型号规格表 |
| 电池 | | **位置必须写实** | 电子秤 |
| 驱动板 + 线材 | | | |

只需给出每个刚体的 mass，惯量可由 MuJoCo 自动计算（`geom type="mesh"` 配合 `mass`），无需手推惯量张量。**电池位置决定重心**，对稳定性的影响通常大于预期。

---

## 5. 关节表（模板，每个舵机一行）

| 关节名 | 父刚体 | 本刚体 | 类型 | 轴线（机体系） | 原点 pos | 机械行程 | 正方向约定 | 舵机型号 |
|--------|--------|--------|------|----------------|----------|----------|------------|----------|
| hip_yaw_L | body | thigh_L | hinge | 0 0 1 | 0.06 0.03 0 | ±90° | 俯视逆时针为正 | SG90 |
| hip_pitch_L | thigh_L | thigh_L | hinge | 0 1 0 | 0 0.01 -0.02 | −60~30° | | |
| knee_L | thigh_L | shin_L | hinge | 0 1 0 | 0 0 -0.05 | 0~120° | | |

要点：

- **轴线方向写错会导致动作方向相反**。用装配图标注视向与正方向（"从上往下看顺时针为正"）比纯文字描述可靠。
- **机械行程必须写入**（`range`）。缺失会让模型自由度大于真机，仿真"能走"而实机做不到。
- 填完后核对：行数应等于舵机数，且 `model.nv` 应等于舵机数（每舵机 1 自由度）。

---

## 6. 执行器建模：舵机 → `<position>`

舵机是**闭环位置控制**器件，不是力矩电机，因此应使用 `<position>` 执行器：控制量即"目标角度"，与实机控制接口一一对应。

参数换算：

| 规格表项目 | 换算方式 | 用途 |
|------------|----------|------|
| 失速扭矩 `X` kg·cm | `X × 0.0981` = N·m | `forcerange="-T T"` |
| 空载转速 `t` s/60°（标称电压下） | `60/t` °/s，再 `×π/180` 得 rad/s | 角速度上限，反映到 `kv` 与关节 `damping` |
| 机械行程 `a~b`（度） | 需转为**弧度** | `ctrlrange`（见 §9） |

起步写法（示意）：

```xml
<position name="hip_pitch_L" joint="hip_pitch_L"
          ctrlrange="-1.047 0.524"   <!-- -60°~30°，此处为弧度 -->
          forcerange="-0.9 0.9"      <!-- ≈9.2 kg·cm -->
          kp="8" kv="0.6"/>
```

注意事项：

- `kp` 的单位是 **N·m / rad**。
- `<position>` 的速度增益 `kv` **默认为 0**，只写 `kp` 会持续振荡或超调；初始可取 `kv ≈ 0.05~0.1 × kp`，构件越轻，所需 `kv` 相对值越大。
- 舵机的死区与齿隙可用关节侧 `damping="0.05"` `frictionloss="0.05"` 粗略近似。缺省这两项的仿真通常比实机"灵活"得多，导致步态参数无法迁移。

---

## 7. 接触与摩擦起步值

MuJoCo 的 friction 为三段：`sliding torsional rolling`。

| 接触场景 | sliding | torsional | rolling |
|----------|---------|-----------|---------|
| 橡胶 / TPU 脚 on 瓷砖 | 0.9~1.2 | 0.05 | 0.001 |
| PLA 打印脚 on 木地板 | 0.5~0.7 | 0.02 | 0.0005 |
| 泡沫 / 纸胶带脚 on 玻璃 | 0.4~0.6 | 0.01 | 0.0005 |
| **未知，先用此值** | 0.8 | 0.02 | 0.001 |

- `timestep` 从 **0.001** 起步；接触多、结构刚硬的系统在 0.002 以上容易抖动。稳定后再逐步放大以节省时间。
- `solref` / `solimp` 保持默认，仅在地面出现明显"下陷"或"弹跳"时调整。
- **打滑判别**：若实际前进速度远低于腿摆动所对应的理论速度，通常是摩擦不足而非控制问题，应优先增大 friction 再调步态。

---

## 8. 传感器清单（需要闭环或 RL 时）

| 需求 | MJCF 传感器类型 |
|------|-----------------|
| 关节角反馈 | `jointpos` |
| IMU | `accelerometer` + `gyro`（挂在机身 body 上） |
| 触地检测 | `touch` 或 `force`（挂在脚部 site 上）——RL 中几乎必需 |
| 位移（用于判据） | `framepos` 或 `subtreepos` |
| 传感器噪声 | `noise` 属性，建议先设小值再逐步放大 |

---

## 9. 单位与角度约定（MuJoCo 3.17.0 实测）

| 属性写法 | 输入单位 | 内部存储/使用 | 后果 |
|----------|----------|---------------|------|
| `<joint range="-90 90">` | **度** | 弧度（±1.5708） | 正常 |
| `<position ctrlrange="-90 90">` | **不转换**，按弧度处理 | ±90 | 以 `ctrl=90` 表示 90° 时，关节会一路转到约 **3850°**，软限位被顶穿且**不报错** |
| `<position kp="30">` | — | `gainprm[0]=30`，`biasprm=[0,-30,0,…]` | τ = kp·(ctrl−q) − kv·qvel，且 **kv 默认 0** |
| `qpos` / `ctrl` | — | **弧度** | — |

由此得到三条约定：

1. 关节限位用**度**写 `range`，执行器 `ctrlrange` 用**弧度**写，两者数值不同，不可复制粘贴。
2. 每次生成模型后，打印 `model.jnt_range` 与 `model.actuator_ctrlrange` 并人工核对数值区间。
3. 关节限位是**软约束**：被顶穿时表现为 `qpos` 超出 `range`，而非报错或卡死。因此任何仿真过程都应检查 `qpos` 是否越界（§10 第 4 关）。

验证脚本（可独立运行，用于确认当前 MuJoCo 版本的单位行为）：

```python
import math, mujoco
xml = """
<mujoco><worldbody><body name="b" pos="0 0 1">
  <joint name="j" type="hinge" axis="0 1 0" range="-90 90"/>
  <geom type="box" size="0.1 0.02 0.05" mass="0.05"/></body></worldbody>
  <actuator><position name="a" joint="j" ctrlrange="-90 90" kp="30"/></actuator>
</mujoco>"""
m = mujoco.MjModel.from_xml_string(xml); d = mujoco.MjData(m)
print("jnt_range(rad):", m.jnt_range[0], "| ctrlrange:", m.actuator_ctrlrange[0])
d.ctrl[0] = 90.0
for _ in range(3000): mujoco.mj_step(m, d)
print("ctrl=90 -> qpos(deg):", math.degrees(d.qpos[0]))   # 约 3850：软限位被顶穿
```

---

## 10. 验证阶梯（新模型逐级通过，不建议跳级）

| 关卡 | 操作 | 通过判据 |
|------|------|----------|
| 1 结构 | 加载 XML，打印 `nq/nv/nu`、各刚体质量、总质量与重心 | `nv` = 舵机数；总质量与实物称重差 < 10%；重心位于电池附近 |
| 2 静态 | 空仿真 2 s，控制量保持初值 | `qpos/qvel` 变化 < 1e-3，无 NaN |
| 3 落地 | 从略高于地面的初始位姿自由落体 2 s | 静止后不抖动、不陷入地面、不倾倒 |
| 4 单关节 | 每个执行器以梯形指令扫过整个行程 | 能到达目标角、无持续振荡、`qpos` 不越 `range`、不越过 `forcerange` |
| 5 步态前检查 | 全部关节同步小幅摆动 5 s | `data.ncon` 落在预期区间；无构件互相穿透 |

任一关未通过时，不建议开始步态与控制——后续所有异常都会被错误归因。

---

## 11. 验收判据模板（随需求一并交给实现方）

```
功能判据
  - 机体沿 +x 平均速度 ≥ ___ cm/s
  - 10 s 内不倾倒（机体 z 轴与全局 z 轴夹角 < 45°）
  - 净位移 > 0，且后退距离 < ___ cm
  - 单步打滑率 < ___%（触地期间脚的水平位移 / 步长）
数值健康
  - 全程 qpos/qvel 无 NaN/inf
  - timestep 减半重跑，10 s 末状态差 < ___%（数值可信）
  - 无控制输入、无耗散项时，5 s 内 data.energy() 不增加
可迁移性
  - 摩擦 ±30%、质量 ±15%、kp ±20% 随机化后仍满足上述判据（域随机化预检）
交付形式
  - 模型以独立 .xml 文件交付（不内联在代码字符串中）
  - 固定随机种子
  - 判据以断言形式写入代码，失败即报错；仅提交视频不视为通过
```

---

## 12. 常见静默错误（不报错，只给错误结果）

1. STL 未做 mm→m 换算，模型尺寸放大 1000 倍，动作缓慢飘忽
2. `ctrlrange` 按度填写，指令范围达数千度并顶穿软限位（§9）
3. 未设 `kv`，执行器持续振荡，容易被误判为控制算法问题
4. `timestep` 过大，能量缓慢漂移，RL 仍可训练但策略不可用
5. 初始位姿存在穿透，第一步出现"弹飞"，容易被误判为步态问题
6. `contype` / `conaffinity` 配置错误，构件互相穿透但流程仍能跑完
7. 未调用 `mj_forward()` 直接渲染，得到黑屏或几何体堆在原点
8. 网格不水密，惯量计算错误，构件出现异常抖动
9. 电池放在默认原点，重心偏移，静态过关但一动就倒
10. 直接以打印网格作接触面，接触不稳定且与真实脚底不符

---

## 13. 控制路线建议（同一阶段只走一条）

1. **开环定相位步态**（三角波/正弦 + 相位差表，或简单 CPG 振荡器）：先证明机械结构走得动、不打滑。**推荐起点。**
2. **强化学习**（gymnasium + Stable-Baselines3，配合域随机化）：在第 1 步走通后引入，否则不收敛时难以区分是模型问题还是训练问题。
3. MPC 等模型预测控制：涉及多接触切换，不建议作为首个方案。

---

## 14. 任务描述模板（交给实现方 / AI agent）

```
任务：为 3D 打印爬行机器人搭建 MuJoCo 模型，范围限于建模与物理体检，不含训练与步态实现。

输入（已确认）：
- 舵机数 ___，关节明细见下表：<关节表>
- 零件质量表：<质量表>
- STL 文件：<路径列表>，单位已为米
- 舵机型号 ___，失速扭矩 ___ kg·cm，@___ V，空载转速 ___ s/60°
- 脚底材料 ___，地面 ___

硬性要求：
1. 模型存为独立 robot.xml，mesh 放 assets/，不内联在 Python 字符串中
2. 每个舵机使用 <position> 执行器；ctrlrange 以弧度给出；forcerange 使用换算后的 N·m；kv 不得为 0
3. 关节以度写 range；脚底接触使用 sphere/capsule primitive；外观 mesh 设 contype=0 conaffinity=0
4. timestep=0.001；执行器与关节的公共参数集中写在 <default> 中
5. 交付 healthcheck.py，实现本文档 §10 的 5 个关卡并打印结果，任一项失败即抛出异常
6. 打印 nq/nv/nu、总质量、重心、各关节 jnt_range 与 ctrlrange 以供核对

禁止：擅自修改给定数值；使用缺省 kp/kv；留空关节限位。
```

---

## 15. 体检脚本骨架

```python
"""healthcheck.py —— 逐关验证，任一关未通过即抛错"""
import numpy as np, mujoco

M = mujoco.MjModel.from_xml_path("robot.xml")
D = mujoco.MjData(M)

def check_structure(expect_nv, expect_mass):
    assert M.nv == expect_nv, f"nv={M.nv} 期望 {expect_nv}"
    total = mujoco.mj_getTotalmass(M)
    assert abs(total - expect_mass) < 0.1 * expect_mass, f"总质量 {total:.3f} kg 与实物差过大"
    return total

def settle(seconds=2.0):
    mujoco.mj_resetData(M, D)
    for _ in range(int(seconds / M.opt.timestep)):
        mujoco.mj_step(M, D)
        assert np.isfinite(D.qpos).all() and np.isfinite(D.qvel).all(), "出现 NaN/inf"
    return D.qpos.copy(), D.qvel.copy()

def check_limits(seconds=5.0):
    mujoco.mj_resetData(M, D)
    lo, hi = M.jnt_range[:, 0], M.jnt_range[:, 1]
    for i in range(int(seconds / M.opt.timestep)):
        t = i * M.opt.timestep
        D.ctrl[:] = 0.5 * (hi + lo) + 0.3 * (hi - lo) * np.sin(2 * np.pi * 0.5 * t)  # 扫行程
        mujoco.mj_step(M, D)
        if not np.isfinite(D.qpos).all():
            raise AssertionError(f"t={t:.2f}s 出现 NaN")
        if ((D.qpos > hi + 0.05) | (D.qpos < lo - 0.05)).any():
            raise AssertionError(f"t={t:.2f}s qpos 越过软限位: {D.qpos}")
    return {"ncon": D.ncon, "qpos_deg": np.round(np.degrees(D.qpos), 1)}

if __name__ == "__main__":
    print("nq/nv/nu:", M.nq, M.nv, M.nu)
    print("总质量:", check_structure(expect_nv=M.nu, expect_mass=0.6))
    print("ctrlrange:", M.actuator_ctrlrange)
    print("静置 2s:", np.round(settle()[0], 4))
    print("扫行程:", check_limits())
```

---

## 16. 参考资料与工具

- [MuJoCo XML 参考](https://mujoco.readthedocs.io/en/stable/XMLreference.html)（属性权威定义）、[Python 绑定](https://mujoco.readthedocs.io/en/stable/python.html)
- [mujoco_menagerie](https://github.com/google-deepmind/mujoco_menagerie)：参考真实机器人模型的 `<default>` 分层、质量与接触参数写法
- [mujoco_playground](https://playground.mujoco.org/assets/playground_technical_report.pdf)：进入 RL 阶段后参考
- 本地查看器：`python -m mujoco.viewer --mjcf robot.xml`
- 本仓库中文教程对应章节：[06 MJCF 建模](tutorial/zh/06_xml_modeling.ipynb)、[04 执行器与控制](tutorial/zh/04_control.ipynb)、[03 仿真](tutorial/zh/03_simulation.ipynb)、[10 故障排查](tutorial/zh/10_troubleshooting.ipynb)

## 附录 A：Windows 部署相关（与建模无关，仅影响本机可用性）

- 启动 JupyterLab 使用仓库内的 `lab.cmd`，原因与排查过程见 [WINDOWS-NOTES.md](WINDOWS-NOTES.md)
- `MUJOCO_GL` 仅支持 `glfw`，设为 `egl` / `osmesa` 会在 `import mujoco` 时报错
- 需要 GPU 并行仿真时安装 `mujoco-mjx` + `jax`；Windows 上不要安装 `jax[cuda12]`
- mesh 与模型文件名建议使用 ASCII，避免代码页相关的编码问题

---

## 阶段推进清单

- [ ] §1 的 5 项已确定
- [ ] 关节表已填（§5），行数 = 舵机数
- [ ] 零件质量表已填（§4）
- [ ] STL 已减面、确认水密、完成单位换算（§3）
- [ ] 执行器与接触参数已按 §6 / §7 填写
- [ ] 验收判据已填写（§11）
- [ ] `healthcheck.py` 五关全部通过（§10 / §15）
- [ ] 在此之后才开始步态与控制（§13）
