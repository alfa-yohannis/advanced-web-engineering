# Advanced Web Engineering

## Peta Pertemuan

Urutan pertemuan disusun untuk menopang pengerjaan empat topik penelitian teratas. Materi yang paling dibutuhkan diletakkan paling awal. Materi yang paling jauh kaitannya diletakkan paling akhir. Kolom terakhir menunjukkan topik penelitian yang dilayani.

| # | Pertemuan | Praktikum | Menopang |
| --- | --- | --- | --- |
| 1 | **Overview Mata Kuliah & Alur Rekayasa** | Penyiapan *environment*, inisialisasi *monorepo*, alur Git, kerangka CI, dan kerangka API minimal | semua |
| 2 | Browser, HTTP & Network Internals | Memprofil aplikasi yang sengaja dibuat lambat, lalu menetapkan *baseline* performa | T1, T5 |
| 3 | Data Engineering for Web Applications | Merancang skema, migrasi, dan batas transaksi; mengoptimalkan *query* terpilih | **T1, T6** |
| 4 | Caching, Consistency & Resilience | Menerapkan *caching* dan *resilience*, lalu membandingkannya dengan *baseline* Pertemuan 2 | **T1** |
| 5 | Performance Engineering | Memenuhi anggaran latensi dan Core Web Vitals. Praktikum gagal bila anggaran terlampaui | **T1**, T5 |
| 6 | Testing, Reliability & Code Quality | Membangun *pipeline* pengujian otomatis dan CI yang memblokir *merge* cacat | **T6** |
| 7 | Web Application Security | Menyerang *branch* yang sengaja dibuat rentan, mendokumentasikan eksploitasi, lalu menambalnya | **T2** |
| 8 | Modern Web Architecture | Membandingkan tiga arsitektur untuk satu kebutuhan, lalu menulis keputusannya | **T5** |
| 9 | Cloud Deployment, DevOps & Observability | Men-*deploy*, menginstrumentasi, membuat *dashboard*, dan satu *alert* bermakna | **T6** |
| 10 | Identity, Authentication & Authorization | Menambahkan *authentication*, *authorization*, dan isolasi *tenant* | **T2** |
| 11 | Frontend Architecture at Scale | Membangun *application shell*, *routing*, *layout*, dan arsitektur komponen | **T5** |
| 12 | Type Safety, API Contracts & Service Design | Memformalkan kontrak API, meng-*generate* tipe, menguji kompatibilitas versi, memasang *gateway* dan *rate limiting* | **T2** |
| 13 | Real-Time & Asynchronous Systems | Membangun satu fitur *real-time* dan satu alur asinkron | T3 |
| 14 | Scaling, Distributed Web Systems & Emerging Web | Latihan evolusi arsitektur pada beban 100 kali lipat, ditambah eksperimen satu teknologi *emerging* | T4 |

Pertemuan 1 sampai 5 memasok Topik 1 secara berurutan. Pertemuan 6 sampai 12 berselang-seling antara tiga jalur: **T6, T2, T5, T6, T2, T5, T2**. Susunan berselang ini membuat ketiga jalur berjalan paralel. Tidak ada tim yang menganggur menunggu satu jalur selesai. Pertemuan 13 dan 14 menutup dengan materi bagi dua topik berprioritas terendah.

**Titik siap eksekusi penelitian.** T1 siap setelah Pertemuan 5. T6 setelah Pertemuan 9. T5 setelah Pertemuan 11. T2 setelah Pertemuan 12. Susunan berselang punya satu konsekuensi. Tidak ada topik yang menunggu lama untuk dimulai, tetapi topik yang selesai paling akhir, yaitu T2, hanya menyisakan dua pertemuan untuk eksperimen dan penulisan. Sebagian besar bahan T2 sebenarnya sudah tersedia sejak Pertemuan 7 dan 10. Pertemuan 12 hanya melengkapi sisi *gateway* dan *rate limiting*, sehingga eksperimen dapat dimulai lebih awal.

---

## Rencana Pertemuan

### Bagian I. Fondasi dan Pengukuran (1 sampai 2)

#### Pertemuan 01 · Overview Mata Kuliah & Alur Rekayasa

Orientasi, tanpa materi teknis mendalam. Pembahasan mencakup arti "advanced" pada mata kuliah ini dan bedanya dengan pemrograman web pengantar. Dilanjutkan penelusuran 14 pertemuan, aplikasi yang dibangun bersama, dan enam topik penelitian yang ditopangnya. *Tech stack* yang dipakai dijelaskan beserta alasan pemilihannya. Bagian terakhir membahas alur kerja rekayasa yang berlaku sepanjang semester: *monorepo*, strategi *branching*, aturan *code review*, dan kerangka CI (*Continuous Integration*).

