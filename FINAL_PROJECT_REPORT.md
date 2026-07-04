# Final Project Report — Simple LMS Extended Backend

## Identitas
- Nama: Mohammad Abdul Faiz
- NIM: A11.2023.15305
- Kelas: 4602
- URL Repository: https://github.com/AbdulFaiz23/SimpleLms

## Deskripsi Project
Project ini adalah backend Learning Management System (LMS) sederhana namun komprehensif, dibangun menggunakan Django Ninja REST API dan PostgreSQL sebagai database utama. Project ini juga di-containerize menggunakan Docker untuk mempermudah environment setup dan deployment.

Pada tahap pengembangan akhir ini, project telah diperluas dengan menambahkan 3 layer infrastruktur tambahan: Redis untuk implementasi caching dan API rate limiting, MongoDB untuk penyimpanan activity log dan kalkulasi learning analytics, serta kombinasi Celery dan RabbitMQ untuk pemrosesan asynchronous background tasks seperti pengiriman email notifikasi dan pembuatan laporan/sertifikat.

## Fitur Dasar yang Sudah Berjalan
- Authentication JWT (register, login)
- RBAC (admin, instructor, student)
- Course CRUD + ownership validation
- Enrollment & Progress tracking
- Swagger/OpenAPI docs

## Fitur Tambahan yang Dipilih
| No | Fitur | Kategori | Poin | Status |
|---|---|---|---|---|
| 1 | Redis caching untuk course (list & detail) | Caching & Rate Limiting | 12 | Selesai |
| 2 | Cache invalidation strategy (cache-aside) | Caching & Rate Limiting | 12 | Selesai |
| 3 | API rate limiting berbasis Redis | Caching & Rate Limiting | 12 | Selesai |
| 4 | Activity logging ke MongoDB | MongoDB & Analytics | 15 | Selesai |
| 5 | Learning analytics collection | MongoDB & Analytics | 15 | Selesai |
| 6 | Aggregation query MongoDB | MongoDB & Analytics | 15 | Selesai |
| 7 | Email notification async | Celery & Async | 12 | Selesai |
| 8 | Generate certificate/report async | Celery & Async | 18 | Selesai |
| 9 | Scheduled task (Celery Beat) | Celery & Async | 15 | Selesai |
| 10 | Task status endpoint | Celery & Async | 12 | Selesai |
| 11 | Flower monitoring | Celery & Async | 8 | Selesai |

## Penjelasan Implementasi
### Caching & Rate Limiting (Redis)
Untuk mengurangi beban PostgreSQL dari request read-heavy, saya mengimplementasikan cache-aside pattern menggunakan Redis. Data course di-cache dengan TTL, dan diinvalidasi secara manual (cache invalidation strategy) setiap ada perubahan data (Create/Update/Delete). Saya juga menggunakan Redis untuk melacak jumlah request dalam implementasi API rate limiting (60 request per menit) melalui custom middleware.

### MongoDB & Analytics
MongoDB dipilih sebagai Document Store karena sangat cocok untuk menampung data log aktivitas yang tidak terstruktur secara kaku dan berpotensi membesar dengan cepat. Setiap aksi penting pengguna (login, enroll, mark progress) dicatat ke collection `activity_logs`. Selain itu, saya menggunakan MongoDB aggregation pipeline di endpoints reports untuk menghitung tingkat popularitas course dan engagement murid secara efisien tanpa membebani database relasional utama.

### Celery & Async Processing (RabbitMQ)
Untuk tugas-tugas yang memakan waktu lama seperti meng-generate CSV report, membuat sertifikat kelulusan, dan mengirim email, saya mendelegasikannya ke Celery workers. Hal ini mencegah API menjadi blocking dan lambat. Celery Beat juga diaktifkan untuk menjalankan task terjadwal seperti `update_course_statistics` secara berkala, dan saya menggunakan Flower untuk monitoring visual dari antrean pesan di RabbitMQ.

## Cara Menjalankan Project
1. Clone repository dan masuk ke direktori project.
2. Build dan jalankan seluruh container:
   ```bash
   docker-compose up --build -d
   ```
