# Product Review Analyzer

Aplikasi web untuk menganalisis review produk menggunakan AI.

---

## Identitas

**Nama:** Muhammad Nurikhsan  
**NIM:** 123140057  
**Mata Kuliah:** Pemrograman Aplikasi Web  
**Semester:** 5

---

## Tentang Aplikasi

Aplikasi ini dibuat untuk menganalisis review produk secara otomatis menggunakan AI. Review yang diinput akan dianalisis sentimentnya (positif/negatif/netral) dan diekstrak poin-poin pentingnya.

---

## Fitur

1. **Analisis Sentiment** - Mendeteksi apakah review positif, negatif, atau netral dengan confidence score
2. **Ekstraksi Key Points** - Mengambil poin-poin penting dari review
3. **Riwayat Review** - Menyimpan dan menampilkan semua review yang pernah dianalisis
4. **Filter Sentiment** - Filter review berdasarkan sentiment tertentu

---

## Tech Stack

**Backend:**
- Flask (Python web framework)
- PostgreSQL (Database)
- SQLAlchemy (ORM)

**Frontend:**
- React JS
- Axios
- CSS

**AI:**
- Hugging Face (Sentiment Analysis)
- Google Gemini (Key Points Extraction)

---

## Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/muhammad-nurikhsan/tugas_individu3.git
cd tugas_individu3
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Buat file `.env`:
```env
DATABASE_URL=postgresql://postgres:password@localhost/review_analyzer_db
HUGGINGFACE_API_KEY=your_token
GEMINI_API_KEY=your_key
```

Buat database di PostgreSQL:
```sql
CREATE DATABASE review_analyzer_db;
```

Jalankan server:
```bash
python app.py
```

### 3. Setup Frontend

```bash
cd frontend
npm install
npm start
```

Aplikasi berjalan di `http://localhost:3000`

---

## Cara Pakai

1. Buka aplikasi di browser
2. Isi nama produk dan review
3. Klik "Analyze Review"
4. Tunggu beberapa detik
5. Hasil analisis akan muncul dengan sentiment dan key points

---

## API Endpoints

### POST `/api/analyze-review`
Analyze review baru.

**Request:**
```json
{
  "product_name": "iPhone 15",
  "review_text": "Great phone but expensive"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "sentiment": "positive",
    "sentiment_score": 0.85,
    "key_points": ["Great phone", "Expensive"]
  }
}
```

### GET `/api/reviews`
Ambil semua review.

**Optional params:**
- `limit` - jumlah data
- `sentiment` - filter sentiment

---

## Database

**Table: reviews**

| Kolom           | Tipe     | Keterangan                    |
|-----------------|----------|-------------------------------|
| id              | Integer  | Primary key                   |
| product_name    | String   | Nama produk                   |
| review_text     | Text     | Isi review                    |
| sentiment       | String   | positive/negative/neutral     |
| sentiment_score | Float    | Confidence (0-1)              |
| key_points      | Text     | JSON array key points         |
| created_at      | DateTime | Waktu dibuat                  |

---

## Testing

**Backend:**
```powershell
# Health check
curl http://localhost:5000/api/health

# Test analyze
$body = @{
    product_name = "Test Product"
    review_text = "This is a test review"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:5000/api/analyze-review -Method POST -Body $body -ContentType "application/json"
```

**Frontend:**
- Buka developer tools (F12)
- Cek console untuk error
- Test form input dan hasil

---

## Dokumentasi

**1. Review Form**
   ![Page Review Form](screenshot/ReviewForm.png)
**2. Analysis Results**
   ![Page Analysis Result](screenshot/AnalaysisResult.png)
**3. Database**
   ![Database](screenshot/Database.png)   

---

## Kendala & Solusi

**1. AI Processing Lama**
- Masalah: Response time 5-10 detik
- Solusi: Tambahkan loading indicator

**2. Rate Limit API**
- Masalah: Hugging Face free tier punya limit
- Solusi: Error handling yang baik

**3. JSON Response Tidak Konsisten**
- Masalah: Gemini kadang return format berbeda
- Solusi: Parsing dengan fallback handling

---

## Catatan

- File `.env` jangan di-commit ke Git
- API keys harus dijaga kerahasiaannya
- Database harus dibuat manual sebelum run aplikasi

---

**Muhammad Nurikhsan (123140057)**  
Institut Teknologi Sumatera - 2025