# PRD — Final Project: Simple LMS Extended Backend

## 1. Background

Project ini adalah lanjutan dari Simple LMS (Progress 3 & 4) yang sudah punya fondasi lengkap (Docker, Django Ninja REST API, JWT + RBAC, PostgreSQL) plus 3 layer infrastruktur tambahan yang sudah berjalan: Redis caching, MongoDB activity log & analytics, dan Celery async task processing.

**Scope PRD ini bukan menambah fitur baru** — fitur tambahan yang dinilai sudah cukup (lihat §3). Fokus PRD ini adalah menutup gap yang masih bikin nilai tidak maksimal: testing, bukti pengujian per fitur, dan dokumentasi laporan akhir. Ini yang paling menentukan sekarang karena 2 dari 5 komponen penilaian (testing + dokumentasi/presentasi = 20 poin, plus bagian dari kualitas kode 15 poin) belum tersentuh sama sekali.

## 2. Goal

Melengkapi seluruh deliverable dan bukti yang dibutuhkan supaya nilai maksimal di setiap komponen rubrik tercapai, tanpa menambah kompleksitas fitur baru yang berisiko bikin demo gagal.

## 3. Fitur Tambahan yang Dipilih (Sudah Final — Jangan Diubah)

Ini yang akan ditulis di tabel `FINAL_PROJECT_REPORT.md`. Total poin nominal 146, dicap maksimal 50 sesuai aturan PRD dosen.

### Cluster 1 — Caching & Rate Limiting (Redis)
| Fitur | Poin | File terkait |
|---|---|---|
| Redis caching untuk course (list & detail) | 12 | `lms/api_courses.py` |
| Cache invalidation strategy (cache-aside) | 12 | `lms/api_courses.py` |
| API rate limiting berbasis Redis | 12 | `lms/middleware.py` |

### Cluster 2 — MongoDB & Analytics
| Fitur | Poin | File terkait |
|---|---|---|
| Activity logging ke MongoDB | 15 | `lms/mongo.py`, dipanggil dari `api_auth.py`, `api_courses.py`, `api_enrollments.py` |
| Learning analytics collection | 15 | `lms/mongo.py`, `api_enrollments.py` (mark_progress) |
| Aggregation query MongoDB (course-popularity, student-engagement) | 15 | `lms/api_reports.py` |

### Cluster 3 — Celery & Async Processing
| Fitur | Poin | File terkait |
|---|---|---|
| Email notification async | 12 | `lms/tasks.py` → `send_enrollment_email` |
| Generate certificate/report async | 18 | `lms/tasks.py` → `generate_certificate`, `export_course_report` |
| Scheduled task (Celery Beat) | 15 | `config/celery.py` → `update_course_statistics` |
| Task status endpoint | 12 | `lms/api_tasks.py` |
| Flower monitoring | 8 | `docker-compose.yml` (service `flower`) |

**Jangan tambah/ubah fitur di luar ini kecuali ada bug baru yang ketemu.** Kalau ada waktu lebih, prioritas ada di §4-§6, bukan fitur baru.

## 4. Testing — 10 Poin (WAJIB, belum ada progress)

Buat folder `lms/tests/` dengan struktur berikut. Semua pakai Django `TestCase` / `django.test.Client` atau `pytest-django` (pilih salah satu, konsisten).

### 4.1 `lms/tests/test_models.py` — Unit test model & business logic
- Test `Progress.completed` toggle dan hitung persentase completion per course
- Test `Enrollment` tidak bisa duplikat (unique constraint student+course, kalau ada)
- Test relasi `Course.lesson_set` menghitung jumlah lesson dengan benar

### 4.2 `lms/tests/test_api_auth.py` — API test dasar
- Test register berhasil → return token
- Test login sukses → JWT valid
- Test login gagal (password salah) → 401
- Test akses endpoint protected tanpa token → 401

### 4.3 `lms/tests/test_api_courses.py` — API test course + cache
- Test `GET /api/courses` return list dengan benar
- Test `GET /api/courses/{id}` return detail dengan benar
- Test create course oleh instructor berhasil, oleh student ditolak (403)
- Test cache: request kedua ke endpoint yang sama tidak query ulang ke DB (bisa dites pakai `django.test.utils.CaptureQueriesContext` atau assert cache key muncul di `django_redis` cache backend)

### 4.4 `lms/tests/test_permissions.py` — RBAC test
- Test admin bisa akses semua endpoint admin-only
- Test instructor hanya bisa update/delete course miliknya sendiri (ownership), bukan course instructor lain
- Test student ditolak dari endpoint instructor/admin-only
- Test anonymous user ditolak dari semua endpoint yang butuh auth

