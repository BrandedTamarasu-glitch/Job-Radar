# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Job Radar.

Build with: pyinstaller job-radar.spec --clean
Output: dist/job-radar/ (onedir bundle)
"""

import sys
from pathlib import Path

project_root = Path('.').resolve()

# Data files to bundle (source_path, dest_folder_in_bundle)
# Profile template so users have a starting point
added_files = [
    (str(project_root / 'profiles' / '_template.json'), 'profiles'),
]

# Add CustomTkinter theme assets (if installed)
try:
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent
    added_files.append((str(ctk_path / 'assets'), 'customtkinter/assets'))
except ImportError:
    pass  # CustomTkinter not installed - skip bundling assets

# Hidden imports: modules that PyInstaller's static analysis misses
# because they are imported dynamically at runtime
hidden_imports = [
    # Direct dependencies
    'requests',
    'bs4',
    'html.parser',          # bs4 parser (used in sources.py)
    'platformdirs',
    'pyfiglet',
    'colorama',
    'certifi',
    # Transitive dependencies
    'prompt_toolkit',       # questionary dependency (Phase 7)
    'questionary',          # Setup wizard (Phase 7, declare now to avoid rebuild)
    'charset_normalizer',   # requests dependency
    'idna',                 # requests dependency
    'urllib3',              # requests dependency
    'soupsieve',            # bs4 dependency
    # PDF parsing (Phase 15)
    'pdfplumber',
    'pdfminer',
    'pdfminer.high_level',
    'pdfminer.layout',
    'pdfminer.pdfparser',
    'pdfminer.pdfdocument',
    'pdfminer.pdfpage',
    'pdfminer.pdfinterp',
    'pdfminer.converter',
    'pdfminer.cmapdb',
    'pdfminer.psparser',
    'pdfminer.pdftypes',
    'pdfminer.utils',
    'dateutil',
    'dateutil.parser',
    # CustomTkinter GUI (Phase 28)
    'customtkinter',
    'customtkinter.windows',
    'customtkinter.windows.widgets',
]

a = Analysis(
    [str(project_root / 'job_radar' / '__main__.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,     # True = onedir mode (PKG-04)
    name='job-radar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                 # Disabled: reduces antivirus false positives
    console=True,              # Locked decision: show console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
    icon='icon.png' if sys.platform == 'win32' else None,  # Windows uses .ico (converted by PyInstaller)
)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='job-radar-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,             # No console window for GUI mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
    icon='icon.png' if sys.platform == 'win32' else None,
)

coll = COLLECT(
    exe,
    gui_exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='job-radar',
)

# macOS app bundle (only when building on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='JobRadar.app',
        icon='icon.icns',
        bundle_identifier='com.jobradar.app',
        entitlements_file='entitlements.plist',
        info_plist={
            'CFBundleExecutable': 'job-radar-gui',  # Launch GUI by default (not CLI wrapper)
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',    # Locked decision: show in dock
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeName': 'Job Radar Profile',
                    'CFBundleTypeExtensions': ['jobprofile'],
                    'CFBundleTypeRole': 'Editor',
                    'LSHandlerRank': 'Owner',
                },
            ],
            'CFBundleShortVersionString': '2.1.0',
            'CFBundleVersion': '2.1.0',
        },
    )
