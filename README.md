
# 📘 Resume Grader - AI-Powered Bulk Resume Analysis Platform

A comprehensive, production-ready automated resume evaluation system designed for Placement Teams, Recruiters, Colleges, and HR Departments to analyze resumes at scale.

---

## 🎯 What It Does

**Resume Grader** is an intelligent platform that automates the resume screening process, providing:

* **Bulk Upload & Processing** - Upload up to 50 PDFs directly or 200 resumes via CSV with Google Drive links
* **Intelligent Parsing** - Advanced PDF extraction with multi-column layout support and margin detection
* **Comprehensive Scoring** - Evaluate across 7 weighted buckets with 100-point scale
* **Smart Validation** - Detect formatting issues, missing information, and margin problems
* **Actionable Feedback** - Specific, detailed improvement suggestions for each resume
* **Professional Dashboard** - Modern, theme-adaptive Streamlit interface with filtering and sorting
* **Flexible Exports** - Download results in CSV, Excel, or JSON formats
* **Database Management** - SQLite/PostgreSQL support with migration capabilities

This project is designed for **scalability, accuracy, and automation**, perfectly matching the workflow of college placement cells, recruitment agencies, and training institutes.

---

## ✨ Recent Enhancements (v1.0)

### 🚀 CSV Google Drive Upload Feature (NEW!)
- **Batch Processing**: Upload CSV file with up to 200 Google Drive resume links
- **Automatic Download**: System downloads PDFs from public Google Drive links automatically
- **Template Provided**: Download pre-formatted CSV template from the UI
- **Real-time Progress**: Track download and processing progress for each resume
- **Detailed Results**: See which resumes succeeded/failed with specific error messages
- **Public Links Only**: No Google API authentication needed - just shareable links

### 🎨 Enhanced UI/UX
- ✅ **Theme-Adaptive Interface** - Seamless light/dark mode support throughout the app
- ✅ **Enhanced Resume List** - Full Resume IDs with copy buttons and quick view actions
- ✅ **Improved Detail Page** - Dynamic gradient scores, better metrics display, enhanced layout
- ✅ **Auto-Navigation** - Seamless flow from Resume List → Resume Details with session state

### 🔍 Advanced Contact Extraction
- ✅ **Indian Phone Validation** - Strict 10-digit validation (must start with 6-9)
- ✅ **Enhanced Email Detection** - PDF artifact handling and comprehensive validation
- ✅ **Format Normalization** - Consistent +91 phone format, lowercase emails
- ✅ **False Positive Filtering** - No more years/page numbers detected as phone numbers

### 📏 Professional Formatting Analysis
- ✅ **Margin Detection** - Validates all 4 margins against industry standards (0.5-1 inch)
- ✅ **Balance Checking** - Detects unbalanced left-right and top-bottom margins
- ✅ **Specific Feedback** - Exact measurements in inches with actionable advice
- ✅ **Layout Analysis** - Multi-column detection, font consistency scoring

### 🗄️ Database Management
- ✅ **Smart Reset** - Database reset now cleans upload folder automatically
- ✅ **No Orphaned Files** - Maintains consistency between database and filesystem
- ✅ **Detailed Feedback** - Shows count of deleted files on reset

---

## 📊 Comprehensive Scoring System

Each resume is evaluated across 7 weighted buckets for a holistic assessment:

| Bucket | Weight | Key Criteria | Max Points |
|--------|--------|--------------|------------|
| **Formatting & Styling** | 20% | Page count, bullets, spacing, fonts, **margins** | 100 |
| **Technical Skills** | 15% | Relevant technologies, programming languages | 100 |
| **Projects** | 15% | Technical projects with descriptions, action verbs | 100 |
| **Education** | 10% | Degree, institution, graduation year | 100 |
| **Contact Information** | 10% | Phone, email, LinkedIn, GitHub | 100 |
| **Work Experience** | 10% | Internships, jobs with measurable outcomes | 100 |
| **Soft Skills** | 5% | Communication, teamwork, leadership mentions | 100 |

