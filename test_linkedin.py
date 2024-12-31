from utils.linkedin_scraper import save_linkedin_data

# Test LinkedIn data extraction
url = "https://www.linkedin.com/in/ignacio-garc%C3%ADa-96a1a22/"
success = save_linkedin_data(url)
print(f"LinkedIn data extraction {'succeeded' if success else 'failed'}")
