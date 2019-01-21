# -*- mode: python -*-

block_cipher = None

added_files = [
         ( 'C:\\Users\\armigrs1\\AppData\\Local\\Programs\\Python\\Python37\\Lib\\site-packages\\spectrum\\data\\*.wav', 'spectrum\\data' )
         ]

a = Analysis(['run_www.py'],
             pathex=['C:\\git\\minivie\\python\\minivie'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='run_www',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='run_www')
