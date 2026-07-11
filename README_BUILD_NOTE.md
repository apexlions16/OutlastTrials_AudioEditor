# Windows EXE Derleme Notu

Windows uygulama paketi artık GitHub Actions üzerinde gerçek Windows ortamında PyInstaller ile oluşturulur. İş akışı, derlenen `OutlastTrials AudioEditor.exe` dosyasını `--smoke-test` parametresiyle gerçekten çalıştırır ve yalnızca açılış testi başarılı olursa ZIP artefaktını yayımlar.

Yerel Windows derlemesi için `build_windows.bat` dosyasını çalıştırın.
