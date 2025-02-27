import time
import jwt
import streamlit as st
import asyncio
import requests
import speech_recognition as sr
import re
import pyttsx3
import threading
import google.generativeai as genai
from datetime import datetime
import os

# LiveKit Server Details
LIVEKIT_URL = "wss://voice-chat-em3qvvl2.livekit.cloud"
API_KEY = "APIRiqaMhPvtXyt"
API_SECRET = "lfpveQi875IqUIyleBA0YQKE7Llzjg7MjImkEAk3iTvA"

# Set page configuration
st.set_page_config(
    page_title="Optimus AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Configure Gemini Pro - Use direct API key instead of secrets
GEMINI_API_KEY = "AIzaSyA2GfqpEpwZBmHHbXg07YRKAf1WnalTd0o"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini Pro model
def get_gemini_model():
    try:
        model = genai.GenerativeModel('gemini-pro')
        return model
    except Exception as e:
        st.error(f"Error initializing Gemini Pro: {e}")
        return None

# Black and White custom styling
st.markdown("""
<style>
    body {
        background-color: #000000;
        color: #FFFFFF;
    }
    .stApp {
        background-color: #000000;
    }
    .main-header {
        font-size: 42px;
        font-weight: bold;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 20px;
    }
    .sub-header {
        font-size: 20px;
        color: #CCCCCC;
        text-align: center;
        margin-bottom: 30px;
    }
    .chat-container {
        background-color: #121212;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #333333;
    }
    .model-selector {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        border: 1px solid #333333;
    }
    .voice-settings {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        border: 1px solid #333333;
    }
    .stTextInput > div > div > input {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #333333;
    }
    .stButton > button {
        background-color: #333333;
        color: #FFFFFF;
    }
    .stButton > button:hover {
        background-color: #555555;
    }
    /* Override Streamlit's default colors */
    .css-1d391kg, .css-12oz5g7 {
        background-color: #000000;
    }
    .css-1344mvx, .css-13sdm1b {
        background-color: #121212;
    }
    .stSpinner > div {
        border-top-color: #FFFFFF !important;
    }
    .stAlert {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# Customized headers
st.markdown('<div class="main-header">OPTIMUS AI ASSISTANT</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Your intelligent voice and text companion</div>', unsafe_allow_html=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [("AI", "Welcome to Optimus AI! I can help you with information, assist with tasks, or just chat. How can I assist you today?")]

if 'gemini_chat' not in st.session_state:
    st.session_state.gemini_chat = None

# Model selection sidebar
with st.sidebar:
    st.markdown("## Model Settings")
    
    st.markdown('<div class="model-selector">', unsafe_allow_html=True)
    model_choice = st.radio(
        "Choose AI Model:",
        ["Default API", "Gemini Pro"],
        index=1
    )
    
    temperature = st.slider("Response Creativity", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    
    max_tokens = st.slider("Max Response Length", min_value=50, max_value=2048, value=500, step=50)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("## Voice Settings")
    st.markdown('<div class="voice-settings">', unsafe_allow_html=True)
    voice_enabled = st.checkbox("Enable Voice Response", value=True)
    
    voice_speed = st.slider("Voice Speed", min_value=50, max_value=200, value=120, step=10)
    voice_volume = st.slider("Voice Volume", min_value=0.0, max_value=1.0, value=1.0, step=0.1)
    st.markdown('</div>', unsafe_allow_html=True)

# Add current date and time information
current_time = datetime.now().strftime("%B %d, %Y | %I:%M %p")
st.markdown(f"<div style='text-align: right; color: #AAAAAA; font-size: 14px;'>{current_time}</div>", unsafe_allow_html=True)

# Initialize text-to-speech engine
@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", 120)  
    engine.setProperty("volume", 1.0)
    
    # Set Female Voice if available
    voices = engine.getProperty("voices")
    for voice in voices:
        if "female" in voice.name.lower():
            engine.setProperty("voice", voice.id)
            break
    return engine

engine = get_tts_engine()

# Update TTS engine with sidebar settings
if voice_enabled:
    engine.setProperty("rate", voice_speed)
    engine.setProperty("volume", voice_volume)

# Function to generate LiveKit JWT token
def generate_token(room_name, identity):
    payload = {
        "exp": int(time.time()) + 3600,  # Token valid for 1 hour
        "iss": API_KEY,
        "sub": identity,
        "video": {
            "room": room_name,
            "canPublish": True,
            "canSubscribe": True
        }
    }
    return jwt.encode(payload, API_SECRET, algorithm="HS256")

# Function to get user voice input with noise reduction
def get_voice_input():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300  # Reduce background noise
    recognizer.dynamic_energy_threshold = True  # Adjust sensitivity

    with sr.Microphone() as source:
        status_placeholder = st.empty()
        status_placeholder.info("🎤 Speak now...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            text = recognizer.recognize_google(audio)
            status_placeholder.empty()
            return text
        except sr.UnknownValueError:
            status_placeholder.error("Could not understand your voice. Try speaking clearly.")
            return None
        except sr.RequestError:
            status_placeholder.error("Speech recognition request failed. Check your internet connection.")
            return None

# Function to clean AI response
def clean_response(response):
    response = re.sub(r"[*_]", "", response)
    response = re.sub(r"\s+", " ", response).strip()
    return response

# Function to get response from Gemini Pro
def get_gemini_response(user_input):
    try:
        # Initialize or get existing chat session
        if st.session_state.gemini_chat is None:
            model = get_gemini_model()
            if model:
                st.session_state.gemini_chat = model.start_chat(
                    history=[],
                )
        
        # Get response from Gemini
        if st.session_state.gemini_chat:
            response = st.session_state.gemini_chat.send_message(
                user_input,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        else:
            return "Gemini model is not available. Please try the default API."
    except Exception as e:
        return f"Error with Gemini Pro: {e}"

# Function to get AI response dynamically from original API
def get_default_api_response(user_input):
    try:
        CHATBOT_API_URL = "http://204.12.227.152:8000/chatbot/send_message"

        # Get all URL query parameters dynamically
        query_params = st.query_params
        extracted_params = {"message": user_input}  # Include user message

        # Add conversation context if available
        if len(st.session_state.chat_history) > 0:
            # Create a condensed context from the last 5 exchanges
            context = "\n".join([f"{'User' if role == 'User' else 'Assistant'}: {message}" 
                                for role, message in st.session_state.chat_history[-5:]])
            extracted_params["context"] = context

        # Iterate dynamically over all provided query parameters
        for key, value in query_params.items():
            extracted_params[key] = value[0] if isinstance(value, list) else value  # Handle list values

        # Make the API call
        response = requests.post(CHATBOT_API_URL, headers={"accept": "application/json"}, params=extracted_params)

        if response.status_code == 200:
            response_data = response.json()
            cleaned_response = clean_response(response_data.get("actual_response", "No response received."))
            return cleaned_response
        else:
            return f"Error: Received status code {response.status_code}"
    except Exception as e:
        return f"Error contacting chatbot API: {e}"

# Function to get AI response based on selected model
def get_ai_response(user_input):
    if model_choice == "Gemini Pro":
        return get_gemini_response(user_input)
    else:
        return get_default_api_response(user_input)

# Function to stream AI voice response
def speak_response(response_text):
    # Add to chat history
    st.session_state.chat_history.append(("AI", response_text))
    
    # Speak the response if voice is enabled
    if voice_enabled:
        threading.Thread(target=lambda: engine.say(response_text) or engine.runAndWait()).start()

# Display chat history - Modified for black and white theme
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for role, message in st.session_state.chat_history:
    if role == "User":
        st.markdown(f"<div style='text-align: right;'><span style='background-color: #333333; padding: 8px 12px; border-radius: 15px; display: inline-block;'><b>You:</b> {message}</span></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: left;'><span style='background-color: #1E1E1E; padding: 8px 12px; border-radius: 15px; display: inline-block;'><b>AI:</b> {message}</span></div>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Create a form for user input to avoid session state issues
with st.form(key="message_form", clear_on_submit=True):
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input("Type your message:", key="input_text")
    
    with col2:
        submit_button = st.form_submit_button("Send")
        
# Add speak button outside the form
speak_button = st.button("🎙️ Speak")

# Process form submission
if submit_button and user_input:
    # Add to chat history
    st.session_state.chat_history.append(("User", user_input))
    
    # Get AI response
    with st.spinner("Thinking..."):
        ai_response = get_ai_response(user_input)
        if ai_response:
            speak_response(ai_response)
    
    # Force a rerun to update chat history
    st.experimental_rerun()

# Process user input from voice button
if speak_button:
    voice_text = get_voice_input()
    if voice_text:
        # Display user message
        st.session_state.chat_history.append(("User", voice_text))
        
        # Get and display AI response
        with st.spinner("Thinking..."):
            ai_response = get_ai_response(voice_text)
            if ai_response:
                speak_response(ai_response)
        
        # Force a rerun to update the chat history display
        st.experimental_rerun()

# Add footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888888; font-size: 12px;'>Powered by Optimus AI © 2025 | For assistance contact support@optimusai.com</div>", unsafe_allow_html=True)
