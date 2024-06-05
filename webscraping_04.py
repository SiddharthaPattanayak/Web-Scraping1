import re
import streamlit as st
from bs4 import BeautifulSoup
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from string import punctuation
from heapq import nlargest
import requests

# Function to remove HTML/XML tags
def remove_html_xml_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text()

# Function to remove square brackets and their contents
def remove_square_brackets(text):
    return re.sub(r'\[[^]]*\]', ' ', text)

# Function to preprocess the text
def preprocess_text(text):
    text = remove_html_xml_tags(text)
    text = remove_square_brackets(text)
    text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
    return text.strip()

# Function to summarize the text
def summarize_text(text, ratio=0.4):
    # Load the spaCy model
    nlp = spacy.load('en_core_web_sm')
    
    # Tokenize the text
    doc = nlp(text)
    
    # Create a list of stop words and punctuation
    stop_words = set(STOP_WORDS)
    punctuation_set = set(punctuation)
    
    # Calculate word frequencies
    word_freq = {}
    for token in doc:
        word = token.text.lower()
        if word not in stop_words and word not in punctuation_set:
            if word not in word_freq:
                word_freq[word] = 1
            else:
                word_freq[word] += 1
    
    # Calculate maximum word frequency
    word_max_freq = max(word_freq.values())
    
    # Normalize word frequencies
    for word in word_freq:
        word_freq[word] /= word_max_freq
    
    # Score sentences based on word frequencies
    sentence_scores = {}
    for sent in doc.sents:
        for word in sent:
            if word.text.lower() in word_freq:
                if sent not in sentence_scores:
                    sentence_scores[sent] = word_freq[word.text.lower()]
                else:
                    sentence_scores[sent] += word_freq[word.text.lower()]
    
    # Select top sentences to form the summary
    select_len = int(len(sentence_scores) * ratio)
    summary_sentences = nlargest(select_len, sentence_scores, key=sentence_scores.get)
    
    # Join the sentences to form the final summary
    final_summary = ' '.join([sent.text for sent in summary_sentences])
    
    return final_summary

# Streamlit app layout
st.title("HTML/XML File Summarizer")

# File uploader
uploaded_file = st.file_uploader("Choose an HTML or XML file", type=["html", "xml"])

if uploaded_file is not None:
    # Read the uploaded file
    file_content = uploaded_file.read().decode('utf-8')
    
    # Preprocess the file content
    cleaned_text = preprocess_text(file_content)
    
    # Generate summary
    summary = summarize_text(cleaned_text)
    
    # Display the summary
    st.subheader("Summary")
    st.write(summary)

# URL input box
url = st.text_input("Or enter a URL")

if url:
    try:
        # Fetch content from the URL
        response = requests.get(url)
        if response.status_code == 200:
            page_content = response.text
            
            # Preprocess the page content
            cleaned_text = preprocess_text(page_content)
            
            # Generate summary
            summary = summarize_text(cleaned_text)
            
            # Display the summary
            st.subheader("Summary from URL")
            st.write(summary)
        else:
            st.error("Failed to retrieve the webpage. Please check the URL.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
