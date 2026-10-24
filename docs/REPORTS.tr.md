# Bir sonraki PR'ınıza kanıt kaydı ekleyin

Projenizin gerçek kontrolünü çalıştırın, ardından yerel kayıt belgesini Markdown veya küçük bir JSON özetine dönüştürün. Bu isteğe bağlı araçlar için eklenti veya sağlayıcı hesabı gerekmez; Python 3.10+ ve bu araç setinin bir klonu yeterlidir. Yalnızca skill'leri kurmak Python araçlarını projenize eklemez.

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

Raporlayıcı varsayılan olarak terminale Markdown yazar. İnceleyin, sonra kabul koşulunuz ve çalıştırmadığınız kontrollerle birlikte bunu PR açıklamasına veya yorumuna kopyalayın. Araç hiçbir şey yayımlamaz veya kaydedilen komutu yeniden çalıştırmaz. Ham kayıtlar ve günlükler yerel kalmalıdır; henüz yoksa projenizin ignore kurallarına `.local/` ekleyin.

## CI tüketicileri için isteğe bağlı JSON

Makine tarafından okunabilen paylaşılabilir özet için aynı kayıt ve proje ile
`--format json` kullanın:

```bash
python tools/report_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project --format json
```

Bu, ham kayıt veya yerel yeniden denetleyicinin tanı JSON'u değil, ayrı bir
**paylaşılabilir özet v1** biçimidir. Tam olarak altı alan içerir:

```json
{
  "schema_version": 1,
  "historical_command_status": "command_succeeded",
  "historical_child_exit": 0,
  "recheck_state": "different",
  "freshness": "changed",
  "reason_code": "observations_differ"
}
```

Örnek, kaydedilmiş sıfır çıkışından sonra seçilen baytların değişmesini gösterir;
geçmiş komut sonucunu bugünkü başarı iddiasına dönüştürmez.
`historical_command_status`; `command_succeeded`, `command_failed`, `not_run`
veya `null` olur. Kaydedilmiş `not_run`, geçmiş sonucun bilinmemesinden ayrılır.
Alt süreç çıkışı tamsayı veya `null` olur; mevcut Markdown'ın taşınabilir aralığı,
`-2147483648` ile `4294967295`, korunur. Daha büyük veya küçük değerler `null`
olarak saklı tutulur; yeniden kontrol durumu ve raporlayıcı çıkışı değişmez.
Genel durum `invalid` ise iki geçmiş alanı da `null` olur.

`freshness`; `different` için `changed`, `invalid` veya `incomplete` için
`unverifiable`, diğer durumlarda `matches` olur. Eşleşen gözlemler yine de
kaydedilmiş başarısızlık içerebilir. Bu değerler yalnızca seçilen gözlem kapsamını
anlatır.

| Yeniden kontrol durumu | Sabit `reason_code` |
| --- | --- |
| `matches` | `observations_match` |
| `different` | Önceden yakalanmış seçili girdi eksikse `selected_input_missing`; değilse `observations_differ` |
| `invalid` | `invalid_evidence_or_context` |
| `recorded_failure` | Kayıt sırasında oluşan hata veya girdi/HEAD değişimi dahil `historical_failure` |
| `incomplete` | Yapılandırılmış bir bileşen kullanılamıyorsa `observation_unavailable`; değilse `evidence_incomplete` |

Neden seçilmeden önce mevcut genel durum ve çıkış önceliği uygulanır. Tek neden,
tüm gözlemleri değil, baskın koşulu anlatır. Neden kodları dosya adı veya istisna
metni içermez.

JSON; argümanları, günlük içeriğini, yolları, dosya adlarını, karmaları, HEAD
değerlerini, zaman damgalarını, sayıları ve serbest biçimli tanıları çıkarır.
`--include-command` ile birleştirilemez; bu birleşim çıkış `2` ile özel verileri
göstermeyen bir CLI hatası verir ve özet üretmez. Diğer CLI ayrıştırma hatalarında
da stdout boş olabilir. Geçersiz kanıt veya bağlam ise altı alanlı `invalid`
özetini üretir. Bunun yerine `tools/check_receipt.py --json` kullanmayın: o yerel
tanı biçimi yolları gösterebilir.

JSON'u ayrıştırırken veya paylaşırken raporlayıcının kendi sıfır olmayan çıkışını
görünür tutun; sonraki ayrıştırıcının başarısı onun yerine geçmez. Markdown,
bilerek seçilen `--include-command` seçeneğiyle birlikte varsayılan olmaya devam
eder. İki biçim de kaydedilmiş komutu yeniden çalıştırmaz veya ileri sürülen
geçmiş sonucun özgünlüğünü kanıtlamaz.