### 4.5 `lms/tests/test_tasks.py` — Test fitur tambahan (Celery/Mongo/Redis)
Ini yang isinya cover 3 cluster fitur tambahan sekaligus, jadi penting buat pembuktian:
- Test `export_course_report` jalan tanpa error dan CSV yang dihasilkan berisi data yang benar (regression test untuk bug yang sudah difix)
- Test `log_activity` berhasil insert ke MongoDB (bisa pakai `mongomock` biar tidak butuh koneksi Mongo asli saat test, atau test terhadap instance Mongo di docker-compose)
- Test rate limit: request ke-61 dalam 1 menit return 429

### 4.6 Setup
- Tambahkan `pytest-django` atau gunakan `python manage.py test` — pastikan command dijalankan didokumentasikan di README (kriteria "Test bisa dijalankan dengan command jelas" — 1 poin)
- Tambahkan section "Cara Menjalankan Test" di README dengan command persis, contoh:
  ```bash
  docker compose exec web python manage.py test lms.tests
  ```
- (Opsional, kalau ada waktu) tambahkan `coverage.py` dan generate laporan coverage sederhana — bukan syarat wajib di rubrik testing 10 poin ini tapi ada di Lampiran sebagai fitur terpisah (15 poin) kalau mau dikejar lebih

**Acceptance §4:**
- [ ] Semua 5 file test di atas ada dan pass
- [ ] Command test terdokumentasi di README
- [ ] Minimal test menyentuh: auth/API utama, permission/RBAC, dan fitur tambahan (sesuai rubrik testing 10 poin)

## 5. Dokumentasi & Presentasi — 10 Poin

### 5.1 `FINAL_PROJECT_REPORT.md` (root repo) — belum ada, wajib dibuat

Struktur wajib sesuai PRD dosen:

```markdown
# Final Project Report — Simple LMS Extended Backend

## Identitas
- Nama: [isi]
- NIM: A11.2023.15305
- Kelas: [isi]
- URL Repository: [isi — pastikan pakai nama repo terbaru, SimpleLms]

## Deskripsi Project
[2-3 paragraf: LMS dengan Django Ninja + PostgreSQL, ditambah caching Redis,
activity logging & analytics MongoDB, dan async processing Celery+RabbitMQ]

## Fitur Dasar yang Sudah Berjalan
- Authentication JWT (register, login)
- RBAC (admin, instructor, student)
- Course CRUD + ownership validation
- Enrollment & Progress tracking
- Swagger/OpenAPI docs

## Fitur Tambahan yang Dipilih
[Tabel: No, Fitur, Kategori, Poin, Status — isi dari §3 di atas, semua Status "Selesai"]

## Penjelasan Implementasi
[Per cluster: jelaskan alur teknis singkat + kenapa dipilih pendekatan itu.
Sertakan potongan arsitektur/diagram dari README kalau relevan]

## Cara Menjalankan Project
[docker compose up, migrate, seed data — step by step]

## Akun Demo
[username/password admin, instructor, student — lihat §5.3]

## Endpoint Penting
[Daftar endpoint utama + fitur tambahan, bisa link ke Swagger]

## Screenshot / Bukti Pengujian
[Lihat §5.2 — embed semua di sini]

## Kendala dan Solusi
[Ceritakan bug export_course_report yang sempat salah field model, dan
proses fix-nya — ini justru bagus buat presentasi karena nunjukkan
proses debugging yang nyata]

## Kesimpulan
[Refleksi singkat]
```

### 5.2 Bukti Pengujian per Fitur (Screenshot/Log) — kumpulkan semua ini

Ini yang menentukan poin "dokumentasi/pembuktian pengujian" di rubrik per-fitur (15% dari tiap fitur tambahan), jangan sampai ada fitur yang "jalan tapi gak ada buktinya":

| Fitur | Bukti yang perlu dikumpulkan |
|---|---|
| Redis caching | Screenshot/log `X-Cache: HIT` vs `MISS`, atau `redis-cli GET course:detail:{id}` |
| Cache invalidation | Before/after: `redis-cli KEYS "courses:*"` sebelum & sesudah create course baru |
| Rate limiting | Screenshot response 429 setelah request ke-61 |
| Activity logging | Screenshot MongoDB Compass atau `mongosh` query `db.activity_logs.find()` |
| Learning analytics | Screenshot `db.learning_analytics.find()` |
| Aggregation report | Screenshot response JSON dari `GET /api/reports/course-popularity` dan `student-engagement` |
| Email async | Screenshot log Celery worker menunjukkan task `send_enrollment_email` SUCCESS |
| Certificate/report async | Screenshot file hasil di `/media/certificates/` atau `/media/reports/`, plus status task |
| Scheduled task | Screenshot Flower menunjukkan `update_course_statistics` berjalan otomatis tiap jam (bisa dipercepat interval sementara untuk keperluan demo, lalu dikembalikan) |
| Task status endpoint | Screenshot response `GET /api/tasks/{id}/status` |
| Flower monitoring | Screenshot dashboard Flower dengan minimal beberapa task history (sudah ada satu, lengkapi dengan task-task lain) |

