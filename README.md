# Retrieval Augmented Generation (RAG) Memoir Project ![](https://github.com/maxplush/ragnews-new/workflows/tests/badge.svg)

This project involves Retrieval Augmented Generation (RAG), a method that combines retrieval and generation models to enhance the ability to generate responses based on retrieved information. Specifically, this project focuses on engaging with memoirs, allowing users to ask questions and receive answers that reflect the author's style and content.

## Prerequisites

- Before running the script, make sure you have the packages listed in the requirements.txt file.
- A `.env` file in the same directory containing your  [Groq API KEY](https://groq.com). The file should have the following format:
  
  ```env
  GROQ_API_KEY=your_groq_api_key_here

## Usage

To use ragnews.py, follow these steps:

1. Ensure your .env file is configured correctly with your Groq API key. Connect your .env by running the command.

```
$ export $(cat .env)
```

2. Run the ragnews.py script within your virtual environment:

```
python3 ragstory.py --memoir /path/to/your/memoir.txt
```

3. The system will prompt with:

```
ragstory>
```

4. Ask a question, for example:

```
What did the author learn from his experiences at the beach?
```

```
I'm happy to help you with that! Based on the memoir, the author recounts two pivotal childhood experiences at Rockaway Beach and Jones Beach, where he learned about both joy and vulnerability. These experiences shaped his understanding of childhood and the complexities of emotions.
```