**Praktikum.** Penyiapan *environment* berupa *runtime*, *package manager*, Docker, dan *database client*, lalu diverifikasi dengan skrip *smoke test*. Dilanjutkan inisialisasi *monorepo*, alur Git, dan kerangka CI yang sudah hijau. Ditambah kerangka API minimal berpola *route*, *service*, *repository*, agar praktikum berikutnya punya sistem untuk diukur.

#### Pertemuan 02 · Browser, HTTP & Network Internals

**Topik.** Arsitektur browser. DNS (*Domain Name System*), TCP (*Transmission Control Protocol*), dan TLS (*Transport Layer Security*). Perbandingan HTTP (*HyperText Transfer Protocol*) 1.1, HTTP/2, dan HTTP/3. Siklus hidup *request*. *Event loop*. *Rendering pipeline* dan *critical rendering path*. Core Web Vitals. Penguasaan *browser DevTools*.

**Praktikum.** Memprofil aplikasi yang sengaja dibuat lambat. Hasilnya adalah *baseline* performa berupa **angka**, yaitu Core Web Vitals dan latensi server pada persentil 50 dan 95. Angka tersebut diuji ulang pada Pertemuan 4 dan 5.

### Bagian II. Data, Caching, dan Performa (3 sampai 5)

#### Pertemuan 03 · Data Engineering for Web Applications

**Topik.** Pemodelan relasional dan SQL (*Structured Query Language*). Perbandingan ORM (*Object-Relational Mapping*), *query builder*, dan SQL langsung. Transaksi dan ACID (*Atomicity, Consistency, Isolation, Durability*). *Isolation level*. Konkurensi. Masalah N+1. *Indexing*. Pembacaan *query plan*. *Connection pooling*. Migrasi.

**Praktikum.** Merancang skema produksi, migrasi, dan batas transaksi. Mengoptimalkan *query* terpilih, disertai *query plan* sebelum dan sesudah perbaikan.

#### Pertemuan 04 · Caching, Consistency & Resilience

**Topik.** *Caching* di browser dan HTTP. Header `Cache-Control`. CDN (*Content Delivery Network*). *Cache* tingkat aplikasi memakai Redis. Pola *cache-aside*. Invalidasi. Pemilihan TTL (*Time To Live*). Strategi `stale-while-revalidate`. *Optimistic update*. *Eventual consistency*. *Resilience* melalui *timeout*, *retry*, dan *circuit breaker*.

**Praktikum.** Menerapkan *caching* dan mekanisme *resilience*. Hasil pengukurannya dibandingkan dengan *baseline* Pertemuan 2.

#### Pertemuan 05 · Performance Engineering

**Topik.** Anggaran performa. Metodologi *profiling*. Analisis *bundle*. *Tree shaking*. *Code splitting*. *Lazy loading*. Optimasi gambar dan huruf. *Streaming* SSR. *Tuning* basis data dan *query*. *Load testing*. Identifikasi *bottleneck* skalabilitas.

**Praktikum.** Memenuhi anggaran latensi dan Core Web Vitals yang sudah ditetapkan secara eksplisit. **Praktikum dinyatakan gagal bila anggaran tidak terpenuhi.** Perbaikan tanpa bukti pengukuran tidak dihitung.

> Sampai titik ini seluruh perkakas untuk **Topik 1** sudah lengkap. Skema dan *query* dari Pertemuan 03. Mekanisme *caching* dari Pertemuan 04. *Load generator* dan cara membaca hasilnya dari Pertemuan 05.

### Bagian III. Jalur Berselang T6, T2, dan T5 (6 sampai 12)

Tiga jalur penelitian dijalankan bergantian. Tujuannya agar tim yang mengerjakan ketiganya sama-sama bergerak, bukan mengantre.

#### Pertemuan 06 · Testing, Reliability & Code Quality, *jalur T6*

**Topik.** Perbandingan *unit test*, *integration test*, dan E2E (*End-to-End*). *Testing pyramid* dan *testing trophy*. *Test double*. Pengujian dengan basis data di dalam *container*. Playwright. Pengujian API dan *contract testing*. Konsep *property-based testing*. Analisis statis. Keterbatasan *coverage* sebagai metrik. *Quality gate* di CI.

**Praktikum.** Membangun *pipeline* pengujian otomatis. Mengonfigurasi CI agar memblokir *merge* yang cacat.

#### Pertemuan 07 · Web Application Security, *jalur T2*

**Topik.** *Threat modelling*. OWASP (*Open Worldwide Application Security Project*) Top 10. XSS (*Cross-Site Scripting*). CSRF (*Cross-Site Request Forgery*). Injeksi SQL dan perintah sistem. SSRF (*Server-Side Request Forgery*). CORS (*Cross-Origin Resource Sharing*). CSP (*Content Security Policy*). Cookie yang aman. Manajemen *secret*. Serangan lewat dependensi. Keamanan rantai pasok perangkat lunak.