Şema ve test planı tasarım katkısı:
[sacravenger / NaN Mesh](https://github.com/Grit-77/done-is-a-claim/issues/14#issuecomment-6389322903).


## İki sonucu ayrı okuyun

Raporun bir **geçmiş alt süreç çıkışı** ve bir **yeniden kontrol durumu** vardır. Bir komut `7` ile döndüyse, seçilen baytların tümü hâlâ eşleşse bile kaydedilmiş başarısızlık olarak kalır. `0` ile dönen bir komutun kanıtı ise bir düzenlemeden sonra bayatlamış olabilir.

| Raporlayıcı çıkışı | Yeniden kontrol durumu | Anlamı |
| --- | --- | --- |
| 0 | `matches` | Seçilen gözlemler eşleşir; kaydedilmiş komut hatası veya değişiklik yoktur. Bu, testlerin çalıştığını veya görevin tamamlandığını kanıtlamaz. |
| 1 | `different` | Seçilen bir dosya veya günlük farklı ya da eksik, ya da Git HEAD farklı. |
| 2 | `invalid` | Meta veri veya gerekli yerel gözlem geçersiz ya da kullanılamaz. Ayrıntılar için yerel yeniden denetleyiciyi kullanın. |
| 3 | `recorded_failure` | Eşleşen mevcut gözlemler, geçmişteki komut hatasını, çalışmama durumunu veya girdi/HEAD değişimini korur. |
| 4 | `incomplete` | Kanıtta gerekli kapsam veya gözlemler eksik; örneğin seçilmiş dosyalar veya bağlı günlük SHA-256 karması yok. |

Bunlar, yakalanan alt sürecin çıkış kodu değil, **raporlayıcı** çıkışlarıdır. Farklılıklar eksikliğe, eksiklik de kaydedilmiş başarısızlığa göre önceliklidir; geçmiş sonuç her geçerli raporda görünmeye devam eder. Markdown'ı başarıyla yazdırmış olsa bile otomasyonda sıfır olmayan raporlayıcı sonucunu görünür tutun. [Tam yeniden kontrol anlamları](RECHECK.md).

Tablo; seçilen girdi sayılarını, günlük SHA-256 karmalarını, isteğe bağlı Git HEAD değerlerini ve doğrulanmış zaman damgalarını içerir. Dosya adlarını ve serbest biçimli hata metnini kasıtlı olarak çıkarır. Yerelde incelemek için şunu çalıştırın:

```bash
python tools/check_receipt.py ../my-project/.local/receipts/run-EXAMPLE/receipt.json --project ../my-project --json
```

Bu tanı çıktısı yerel yollar ve dosya adları içerebilir. Paylaşmadan önce gözden geçirin.

## Yalnızca paylaşmak istediğiniz bilgileri paylaşın

Varsayılan Markdown, komut bağımsız değişkenlerini, günlük içeriğini, yerel yolları, dosya adlarını ve serbest biçimli tanıları çıkarır. Buna rağmen zaman damgalarını, durum/sayıları, günlük SHA-256 karmalarını ve isteğe bağlı Git HEAD değerlerini açıklar. Bu araç bir gizli bilgi tarayıcısı veya her gözlemin paylaşmaya uygun olduğuna dair bir güvence değildir.

Kaydedilmiş bağımsız değişkenleri bilerek eklemek isterseniz `--include-command` kullanın. Bağımsız değişkenler gizli bilgi içerebilir. Bunlar kopyalayıp çalıştırılacak bir kabuk komutu olarak değil, kaçışlanmış ve sınırlı bir dizi olarak gösterilir. Paylaşmadan önce inceleyin; ham günlükler hiçbir zaman dahil edilmez.

Kayıtlar düzenlenebilir yerel dosyalardır, imzalı tasdikler değildir. Eşleşen karmalar, sağlanan kayıtla tutarlılığı gösterir; özgünlüğünü göstermez. Kontroller atomik değildir ve seçilen dosyalar, bitişik günlük ve isteğe bağlı Git HEAD ile sınırlıdır. Rapor, kabul koşullarınızın yeterince iyi olup olmadığına veya kullanıcının amaçladığı sonuca ulaşılıp ulaşılmadığına karar veremez.

## Ajanınıza sorun

> Bu değişiklik için kabul kontrolünü kayıt aracıyla çalıştır. İlgili kaynak ve test dosyalarını seç, gerçek çıktıyı incele ve varsayılan Markdown raporunu oluştur. Kontrolün neyi kanıtladığını ve neyin hâlâ doğrulanmadığını açıkla. Ham kayıtları yerelde tut ve paylaşmadan önce özeti bana göster.

Bu, yanıltıcı bir sonucu yakalamanıza yardımcı olduysa veya kafa karıştırıcı geldiyse, sürümü, görev sınırını, gözlenen sonucu ve sınırlamaları içeren bir [kullanım raporu](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml) gönderin. Önce özel bilgileri çıkarın.
