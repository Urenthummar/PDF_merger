@echo off
setlocal

REM Change to your project directory
cd /d "D:\Python Codes\merge_pdf"
if errorlevel 1 goto :error

REM Check whether the virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment was not found.
    echo Expected file:
    echo D:\Python Codes\merge_pdf\.venv\Scripts\activate.bat
    pause
    exit /b 1
)

REM Activate the virtual environment
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

echo.
echo Active Python:
where python

echo.
echo Python version:
python --version

echo.
echo Installing or updating required packages...
python -m pip install --upgrade ^
    pypdf ^
    ttkbootstrap ^
    pymupdf ^
    pillow ^
    pyinstaller

if errorlevel 1 goto :error

REM Confirm that critical libraries work inside the virtual environment
echo.
echo Checking PDF thumbnail libraries...

python -c "import pymupdf; from PIL import Image, ImageTk; import pypdf; print('Required libraries are working')"

if errorlevel 1 goto :error

REM Confirm that required project files exist
if not exist "offline_pdf_merger_v1_3.py" (
    echo.
    echo ERROR: offline_pdf_merger_v1_3.py was not found.
    pause
    exit /b 1
)

if not exist "app_icon.ico" (
    echo.
    echo ERROR: app_icon.ico was not found.
    echo Keep app_icon.ico in the project directory.
    pause
    exit /b 1
)

REM Remove previous build output
echo.
echo Removing previous build files...

if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

if exist "Offline PDF Merger.spec" (
    del /q "Offline PDF Merger.spec"
)

REM Build the Windows executable
echo.
echo Building Offline PDF Merger.exe...

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
	--version-file="file_version_info.txt" ^
    --name "Offline PDF Merger" ^
    --icon "app_icon.ico" ^
    --add-data "app_icon.ico;." ^
    --collect-all pymupdf ^
    --collect-all PIL ^
    --collect-all ttkbootstrap ^
    --hidden-import pymupdf ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageTk ^
    offline_pdf_merger_v1_3.py

if errorlevel 1 goto :error

echo.
echo ==========================================
echo Build completed successfully
echo ==========================================
echo.
echo EXE location:
echo D:\Python Codes\merge_pdf\dist\Offline PDF Merger.exe
echo.

explorer "D:\Python Codes\merge_pdf\dist"

endlocal
pause
exit /b 0

:error
echo.
echo ==========================================
echo Build failed
echo ==========================================
echo.
echo Review the error shown above.
echo.

endlocal
pause
exit /b 1