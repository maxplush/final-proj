import sqlite3
import streamlit as st
from memoir_rag import search_across_chunks

def load_memoir_from_db(conn, memoir_id):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT memoirs.author, memoir_chunks.content, memoir_chunks.image_path
        FROM memoirs
        JOIN memoir_chunks ON memoir_chunks.memoir_id = memoirs.id
        WHERE memoirs.id = ?
    ''', (memoir_id,))
    return cursor.fetchall()

def display_memoir_content(memoir_data):
    for author, chunk, image_path in memoir_data:
        if image_path:
                st.image(
                image_path,
                caption="MonsterGPT - Memoir Chapter Image",
                use_container_width=True
            )
        st.write(chunk)

def handle_user_question(conn, user_input, memoir_id, author):
    return search_across_chunks(conn, user_input, memoir_id, author)

def main():
    st.title("Memoir Interactive QA")
    conn = sqlite3.connect('memoirs.db')
    memoir_id = 1 # Modify per the memoir ID you want to interact with
    memoir_data = load_memoir_from_db(conn, memoir_id)
    display_memoir_content(memoir_data)
    author = memoir_data[0][0] if memoir_data else None
    user_input = st.text_input("Ask a question about the memoir:")
    if user_input and author:
        response = handle_user_question(conn, user_input, memoir_id, author)
        st.write(f"**Answer:** {response}")

if __name__ == "__main__":
    main()
