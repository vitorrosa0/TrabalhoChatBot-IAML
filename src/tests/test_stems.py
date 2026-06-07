import re, unicodedata
from nltk.stem import RSLPStemmer

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c))

s = RSLPStemmer()

palavras = ["ação", "comédia", "drama", "terror", "suspense", "romance", "animação", "ficção"]
for p in palavras:
    print(f"{p} → {s.stem(normalize(p))}")