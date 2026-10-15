# Offline PDF Merger

A Windows desktop application for selecting, previewing, arranging, and merging multiple PDF files into one document.

The application runs completely offline. PDF files remain on the local computer and are not uploaded to any website or external service.

## Features

- Add multiple PDF files at once
- Preview the first page of each PDF as a thumbnail
- Switch between grid view and list view
- Select one or more files
- Use `Ctrl + Click` to select individual files
- Use `Shift + Click` to select a range of files
- Move selected files up or down while preserving their order
- Remove one file or multiple selected files
- Display PDF page count and file size
- Merge PDFs in the displayed sequence
- Modern Windows-style interface using `ttkbootstrap`
- Custom application icon
- Works without internet access
- Can be packaged as a standalone Windows EXE

## Project Files

Keep the following files in the same project folder:

```text
D:\Python Codes\merge_pdf\
|
|-- .venv\
|-- offline_pdf_merger_v1_3.py
|-- app_icon.ico
|-- build_exe_v1_3.bat
|-- README.md
```

After building the application, the following folders are generated automatically:

```text
|-- build\
|-- dist\
|   |-- Offline PDF Merger.exe
|-- Offline PDF Merger.spec
```

## System Requirements

- Windows 10 or Windows 11
- Python 3.10 or later recommended
- A local Python virtual environment
- Approximately 150 MB of free space for Python packages and build files

The final EXE size can vary depending on the installed versions of PyMuPDF, Pillow, ttkbootstrap, and PyInstaller.

## Python Packages

The application uses the following packages:

- `pypdf` for reading and merging PDF files
- `pymupdf` for rendering PDF thumbnails
- `Pillow` for displaying thumbnail images
- `ttkbootstrap` for the modern desktop interface
- `PyInstaller` for creating the Windows EXE
- `tkinter` for the desktop UI, normally included with Python on Windows

## Create the Virtual Environment

Open Command Prompt and change to the project directory:

```bat
cd /d "D:\Python Codes\merge_pdf"
```

Create the virtual environment:

```bat
py -m venv .venv
```

Activate the virtual environment:

```bat
call ".venv\Scripts\activate.bat"
```

After activation, the command prompt should show `(.venv)` before the project path.

## Install Required Packages

With the virtual environment active, run:

```bat
python -m pip install --upgrade pip
python -m pip install pypdf ttkbootstrap pymupdf pillow pyinstaller
```

If the unrelated legacy `fitz` package is installed, remove it because the application imports PyMuPDF using `import pymupdf`:

```bat
python -m pip uninstall fitz -y
```

Verify the thumbnail libraries:

```bat
python -c "import pymupdf; from PIL import Image, ImageTk; print('Thumbnail libraries OK')"
```

Expected output:

```text
Thumbnail libraries OK
```

## Run the Application from Python

Activate the virtual environment:

```bat
cd /d "D:\Python Codes\merge_pdf"
call ".venv\Scripts\activate.bat"
```

Run the application:

```bat
python offline_pdf_merger_v1_3.py
```

Before building the EXE, confirm the following:

- The application opens without an error
- PDF files can be added
- First-page thumbnails are visible
- Grid view and list view both work
- Single selection works
- `Ctrl + Click` multiple selection works
- `Shift + Click` range selection works
- Selected files move up and down correctly
- The merged PDF opens and has the expected page sequence
- The About window displays correctly
- The application icon appears in the title bar

## Using the Application

### Add PDF files

Select **Add PDFs**, then choose one or more PDF files.

### Change the PDF order

The displayed order determines the order in the merged PDF.

1. Select one or more files.
2. Use **Move up** or **Move down**.
3. Confirm that the sequence numbers are correct.

### Select multiple files

- Click a card to select one file.
- Hold `Ctrl` and click cards to select separate files.
- Click the first file, hold `Shift`, and click another file to select the complete range.

### Switch the layout

Use the **List view** or **Grid view** button.

- Grid view displays more PDF files on the screen and reduces vertical scrolling.
- List view shows wider file details and is useful for long file names.

### Merge PDF files

1. Arrange the files in the required order.
2. Select **Create merged PDF**.
3. Enter the output file name.
4. Select the destination folder.
5. Open the generated PDF and verify the page sequence.

## Application Icon

The application expects the icon file to be named:

```text
app_icon.ico
```

Keep the icon in the same folder as the Python file and BAT file.

A Windows ICO file should preferably contain multiple sizes:

```text
16 x 16
24 x 24
32 x 32
48 x 48
64 x 64
128 x 128
256 x 256
```

The Python application uses the icon for the main window and About window. PyInstaller uses the same file for the generated EXE.

## Build the Windows EXE

The supplied build script uses the virtual environment located at:

```text
D:\Python Codes\merge_pdf\.venv
```

Run:

```text
build_exe_v1_3.bat
```

The BAT file performs these steps:

1. Changes to the project directory
2. Activates `.venv`
3. Confirms that the Python file and icon exist
4. Installs or updates required packages inside the virtual environment
5. Checks PyMuPDF and Pillow imports
6. Removes previous `build` and `dist` folders
7. Runs PyInstaller
8. Opens the output folder after a successful build

The final EXE is created at:

```text
D:\Python Codes\merge_pdf\dist\Offline PDF Merger.exe
```

