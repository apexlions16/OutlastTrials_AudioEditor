# OutlastTrials AudioEditor v1.2.1 — Windows EXE Düzeltmesi

Bu bakım sürümü, v1.2.0 için daha önce hazırlanan deneysel taşınabilir başlatıcının Windows üzerinde açılmaması sorununu giderir.

## Düzeltmeler

- Yeniden adlandırılmış `pythonw.exe` tabanlı deneysel paket kaldırıldı.
- Uygulama artık doğrudan Windows üzerinde PyInstaller ile gerçek bir Windows GUI uygulaması olarak derlenir.
- Başlatma sırasında oluşan import veya çalışma zamanı hataları artık sessizce kaybolmaz:
  - kullanıcıya Windows hata iletişim kutusu gösterilir;
  - ayrıntılar `startup_crash.log` dosyasına yazılır.
- EXE içine alınan `data/` yolu uygulamanın mevcut dosya yolu beklentileriyle uyumlu tutuldu.
- Git LFS üzerinden FFmpeg alınamadığında doğrulanmış Windows FFmpeg ikilisi otomatik olarak kullanılır.

## Otomatik doğrulama

GitHub Actions, Windows Server üzerinde aşağıdaki işlemleri gerçekleştirir:

1. Python 3.11 x64 ve bütün çalışma zamanı bağımlılıklarını kurar.
2. Mevcut birim ve regresyon testlerini çalıştırır.
3. Uygulamayı PyInstaller ile derler.
4. Derlenen `OutlastTrials AudioEditor.exe` dosyasını `--smoke-test` modunda gerçekten başlatır.
5. PyQt5, Qt platform eklentileri, bütün modüler Python paketleri ve gerekli `data/` araçlarının yüklenmesini doğrular.
6. Yalnızca açılış testi başarılı olursa dağıtım ZIP dosyasını oluşturur.

## Dağıtım biçimi

Release varlığı tek bir ZIP dosyasıdır:

`OutlastTrialsAudioEditor_v1.2.1_Windows_x64.zip`

ZIP tamamen çıkarılmalı ve klasör içindeki `OutlastTrials AudioEditor.exe` çalıştırılmalıdır. Uygulama tek dosyalı değildir; EXE yanındaki DLL, Python/Qt çalışma zamanı ve `data/` klasörüne ihtiyaç duyar.

WAV → WEM dönüşümü için **Wwise 2019.1.6.7110** ayrıca kurulmalıdır.
