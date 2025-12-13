import os
import sys
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

def analyze_documents():
    # Load environment variables
    load_dotenv()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        return

    genai.configure(api_key=api_key)

    # Input prompts
    print("--- Gemini Document Analyzer ---")
    
    template_path = input("Enter path to the template file (e.g., template.txt): ").strip()
    if not os.path.exists(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        return

    doc_paths_input = input("Enter paths to document(s) to analyze (comma-separated): ").strip()
    doc_paths = [p.strip() for p in doc_paths_input.split(',')]
    
    valid_docs = []
    for p in doc_paths:
        if os.path.exists(p):
            valid_docs.append(p)
        else:
            print(f"Warning: Document '{p}' not found. Skipping.")
    
    if not valid_docs:
        print("Error: No valid documents provided.")
        return

    output_path = input("Enter path for the output file (e.g., result.txt): ").strip()
    if not output_path:
        print("Error: Output path cannot be empty.")
        return

    # Read content
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template file: {e}")
        return

    docs_content = ""
    for idx, p in enumerate(valid_docs):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                docs_content += f"\n--- Document {idx+1} ({p}) ---\n"
                docs_content += f.read()
                docs_content += "\n"
        except Exception as e:
            print(f"Error reading document '{p}': {e}")
            return

    # Construct Prompt
    prompt = f"""
    You are a helpful assistant that analyzes documents based on a specific template.

    Here is the template you must follow for the output:
    {template_content}

    Here are the documents to analyze:
    {docs_content}

    Please analyze the documents and produce an output that strictly follows the format and structure of the provided template.
    """

    print("\nAnalyzing documents with Gemini...")

    try:
        model = genai.GenerativeModel('gemini-2.5-flash') # Using flash model as requested, mapped to available model
        response = model.generate_content(prompt)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"\nAnalysis complete! Output saved to '{output_path}'.")

    except Exception as e:
        print(f"An error occurred during analysis: {e}")

if __name__ == "__main__":
    analyze_documents()
