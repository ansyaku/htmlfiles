# Screening Saham Bluechip US

Halaman statis (GitHub Pages) tanpa build/dependensi untuk menyaring 170 saham dari Dow 30, S&P 100, dan Nasdaq-100.

- `index.html` – halaman Screening: filter, 7 indikator fundamental + skor, subsektor
- `ringkasan.html` – jumlah saham per indeks, irisan, diagram persentase per sektor/subsektor
- `data/universe.json` – daftar saham, sektor, subsektor (GICS Industry), keanggotaan indeks (ubah manual saat indeks berubah)
- `data/quotes.json` – harga & valuasi, diperbarui otomatis tiap hari kerja oleh GitHub Actions
- `scripts/update_data.py` + `.github/workflows/update-data.yml` – pengambil data harian (Yahoo Finance via yfinance)

## Cara pasang
1. Buat repo GitHub, upload semua file ini.
2. Settings → Pages → Source: *Deploy from a branch*, branch `main`, folder `/ (root)`.
3. Actions → *Update data harian* → *Run workflow* sekali untuk mengisi data pertama (S&P 100 yang belum ada angkanya akan terisi).
4. Seterusnya berjalan otomatis tiap hari kerja pukul 22:30 UTC.

Catatan: yfinance bukan API resmi; kalau gagal, nilai terakhir dipertahankan. Keanggotaan indeks di `universe.json` tidak diperbarui otomatis.
Uji lokal: `python -m http.server` lalu buka http://localhost:8000.

## 7 indikator
Diambil dari laporan keuangan tahunan Yahoo Finance (NPM, ROE, pertumbuhan pendapatan & EPS, current ratio, Net Debt/EBITDA & DER, interest coverage, FCF/laba). Ambang batas ada di bagian "Aturan penilaian" pada halaman dan di fungsi `evaluate()` dalam `index.html`. Sektor Financials hanya dinilai pada indikator 1-3. Data fundamental baru terisi setelah workflow pertama jalan.