**Praktikum.** Menyerang *branch* yang sengaja dibuat rentan. Eksploitasi yang berhasil didokumentasikan, lalu seluruh temuan ditambal pada *branch* utama.

#### Pertemuan 08 · Modern Web Architecture, *jalur T5*

**Topik.** Evolusi dari aplikasi web tradisional ke SPA (*Single-Page Application*), SSR (*Server-Side Rendering*), SSG (*Static Site Generation*), dan ISR (*Incremental Static Regeneration*). *Islands architecture*. Perbandingan *server component* dan *client component*. Perbandingan *edge* dan *origin*. *Monolith*, *modular monolith*, dan BFF (*Backend for Frontend*). Cara membaca dan mempertanggungjawabkan *trade-off* arsitektur.

**Praktikum.** Mengambil satu kebutuhan nyata, lalu membandingkan tiga alternatif arsitektur untuknya. Hasilnya adalah keputusan singkat berisi opsi yang dipertimbangkan, pilihan yang diambil, dan konsekuensinya.

#### Pertemuan 09 · Cloud Deployment, DevOps & Observability, *jalur T6*

**Topik.** *Container*. *Twelve-factor app*. Konfigurasi dan *secret*. CI/CD (*Continuous Integration / Continuous Delivery*). IaC (*Infrastructure as Code*). *Reverse proxy*. *Deployment* ke *cloud* dan *edge*. Rilis *blue-green* dan *canary*. *Rollback*. OpenTelemetry beserta *log*, metrik, dan *trace*. Dasar SLI dan SLO (*Service Level Indicator* dan *Service Level Objective*).

**Praktikum.** Men-*deploy* aplikasi ke produksi. Menginstrumentasi aplikasi tersebut. Membuat *dashboard* operasional. Mengonfigurasi minimal satu *alert* yang bermakna.

> **Topik 6** lengkap. Pembacaan *query plan* dari Pertemuan 03. Uji integrasi dan gerbang CI dari Pertemuan 06. Instrumentasi *query* dari Pertemuan 09.

#### Pertemuan 10 · Identity, Authentication & Authorization, *jalur T2*

**Topik.** Cookie dan *session*. JWT (*JSON Web Token*). OAuth 2.x (*Open Authorization*). OpenID Connect (OIDC). *Access token* dan *refresh token*. Rotasi token. Perbandingan RBAC (*Role-Based Access Control*) dan ABAC (*Attribute-Based Access Control*). Model *permission*. *Multi-tenancy*. *Identity provider* dan konsep *zero trust*.

**Praktikum.** Menambahkan *authentication*, *authorization*, serta isolasi *tenant* pada aplikasi.

#### Pertemuan 11 · Frontend Architecture at Scale, *jalur T5*

**Topik.** Batas komponen dan komposisi. *Design system*. Arsitektur *state*. Perbandingan *server state* dan *client state*. Penerapan *server component* dan *client component*. Perbandingan hidrasi penuh dan hidrasi selektif. *Routing*. Strategi pengambilan data. *Error boundary*. Aksesibilitas. *Progressive enhancement*.

**Praktikum.** Membangun *application shell*, *routing*, *layout*, serta arsitektur komponen. Membandingkan biaya hidrasi antara dua varian halaman yang sama.

> **Topik 5** lengkap. Perkakas pengukuran dari Pertemuan 02 dan 05. Strategi *rendering* dari Pertemuan 08. Mekanisme hidrasi dari Pertemuan 11.

#### Pertemuan 12 · Type Safety, API Contracts & Service Design, *jalur T2*

**Topik.** TypeScript untuk sistem besar. Perbandingan validasi *runtime* dan *compile-time*. *Schema validation*. OpenAPI dan pengembangan *contract-first*. *Client* hasil generate. DTO (*Data Transfer Object*). Validasi di batas sistem. Kompatibilitas dan *versioning* API (*Application Programming Interface*). Bagian kedua membahas desain layanan: *constraint* REST (*Representational State Transfer*) beserta tingkat kematangannya, GraphQL, konsep RPC (*Remote Procedure Call*) beserta tRPC dan gRPC, *trade-off* pemilihan gaya API, *pagination*, *filtering*, model error, *idempotency*, *rate limiting*, API *gateway*, dan pola BFF.

**Praktikum.** Memformalkan kontrak API yang selama ini tumbuh organik. Kontrak ditulis sebagai OpenAPI. Antarmuka *client* dan server yang bertipe di-*generate* dari kontrak tersebut. Terakhir, kompatibilitas terhadap versi sebelumnya diuji.

> **Topik 2** lengkap. Skenario ancaman berupa token dicuri lalu diputar ulang dari Pertemuan 07. Alur token dari Pertemuan 10. *Gateway* dan *rate limiting* dari Pertemuan 12.

### Bagian IV. Sistem Asinkron dan Skala (13 sampai 14)

