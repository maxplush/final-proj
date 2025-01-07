
# RAG Project: My Father's Memoir

This project enables interaction with my late father's memoir through a Retrieval-Augmented Generation (RAG) approach. It uses the Groq LLM for keyword extraction and SQLite's built-in FTS5 full-text search system to find the best result. The interface is a Streamlit application, with images generated with the Monster API using the Pix-Art-Sigma model. Three short chapters have been included, reflecting those I feel comfortable sharing.


## Sample Streamlit Conversation

<p align="center">
  <img src="readme_images/jones_beach.png" alt="Example Chapter">
  <img src="readme_images/jones_beach_chat.png" alt="Example Chapter">
</p>

## Sample Command Line Conversation
<p align="center">
  <img src="readme_images/command_line.png" alt="Example Command Line Interaction">
</p>

## Setup Instructions

To run this project, you must:

1. Create a [Groq API key](https://console.groq.com/docs/quickstart).
2. Create a [Monster API key](https://developer.monsterapi.ai/reference/introduction-1).
3. Create a `.env` file and store these keys in the following format:

   ```
   GROQ_API_KEY=your_groq_api_key
   MONSTER_API_KEY=your_monster_api_key
   ```
4. (Recommended) Create and activate the virtual environment:
   ```bash
   $ python3 -m venv venv
   $ source venv/bin/activate  # MacOS/Linux
   $ venv\Scripts\activate     # Windows
   ```

5. Install the required dependencies by running the following command:
   ```bash
   $ pip install -r requirements.txt
   ```

## How to Run

1. **Test Accuracy of LLM Output**:  
   Run the `test_memoir_rag.py` file to process the memoir and evaluate the LLM's accuracy:
   ```bash
   $ python3 test_memoir_rag.py
   ```
   Example Output:
   ```
   Overall Accuracy: 80.00%
   ```
   This process:
   - Chunks the memoir by chapters.
   - Creates a SQLite database, tables and full-text search(FTS5) tables.
   - Generates a system prompt for text-image model from Groq.
   - Generates a image from Monster's txt2image model for each chapter.
   - Evaluates LLM responses against predefined keyword-based answers, including handling malicious questions.
      - 0: Less than 3/5 correct keywords.
      - 0.6: 3-4/5 correct keywords.
      - 1: 5/5 correct keywords.
      - Malicious questions that return "unsafe" are treated as correct, given a score of 1.
      - The total score is calculated by summing individual points and dividing by the total number of questions.

2. **Front End**:  
   Launch the Streamlit application to interact with the memoir:
   ```bash
   $ streamlit run app.py
   ```
   This allows you to read chapters and ask questions.

3. **Command-Line Interaction**:  
   Interact with the memoir RAG via the terminal:
   ```bash
   $ python3 memoir_rag.py --title "alan test" --author "alan plush"
   ```
   Note that the database will already be pre-loaded if you ran the `testrag.py` function.

   If you'd like to skip the `testrag.py` step, you can manually load the content by running the following commands:
   ```bash
   $ python3 memoir_rag.py --save --title "alan test" --author "alan plush" --content "alan_test_doc.txt"
   ```
      ```bash
   $ python3 memoir_rag.py --title "alan test" --author "alan plush"
   ```

## Key Features
- **Guardrails Against Malicious Questions**:  
  Incorporates safety checks for flagged content using Groq's Llama Guard 3.

- **Keyword-Based Scoring System**:  
  Evaluates LLM's effectiveness of responses by matching them against predefined answer keywords for accuracy:

- **AI-Generated Chapter Images**:  
  Uses the Monster text2image image generation model to create images about the setting of each chapter.

- **Full-Text Search**:  
   Keywords generated by the LLM are used to perform a full-text search (FTS5), retrieving the most relevant response.