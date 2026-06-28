# ⚖️ NyayaAI — AI-Powered Legal Awareness Chatbot

NyayaAI is a **Retrieval-Augmented Generation (RAG)** based legal awareness chatbot that helps users understand Indian laws related to **Cybercrime, Traffic & Motor Vehicle Laws, and Criminal Law (BNS & IT Act).**

The chatbot retrieves relevant legal information from its knowledge base before generating responses, making answers more accurate and reliable than a normal AI chatbot.

---

# 🚀 Features

- ✅ RAG-based Legal Question Answering
- ✅ Cybercrime Awareness
- ✅ Traffic & Motor Vehicle Law Guidance
- ✅ Criminal Law (BNS & IT Act)
- ✅ Topic Lock System
- ✅ English & Hindi Support
- ✅ Chat History
- ✅ Session Management
- ✅ PDF Upload & Analysis
- ✅ Image Upload & Analysis
- ✅ OCR-based PDF Reading
- ✅ Legal Knowledge Retrieval using ChromaDB
- ✅ Persona-based Responses
- ✅ Context-aware Conversations

---

# 🧠 How It Works

## Text Questions

1. User asks a legal question.
2. SentenceTransformer converts the question into embeddings.
3. ChromaDB retrieves the most relevant legal knowledge.
4. Retrieved context is sent to the Groq LLM.
5. The AI generates an answer using the retrieved legal context.

---

## PDF Upload

Users can upload documents such as:

- FIR Copy
- Court Notice
- Traffic Challan
- Legal Notice
- Complaint Copy
- Any Legal PDF

NyayaAI will:

- Read the PDF
- Extract text using OCR/PyMuPDF
- Search the legal knowledge base
- Explain the document
- Identify applicable laws
- Suggest practical next steps

---

## Image Upload

Users can upload images such as:

- Traffic Challan
- FIR Screenshot
- Scam Message
- Fraud Email
- WhatsApp Screenshot
- Legal Notice

NyayaAI will:

- Analyze the image
- Read visible text
- Explain the legal meaning
- Detect scams if applicable
- Suggest appropriate legal actions

---

# 📚 Supported Legal Domains

### 🔐 Cybercrime

Examples:

- Digital Arrest
- Phishing
- UPI Fraud
- Banking Fraud
- QR Code Scam
- Loan App Fraud
- OTP Fraud
- Crypto Scam
- Fake KYC
- Social Media Hacking

---

### 🚦 Traffic & Motor Vehicle Laws

Examples:

- Challans
- Helmet Rules
- Seat Belt Rules
- Driving Licence
- Registration
- Road Accidents
- Insurance
- Vehicle Documents
- RTO Procedures

---

### ⚖️ Criminal Law (BNS & IT Act)

Examples:

- Theft
- Robbery
- Assault
- Murder
- Cheating
- Forgery
- Dowry
- Cyber Offences
- BNS Sections
- IT Act Provisions

---

# 🏗️ Tech Stack

| Component | Technology |
|------------|------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Vector Database | ChromaDB |
| Embedding Model | SentenceTransformers |
| LLM | Groq API (Llama-3.3-70B-Versatile) |
| Vision Model | Qwen 3.6 27B |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| PDF Reader | PyMuPDF |
| Image Processing | Groq Vision |

---

# 📁 Project Structure

```
NyayaAI/

│
├── Backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── utils/
│
├── frontend/
│   ├── app.py
│   ├── components/
│   └── assets/
│
├── ai/
│   ├── config.py
│   ├── data/
│   │   ├── chroma_db/
│   │   ├── pdfs/
│   │   └── faqs/
│   └── ingest/
│
├── requirements.txt
├── README.md
└── .env
```

---

# ⚙️ Installation

## 1. Clone Repository

```bash
git clone <repository_url>
cd NyayaAI
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Configure Environment Variables

Create a `.env` file.

```env
GROQ_API_KEY=your_api_key

GROQ_MODEL=llama-3.3-70b-versatile

GROQ_VISION_MODEL=qwen/qwen3.6-27b

EMBEDDING_MODEL=BAAI/bge-base-en-v1.5

CHROMA_DB_PATH=ai/data/chroma_db
```

---

## 4. Setup PostgreSQL

Create a database named:

```
nyayaai_db
```

If upgrading from an older version, run:

```sql
ALTER TABLE chat_history
ADD COLUMN IF NOT EXISTS attachment_name VARCHAR;
```

---

## 5. Run Backend

```bash
cd Backend

uvicorn main:app --reload
```

---

## 6. Run Frontend

```bash
streamlit run frontend/app.py
```

---

# 📥 Adding New Legal Data

## PDF Documents

Place PDFs inside

```
ai/data/pdfs/
```

---

## FAQ Files

Place FAQ files inside

```
ai/data/faqs/
```

---

## Rebuild Knowledge Base

```bash
python -m ai.ingest.ingest_pipeline
```

The ChromaDB vector database will automatically update.

---

# 📎 Document Upload

Supported Formats

- PDF
- PNG
- JPG
- JPEG
- WEBP

NyayaAI can explain:

- FIR
- Court Notice
- Traffic Challan
- Fraud Message
- Legal Notice
- Complaint Copy

It extracts text, retrieves relevant legal information from the knowledge base, and generates an accurate explanation.

---

# 🌐 API Endpoints

| Method | Endpoint | Description |
|----------|-----------|-------------|
| POST | `/session/new` | Create new chat session |
| GET | `/sessions` | Get all chat sessions |
| GET | `/session/{id}/history` | Retrieve chat history |
| POST | `/chat` | Ask a legal question |
| POST | `/chat/upload` | Upload PDF/Image |
| DELETE | `/session/{id}` | Delete chat session |

---

# 🔒 Topic Lock

NyayaAI supports **Topic Lock**, allowing users to restrict conversations to a specific legal domain.

Available topics:

- Cybercrime
- Traffic & Motor Vehicle Laws
- Criminal Law (BNS & IT Act)
- All Topics

If a user asks a question outside the selected topic, NyayaAI requests them to switch the topic lock before proceeding.

---

# 🌍 Language Support

NyayaAI supports:

- English
- Hindi (Devanagari)

Responses are automatically generated in the language selected by the user.

---

# 🧩 AI Pipeline

```
User Question
        │
        ▼
SentenceTransformer Embedding
        │
        ▼
ChromaDB Semantic Search
        │
        ▼
Relevant Legal Context
        │
        ▼
Groq LLM
        │
        ▼
Final Legal Response
```

---

# 📌 Current Capabilities

- Legal Question Answering
- Retrieval-Augmented Generation (RAG)
- Context-Aware Responses
- Chat History
- Topic Lock
- PDF Understanding
- Image Understanding
- Scam Detection
- Legal Guidance
- OCR-Based Document Reading

---

# 🚀 Future Improvements

- Voice Input
- Voice Response
- Bare Act Search
- Court Judgment Search
- Citation Support
- Multi-file Upload
- Authentication & User Accounts
- PDF Highlighting
- Advanced OCR
- Legal Document Comparison

---

# 👨‍💻 Developed By

**Pramod**

AI/ML Developer | Data Science Enthusiast

Built using **FastAPI, Streamlit, ChromaDB, SentenceTransformers, PostgreSQL, and Groq LLM**.

---

# 📄 License

This project is intended for **educational and legal awareness purposes only**.

NyayaAI does **not** provide official legal advice and should not replace consultation with a qualified legal professional.
