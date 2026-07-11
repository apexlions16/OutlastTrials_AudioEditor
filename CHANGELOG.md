# Değişiklik Günlüğü

Bu dosyada OutlastTrials AudioEditor için yapılan önemli değişiklikler listelenir.

## [v1.2.0] — 2026-07-11

### Değiştirildi

- 18.698 satırlık monolit uygulama dosyası modüler `outlast_trials_audio_editor/` paketine ayrıldı.
- Ana pencere işlevleri sorumluluk odaklı mixin modüllerine taşındı.
- Tarihsel `OutlastTrialsAudioEditor.py` dosyası geriye dönük uyumlu küçük bir başlatıcıya dönüştürüldü.
- README dosyasının tamamı Türkçeye çevrildi ve yeni mimari bilgileri eklendi.
- Uygulama sürümü `v1.2.0` olarak güncellendi.

### Düzeltildi

- Wwise proje dizininde yanlış `os.removedirs()` kullanımı kaldırıldı.
- Mevcut ve boş olmayan Wwise proje klasörlerinin silinmesi engellendi.
- `shell=False` kullanılan WwiseCLI çağrısında proje yoluna elle çift tırnak eklenmesi düzeltildi.

### Temizlendi

- Çalışma zamanında erişilemeyen yinelenen metot tanımları kaldırıldı.
- Son ve etkin uygulamalar korunarak kod tekrarları azaltıldı.

### Eklendi

- Kaynak düzeni ve çalışma zamanı API uyumluluğu için regresyon testleri.
- Wwise proje oluşturma güvenliği için hedefli testler.
- `ARCHITECTURE.md` mimari dokümantasyonu.
- `REFACTOR_VALIDATION.md` doğrulama raporu.
- `RELEASE_NOTES_v1.2.0.md` ayrıntılı Türkçe sürüm açıklaması.
- Kaynak kurulumuna Git LFS indirme adımları ve FFmpeg LFS uyarısı.

### Doğrulandı

- 461/461 etkin önceki sürüm metodu yeni yapıda mevcut.
- 460/461 metot gövdesi mekanik olarak eşdeğer.
- Bilinçli tek davranış değişikliği Wwise proje güvenliği düzeltmesi.
- Bütün paket modülleri import edildi.
- Bütün Python kaynakları ayrıştırma ve bayt kod derleme kontrolünden geçti.
- Ana pencere ekransız Qt ortamında oluşturulup kapatıldı.
- 8/8 otomatik test başarılı.
