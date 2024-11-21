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
import re

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

def add_questions_column(conn):
    '''
    Adds a 'questions' column to the memoir_chunks table if it doesn't already exist.
    '''
    cursor = conn.cursor()
    try:
        cursor.execute('''
            ALTER TABLE memoir_chunks ADD COLUMN questions TEXT
        ''')
        conn.commit()
    except sqlite3.OperationalError:
        # If the column already exists, we just pass
        pass

def save_memoir_to_db(conn, title, author, content):
    '''
    Save the memoir and its chunks to the database.
    Generates questions for each chapter using the LLM and stores them in the database.
    '''
    cursor = conn.cursor()
    
    # Insert memoir metadata
    cursor.execute('''
        INSERT INTO memoirs (title, author)
        VALUES (?, ?)
    ''', (title, author))
    
    memoir_id = cursor.lastrowid  # Get the ID of the newly inserted memoir
    
    # Chunk the memoir content by chapters
    chapters = chunk_by_chapter(content)
    for chapter in chapters:
        cursor.execute('''
            INSERT INTO memoir_chunks (memoir_id, content)
            VALUES (?, ?)
        ''', (memoir_id, chapter))
        chunk_id = cursor.lastrowid  # Get the ID of the newly inserted chunk

        # Generate questions for the current chunk
        questions = generate_questions_for_chunk(author, chapter)
        
        # Store questions in the database
        cursor.execute('''
            UPDATE memoir_chunks
            SET questions = ?
            WHERE chunk_id = ?
        ''', (questions, chunk_id))
    
    conn.commit()

def generate_questions_for_chunk(author, chapter_content):
    '''
    Generates questions for a specific chapter chunk using the LLM.
    '''
    system_prompt = (
        f"Read this chapter about {author} and come up with 2 specific questions "
        "that can be answered given what you read. Only respond with the two Questions."
    )
    questions = run_llm(system_prompt, chapter_content)
    return questions

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


# Call this function after initializing the database
conn = initialize_db()
add_questions_column(conn)

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

# Define a function to chunk the memoir by chapters
def chunk_by_chapter(text):
    '''
    Splits the memoir into chapters based on the format "Chapter X - Title".
    '''
    # Regular expression to match chapter headings like "Chapter 5 - Jones Beach Undertow !!!"
    chapter_pattern = r"(Chapter \d+ - .+?)(?=\nChapter \d+ - |\Z)"
    
    # Find all chapters based on the pattern
    chapters = re.findall(chapter_pattern, text, re.DOTALL)

    return chapters

def is_appropriate_question(user_input):
    # This can be a simple keyword-based rule or a small model.
    storytelling_keywords = ["tell me", "make up", "create a story", "imagine"]
    return not any(keyword in user_input.lower() for keyword in storytelling_keywords)

def search_across_chunks(conn, user_input, memoir_id, author, seed=None):
    '''
    Searches across memoir chunks in the database and returns the best response.
    '''
    cursor = conn.cursor()
    cursor.execute('''
        SELECT content FROM memoir_chunks WHERE memoir_id = ?
    ''', (memoir_id,))
    chunks = [row[0] for row in cursor.fetchall()]

    responses = []
    for chunk in chunks:
        system = (
            f"You are a knowledgeable assistant summarizing specific details from a memoir by {author}. "
            "Provide clear, factual answers using only the provided text. If you are uncertain, "
            "respond with 'I don't know' or 'The text does not provide that information.'"
        )
        user = f"Memoir content: {chunk}\n\nUser's question: {user_input}"
        response = run_llm(system, user, seed=seed)
        responses.append(response)

    best_response = max(responses, key=len)
    return best_response

def is_malicious_question(user_input):
    '''
    Use Llama Guard 3 to classify whether the input is malicious or safe.
    Returns True if the question is deemed unsafe.
    '''
    completion = client.chat.completions.create(
        model="llama-guard-3-8b",
        messages=[
            {
                "role": "system",
                "content": "Classify this input as either 'safe' or 'unsafe' with reasoning if unsafe."
            },
            {
                "role": "user",
                "content": user_input,
            },
        ],
        temperature=0,  # Deterministic classification
        max_tokens=50,
    )
    response = completion.choices[0].message.content.strip().lower()
    return "unsafe" in response


def chat_with_memoir(user_input, memoir, author, seed=None):
    '''
    Conduct a Q&A session with the memoir as context.
    First filters malicious questions, then searches memoir chunks.
    '''
    # Step 1: Check for malicious content
    if is_malicious_question(user_input):
        return "I'm sorry, but your question is inappropriate and cannot be processed."

    # Step 2: Process the question if it's safe
    # Chunk the memoir by chapters if necessary
    chapters = chunk_by_chapter(memoir)
    
    # Search across all chapters and return the best response
    best_response = search_across_chunks(conn, user_input, memoir_id, author, seed=seed)
    return best_response

# def chat_with_memoir(user_input, memoir, author, seed=None):
#     '''
#     Conduct a Q&A session with the memoir as context.
#     Searches across all chunks and retrieves the best response if the question is appropriate.
#     '''
#     # First, check if the question is appropriate
#     if not is_appropriate_question(user_input):
#         return "I'm sorry, but I can't answer that kind of question."

#     # Chunk the memoir by chapters if necessary
#     chapters = chunk_by_chapter(memoir)
    
#     # Search across all chapters and return the best response
#     best_response = search_across_chunks(user_input, chapters, author, seed=seed)
#     return best_response

# this part I'm a bit unclear about how does the best_response work and should
# we focus more on the keywords like in ragnews?

# current state is searching across chunks 

################################################################################
# Main interaction
################################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Memoir Q&A System")
    parser.add_argument('--save', action='store_true', help="Save a new memoir to the database")
    parser.add_argument('--title', type=str, help="Title of the memoir")
    parser.add_argument('--author', type=str, help="Author of the memoir")
    parser.add_argument('--content', type=str, help="Path to the text file of the memoir content (required for --save)")
    args = parser.parse_args()
    
    # Initialize the database connection
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
            print("To start a Q&A session, please provide both --title and --author.")
        else:
            # Check if the memoir exists in the database
            cursor = conn.cursor()
            memoir_id = cursor.execute(
                'SELECT id FROM memoirs WHERE title = ? AND author = ?',
                (args.title, args.author)
            ).fetchone()
            
            if memoir_id:
                memoir_id = memoir_id[0]
                print(f"Memoir '{args.title}' by {args.author} loaded successfully.")
                
                # Start interactive Q&A session
                while True:
                    user_input = input("\nAsk a question about the memoir (or type 'exit' to quit): ")
                    if user_input.lower() == 'exit':
                        print("Exiting Q&A session.")
                        break
                    
                    # Retrieve answer using search_across_chunks
                    response = search_across_chunks(conn, user_input, memoir_id, args.author)
                    print("\nResponse:\n", response)
            else:
                print(f"Memoir '{args.title}' by {args.author} not found in the database.")




# python3 ragstory.py --save --title "alan test" --author "alan plush" --content "alantestdoc.txt"
# to run
# python3 ragstory.py --title "alan test" --author "alan plush" 