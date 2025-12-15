import streamlit as st
import os
import re
from dotenv import load_dotenv
import google.generativeai as genai
import pypdf
import io

# Page Config for Modern Light Mode
st.set_page_config(
    page_title="Gemini Doc Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Force light mode styles */
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }

    /* Force Sidebar Light */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
    }
    [data-testid="stSidebar"] * {
        color: #333333 !important;
    }
    
    /* Modern button styling (Analyze) */
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    div.stButton > button:active {
        color: white !important;
    }

    /* Download Buttons - Make them light/neutral */
    div.stDownloadButton > button {
        background-color: #f1f3f4 !important;
        color: #333333 !important;
        border: 1px solid #dadce0 !important;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px; 
    }
    div.stDownloadButton > button:hover {
        background-color: #e8eaed !important;
        color: #333333 !important;
        border-color: #dadce0 !important;
    }

    /* Card-like containers */
    .css-1r6slb0 {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #2c3e50;
    }
    
    /* File uploader styling tweaks - Force Light */
    [data-testid='stFileUploader'] {
        width: 100%;
    }
    [data-testid='stFileUploader'] section {
        background-color: #f8f9fa !important;
        border: 2px dashed #e0e0e0 !important;
    }
    /* Force ALL text inside the uploader to be dark */
    [data-testid='stFileUploader'] * {
        color: #333333 !important;
    }
    /* The browse button inside uploader - ensure good contrast */
    [data-testid='stFileUploader'] section button {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #ccc !important;
    }
    /* Uploaded file item */
    [data-testid='stFileUploader'] ul li {
        background-color: #ffffff !important;
        color: #333333 !important;
    }
    /* Remove SVG fill if it's white */
    [data-testid='stFileUploader'] svg {
        fill: #333333 !important;
    }
    
    /* Output Code Blocks - Light theme */
    .stCodeBlock {
        background-color: #f8f9fa !important;
    }
    
    /* Ensure inputs have light background */
    .stTextInput input {
        background-color: #ffffff !important;
        color: #333333 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

def read_file_content(uploaded_file):
    """Reads content from an uploaded file (txt, md, or pdf)."""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        else:
            # Assume text based
            return uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {e}")
        return None

def analyze_documents(api_key, instruction_content, docs_contents, is_checklist=False):
    """Analyzes documents using Gemini and returns the response."""
    genai.configure(api_key=api_key)
    
    # Construct Prompt
    combined_docs = ""
    for filename, content in docs_contents.items():
        combined_docs += f"\n--- Document ({filename}) ---\n{content}\n"

    role_instruction = "You are a helpful assistant that analyzes documents."
    if is_checklist:
        role_instruction += " Your goal is to complete the provided checklist based on the documents. Ensure you fill in the 'Company name' field if present."

    prompt = f"""
    {role_instruction}

    Here is the template/checklist you must follow for the output:
    {instruction_content}

    Here are the documents to analyze:
    {combined_docs}

    Please analyze the documents and produce an output that strictly follows the format and structure of the provided template/checklist.
    """
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        return response.text, response.usage_metadata
    except Exception as e:
        return f"Error during analysis: {str(e)}", None

def extract_company_name(text):
    """Extracts company name from the checklist text."""
    # Look for "Company name: [Name]" or similar patterns
    match = re.search(r"Company name:\s*(.+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip().strip("[]") # Remove brackets if Gemini kept them
        return name
    return "Company"

# Sidebar for Configuration
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("Configure your analysis session.")
    
    # API Key Handling
    # Try to load from secrets/env
    if "GOOGLE_API_KEY" in st.secrets:
        system_api_key = st.secrets["GOOGLE_API_KEY"]
    else:
        system_api_key = os.getenv("GOOGLE_API_KEY")

    # API Key Status Indicator
    if system_api_key:
        st.success("✅ System API Key loaded")
    else:
        st.warning("⚠️ No System API Key found")

    # Advanced Settings for manual override
    with st.expander("Advanced: Override API Key"):
        user_api_key = st.text_input(
            "Enter Google API Key", 
            value="", 
            type="password",
            help="Enter your API Key if you wish to override the system key.",
            key="google_api_key_input_v2" 
        )

    if user_api_key:
        api_key = user_api_key
    elif system_api_key:
        api_key = system_api_key
    else:
        api_key = None
    
    st.divider()
    
    # Placeholder for Cost Stats
    stats_container = st.container()
    
    st.info("Upload your template and documents to begin analysis.")

def display_cost_stats(usage_metadata):
    """Displays token usage and estimated cost in the sidebar."""
    if not usage_metadata:
        return

    prompt_count = usage_metadata.prompt_token_count
    candidates_count = usage_metadata.candidates_token_count
    total_count = usage_metadata.total_token_count
    
    # Pricing (Gemini 1.5 Flash estimate)
    # Input: $0.075 / 1M tokens
    # Output: $0.30 / 1M tokens
    input_cost = (prompt_count / 1_000_000) * 0.3
    output_cost = (candidates_count / 1_000_000) * 2.5
    total_cost = input_cost + output_cost
    
    with stats_container:
        st.subheader("📊 Usage Stats")
        st.write(f"**Total Tokens:** {total_count:,}")
        st.caption(f"Input: {prompt_count:,} | Output: {candidates_count:,}")
        st.write(f"**Est. Cost:** ${total_cost:.6f}")
        st.caption("Based on Gemini 2.5 Flash pricing")
        st.divider()

# Main Content Area
st.title("📄 Gemini Document Analyzer")
st.markdown("Use AI to analyze your documents according to a custom template.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Upload Templates")
    template_file = st.file_uploader("Upload Analysis Template (.txt, .pdf)", type=['txt', 'pdf'], key="template")
    checklist_file = st.file_uploader("Upload Checklist (.txt, .pdf)", type=['txt', 'pdf'], key="checklist")
    
    st.subheader("2. Upload Documents")
    doc_files = st.file_uploader("Upload Documents to Analyze", type=['txt', 'md', 'pdf'], accept_multiple_files=True, key="docs")

with col2:
    st.subheader("3. Results")
    analyze_btn = st.button("🚀 Analyze Documents")
    
    if analyze_btn:
        if not api_key:
            st.error("Please provide a Google API Key in the settings sidebar.")
        elif not template_file and not checklist_file:
            st.warning("Please upload at least one template or checklist file.")
        elif not doc_files:
            st.warning("Please upload at least one document.")
        else:
            with st.spinner("Analyzing your documents... this may take a moment."):
                # Read files
                try:
                    docs_contents = {}
                    for doc in doc_files:
                        content = read_file_content(doc)
                        if content:
                            docs_contents[doc.name] = content
                    
                    if not docs_contents:
                        st.error("Could not read any document content.")
                        st.stop()
                    
                    # 1. Process Template Analysis
                    if template_file:
                        template_content = read_file_content(template_file)
                        if template_content:
                            st.info("Generating Analysis Report...")
                            result, usage = analyze_documents(api_key, template_content, docs_contents, is_checklist=False)
                            
                            display_cost_stats(usage)
                            
                            st.success("✅ Analysis Report Ready")
                            st.subheader("Analysis Output")
                            st.code(result, language=None) # Using st.code for one-click copy
                            st.download_button(
                                label="📥 Download Analysis Report",
                                data=result,
                                file_name="analysis_result.txt",
                                mime="text/plain",
                                key="dl_analysis"
                            )
                        else:
                            st.error("Could not read template content.")

                    # 2. Process Checklist
                    if checklist_file:
                        checklist_content = read_file_content(checklist_file)
                        if checklist_content:
                            st.info("Processing Checklist...")
                            checklist_result, usage = analyze_documents(api_key, checklist_content, docs_contents, is_checklist=True)
                            
                            display_cost_stats(usage)
                            
                            # Extract company name for filename
                            company_name = extract_company_name(checklist_result)
                            safe_company_name = "".join([c for c in company_name if c.isalnum() or c in (' ', '-', '_')]).strip()
                            safe_company_name = safe_company_name.replace(" ", "_")
                            filename = f"checklist_{safe_company_name}.txt"
                            
                            st.success(f"✅ Checklist Ready ({company_name})")
                            st.subheader("Checklist Output")
                            st.code(checklist_result, language=None) # Using st.code for one-click copy
                            st.download_button(
                                label=f"📥 Download Checklist ({filename})",
                                data=checklist_result,
                                file_name=filename,
                                mime="text/plain",
                                key="dl_checklist"
                            )
                        else:
                            st.error("Could not read checklist content.")
                            
                except Exception as e:
                    st.error(f"An error occurred reading the files: {e}")

if not analyze_btn and not template_file and not checklist_file and not doc_files:
    # Empty state placeholder
    with col2:
        st.info("Results will appear here after analysis.")

