from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def calculate_match(resume_text, job_description):

    documents = [resume_text, job_description]

    vectorizer = TfidfVectorizer()

    tfidf = vectorizer.fit_transform(documents)

    score = cosine_similarity(tfidf[0:1], tfidf[1:2])

    return round(score[0][0] * 100, 2)