#### Pertemuan 13 · Real-Time & Asynchronous Systems

**Topik.** Perbandingan *polling*, SSE (*Server-Sent Events*), dan WebSocket. *Publish/subscribe*. Antrean. *Background worker*. *Scheduled job*. *Webhook*. *Retry* dan *exponential backoff*. *Consumer* yang idempoten. Pengiriman *at-least-once*. *Eventual consistency*.

**Praktikum.** Membangun satu fitur *real-time* dan satu alur asinkron secara utuh dari ujung ke ujung.

#### Pertemuan 14 · Scaling, Distributed Web Systems & Emerging Web

**Topik.** Penskalaan vertikal dan horizontal. Perpindahan dari *modular monolith* menuju *microservices*. Penentuan batas layanan. *Trade-off* sistem terdistribusi. Sistem *multi-region*. *Edge computing*. Bagian akhir membahas arah teknologi yang sedang tumbuh: PWA (*Progressive Web App*) dan *offline-first*, WebAssembly (Wasm), *serverless*, serta aplikasi web terintegrasi LLM (*Large Language Model*) beserta pertimbangan latensi, biaya, privasi, dan keamanan.

**Praktikum.** Latihan evolusi arsitektur. Rencana penskalaan aplikasi disusun untuk beban 100 kali lipat, mencakup batas layanan, replikasi, partisi, dan biaya. Ditambah eksperimen kecil pada satu teknologi *emerging*, misalnya mode *offline* PWA, satu fungsi *serverless* di *edge*, atau satu fitur berbantuan LLM.

---

## Topik Penelitian Skala Q3 dan Q4

Keenam topik diturunkan dari materi di atas. Semuanya mengikuti pola argumen yang sama:

> **Masalah**, lalu **Solusi A** menyelesaikannya tetapi memunculkan *trade-off* atau efek samping, lalu **Komponen B** ditambahkan untuk menekan efek samping tersebut sekaligus menaikkan kualitas A.

Sasarannya adalah artikel jurnal terindeks Q3 sampai Q4. Kebaruan yang dikejar berupa **kombinasi dan evaluasi empiris pada beban kerja web yang realistis**, bukan teori baru. Keenamnya memakai *testbed* yang sama, yaitu Docker Compose, PostgreSQL, Redis, k6 atau Locust, dan OpenTelemetry. Satu investasi infrastruktur menghasilkan enam naskah.

### Topik 1 · Invalidasi Cache Hibrida untuk Menekan Data Basi Tanpa Mengorbankan Hit Ratio

*Kaitan materi: Pertemuan 3 sampai 5, yaitu lapisan data, caching, dan performance engineering.*

**Masalah.** Aplikasi web dengan beban baca dominan menumpuk tekanan pada basis data. Latensi persentil 95 naik dan biaya *origin* membengkak saat trafik memuncak.

**Solusi A: *cache-aside* dengan Redis.** *Hit ratio* tinggi, latensi baca turun drastis, dan beban basis data berkurang.

**Efek samping A.** Ada tiga. Pertama, data basi selama rentang TTL, dan ini tidak dapat diterima untuk entitas yang sering berubah. Kedua, TTL yang serentak kedaluwarsa memicu *cache stampede*. Ketiga, memperpendek TTL demi kesegaran justru mengembalikan beban ke *origin*, sehingga manfaat A ikut hilang.

**Komponen B: invalidasi berbasis *event*, TTL *jitter*, dan *refresh* probabilistik.** Perubahan data dipublikasikan lewat pola *transactional outbox*, sehingga entri *cache* dibatalkan pada saat penulisan, bukan menunggu TTL. TTL diberi *jitter* agar kedaluwarsa tidak serentak. *Probabilistic early refresh* (XFetch) dan *single-flight lock* memperbarui entri panas sebelum kedaluwarsa. Kesegaran naik tanpa memperpendek TTL, sehingga efek samping ditekan sambil *hit ratio* A justru meningkat.

**Rancangan evaluasi.** Beban Zipfian dengan rasio baca dan tulis 90:10 serta 70:30. Baseline disusun berjenjang: tanpa *cache*, lalu *cache* TTL murni, lalu invalidasi *event* saja, lalu hibrida.

**Metrik.** *Hit ratio*. Latensi persentil 50, 95, dan 99. QPS (*Query Per Second*) ke *origin*. *Stale-read rate*, yaitu proporsi respons yang lebih tua dari ambang tertentu. Jumlah kejadian *stampede*. Jejak memori Redis.

**Klaim kontribusi.** Kurva *trade-off* empiris antara kesegaran data, *hit ratio*, dan beban *origin* untuk kombinasi mekanisme invalidasi pada aplikasi web *multi-tenant*, beserta rekomendasi konfigurasi per profil beban.

### Topik 2 · Pencabutan Token pada Autentikasi Stateless: Rotasi Refresh Token dengan Filter Probabilistik di Gateway

