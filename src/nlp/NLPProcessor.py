import re
import unicodedata
import nltk
from nltk.stem import RSLPStemmer

nltk.download('rslp', quiet=True)

class NLPProcessor:
    def __init__(self):
        self.stemmer = RSLPStemmer()

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        return text

    def stem(self, word: str) -> str:
        return self.stemmer.stem(self.normalize(word))

    def process_text(self, text: str):
        clean = re.sub(r'[^\w\s]', '', self.normalize(text))
        tokens = clean.split()
        stemmed = [self.stemmer.stem(t) for t in tokens]
        return stemmed, text