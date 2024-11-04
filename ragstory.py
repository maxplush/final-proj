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
    Initialize the SQLite database for storing memoirs.
    '''
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create a table for memoirs if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoirs (
            id INTEGER PRIMARY KEY,
            title TEXT,
            author TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    return conn

def save_memoir_to_db(conn, title, author, content):
    '''
    Save the memoir to the database.
    '''
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memoirs (title, author, content)
        VALUES (?, ?, ?)
    ''', (title, author, content))
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

def search_across_chunks(user_input, chunks, seed=None):
    '''
    Searches across all chunks, returning the best summarization response for the question.
    '''
    responses = []
    for chunk in chunks:
        # Generate a response from the current chunk
        system = (
            "You are a knowledgeable assistant summarizing specific details from a memoir. "
            "Provide clear, factual answers using only the provided text. If you are uncertain, "
            "respond with 'I don't know' or 'The text does not provide that information.'"
        )
        user = f"Memoir content: {chunk}\n\nUser's question: {user_input}"
        response = run_llm(system, user, seed=seed)

        # Append responses for post-processing and ranking
        responses.append(response)
    
    # Select the best response by ranking (for simplicity, pick the longest relevant answer or keyword-based)
    best_response = max(responses, key=len)  # Or use a relevance scoring metric here
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

################################################################################
# Main interaction
################################################################################

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Store and chat with a memoir using the Groq LLM API.")
    parser.add_argument('--memoir', help='Path to the memoir text file')
    parser.add_argument('--author', required=True, help='Author of the memoir (e.g., Alan Plush)')
    parser.add_argument('--title', required=True, help='Title of the memoir (e.g., Alan Plush Memoir)')
    parser.add_argument('--loglevel', default='warning')
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.loglevel.upper()))
    
    # Initialize the database connection
    conn = initialize_db()

    # Load and save memoir to the database
    if args.memoir:
        memoir_text = load_memoir(args.memoir)
        save_memoir_to_db(conn, args.title, args.author, memoir_text)
        print(f"Memoir '{args.title}' by {args.author} saved to the database.")
    
    # Load memoir from the database for chatting
    memoir_content = load_memoir_from_db(conn, args.author)
    if memoir_content:
        print(f"Memoir '{args.title}' by {args.author} loaded from the database.")
        print("\nLoaded memoir content:\n", memoir_content)  # Display full memoir content
        
        # Start a Q&A session with the memoir
        while True:
            user_input = input("\nAsk a question about the memoir (or type 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break

            # Get LLM response based on the memoir and user question
            response = chat_with_memoir(user_input, memoir_content)
            print("\nResponse:\n", response)
    else:
        print(f"Memoir by {args.author} not found in the database.")
