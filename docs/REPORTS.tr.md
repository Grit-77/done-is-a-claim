# Bir sonraki PR'ınıza kanıt kaydı ekleyin

Projenizin gerçek kontrolünü çalıştırın, ardından yerel kayıt belgesini Markdown özetine dönüştürün. Bu isteğe bağlı araçlar için eklenti veya sağlayıcı hesabı gerekmez; Python 3.10+ ve bu araç setinin bir klonu yeterlidir. Yalnızca skill'leri kurmak Python araçlarını projenize eklemez.

[English](REPORTS.md) · **Türkçe**

## Mevcut projenizi kullanın

Araç seti klonunu ve projenizi ayrı tutun. Araç setinin kökünden, `../my-project` yerine mevcut proje yolunuzu yazın. Bu örnek, projenizde `app.py` ve `test_app.py` bulunduğunu varsayar; bunların yerine gerçek kaynak ve test dosyalarınızı, ayrıca gerçek kontrol komutunuzu seçin:

```bash
python tools/receipt.py --cwd ../my-project --input app.py --input test_app.py -- python -m unittest test_app
```

Komut **projenizin içinde** çalışır. Araç, yeni bir `receipt.json` dosyasının tam yolunu yazdırır; yanındaki `command.log` tam komut çıktısını içerir. Bu çıktıyı okuyun ve görevinizin kabul koşullarıyla karşılaştırın. Daha fazla mevcut dosya seçmek için `--input` seçeneğini tekrarlayın. Seçilmemiş dosyalar, bağımlılıklar ve ortam, dosya karşılaştırmasının dışındadır.

Yazdırılan kayıt yolunu sonraki komutta kullanın. `run-EXAMPLE` yerine gerçek dizini yazın ve aynı proje kökünü koruyun:

```bash
python tools/report_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project
```

Raporlayıcı terminale Markdown yazar. İnceleyin, sonra kabul koşulunuz ve çalıştırmadığınız kontrollerle birlikte bunu PR açıklamasına veya yorumuna kopyalayın. Araç hiçbir şey yayımlamaz veya kaydedilen komutu yeniden çalıştırmaz. Ham kayıtlar ve günlükler yerel kalmalıdır; henüz yoksa projenizin ignore kurallarına `.local/` ekleyin.

## İki sonucu ayrı okuyun

Raporun bir **geçmiş alt süreç çıkışı** ve bir **yeniden kontrol durumu** vardır. Bir komut `7` ile döndüyse, seçilen baytların tümü hâlâ eşleşse bile kaydedilmiş başarısızlık olarak kalır. `0` ile dönen bir komutun kanıtı ise bir düzenlemeden sonra bayatlamış olabilir.

| Raporlayıcı çıkışı | Yeniden kontrol durumu | Anlamı |
| --- | --- | --- |
| 0 | `matches` | Seçilen gözlemler eşleşir; kaydedilmiş komut hatası veya değişiklik yoktur. Bu, testlerin çalıştığını veya görevin tamamlandığını kanıtlamaz. |
| 1 | `different` | Seçilen bir dosya, günlük veya Git HEAD farklı ya da eksik. |
| 2 | `invalid` | Meta veri veya gerekli yerel gözlem geçersiz ya da kullanılamaz. Ayrıntılar için yerel yeniden denetleyiciyi kullanın. |
| 3 | `recorded_failure` | Eşleşen mevcut gözlemler, geçmişteki komut hatasını, çalışmama durumunu veya girdi/HEAD değişimini korur. |
| 4 | `incomplete` | Kanıtta gerekli kapsam veya gözlemler eksik; örneğin seçilmiş dosyalar veya bağlı günlük özeti yok. |

Bunlar, yakalanan alt sürecin çıkış kodu değil, **raporlayıcı** çıkışlarıdır. Farklılıklar eksikliğe, eksiklik de kaydedilmiş başarısızlığa göre önceliklidir; geçmiş sonuç her geçerli raporda görünmeye devam eder. Markdown'ı başarıyla yazdırmış olsa bile otomasyonda sıfır olmayan raporlayıcı sonucunu görünür tutun. [Tam yeniden kontrol anlamları](RECHECK.md).

Tablo; seçilen girdi sayıları, günlük özetleri, isteğe bağlı Git commit özetleri ve doğrulanmış zaman damgalarını içerir. Dosya adlarını ve serbest biçimli hata metnini kasıtlı olarak çıkarır. Yerelde incelemek için şunu çalıştırın:

```bash
python tools/check_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project --json
```

Bu tanı çıktısı yerel yollar ve dosya adları içerebilir. Paylaşmadan önce gözden geçirin.

## Yalnızca paylaşmak istediğiniz bilgileri paylaşın

Varsayılan Markdown, komut bağımsız değişkenlerini, günlük içeriğini, yerel yolları, dosya adlarını ve serbest biçimli tanıları çıkarır. Buna rağmen zaman damgalarını, durum/sayıları, günlük özetlerini ve isteğe bağlı Git commit özetlerini açıklar. Bu araç bir gizli bilgi tarayıcısı veya her gözlemin paylaşmaya uygun olduğuna dair bir güvence değildir.

Kaydedilmiş bağımsız değişkenleri bilerek eklemek isterseniz `--include-command` kullanın. Bağımsız değişkenler gizli bilgi içerebilir. Bunlar kopyalayıp çalıştırılacak bir kabuk komutu olarak değil, kaçışlanmış ve sınırlı bir dizi olarak gösterilir. Paylaşmadan önce inceleyin; ham günlükler hiçbir zaman dahil edilmez.

Kayıtlar düzenlenebilir yerel dosyalardır, imzalı tasdikler değildir. Eşleşen özetler, sağlanan kayıtla tutarlılığı gösterir; özgünlüğünü göstermez. Kontroller atomik değildir ve seçilen dosyalar, bitişik günlük ve isteğe bağlı Git HEAD ile sınırlıdır. Rapor, kabul koşullarınızın yeterince iyi olup olmadığına veya kullanıcının amaçladığı sonuca ulaşılıp ulaşılmadığına karar veremez.

## Ajanınıza sorun

> Bu değişiklik için kabul kontrolünü kayıt aracıyla çalıştır. İlgili kaynak ve test dosyalarını seç, gerçek çıktıyı incele ve varsayılan Markdown raporunu oluştur. Kontrolün neyi kanıtladığını ve neyin hâlâ doğrulanmadığını açıkla. Ham kayıtları yerelde tut ve paylaşmadan önce özeti bana göster.

Bu, yanıltıcı bir sonucu yakalamanıza yardımcı olduysa veya kafa karıştırıcı geldiyse, sürümü, görev sınırını, gözlenen sonucu ve sınırlamaları içeren bir [kullanım raporu](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml) gönderin. Önce özel bilgileri çıkarın.
