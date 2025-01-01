import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = OpenAI()

def load_content_from_file(file_path: str = "content/knowledge_base.txt") -> List[Dict[str, str]]:
    """
    Load and chunk content from a text file.

    The knowledge base is split into sections based on headers (lines starting with #).
    Each section becomes a separate chunk that can be independently embedded and retrieved.

    GPT-3.5-turbo has a context window of 16K tokens (~12,000 words)
    GPT-4 has a context window of 32K tokens (~24,000 words)

    When chunking the content:
    1. Each section (chunk) should be meaningful on its own
    2. We aim to keep sections under 2000 words to ensure we can combine multiple relevant sections
    3. Headers help maintain context when sections are retrieved independently
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []

        with open(file_path, 'r') as file:
            content = file.read()

        # Split content into sections based on headers
        sections = []
        current_section = {"title": "", "content": []}

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Start new section on headers (lines starting with #)
            if line.startswith('#'):
                # Save previous section if it exists
                if current_section["title"] and current_section["content"]:
                    sections.append({
                        "title": current_section["title"],
                        "content": " ".join(current_section["content"])
                    })
                current_section = {"title": line[1:].strip(), "content": []}
            else:
                current_section["content"].append(line)

        # Add the last section
        if current_section["title"] and current_section["content"]:
            sections.append({
                "title": current_section["title"],
                "content": " ".join(current_section["content"])
            })

        logger.info(f"Loaded {len(sections)} sections from {file_path}")
        return sections

    except Exception as e:
        logger.error(f"Error loading content: {str(e)}")
        return []

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a piece of text using OpenAI's API.

    The text-embedding-ada-002 model:
    - Can handle up to 8191 tokens per input
    - Generates 1536-dimensional embeddings
    - Cost is very low ($0.0001 per 1K tokens)
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        return []

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def find_relevant_context(query: str, sections: List[Dict[str, str]], top_k: int = 2) -> str:
    """
    Find the most relevant sections for a given query.

    Process:
    1. Convert query to embedding vector
    2. Convert each section to embedding vector
    3. Find sections with highest cosine similarity to query
    4. Return concatenated text of top-k most relevant sections

    The returned context + query + system prompt should fit in model's context window:
    - GPT-3.5-turbo: 16K tokens
    - GPT-4: 32K tokens

    We typically retrieve top 2-3 most relevant sections to ensure:
    1. We have enough context to answer the question
    2. We stay well within token limits
    3. We keep response focused and relevant
    """
    try:
        if not sections:
            logger.warning("No sections available for context retrieval")
            return ""

        # Get query embedding
        query_embedding = get_embedding(query)
        if not query_embedding:
            return ""

        # Get embeddings for all sections
        section_embeddings = []
        for section in sections:
            # Combine title and content for embedding
            section_text = f"{section['title']}: {section['content']}"
            embedding = get_embedding(section_text)
            if embedding:
                section_embeddings.append({
                    "text": section_text,
                    "embedding": embedding
                })

        # Calculate similarities and get top-k sections
        similarities = [
            (cosine_similarity(query_embedding, section["embedding"]), section["text"])
            for section in section_embeddings
        ]
        similarities.sort(reverse=True)

        # Return concatenated top-k sections
        relevant_sections = [text for _, text in similarities[:top_k]]
        return "\n".join(relevant_sections)

    except Exception as e:
        logger.error(f"Error finding relevant context: {str(e)}")
        return ""

def get_chat_response(query: str, context: str) -> str:
    """
    Get chat completion using the relevant context.

    Process:
    1. Start with system prompt that defines Nacho's personality
    2. Add context from relevant sections
    3. Add user's query
    4. Get response from GPT model

    Token usage typically breaks down as:
    - System prompt: ~200-400 tokens
    - Context: ~1000-3000 tokens (2-3 relevant sections)
    - User query: ~50-100 tokens
    - Response: ~150 tokens (max_tokens parameter)

    Total is well within 16K token limit of GPT-3.5-turbo
    """
    try:
        system_prompt = """You are Ignacio Garcia (Nacho), an experienced IT Manager and technology leader. 
        Your communication style is professional yet approachable. When answering questions:

        - Focus on your extensive experience in IT service management, digital transformation, and team leadership
        - Share specific examples from your career when relevant
        - Be honest and direct about your expertise and limitations
        - Maintain professionalism and avoid inappropriate topics
        - For technical questions, demonstrate both strategic thinking and hands-on knowledge
        - When discussing hobbies or personal interests, keep responses appropriate and professional
        - If asked about salary expectations or confidential information, politely deflect
        - For questions about availability or interviews, encourage scheduling a meeting

        Use the provided context to answer questions accurately, and if you're unsure about something, 
        acknowledge the limitation of your knowledge rather than making assumptions."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting chat response: {str(e)}")
        return "I apologize, but I encountered an error processing your question."

# Configuration
EMBEDDING_MODEL = "text-embedding-ada-002"  # 8K token limit per input
COMPLETION_MODEL = "gpt-3.5-turbo"         # 16K token context window
SIMILARITY_THRESHOLD = 0.7                  # Minimum similarity score to consider a section relevant