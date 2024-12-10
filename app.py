import streamlit as st
import sqlite3
import os
from PIL import Image

# Initialize database connection
def get_db_connection():
    db_path = 'memoirs.db'
    conn = sqlite3.connect(db_path)
    return conn

# Load data from the database
def load_memoir_chunks(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT image_path, content FROM memoir_chunks
    ''')
    return cursor.fetchall()

# Function to interact with the LLM
def query_llm(author, question, title):
    import groq
    groq_client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
    system_prompt = f"You are an assistant summarizing a memoir by {author}. Answer the user's question based on the text from the memoir '{title}'."
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question},
        ],
        model="llama3-8b-8192",
    )
    return chat_completion.choices[0].message.content

# Streamlit App Layout
st.title("Memoir Interactive QA")

# Display loaded memoir chunks
conn = get_db_connection()
memoir_chunks = load_memoir_chunks(conn)

st.subheader("Memoir Chapters")
for image_path, content in memoir_chunks:
    if image_path:
        image = Image.open(image_path)
        st.image(image, use_container_width=True)
    st.write(content)

# Interactive QA section
st.subheader("Ask Questions About the Memoir")
author = "Alan Plush"
title = "Alan Test"
question = st.text_input("Enter your question:")

if st.button("Get Answer"):
    if question:
        response = query_llm(author, question, title)
        st.text_area("LLM Response:", response, height=200)
    else:
        st.error("Please enter a question.")

# Close the database connection
conn.close()
