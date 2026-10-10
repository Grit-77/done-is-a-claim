# Done is a claim

[English](README.md) · **Türkçe**

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/receipt.svg">
  <img src="assets/receipt-stamp.gif" alt="Done is a claim. Kırmızı SHOW THE RECEIPT damgası kırık beyaz kapağın üzerine basılıyor.">
</picture>

[Damgayı tekrar oynat](assets/receipt-stamp.gif) · [Hareketsiz kapak](assets/receipt.svg)

**Ajanınız “bitti” diyor. Bunu ne kanıtlar?**

Kod yazan ajanlar için gerçek olaylardan çıkarılmış 18 kural ve belirli sorunlara
odaklanan 6 skill. Ajana açık bir kabul hedefi verin, gerçek sonucu isteyin ve
kanıtı test edilen çalışmaya bağlı tutun. Kurallar ve skill’ler düz Markdown;
yerel araçlar isteğe bağlı. İhtiyacınız olan parçaları kullanın.

[Başlayın](#başlayın) · [Skill seçin](#skill-seçin) · [Demoyu deneyin](#yanlış-bir-yeşil-sonucu-görün) · [Olayları okuyun](INCIDENTS.md)

## Yanlış bir yeşil sonucu görün

Bir komut başarısız olur. Çıktısını okuyan süreç ise başarıyla tamamlanır. Yanlış
çıkış kodunu raporlarsanız başarısız bir kontrol, raporda yeşile döner.

[Çalıştırılabilir kaynak](examples/false_green.py). Bu sentetik bir örnektir;
üretim sistemi günlüğü veya performans ölçümü değildir.

Klonladığınız reponun kökünde, Python 3.10 veya üzeriyle kendiniz çalıştırın:

```bash
python examples/false_green.py
```

Demo, farkı ortaya çıkardığında başarılıdır. **İçindeki doğrulayıcı yine de
başarısızdır.** Demonun göstermek istediği ayrım budur.

## Başlayın

```bash
git clone https://github.com/Grit-77/done-is-a-claim.git
cd done-is-a-claim
```

| Kullandığınız ajan | Projenize ekleyin |
|---|---|
| Codex veya `AGENTS.md` okuyan bir ajan | [AGENTS.md](AGENTS.md) dosyasını projenin köküne kopyalayın. |
| Claude Code | [AGENTS.md](AGENTS.md) ile onu `@AGENTS.md` üzerinden içeri aktaran [CLAUDE.md](CLAUDE.md) dosyasını kopyalayın. |
| Mevcut talimatlarınız varsa | İlgili kuralları dosyanıza ekleyin. Projeye özel komutları ve kısıtları koruyun. |

Tek kural dosyasıyla başlayabilirsiniz. İsteğe bağlı skill'ler, belirli bir
sorunla karşılaştığınızda konuyu daha ayrıntılı ele alır.
[macOS, Linux veya Windows'ta skill kurulumu →](docs/INSTALL.md)

Mevcut dosyaların üzerine yazmadan proje içine bir skill kurmak için bu klonun
kökünde aşağıdaki planı çalıştırın. `../my-project` yerine mevcut proje yolunuzu yazın:

```bash
python tools/install_skills.py --project ../my-project --agent codex --skill reading-measurements --dry-run
```

Kurmak için `--dry-run` seçeneğini kaldırın. Claude Code için `--agent claude-code`
kullanın. Mevcut skill hedefleri reddedilir; proje talimatlarınız korunur.

Kendi projenizde ilk olarak şu isteği deneyin:

> Proje talimatlarını oku. Değişiklik yapmadan önce bu işin kabul komutunu ve
> komutun kontrol ettiği, kullanıcının görebileceği sonucu belirle. Sonucu
> raporlarken test edilen sürümü, gerçek çıktıyı ve kontrol etmediğin noktaları
> belirt.

Bu, ajanın isteği anlayıp anlamadığını kontrol eder. Talimatlara uymasını zorunlu
kılmaz.

## Komutun sonucunu kaydedin

İsteğe bağlı yerel araçla komutun kendi çıkış kodunu, tam çıktısını ve Git durumunu
kaydedin:

```bash
python tools/receipt.py -- python tools/run_tests.py
```

Her çalıştırma için `.local/receipts/` altında yeni bir `receipt.json` ve
`command.log` oluşturur. Seçtiğiniz dosyaların önceki ve sonraki parmak izlerini
karşılaştırmak için `--input` kullanın. Sıfır çıkış kodu komutun başarıyla
tamamlandığını kaydeder; kullanıcının görevinin bittiğine karar vermez.
[Kullanım, kontrol edilen girdiler ve sınırlar →](docs/RECEIPTS.md)

## Raporda ne değişir?

| İddia | İddiayı destekleyebilecek kanıt |
|---|---|
| “Testler geçti.” | Komut, bulunan testler, gerçek sonuç, komutun kendi çıkış kodu ve test edilen çalışma ağacı. |
| “Bu hata zaten ana dalda vardı.” | Dalda ve temiz temel sürümde yapılmış karşılaştırılabilir çalıştırmalar; eşleşen hata belirtileri. |
| “Alt ajan işi bitirdi.” | Alt ajanın gerçek değişiklikleri, kontrol edilen girdiler ve kabul sonucu. Teslim durumu ayrıca kaydedilir. |
| “Ekran görüntüsü kaydedildi.” | Açılabilen ve görsel olarak incelenmiş bir görüntü. |
| “Yayımlamaya hazır.” | İncelenen dosyalarla yayımlanacak dosyaların hâlâ aynı olması. |

[Tamamlama kaydı](templates/completion-receipt.md),
[kabul brief'i](templates/acceptance-brief.md) ve
[devir notunu](templates/handoff.md) küçük, tekrar kullanılabilir biçimler olarak
kullanın. Yapılmayan kontrol de raporda yer almalıdır.

[Bash ve PowerShell için pratik kanıt toplama örnekleri →](docs/RECIPES.md)

## Skill seçin

| Karşılaştığınız durum | Kullanılacak skill | Karar vermenize yardımcı olduğu soru |
|---|---|---|
| İşin hangi durumda “geçti” sayılacağı belirsiz | [acceptance-design](skills/acceptance-design/SKILL.md) | Bu kontrol, kullanıcının gerçekten önemsediği sınırı aşıyor mu? |
| Bir rakam ikna edici görünüyor | [reading-measurements](skills/reading-measurements/SKILL.md) | Bu çıktı neyi kanıtlıyor, neyi belirsiz bırakıyor? |
| Dalınızda bir test başarısız oluyor | [whose-red](skills/whose-red/SKILL.md) | Yeni bir hataya, mevcut bir hataya veya henüz çözülememiş bir nedene işaret eden karşılaştırılabilir kanıt var mı? |
| Bir alt ajan başarı bildiriyor | [collecting-worker-results](skills/collecting-worker-results/SKILL.md) | İlgili bir değişiklik var mı, test edildi mi ve teslim edildi mi? |
| Kontrolden sonra iş değişti | [evidence-freshness](skills/evidence-freshness/SKILL.md) | Sonuç kaydı, işlem yapacağınız girdileri hâlâ doğru anlatıyor mu? |
| Bir README veya duyuru iddia içeriyor | [public-claims](skills/public-claims/SKILL.md) | Okur iddianın kaynağına ulaşabiliyor mu ve doğrulamanın sınırları belirtilmiş mi? |

Her skill bağımsız bir `SKILL.md` dosyasıdır. Grit servisi, hesabı veya CLI'ı
gerekmez. Skill metinleri İngilizcedir.

## Sahadan gelen kurallar

Kuralların tam metni [AGENTS.md](AGENTS.md) dosyasındadır. Her özgün kuralın
arkasındaki hata hikâyesi [INCIDENTS.md](INCIDENTS.md) dosyasında yer alır.

| Aşama | Kurallar |
|---|---|
| **Başlamadan önce** | **01** Kabul koşulunu işten önce belirleyin. **02** Yolları kontrol edin. |
| **“Bitti” demeden önce** | **03** Güncel çalışmada yeniden kontrol edin. **04** Daha geniş test setini çalıştırın. **05** Komutun kendi çıkış kodunu kaydedin. **06** Test çalışmadıysa geçti saymayın. **07** Bilinmiyor, geçti demek değildir. **08** Gerekli kontrollerin hepsini okuyun. |
| **Rapor verirken** | **09** Asıl çıktıyı okuyun. **10** Yazılan dosyayı açın. **11** Kendi gözünüzle bakın. **12** Kaynakları doğrulayın. **13** Temel sürümü belirtin ve yayımlamadan önce yeniden kontrol edin. |
| **Test ve düzeltme yazarken** | **14** Bir sabitle uyumu değil, davranışı test edin. **15** Hata sınıfını düzeltin. **16** Dedektörü iyi olduğunu bildiğiniz bir örnekte sınayın. **17** Temizliği işten önce kaydedin. |
| **İşi her zaman koruyun** | **18** Bir soruyu yanıtlamak için asla yıkıcı bir komut kullanmayın. |

## Nereden çıktı?

Bu kurallar, Grit'in kendi deposunda Claude Code ve Codex çalıştırırken oluştu.
Özgün iç kayıtlar, 14–29 Eylül 2026 arasında **3.489** görevin kabul komutunun
yeniden çalıştırıldığını ve **2.282** görevin ilk bağımsız denemede geçtiğini
bildiriyor. Ayrı bir iç sayımda, kendi kabul kontrolünü geçtiği hâlde ana daldaki
test setinin tamamını bozan **736** görev raporlanıyor.

**Bunlar yazarın bildirdiği tarihsel gözlemlerdir; kamuya açık bir karşılaştırma
testi değildir.** Ham iç günlükler bu depoda bulunmaz. Başarısız denemelerin bir
kısmı ortam sorunlarından kaynaklanmıştır; bu rakamlar bir ajan hata oranı veya
bu araç setinin etkinliğini kanıtlamaz. [İddialar ve sınırları →](CLAIMS.md)

Ek iş akışları, Grit'in operasyon yönergelerinden derlenmiştir. Yeni ölçülmüş
olaylar olarak değil, rehberlik olarak tanımlanırlar. İlgili projelerin kurulum,
skill ve doğrulama düzenlerini de inceledik.
[Kaynaklar ve tasarım kararları →](SOURCES.md)

## Yanıltmayı deneyin

Bir ajan kuralı tekrar edip yine de yanlış karar verebilir.
[Senaryo paketi](evals/README.md), talimatları zor durumlarda sınar: başarılı
görünen bir pipe, uyumsuz kontrol koşulları, ilgili hiçbir değişikliği olmayan
bir alt ajan, güncelliğini yitirmiş kanıt ve başka tuzaklar. Katılımcı istekleri
değerlendirici cevap anahtarından ayrı dosyalardadır. İstekleri yeni oturumlarda
çalıştırın ve yanıtları saklayın.

Bunlar elle yürütülen davranış değerlendirmeleridir; yayımlanmış başarı oranı
iddiaları değildir.

Deponun kendisini kontrol etmek için:

```bash
python tools/run_tests.py
python tools/check_repository.py
```

Test çalıştırıcısı, hiç test bulunmamasını ve testlerin tamamının atlanmasını
başarısız sayar.

Bu kontroller araçları sınar; yerel belge hedeflerini, skill üst bilgilerini ve
içeri aktarımları doğrular. [CI](.github/workflows/check.yml), Windows ve Linux'ta
çalışır. Bu kontrollerin geçmesi, ajanın talimatlara uyduğunu kanıtlamaz.

## Kural, denetim kapısı değildir

Bu depo talimatlar, küçük yerel araçlar, örnekler ve değerlendirme malzemeleri sunar. Ajanın araç
çağrılarına müdahale etmez, birleştirme işlemini engellemez veya dağıtım
politikasını zorunlu kılmaz. Kuralları uygulatmak için projenizin gerçek test ve yayımlama
kontrollerini kullanın. Grit'in ayrı
[RADAR projesi](https://github.com/Grit-77/radar) bu operasyon katmanını araştırır.

## Size ders olan hatayı getirin

Yararlı bir katkı, ajanın ne iddia ettiği, gerçekte ne olduğu ve aradaki farkı
hangi kanıtın ortaya çıkardığıyla başlar.
[Bir kural önerin](https://github.com/Grit-77/done-is-a-claim/issues/new?template=new-rule.yml)
veya [katkı rehberini okuyun](CONTRIBUTING.md).

Kendi projenizde denediniz mi? [Somut bir kullanım deneyimi paylaşın](https://github.com/Grit-77/done-is-a-claim/issues/new?template=use-report.yml):
hangi parçayı kullandığınız, ne olduğu ve neyin belirsiz kaldığı.

[Apache-2.0](LICENSE) · [Grit](https://github.com/Grit-77) tarafından hazırlandı, Ankara.
