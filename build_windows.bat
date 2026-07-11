@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "APP_VERSION=v1.2.1"
set "DIST_NAME=OutlastTrialsAudioEditor_%APP_VERSION%_Windows_x64"

echo [1/6] Python 3.11 x64 kontrol ediliyor...
where py >nul 2>nul || (
  echo HATA: Python Launcher bulunamadi. Python 3.11 x64 kurun.
  exit /b 1
)
py -3.11 -c "import struct; raise SystemExit(0 if struct.calcsize('P') == 8 else 1)" || exit /b 1

if not exist ".venv-build\Scripts\python.exe" (
  echo [2/6] Derleme ortami olusturuluyor...
  py -3.11 -m venv .venv-build || exit /b 1
) else (
  echo [2/6] Mevcut derleme ortami kullaniliyor...
)
set "PY=.venv-build\Scripts\python.exe"

echo [3/6] Bagimliliklar kuruluyor...
"%PY%" -m pip install --upgrade pip || exit /b 1
"%PY%" -m pip install -r requirements.txt pyinstaller==6.21.0 numpy==1.26.4 scipy==1.13.1 matplotlib==3.8.4 psutil==6.1.1 imageio-ffmpeg==0.6.0 || exit /b 1

for %%F in (data\ffmpeg.exe) do set "FFMPEG_SIZE=%%~zF"
if not exist data\ffmpeg.exe set "FFMPEG_SIZE=0"
if !FFMPEG_SIZE! LSS 1000000 (
  echo Git LFS FFmpeg bulunamadi; dogrulanmis yedek ikili kopyalaniyor...
  for /f "usebackq delims=" %%F in (`"%PY%" -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`) do set "FALLBACK_FFMPEG=%%F"
  copy /y "!FALLBACK_FFMPEG!" "data\ffmpeg.exe" >nul || exit /b 1
)

set "QT_QPA_PLATFORM=offscreen"
echo [4/6] Testler calistiriliyor...
"%PY%" -m unittest discover -s tests -v || exit /b 1

echo [5/6] PyInstaller paketi olusturuluyor...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
"%PY%" -m PyInstaller --noconfirm --clean OutlastTrialsAudioEditor.spec || exit /b 1

set "DIST_DIR=dist\%DIST_NAME%"
set "APP_EXE=%DIST_DIR%\OutlastTrials AudioEditor.exe"
if not exist "%APP_EXE%" (
  echo HATA: EXE olusturulamadi.
  exit /b 1
)

echo [6/6] Derlenen EXE acilis testi ve ZIP paketleme...
"%APP_EXE%" --smoke-test
if errorlevel 1 (
  echo HATA: EXE acilis testi basarisiz.
  if exist "%DIST_DIR%\packaging_smoke_test.log" type "%DIST_DIR%\packaging_smoke_test.log"
  if exist "%DIST_DIR%\startup_crash.log" type "%DIST_DIR%\startup_crash.log"
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $src='%DIST_DIR%'; $zip='dist\%DIST_NAME%.zip'; if(Test-Path $zip){Remove-Item $zip -Force}; Compress-Archive -Path $src -DestinationPath $zip -CompressionLevel Optimal" || exit /b 1

echo.
echo Derleme ve acilis testi tamamlandi:
echo   %APP_EXE%
echo   dist\%DIST_NAME%.zip
exit /b 0
