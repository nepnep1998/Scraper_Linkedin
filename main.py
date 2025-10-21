from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import json
import os
from dotenv import load_dotenv

class LinkedInScraper:
    def __init__(self):
        self.setup_driver()
        load_dotenv()
    
    def setup_driver(self):
        """Configura o ChromeDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--user-data-dir=./chrome_profile")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login_linkedin(self):
        """Faz login no LinkedIn (manual pela primeira vez)"""
        print("🔐 Por favor, faça login manualmente no LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        input("Pressione Enter após fazer login...")
    
    def scrape_profile(self, profile_url):
        """Coleta dados de um perfil específico"""
        print(f"📊 Coletando dados de: {profile_url}")
        
        self.driver.get(profile_url)
        time.sleep(3)
        
        profile_data = {
            "nome": self.get_element_text("h1"),
            "cargo": self.get_element_text(".text-body-medium"),
            "empresa": self.get_element_text(".experience-item__company"),
            "localizacao": self.get_element_text(".top-card-location"),
            "habilidades": self.get_skills()
        }
        
        return profile_data
    
    def get_element_text(self, selector):
        """Extrai texto de um elemento se existir"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return "Não encontrado"
    
    def get_skills(self):
        """Extrai habilidades do perfil"""
        skills = []
        try:
            skill_elements = self.driver.find_elements(By.CSS_SELECTOR, ".skill-badge")
            skills = [skill.text for skill in skill_elements]
        except:
            pass
        return skills
    
    def save_data(self, data, filename="dados_especialistas.json"):
        """Salva os dados em JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Dados salvos em {filename}")

# Exemplo de uso
if __name__ == "__main__":
    scraper = LinkedInScraper()
    
    try:
        # Login (apenas primeira vez)
        scraper.login_linkedin()
        
        # Lista de URLs para scraping (exemplo)
        profile_urls = [
            "https://www.linkedin.com/in/fernando-farias-pires-8b0491195/"
        ]
        
        all_data = []
        for url in profile_urls:
            data = scraper.scrape_profile(url)
            all_data.append(data)
            time.sleep(2)  # Respeitar o rate limiting
        
        scraper.save_data(all_data)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        scraper.driver.quit()