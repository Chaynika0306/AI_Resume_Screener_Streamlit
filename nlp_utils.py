# nlp_utils.py
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# NLTK resources (will download on first import if missing)
def ensure_nltk():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords")
    try:
        nltk.data.find("corpora/wordnet")
    except LookupError:
        nltk.download("wordnet")

ensure_nltk()

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).lower()
    # keep alphanum and spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def preprocess(text: str) -> str:
    text = clean_text(text)
    tokens = nltk.word_tokenize(text)
    tokens = [t for t in tokens if t not in stop_words and len(t) > 1 and not t.isdigit()]
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    return " ".join(tokens)

def compute_tfidf_scores(resume_texts, jd_text, ngram_range=(1,2)):
    """
    resume_texts: list[str] preprocessed resumes
    jd_text: preprocessed jd
    returns: scores (numpy array), top_keywords(list), vectorizer
    """
    corpus = list(resume_texts) + [jd_text]
    vectorizer = TfidfVectorizer(ngram_range=ngram_range)
    X = vectorizer.fit_transform(corpus)
    jd_vec = X[-1]
    resume_vecs = X[:-1]
    scores = cosine_similarity(resume_vecs, jd_vec).flatten()
    # extract top JD features
    feature_names = vectorizer.get_feature_names_out()
    jd_dense = jd_vec.todense()
    coefs = np.asarray(jd_dense).ravel()
    top_idx = coefs.argsort()[-20:][::-1]  # top 20 ngram features
    top_keywords = [feature_names[i] for i in top_idx if coefs[i] > 0]
    return scores, top_keywords, vectorizer
