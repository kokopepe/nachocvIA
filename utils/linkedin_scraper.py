import trafilatura
import json
import os
from typing import Dict, List

def scrape_linkedin_profile(url: str) -> Dict:
    """
    Scrapes a LinkedIn profile and extracts relevant information.
    Returns a dictionary with structured profile data.
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            raise ValueError("Could not download the LinkedIn page")
        
        text_content = trafilatura.extract(downloaded, include_links=True, include_formatting=True)
        if text_content is None:
            raise ValueError("Could not extract content from the LinkedIn page")
        
        # Basic information extraction (we'll enhance this based on the actual content structure)
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
            elif "education" in lower_section and len(section) < 20:
                current_section = "education"
            elif "skills" in lower_section and len(section) < 20:
                current_section = "skills"
            elif "about" in lower_section and len(section) < 20:
                current_section = "summary"
            else:
                if current_section == "summary" and not profile_data["summary"]:
                    profile_data["summary"] = section
                elif current_section == "experience":
                    profile_data["experience"].append(section)
                elif current_section == "education":
                    profile_data["education"].append(section)
                elif current_section == "skills" and '•' in section:
                    profile_data["skills"].extend([s.strip() for s in section.split('•') if s.strip()])
        
        return profile_data
        
    except Exception as e:
        print(f"Error scraping LinkedIn profile: {e}")
        return {}

def convert_to_qa_format(profile_data: Dict) -> List[Dict]:
    """
    Converts LinkedIn profile data into Q&A format for the chatbot.
    """
    qa_pairs = []
    
    # Add summary Q&A
    if profile_data.get("summary"):
        qa_pairs.append({
            "question": "Tell me about yourself",
            "answer": profile_data["summary"]
        })
        
    # Add experience Q&A
    if profile_data.get("experience"):
        experience_text = "\n".join(profile_data["experience"])
        qa_pairs.append({
            "question": "What is your work experience?",
            "answer": experience_text
        })
        
    # Add education Q&A
    if profile_data.get("education"):
        education_text = "\n".join(profile_data["education"])
        qa_pairs.append({
            "question": "What is your educational background?",
            "answer": education_text
        })
        
    # Add skills Q&A
    if profile_data.get("skills"):
        skills_text = ", ".join(profile_data["skills"])
        qa_pairs.append({
            "question": "What are your key skills and competencies?",
            "answer": f"My key skills include: {skills_text}"
        })
    
    return qa_pairs

def save_linkedin_data(url: str, output_dir: str = "content/interviews") -> bool:
    """
    Scrapes LinkedIn profile and saves the Q&A data to a JSON file.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Scrape and convert the data
        profile_data = scrape_linkedin_profile(url)
        if not profile_data:
            return False
            
        qa_pairs = convert_to_qa_format(profile_data)
        
        # Save to JSON file
        output_file = os.path.join(output_dir, "linkedin_qa.json")
        with open(output_file, "w") as f:
            json.dump(qa_pairs, f, indent=2)
            
        return True
        
    except Exception as e:
        print(f"Error saving LinkedIn data: {e}")
        return False
