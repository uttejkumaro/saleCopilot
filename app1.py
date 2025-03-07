

import os
import time
import streamlit as st
import google.generativeai as genai

# Get API Key from Streamlit Secrets (Cloud Deployment)
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("🚨 Google API Key is missing! Set it in Streamlit Secrets.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# Function to get response from Gemini with Retry for 429 errors
def get_gemini_response(conversation_history, retries=3, delay=5):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = "\n".join(conversation_history)

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)

            if response and response.candidates:
                return response.candidates[0].content.parts[0].text.strip()[:150]  # Shorten the response

            else:
                return "🤖 [Bot] Oops, something went wrong."

        except Exception as e:
            if "429" in str(e):  # Handle rate limit errors
                if attempt < retries - 1:
                    st.warning(f"⚠ Rate limit exceeded. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    return "🚨 [Bot] Error: API limit exceeded. Try again later."
            else:
                return f"🚨 [Bot] Error: {str(e)}"

# Function to analyze conversation and predict the next response
def analyze_conversation_and_predict(conversation_history):
    analysis = f"📊 Analysis of the last few messages: {', '.join(conversation_history[-4:])}"
    
    # Avoid unnecessary API calls if quota is exhausted
    next_response = get_gemini_response(conversation_history)

    if "API limit exceeded" in next_response:
        return analysis, "🚨 API limit reached. Try again later."
    
    return analysis, next_response

# Streamlit Chatbot UI
def main():
    st.title("💼 SY-PI")

    # Set up session state to manage conversation
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
        
    if "analysis" not in st.session_state:
        st.session_state.analysis = ""
        
    if "next_response" not in st.session_state:
        st.session_state.next_response = ""

    # Layout with two columns for better separation of analysis and conversation
    col1, col2 = st.columns([2, 5])

    with col1:
        # Display analysis and predictions if available
        if st.session_state.analysis:
            st.subheader("📊 Conversation Analysis")
            st.write(st.session_state.analysis)

        if st.session_state.next_response:
            st.subheader("🔮 Predicted Next Response")
            st.write(st.session_state.next_response)

    with col2:
        # Show conversation history
        for message in st.session_state.conversation_history:
            role, text = message.split(": ", 1)
            with st.chat_message(role.lower()):
                st.write(text)

        # User input for chat
        user_input = st.chat_input("💬 Type your message...")

        if user_input:
            # Add user message to history
            st.session_state.conversation_history.append(f"User: {user_input}")

            # Get bot response
            bot_response = get_gemini_response(st.session_state.conversation_history)
            st.session_state.conversation_history.append(f"Bot: {bot_response}")

            # Show user and bot messages in chat UI
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("bot"):
                st.write(bot_response)

            # Perform analysis and prediction after every second exchange
            user_messages = [msg for msg in st.session_state.conversation_history if msg.startswith("User:")]
            if len(user_messages) % 2 == 0:
                st.session_state.analysis, st.session_state.next_response = analyze_conversation_and_predict(st.session_state.conversation_history)

if __name__ == "__main__":

    main()
