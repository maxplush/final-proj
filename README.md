
# RAG Project: My Father's Memoir

This project centers around the memoir of my late father, using a Retrieval-Augmented Generation (RAG) approach. I utilized the Groq RAG LLM to process text from select chapters of his memoir and integrated Monster GPT to generate AI images based on the content of each chapter. Additionally, I used Streamlit to create a front-end interface for interaction with the application.

## Requirements

To run this project, you must:

1. Create a **Groq API key**.
2. Create a **Monster API key**.
3. Store these keys in a `.env` file with the following format:

```
GROQ_API_KEY=your_groq_api_key
MONSTER_API_KEY=your_monster_api_key
```

4. Install the required dependencies by running the following command:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Code

### Testing the Quality of the LLM Output

To test the quality of the LLM output, I created the `testrag.py` file. This script performs the following steps:

1. Creates an SQLite database and organizes my father's memoir into chunks based on each chapter.
2. Creates a Full-Text Search (FTS5) table in the database.
3. Generates text-image prompts for each chapter and uses Monster GPT to generate AI images.
4. Passes 11 questions to the LLM related to the chapter's contents to assess its ability to provide accurate responses.

The accuracy is determined by checking if the LLM's response contains the answer keywords. Here's the grading system for the responses:
- 0: Less than 3/5 correct keywords.
- 0.6: 3/5 correct keywords.
- 1: 5/5 correct keywords.
- Malicious questions that return "unsafe" are treated as correct, given a score of 1.

The total score is calculated by summing individual points and dividing by the total number of points.

### Running the Streamlit App

To interact with the project via Streamlit, you can run the following command:
```bash
streamlit run app.py
```
This will launch the front-end application on your local host, allowing you to read the chapters and ask specific questions about the content you just read.

### Interacting with the LLM via Terminal

If you'd like to interact with the LLM via the terminal, you can run the following command:
```bash
python3 memrag.py --title "alan test" --author "alan plush"
```
Note that the database will already be pre-loaded if you ran the `testrag.py` function.

### Skipping the `testrag.py` Step

If you'd like to skip the `testrag.py` step, you can manually load the content by running the following commands:
```bash
python3 memrag.py --save --title "alan test" --author "alan plush" --content "alan_test_doc.txt"
python3 memrag.py --title "alan test" --author "alan plush"
```

## Additional Features

1. **Guard Rails for Malicious Questions**: I added an additional Groq LLM feature, Llama Guard 3, to detect malicious questions and ensure safe responses from the system.
