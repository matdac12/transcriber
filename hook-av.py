"""
PyInstaller hook for PyAV (av module).
Ensures all FFmpeg DLLs and binaries are collected.
"""

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules

# Collect all dynamic libraries (.pyd, .dll) from av package
binaries = collect_dynamic_libs('av')

# Collect all data files
datas = collect_data_files('av')

# Collect all submodules
hiddenimports = collect_submodules('av')
