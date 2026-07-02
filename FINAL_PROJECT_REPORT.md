# Final Project Report — Simple LMS Extended Backend

## Identitas
- Nama: [ISI NAMA ANDA]
- NIM: A11.2023.15305
- Kelas: [ISI KELAS ANDA]
- URL Repository: [ISI URL REPO - pastikan nama repo terbaru, misal: github.com/AbdulFaiz23/SimpleLms]

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

> **[📝 CATATAN UNTUK MAHASISWA]**: 
> Silakan tambahkan screenshot (gambar) dari aplikasi Anda di bawah masing-masing judul poin ini sebelum mengumpulkan tugas! Gunakan sintaks markdown: `![Deskripsi](path/to/image.png)`.

### 1. Redis caching (X-Cache: HIT vs MISS / redis-cli)
[Tampilkan gambar / log di sini]

### 2. Cache invalidation (Before & After CREATE course)
[Tampilkan gambar / log di sini]

### 3. Rate limiting (Response 429)
[Tampilkan gambar response error 429 di sini]

### 4. Activity logging (MongoDB Compass / mongosh)
[Tampilkan screenshot MongoDB berisi collection activity_logs]

### 5. Learning analytics (MongoDB Compass)
[Tampilkan screenshot MongoDB berisi collection learning_analytics]

### 6. Aggregation report (Response JSON endpoint reports)
[Tampilkan response postman untuk course-popularity / student-engagement]

### 7. Email async (Celery Worker Log)
[Tampilkan log worker yang menunjukkan "Task send_enrollment_email SUCCESS"]

### 8. Certificate/report async (File Hasil / Task Status)
[Tampilkan gambar file hasil CSV/sertifikat yang dibuat]

### 9. Scheduled task (Flower Dashboard - Periodic Task)
[Tampilkan dashboard yang menunjukkan task `update_course_statistics`]

### 10. Task status endpoint (Response status)
[Tampilkan JSON response dari /api/tasks/{id}/status]

### 11. Flower monitoring (Dashboard History)
[Tampilkan dashboard utama Flower]


## Kendala dan Solusi
Selama pengerjaan, saya sempat menemui kendala pada fitur export_course_report (Celery). Terdapat bug di mana query ORM memanggil field model yang salah sehingga task selalu gagal (FAILED di log Celery). Solusinya adalah dengan melakukan debugging pada traceback di log worker, menyesuaikan nama field di dalam script `tasks.py`, dan memperbaiki path URL di router menjadi `/api/courses/{id}/export-report`. Hal ini mengajarkan saya pentingnya membaca log asinkron untuk memperbaiki background task.

## Kesimpulan
Melalui project LMS ini, saya belajar tidak hanya cara membangun API dengan Django, namun juga mengintegrasikan berbagai arsitektur microservices-lite seperti caching layer dengan Redis, NoSQL document-based data processing dengan MongoDB, dan event-driven async pattern dengan Celery & RabbitMQ. Kombinasi stack teknologi ini menjadikan aplikasi jauh lebih skalabel, performant, dan mirip dengan standar aplikasi modern di industri nyata.