*Kaitan materi: Pertemuan 7, 10, dan 12, yaitu API gateway, identity, authentication, authorization, dan security.*

**Masalah.** Sesi yang tersimpan di server menyulitkan penskalaan horizontal. Setiap *request* menuntut pencarian sesi terpusat, dan tiap *node* menjadi *stateful*.

**Solusi A: JWT stateless.** Verifikasi cukup memakai *signature*, tanpa perjalanan bolak-balik ke penyimpanan sesi. Layanan menjadi tanpa *state* dan mudah direplikasi.

**Efek samping A.** Token tidak dapat dicabut sebelum kedaluwarsa. Logout, pencabutan hak akses, dan penanganan token curian tertunda selama sisa masa berlaku. Memperpendek masa berlaku memang mempersempit jendela risiko. Namun cara itu melipatgandakan panggilan *refresh* ke *identity provider*, yaitu beban yang justru ingin dihindari oleh A.

**Komponen B: rotasi *refresh token* dengan *reuse detection*, ditambah daftar cabut berbasis Bloom filter atau cuckoo filter yang direplikasi ke *gateway*.** Filter berukuran kilobita memungkinkan pemeriksaan pencabutan secara lokal di setiap *gateway*, tanpa pencarian terpusat. *False positive* hanya memaksa satu verifikasi presisi ke penyimpanan, bukan menolak pengguna. Jendela pencabutan menyempit hingga hitungan detik, sementara sifat *stateless* A tetap terjaga.

**Rancangan evaluasi.** Baseline berjenjang: sesi di server, JWT murni, JWT dengan *blacklist* Redis per *request*, lalu JWT dengan rotasi dan filter di *gateway*. Skenario ancaman mencakup token dicuri lalu diputar ulang, serta pencabutan hak akses massal.

**Metrik.** *Revocation propagation delay*. Overhead verifikasi per *request* dalam mikrodetik. *Throughput* autentikasi. Jumlah panggilan *refresh* per sesi. Laju *false positive* dan dampaknya pada pengalaman pengguna. Memori filter. Keberhasilan deteksi penggunaan ulang token.

**Klaim kontribusi.** Evaluasi empiris ruang *trade-off* antara jendela pencabutan, overhead per *request*, dan beban *identity provider*. Hasilnya menjadi panduan pemilihan konfigurasi, yang selama ini hanya dibahas secara normatif dalam dokumentasi.

### Topik 3 · Transport Real-Time Adaptif: SSE dan WebSocket Hibrida dengan Fan-out Ter-shard

*Kaitan materi: Pertemuan 5 dan 13, yaitu performance serta sistem real-time dan asinkron.*

**Masalah.** *Polling* periodik memboroskan *bandwidth* dan siklus CPU (*Central Processing Unit*), sekaligus tetap memberi pembaruan yang terlambat.

**Solusi A: WebSocket.** Kanal dua arah dengan latensi pembaruan rendah dan overhead per pesan yang kecil.

**Efek samping A.** Koneksi bersifat *stateful* dan berumur panjang. Memori per koneksi membatasi kepadatan *node*. Penskalaan horizontal menuntut *sticky session* atau *fan-out* antar-*node*. *Reconnect storm* muncul setelah *deploy* atau kegagalan *node*. Sebagian *proxy* korporat juga memperlakukan koneksi ini secara tidak ramah.

**Komponen B: pemilihan transport adaptif di atas *fan-out* Redis *pub/sub* yang di-*shard* per topik, dengan *message coalescing* dan *backpressure*.** SSE dipakai untuk aliran satu arah, sedangkan WebSocket hanya dipakai saat interaksi dua arah dibutuhkan. Sebagian besar kanal turun ke SSE yang lebih murah dan ramah HTTP/2. Pemecahan *shard* memutus ketergantungan pada *sticky session*. Kepadatan koneksi per *node* naik dan pemulihan setelah kegagalan lebih cepat, tanpa mengorbankan latensi pembaruan yang menjadi alasan memilih A.

**Rancangan evaluasi.** Baseline: *short polling*, *long polling*, WebSocket murni, SSE murni, lalu hibrida adaptif. Skenario uji mencakup kenaikan jumlah klien bertahap sampai titik jenuh, *deploy* bergulir, dan kegagalan satu *node*.

**Metrik.** Latensi pembaruan ujung ke ujung pada persentil 95. Koneksi konkuren maksimum per *node*. CPU dan memori per 1.000 koneksi. *Bandwidth* per pembaruan. Pesan hilang saat *failover*. Waktu pemulihan setelah *reconnect storm*.

**Klaim kontribusi.** Aturan pemilihan transport berbasis pengukuran, bukan anekdot, beserta biaya sumber daya tiap pilihan pada skala yang lazim untuk aplikasi web menengah.

