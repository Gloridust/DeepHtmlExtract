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
        self.classifier = MultinomialNB(alpha=0.1)  # Decreased alpha for less smoothing

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

        main_content = self._extract_main_content(soup, url)

        return {
            'title': title,
            'author': author,
            'date': date,
            'content': main_content
        }

    def _extract_main_content(self, soup, base_url):
        for script in soup(["script", "style"]):
            script.decompose()

        # Remove obvious navigation elements
        for nav in soup.find_all(['nav', 'header', 'footer']):
            nav.decompose()

        # Try to find the main content area
        main_content_area = soup.find('article') or soup.find('main') or soup.find('div', class_='content') or soup.body

        # Extract content with structure and images
        content = self._extract_structured_content(main_content_area, base_url)

        # Classify each paragraph
        paragraphs = content.split('\n')
        X = self.vectorizer.transform(paragraphs)
        probabilities = self.classifier.predict_proba(X)

        # Keep paragraphs classified as main content or with high probability
        main_content = []
        for p, prob in zip(paragraphs, probabilities):
            if prob[1] > 0.3 or p.strip().startswith(('#', '![', '```')):  # Adjusted threshold
                main_content.append(p)
            elif len(p.split()) > 20:  # Keep longer paragraphs
                main_content.append(p)

        return '\n'.join(main_content)

    def _extract_structured_content(self, element, base_url, level=0):
        if element is None:
            return ""
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return f"{'#' * (int(element.name[1]) + level)} {element.get_text().strip()}\n"
        elif element.name == 'p':
            return f"{element.get_text().strip()}\n"
        elif element.name in ['ul', 'ol']:
            content = ""
            for li in element.find_all('li', recursive=False):
                content += f"{'  ' * level}- {li.get_text().strip()}\n"
            return content
        elif element.name == 'blockquote':
            return f"> {element.get_text().strip()}\n"
        elif element.name == 'img':
            src = element.get('src')
            if src:
                full_url = urljoin(base_url, src)
                alt = element.get('alt', '')
                return f"![{alt}]({full_url})\n"
        elif element.name in ['pre', 'code']:
            return f"```\n{element.get_text().strip()}\n```\n"
        else:
            content = ""
            for child in element.children:
                if child.name:
                    content += self._extract_structured_content(child, base_url, level)
                elif isinstance(child, str) and child.strip():
                    content += child.strip() + "\n"
            return content

def format_as_markdown(extracted_content):
    md = f"# {extracted_content['title']}\n\n"
    
    if extracted_content['author']:
        md += f"**Author:** {extracted_content['author']}\n\n"
    
    if extracted_content['date']:
        md += f"**Date:** {extracted_content['date']}\n\n"
    
    md += extracted_content['content']
    
    return md