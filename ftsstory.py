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
            id INTEGER PRIMARY KEY, -- Add this column
            memoir_id INTEGER,
            content TEXT,
            system_prompt TEXT,
            FOREIGN KEY (memoir_id) REFERENCES memoirs (id)
        )
    ''')


    # Create an FTS table for fast full-text search
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS memoir_chunks_fts
        USING fts5(content, chunk_id UNINDEXED, memoir_id UNINDEXED)
    ''')

    conn.commit()
    return conn

def add_system_prompt_column(conn):
    """
    Ensures the system_prompt column exists in memoir_chunks.
    """
    cursor = conn.cursor()
    cursor.execute('''
        PRAGMA table_info(memoir_chunks);
    ''')
    columns = [row[1] for row in cursor.fetchall()]
    if 'system_prompt' not in columns:
        cursor.execute('''
            ALTER TABLE memoir_chunks ADD COLUMN system_prompt TEXT
        ''')
        conn.commit()

def save_memoir_to_db(conn, title, author, content):
    cursor = conn.cursor()
    
    # Insert memoir metadata
    cursor.execute('''
        INSERT INTO memoirs (title, author)
        VALUES (?, ?)
    ''', (title, author))
    memoir_id = cursor.lastrowid

    # Chunk the memoir content by chapters
    chapters = chunk_by_chapter(content)
    for chapter in chapters:
        cursor.execute('''
            INSERT INTO memoir_chunks (memoir_id, content)
            VALUES (?, ?)
        ''', (memoir_id, chapter))
        chunk_id = cursor.lastrowid

        # Add to FTS table
        cursor.execute('''
            INSERT INTO memoir_chunks_fts (content, chunk_id, memoir_id)
            VALUES (?, ?, ?)
        ''', (chapter, chunk_id, memoir_id))

        # Generate a system prompt for the chapter
        system_prompt = generate_system_prompt(author, chapter)

        # Update the system_prompt column in memoir_chunks
        cursor.execute('''
            UPDATE memoir_chunks
            SET system_prompt = ?
            WHERE id = ?
        ''', (system_prompt, chunk_id))

    conn.commit()
    print(f"Memoir '{title}' by {author} saved with chunks and system prompts.")


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

# def is_appropriate_question(user_input):
#     # This can be a simple keyword-based rule or a small model.
#     storytelling_keywords = ["tell me", "make up", "create a story", "imagine"]
#     return not any(keyword in user_input.lower() for keyword in storytelling_keywords)

def extract_keywords(text, seed=None):
    """
    Extracts search keywords from user input using the LLM.
    """
    system = (
        "You are a professional database query optimizer. "
        "Given the text below, extract a list of relevant and concise keywords "
        "that best represent the user's query. "
        "Return the keywords separated by spaces. Do not include any other text."
    )
    keywords = run_llm(system, text, seed=seed).strip()
    return keywords

def sanitize_for_match_query(keywords):
    """
    Sanitizes extracted keywords for FTS MATCH queries.
    """
    sanitized_keywords = re.sub(r'[^\w\s]', '', keywords)  # Remove non-alphanumeric chars
    sanitized_keywords = ' '.join(sanitized_keywords.split())  # Normalize spaces
    return f'"{sanitized_keywords}"' if sanitized_keywords else None


def search_across_chunks(conn, user_input, memoir_id, author, seed=None):
    """
    Improved version of search_across_chunks.
    Includes safety check to classify user input before processing.
    """
    # Classify the user's input for safety using Llama Guard 3
    is_safe, guard_response = classify_question_with_guard(user_input)
    if not is_safe:
        return f"Your question has been flagged as unsafe. Details: {guard_response}"
    
    # Step 1: Extract keywords
    keywords = extract_keywords(user_input, seed=seed)
    if not keywords:
        return "I couldn't understand your query. Please try rephrasing."

    # Step 2: Sanitize for FTS MATCH
    sanitized_keywords = sanitize_for_match_query(keywords)
    if not sanitized_keywords:
        return "No valid keywords found. Please refine your question."

    # Step 3: Perform FTS MATCH query
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT content
            FROM memoir_chunks_fts
            WHERE memoir_id = ? AND content MATCH ?
            ORDER BY rank DESC
        ''', (memoir_id, sanitized_keywords))
        results = cursor.fetchall()
    except sqlite3.OperationalError as e:
        logging.error(f"FTS MATCH query error: {e}")
        return "An error occurred while searching the memoir."

    if not results:
        # Fallback: Provide the entire memoir if no matches
        cursor.execute('''
            SELECT content
            FROM memoir_chunks
            WHERE memoir_id = ?
        ''', (memoir_id,))
        full_memoir = " ".join(row[0] for row in cursor.fetchall())
        user_prompt = f"Memoir text: {full_memoir}\n\nUser's question: {user_input}"
        system = (
            f"You are an assistant summarizing content from a memoir by {author}. "
            "Answer the user's question based on the text provided. If you cannot find "
            "specific information, respond with 'The memoir does not address this.'"
        )
        return run_llm(system, user_prompt, seed=seed)

    # Step 4: Use the highest-ranked chunk for the LLM
    best_match = results[0][0]
    system = (
        f"You are an assistant summarizing content from a memoir by {author}. "
        "Answer the user's question based on the text provided. If you cannot find "
        "specific information, respond with 'The memoir does not address this.'"
    )
    user_prompt = f"Memoir text: {best_match}\n\nUser's question: {user_input}"
    return run_llm(system, user_prompt, seed=seed)

def classify_question_with_guard(user_input):
    '''
    Classifies the user input for safety using Llama Guard 3.
    '''
    completion = client.chat.completions.create(
        model="llama-guard-3-8b",
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
        temperature=0,
        max_tokens=1024,
        top_p=1,
        stop=None,
    )
    response = completion.choices[0].message.content
    if "unsafe" in response.lower():
        return False, response  # Unsafe detected, include category information
    return True, None  # Safe

def chat_with_memoir(user_input, memoir, author, seed=None):
    '''
    Conduct a Q&A session with the memoir as context.
    Uses Llama Guard 3 to classify questions before responding.
    '''
    # Classify the question for safety
    is_safe, guard_response = classify_question_with_guard(user_input)
    if not is_safe:
        return f"Your question has been flagged as unsafe. Details: {guard_response}"
    
    # Proceed with memoir Q&A logic if the question is safe
    chapters = chunk_by_chapter(memoir)
    best_response = search_across_chunks(conn, user_input, memoir, author, seed=seed)
    return best_response

def generate_system_prompt(author, chapter_content):
    """
    Generates a system prompt for text-to-image generation based on the chapter content.
    """
    system_prompt = (
        f"You are an expert at crafting detailed prompts for text-to-image models."
        " Based on the chapter below, generate a vivid and descriptive image prompt that includes:\n"
        "- Key subjects or characters\n"
        "- Setting (environment, time, atmosphere)\n"
        "- Mood and emotions\n"
        "Return only the description, with no extra text or explanations."
    )
    image_prompt = run_llm(system_prompt, chapter_content)
    return image_prompt

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
    add_system_prompt_column(conn)

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




# python3 ftsstory.py --save --title "alan test" --author "alan plush" --content "alantestdoc.txt"
# to run
# python3 ftsstory.py --title "alan test" --author "alan plush" 