@echo off
rem ==========================================================================
rem  Start JupyterLab with all runtime dirs inside this project.
rem  Needed because this machine refuses writes under %USERPROFILE% / %APPDATA%
rem  for a normal (non-elevated) shell.
rem
rem  Usage:  lab.cmd                                   open the file browser
rem          lab.cmd tutorial\00_what_is_mujoco.ipynb  open one notebook
rem
rem  Deliberately a .cmd, not a .ps1: PowerShell policy here is AllSigned, so an
rem  unsigned .ps1 cannot run. Also keep this file ASCII-only: cmd.exe reads
rem  batch files in the OEM codepage, so UTF-8 comments break line parsing.
rem ==========================================================================
setlocal
set "ROOT=%~dp0"

rem JUPYTER_DATA_DIR is the important one: opening a notebook makes jupyter_server
rem write notebook_secret and nbsignatures.db there, and %APPDATA%\jupyter refuses
rem those writes -> every notebook open fails with "File Load Error: Unhandled error".
set "JUPYTER_DATA_DIR=%ROOT%.jupyter\data"
set "JUPYTER_RUNTIME_DIR=%ROOT%.jupyter\runtime"
set "JUPYTER_CONFIG_DIR=%ROOT%.jupyter\config"
set "IPYTHONDIR=%ROOT%.ipython"
set "MPLCONFIGDIR=%ROOT%.mplcache"

rem On Windows MuJoCo only accepts MUJOCO_GL=glfw (unset gives the same default).
rem egl / osmesa raise RuntimeError at "import mujoco".
set "MUJOCO_GL=glfw"

if not exist "%JUPYTER_DATA_DIR%"    mkdir "%JUPYTER_DATA_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
if not exist "%JUPYTER_CONFIG_DIR%"  mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%IPYTHONDIR%"          mkdir "%IPYTHONDIR%"
if not exist "%MPLCONFIGDIR%"        mkdir "%MPLCONFIGDIR%"

if not exist "%ROOT%.venv\Scripts\jupyter.exe" (
  echo [error] not found: %ROOT%.venv\Scripts\jupyter.exe
  exit /b 1
)

"%ROOT%.venv\Scripts\jupyter.exe" lab %*
