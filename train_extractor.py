import json
from html_content_extractor import HTMLContentExtractor

def load_training_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    # Load training data
    training_data = load_training_data('training_data.json')

    # Initialize and train the extractor
    extractor = HTMLContentExtractor()
    extractor.train(training_data)

    # Save the trained model
    extractor.save_model('vectorizer.pkl', 'classifier.pkl')

    print("Model trained and saved successfully.")