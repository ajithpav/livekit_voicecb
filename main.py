import streamlit as st
import openai
import pinecone
import PyPDF2
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Set API Keys
# OPENAI_API_KEY = "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"
# PINECONE_API_KEY = "pcsk_4SfNW3_UsE4Nq5hX6bXT7dAqdm5G5sJZhxTy6j6H6SET3ARJUqxAnjijYhf2iGWhvNRRHU"
# PINECONE_ENVIRONMENT = "us-east-1"
# PINECONE_INDEX_NAME = "chatbot"

# Initialize OpenAI embeddings
openai.api_key = OPENAI_API_KEY
embedding_model = OpenAIEmbeddings()

# Initialize Pinecone
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
index = pinecone.Index(PINECONE_INDEX_NAME)

# Streamlit UI
st.title("📄 Chat with PDF using LLM + Pinecone")
st.sidebar.header("Upload a PDF")

# Upload PDF
pdf_file = st.sidebar.file_uploader("Upload your PDF", type=["pdf"])

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file."""
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

if pdf_file:
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(pdf_file)
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    text_chunks = text_splitter.split_text(pdf_text)
    
    # Generate embeddings and store in Pinecone
    embeddings = [embedding_model.embed_query(chunk) for chunk in text_chunks]
    vectors_to_upsert = [(f"chunk-{i}", embeddings[i], {"text": text_chunks[i]}) for i in range(len(text_chunks))]
    index.upsert(vectors=vectors_to_upsert)

    st.sidebar.success("PDF Uploaded & Processed! ✅")

# Chat interface
st.subheader("💬 Ask Questions about the PDF")
user_input = st.text_input("Enter your question:")

def get_response(query):
    """Search for the most relevant answer in Pinecone."""
    query_embedding = embedding_model.embed_query(query)
    search_results = index.query(vector=query_embedding, top_k=2, include_metadata=True)
    
    if search_results["matches"]:
        return search_results["matches"][0]["metadata"]["text"]
    else:
        return "Sorry, no relevant information found."

if user_input:
    response = get_response(user_input)
    st.write(f"🧠 AI Response: {response}")
