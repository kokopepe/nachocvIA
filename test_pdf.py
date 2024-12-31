from utils.pdf_parser import extract_pdf_content
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Extract content from PDF
pdf_path = "attached_assets/Profile.pdf"
logger.info(f"Starting PDF content extraction from: {pdf_path}")

content = extract_pdf_content(pdf_path)
if content:
    logger.info("PDF content extraction succeeded")
    for section, data in content.items():
        logger.info(f"\n{section.upper()}:")
        logger.info(data[:200] + "..." if len(data) > 200 else data)
else:
    logger.error("PDF content extraction failed")

print("PDF content extraction complete")
