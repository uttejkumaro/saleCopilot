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
                return response.candidates[0].content.parts[0].text.strip()
            else:
                return "🤖 [Bot] Error: No valid response received."

        except Exception as e:
            if "429" in str(e):  # Handle rate limit errors
                if attempt < retries - 1:
                    st.warning(f"⚠️ Rate limit exceeded. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    return "🚨 [Bot] Error: API quota exceeded. Try again later."
            else:
                return f"🚨 [Bot] Error: {str(e)}"

# Function to analyze conversation
def analyze_conversation_and_predict(conversation_history):
    analysis = f"📊 Analysis of last 4 messages: {', '.join(conversation_history[-4:])}"
    
    # Avoid unnecessary API calls if quota is exhausted
    next_response = get_gemini_response(conversation_history)

    if "API quota exceeded" in next_response:
        return analysis, "🚨 API limit reached. Try again later."
    
    return analysis, next_response

# Streamlit Chatbot UI
def main():
    st.title("💼 B2B Chatbot using Gemini")

    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
        
    if "analysis" not in st.session_state:
        st.session_state.analysis = ""
        
    if "next_response" not in st.session_state:
        st.session_state.next_response = ""

    for message in st.session_state.conversation_history:
        role, text = message.split(": ", 1)
        with st.chat_message(role.lower()):
            st.write(text)

    user_input = st.chat_input("💬 Type your message...")

    if user_input:
        st.session_state.conversation_history.append(f"User: {user_input}")

        bot_response = get_gemini_response(st.session_state.conversation_history)
        st.session_state.conversation_history.append(f"Bot: {bot_response}")

        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("bot"):
            st.write(bot_response)

        user_messages = [msg for msg in st.session_state.conversation_history if msg.startswith("User:")]
        if len(user_messages) % 4 == 0:
            st.session_state.analysis, st.session_state.next_response = analyze_conversation_and_predict(st.session_state.conversation_history)

        if st.session_state.analysis:
            st.subheader("📊 Conversation Analysis")
            st.write(st.session_state.analysis)

        if st.session_state.next_response:
            st.subheader("🔮 Predicted Next Response")
            st.write(st.session_state.next_response)

if __name__ == "__main__":
    main()
