# 🛡️ Smart Amp IoT Protection System

![Project Status](https://img.shields.io/badge/Status-Stable-success)
![Version](https://img.shields.io/badge/Version-v1.0-blue)
![Python](https://img.shields.io/badge/Python-3.x-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

> **Sistem Proteksi & Monitoring Amplifier Kelas-D Berbasis IoT dengan Mekanisme Safety Latching & OTA Firmware Update.**

---

## 📖 Overview (Ringkasan)

**Smart Amp IoT System** adalah solusi perangkat lunak berbasis Desktop (Python) yang dirancang untuk memantau kesehatan *Power Amplifier* secara *real-time* melalui protokol internet (MQTT). 

Sistem ini tidak hanya berfungsi sebagai monitoring pasif, tetapi juga sebagai **Sistem Proteksi Aktif** yang dapat memutus daya secara otomatis saat terjadi anomali (Over-Heat atau Short Circuit). Dilengkapi dengan fitur **Lifecycle Management** yang memungkinkan aplikasi mendeteksi pembaruan versi (Firmware Update) secara otomatis melalui Cloud.

---

## ✨ Key Features (Fitur Unggulan)

Fitur-fitur ini merupakan kontribusi utama (Novelty) dalam penelitian ini:

### 1. 📡 IoT Remote Monitoring
Memisahkan status koneksi "Cloud" dengan status "Hardware". Data tegangan, arus, dan suhu dikirim dari ESP32 ke Desktop App via Broker MQTT (`broker.emqx.io`) dengan latensi rendah.

### 2. 🔐 Safety Latching Logic (Standar Industri)
Mengadopsi standar keamanan industri dimana sistem proteksi bersifat **Non-Self-Resetting**. 
* Jika proteksi terpicu (TRIP), sistem akan terkunci dalam keadaan mati.
* Mewajibkan operator melakukan **Manual Reset** melalui GUI untuk menyalakan kembali alat.
* Mencegah *power oscillation* (hidup-mati berulang) yang merusak komponen.

### 3. ☁️ OTA Firmware Update (Self-Diagnostic)
Aplikasi memiliki kemampuan **Self-Update**. Sistem secara otomatis mengecek repository GitHub untuk membandingkan versi lokal dengan versi Cloud. Jika versi baru tersedia, sistem akan mengarahkan pengguna untuk mengunduh pembaruan.

### 4. 🎛️ Software-Based Sensor Calibration
Fitur kalibrasi *offset* sensor (Suhu & Arus) yang dapat diatur langsung melalui GUI tanpa perlu memprogram ulang mikrokontroler atau memutar trimpot fisik.

---

## 📸 Screenshots

*(Upload screenshot aplikasi kamu ke folder `assets` atau `images` di repo ini, lalu ganti link di bawah ini)*

| Dashboard Monitoring | Logic Analysis |
|:---:|:---:|
| ![Dashboard Monitoring](https://github.com/user-attachments/assets/c0cae0ea-9093-4d8c-957f-82e83ebcb0cf) | ![Logic Analysis](https://github.com/user-attachments/assets/9f0f880c-3eeb-4fd9-9d16-0b4a95121e1a) |

| OTA Update Notification | Calibration Menu |
|:---:|:---:|
| ![OTA Update](https://placehold.co/600x400?text=OTA+Alert) | ![Calibration](https://placehold.co/600x400?text=Calibration) |

---

## 🛠️ Tech Stack & Hardware

### Software
* **Language:** Python 3.10+
* **GUI Framework:** Tkinter (Custom Dark Theme)
* **Communication:** MQTT Protocol (`paho-mqtt`)
* **Data Viz:** Matplotlib (Live Graph)
* **Packaging:** PyInstaller (Standalone .EXE)

### Hardware
* **MCU:** ESP32 DevKit V1
* **Sensor Arus:** INA219 (I2C)
* **Sensor Suhu:** LM35 (Analog)
* **Actuator:** Relay Module 5V (Active Low/High)
* **Load:** Class-D Power Amplifier

---

## 🚀 Installation & Usage

### Opsi 1: Menggunakan Executable (Recommended)
Untuk pengguna umum atau pengujian tanpa instalasi Python:
1.  Buka tab **[Releases](../../releases)** di repository ini.
2.  Download file `.exe` versi terbaru (misal: `SmartAmp_v1.0.exe`).
3.  Jalankan aplikasi (Portable, tidak perlu install).

### Opsi 2: Menjalankan Source Code (Developer)
1.  Clone repository ini:
    ```bash
    git clone [https://github.com/username/smartamp-iot.git](https://github.com/username/smartamp-iot.git)
    cd smartamp-iot
    ```
2.  Install library yang dibutuhkan:
    ```bash
    pip install -r requirements.txt
    ```
3.  Jalankan aplikasi:
    ```bash
    python main.py
    ```

---

## 🔄 OTA Update Mechanism

Sistem OTA bekerja dengan alur berikut:
1.  Aplikasi membaca file `version.txt` di repository ini (Raw URL).
2.  Aplikasi membandingkan dengan versi internal (`self.app_version`).
3.  Jika **Versi Cloud > Versi Lokal**, notifikasi update muncul.
4.  User diarahkan ke halaman **Releases** untuk mengunduh *binary* terbaru.

---

## 📝 License

Project ini dibuat untuk keperluan penelitian akademis (Skripsi/Jurnal).
Dilisensikan di bawah **MIT License**.

**Developed by Andri - 2024/2025**
