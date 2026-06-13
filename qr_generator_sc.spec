# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for QR Generator SC.
Build: pyinstaller qr_generator_sc.spec
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Include assets folder
    ],
    hiddenimports=[
        'flet',
        'qrcode',
        'qrcode.image',
        'qrcode.image.pil',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='QRGeneratorSC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    target_arch='x86_64',
    icon='./assets/logo_qr_generator_sc.ico',
    version_file=None,
)
