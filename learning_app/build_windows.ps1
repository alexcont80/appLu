$ErrorActionPreference = "Stop"
$AppRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $AppRoot

py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r learning_app\requirements.txt
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name AppLu-Apprendimento --collect-all fitz --collect-all pymupdf --collect-all docx --distpath learning_app\dist --workpath learning_app\build run_app.py

if (Test-Path .\learning_app\AppLu-Apprendimento-portable.zip) { Remove-Item .\learning_app\AppLu-Apprendimento-portable.zip }
Compress-Archive -Path .\learning_app\dist\AppLu-Apprendimento\* -DestinationPath .\learning_app\AppLu-Apprendimento-portable.zip
Write-Host "Portable build: $AppRoot\learning_app\AppLu-Apprendimento-portable.zip"