**Overall Score Calculation (Scoring Engine v2.0)**: The bucket weights above sum to 85%, not 100% — this is
intentional (it preserves each bucket's relative importance, e.g. Formatting counts 2x Soft Skills), but the overall
score is always **normalized** so a perfect resume reaches exactly 100:

```
overall_score = Σ(bucket_score × weight) / Σ(weight)
```

Every score is traceable: each deduction is recorded as a structured finding with a severity (critical/high/medium/
low), the measured value, and what was expected (e.g. "Narrow margin: right (0.42in) — expected ≥ 0.5in"), returned
alongside `scoring_version` and `weight_total` from `/resumes/{id}` and `/resumes/process/{id}`.

### Formatting & Styling Breakdown
- **Page Count** (25 points): 1 page = full points, 2 pages = 15 points
- **Bullet Consistency** (15 points): Proper use of bullets or numbered lists
- **Spacing** (20 points): Consistent spacing between sections
- **Font Consistency** (20 points): Limited font sizes (2-3 maximum)
- **Margins** (20 points): Industry-standard margins on all sides
- **Contact at Top** (20 points): Contact information easily visible

### Margin Standards (Industry Best Practices)
- ✅ **Optimal**: 0.5-1 inch on all sides
- ⚠️ **Too Narrow**: < 0.5 inch (readability/printing issues)
- ⚠️ **Too Wide**: > 1.25 inch (wasted space)
- ⚠️ **Unbalanced**: > 0.25 inch difference between sides

---

## 🔥 Key Features

### Advanced PDF Parsing
- **pdfminer.six Integration** - Layout-aware text extraction that preserves structure
- **Multi-Column Support** - Correctly processes 2-3 column resume layouts
- **Font Analysis** - Font size and style consistency scoring across document
- **Link Extraction** - Extracts clickable URLs from PDF annotations
- **Margin Measurement** - Precise margin detection in points and inches
- **Fallback Strategy** - Uses pypdf if pdfminer fails, ensuring robustness

### Smart Validation & Detection
- **Phone Numbers**: Indian format only (10 digits starting with 6-9, optional +91)
- **Email Addresses**: Comprehensive validation with TLD checking and artifact handling
- **Formatting Rules**: Bullet points, spacing consistency, font uniformity
- **Professional Standards**: Margin requirements, page limits, section headers

### Comprehensive Feedback System
- **Specific Errors**: Exact issues identified with clear explanations
- **Actionable Advice**: How to fix each problem with concrete steps
- **Priority Levels**: Critical vs minor issues for focused improvements
- **Measurements**: Actual values provided (e.g., "left margin: 0.3 inch - increase to 0.5"")

### Modern UI/UX
- **Responsive Design**: Works seamlessly on all screen sizes
- **Theme Support**: Automatic light/dark mode based on user preferences
- **Quick Actions**: Copy Resume IDs, view details, export data with one click
- **Visual Feedback**: Progress indicators, success animations, error messages
- **Enhanced Navigation**: Seamless page transitions with session state management

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     STREAMLIT FRONTEND                       │
│  ┌─────────────┬──────────────┬─────────────┬─────────────┐│
│  │  Home Page  │ Upload Page  │ Resume List │ Detail Page ││
│  │  (app.py)   │ (Upload.py)  │  (List.py)  │(Details.py) ││
│  └─────────────┴──────────────┴─────────────┴─────────────┘│
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Endpoints: /upload, /process, /resumes, /export     │  │
│  └────────────────────┬─────────────────────────────────┘  │
│                       │                                      │
│       ┌───────────────┼───────────────┬─────────────────┐  │
│       ▼               ▼               ▼                 ▼  │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐│
│  │ Parser  │   │Extractor │   │ Scorer   │   │ Database ││
│  │ Engine  │──▶│ Engine   │──▶│ Engine   │──▶│  (ORM)   ││
│  └─────────┘   └──────────┘   └──────────┘   └──────────┘│
│      │              │               │               │      │
│   pdfminer      Regex+NLP      7 Buckets      SQLAlchemy  │
│   Multi-col     Contact Info   Weighted       SQLite/     │
│   Layout        Skills/Exp     Scoring        PostgreSQL  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Technology Stack

### **Frontend (Streamlit)**
- `streamlit` - Modern web UI framework with reactive components
- `requests` - HTTP client for API communication
- `plotly` - Interactive data visualization
- `pandas` - Data manipulation and CSV handling
- Custom theme-adaptive components with dark mode support

### **Backend (FastAPI)**
- `fastapi` - High-performance async web framework
- `uvicorn[standard]` - ASGI server with auto-reload
- `pydantic` - Data validation and settings management
- `python-multipart` - File upload handling
- `sqlalchemy` - Database ORM for SQLite/PostgreSQL
- `alembic` - Database migration management

### **PDF Processing**
- `pypdf` - PDF reading and link extraction
- `pdfminer.six` - Layout-aware text extraction with column detection
- Multi-column detection algorithms for complex layouts
- Font and margin analysis utilities

### **Data Extraction & Analysis**
- Regular expressions for pattern matching (emails, phones, dates)
- Custom validation functions for contact info
- Unicode normalization for PDF artifact handling
- `spacy` - NLP capabilities (optional, for future enhancements)

### **Scoring & Analysis**
- 7-bucket weighted scoring system
- Margin detection using industry standards
- Font consistency analysis
- Contact information validation with Indian phone number support

### **Data Export**
- `pandas` - Data processing and transformation
- `xlsxwriter` - Excel file generation
- Built-in CSV writer
- JSON serialization for API responses

### **Database**
- **Development**: SQLite (file-based, zero configuration)
- **Production**: PostgreSQL-ready with connection pooling
- Migration system using Alembic
- Session management with SQLAlchemy ORM

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git (for cloning repository)
- Virtual environment support
- 2GB free disk space (for dependencies and uploads)

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/Anurag-Ahirwar/resume-grader.git
cd resume-grader
```

#### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including FastAPI, Streamlit, pdfminer.six, pandas, and more.

---

## 🖥️ Running the Application

You need to run both the backend and frontend simultaneously in separate terminals.

### Terminal 1 - Start Backend Server

```bash
# Activate virtual environment (if not already activated)
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Mac/Linux

# Start FastAPI backend
python -m uvicorn backend.app.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\resume-grader']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Access API Documentation:**
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Terminal 2 - Start Frontend Application

```bash
# Open a new terminal
cd resume-grader

# Activate virtual environment
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Mac/Linux

# Start Streamlit frontend
python -m streamlit run frontend_streamlit/app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

**Access Application:**
- Open browser and navigate to: http://localhost:8501

---

## 📤 How to Use - Upload Methods

### Method 1: Direct PDF Upload

1. Navigate to **"Upload Resumes"** page
2. Click on **"Upload PDF Files"** tab
3. Select up to 50 PDF files from your computer
4. Click **"Upload & Process Resumes"**
5. Wait for processing to complete (progress bar shown)
6. Navigate to **"Resume List"** to view results

### Method 2: CSV with Google Drive Links (Recommended for Bulk)

#### Step 1: Prepare Google Drive Links

For each resume PDF in Google Drive:
1. Right-click the file
2. Click **"Share"**
3. Change from "Restricted" to **"Anyone with the link"**
4. Set permission to **"Viewer"**
5. Click **"Copy link"**

#### Step 2: Create CSV File

1. Go to **"Upload Resumes"** → **"Upload CSV (Google Drive Links)"** tab
2. Click **"Download Template CSV"**
3. Open template in Excel/Google Sheets
4. Paste Google Drive links in the `resume_link` column
5. Save file as CSV

**Example CSV:**
```csv
resume_link
https://drive.google.com/file/d/1ABC123XYZ456/view
https://drive.google.com/file/d/1DEF789UVW012/view
https://drive.google.com/file/d/1GHI345RST678/view
```

#### Step 3: Upload and Process

1. Click **"Choose CSV file"** and select your CSV
2. Preview shows first 10 rows for verification
3. Validation checks for required column and row limit
4. Click **"Download & Process All Resumes"**
5. Monitor progress:
   - Download progress (0-50%)
   - Processing progress (50-100%)
6. Review results table showing successful/failed downloads
7. Navigate to **"Resume List"** to view all processed resumes

---

## 🔌 API Endpoints Reference

### Core Endpoints

#### Upload PDF Files
```http
POST /resumes/upload
Content-Type: multipart/form-data

files: [PDF files]

Response:
{
  "upload_ids": ["uuid1", "uuid2", ...]
}
```

#### Upload CSV with Google Drive Links
```http
POST /resumes/upload-csv
Content-Type: multipart/form-data

file: resumes.csv

Response:
{
  "total": 10,
  "successful": 8,
  "failed": 2,
  "upload_ids": ["uuid1", "uuid2", ...],
  "results": [...]
}
```

#### Process Resume
```http
POST /resumes/process/{upload_id}

Response:
{
  "resume_id": "uuid",
  "overall_score": 81.5,
  "scoring_version": "2.0",
  "weight_total": 0.85,
  "buckets": [
    {"name": "Formatting & Styling", "score": 95.0, "weight": 0.2, "weighted_score": 19.0}
  ]
}
```

#### List Resumes
```http
GET /resumes?min_score=50&max_score=100&sort_by=score_desc

Query Parameters:
- min_score: Minimum score filter (0-100)
- max_score: Maximum score filter (0-100)
- missing_linkedin: Boolean filter
- missing_github: Boolean filter
- no_projects: Boolean filter
- sort_by: score_desc, score_asc, latest, oldest

Response:
[
  {
    "resume_id": "uuid",
    "overall_score": 85,
    "created_at": "2026-01-05T...",
    ...
  }
]
```

#### Get Resume Details
```http
GET /resumes/{resume_id}

Response:
{
  "resume_id": "uuid",
  "overall_score": 81.5,
  "scoring_version": "2.0",
  "weight_total": 0.85,
  "buckets": [...],
  "mistakes": [
    {"category": "Formatting & Styling", "mistake": "...", "feedback": "...",
     "severity": "medium", "criterion": "margins", "value": "0.42in", "expected": ">= 0.5in"}
  ],
  "contact_info": {...}, "skills": [...], "experience": [...], "projects": [...], "education": [...]
}
```

### Export Endpoints

```http
GET /export/csv      # Download all resumes as CSV
GET /export/excel    # Download all resumes as Excel (.xlsx)
GET /export/json     # Download all resumes as JSON
```

### Admin Endpoints

```http
POST /admin/reset-db

Response:
{
  "status": "success",
  "message": "Database reset successfully. X uploaded file(s) deleted."
}
```

⚠️ **Warning**: This permanently deletes all data and uploaded files!

---

## 🧪 Testing

Run the contact extraction test suite:

```bash
python test_contact_extraction.py
```

**Tests Include:**
- Phone number validation (Indian format)
- Email extraction with PDF artifacts
- Contact information parsing
- Margin detection validation

---

## 🐛 Troubleshooting

### Common Issues

**1. PDF Not Parsing Correctly**
- Ensure PDF is text-based (not scanned image)
- Check for multi-column layouts (system handles 2-3 columns)
- Try re-saving PDF from original document (Word/Google Docs)

**2. Contact Info Not Detected**
- Phone numbers must be 10 digits starting with 6-9
- Emails must have valid TLD (.com, .in, .org, etc.)
- Check for PDF extraction artifacts (spaces in email/phone)

**3. Low Formatting Score**
- Check margins (should be 0.5-1 inch on all sides)
- Limit to 1-2 pages maximum
- Use consistent fonts (2-3 sizes maximum)
- Add proper spacing between sections

**4. CSV Upload Fails**
- Ensure CSV has `resume_link` column
- Verify Google Drive links are public ("Anyone with link")
- Check that links point to PDF files, not Google Docs
- Maximum 200 resumes per CSV

**5. Google Drive Download Timeout**
- File may be too large (max 10MB per PDF)
- Check internet connection stability
- Compress large PDFs before uploading to Drive

**6. Database Issues**
- Use **Admin Reset DB** to clear database
- Check that `resume_grader.db` file exists in project root
- Verify SQLite is properly installed

---

## 📈 Use Cases & Applications

### ✅ College Placement Cells
- Screen hundreds of student resumes efficiently
- Provide standardized feedback to students
- Track resume quality across batches
- Export reports for placement coordinators

### ✅ HR Departments
- Standardize candidate evaluation process
- Reduce manual screening time by 80%
- Identify top candidates quickly
- Maintain consistency across recruiters

### ✅ Recruitment Agencies
- Bulk process client resumes
- Quality check before client submission
- Provide value-added resume feedback
- Scale operations without additional resources

### ✅ Training Institutes
- Provide detailed resume feedback to students
- Track improvement over training period
- Benchmark against industry standards
- Automate feedback delivery

---

## 🛠 Future Roadmap

### Short-term
- [ ] Docker containerization for easy deployment
- [ ] CI/CD pipeline setup with GitHub Actions
- [ ] Comprehensive unit test suite
- [ ] API authentication with JWT tokens

### Medium-term
- [ ] Resume comparison feature (side-by-side)
- [ ] Advanced analytics dashboard
- [ ] Email notifications for batch completion
- [ ] Resume template suggestions

### Long-term
- [ ] AI-powered resume improvements (GPT integration)
- [ ] OCR support for scanned/image PDFs
- [ ] ATS-style keyword matching engine
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Resume anonymization feature
- [ ] PDF feedback report generation

---

## 📝 Project Status

**Version**: 1.0  
**Status**: Production-Ready  ✅  
**Last Updated**: 05th January 2026

### Recent Updates
- ✅ CSV Google Drive upload feature
- ✅ Enhanced contact extraction with validation
- ✅ Professional margin detection
- ✅ Improved UI/UX with theme support
- ✅ Smart database cleanup on reset
- ✅ Advanced PDF parsing with multi-column support

---

## 👥 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Add tests for new functionality
5. Commit changes (`git commit -m 'Add AmazingFeature'`)
6. Push to branch (`git push origin feature/AmazingFeature`)
7. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints to functions
- Write docstrings for public APIs
- Include tests for new features
- Update documentation as needed

---

## 📄 License

This project is open source and available for educational and commercial use.

---

## 👤 Author

**Anurag Ahirwar**  
GitHub: [@Anurag-Ahirwar](https://github.com/Anurag-Ahirwar)

---

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

## 🎯 Summary

This is a **full production-grade** resume analysis platform featuring:

✅ **Advanced Parsing** - Multi-column layouts, margin detection, font analysis  
✅ **Smart Validation** - Phone/email validation, formatting checks  
✅ **Comprehensive Scoring** - 7-bucket weighted system with detailed feedback  
✅ **Bulk Processing** - CSV upload with Google Drive integration (up to 200 resumes)  
✅ **Modern UI** - Theme-adaptive Streamlit interface with enhanced UX  
✅ **Flexible Exports** - CSV, Excel, JSON formats  
✅ **Professional Standards** - Industry-standard margin requirements and validation  
✅ **Clean Architecture** - Modular, maintainable, scalable codebase  

**Perfect for**: Placement cells, HR teams, recruitment agencies, training institutes

---

**Built with ❤️ for efficient recruitment and student placement**
