import PyInstaller.__main__

if __name__ == '__main__':
    PyInstaller.__main__.run([
        'hw1.py',
        '--onefile',
        '--windowed'
    ])
