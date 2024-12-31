import trafilatura
import json
import os
import logging
from typing import Dict, List
from urllib.parse import unquote

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def scrape_linkedin_profile(url: str) -> Dict:
    """
    Scrapes a LinkedIn profile and extracts relevant information.
    Returns a dictionary with structured profile data.
    """
    try:
        # Decode URL to handle special characters
        decoded_url = unquote(url)
        logger.info(f"Attempting to scrape LinkedIn profile: {decoded_url}")

        downloaded = trafilatura.fetch_url(decoded_url)
        if downloaded is None:
            logger.error("Could not download the LinkedIn page")
            raise ValueError("Could not download the LinkedIn page")

        text_content = trafilatura.extract(downloaded, include_links=True, include_formatting=True)
        if text_content is None:
            logger.error("Could not extract content from the LinkedIn page")
            raise ValueError("Could not extract content from the LinkedIn page")

        logger.debug(f"Successfully extracted raw content length: {len(text_content)}")

        # Basic information extraction
        sections = text_content.split('\n\n')
        profile_data = {
            "summary": "",
            "experience": [],
            "education": [],
            "skills": []
        }

        current_section = None
        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Identify sections based on common LinkedIn headers
            lower_section = section.lower()
            if "experience" in lower_section and len(section) < 20:
                current_section = "experience"
                logger.debug("Found experience section")
            elif "education" in lower_section and len(section) < 20:
                current_section = "education"
                logger.debug("Found education section")
            elif "skills" in lower_section and len(section) < 20:
                current_section = "skills"
                logger.debug("Found skills section")
            elif "about" in lower_section and len(section) < 20:
                current_section = "summary"
                logger.debug("Found summary section")
            else:
                if current_section == "summary" and not profile_data["summary"]:
                    profile_data["summary"] = section
                elif current_section == "experience":
                    profile_data["experience"].append(section)
                elif current_section == "education":
                    profile_data["education"].append(section)
                elif current_section == "skills" and '•' in section:
                    skills = [s.strip() for s in section.split('•') if s.strip()]
                    profile_data["skills"].extend(skills)

        logger.info("Successfully parsed LinkedIn profile data")
        return profile_data

    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile: {str(e)}")
        return {}

def convert_to_qa_format(profile_data: Dict) -> List[Dict]:
    """
    Converts LinkedIn profile data into Q&A format for the chatbot.
    """
    try:
        qa_pairs = []

        # Add summary Q&A
        if profile_data.get("summary"):
            qa_pairs.append({
                "question": "Tell me about yourself",
                "answer": profile_data["summary"]
            })
            qa_pairs.append({
                "question": "What is your professional background?",
                "answer": profile_data["summary"]
            })

        # Add experience Q&A
        if profile_data.get("experience"):
            experience_text = "\n".join(profile_data["experience"])
            qa_pairs.append({
                "question": "What is your work experience?",
                "answer": experience_text
            })
            qa_pairs.append({
                "question": "What roles have you worked in?",
                "answer": experience_text
            })

        # Add education Q&A
        if profile_data.get("education"):
            education_text = "\n".join(profile_data["education"])
            qa_pairs.append({
                "question": "What is your educational background?",
                "answer": education_text
            })
            qa_pairs.append({
                "question": "Where did you study?",
                "answer": education_text
            })

        # Add skills Q&A
        if profile_data.get("skills"):
            skills_text = ", ".join(profile_data["skills"])
            qa_pairs.append({
                "question": "What are your key skills and competencies?",
                "answer": f"My key skills include: {skills_text}"
            })
            qa_pairs.append({
                "question": "What technologies are you proficient in?",
                "answer": f"I am proficient in: {skills_text}"
            })

        logger.info(f"Created {len(qa_pairs)} Q&A pairs from LinkedIn data")
        return qa_pairs

    except Exception as e:
        logger.error(f"Error converting profile data to Q&A format: {str(e)}")
        return []

def save_linkedin_data(url: str, output_dir: str = "content/interviews") -> bool:
    """
    Scrapes LinkedIn profile and saves the Q&A data to a JSON file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Scrape and convert the data
        logger.info("Starting LinkedIn data extraction")
        profile_data = scrape_linkedin_profile(url)
        if not profile_data:
            logger.error("Failed to extract profile data")
            return False

        qa_pairs = convert_to_qa_format(profile_data)
        if not qa_pairs:
            logger.error("Failed to convert profile data to Q&A format")
            return False

        # Save to JSON file
        output_file = os.path.join(output_dir, "linkedin_qa.json")
        with open(output_file, "w", encoding='utf-8') as f:
            json.dump(qa_pairs, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully saved LinkedIn Q&A data to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error saving LinkedIn data: {str(e)}")
        return False