### Topik 4 · *Semantic Caching* Terverifikasi untuk Aplikasi Web Terintegrasi LLM

*Kaitan materi: Pertemuan 4, 5, dan 14, yaitu caching, performance, dan emerging web.*

**Masalah.** Fitur berbantuan LLM menambah latensi dalam hitungan detik dan biaya token per permintaan. Di sisi lain, antarmuka web menuntut respons cepat dan biaya operasional yang terkendali.

**Solusi A: pemanggilan model di sisi server dengan respons *streaming*.** *Time-to-first-token* terasa cepat bagi pengguna, dan kunci API tidak bocor ke klien.

**Efek samping A.** *Streaming* hanya menyembunyikan latensi, tidak menghilangkannya. Setiap permintaan tetap dibayar penuh dalam token dan tetap terkena batas laju penyedia. *Cache* berbasis kecocokan persis nyaris tidak pernah kena, karena pengguna menulis pertanyaan yang sama dengan kalimat berbeda.

**Komponen B: *semantic cache* berbasis *embedding* dengan pencarian tetangga terdekat, ditambah lapisan verifikasi ringan sebelum jawaban dipakai ulang.** Kemiripan makna membuat *hit ratio* melonjak dibanding kecocokan persis. Verifikasi berupa pemeriksa murah atau uji kecocokan ulang menekan *false hit*, yaitu jawaban mirip yang sebenarnya tidak sesuai. *False hit* adalah risiko utama pendekatan ini. Biaya dan latensi turun tanpa menurunkan mutu jawaban yang menjadi alasan memakai A.

**Rancangan evaluasi.** Dataset kueri pengguna dengan parafrasa terkontrol. Baseline: tanpa *cache*, *cache* kecocokan persis, *semantic cache* tanpa verifikasi, lalu *semantic cache* terverifikasi. Ambang kemiripan divariasikan untuk memetakan kurvanya.

**Metrik.** *Hit ratio* semantik. Penghematan biaya token. *Time-to-first-token* dan latensi total pada persentil 95. Laju *false hit*. Mutu jawaban memakai rubrik penilai manusia, dengan penilai LLM sebagai pembanding. Jejak penyimpanan indeks vektor. Catatan privasi atas isi yang disimpan di *cache*.

**Klaim kontribusi.** Kuantifikasi *trade-off* tiga arah antara biaya, latensi, dan mutu jawaban, sebagai fungsi ambang kemiripan dan biaya verifikasi pada aplikasi web nyata, bukan pada tolok ukur sintetis.

### Topik 5 · Hidrasi Selektif untuk Menekan Biaya JavaScript pada Rendering Sisi Server

*Kaitan materi: Pertemuan 5, 8, dan 11, yaitu performance engineering, arsitektur web modern, dan frontend.*

**Masalah.** SPA mengirim *bundel* JavaScript besar sebelum apa pun tampil. Pada perangkat kelas bawah dan jaringan lambat, halaman pertama terasa kosong berdetik-detik. Mesin pencari juga kesulitan mengindeksnya.

**Solusi A: SSR.** *Markup* dikirim sudah jadi, sehingga LCP (*Largest Contentful Paint*) dan indeksabilitas membaik, tanpa mengubah model komponen yang sudah dipakai tim.

**Efek samping A.** Halaman memang tampil lebih cepat, tetapi belum bisa dipakai. Seluruh pohon komponen tetap harus dihidrasi di klien. Akibatnya *bundel* JavaScript tidak berkurang sama sekali, dan INP (*Interaction to Next Paint*) justru memburuk karena hidrasi memblokir *main thread*. Biaya CPU per *request* di server juga naik, sehingga TTFB (*Time To First Byte*) dan biaya operasional bertambah. Sebagian keunggulan A termakan sendiri.

**Komponen B: hidrasi selektif berbasis *islands* dengan prioritas menurut *viewport* dan interaksi, di atas *streaming* SSR.** Hanya komponen interaktif yang dikirimi JavaScript. Urutan hidrasinya mengikuti kemungkinan pemakaian, bukan urutan pohon komponen. *Bundel* mengecil dan *main thread* lebih longgar, sehingga INP membaik. Keunggulan LCP dan indeksabilitas yang menjadi alasan memilih A tetap dipertahankan.

**Rancangan evaluasi.** Satu aplikasi yang sama dibangun dalam empat varian: CSR (*Client-Side Rendering*) murni, SSR dengan hidrasi penuh, SSG atau ISR, dan SSR dengan hidrasi selektif. Pengujian memakai profil perangkat kelas bawah serta jaringan 3G dan 4G yang dibatasi. Sesi pengguna direkam lebih dahulu agar interaksinya identik antar-varian.

**Metrik.** LCP, INP, dan CLS (*Cumulative Layout Shift*). TTFB. Jumlah byte JavaScript yang terkirim dan yang tereksekusi. *Total blocking time*. CPU server per *render* dan biaya per 1.000 *render*. Skor indeksabilitas.

