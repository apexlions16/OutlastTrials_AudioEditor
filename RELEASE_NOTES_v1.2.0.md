# OutlastTrials AudioEditor v1.2.0 — Modüler Mimari Sürümü

Bu sürüm, kullanıcı tarafındaki mevcut ses ve altyazı modlama özelliklerini korurken projenin geliştirilmesini, test edilmesini ve bakımını kolaylaştıran kapsamlı bir mimari yeniden yapılandırma içerir.

## Öne çıkan değişiklikler

### Büyük kaynak dosyası modüler bir pakete ayrıldı

Önceki sürümde uygulamanın neredeyse tamamı 18.698 satırlık `OutlastTrialsAudioEditor.py` dosyasında bulunuyordu. Bu dosya artık geriye dönük uyumlu, küçük bir başlatıcıdır. Uygulama kodu `outlast_trials_audio_editor/` paketi altındaki sorumluluk odaklı modüllere taşındı.

Yeni yapı başlıca şu katmanlardan oluşur:

- `app.py`: uygulama başlangıcı ve açılış ekranı.
- `common.py`: ortak bağımlılıklar, platform ayarları, sürüm ve uygulama yolları.
- `debug.py`: loglama, hata ayıklama penceresi ve genel hata işleyicileri.
- `models.py`: veri modelleri.
- `profiles.py`: mod profili yönetimi ve içe aktarma işlemleri.
- `workers.py`: uzun süren işlemler için Qt arka plan işçileri.
- `i18n/`: yerleşik dil ve çeviri verileri.
- `services/audio.py`: ses dönüştürme ve Wwise işlemleri.
- `services/bnk.py`: BNK/WEM bank işlemleri.
- `services/localization.py`: LOCRES ve altyazı işleme mantığı.
- `services/settings.py`: uygulama ayarları.
- `ui/widgets.py`: yeniden kullanılabilir Qt bileşenleri.
- `ui/audio_dialogs.py`: ses kırpma ve ses seviyesi diyalogları.
- `ui/statistics.py`: istatistik arayüzü.
- `ui/main_window.py`: somut ana pencere, Qt slotları ve yaşam döngüsü metotları.
- `ui/mixins/`: eski ana pencere sınıfındaki işlevlerin sorumluluklarına göre ayrılmış parçaları.

### Geriye dönük başlatma uyumluluğu korundu

Mevcut kullanım ve paketleme akışlarının bozulmaması için aşağıdaki komut çalışmaya devam eder:

```bash
python OutlastTrialsAudioEditor.py
```

Qt tarafından işlenen `@pyqtSlot` metotları, meta-object ve queued invocation davranışlarının korunması için somut `WemSubtitleApp` sınıfında bırakıldı.

### Erişilemeyen yinelenen kodlar temizlendi

Python'ın “son tanım geçerlidir” davranışı nedeniyle çalışma zamanında hiçbir zaman kullanılmayan eski metot tanımları kaldırıldı. Son ve gerçekten kullanılan uygulamalar korunmuştur:

- `WavToWemConverter.convert_single_file`
- `WemSubtitleApp._on_scan_finished`
- `WemSubtitleApp.batch_adjust_volume`
- `WemSubtitleApp.update_conversion_status`

Bu temizlik özellik kaybına yol açmadan kod karmaşıklığını azalttı.

## Hata düzeltmeleri ve güvenlik iyileştirmeleri

### Wwise proje klasörünün yanlışlıkla silinmesi önlendi

`WavToWemConverter.ensure_project_exists()` içindeki hatalı `os.removedirs(project_dir)` kullanımı düzeltildi. Yeni davranış:

- Var olmayan proje klasörünü güvenli biçimde oluşturur.
- Mevcut ve boş olmayan Wwise proje klasörünü silmez.
- Mevcut `.wproj` dosyasını korur.

Bu düzeltme, ses dönüştürme sırasında kullanıcı verisinin veya üst klasörlerin yanlışlıkla kaldırılması riskini ortadan kaldırır.

### WwiseCLI yol argümanı düzeltildi

