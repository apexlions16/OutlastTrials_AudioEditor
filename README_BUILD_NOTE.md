# Windows EXE Derleme Notu

Windows uygulama paketi artık GitHub Actions üzerinde gerçek Windows ortamında PyInstaller ile oluşturulur. İş akışı, derlenen `OutlastTrials AudioEditor.exe` dosyasını `--smoke-test` parametresiyle gerçekten çalıştırır ve yalnızca açılış testi başarılı olursa ZIP artefaktını yayımlar.

v1.2.1 derleme zinciri; Python 3.11 kaynak uyumluluğunu, çalışma zamanı API'sini, Wwise proje güvenliğini, gerekli yardımcı araçları ve paketlenmiş ana pencerenin açılmasını doğrular.

Yerel Windows derlemesi için `build_windows.bat` dosyasını çalıştırın.
