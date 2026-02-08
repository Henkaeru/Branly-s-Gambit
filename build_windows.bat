@echo off
pyinstaller --onefile --windowed main.py ^
    --hidden-import=pygame._sdl2 ^
    --hidden-import=pygame_gui.core ^
    --add-data "assets;assets" ^
    --add-data "data;data" ^
    --name "Branlys_Gambit"

echo Build complete. Executable is in dist\