`subprocess.run(..., shell=False)` çağrısına verilen `.wproj` yolu artık elle eklenmiş çift tırnak karakterleri içermiyor. Python argüman kaçışını kendisi yönettiği için boşluk içeren Windows yolları daha güvenilir biçimde çalışır.

## Testler ve doğrulama

Bu yeniden yapılandırma için otomatik regresyon testleri ve statik doğrulamalar eklendi.

Doğrulanan noktalar:

- Paket içindeki bütün Python modülleri ekransız Qt ortamında başarıyla import edildi.
- Bütün Python kaynakları ayrıştırma ve bayt kod derleme kontrolünden geçti.
- Eski monolitteki bütün etkin sınıflar ve metotlar yeni yapıda korundu.
- Eski API'deki 461 etkin metodun 461'i yeni yapıda mevcut.
- 460 metodun gövdesi mekanik AST karşılaştırmasında eşdeğer bulundu.
- Tek bilinçli davranış değişikliği Wwise proje klasörü güvenliği düzeltmesidir.
- Ana pencere, paketle birlikte gelen çalışma zamanı varlıklarıyla ekransız Qt ortamında oluşturulup temiz biçimde kapatıldı.
- Wwise proje oluşturma işlemi için boşluk içeren yollar, mevcut proje dosyası ve boş olmayan klasör koruması test edildi.
- Toplam 8 otomatik test başarıyla geçti.

Testleri çalıştırmak için:

```bash
python -m unittest discover -s tests -v
```

## Dokümantasyon

- README dosyasının tamamı Türkçeye çevrildi.
- Yeni modüler yapı README içinde özetlendi.
- Ayrıntılı modül haritası `ARCHITECTURE.md` dosyasında belgelendi.
- Yeniden yapılandırma doğrulama sınırları `REFACTOR_VALIDATION.md` dosyasında açıklandı.

## Uyumluluk

- Windows 10/11 — 64 bit.
- Python 3.8 veya üzeri.
- Ses dönüşümü için Wwise 2019.1.6.7110.
- Mevcut `OutlastTrialsAudioEditor.py` çalıştırma komutu korunmuştur.
- Kullanıcıya sunulan ses, BNK, altyazı, profil, derleme ve dağıtım özelliklerinde kasıtlı bir özellik kaldırma yapılmamıştır.

## Kaynak paket ve Git LFS notu

`data/ffmpeg.exe` büyük boyutu nedeniyle Git LFS ile izlenir. Depoyu kaynak koddan kullanan geliştiricilerin klonlama sonrasında aşağıdaki komutları çalıştırması gerekir:

```bash
git lfs install
git lfs pull
```

Git LFS nesnesi indirilmeden oluşturulan standart kaynak arşivlerinde gerçek `ffmpeg.exe` yerine küçük bir LFS işaretçi dosyası bulunabilir. Çalıştırılabilir Windows dağıtım paketine gerçek FFmpeg ikilisi ayrıca dahil edilmelidir.

## Bilinen doğrulama sınırı

Statik kontroller ve ekransız Qt testleri başarılıdır; ancak bu sürüm Linux tabanlı geliştirme ortamında hazırlandığı için Windows üzerinde aşağıdaki gerçek ortam testi ayrıca yapılmalıdır:

- Wwise 2019.1.6.7110 ile gerçek WAV → WEM dönüşümü.
- Gerçek The Outlast Trials BNK/WEM/LOCRES dosyaları.
- Oyunun güncel PAK dosyalarından kaynak çıkarma.
- Mod derleme, oyunun `Paks` klasörüne dağıtma ve oyun içinde doğrulama.

Bu nedenle kaynak kod sürümü kullanıma hazırdır; Windows `.exe` dağıtım paketi yayımlanmadan önce gerçek oyun ortamında uçtan uca test önerilir.

## Katkıda bulunanlar ve teşekkür

Orijinal OutlastTrials AudioEditor projesini geliştiren **Bezna**'ya ve projede kullanılan Red Barrels, vgmstream, UnrealLocres, repak, Audiokinetic, PyQt5 ve FFmpeg topluluklarına teşekkürler.
