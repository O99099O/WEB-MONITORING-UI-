Berikut `README.md` yang profesional, rapih, dan menjelaskan isi script `main2.py` di repo GitHub-mu:

---

````markdown
# 💻 WEB MONITORING UI - POLOSS

**Advanced Network Monitoring GUI Tool**  
Dibuat oleh: [POLOSS](https://github.com/O99099O)

> Repositori ini berisi **aplikasi GUI monitoring jaringan** berbasis Python + Tkinter yang kuat, real-time, dan interaktif. Cocok untuk pentester, admin jaringan, dan analis keamanan.

---

## 🧠 Fitur Utama

- 🔎 **Pemantauan Real-Time**
  - Ping latency (dengan grafik)
  - Status port (terbuka atau tertutup)
  - Status ONLINE / OFFLINE otomatis
  
- 🛰️ **Traffic Monitor**
  - Mendeteksi data `Upload / Download` langsung dari adapter lokal
  - Auto-refresh setiap detik

- 📊 **Grafik Interaktif**
  - 6 jenis grafik: `line`, `bar`, `scatter`, `step`, `candlestick`, dan lainnya
  - 6 channel grafik aktif sekaligus
  - Bisa diubah warna dan jenisnya
  - Scrollable & customizable background (dark/grid/image)

- 🚪 **Port Scanner**
  - Otomatis memindai 15+ port penting (21, 22, 80, 443, dll)
  - Dilengkapi nama service (FTP, SSH, HTTP, dsb)

- 📝 **Notification System**
  - Notifikasi koneksi hilang/tersambung
  - Notifikasi aktivitas penting (export, speed test, dll)

- ⚙️ **Tools Tambahan**
  - Export data hasil monitoring
  - Speed test jaringan lokal (simulasi)
  - Riwayat pemantauan (history monitoring)
  - Sistem loading & banner saat startup

---

## 📁 Struktur File

- `main2.py` — Source utama aplikasi GUI
- `monitor_history.json` — File history target yang pernah dimonitor

---

## 🖼️ Tampilan Antarmuka

- Dibangun dengan **Tkinter + Matplotlib + PIL**
- UI modern bergaya dark mode
- Auto-layout dan responsive
- Panel informasi lengkap (IP, status ping, traffic, OS info, dll)

---

## ▶ Cara Menjalankan

### 1. Persiapkan Environment

```bash
pip install -r requirements.txt
# atau manual:
pip install psutil matplotlib pillow
````

### 2. Jalankan Program

```bash
python3 main2.py
```

### 3. Masukkan Target

* Bisa `URL` seperti `example.com`
* Bisa juga IP langsung seperti `192.168.1.1`

---

## 🧠 Informasi Teknis

| Komponen      | Library      |
| ------------- | ------------ |
| GUI           | Tkinter      |
| Grafik        | matplotlib   |
| Ping & Socket | socket       |
| Monitor Net   | psutil       |
| Gambar UI     | PIL (Pillow) |

---

## 📌 Catatan Tambahan

* Tidak memerlukan hak root/admin
* Dapat dijalankan di Linux/Windows
* Auto clean history > 20 entri
* Background grafik bisa pakai **gambar sendiri**

---

## ✅ Status

> 🚀 Versi: 3.0
> 📆 Terakhir update: Juli 2025
> 🧠 Dibuat oleh: POLOSS
> 🔓 Bebas digunakan, dimodifikasi, dan dikembangkan untuk tujuan pembelajaran dan monitoring.
