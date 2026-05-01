import re
import nltk
from nltk.stem import RSLPStemmer

nltk.download('rslp', quiet=True)

class NLPProcessor:
    def __init__(self):
        self.stemmer = RSLPStemmer()

    def stem(self, word: str) -> str:
        return self.stemmer.stem(word.lower())

    def process_text(self, text: str):
        clean = re.sub(r'[^\w\s]', '', text.lower())  # remove ? ! . , etc
        tokens = clean.split()
        stemmed = [self.stem(t) for t in tokens]
        return stemmed, text