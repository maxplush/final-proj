
# RAG Project: My Father's Memoir

This project centers around the memoir of my late father, using a Retrieval-Augmented Generation (RAG) approach. I utilized the Groq RAG LLM to process text from select chapters of his memoir and integrated Monster GPT to generate AI images based on the content of each chapter. I also used Streamlit to create a front-end interface for interaction with the application.

## Requirements

To run this project, you must:

1. Create a **Groq API key**.
2. Create a **Monster API key**.
3. Store these keys in a `.env` file with the following format:

   ```
   GROQ_API_KEY=your_groq_api_key
   MONSTER_API_KEY=your_monster_api_key
   ```
4. (Recommended) Create and activate the virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # MacOS/Linux
   venv\Scripts\activate     # Windows
   ```

5. Install the required dependencies by running the following command:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

### Testing the Quality of the LLM Output

1. **Test Accuracy of LLM Output**:  
   Run the `test_memoir_rag.py` file to process the memoir and evaluate the LLM's accuracy:
   ```bash
   python3 test_memoir_rag.py
   ```
   Example Output:
   ```
   Overall Accuracy: 80.00%
   ```
   This process:
   - Chunks the memoir by chapters.
   - Creates a SQLite database with FTS5 full-text search.
   - Generates system prompt for text-image model.
   - Generates a image from MonsterGPT's txt2image model for each chapter.
   - Evaluates LLM responses against predefined keyword-based scores, including handling malicious questions.

2. **Front End**:  
   Launch the Streamlit application to interact with the memoir:
   ```bash
   streamlit run app.py
   ```
   This allows you to read chapters and ask questions about the content.

3. **Command-Line Interaction**:  
   Interact with the memoir RAG via the terminal:
   ```bash
   python3 memoir_rag.py --title "alan test" --author "alan plush"
   ```
   Note that the database will already be pre-loaded if you ran the `testrag.py` function.

   If you'd like to skip the `testrag.py` step, you can manually load the content by running the following commands:
   ```bash
   python3 memoir_rag.py --save --title "alan test" --author "alan plush" --content "alan_test_doc.txt"
   python3 memoir_rag.py --title "alan test" --author "alan plush"
   ```

## Key Features
- **Guardrails Against Malicious Questions**:  
  Incorporates safety checks for flagged content using Groq's Llama Guard 3.

- **Keyword-Based Scoring System**:  
  Evaluates LLM responses by matching them against predefined answer keywords for accuracy:
   - 0: Less than 3/5 correct keywords.
   - 0.6: 3/5 correct keywords.
   - 1: 5/5 correct keywords.
   - Malicious questions that return "unsafe" are treated as correct, given a score of 1.

   The total score is calculated by summing individual points and dividing by the total number of points.

- **AI-Generated Chapter Images**:  
  Uses Monster GPT to create unique visual images for each chapter.

