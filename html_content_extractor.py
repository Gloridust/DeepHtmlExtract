import requests
from bs4 import BeautifulSoup
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from urllib.parse import urljoin
import pickle
from dateutil import parser
from datetime import datetime

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

        author = self._extract_author(soup)
        date = self._extract_date(soup)

        main_content = self._extract_main_content(soup, url)

        return {
            'title': title,
            'author': author,
            'date': date,
            'content': main_content
        }

    def _extract_author(self, soup):
        author = soup.find('meta', {'name': 'author'})
        if author:
            return author['content']
        
        # Try to find author in common locations
        author_elements = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and 'author' in x.lower())
        for element in author_elements:
            return element.get_text().strip()
        
        return ""

    def _extract_date(self, soup):
        def parse_and_format_date(date_str):
            try:
                parsed_date = parser.parse(date_str)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                return None

        # Try meta tags first
        date_meta = soup.find('meta', {'property': 'article:published_time'}) or \
                    soup.find('meta', {'name': 'pubdate'}) or \
                    soup.find('meta', {'name': 'date'})
        if date_meta:
            formatted_date = parse_and_format_date(date_meta['content'])
            if formatted_date:
                return formatted_date

        # Look for common date patterns in the text
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',      # YYYY-MM-DD
            r'\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}',  # DD Mon YYYY
        ]

        for pattern in date_patterns:
            date_match = re.search(pattern, soup.get_text())
            if date_match:
                formatted_date = parse_and_format_date(date_match.group())
                if formatted_date:
                    return formatted_date

        # Look for elements with date-related classes or IDs
        date_elements = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and 'date' in x.lower())
        for element in date_elements:
            formatted_date = parse_and_format_date(element.get_text().strip())
            if formatted_date:
                return formatted_date

        return ""

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
        if isinstance(element, str):
            return element.strip() + "\n"
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return f"{'#' * (int(element.name[1]) + level)} {element.get_text().strip()}\n"
        elif element.name == 'p':
            content = element.get_text().strip()
            img = element.find('img')
            if img:
                img_content = self._extract_image(img, base_url)
                content = f"{content}\n\n{img_content}".strip()
            return f"{content}\n\n"
        elif element.name in ['ul', 'ol']:
            content = ""
            for li in element.find_all('li', recursive=False):
                content += f"{'  ' * level}- {li.get_text().strip()}\n"
            return content + "\n"
        elif element.name == 'blockquote':
            return f"> {element.get_text().strip()}\n\n"
        elif element.name == 'img':
            return self._extract_image(element, base_url)
        elif element.name in ['pre', 'code']:
            return f"```\n{element.get_text().strip()}\n```\n\n"
        else:
            content = ""
            for child in element.children:
                content += self._extract_structured_content(child, base_url, level)
            return content

    def _extract_image(self, img, base_url):
        src = img.get('src')
        if src:
            full_url = urljoin(base_url, src)
            alt = img.get('alt', '')
            return f"![{alt}]({full_url})\n\n"
        return ""

def format_as_markdown(extracted_content):
    md = f"# {extracted_content['title']}\n\n"
    
    if extracted_content['author']:
        md += f"**Author:** {extracted_content['author']}\n\n"
    
    if extracted_content['date']:
        md += f"**Date:** {extracted_content['date']}\n\n"
    
    md += extracted_content['content']
    
    return md
