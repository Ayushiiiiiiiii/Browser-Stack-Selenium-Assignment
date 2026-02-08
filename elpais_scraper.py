import os
import sys
import time
import json
import requests
from collections import Counter
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager

os.environ['WDM_LOG'] = '0'

class ElPaisScraper:
    def __init__(self, driver=None):  # ← Changed: Accept optional driver
        self.base_url = "https://elpais.com/opinion/editoriales/"
        self.driver = driver  # ← Use provided driver or None
        self.articles = []
        self.translated_headers = []

        load_dotenv()
        self.google_api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY")

        if not self.google_api_key:
            print("⚠ GOOGLE_TRANSLATE_API_KEY missing in .env. Translation will be skipped.")

        os.makedirs("article_images", exist_ok=True)

    def setup_local_driver(self):
        print("🚀 Launching Chrome...")
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--lang=es")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    def navigate_to_opinion_section(self):
        print("\n🌍 Opening El País Opinion section...")
        self.driver.get(self.base_url)

        try:
            btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )
            btn.click()
            print("✓ Cookies accepted")
        except:
            print("✓ No cookie popup or already accepted")

    def scrape_articles(self, num_articles=5):
        print(f"\n📰 Scraping top {num_articles} opinion articles...\n")
        
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
        )
        
        article_blocks = self.driver.find_elements(By.TAG_NAME, "article")
        count = 0

        for article in article_blocks:
            if count >= num_articles:
                break

            try:
                title_element = article.find_element(By.TAG_NAME, "h2")
                title = title_element.text.strip()
                
                link = article.find_element(By.TAG_NAME, "a").get_attribute("href")

                try:
                    content = article.find_element(By.TAG_NAME, "p").text.strip()
                except:
                    content = "No description available."

                image_url = None
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", article)
                    time.sleep(0.5)

                    sources = article.find_elements(By.TAG_NAME, "source")
                    if sources:
                        srcset = sources[0].get_attribute("srcset")
                        if srcset:
                            image_url = srcset.split(",")[0].split(" ")[0]
                    
                    if not image_url:
                        img_tag = article.find_element(By.TAG_NAME, "img")
                        image_url = (img_tag.get_attribute("src") or 
                                     img_tag.get_attribute("data-src"))
                except NoSuchElementException:
                    image_url = None

                count += 1
                data = {
                    "id": count,
                    "title": title,
                    "content": content,
                    "url": link,
                    "image_url": image_url
                }

                self.articles.append(data)
                print(f"{count}. {title}")
                
                if image_url:
                    self.download_image(image_url, count)
                else:
                    print("   ⚠ No image found for this article.")

            except Exception as e:
                print(f"⚠ Error processing article {count+1}: {e}")

    def download_image(self, url, article_id):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://elpais.com/"
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                ext = "jpg"
                if "webp" in url: ext = "webp"
                elif "png" in url: ext = "png"
                
                filename = f"article_images/article_{article_id}.{ext}"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"   ✅ Image saved: {filename}")
            else:
                print(f"   ❌ Failed to download image (Status: {response.status_code})")
        except Exception as e:
            print(f"   ❌ Image download error: {e}")

    def translate_headers(self):
        if not self.google_api_key:
            self.translated_headers = [a["title"] for a in self.articles]
            return

        print("\n🌐 Translating titles to English...")
        endpoint = "https://translation.googleapis.com/language/translate/v2"

        for article in self.articles:
            try:
                params = {
                    "q": article["title"],
                    "source": "es",
                    "target": "en",
                    "format": "text",
                    "key": self.google_api_key
                }
                res = requests.post(endpoint, params=params, timeout=10)
                translated = res.json()["data"]["translations"][0]["translatedText"]
                article["translated_title"] = translated
                self.translated_headers.append(translated)
                print(f"EN: {translated}")
            except:
                self.translated_headers.append(article["title"])
                print(f"❌ Translation failed for: {article['title']}")

    def analyze_word_frequency(self):
        print("\n📊 Word Frequency Analysis (Words repeated > 2 times):")
        words = []
        for title in self.translated_headers:
            clean_words = [w.strip(".,!?\"").lower() for w in title.split() if len(w) > 3]
            words.extend(clean_words)

        freq = Counter(words)
        repeated = {k: v for k, v in freq.items() if v > 2}

        if repeated:
            for word, count in repeated.items():
                print(f" - {word}: {count}")
        else:
            print(" No words found with count > 2.")

    def run(self, close_driver=True):  # ← Changed: Optional driver closing
        try:
            # Only setup driver if not provided
            if not self.driver:
                self.setup_local_driver()
            
            self.navigate_to_opinion_section()
            self.scrape_articles(5)
            self.translate_headers()
            self.analyze_word_frequency()
            
            with open("results.json", "w", encoding="utf-8") as f:
                json.dump(self.articles, f, indent=2, ensure_ascii=False)
            
            print("\n🎉 Task Complete!")
            return True
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
        finally:
            # Only close driver if we created it AND close_driver is True
            if self.driver and close_driver and not hasattr(self, 'external_driver'):
                self.driver.quit()

if __name__ == "__main__":
    scraper = ElPaisScraper()
    scraper.run()