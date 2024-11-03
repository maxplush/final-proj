
# Retrieval Augmented Generation (RAG) Summarization Project ![](https://github.com/maxplush/ragnews-new/workflows/tests/badge.svg)

This project involves Retrieval Augmented Generation (RAG), a method that combines retrieval and generation models to enhance the ability to generate responses based on retrieved information. Specifically, this project focuses on engaging with memoirs, allowing users to ask questions and receive answers that reflect the author's style and content.

## Prerequisites

- Before running the script, make sure you have the packages listed in the requirements.txt file.
- A `.env` file in the same directory containing your [Groq API KEY](https://groq.com). The file should have the following format:

  ```env
  GROQ_API_KEY=your_groq_api_key_here
  ```

## Usage

To use `ragstory.py`, follow these steps:

1. Ensure your `.env` file is configured correctly with your Groq API key. Connect your `.env` by running the command:

   ```bash
   $ export $(cat .env)
   ```

2. Run the `ragstory.py` script within your virtual environment:

   ```bash
   python3 ragstory.py --memoir /path/to/your/memoir.txt --author "Author Name" --title "Memoir Title"
   ```

3. The system will prompt with:

   ```bash
   ragstory>
   ```

4. Ask a question, for example:

   ```bash
   What did the author learn from his experiences at the beach?
   ```

   And receive a response like:

   ```
   I'm happy to help you with that! Based on the memoir, the author recounts two pivotal childhood experiences at Rockaway Beach and Jones Beach, where he learned about both joy and vulnerability. These experiences shaped his understanding of childhood and the complexities of emotions.
   ```

## Features

- **Interactive Q&A**: Users can ask questions about the memoir and receive contextually relevant answers while retaining the author's voice and tone.
- **Memoir Storage**: The system stores memoirs in an SQLite database, allowing for efficient querying and retrieval based on the author's name.
- **Content Handling**: The LLM processes the memoir content to provide summaries and answers to factual questions, minimizing the risk of hallucination.
- **Guardrails for Questions**: The system checks if questions are appropriate before attempting to answer them, helping to improve response accuracy and reliability.