### 5.3 Demo Account & Seed Data

Buat management command `python manage.py seed_demo_data` (kalau belum ada) yang generate:
- 1 admin, 2 instructor, 3-5 student dengan password yang didokumentasikan di README & `FINAL_PROJECT_REPORT.md`
- Minimal 3-5 course dengan lesson, sebagian sudah ada enrollment & progress supaya endpoint report/analytics langsung ada datanya saat demo (jangan demo dari database kosong)

### 5.4 Postman Collection

Update `postman_collection.json` yang sudah ada supaya mencakup:
- Flow lengkap: register → login → create course → enroll → mark progress → export report → check task status
- Endpoint reports (`course-popularity`, `student-engagement`)
- Path `export-report` yang sudah difix (`/api/courses/{id}/export-report`)

**Acceptance §5:**
- [ ] `FINAL_PROJECT_REPORT.md` ada di root, lengkap semua section
- [ ] Semua 11 fitur di §3 punya minimal 1 bukti visual (screenshot/log) yang di-embed di report
- [ ] Seed data command ada dan didokumentasikan
- [ ] Postman collection ter-update dan bisa dijalankan urut dari awal sampai akhir

## 6. Kualitas Kode — 15 Poin (verifikasi, bukan kerjaan baru)

Sudah relatif aman berdasarkan review sebelumnya, tapi cek ulang sebelum submit:

- [ ] Tidak ada hardcode secret (semua lewat env var — sudah sesuai `.env.example`)
- [ ] Struktur app rapi (sudah sesuai — `api_*.py` per domain, `tasks.py`, `mongo.py`, `middleware.py` terpisah)
- [ ] Error handling di endpoint utama (permission, validation, not found) — cek tiap endpoint return status code yang tepat, bukan generic 500
- [ ] Naming konsisten (endpoint, schema, model)

## 7. Bonus (Opsional, Prioritas Rendah — kerjakan hanya kalau §4-§6 sudah selesai)

| Bonus | Poin | Effort |
|---|---|---|
| Deployment online (VPS/Railway/Render) | +5 | Tinggi — perlu setup ulang production env, DB, worker |
| UI/frontend sederhana untuk demo | +5 | Sedang |
| Dokumentasi sangat rapi dengan diagram arsitektur | +3 | Rendah — README sudah punya Mermaid diagram, tinggal pastiin update |
| Test coverage tinggi + CI berjalan | +5 | Sedang — tambahan dari §4 |

**Rekomendasi:** kejar bonus "dokumentasi diagram arsitektur" (+3) dulu karena effort rendah dan diagramnya sudah ada, tinggal dicek masih akurat. Bonus lain opsional kalau waktu masih ada setelah §4-§6 tuntas.

## 8. Urutan Pengerjaan (Rekomendasi)

1. **Testing (§4)** — paling berisiko karena 0 progress, dan poinnya wajib (10 poin murni + menyelamatkan sebagian dari 15% "dokumentasi/pembuktian" tiap fitur tambahan)
2. **Kumpulkan bukti pengujian (§5.2)** — sambil jalan testing, screenshot langsung diambil satu-satu
3. **Seed data + demo account (§5.3)** — supaya bukti di atas datanya representatif
4. **`FINAL_PROJECT_REPORT.md` (§5.1)** — disusun terakhir karena butuh semua bukti dari langkah 1-3
5. **Update Postman collection (§5.4)**
6. **Verifikasi kualitas kode (§6)**
7. (Opsional) Bonus (§7)

## 9. Non-Goals

- Tidak menambah fitur baru di luar 3 cluster yang sudah dipilih (§3)
- Tidak mengubah database schema
- Tidak refactor besar-besaran struktur project yang sudah ada
- Deployment online bukan prioritas utama (masuk §7, opsional)

## 10. Referensi Kondisi Kode Saat Ini

- Repo: `AbdulFaiz23/SimpleLms` (perhatikan: nama repo sudah berubah dari `Progress3`)
- Semua bug dari review sebelumnya sudah fixed: `export_course_report` field model, path endpoint `export-report`, `.env.example`, screenshot Flower di README, `requirements.txt` cleanup, rate limit atomic incr
- File yang akan disentuh di PRD ini: folder baru `lms/tests/`, file baru `FINAL_PROJECT_REPORT.md`, update `postman_collection.json`, kemungkinan file baru `lms/management/commands/seed_demo_data.py`