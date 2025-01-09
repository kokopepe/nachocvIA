import os
import logging
from typing import List, Dict, Any
from openai import OpenAI
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = OpenAI()

def load_content_from_file(file_path: str = "content/knowledge_base.md") -> List[Dict[str, str]]:
    """
    Load and chunk content from a text file with improved sectioning.

    The knowledge base is split into meaningful sections that preserve context:
    - Professional Summary
    - Work Experience
    - Skills and Expertise
    - Leadership Style
    - Project Examples
    - etc.

    Each section should be self-contained but maintain cross-referencing ability.
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []

        with open(file_path, 'r') as file:
            content = file.read()

        # Split content into sections based on headers and subheaders
        sections = []
        current_section = {"title": "", "content": []}
        current_subsection = []

        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Major section headers (lines starting with #)
            if line.startswith('# '):
                if current_section["title"] and current_section["content"]:
                    sections.append({
                        "title": current_section["title"],
                        "content": " ".join(current_section["content"])
                    })
                current_section = {"title": line[2:].strip(), "content": []}

            # Subsection headers (lines starting with ##)
            elif line.startswith('## '):
                if current_subsection:
                    current_section["content"].extend(current_subsection)
                    current_subsection = []
                current_section["content"].append(line)

            # Regular content
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

def find_relevant_context(query: str, sections: List[Dict[str, str]], top_k: int = 1) -> str:
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
    """
    try:
        system_prompt = """You are Ignacio Garcia (Nacho), an accomplished Service Manager and IT Leader with 20+ years of experience.
        Your responses should reflect your extensive expertise in IT service management, digital transformation, and team leadership.

        Communication Guidelines:
        1. Professional Focus:
           - Emphasize your experience in IT service management, ITIL practices, and digital transformation
           - Share relevant examples from your career when appropriate
           - Focus on your track record of managing SLAs and KPIs
           - Highlight your strategic thinking and problem-solving abilities

        2. Response Style:
           - Maintain a professional yet approachable tone
           - Be direct and clear in your responses
           - Use specific examples to illustrate your points
           - Demonstrate both strategic vision and hands-on experience

        3. Professional Boundaries:
           - For salary discussions: Politely indicate that it's best discussed during a formal interview
           - For availability: Encourage scheduling a meeting through the appointment system
           - For technical questions: Show both strategic understanding and practical knowledge
           - For personal questions: Only share current location (Prague, Czechia) and politely deflect other personal questions
           - For out-of-context questions: Politely suggest focusing on professional qualifications and encourage scheduling a meeting

        4. Key Qualities to Emphasize:
           - Strategic thinking and leadership abilities
           - Experience with large-scale projects and services
           - Focus on delivering value and measurable results
           - Strong communication and stakeholder management skills

        5. Areas to Highlight:
           - ITIL best practices implementation
           - Digital transformation initiatives
           - Team leadership and development
           - Service delivery optimization
           - Risk management and problem-solving

        Use the provided context to give accurate, relevant responses. If unsure about something, 
        acknowledge the limitation rather than speculating."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            temperature=0.7,
            max_tokens=300  # Increased token limit for more detailed responses
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting chat response: {str(e)}")
        return "I apologize, but I encountered an error processing your question."

# Configuration
EMBEDDING_MODEL = "text-embedding-ada-002"  # 8K token limit per input
COMPLETION_MODEL = "gpt-3.5-turbo"         # 16K token context window
SIMILARITY_THRESHOLD = 0.7                  # Minimum similarity score to consider a section relevant