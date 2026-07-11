# 🎮 OutlastTrials AudioEditor

<div align="center">

**🔊 The Outlast Trials için Kapsamlı Ses ve Altyazı Modlama Aracı 🔊**

[![Sürüm](https://img.shields.io/badge/sürüm-v1.2.0-success?style=for-the-badge&logo=semantic-release)](../../releases)
[![Lisans](https://img.shields.io/badge/lisans-MIT-blue?style=for-the-badge&logo=opensourceinitiative)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightblue?style=for-the-badge&logo=windows)](../../releases)

[![Katkıda Bulunanlar](https://img.shields.io/badge/katkıda_bulunanlar-hoş_geldiniz-orange?style=for-the-badge&logo=github)](../../graphs/contributors)
[![Discord](https://img.shields.io/badge/Discord-Bezna-7289da?style=for-the-badge&logo=discord)](https://discord.com)

[🚀 Hızlı Başlangıç](#-hızlı-başlangıç) • [✨ Özellikler](#-özellikler) • [📖 Ayrıntılı Kullanım](#-ayrıntılı-kullanım-kılavuzu) • [💬 Destek](#-destek-ve-iletişim)

</div>

---

## 🌟 Genel Bakış

<div align="center">
  <img src="https://i.imgur.com/RlDeIq0.png" alt="Uygulama ekran görüntüsü" width="750" style="border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"/>
</div>

<br>

**OutlastTrials AudioEditor**, The Outlast Trials için geliştirilmiş kapsamlı bir modlama aracıdır. İçerik üreticileri, seslendirme sanatçıları, çevirmenler ve oyunu kişiselleştirmek isteyen oyuncular; ses ve altyazı değişikliklerini tek bir masaüstü uygulaması üzerinden hazırlayabilir, paketleyebilir ve oyuna dağıtabilir.

Bu depo, uygulamanın özelliklerini korurken bakım ve katkı süreçlerini kolaylaştırmak amacıyla modüler bir Python paket yapısına geçirilmiştir. Eski başlatma komutu geriye dönük uyumluluk için çalışmaya devam eder.

---

## ✨ Özellikler

### 🎵 **Gelişmiş Ses Yönetimi**
<details>
<summary><b>🔧 Ses özelliklerini görüntülemek için tıklayın</b></summary>

- **🎧 WEM Dosyası Desteği:** The Outlast Trials tarafından kullanılan Wwise ses dosyalarını doğrudan işler.
- **▶️ Anlık Oynatma:** Yerleşik oynatıcıyla orijinal veya değiştirilmiş sesi anında dinleyebilirsiniz.
- **⚡ Hızlı Yükleme ve Sürükle-Bırak:** `.wav`, `.mp3` veya `.ogg` dosyalarını doğrudan bir ses kaydının üzerine bırakarak saniyeler içinde değiştirebilirsiniz.
- **🔊 Ses Seviyesi Ayarı:** Tek bir sesin veya birden fazla ses dosyasının seviyesini görsel düzenleyici üzerinden hassas biçimde ayarlayabilirsiniz.
- **✂️ Ses Kırpma:** Görsel dalga biçimi düzenleyicisiyle seslerin başlangıç ve bitiş noktalarını tahribatsız olarak kırpabilirsiniz.
- **🔄 Akıllı Dönüştürme:** İki çalışma moduna sahip gelişmiş `Ses -> WEM` dönüştürücüsü:
  - **BNK Üzerine Yazma — Önerilen:** En yüksek kalitede dönüştürür ve bank dosyasındaki boyut bilgisini güncelleyerek boyut kısıtını ortadan kaldırır.
  - **Uyarlanabilir Boyut Eşleştirme:** Dönüştürme kalitesini orijinal dosya boyutuna yaklaşacak şekilde otomatik ayarlar.
- **📁 BNK Bütünlük Araçları:** Oyun içi ses sorunlarını önlemek için `.bnk` dosyalarındaki boyut uyuşmazlıklarını doğrular ve otomatik olarak düzeltebilir.
</details>

### 📝 **Profesyonel Altyazı ve Yerelleştirme Araçları**
<details>
<summary><b>🌍 Altyazı özelliklerini görüntülemek için tıklayın</b></summary>

- **🌐 Çoklu Dil Desteği:** Oyundaki 14'ten fazla dil için kapsamlı destek sunar.
- **📄 LOCRES Dosyası İşleme:** Unreal Engine yerelleştirme dosyalarını doğrudan işler.
- **✏️ Merkezi Yerelleştirme Düzenleyicisi:** Farklı dosyalardaki altyazıları tek, aranabilir bir tablo üzerinden düzenlemenizi sağlar.
- **📦 Toplu Dışa Aktarma:** Bütün altyazı değişikliklerini tek tıklamayla temiz ve oyun için hazır bir mod klasör yapısına aktarır.
</details>

### 🛠️ **Eksiksiz Modlama İş Akışı**
<details>
<summary><b>⚙️ Modlama araçlarını görüntülemek için tıklayın</b></summary>

- **🚀 Tek Tıkla Derleme ve Dağıtım:** `F5` tuşuyla modunuzu derleyebilir, oyuna dağıtabilir ve oyunu başlatabilirsiniz.
- **📁 Mod Profili Yöneticisi:** Birden fazla mod projesini oluşturabilir, yönetebilir ve aralarında kolayca geçiş yapabilirsiniz. Her profil kendi klasöründe bağımsız olarak saklanır.
- **🔄 Kaynak Güncelleyici:** Yerel ses ve altyazı kaynaklarını oyunun güncel `.pak` arşivlerinden yeniden çıkararak güncel tutabilirsiniz.
</details>

---

## 🚀 Hızlı Başlangıç

### ⚡ **Seçenek 1: Hazır Sürümü Kullanma — Önerilen**

<div align="center">

[![En Güncel Sürümü İndir](https://img.shields.io/badge/📥_En_Güncel_Sürümü_İndir-success?style=for-the-badge&logo=download)](../../releases/latest)

</div>

1. 📥 En güncel sürümün `.zip` dosyasını indirin.
2. 📂 Arşivi bilgisayarınızdaki bir klasöre çıkarın.
3. ▶️ `OutlastTrials AudioEditor.exe` dosyasını çalıştırın.
4. 🛠️ **İlk Çalıştırma:** Uygulama sizden **Kaynak Güncelleyici** aracını çalıştırmanızı isteyecektir. Gerekli oyun seslerini ve metinlerini çıkarmak için oyunun `.pak` dosyasını seçin:
   `.../The Outlast Trials/OPP/Content/Paks/OPP-WindowsClient.pak`
5. 🎉 Modlamaya başlayın.

> **Not:** Bu depodaki v1.2.0 yeniden yapılandırma sürümü kaynak kod ve geliştirme paketi olarak hazırlanmıştır. Windows `.exe` paketi yayımlanmamışsa uygulamayı aşağıdaki geliştirici kurulumu ile çalıştırabilirsiniz.

### 🔧 **Seçenek 2: Kaynak Koddan Geliştirici Kurulumu**

<details>
<summary><b>🛠️ Gelişmiş kurulum adımlarını görüntülemek için tıklayın</b></summary>

```bash
# 📋 Depoyu klonlayın
git clone <REPO_ADRESİNİZ>
cd OutlastTrials_AudioEditor

# 📦 Git LFS ile izlenen büyük dosyaları indirin
git lfs install
git lfs pull

# 🐍 Python bağımlılıklarını kurun
pip install -r requirements.txt

# ▶️ Uygulamayı başlatın
python OutlastTrialsAudioEditor.py
```
</details>

### 📋 **Sistem Gereksinimleri**

| Bileşen | Gereksinim |
| --- | --- |
| **İşletim Sistemi** | Windows 10/11 — 64 bit |
| **Oyun Sürümü** | The Outlast Trials — Steam veya Epic Games |
| **Ses Motoru** | [Wwise 2019.1.6.7110](https://www.audiokinetic.com/download/) — ses dönüşümü için gereklidir |
| **Kaynak Koddan Çalıştırma** | Python 3.8 veya daha yeni bir sürüm ve Git LFS |

---

## 📚 Ayrıntılı Kullanım Kılavuzu

**Resmî eğitim videosu — eski sürüm:** https://www.youtube.com/watch?v=HDV8ocAPtzo

### 🎵 **Ses Modlama İş Akışı**

Bir sesi değiştirmenin en kolay yolu **Hızlı Yükleme** özelliğini kullanmaktır.

<div align="center">
<img src="https://i.imgur.com/your-quick-load-gif.gif" alt="Hızlı Yükleme gösterimi" width="600"/>
</div>

1. **Sesi Bulun:** Ana listede değiştirmek istediğiniz ses dosyasına göz atın veya arama alanını kullanın.
2. **Hızlı Yükleme:**
   - Dosyaya **sağ tıklayın** ve `🎵 Özel Sesi Hızlı Yükle...` seçeneğini seçin.
   - Alternatif olarak yeni ses dosyanızı (`.mp3`, `.wav`, `.ogg` ve benzeri) doğrudan listedeki kaydın üzerine **sürükleyip bırakın**.
3. **Tamamlandı:** Düzenleyici yeni sesi otomatik olarak dönüştürür ve etkin mod profiline yerleştirir.

### 📝 **Altyazı Düzenleme İş Akışı**

1. **Dili Seçin:** `Ayarlar` bölümünden hedef altyazı dilini seçin.
2. **Düzenleyiciyi Açın:** **Yerelleştirme Düzenleyicisi** sekmesine geçin.
3. **Metni Bulun ve Düzenleyin:** Değiştirmek istediğiniz metni arama alanıyla bulun. Düzenlemek için “Geçerli” sütununa çift tıklayın.
4. **Kaydedin:** Alt bölümdeki `💾 Tüm Değişiklikleri Kaydet` düğmesine basın.

### 🚀 **Modu Derleme ve Oyuna Dağıtma**

1. **Derleyin:** Değişikliklerinizi tamamladıktan sonra `Araçlar -> Modu Derle` seçeneğini kullanın. Uygulama değiştirilmiş dosyaları oyun için hazır tek bir `.pak` dosyasında paketler.
2. **Dağıtın ve Çalıştırın:** En kolay test yöntemi `F5` tuşuna basmaktır. Alternatif olarak `Araçlar -> Modu Dağıt ve Oyunu Çalıştır` seçeneğini kullanabilirsiniz. Bu işlem `.pak` dosyasını oyunun `Paks` klasörüne kopyalar ve The Outlast Trials'ı başlatır.

---

## 🧑‍💻 Geliştirme Mimarisi

Uygulama kaynak kodu `outlast_trials_audio_editor/` Python paketi altında modüler olarak düzenlenmiştir. Tarihsel `OutlastTrialsAudioEditor.py` dosyası geriye dönük uyumlu, küçük bir başlatıcı olarak korunmuştur. Böylece mevcut çalıştırma komutları ve paketleme giriş noktaları çalışmaya devam eder.

Başlıca katmanlar:

- `common.py`: ortak bağımlılıklar, platform bayrakları, sürüm ve uygulama kök dizini.
- `i18n/`: yerleşik çeviri verileri.
- `models.py`: hafif veri modelleri.
- `debug.py`: loglama, hata ayıklama penceresi ve genel hata yakalama mekanizması.
- `services/`: BNK, WEM, ses, yerelleştirme ve ayar iş mantığı.
- `workers.py`: arka planda çalışan Qt iş parçacıkları.
- `profiles.py`: profil yönetimi ve mod içe aktarma akışı.
- `ui/`: yeniden kullanılabilir bileşenler, diyaloglar ve ana pencere.
- `ui/mixins/`: eski büyük ana pencere sınıfından ayrılan işlevsel modüller.
- `app.py`: uygulama başlangıcı ve açılış ekranı akışı.

Ayrıntılı modül haritası ve yeniden yapılandırma kuralları için [ARCHITECTURE.md](ARCHITECTURE.md) dosyasına bakın.

Regresyon testlerini çalıştırmak için:

```bash
python -m unittest discover -s tests -v
```

---

## 🤝 Katkıda Bulunma ve Topluluk

<div align="center">

[![Katkıda Bulunanlar](https://img.shields.io/badge/👥_Katkıda_Bulunun-orange?style=for-the-badge)](../../graphs/contributors)
[![Hatalar](https://img.shields.io/badge/🐛_Hata_Bildir-red?style=for-the-badge&logo=github)](../../issues)
[![Değişiklik İsteği](https://img.shields.io/badge/🔀_Değişiklik_İsteği_Aç-blue?style=for-the-badge&logo=github)](../../pulls)

<br>

| 🐛 Hata Bildirimi | 💡 Özellik Önerisi | 📖 Dokümantasyon | 💻 Kod |
| :---: | :---: | :---: | :---: |
| Bir sorun mu buldunuz?<br>[**Buradan bildirin**](../../issues) | Bir öneriniz mi var?<br>[**Fikrinizi paylaşın**](../../issues) | Kılavuzları geliştirin<br>**Değişiklik isteği gönderin** | Hataları düzeltin veya özellik ekleyin<br>**Depoyu çatallayıp katkıda bulunun** |

</div>

Katkı hazırlarken mümkün olduğunca şu ilkeleri uygulayın:

- Kullanıcı davranışını ve mevcut dosya formatı uyumluluğunu koruyun.
- Yeni iş mantığını uygun `services/`, `workers/` veya `ui/` modülüne ekleyin.
- Ana başlatıcı dosyayı yeniden büyütmeyin.
- Davranış değişiklikleri için test ekleyin.
- Windows dosya yolları, boşluk içeren klasör adları ve Unicode dosya adlarını göz önünde bulundurun.

---

## 💬 Destek ve İletişim

<div align="center">

### **🆘 Yardıma mı ihtiyacınız var?**

| 💬 Discord Desteği | 🐛 Hata Bildirimi |
| :---: | :---: |
| <img src="https://img.shields.io/badge/Discord-Bezna-7289da?style=for-the-badge&logo=discord" alt="Discord rozeti"/><br>**Discord: Bezna** | <a href="../../issues"><img src="https://img.shields.io/badge/GitHub-Hatalar-red?style=for-the-badge&logo=github" alt="GitHub hata bildirimleri"/></a><br><i>Teknik sorunlar ve hatalar</i> |

</div>

Bir hata bildirirken şunları ekleyin: ayrıntılı sorun açıklaması, hatayı yeniden oluşturma adımları, hata ayıklama günlüğü (`Ctrl+D`) ve ilgili dosya veya ekran görüntüleri.

---

## 🙏 Teşekkürler

Bu projenin geliştirilmesini mümkün kılan araçlara ve topluluklara teşekkür ederiz:

- **Red Barrels:** The Outlast Trials oyununu geliştirdikleri için.
- **vgmstream Ekibi:** Ses dönüştürme araçları için.
- **UnrealLocres Katkıcıları:** Yerelleştirme dosyası işleme desteği için.
- **hypermetric tarafından geliştirilen repak:** PAK dosyası oluşturma desteği için — büyük teşekkürler.
- **Audiokinetic:** Wwise ses motoru için.
- **PyQt5 Ekibi:** Grafik kullanıcı arayüzü çatısı için.
- **FFmpeg Ekibi:** Evrensel ses dönüştürme desteği için.
- **Bezna:** Orijinal OutlastTrials AudioEditor projesini geliştirdiği için.

## 💰 Projeyi Destekleyin

Bu araç işinize yaradıysa geliştirme sürecini destekleyebilirsiniz:

- [**DonationAlerts üzerinden destek olun**](https://www.donationalerts.com/r/bezna_)
- ⭐ GitHub deposuna yıldız verin.
- 📢 Aracı diğer mod geliştiricileriyle paylaşın.

---

<div align="center">

**The Outlast Trials modlama topluluğu için ❤️ ile geliştirildi.**

*İyi modlamalar!* 🎮

[⬆ Başa Dön](#-outlasttrials-audioeditor)

</div>