**Klaim kontribusi.** Pemetaan empiris hubungan antara granularitas hidrasi, biaya server, dan Core Web Vitals pada kelas perangkat yang berbeda. Termasuk di dalamnya titik ketika penambahan *islands* berhenti memberi manfaat dan mulai menambah kerumitan.

### Topik 6 · Gerbang Kualitas Kinerja di CI: Deteksi Otomatis N+1 dan Regresi Rencana Query

*Kaitan materi: Pertemuan 3, 6, dan 9, yaitu data engineering, testing dan CI, serta observability.*

**Masalah.** Menulis akses basis data secara manual menghasilkan kode berulang, rawan salah, dan lambat dikembangkan.

**Solusi A: ORM atau *query builder*.** Produktivitas melonjak, model data terpusat, dan migrasi menjadi artefak berversi yang aman.

**Efek samping A.** Abstraksi menyembunyikan biaya eksekusi. Relasi malas memicu N+1. Indeks yang hilang tidak terlihat sampai data membesar. Perubahan kecil pada kode dapat mengubah rencana eksekusi tanpa satu pun uji yang gagal. Regresi baru ketahuan di produksi, yaitu persis pengetahuan yang dihapus oleh A.

**Komponen B: gerbang kualitas kinerja di CI.** Isinya tiga bagian: instrumentasi *query* saat uji integrasi berjalan, deteksi pola N+1, dan pembandingan rencana eksekusi terhadap *baseline* yang tersimpan. *Merge* diblokir ketika jumlah *query* per *endpoint* melonjak, atau ketika rencana berubah dari *index scan* menjadi *sequential scan*. Produktivitas ORM tetap utuh, tetapi biaya eksekusi kembali terlihat sejak sebelum kode digabungkan.

**Rancangan evaluasi.** Korpus perubahan kode nyata, berisi cacat N+1 dan indeks hilang yang disuntikkan secara terkendali, ditambah perubahan tak berbahaya sebagai kontrol negatif. Baseline berjenjang: tanpa gerbang, hanya batas waktu uji, hanya deteksi N+1, lalu deteksi N+1 digabung pembandingan rencana.

**Metrik.** Presisi dan *recall* deteksi. Proporsi regresi yang tertangkap sebelum *merge*. Laju alarm palsu, yang menentukan apakah tim akan mematikan gerbang ini. Tambahan durasi *pipeline* CI. Korelasi antara temuan CI dan latensi persentil 95 yang teramati saat uji beban.

**Klaim kontribusi.** Rancangan gerbang kinerja yang praktis dipakai tim kecil, beserta bukti seberapa banyak regresi basis data yang benar-benar tertangkap dan berapa biaya CI yang harus dibayar untuk itu.

### Urutan Pengerjaan yang Disarankan

Diurutkan dari yang paling mudah dieksekusi sampai yang paling menuntut.

| Urutan | Topik | Beban implementasi | Risiko metodologis |
| --- | --- | --- | --- |
| 1 | T1, cache hibrida | Rendah | Rendah |
| 2 | T6, gerbang kualitas kinerja di CI | Rendah sampai sedang | Rendah |
| 3 | T2, pencabutan token | Sedang | Sedang |
| 4 | T5, hidrasi selektif | Tinggi | Rendah |
| 5 | T3, transport real-time adaptif | Tinggi | Sedang |
| 6 | T4, semantic caching LLM | Sedang | Tinggi |

**Mulai dari T1.** Seluruh komponennya sudah tersedia sebagai pustaka dan tinggal dirangkai. Bebannya dapat disintesis dengan k6 dalam hitungan hari. Semua metriknya objektif dan terkumpul otomatis. Baselinenya berjenjang rapi, sehingga alur naskahnya jelas sejak awal. Tidak ada biaya API, partisipan manusia, maupun perangkat keras khusus. Kelemahannya hanya satu, yaitu kebaruannya paling tipis. Karena itu kekuatan naskah harus bertumpu pada kelengkapan kurva *trade-off*.

**Lanjutkan ke T6 dan T2.** Keduanya memakai ulang *testbed* T1 tanpa penyiapan tambahan. T6 menuntut korpus perubahan kode berlabel sebagai *ground truth*. Itu biaya waktu yang dapat diperkirakan, bukan risiko yang dapat menggagalkan penelitian. T2 mengukur overhead pada skala mikrodetik, sehingga menuntut disiplin ekstra dalam menekan *noise* pengukuran. Ada kemungkinan selisihnya terlalu kecil untuk bermakna secara statistik.

**T5** justru punya metrik paling objektif dan perkakas paling matang. Kesulitannya ada pada tuntutan membangun satu aplikasi dalam empat varian. Topik ini cocok untuk tim yang kuat di *frontend*, dengan satu syarat. Keempat varian harus memakai satu *framework* yang mendukung *islands*, agar perbedaan hasil tidak berasal dari perbedaan *framework*.

