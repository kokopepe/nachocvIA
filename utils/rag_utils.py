import os
import json
from typing import List, Dict
import openai
from openai import OpenAI

client = OpenAI()

def load_interview_content(directory: str = "content/interviews") -> List[Dict]:
    """Load interview Q&A content from text files."""
    documents = []

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # If no files exist yet, create a sample one
    if not os.listdir(directory):
        sample_content = [
            {"question": "Tell me about yourself", 
             "answer": "I am Ignacio Garcia, a software developer with expertise in web development and system architecture. I specialize in creating efficient, scalable solutions using modern technologies."},
            {"question": "What are your strengths?",
             "answer": "My key strengths include problem-solving, adaptability, and strong communication skills. I excel at breaking down complex problems and finding innovative solutions."}
        ]
        with open(f"{directory}/sample_qa.json", "w") as f:
            json.dump(sample_content, f, indent=2)

    # Load all JSON files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            try:
                with open(os.path.join(directory, filename), 'r') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        documents.extend(content)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
                continue

    return documents

def get_embedding(text: str) -> List[float]:
    """Get embedding for a piece of text using OpenAI's API."""
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return []

def find_best_match(query: str, documents: List[Dict]) -> Dict:
    """Find the best matching Q&A pair for a given query."""
    try:
        if not documents:
            return {
                "question": "",
                "answer": "I apologize, but I don't have any information loaded yet. Please try again later."
            }

        # Get query embedding
        query_embedding = get_embedding(query)
        if not query_embedding:
            return {
                "question": "",
                "answer": "I apologize, but I encountered an error processing your question. Please try again."
            }

        # Get embeddings for all questions
        best_similarity = -1
        best_match = None

        for doc in documents:
            # Get embedding for the question
            doc_embedding = get_embedding(doc["question"])
            if not doc_embedding:
                continue

            # Calculate cosine similarity
            similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = doc

        return best_match if best_match else {
            "question": "",
            "answer": "I apologize, but I don't have specific information about that. Please try asking another question about my professional experience or qualifications."
        }

    except Exception as e:
        print(f"Error in finding best match: {e}")
        return {
            "question": "",
            "answer": "I apologize, but I encountered an error processing your question. Please try again."
        }

# Configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
COMPLETION_MODEL = "gpt-3.5-turbo"
SIMILARITY_THRESHOLD = 0.7

def get_chat_completion(query: str, context: str) -> str:
    """Get chat completion using GPT-3.5."""
    try:
        response = client.chat.completions.create(
            model=COMPLETION_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant answering questions based on the provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting chat completion: {e}")
        return "I apologize, but I encountered an error processing your question."