# Windows 环境备忘（本机实测记录）

实测机器：Windows，PowerShell 执行策略 `AllSigned`，`.venv` = Python 3.11.3。

## 1. 启动方式：用 `lab.cmd`，不要用 `jupyter lab` 直接开

```powershell
.\lab.cmd tutorial\00_what_is_mujoco.ipynb
```

kernel 选 **mujoco**（spec 在 `.venv\share\jupyter\kernels\mujoco`，指向 `.venv\Scripts\python.exe`）。

`lab.cmd` 做了三件事：把 Jupyter/IPython/matplotlib 的运行期目录全部指到项目内、设 `MUJOCO_GL=glfw`、调用 venv 内的 jupyter。必须是 `.cmd`：本机策略 AllSigned，未签名 `.ps1` 无法运行；文件也必须保持 ASCII，`cmd.exe` 按 OEM 代码页读批处理，UTF-8 注释会把行解析打碎。

重定向出来的目录（已在 `.gitignore` 里）：`.jupyter\data`、`.jupyter\runtime`、`.jupyter\config`、`.ipython`、`.mplcache`。其中 `.jupyter\data`（即 `JUPYTER_DATA_DIR`）是关键，见下一节。

## 2. 为什么必须重定向：普通 shell 在用户目录里写不进去

已证实的现象：

- `New-Item` 建 `%APPDATA%\jupyter\runtime` → `[WinError 5] 拒绝访问`；`jupyter lab` 启动即死在 `runtime_dir`
- 内核启动时建 `C:\Users\User\.ipython\profile_default` → 同样被拒，表现为 `Kernel died before replying to kernel_info`
- **打开 notebook 报 `File Load Error: Unhandled error`，服务端是 500**。回溯链很具体：
  `GET /api/contents/<nb>.ipynb` → `mark_trusted_cells` → `NotebookNotary.check_signature` → `secret` 默认值 → `_write_secret_file`
  → `PermissionError: [Errno 13] Permission denied: 'C:\Users\User\AppData\Roaming\jupyter\notebook_secret'`
  （同一请求里 `nbsignatures.db` 也打不开，服务器降级成内存签名库并警告 "Failed committing signatures database to disk"）

关键点：`notebook_secret` 和 `nbsignatures.db` 都在 **`JUPYTER_DATA_DIR`（默认 `%APPDATA%\jupyter`）** 下，`JUPYTER_RUNTIME_DIR` / `JUPYTER_CONFIG_DIR` 管不到它。所以只重定向 runtime/config 的 `lab.cmd` 能让服务器起来，却一打开 notebook 就 500。现在 `JUPYTER_DATA_DIR` 也指到 `.jupyter\data`，同一个请求从 **500 变 200**（实测），`notebook_secret`、`nbsignatures.db` 落在 `.jupyter\data\`。

已排除的原因（两次独立读取，均无改动）：

- DACL 干净：`C:\Users\User`、`AppData`、`AppData\Roaming`、`...\jupyter`、`...\jupyter\kernels\mujoco`、`kernel.json` 上当前用户都是 `FullControl`（继承），**没有任何 deny 项**
- 权限检查脚本判定 `NOT_THIS_CLASS`，`FIXED=0`（报告：`.acl-recovery\acl-report-*.jsonl`）

即拦截发生在 DACL 之外。一个耐人寻味的细节：同一台机器上，提权进程能在 `%APPDATA%\jupyter` 里正常创建 `probe.txt`，却写不出 `notebook_secret`，SQLite 也提交失败 —— 指向安全软件按文件名/进程行为做的防护，而不是文件系统权限配置。想根治就把 `%APPDATA%\jupyter`、`C:\Users\User\.ipython` 或 venv 的 `python.exe` 加入防护软件白名单，之后就不再需要 `lab.cmd`。

## 3. `MUJOCO_GL`：Windows 只认 `glfw`

实测：不设置或 `glfw` → `mujoco.Renderer` 正常出图；`egl` / `osmesa` → `import mujoco` 直接 `RuntimeError: invalid value for environment variable MUJOCO_GL: egl`。

因此本仓库原来的 `scripts/test_examples.py`（硬编码 `MUJOCO_GL="egl"`）在 Windows 上**一条 example 都测不了**，已改为按平台选择：

```python
os.environ.setdefault("MUJOCO_GL", "glfw" if sys.platform == "win32" else "egl")
```

同理，教程 notebook 里 `10_troubleshooting.ipynb` 关于 "设 `MUJOCO_GL=egl`" 的建议在 Windows 上不要照抄。

## 4. 冒烟测试结果：14 通过 / 3 失败 / 1 跳过

`python scripts\test_examples.py`（修完 GL 后）：

```
Results: 14 passed, 3 failed, 1 skipped
```

`tutorial\00_what_is_mujoco.ipynb` 已用 `mujoco` kernel 无头执行通过（含 Renderer + mediapy 视频，退出码 0），所以 notebook 主链路在这台机器上是通的。

### 3 个失败是仓库自身的 bug，与你的环境无关

| 文件 | 现象 | 原因与修法 |
|---|---|---|
| `examples/record_playback.py:112,115` | `PermissionError: '/tmp/demo_trajectory.npz'` | 硬编码 POSIX 路径。改成 `pathlib.Path(tempfile.gettempdir())/"demo_trajectory.npz"` 或直接写到项目内 |
| `examples/operational_space_control.py:74` | `MjData object has no attribute 'qM'` | MuJoCo 3.17 里 `MjData.qM` 已不存在，字段叫 `M`，且签名变成 `mj_fullM(model, data, dst)`。改成 `mujoco.mj_fullM(model, data, M)` |
| `examples/impedance_control.py:80` | `could not broadcast (3,) into (2,)` | 障碍物的 `<joint type="slide">` 也被算进 `nv`，于是 `nv=3` 而 `nu=2`。改成 `np.clip(tau[:model.nu], -100, 100)` |

`menagerie_robot.py` 报 OK 但实际没测到东西：需要先 `git clone https://github.com/google-deepmind/mujoco_menagerie`（放在仓库同级或按脚本里的相对路径）。
`mjx_parallel.py` 被脚本主动跳过。

## 5. 想做 MJX（第 07 章）再装

```powershell
pip install mujoco-mjx jax
```

**不要**照 notebook 里的 `jax[cuda12]` 装——Windows 上没有对应的 CUDA wheel，GPU 版 MJX 需要 WSL。CPU 版 `jax` 可以直接跑。

## 6. 每个 notebook 开头都有 `!pip install ...` cell

在 venv kernel 里跑是幂等的（已装的会跳过），只是浪费时间；07 的那个 cell 会试图装 `jax[cuda12]`，见上一条。
