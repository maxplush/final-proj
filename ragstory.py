#!/bin/python3

'''
Store a memoir in a database and run an interactive QA session using the Groq LLM API.
The memoir is loaded from a text file, stored in a database, and can be referenced during conversations.
'''

import logging
import os
import groq
import sqlite3
import textwrap
import argparse

################################################################################
# LLM setup
################################################################################

client = groq.Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def run_llm(system, user, model='llama3-8b-8192', seed=None):
    '''
    Helper function to interact with the LLM using the Groq API.
    '''
    chat_completion = client.chat.completions.create(
        messages=[
            {
                'role': 'system',
                'content': system,
            },
            {
                "role": "user",
                "content": user,
            }
        ],
        model=model,
        seed=seed,
    )
    return chat_completion.choices[0].message.content

################################################################################
# Database functions
################################################################################

def initialize_db(db_path='memoirs.db'):
    '''
    Initialize the SQLite database for storing memoirs and their chunks.
    '''
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table for memoirs metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoirs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT
        )
    ''')
    
    # Table for storing memoir chunks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoir_chunks (
            chunk_id INTEGER PRIMARY KEY,
            memoir_id INTEGER,
            content TEXT,
            FOREIGN KEY (memoir_id) REFERENCES memoirs (id)
        )
    ''')
    conn.commit()
    return conn

def save_memoir_to_db(conn, title, author, content, chunk_size=2000):
    '''
    Save the memoir and its chunks to the database.
    '''
    cursor = conn.cursor()
    
    # Insert memoir metadata
    cursor.execute('''
        INSERT INTO memoirs (title, author)
        VALUES (?, ?)
    ''', (title, author))
    
    memoir_id = cursor.lastrowid  # Get the ID of the newly inserted memoir
    
    # Split content into chunks and save each chunk
    chunks = split_into_chunks(content, chunk_size)
    for chunk in chunks:
        cursor.execute('''
            INSERT INTO memoir_chunks (memoir_id, content)
            VALUES (?, ?)
        ''', (memoir_id, chunk))
    
    conn.commit()


def load_memoir_from_db(conn, author):
    '''
    Load a memoir from the database based on the author's name.
    '''
    cursor = conn.cursor()
    cursor.execute('''
        SELECT content FROM memoirs WHERE author = ?
    ''', (author,))
    result = cursor.fetchone()
    return result[0] if result else None

################################################################################
# Memoir functions
################################################################################

def load_memoir(file_path):
    '''
    Load the memoir from a text file.
    '''
    with open(file_path, 'r', encoding='utf-8') as file:
        memoir_text = file.read()
    return memoir_text

# Define a helper function to split the memoir into chunks
def split_into_chunks(text, chunk_size=2000):
    '''
    Splits the memoir text into smaller chunks that can fit within the LLM's context limit.
    Each chunk should not exceed the specified chunk_size.
    '''
    return textwrap.wrap(text, chunk_size)

def is_appropriate_question(user_input):
    # This can be a simple keyword-based rule or a small model.
    storytelling_keywords = ["tell me", "make up", "create a story", "imagine"]
    return not any(keyword in user_input.lower() for keyword in storytelling_keywords)

def search_across_chunks(conn, user_input, memoir_id, seed=None):
    '''
    Searches across memoir chunks in the database and returns the best response.
    '''
    # Retrieve chunks based on memoir_id
    cursor = conn.cursor()
    cursor.execute('''
        SELECT content FROM memoir_chunks WHERE memoir_id = ?
    ''', (memoir_id,))
    chunks = [row[0] for row in cursor.fetchall()]
    
    responses = []
    for chunk in chunks:
        system = (
            "You are a knowledgeable assistant summarizing specific details from a memoir. "
            "Provide clear, factual answers using only the provided text. If you are uncertain, "
            "respond with 'I don't know' or 'The text does not provide that information.'"
        )
        user = f"Memoir content: {chunk}\n\nUser's question: {user_input}"
        response = run_llm(system, user, seed=seed)
        responses.append(response)
    
    # Select the best response by ranking
    best_response = max(responses, key=len)
    return best_response


def chat_with_memoir(user_input, memoir, seed=None):
    '''
    Conduct a Q&A session with the memoir as context.
    Searches across all chunks and retrieves the best response if the question is appropriate.
    '''
    # First, check if the question is appropriate
    if not is_appropriate_question(user_input):
        return "I'm sorry, but I can't answer that kind of question."

    # Split the memoir into smaller chunks if necessary
    chunks = split_into_chunks(memoir, chunk_size=2000)
    
    # Search across all chunks and return the best response
    best_response = search_across_chunks(user_input, chunks, seed=seed)
    return best_response

# current state is searching across chunks 

################################################################################
# Main interaction
################################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Memoir Q&A System")
    parser.add_argument('--save', action='store_true', help="Save a new memoir to the database")
    parser.add_argument('--title', type=str, help="Title of the memoir")
    parser.add_argument('--author', type=str, help="Author of the memoir")
    parser.add_argument('--content', type=str, help="Path to the text file of the memoir content")
    args = parser.parse_args()
    
    conn = initialize_db()
    
    if args.save:
        # Saving a memoir to the database
        if not (args.title and args.author and args.content):
            print("To save a memoir, please provide --title, --author, and --content.")
        else:
            with open(args.content, 'r') as file:
                content = file.read()
            save_memoir_to_db(conn, args.title, args.author, content)
            print(f"Memoir '{args.title}' by {args.author} has been saved to the database.")
    
    else:
        # Load a memoir for Q&A session
        if not (args.title and args.author):
            print("To start a Q&A session, please provide --title and --author.")
        else:
            cursor = conn.cursor()
            memoir_id = cursor.execute(
                'SELECT id FROM memoirs WHERE title = ? AND author = ?',
                (args.title, args.author)
            ).fetchone()
            
            if memoir_id:
                memoir_id = memoir_id[0]
                print(f"Memoir '{args.title}' by {args.author} loaded from the database.")
                
                # Start the Q&A session
                while True:
                    user_input = input("\nAsk a question about the memoir (or type 'exit' to quit): ")
                    if user_input.lower() == 'exit':
                        break
                    
                    # Get LLM response based on the memoir and user question
                    response = search_across_chunks(conn, user_input, memoir_id)
                    print("\nResponse:\n", response)
            else:
                print(f"Memoir '{args.title}' by {args.author} not found in the database.")
