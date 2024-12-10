import streamlit as st
import sqlite3
import logging
from memrag import (
    search_across_chunks,
    add_image_path_column,  # Ensure you import this function
)

def initialize_db(db_path='memoirs.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create memoirs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoirs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT
        )
    ''')

    # Create memoir chunks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoir_chunks (
            id INTEGER PRIMARY KEY,
            memoir_id INTEGER,
            content TEXT,
            system_prompt TEXT,
            image_path TEXT,  -- Add the image_path column directly here
            FOREIGN KEY (memoir_id) REFERENCES memoirs (id)
        )
    ''')

    # Create an FTS table for fast full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS memoir_chunks_fts
        USING fts5(content, chunk_id UNINDEXED, memoir_id UNINDEXED)
    ''')

    # Ensure image_path column is present
    add_image_path_column(conn)

    conn.commit()
    return conn

def load_memoir_from_db(conn, memoir_id):
    """Load memoir content and associated images from the database."""
    cursor = conn.cursor()

    # Fetch memoir details (content, image_path, and author)
    cursor.execute('''
        SELECT memoirs.author, memoir_chunks.content, memoir_chunks.image_path
        FROM memoirs
        JOIN memoir_chunks ON memoir_chunks.memoir_id = memoirs.id
        WHERE memoirs.id = ?
    ''', (memoir_id,))
    memoir_data = cursor.fetchall()

    return memoir_data

def display_memoir_content(memoir_data):
    """Display memoir chunks and associated images in Streamlit."""
    for author, chunk, image_path in memoir_data:
        if image_path:
            st.image(image_path, caption="Monster API generated memoir chapter image", use_container_width=True)  # Display associated image
            st.write(chunk)  # Display text content of memoir chunk

def handle_user_question(conn, user_input, memoir_id, author):
    """Handle user input, search across memoir chunks, and return relevant content."""
    # Get the response from the RAG system (search across chunks)
    response = search_across_chunks(conn, user_input, memoir_id, author)
    return response

def main():
    st.title("Memoir Interactive QA")

    # Initialize the database and load memoirs
    conn = initialize_db()
    memoir_id = 1  # Modify this as per the memoir ID you want to interact with
    
    # Load memoir content and display it
    memoir_data = load_memoir_from_db(conn, memoir_id)
    display_memoir_content(memoir_data)

    # Extract the author for use in search
    author = memoir_data[0][0] if memoir_data else None

    # User input for Q&A
    user_input = st.text_input("Ask a question about the memoir:")

    if user_input and author:
        # Get the answer from the system (using the RAG system)
        response = handle_user_question(conn, user_input, memoir_id, author)
        st.write(f"**Answer:** {response}")

if __name__ == "__main__":
    main()
