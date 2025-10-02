# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=[('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\abseil_dll.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\bz2.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\highs.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\libprotobuf.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\libscip.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\libutf8_validity.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\ortools.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\re2.dll', 'ortools/.libs'), ('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\.venv\\Lib\\site-packages\\ortools\\.libs\\zlib1.dll', 'ortools/.libs')],
    datas=[('c:\\Users\\Jordan\\Documents\\GitHub\\ChatGPT Schedule Generator\\Project\\backend\\app\\static\\dist', 'app/static/dist')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='run_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