**T3 dan T4 sebaiknya bukan proyek pertama.** T3 menuntut *load generator* puluhan ribu koneksi konkuren dan beberapa *node*. Hasilnya sensitif terhadap *tuning* sistem operasi, misalnya `ulimit` dan *ephemeral port*. Salah *tuning* berarti yang terukur adalah batas sistem operasi, bukan batas rancangan. T4 paling menarik perhatian, tetapi paling sulit dibuat rigor. Penilaian mutu jawaban bersifat subjektif, ada biaya API, dan reproduksibilitasnya rapuh karena model penyedia berubah tanpa pemberitahuan.

### Catatan Pelaksanaan

**Infrastruktur bersama.** Satu *testbed* melayani keenam topik, terdiri atas aplikasi referensi, Docker Compose, PostgreSQL, Redis, k6 atau Locust sebagai *load generator*, dan OpenTelemetry untuk pengumpulan metrik. Repositori artefak yang dapat direproduksi, berisi skrip beban, konfigurasi, dan data mentah, menaikkan peluang penerimaan secara berarti pada tingkat jurnal ini.

**Disiplin metodologis.** Bagian inilah yang biasanya menjadi pembeda antara diterima dan ditolak. Tiap konfigurasi dijalankan minimal 30 repetisi. Yang dilaporkan adalah sebaran, bukan hanya rerata. Interval kepercayaan disertakan. Versi seluruh dependensi dikunci. Spesifikasi perangkat keras dilaporkan. Ancaman terhadap validitas disebutkan secara jujur, terutama bahwa hasil diperoleh pada satu *testbed*.

**Kalibrasi kebaruan.** Tidak satu pun dari keenam komponen B ini baru secara individual. Kebaruan yang layak diklaim pada tingkat Q3 dan Q4 adalah **kombinasinya, konteks aplikasi webnya, dan kurva *trade-off* yang dihasilkan pengukuran**. Klaim tidak boleh melebihi itu, karena klaim berlebihan justru menjadi alasan penolakan yang paling umum.

**Sasaran publikasi.** Jurnal internasional terindeks Scopus tingkat Q3 sampai Q4 pada rumpun rekayasa perangkat lunak dan sistem informasi umumnya menerima format ini. Kuartil sebuah jurnal berubah tiap tahun. Karena itu status terkininya diperiksa lebih dahulu di Scopus atau SJR sebelum naskah dikirim, termasuk memeriksa daftar jurnal yang diragukan.

---

## Daftar Singkatan

| Singkatan | Kepanjangan |
| --- | --- |
| ABAC | Attribute-Based Access Control |
| ACID | Atomicity, Consistency, Isolation, Durability |
| API | Application Programming Interface |
| AWS | Amazon Web Services |
| BFF | Backend for Frontend |
| CDN | Content Delivery Network |
| CI/CD | Continuous Integration / Continuous Delivery |
| CLS | Cumulative Layout Shift |
| CORS | Cross-Origin Resource Sharing |
| CPU | Central Processing Unit |
| CSP | Content Security Policy |
| CSR | Client-Side Rendering |
| CSRF | Cross-Site Request Forgery |
| DNS | Domain Name System |
| DSN | Data Source Name |
| DTO | Data Transfer Object |
| E2E | End-to-End |
| GraphQL | Graph Query Language |
| gRPC | gRPC Remote Procedure Call, framework RPC dari Google |
| HTML | HyperText Markup Language |
| HTTP | HyperText Transfer Protocol |
| IaC | Infrastructure as Code |
| INP | Interaction to Next Paint |
| ISR | Incremental Static Regeneration |
| JWT | JSON Web Token |
| LCP | Largest Contentful Paint |
| LLM | Large Language Model |
| LRU | Least Recently Used |
| OAuth | Open Authorization |
| OIDC | OpenID Connect |
| ORM | Object-Relational Mapping |
| OWASP | Open Worldwide Application Security Project |
| PWA | Progressive Web App |
| QPS | Query Per Second |
| RBAC | Role-Based Access Control |
| REST | Representational State Transfer |
| RFC | Request for Comments |
| RPC | Remote Procedure Call |
| RTT | Round-Trip Time |
| SLI / SLO | Service Level Indicator / Service Level Objective |
| SPA | Single-Page Application |
| SQL | Structured Query Language |
| SSE | Server-Sent Events |
| SSG | Static Site Generation |
| SSR | Server-Side Rendering |
| SSRF | Server-Side Request Forgery |
| TCP | Transmission Control Protocol |
| tRPC | TypeScript Remote Procedure Call |
| TLS | Transport Layer Security |
| TTFB | Time To First Byte |
| TTL | Time To Live |
| Wasm | WebAssembly |
| XSS | Cross-Site Scripting |
