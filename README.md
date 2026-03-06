# 🤖 AI Resume Screener

An **AI-powered Resume Screening System** built using **Python, NLP, and Streamlit**.
This application helps recruiters automatically analyze resumes and match them with job descriptions by calculating a **similarity score**.

---

## 🚀 Features

* 📄 Upload resume files
* 🧠 NLP-based resume parsing
* 🎯 Job Description vs Resume similarity scoring
* 📊 Automatic resume ranking
* 📁 Generate screening report (CSV)
* 🌐 Interactive Streamlit UI
* ⚡ Fast and lightweight implementation

---

## 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **Natural Language Processing (NLP)**
* **Scikit-learn**
* **Pandas**
* **TF-IDF Vectorization**

---

## 📂 Project Structure

```
AI_Resume_Screener_Streamlit
│
├── app_streamlit.py              # Main Streamlit application
├── resume_parser.py              # Resume parsing logic
├── nlp_utils.py                  # NLP preprocessing utilities
├── requirements.txt              # Project dependencies
├── Sample_job_description.txt    # Example job description
├── sample_data/                  # Sample resumes and job descriptions
├── assets/                       # Images and logos
├── screenshots/                  # UI screenshots
└── README.md
```

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```
git clone https://github.com/Chaynika0306/AI_Resume_Screener_Streamlit.git
```

### 2️⃣ Navigate to project folder

```
cd AI_Resume_Screener_Streamlit
```

### 3️⃣ Create virtual environment

```
python -m venv .venv
```

### 4️⃣ Activate virtual environment

Windows:

```
.venv\Scripts\activate
```

Mac/Linux:

```
source .venv/bin/activate
```

### 5️⃣ Install dependencies

```
pip install -r requirements.txt
```

---

## ▶️ Run the Application

```
streamlit run app_streamlit.py
```

The application will open in your browser:

```
http://localhost:8501
```

---

## 📊 How It Works

1. User uploads a resume.
2. System extracts text from the resume.
3. Job description is processed using NLP.
4. TF-IDF vectorization converts text to numerical features.
5. Cosine similarity calculates the **match score**.
6. Resume ranking report is generated.

---

## 📈 Example Output

| Resume   | Match Score |
| -------- | ----------- |
| Resume A | 82%         |
| Resume B | 67%         |
| Resume C | 54%         |

---

## 🔮 Future Improvements

* Support for **PDF and DOCX parsing**
* **Deep learning based resume ranking**
* Integration with **ATS systems**
* **Automatic skill extraction**
* Dashboard for recruiters

---

## 👩‍💻 Author

**Chaynika Vyas**

GitHub:
https://github.com/Chaynika0306

---

⭐ If you found this project useful, please consider giving it a **star** on GitHub!
