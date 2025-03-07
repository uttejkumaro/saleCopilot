import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get Google API Key from environment variables
GOOGLE_API_KEY = os.getenv("AIzaSyA10mrLO4SOHA5kHW5q-aVehnqgizi2974")

# Check if API key exists
if not GOOGLE_API_KEY:
    st.error("🚨 Google API Key is missing! Set it in the .env file.")
    st.stop()

# Configure Google Generative AI
genai.configure(api_key=GOOGLE_API_KEY)

# Function to get response from Gemini
def get_gemini_response(conversation_history):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        prompt = "\n".join(conversation_history)
        response = model.generate_content(prompt)

        # Extract the response text safely
        if response and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            return "🤖 [Bot] Error: No valid response received."
    
    except Exception as e:
        return f"🚨 [Bot] Error: {str(e)}"

# Function to analyze conversation
def analyze_conversation_and_predict(conversation_history):
    if len(conversation_history) < 4:
        return "📊 Not enough messages for analysis.", ""

    analysis = f"📊 Analysis of last 4 messages: {', '.join(conversation_history[-4:])}"

    # Get predicted next response
    next_response = get_gemini_response(conversation_history)

    return analysis, next_response

# Streamlit Chatbot UI
def main():
    st.title("💼 B2B Chatbot using Gemini")

    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
        
    if "analysis" not in st.session_state:
        st.session_state.analysis = ""
        
    if "next_response" not in st.session_state:
        st.session_state.next_response = ""

    # Display chat messages with chat formatting
    for message in st.session_state.conversation_history:
        try:
            # Split the message into role and text
            role, text = message.split(": ", 1)
            with st.chat_message(role.lower()):
                st.write(text)
        except ValueError:
            # Handle cases where the message format is invalid
            with st.chat_message("error"):
                st.write(f"⚠️ Invalid message format: {message}")

    # User input field
    user_input = st.chat_input("💬 Type your message...")

    if user_input:
        # Add user input to history
        st.session_state.conversation_history.append(f"User: {user_input}")

        # Get bot response
        bot_response = get_gemini_response(st.session_state.conversation_history)
        st.session_state.conversation_history.append(f"Bot: {bot_response}")

        # Display user and bot messages
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("bot"):
            st.write(bot_response)

        # Trigger analysis after every 4 user inputs
        user_messages = [msg for msg in st.session_state.conversation_history if msg.startswith("User:")]
        if len(user_messages) % 2 == 0:
            st.session_state.analysis, st.session_state.next_response = analyze_conversation_and_predict(st.session_state.conversation_history)

        # Display analysis & next response (if available)
        if st.session_state.analysis:
            st.subheader("📊 Conversation Analysis")
            st.write(st.session_state.analysis)

        if st.session_state.next_response:
            st.subheader("🔮 Predicted Next Response")
            st.write(st.session_state.next_response)

    # Provide a reset button for the user
    if st.button("Reset Conversation"):
        st.session_state.conversation_history = []
        st.session_state.analysis = ""
        st.session_state.next_response = ""
        st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

if __name__ == "__main__":
    main()