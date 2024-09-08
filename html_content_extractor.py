import requests
from bs4 import BeautifulSoup
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from urllib.parse import urljoin
import pickle

class HTMLContentExtractor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.classifier = MultinomialNB()

    def train(self, training_data):
        X = self.vectorizer.fit_transform([item['text'] for item in training_data])
        y = [item['label'] for item in training_data]
        self.classifier.fit(X, y)

    def save_model(self, vectorizer_path, classifier_path):
        with open(vectorizer_path, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        with open(classifier_path, 'wb') as f:
            pickle.dump(self.classifier, f)

    def load_model(self, vectorizer_path, classifier_path):
        with open(vectorizer_path, 'rb') as f:
            self.vectorizer = pickle.load(f)
        with open(classifier_path, 'rb') as f:
            self.classifier = pickle.load(f)

    def extract_content(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string if soup.title else ""

        author = soup.find('meta', {'name': 'author'})
        author = author['content'] if author else ""

        date = soup.find('meta', {'property': 'article:published_time'})
        date = date['content'] if date else ""

        main_content = self._extract_main_content(soup)

        images = self._extract_images(soup, url)

        return {
            'title': title,
            'author': author,
            'date': date,
            'content': main_content,
            'images': images
        }

    def _extract_main_content(self, soup):
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        paragraphs = text.split('\n')
        X = self.vectorizer.transform(paragraphs)
        labels = self.classifier.predict(X)

        main_content = [p for p, label in zip(paragraphs, labels) if label == 'main_content']

        return '\n\n'.join(main_content)

    def _extract_images(self, soup, base_url):
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                alt = img.get('alt', '')
                images.append({'url': full_url, 'alt': alt})
        return images

def format_as_markdown(extracted_content):
    md = f"# {extracted_content['title']}\n\n"
    
    if extracted_content['author']:
        md += f"**Author:** {extracted_content['author']}\n\n"
    
    if extracted_content['date']:
        md += f"**Date:** {extracted_content['date']}\n\n"
    
    md += extracted_content['content'] + "\n\n"
    
    if extracted_content['images']:
        md += "## Images\n\n"
        for img in extracted_content['images']:
            md += f"![{img['alt']}]({img['url']})\n\n"
    
    return md