from html_content_extractor import HTMLContentExtractor, format_as_markdown

if __name__ == "__main__":
    # Initialize the extractor and load the trained model
    extractor = HTMLContentExtractor()
    extractor.load_model('vectorizer.pkl', 'classifier.pkl')

    # Example URL (replace with a real article URL)
    url = "https://gloridust.xyz/blog/2024-06-29-overseas-bank-card-wise+ocbc"

    try:
        # Extract content from the URL
        extracted_content = extractor.extract_content(url)

        # Format the extracted content as Markdown
        markdown_content = format_as_markdown(extracted_content)

        print(markdown_content)
    except Exception as e:
        print(f"An error occurred: {e}")