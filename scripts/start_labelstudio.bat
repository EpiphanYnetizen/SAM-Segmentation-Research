@echo off
set REPO=%~dp0..
set PROJECT=%REPO%\..
set LS_EXE=%PROJECT%\envs\labelstudio\Scripts\label-studio.exe
set LS_HOME=%PROJECT%\tools\labelstudio
set LS_DATA=%LS_HOME%\data
set LS_IMAGES=%LS_HOME%\images

if not exist "%LS_EXE%" (
  echo Label Studio is not installed.
  echo Run these commands in the project directory:
  echo   py -3.10 -m venv envs\labelstudio
  echo   envs\labelstudio\Scripts\pip.exe install label-studio
  pause
  exit /b 1
)

if not exist "%LS_DATA%" mkdir "%LS_DATA%"
if not exist "%LS_IMAGES%" mkdir "%LS_IMAGES%"

set LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED=true
set LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT=%LS_IMAGES%

echo Label Studio data: %LS_DATA%
echo Label Studio images: %LS_IMAGES%
echo Open http://localhost:8080 after startup.
"%LS_EXE%" start --data-dir "%LS_DATA%"