## Recommended Build Script

Save the following as `build_exe_v1_3.bat`:

```bat
@echo off
setlocal

REM Change to the project directory
cd /d "D:\Python Codes\merge_pdf"
if errorlevel 1 goto :error

REM Check the virtual environment
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment was not found.
    echo Expected: D:\Python Codes\merge_pdf\.venv\Scripts\activate.bat
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

REM Confirm the project files
if not exist "offline_pdf_merger_v1_3.py" (
    echo ERROR: offline_pdf_merger_v1_3.py was not found.
    pause
    exit /b 1
)

if not exist "app_icon.ico" (
    echo ERROR: app_icon.ico was not found.
    pause
    exit /b 1
)

REM Remove the conflicting legacy fitz package if present
python -m pip uninstall fitz -y >nul 2>&1

REM Install required packages in the active virtual environment
python -m pip install --upgrade ^
    pypdf ^
    ttkbootstrap ^
    pymupdf ^
    pillow ^
    pyinstaller

if errorlevel 1 goto :error

REM Check thumbnail dependencies
python -c "import pymupdf; from PIL import Image, ImageTk; import pypdf; print('Required libraries are working')"
if errorlevel 1 goto :error

REM Remove the previous build
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Offline PDF Merger.spec" del /q "Offline PDF Merger.spec"

REM Build the executable
python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --windowed ^
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

explorer "D:\Python Codes\merge_pdf\dist"

endlocal
pause
exit /b 0

:error
echo.
echo ==========================================
echo Build failed
echo ==========================================
echo Review the error shown above.

endlocal
pause
exit /b 1
```

## Why the Build Script Uses `setlocal`

`setlocal` keeps changes made by the BAT file limited to the BAT process. This includes the PATH changes made when `.venv` is activated.

At the end of the script, `endlocal` restores the original command environment.

## Why the Script Uses `python` Instead of `py`

After `.venv` is activated, use:

```bat
python -m PyInstaller
```

Do not use:

```bat
py -m PyInstaller
```

The `py` launcher can select a system Python installation. The `python` command uses the Python executable from the active virtual environment.

Verify the active interpreter with:

```bat
where python
```

The first result should be:

```text
D:\Python Codes\merge_pdf\.venv\Scripts\python.exe
```

## Troubleshooting

### Thumbnail shows `Preview unavailable`

First, run the application from Python rather than the EXE:

```bat
python offline_pdf_merger_v1_3.py
```

Then verify the imports:

```bat
python -c "import pymupdf; from PIL import Image, ImageTk; print(pymupdf.__file__)"
```

If the imports fail, reinstall the libraries:

```bat
python -m pip uninstall fitz -y
python -m pip uninstall pymupdf pillow -y
python -m pip install --upgrade pymupdf pillow
```

Rebuild the EXE after reinstalling the packages.

### Thumbnail works in Python but not in the EXE

Delete the old build output:

```bat
rmdir /s /q build
rmdir /s /q dist
```

Run `build_exe_v1_3.bat` again. The build command includes:

```text
--collect-all pymupdf
--collect-all PIL
--hidden-import pymupdf
--hidden-import PIL.Image
--hidden-import PIL.ImageTk
```

These options package the thumbnail libraries into the EXE.

### Application icon is missing

Confirm that:

- The file is named exactly `app_icon.ico`
- The icon is in the project folder
- The build command contains `--icon "app_icon.ico"`
- The build command contains `--add-data "app_icon.ico;."`

Windows can cache old EXE icons. Rename the rebuilt EXE or restart Windows Explorer if the previous icon is still displayed.

### Windows SmartScreen warning

Windows may warn about an internally developed unsigned EXE. This does not automatically indicate malware. For company-wide distribution, the EXE should be reviewed and code-signed according to the organisation's IT security process.

### Build uses the wrong Python installation

Run:

```bat
where python
python -c "import sys; print(sys.executable)"
```

The Python executable should point to:

```text
D:\Python Codes\merge_pdf\.venv\Scripts\python.exe
```

### Password-protected PDF

The merger cannot process a password-protected PDF unless the PDF can be opened without a password. Remove the password using an approved internal process before merging the file.

### Large PDF collection

Generating thumbnails for many large PDFs can take time during the initial load. Subsequent view changes are faster because thumbnails are cached in memory.

## Offline and Privacy Behaviour

- PDF content is processed locally.
- No PDF is uploaded to a website.
- No internet connection is required after the application and dependencies are installed.
- The application does not send usage information or telemetry.
- Output files are written only to the location selected by the user.

## Distribution Checklist

Before sharing the EXE internally, verify:

- The EXE opens on a test computer
- PDF thumbnails display correctly
- The application icon is visible
- Grid and list views work
- Multi-selection works
- PDF order is preserved
- The output PDF page count is correct
- The About window shows the intended name and contact details
- Antivirus and company security checks are completed
- The EXE is code-signed if required by company policy

## Developer Information

**Made by Uren with AI assistance**

- Email: `xxx@gmail.com`
- Phone: `+91 xxxx`
- Application version: `1.3`

## Intended Use

This utility is intended for authorised internal and personal document-processing work. Users remain responsible for following company document-handling, confidentiality, retention, and information-security requirements.
