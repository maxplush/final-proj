import csv

def load_test_data(csv_file):
    """
    Load test data from a CSV file.
    """
    test_data = []
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            question = row['Question']
            answer = row['Answer']
            keywords = row['Keywords'].split(', ')
            test_data.append({'question': question, 'answer': answer, 'keywords': keywords})
    return test_data

def evaluate_response(response, keywords):
    """
    Evaluate the LLM's response based on the presence of keywords.
    Returns 1 if the response meets the keyword threshold, otherwise 0.
    """
    matched_keywords = [kw for kw in keywords if kw in response.lower()]
    return 1 if len(matched_keywords) >= len(keywords) * 0.6 else 0

def test_llm_performance(memrag_func, memoir, author, test_data):
    """
    Test the LLM's performance and calculate accuracy.
    """
    correct_count = 0
    total_questions = len(test_data)
    debug_info = []

    for data in test_data:
        question = data['question']
        expected_keywords = data['keywords']
        
        # Get LLM response
        response = memrag_func(question, memoir, author)
        
        # Evaluate response
        score = evaluate_response(response, expected_keywords)
        correct_count += score

        # Debugging: Check if question has an expected answer
        if not data['answer']:
            debug_info.append(f"Missing correct answer for question: {question}")

    accuracy = correct_count / total_questions
    return accuracy, debug_info

if __name__ == "__main__":
    # Load test data
    test_file = "memoir_test_data.csv"
    test_data = load_test_data(test_file)

    # Memoir and author details
    memoir = "alan_test_doc.txt"
    author = "alan"

    # Function to test
    from memrag import chat_with_memoir

    # Test the LLM
    accuracy, debug_info = test_llm_performance(chat_with_memoir, memoir, author, test_data)

    print(f"Accuracy: {accuracy * 100:.2f}%")
    if debug_info:
        print("Debugging Issues:")
        for issue in debug_info:
            print(f"- {issue}")
