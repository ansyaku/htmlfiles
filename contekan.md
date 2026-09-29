# Cheatsheet: Konversi PDF → Markdown dengan Marker

Env: `~/venv-marker` (Python 3.11)
Jalankan dari folder yang berisi `pdftotext.py` dan file PDF-nya.

## Tentang setup ini

**Marker** adalah tool open-source (dari Datalab, package `marker-pdf`) untuk mengubah PDF menjadi Markdown. Tool ini memakai model deep learning (berbasis PyTorch) untuk OCR, deteksi layout, tabel, dan persamaan. Hasilnya jauh lebih rapi dibanding ekstraksi teks biasa, terutama untuk paper akademik dengan rumus dan tabel, tetapi prosesnya lebih lambat dan berat di memori. Itulah sebabnya file diproses berurutan, bukan paralel.

**`venv-marker`** adalah virtual environment Python terpisah di `~/venv-marker`, dibuat dari Python 3.11 Homebrew (`/opt/homebrew/bin/python3.11`). Semua dependensi marker (torch, transformers, dan lain-lain) terpasang di dalamnya, sehingga tidak tercampur dengan Python sistem Apple (3.9) maupun env proyek lain, misalnya env tesis.

**`pdftotext.py`** adalah script pembungkus yang memanggil marker (opsi `--engine marker`) untuk satu file PDF.

Cek package yang terpasang:

```bash
python -m pip show marker-pdf    # versi marker
python -m pip list               # semua package di env
```

Kalau env ini rusak atau hilang, buat ulang dengan:

```bash
/opt/homebrew/bin/python3.11 -m venv ~/venv-marker
source ~/venv-marker/bin/activate
python -m pip install --upgrade pip
python -m pip install marker-pdf
```

## 1. Aktifkan environment

```bash
source ~/venv-marker/bin/activate
python --version        # harus 3.11.x
```

Keluar dari env setelah selesai:

```bash
deactivate
```

## 2. Satu file

```bash
python3 pdftotext.py 15.pdf --engine marker
```

## 3. Rentang berurutan (misal 16 sampai 20)

Berjalan satu per satu, file berikutnya baru mulai setelah yang sebelumnya selesai.

```bash
for i in {16..20}; do python3 pdftotext.py $i.pdf --engine marker; done
```

Berhenti kalau ada file yang gagal:

```bash
for i in {16..20}; do python3 pdftotext.py $i.pdf --engine marker || break; done
```

## 4. Daftar nomor tertentu (misal 12, 17, 19)

```bash
for i in 12 17 19; do python3 pdftotext.py $i.pdf --engine marker; done
```

Berhenti kalau ada yang gagal:

```bash
for i in 12 17 19; do python3 pdftotext.py $i.pdf --engine marker || break; done
```

## 5. Semua PDF di folder (nama file bebas)

```bash
for f in *.pdf; do python3 pdftotext.py "$f" --engine marker; done
```

Tanda kutip pada `"$f"` membuat nama file yang mengandung spasi tetap aman.

## Catatan

- Kalau muncul error module/marker tidak ditemukan, kemungkinan env belum aktif. Cek dengan `which python`, hasilnya harus `~/venv-marker/bin/python`.
- Format rentang `{a..b}` dan daftar `a b c` bisa digabung, misalnya `for i in 3 5 {10..14}; do ...; done`.
