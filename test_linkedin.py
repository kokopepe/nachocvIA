from utils.linkedin_scraper import save_linkedin_data
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test LinkedIn data extraction
url = "https://www.linkedin.com/in/ignacio-garc%C3%ADa-96a1a22/"
logger.info(f"Starting LinkedIn data extraction from URL: {url}")

success = save_linkedin_data(url)
if success:
    logger.info("LinkedIn data extraction succeeded")
else:
    logger.error("LinkedIn data extraction failed")

print(f"LinkedIn data extraction {'succeeded' if success else 'failed'}")