import requests
from bs4 import BeautifulSoup
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from urllib.parse import urljoin
import random

class HTMLContentExtractor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.classifier = MultinomialNB()

    def train(self, training_data):
        X = self.vectorizer.fit_transform([item['text'] for item in training_data])
        y = [item['label'] for item in training_data]
        self.classifier.fit(X, y)

    def extract_content(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title = soup.title.string if soup.title else ""

        # Extract author (this is a simplified approach and may need to be adjusted)
        author = soup.find('meta', {'name': 'author'})
        author = author['content'] if author else ""

        # Extract date (this is a simplified approach and may need to be adjusted)
        date = soup.find('meta', {'property': 'article:published_time'})
        date = date['content'] if date else ""

        # Extract main content
        main_content = self._extract_main_content(soup)

        # Extract images
        images = self._extract_images(soup, url)

        return {
            'title': title,
            'author': author,
            'date': date,
            'content': main_content,
            'images': images
        }

    def _extract_main_content(self, soup):
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text from all remaining elements
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Classify each paragraph
        paragraphs = text.split('\n')
        X = self.vectorizer.transform(paragraphs)
        labels = self.classifier.predict(X)

        # Keep only the paragraphs classified as main content
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

def generate_training_data(num_samples=100):
    main_content_patterns = [
        "This is the main content of the article. It contains important information.",
        "The article discusses various aspects of the topic in detail.",
        "Key points are elaborated in this section of the text.",
        "The author presents their arguments and supporting evidence here."
    ]

    not_main_content_patterns = [
        "This is a comment left by a reader.",
        "Advertisement: Buy our products now!",
        "Related articles you might be interested in:",
        "Footer: Copyright 2024. All rights reserved."
    ]

    training_data = []

    for _ in range(num_samples):
        if random.random() < 0.7:  # 70% main content
            text = random.choice(main_content_patterns)
            label = 'main_content'
        else:
            text = random.choice(not_main_content_patterns)
            label = 'not_main_content'
        
        training_data.append({'text': text, 'label': label})

    return training_data

# Usage example
if __name__ == "__main__":
    # Generate training data
    training_data = generate_training_data(200)  # Generate 200 samples

    # Initialize and train the extractor
    extractor = HTMLContentExtractor()
    extractor.train(training_data)

    # Example URL (replace with a real article URL)
    url = "https://example.com/article"

    try:
        # Extract content from the URL
        extracted_content = extractor.extract_content(url)

        # Format the extracted content as Markdown
        markdown_content = format_as_markdown(extracted_content)

        print(markdown_content)
    except Exception as e:
        print(f"An error occurred: {e}")