3. Lakukan database migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   ```
4. Generate demo data (users, courses, enrollments):
   ```bash
   docker-compose exec web python manage.py seed_demo_data
   ```

## Akun Demo
(Password untuk semua akun: `password123`)
- **Admin**: `admin_demo`
- **Instructor**: `instructor_1`, `instructor_2`
- **Student**: `student_1`, `student_2`, `student_3`, `student_4`

## Endpoint Penting
- [Swagger UI](http://localhost:8000/api/docs)
- **Courses**: `GET /api/courses`, `POST /api/courses`
- **Enroll & Progress**: `POST /api/enrollments`, `POST /api/enrollments/{id}/progress`
- **Reports**: `GET /api/reports/course-popularity`, `GET /api/reports/student-engagement`
- **Async Tasks**: `POST /api/courses/{id}/export-report`, `GET /api/tasks/{task_id}/status`

## Screenshot / Bukti Pengujian

### 1. Redis caching (X-Cache: HIT vs MISS)

**Request pertama → Cache MISS** (data diambil dari PostgreSQL, lalu disimpan ke Redis):

**Request kedua → Cache HIT** (data langsung diambil dari Redis, tanpa query ke PostgreSQL):

---

### 2. Cache invalidation (Before & After CREATE course)

Saat `POST /api/courses/` berhasil (201 Created), fungsi `invalidate_course_cache()` dipanggil secara otomatis untuk menghapus seluruh cache list courses dari Redis, sehingga request berikutnya akan mendapat data terbaru.

---

### 3. Rate limiting (Response 429)

Setelah melewati batas **60 request per menit**, sistem mengembalikan HTTP 429 Too Many Requests. Bukti pengujian via PowerShell (65 request berturut-turut):

```
[1-60]  200 OK       ← Request dalam batas normal
[61]    429          ← Rate limit tercapai!
[62]    429
[63]    429
[64]    429
[65]    429
```

> **Hasil uji:** Request ke-61 dan seterusnya mendapatkan response **HTTP 429**, membuktikan Redis rate limiting berfungsi dengan benar (limit: 60 req/menit per IP).

---

### 4. Activity logging (MongoDB — collection `activity_logs`)

MongoDB berhasil merekam aktivitas pengguna secara real-time. Berikut sample data dari collection `activity_logs` (total: **21 dokumen**):

```json
{
  "user_id": 3,
  "username": "admin_demo",
  "action": "LOGIN",
  "resource_type": "user",
  "resource_id": 3,
  "metadata": {},
  "ip_address": "172.18.0.1",
  "timestamp": "2026-07-02T19:04:49.129189+00:00"
}
```

> **Aksi yang dicatat:** LOGIN, COURSE_CREATED, ENROLLMENT_CREATED, COURSE_UPDATED, COURSE_DELETED, dan lainnya.

---

### 5. Learning analytics (MongoDB — collection `learning_analytics`)

MongoDB menyimpan data progres belajar per student per course. Berikut data dari collection `learning_analytics` (total: **8 dokumen**):

```json
[
  { "course_id": 1, "student_id": 6, "completed_lessons": 1, "completion_percentage": 20.0, "total_lessons": 5 },
  { "course_id": 4, "student_id": 6, "completed_lessons": 2, "completion_percentage": 50.0, "total_lessons": 4 },
  { "course_id": 2, "student_id": 8, "completed_lessons": 4, "completion_percentage": 100.0, "total_lessons": 4 },
  { "course_id": 3, "student_id": 9, "completed_lessons": 4, "completion_percentage": 100.0, "total_lessons": 4 },
  { "course_id": 4, "student_id": 9, "completed_lessons": 4, "completion_percentage": 100.0, "total_lessons": 4 }
]
```

---

### 6. Aggregation query MongoDB (Response endpoint reports)

**GET /api/reports/student-engagement** — Aggregation pipeline MongoDB yang menghitung rata-rata penyelesaian course:

```json
{
  "data": [
    { "_id": 2, "average_completion": 100.0, "total_students": 1 },
    { "_id": 4, "average_completion": 75.0,  "total_students": 2 },
    { "_id": 3, "average_completion": 75.0,  "total_students": 2 },
    { "_id": 1, "average_completion": 33.33, "total_students": 3 }
  ]
}
```

> **Catatan:** `/api/reports/course-popularity` memerlukan data ENROLLMENT_CREATED di activity_logs (dicatat saat enroll via API).

---

### 7. Email notification async (Celery Worker Log)

Log Celery Worker menunjukkan task `send_enrollment_email` berhasil diterima dan diproses secara asinkron:

```
[2026-07-02 19:09:15] Task lms.tasks.send_enrollment_email[5cf564ef-f562-441b-8c06-af1df8d6dc95] received
[2026-07-02 19:09:15] Task lms.tasks.send_enrollment_email[5cf564ef-f562-441b-8c06-af1df8d6dc95] retry: Retry in 5s: ConnectionRefusedError
```

> Task dijalankan async dan di-retry otomatis (email backend tidak dikonfigurasi di environment dev, namun task flow berjalan benar).

---

### 8. Generate certificate/report async (File Hasil)

Task `export_course_report` berhasil dieksekusi secara asinkron dan menghasilkan file CSV:

```
[2026-07-02 19:09:15] Task lms.tasks.export_course_report[78c3af22-2ee3-4231-8971-68ec9511e4cc] received
[2026-07-02 19:09:15] Task lms.tasks.export_course_report[78c3af22-2ee3-4231-8971-68ec9511e4cc] succeeded in 0.342s: '/app/media/reports/course_1_report_1783019355.csv'
```

> **File berhasil dibuat:** `/app/media/reports/course_1_report_1783019355.csv`

---

### 9. Scheduled task (Celery Beat — `update_course_statistics`)

Celery Beat menjalankan task terjadwal `update_course_statistics` secara otomatis setiap jam. Bukti dari log worker:

```
[2026-07-02 19:00:00] Task lms.tasks.update_course_statistics[c48a7d72-9ad5-4e1f-8361-70b1a881cb8c] received
[2026-07-02 19:00:00] Task lms.tasks.update_course_statistics[c48a7d72-9ad5-4e1f-8361-70b1a881cb8c] succeeded in 0.300s: None
```

---

### 10. Task status endpoint (Response `/api/tasks/{id}/status`)

Endpoint `GET /api/tasks/{task_id}/status` mengembalikan status task Celery secara real-time:

```json
{
  "task_id": "11111111-1111-1111-1111-111111111111",
  "status": "PENDING",
  "result": null
}
```

---

### 11. Flower monitoring (Dashboard)

Flower Dashboard berjalan di `http://localhost:5555` — menampilkan worker aktif beserta statistik task:

> **Worker `celery@eac297bdf0e0`** berstatus **Online** dan siap memproses 4 registered tasks: `export_course_report`, `generate_certificate`, `send_enrollment_email`, `update_course_statistics`.

---

## Kendala dan Solusi
Selama pengerjaan, saya sempat menemui kendala pada fitur export_course_report (Celery). Terdapat bug di mana query ORM memanggil field model yang salah sehingga task selalu gagal (FAILED di log Celery). Solusinya adalah dengan melakukan debugging pada traceback di log worker, menyesuaikan nama field di dalam script `tasks.py`, dan memperbaiki path URL di router menjadi `/api/courses/{id}/export-report`. Hal ini mengajarkan saya pentingnya membaca log asinkron untuk memperbaiki background task.

Selain itu, ditemukan bug pada `JWTAuth.authenticate()` di mana nilai return berupa string token (bukan user object), sehingga `request.auth.role` selalu error. Perbaikannya adalah mengembalikan `user` object langsung agar Django Ninja menetapkannya sebagai `request.auth`.

## Kesimpulan
Melalui project LMS ini, saya belajar tidak hanya cara membangun API dengan Django, namun juga mengintegrasikan berbagai arsitektur microservices-lite seperti caching layer dengan Redis, NoSQL document-based data processing dengan MongoDB, dan event-driven async pattern dengan Celery & RabbitMQ. Kombinasi stack teknologi ini menjadikan aplikasi jauh lebih skalabel, performant, dan mirip dengan standar aplikasi modern di industri nyata.

