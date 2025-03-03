import time
import jwt
import streamlit as st
import requests
import speech_recognition as sr
import re
import pyttsx3
import threading
import google.generativeai as genai
from datetime import datetime, timedelta
import os

# LiveKit Server Details
LIVEKIT_URL = "wss://voice-chat-em3qvvl2.livekit.cloud"
API_KEY = "APIRiqaMhPvtXyt"
API_SECRET = "lfpveQi875IqUIyleBA0YQKE7Llzjg7MjImkEAk3iTvA"

# Set page configuration
st.set_page_config(
    page_title="Optimus AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Gemini Pro
GEMINI_API_KEY = "AIzaSyA2GfqpEpwZBmHHbXg07YRKAf1WnalTd0o"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini Pro model
def get_gemini_model():
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')  # Updated to a valid model
        return model
    except Exception as e:
        st.error(f"Error initializing Gemini Pro: {e}")
        return None

# Initialize session state for theme
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Default to dark mode for better UI

# Dark/Light Mode Toggle
with st.sidebar:
    theme_toggle = st.toggle("Dark Mode", value=st.session_state.dark_mode)
    if theme_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = theme_toggle
        st.rerun()

# Professional modern styling with enhanced theme support
def get_theme_css():
    if st.session_state.dark_mode:
        return """
        /* Dark Theme - More Elegant and Professional */
        :root {
            --primary: #4eca8b;
            --primary-light: #6edba3;
            --secondary: #1a1a1a;
            --text-light: #f8f8f8;
            --text-dark: #1a1a1a;
            --accent: #4eca8b;
            --bg-darker: #121212;
            --bg-dark: #1e1e1e;
            --bg-light: #282828;
            --border: #2d2d2d;
            --shadow: rgba(0, 0, 0, 0.4);
        }
        
        /* Global styles */
        body {
            background-color: var(--bg-darker);
            color: var(--text-light);
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .stApp {
            background-color: var(--bg-darker);
        }
        """
    else:
        return """
        /* Light Theme - White with Premium Green */
        :root {
            --primary: #3cb371;
            --primary-light: #5cd68d;
            --secondary: #333333;
            --text-light: #ffffff;
            --text-dark: #333333;
            --accent: #4eca8b;
            --bg-darker: #ffffff;
            --bg-dark: #f8f8f8;
            --bg-light: #f0f0f0;
            --border: #e0e0e0;
            --shadow: rgba(0, 0, 0, 0.1);
        }
        
        /* Global styles */
        body {
            background-color: var(--bg-darker);
            color: var(--text-dark);
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        .stApp {
            background-color: var(--bg-darker);
        }
        """

# Complete styling with theme variables
st.markdown(f"""
<style>
    {get_theme_css()}
    
    /* Header styling - Enhanced with better spacing and visual hierarchy */
    .main-header {{
        font-size: 42px;
        font-weight: 800;
        color: var(--primary);
        text-align: center;
        margin-bottom: 5px;
        letter-spacing: -0.5px;
        text-shadow: 0 2px 4px var(--shadow);
    }}
    .sub-header {{
        font-size: 18px;
        color: var(--secondary);
        text-align: center;
        margin-bottom: 25px;
        font-weight: 400;
        opacity: 0.9;
    }}
    
    /* Chat container - More polished with better interactions */
    .chat-container {{
        background-color: var(--bg-dark);
        padding: 25px;
        border-radius: 16px;
        margin-bottom: 20px;
        max-height: 550px;
        overflow-y: auto;
        border: 1px solid var(--border);
        box-shadow: 0 8px 24px var(--shadow);
        transition: all 0.3s ease;
    }}
    .chat-container:hover {{
        box-shadow: 0 10px 28px var(--shadow);
    }}
    
    /* Messages styling - Improved with better animations and polish */
    .user-message {{
        text-align: right;
        margin-bottom: 16px;
        animation: fadeIn 0.3s ease;
    }}
    .user-bubble {{
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 2px 20px;
        display: inline-block;
        max-width: 80%;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
        word-wrap: break-word;
        font-size: 15px;
        line-height: 1.5;
        transition: all 0.2s ease;
    }}
    .user-bubble:hover {{
        box-shadow: 0 5px 12px rgba(0, 0, 0, 0.2);
    }}
    .ai-message {{
        text-align: left;
        margin-bottom: 16px;
        animation: fadeIn 0.3s ease;
    }}
    .ai-bubble {{
        background-color: var(--bg-light);
        color: var(--text-light);
        padding: 12px 18px;
        border-radius: 20px 20px 20px 2px;
        display: inline-block;
        max-width: 80%;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
        word-wrap: break-word;
        font-size: 15px;
        line-height: 1.5;
        transition: all 0.2s ease;
    }}
    .ai-bubble:hover {{
        box-shadow: 0 5px 12px rgba(0, 0, 0, 0.2);
    }}
    
    /* Input area - More modern with better interactions */
    .input-area {{
        background-color: var(--bg-dark);
        padding: 20px;
        border-radius: 16px;
        margin-top: 15px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 16px var(--shadow);
        transition: all 0.3s ease;
    }}
    .input-area:hover {{
        box-shadow: 0 6px 20px var(--shadow);
    }}
    .stTextInput > div > div > input {{
        background-color: var(--bg-light);
        color: var(--text-light);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(76, 202, 139, 0.2);
    }}
    .stButton > button {{
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(60, 179, 113, 0.25);
    }}
    .stButton > button:hover {{
        background: linear-gradient(135deg, var(--primary-light), var(--primary));
        box-shadow: 0 6px 16px rgba(60, 179, 113, 0.35);
        transform: translateY(-2px);
    }}
    
    /* Sidebar styling */
    .css-1d391kg, .css-12oz5g7 {{
        background-color: var(--bg-dark);
    }}
    .sidebar-header {{
        font-size: 22px;
        font-weight: 700;
        color: var(--primary);
        margin-bottom: 18px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 12px;
    }}
    .setting-panel {{
        background-color: var(--bg-light);
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 24px;
        border: 1px solid var(--border);
        box-shadow: 0 4px 12px var(--shadow);
        transition: all 0.3s ease;
    }}
    .setting-panel:hover {{
        box-shadow: 0 6px 16px var(--shadow);
    }}
    
    /* Spinner and alerts - More polished and on-brand */
    .stSpinner > div {{
        border-top-color: var(--primary) !important;
    }}
    .stAlert {{
        background-color: var(--bg-light);
        color: var(--text-light);
        border-left-color: var(--primary);
        border-radius: 10px;
    }}
    
    /* Status indicator - More dynamic and professional */
    .status-indicator {{
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        background-color: var(--primary);
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0% {{ opacity: 0.6; transform: scale(0.95); }}
        50% {{ opacity: 1; transform: scale(1.05); }}
        100% {{ opacity: 0.6; transform: scale(0.95); }}
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .status-text {{
        font-size: 14px;
        color: var(--secondary);
        font-weight: 500;
    }}
    
    /* Time badges - More elegant */
    .timestamp {{
        font-size: 11px;
        color: var(--secondary);
        margin: 5px 10px;
        display: block;
        opacity: 0.8;
    }}
    
    /* Footer styling */
    .footer {{
        text-align: center;
        padding: 20px 0;
        color: var(--secondary);
        font-size: 13px;
        border-top: 1px solid var(--border);
        margin-top: 30px;
    }}
    
    /* Sliders and controls - More on-brand and polished */
    .stSlider div[data-baseweb="slider"] div {{
        background-color: var(--border) !important;
    }}
    .stSlider div[data-baseweb="slider"] div[role="progressbar"] {{
        background-color: var(--primary) !important;
    }}
    .stSlider div[data-baseweb="slider"] div[data-baseweb="thumb"] {{
        background-color: var(--primary) !important;
    }}
    .stCheckbox label span[role="checkbox"] {{
        background-color: var(--bg-light) !important;
        border-color: var(--border) !important;
    }}
    .stCheckbox label span[aria-checked="true"] {{
        background-color: var(--primary) !important;
        border-color: var(--primary) !important;
    }}
    
    /* Make checkboxes and toggles more professional */
    button[kind="switchButton"] div[data-baseweb="switch"] {{
        background-color: var(--primary) !important;
    }}
</style>
""", unsafe_allow_html=True)

# Professional headers with enhanced logo
logo_color = "#3cb371" if not st.session_state.dark_mode else "#5cd68d"
st.markdown(f'''
<div style="display: flex; align-items: center; justify-content: center; margin-bottom: 30px;">
    <svg width="60" height="60" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="90" fill="{logo_color}" />
        <path d="M55 75 L145 75 L145 135 C145 150 130 165 100 165 C70 165 55 150 55 135 Z" fill="{('#ffffff' if not st.session_state.dark_mode else '#121212')}" />
        <circle cx="80" cy="105" r="10" fill="{logo_color}" />
        <circle cx="120" cy="105" r="10" fill="{logo_color}" />
        <path d="M75 130 C75 140 125 140 125 130" stroke="{logo_color}" stroke-width="5" fill="none" />
    </svg>
    <div style="margin-left: 15px;">
        <div class="main-header">OPTIMUS AI ASSISTANT</div>
        <div class="sub-header">Enterprise-Grade Intelligent Voice & Text Companion</div>
    </div>
</div>
''', unsafe_allow_html=True)

# Live status indicator
st.markdown('''
<div style="text-align: right; margin-bottom: 15px;">
    <span class="status-indicator"></span>
    <span class="status-text">Live & Ready</span>
    <span style="margin-left: 15px; font-weight: 500;">''' + datetime.now().strftime("%B %d, %Y | %I:%M %p") + '''</span>
</div>
''', unsafe_allow_html=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [("AI", "Welcome to Optimus AI! I'm your dedicated AI assistant for all your needs. How may I help you today?")]

if 'gemini_chat' not in st.session_state:
    st.session_state.gemini_chat = None

# Initialize voice conversation state
if 'voice_conversation_active' not in st.session_state:
    st.session_state.voice_conversation_active = False

# Model selection sidebar - Enhanced UI
with st.sidebar:
    st.markdown('<div class="sidebar-header">Assistant Configuration</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="setting-panel">', unsafe_allow_html=True)
    st.markdown("#### AI Engine")
    model_choice = st.radio(
        "Select AI Provider:",
        ["Enterprise API", "Gemini Pro"],
        index=1,
        help="Choose the AI model that powers your assistant"
    )
    
    st.markdown("#### Intelligence Settings")
    temperature = st.slider(
        "Creativity Level", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.1,
        help="Higher values make responses more creative, lower values make them more precise"
    )
    
    max_tokens = st.slider(
        "Response Length", 
        min_value=100, 
        max_value=2048, 
        value=800, 
        step=50,
        help="Maximum length of AI responses"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="setting-panel">', unsafe_allow_html=True)
    st.markdown("#### Voice Configuration")
    voice_enabled = st.checkbox(
        "Enable Voice Response", 
        value=True,
        key="voice_enabled_checkbox",
        help="Turn on/off AI voice responses"
    )
    
    voice_speed = st.slider(
        "Speech Rate", 
        min_value=80, 
        max_value=200, 
        value=140, 
        step=5,
        help="Control how fast the AI speaks"
    )
    
    voice_volume = st.slider(
        "Voice Volume", 
        min_value=0.1, 
        max_value=1.0, 
        value=1.0, 
        step=0.1,
        help="Adjust the volume of voice responses"
    )
    
    # Voice chat mode in the voice configuration panel
    st.markdown("#### Voice Chat Mode")
    continuous_voice = st.checkbox(
        "Continuous Voice Conversation", 
        value=False,
        key="continuous_voice_checkbox",
        help="Enable continuous voice conversation where the assistant listens after each response"
    )
    
    if continuous_voice:
        st.info("Voice conversation mode is ON. Click 'Speak' to start a continuous voice chat. Say 'exit' to end.")
        # Auto-start voice mode if checkbox is enabled
        if not st.session_state.voice_conversation_active:
            st.session_state.voice_conversation_active = True
            st.rerun()
    else:
        # Turn off voice conversation if checkbox is disabled
        if st.session_state.voice_conversation_active:
            st.session_state.voice_conversation_active = False
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add client branding section
    st.markdown('<div class="setting-panel">', unsafe_allow_html=True)
    st.markdown("#### Client Branding")
    client_logo = st.file_uploader(
        "Upload Client Logo", 
        type=['png', 'jpg', 'jpeg'],
        help="Add your client's logo to customize the interface"
    )
    client_name = st.text_input(
        "Client Organization",
        placeholder="Enter client name",
        help="Display your client's organization name"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Initialize text-to-speech engine
@st.cache_resource
def get_tts_engine():
    engine = pyttsx3.init()
    engine.setProperty("rate", 140)  
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
        status_placeholder.info("🎤 Listening to your voice...")
        
        try:
            # Add a short pause to let the recognizer adjust to ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            status_placeholder.info("🔍 Processing your speech...")
            
            text = recognizer.recognize_google(audio)
            status_placeholder.empty()
            return text
        except sr.UnknownValueError:
            status_placeholder.error("⚠️ Could not understand audio. Please speak clearly and try again.")
            time.sleep(2)  # Show the error for 2 seconds
            status_placeholder.empty()
            return None
        except sr.RequestError:
            status_placeholder.error("⚠️ Speech recognition service unavailable. Check your internet connection.")
            time.sleep(2)
            status_placeholder.empty()
            return None
        except Exception as e:
            status_placeholder.error(f"⚠️ Error: {str(e)}")
            time.sleep(2)
            status_placeholder.empty()
            return None

# Function to clean AI response
def clean_response(response):
    # Remove markdown formatting that might interfere with speech
    response = re.sub(r"[*_#]", "", response)
    response = re.sub(r"\s+", " ", response).strip()
    return response

# Function to get response from Gemini Pro with error handling
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
            # Add robust error handling and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = st.session_state.gemini_chat.send_message(
                        user_input,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                    )
                    return response.text
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retrying
                        continue
                    else:
                        raise e
            
            return "I apologize, but I'm having trouble connecting to my knowledge base. Please try again in a moment."
        else:
            return "Gemini model is not available. Please try the Enterprise API instead."
    except Exception as e:
        error_message = str(e)
        if "Rate limit" in error_message:
            return "I've reached my rate limit. Please wait a moment before asking another question."
        else:
            return f"I encountered an issue processing your request. Technical details: {error_message}"

# Function to get AI response from the default API with improved error handling
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

        # Add client identifier if available
        if client_name:
            extracted_params["client_name"] = client_name

        # Iterate dynamically over all provided query parameters
        for key, value in query_params.items():
            extracted_params[key] = value[0] if isinstance(value, list) else value  # Handle list values

        # Set timeout for the request
        timeout_seconds = 10
        
        # Make the API call with timeout
        response = requests.post(
            CHATBOT_API_URL, 
            headers={"accept": "application/json"}, 
            params=extracted_params,
            timeout=timeout_seconds
        )

        if response.status_code == 200:
            response_data = response.json()
            cleaned_response = clean_response(response_data.get("actual_response", "No response received."))
            return cleaned_response
        else:
            return f"I apologize, but I encountered a service error (code {response.status_code}). Please try again."
    except requests.exceptions.Timeout:
        return "The request timed out. Our servers might be experiencing high traffic. Please try again in a moment."
    except requests.exceptions.ConnectionError:
        return "I'm having trouble connecting to my knowledge base. Please check your internet connection and try again."
    except Exception as e:
        return f"I encountered an unexpected issue. Technical details: {str(e)}"

# Function to get AI response based on selected model
def get_ai_response(user_input):
    if model_choice == "Gemini Pro":
        return get_gemini_response(user_input)
    else:
        return get_default_api_response(user_input)

# Function to speak AI response - FIXED version
def speak_response(response_text):
    # Add to chat history
    st.session_state.chat_history.append(("AI", response_text))
    
    # Speak the response if voice is enabled
    if voice_enabled:
        # Clean the response for better speech
        cleaned_text = clean_response(response_text)
        
        # Create a secondary thread to handle speech
        def speak_text():
            try:
                engine.say(cleaned_text)
                engine.runAndWait()
            except Exception as e:
                st.error(f"Speech error: {str(e)}")
        
        speech_thread = threading.Thread(target=speak_text)
        speech_thread.daemon = True  # Allow thread to terminate when main program exits
        speech_thread.start()
        
        # Return whether speech was initiated successfully
        return True
    return False

# Voice conversation mode function - FIXED version
def voice_conversation_mode():
    # Get the current state of voice conversation
    is_active = st.session_state.voice_conversation_active
    
    status_placeholder = st.empty()
    
    # Start or continue voice conversation
    if is_active:
        status_placeholder.info("🎤 Listening... Say 'exit' or 'stop' to end voice chat.")
        
        # Get voice input
        voice_text = get_voice_input()
        
        # Check if user wants to exit voice mode
        if voice_text and any(exit_word in voice_text.lower() for exit_word in ["exit", "stop", "quit", "end"]):
            st.session_state.voice_conversation_active = False
            status_placeholder.success("Voice conversation ended.")
            time.sleep(1.5)
            status_placeholder.empty()
            return
        
        # Process valid voice input
        if voice_text:
            # Display user message
            st.session_state.chat_history.append(("User", voice_text))
            status_placeholder.info("🧠 Thinking...")
            
            # Get and display AI response
            ai_response = get_ai_response(voice_text)
            if ai_response:
                status_placeholder.info("🔊 Speaking...")
                speak_complete = speak_response(ai_response)
                
                # Wait for speech to complete before continuing
                time.sleep(len(clean_response(ai_response).split()) * 0.15)  # Rough estimate of speech duration
                
                # Continue voice conversation automatically
                status_placeholder.empty()
                st.rerun()
        else:
            # Handle no valid voice input
            status_placeholder.warning("I didn't catch that. Please try again or say 'exit' to stop.")
            time.sleep(2)
            status_placeholder.empty()
            if st.session_state.voice_conversation_active:
                st.rerun()

# Display chat history with enhanced UI
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for i, (role, message) in enumerate(st.session_state.chat_history):
    # Calculate a fake timestamp - fixed the timedelta issue
    time_offset = len(st.session_state.chat_history) - i
    message_time = (datetime.now() - timedelta(minutes=time_offset)).strftime("%I:%M %p")
    
    if role == "User":
        st.markdown(f"""
        <div class="user-message">
            <div class="user-bubble">{message}</div>
            <span class="timestamp">{message_time}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="ai-message">
            <div class="ai-bubble">{message}</div>
            <span class="timestamp">{message_time}</span>
        </div>
        """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Create a more professional input area
st.markdown('<div class="input-area">', unsafe_allow_html=True)
col1, col2, col3 = st.columns([6, 1, 1])

with col1:
    user_input = st.text_input("", placeholder="Type your message here...", key="input_text")

with col2:
    speak_button = st.button("🎙️ Speak", key="speak_button")

with col3:
    send_button = st.button("Send", key="send_button")
st.markdown('</div>', unsafe_allow_html=True)

# Process user input
if send_button and user_input:
    # Add to chat history
    st.session_state.chat_history.append(("User", user_input))
    
    # Get AI response
    with st.spinner("Processing your request..."):
        ai_response = get_ai_response(user_input)
        if ai_response:
            speak_response(ai_response)
    
    # Force a rerun to update chat history
    st.rerun()

# Process user input from speak button
if speak_button:
    # If continuous mode is off, just do a single voice interaction
    if not st.session_state.voice_conversation_active:
        voice_text = get_voice_input()
        if voice_text:
            # Display user message
            st.session_state.chat_history.append(("User", voice_text))
