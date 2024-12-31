import PyPDF2
import io
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def extract_pdf_content(pdf_path: str) -> Dict:
    """Extract content from PDF and organize it into sections."""
    try:
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            content = ""
            for page in pdf_reader.pages:
                content += page.extract_text()

            # Split content into sections
            sections = {
                "summary": "",
                "experience": [],
                "education": [],
                "skills": []
            }

            # Parse content into sections
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                lower_line = line.lower()
                
                # Detect sections
                if "summary" in lower_line or "profile" in lower_line:
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = "summary"
                    current_content = []
                elif "experience" in lower_line or "employment" in lower_line:
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = "experience"
                    current_content = []
                elif "education" in lower_line:
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = "education"
                    current_content = []
                elif "skills" in lower_line or "competencies" in lower_line:
                    if current_section and current_content:
                        sections[current_section] = "\n".join(current_content)
                    current_section = "skills"
                    current_content = []
                elif current_section:
                    current_content.append(line)

            # Add the last section
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content)

            logger.info("Successfully extracted content from PDF")
            return sections

    except Exception as e:
        logger.error(f"Error extracting PDF content: {str(e)}")
        return {}
