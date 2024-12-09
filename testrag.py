import csv
import sqlite3
import logging
from memrag import (
    search_across_chunks,
    save_memoir_to_db,
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

def evaluate_test_questions(csv_path, db_path):
    """
    Evaluates test questions from a CSV file against the RAG system.
    """
    # Initialize the database
    conn = initialize_db(db_path)
    
    # Load the memoir content from file
    with open("alan_test_doc.txt", "r", encoding="utf-8") as file:
        test_memoir_content = file.read()

    # Save memoir to database (this now includes image path handling)
    title = "Alan's Memoir"
    author = "Alan"
    save_memoir_to_db(conn, title, author, test_memoir_content)

    # Load test questions from CSV
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        questions = [row for row in reader]

    # Evaluate questions
    correct_count = 0
    for question in questions:
        user_input = question['question']
        answer_keywords = question['answer_keywords'].split(',')
        memoir_id = 1  # Assuming we saved the memoir with ID 1

        # Get the response from the RAG system
        response = search_across_chunks(conn, user_input, memoir_id, author)

        # Check if the response contains at least 3 out of 5 keywords
        matched_keywords = [kw for kw in answer_keywords if kw in response]
        score = 0
        if len(matched_keywords) >= 5:
            score = 1.0
        elif len(matched_keywords) >= 3:
            score = 0.6

        # Log and calculate accuracy
        if score > 0:
            correct_count += 1

        # Log results for debugging purposes
        print(f"Question: {user_input}")
        print(f"Response: {response}")
        print(f"Matched Keywords: {matched_keywords}")
        print(f"Score: {score}")
        print("-" * 40)

    # Calculate overall accuracy
    accuracy = correct_count / len(questions)
    print(f"Overall Accuracy: {accuracy * 100:.2f}%")

    conn.close()

if __name__ == "__main__":
    # Example usage
    test_csv_path = "test_questions.csv"  # Update with your CSV file path
    database_path = "memoirs.db"
    evaluate_test_questions(test_csv_path, database_path)
