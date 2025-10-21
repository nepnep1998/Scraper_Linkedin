from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import pandas as pd
import re
from urllib.parse import unquote

class LinkedInScraperPro:
    def __init__(self):
        self.setup_driver()
        self.wait = WebDriverWait(self.driver, 15)
    
    def setup_driver(self):
        """Configura o ChromeDriver"""
        print("🔧 CONFIGURANDO NAVEGADOR...")
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✅ NAVEGADOR CONFIGURADO!")
            
        except Exception as e:
            print(f"❌ Erro ao configurar navegador: {e}")
            raise

    def login_linkedin(self):
        """Faz login no LinkedIn"""
        print("\n🔐 INICIANDO LOGIN")
        print("=" * 40)
        
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        print("📋 INSTRUÇÕES:")
        print("1. Faça login MANUALMENTE")
        print("2. Aguarde a página inicial") 
        print("3. Pressione ENTER")
        print("=" * 40)
        
        input("✅ PRESSIONE ENTER APÓS LOGIN...")
        return True

    def get_dynamic_profile_data(self, profile_url):
        """Coleta dados APENAS do perfil, ignorando feed/interface"""
        try:
            print(f"\n🚀 ACESSANDO PERFIL: {profile_url}")
            self.driver.get(profile_url)
            time.sleep(5)
            
            # 🎯 VERIFICA SE ESTÁ NA PÁGINA CORRETA
            if not self.is_profile_page():
                print("❌ Não está na página do perfil! Redirecionando...")
                return None
            
            # Foca apenas na área principal do perfil
            profile_section = self.get_profile_main_section()
            
            if not profile_section:
                print("❌ Não conseguiu encontrar a seção principal do perfil")
                return None
            
            # Coleta dados APENAS da seção do perfil
            profile_data = {
                "url": profile_url,
                "nome": self.get_profile_name(profile_section),
                "cargo_atual": self.get_profile_headline(profile_section),
                "localizacao": self.get_profile_location(profile_section),
                "sobre": self.get_profile_about(profile_section),
                "experiencia_principal": self.get_profile_experience(profile_section),
                "formacao_academica": self.get_profile_education(profile_section),
                "competencias_principais": self.get_precise_skills(),  # 🆕 MÉTODO PRECISO
                "coletado_em": time.strftime("%d/%m/%Y %H:%M:%S")
            }
            
            print("✅ DADOS COLETADOS DO PERFIL!")
            return profile_data
            
        except Exception as e:
            print(f"❌ ERRO: {e}")
            return None

    def is_profile_page(self):
        """Verifica se está realmente na página de perfil"""
        try:
            # Verifica se tem elementos específicos de perfil
            profile_indicators = [
                "//main[contains(@class, 'scaffold-layout__main')]",
                "//div[contains(@class, 'pv-profile-page')]",
                "//section[contains(@class, 'pv-profile-section')]"
            ]
            
            for indicator in profile_indicators:
                if len(self.driver.find_elements(By.XPATH, indicator)) > 0:
                    return True
            
            # Verifica pela URL
            current_url = self.driver.current_url
            if '/in/' in current_url and 'feed' not in current_url:
                return True
                
            return False
        except:
            return False

    def get_profile_main_section(self):
        """Encontra a seção principal do perfil"""
        try:
            # Tenta encontrar a área principal do perfil
            main_selectors = [
                "main.scaffold-layout__main",
                "div.pv-profile-page",
                "div.profile",
                "#main-content",
                "main"
            ]
            
            for selector in main_selectors:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element
                except:
                    continue
            
            # Fallback: pega o body mas filtra depois
            return self.driver.find_element(By.TAG_NAME, "body")
        except:
            return None

    def get_profile_name(self, profile_section):
        """Busca nome APENAS na seção do perfil"""
        try:
            name_selectors = [
                ".//h1[contains(@class, 'text-heading-xlarge')]",
                ".//h1[contains(@class, 'top-card-layout__title')]",
                ".//h1"
            ]
            
            for selector in name_selectors:
                try:
                    element = profile_section.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text and len(text) > 1:
                        return text
                except:
                    continue
            return "Não informado"
        except:
            return "Não informado"

    def get_profile_headline(self, profile_section):
        """Busca cargo APENAS na seção do perfil"""
        try:
            headline_selectors = [
                ".//div[contains(@class, 'text-body-medium')]",
                ".//div[contains(@class, 'top-card-layout__headline')]",
                ".//h2[contains(@class, 'mt1')]"
            ]
            
            for selector in headline_selectors:
                try:
                    element = profile_section.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text and len(text) > 5:
                        return text
                except:
                    continue
            return "Não informado"
        except:
            return "Não informado"

    def get_profile_location(self, profile_section):
        """Busca localização APENAS na seção do perfil"""
        try:
            # Busca específica na área de informações básicas
            location_selectors = [
                ".//span[contains(@class, 'text-body-small')]",
                ".//div[contains(@class, 'pv-text-details__left-panel')]//span"
            ]
            
            for selector in location_selectors:
                try:
                    elements = profile_section.find_elements(By.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if (text and 
                            any(loc in text.lower() for loc in ['manaus', 'amazonas', 'brasil', 'brazil', 'portugal', 'são paulo', 'rio']) and
                            not any(exclude in text.lower() for exclude in ['conexões', 'seguidores', 'contato'])):
                            return text
                except:
                    continue
            return "Localização não encontrada"
        except:
            return "Localização não encontrada"

    def get_profile_about(self, profile_section):
        """Busca seção SOBRE APENAS no perfil"""
        try:
            # Busca pela seção "Sobre" específica
            about_selectors = [
                ".//section[.//h2[contains(., 'Sobre') or contains(., 'About')]]",
                ".//div[contains(@id, 'about')]",
                ".//div[contains(@class, 'pv-about-section')]"
            ]
            
            for selector in about_selectors:
                try:
                    about_section = profile_section.find_element(By.XPATH, selector)
                    # Pega todo o texto da seção
                    text = about_section.text.strip()
                    
                    # Remove o título "Sobre" e limpa
                    lines = text.split('\n')
                    clean_lines = []
                    for line in lines:
                        line_clean = line.strip()
                        if (line_clean and 
                            line_clean.lower() not in ['sobre', 'about'] and
                            len(line_clean) > 20):
                            clean_lines.append(line_clean)
                    
                    if clean_lines:
                        return '\n'.join(clean_lines)
                except:
                    continue
            return "Seção não encontrada"
        except:
            return "Seção não encontrada"

    def get_profile_experience(self, profile_section):
        """Busca EXPERIÊNCIA APENAS no perfil"""
        try:
            experience_data = []
            
            # Busca pela seção de experiência
            exp_selectors = [
                ".//section[.//h2[contains(., 'Experiência') or contains(., 'Experience')]]",
                ".//div[contains(@id, 'experience')]",
                ".//div[contains(@class, 'pv-experience-section')]"
            ]
            
            for selector in exp_selectors:
                try:
                    exp_section = profile_section.find_element(By.XPATH, selector)
                    
                    # Busca itens de experiência
                    items = exp_section.find_elements(By.XPATH, ".//li | .//div[contains(@class, 'pv-entity')]")[:5]
                    
                    for item in items:
                        text = item.text.strip()
                        if text and len(text) > 30:
                            # Filtra apenas conteúdo relevante
                            clean_text = self.clean_experience_text(text)
                            if clean_text and clean_text not in experience_data:
                                experience_data.append(clean_text)
                    
                    if experience_data:
                        return experience_data
                except:
                    continue
            
            return ["Experiência não encontrada"]
        except:
            return ["Erro ao buscar experiência"]

    def get_profile_education(self, profile_section):
        """Busca FORMAÇÃO APENAS no perfil"""
        try:
            education_data = []
            
            # Busca pela seção de educação
            edu_selectors = [
                ".//section[.//h2[contains(., 'Formação acadêmica') or contains(., 'Education')]]",
                ".//div[contains(@id, 'education')]",
                ".//div[contains(@class, 'pv-education-section')]"
            ]
            
            for selector in edu_selectors:
                try:
                    edu_section = profile_section.find_element(By.XPATH, selector)
                    
                    # Busca itens de educação
                    items = edu_section.find_elements(By.XPATH, ".//li | .//div[contains(@class, 'pv-entity')]")[:5]
                    
                    for item in items:
                        text = item.text.strip()
                        if text and len(text) > 20:
                            clean_text = self.clean_education_text(text)
                            if clean_text and clean_text not in education_data:
                                education_data.append(clean_text)
                    
                    if education_data:
                        return education_data
                except:
                    continue
            
            return ["Formação não encontrada"]
        except:
            return ["Erro ao buscar formação"]

    def get_precise_skills(self):
        """🆕 MÉTODO PRECISO - Foca APENAS na seção de competências"""
        try:
            print("🛠️  Buscando COMPETÊNCIAS (abordagem precisa)...")
            
            # 🎯 ESTRATÉGIA 1: Busca DIRETA pela seção de competências
            skills_section = self.find_skills_section()
            if not skills_section:
                return ["Competências não encontradas"]
            
            # 🎯 ESTRATÉGIA 2: Expande a seção se necessário
            self.expand_skills_section(skills_section)
            time.sleep(2)
            
            # 🎯 ESTRATÉGIA 3: Busca competências DENTRO da seção correta
            skills_data = self.extract_skills_from_section(skills_section)
            
            return skills_data[:10] if skills_data else ["Competências não encontradas"]
            
        except Exception as e:
            print(f"⚠️  Erro em competências precisas: {e}")
            return ["Erro ao buscar competências"]

    def find_skills_section(self):
        """Encontra a seção específica de competências"""
        try:
            # 🎯 SELEÇÃO PRECISA - APENAS seções que SÃO competências
            skills_selectors = [
                # Seção principal de competências
                "//section[.//h2[contains(., 'Competências') or contains(., 'Skills') or contains(., 'Conhecimentos')]]",
                "//div[contains(@id, 'skills')]",
                
                # Seções com estrutura de competências
                "//section[.//div[contains(@class, 'pv-skill-category-entity')]]",
                "//section[.//span[contains(@class, 'pv-skill-category-entity__name')]]",
                
                # Área de competências do perfil
                "//div[contains(@class, 'pv-profile-content')]//section[.//*[contains(text(), 'Mapas') or contains(text(), 'SIG')]]"
            ]
            
            for selector in skills_selectors:
                try:
                    section = self.driver.find_element(By.XPATH, selector)
                    print(f"✅ Seção de competências encontrada: {selector}")
                    return section
                except:
                    continue
            
            print("❌ Nenhuma seção de competências encontrada")
            return None
            
        except Exception as e:
            print(f"⚠️  Erro ao encontrar seção: {e}")
            return None

    def expand_skills_section(self, skills_section):
        """Expande a seção de competências se houver botões 'ver mais'"""
        try:
            # Busca botões de expandir DENTRO da seção de competências
            expand_buttons = skills_section.find_elements(By.XPATH, 
                ".//button[contains(., 'ver mais') or contains(., 'Ver mais') or contains(., 'see more') or contains(., 'Exibir todas')]"
            )
            
            for button in expand_buttons:
                try:
                    if button.is_displayed():
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                        print("✅ Seção de competências expandida")
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Erro ao expandir seção: {e}")

    def extract_skills_from_section(self, skills_section):
        """Extrai competências APENAS da seção correta - FOCANDO NOS SPANS ESPECÍFICOS"""
        try:
            skills_data = []
            
            # 🎯 BUSCA ESPECÍFICA PELOS SPANS EXATOS DO LINKEDIN
            span_selectors = [
                ".//span[@aria-hidden='true']",
                ".//span[contains(@class, 'pv-skill-category-entity__name-text')]"
            ]
            
            print("🔍 Buscando spans com nomes de competências...")
            
            for selector in span_selectors:
                try:
                    elements = skills_section.find_elements(By.XPATH, selector)
                    print(f"📌 Encontrados {len(elements)} elementos span")
                    
                    for element in elements:
                        text = element.text.strip()
                        if text and self.is_valid_skill_title(text):
                            # Verifica se é um nome de competência válido
                            skills_data.append(text)
                            print(f"✅ Competência encontrada: {text}")
                    
                except Exception as e:
                    print(f"⚠️  Erro ao buscar com {selector}: {e}")
                    continue
            
            # 🎯 ALTERNATIVA: Busca por textos específicos de competências
            if not skills_data:
                print("🔍 Tentando busca alternativa por competências...")
                alternative_selectors = [
                    ".//*[contains(text(), 'Mapas')]",
                    ".//*[contains(text(), 'SIG')]",
                    ".//*[contains(text(), 'Análise espacial')]",
                    ".//h3[contains(@class, 't-16')]",
                    ".//div[contains(@class, 'pv-skill-category-entity__name')]"
                ]
                
                for selector in alternative_selectors:
                    try:
                        elements = skills_section.find_elements(By.XPATH, selector)
                        for element in elements:
                            text = element.text.strip()
                            if text and self.is_valid_skill_title(text):
                                skills_data.append(text)
                                print(f"✅ Competência alternativa: {text}")
                    except:
                        continue
            
            # 🎯 FILTRAGEM FINAL - Remove duplicatas e limpa
            unique_skills = list(dict.fromkeys(skills_data))
            clean_skills = [skill for skill in unique_skills if self.is_clean_skill(skill)]
            
            print(f"✅ {len(clean_skills)} competências encontradas")
            return clean_skills
            
        except Exception as e:
            print(f"⚠️  Erro ao extrair competências: {e}")
            return []

    def is_valid_skill_title(self, text):
        """Verifica se é um título de competência válido"""
        if not text or len(text) < 2 or len(text) > 50:
            return False
        
        text_lower = text.lower()
        
        # 🚫 EXCLUSÕES ABSOLUTAS - Interface e seções
        hard_excludes = [
            'mensagens', 'notificações', 'eu', 'para negócios', 'premium',
            'conexões', 'comentário', 'seguem esta página', 'experimente',
            'ver mais', 'exibir todas', 'recomendar competência',
            'todos', 'competências', 'skills', 'conhecimentos',
            'recomendar', 'experiências', 'experiência', 'recomendações'
        ]
        
        if any(exclude in text_lower for exclude in hard_excludes):
            return False
        
        # ✅ DEVE SER UM NOME DE COMPETÊNCIA
        return (
            len(text.split()) <= 5 and           # Máximo 5 palavras
            not text.isdigit() and               # Não é só número
            not text[0].isdigit() and            # Não começa com número
            any(char.isalpha() for char in text) # Tem pelo menos uma letra
        )

    def is_clean_skill(self, text):
        """Limpeza final da competência"""
        # Remove números no início (ex: "1. JavaScript" → "JavaScript")
        clean_text = re.sub(r'^\d+\.\s*', '', text.strip())
        
        # Remove textos muito curtos após limpeza
        if len(clean_text) < 2:
            return False
        
        # Remove competências que são nomes de empresas/universidades
        company_indicators = ['universidade', 'faculdade', 'colégio', 'escola', 'instituto']
        if any(indicator in clean_text.lower() for indicator in company_indicators):
            return False
        
        return clean_text

    def clean_experience_text(self, text):
        """Limpa texto de experiência"""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if (line_clean and 
                len(line_clean) > 5 and
                not any(exclude in line_clean.lower() for exclude in [
                    'conectar', 'seguir', 'ver mais', '...', 'mensagens',
                    'atualizações do feed', 'feed', 'notificações', 'início', 
                    'minha rede', 'atualização de rede'
                ])):
                clean_lines.append(line_clean)
        
        return ' | '.join(clean_lines[:4]) if clean_lines else None

    def clean_education_text(self, text):
        """Limpa texto de educação"""
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if (line_clean and 
                len(line_clean) > 5 and
                not any(exclude in line_clean.lower() for exclude in [
                    'conectar', 'seguir', 'ver mais', '...', 'mensagens',
                    'atualizações do feed', 'feed', 'notificações', 'início', 
                    'minha rede', 'atualização de rede'
                ])):
                clean_lines.append(line_clean)
        
        return ' | '.join(clean_lines[:3]) if clean_lines else None

    def filter_interface_content(self, data_list):
        """Filtra conteúdo de interface como 'atualizações do feed'"""
        if not data_list or data_list[0] in ["Experiência não encontrada", "Formação não encontrada"]:
            return data_list
        
        filtered_data = []
        for item in data_list:
            # Remove itens que contêm padrões de interface/feed
            if not any(pattern in item.lower() for pattern in [
                'atualizações do feed', 
                'feed', 
                'notificações',
                'início', 
                'minha rede',
                'atualização de rede'
            ]):
                filtered_data.append(item)
        
        return filtered_data if filtered_data else ["Não informado"]

    def show_detailed_results(self, profile_data):
        """Mostra resultados formatados"""
        print("\n" + "=" * 70)
        print("📊 DADOS REAIS DO PERFIL")
        print("=" * 70)
        
        print(f"👤 NOME: {profile_data.get('nome', 'N/A')}")
        print(f"💼 CARGO ATUAL: {profile_data.get('cargo_atual', 'N/A')}")
        print(f"📍 LOCALIZAÇÃO: {profile_data.get('localizacao', 'N/A')}")
        
        sobre = profile_data.get('sobre', 'N/A')
        print(f"\n📝 SOBRE:")
        print("-" * 40)
        if sobre != "N/A" and sobre != "Seção não encontrada":
            print(f"   {sobre}")
        else:
            print("   Não informado")
        print("-" * 40)
        
        # EXPERIÊNCIA - COM FILTRO
        experiencias = self.filter_interface_content(profile_data.get('experiencia_principal', []))
        print(f"\n💼 EXPERIÊNCIA ({len(experiencias)}):")
        print("-" * 40)
        if experiencias and experiencias[0] != "Não informado":
            for i, exp in enumerate(experiencias, 1):
                print(f"   {i}. {exp}")
        else:
            print("   Não informado")
        print("-" * 40)
        
        # FORMAÇÃO - COM FILTRO
        formacao = self.filter_interface_content(profile_data.get('formacao_academica', []))
        print(f"\n🎓 FORMAÇÃO ({len(formacao)}):")
        print("-" * 40)
        if formacao and formacao[0] != "Não informado":
            for i, edu in enumerate(formacao, 1):
                print(f"   {i}. {edu}")
        else:
            print("   Não informado")
        print("-" * 40)
        
        # 🆕 COMPETÊNCIAS - PRECISAS
        competencias = profile_data.get('competencias_principais', [])
        print(f"\n🛠️  COMPETÊNCIAS:")
        print("-" * 40)
        if competencias and competencias[0] not in ["Competências não encontradas", "Erro ao buscar competências"]:
            for i, skill in enumerate(competencias, 1):
                print(f"   🎯 {skill}")
                if i < len(competencias):  # Linha em branco entre competências
                    print()
        else:
            print("   Não informado")
        print("-" * 40)
        
        print("=" * 70)

    def save_data(self, data, filename="linkedin_data.json"):
        """Salva dados em JSON"""
        try:
            existing_data = []
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            if isinstance(data, list):
                existing_data.extend(data)
            else:
                existing_data.append(data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Dados salvos: {filename}")
            
        except Exception as e:
            print(f"⚠️  Erro ao salvar: {e}")

    def close(self):
        """Fecha o navegador"""
        try:
            self.driver.quit()
            print("🔚 NAVEGADOR FECHADO")
        except:
            pass

# PROGRAMA PRINCIPAL
def main():
    print("=" * 50)
    print("🚀 LINKEDIN SCRAPER - COMPETÊNCIAS PRECISAS")
    print("🎯 Foca APENAS na seção correta de competências")
    print("=" * 50)
    
    scraper = None
    
    try:
        scraper = LinkedInScraperPro()
        
        print("\n🔐 FAZENDO LOGIN...")
        scraper.login_linkedin()
        
        while True:
            print("\n" + "=" * 40)
            print("🎯 MENU PRINCIPAL")
            print("=" * 40)
            print("1. 🔍 Coletar perfil único")
            print("2. 🚪 Sair")
            print("=" * 40)
            
            opcao = input("👉 Opção: ").strip()
            
            if opcao == "1":
                url = input("🔗 URL do perfil: ").strip()
                if url:
                    data = scraper.get_dynamic_profile_data(url)
                    if data:
                        scraper.save_data(data)
                        scraper.show_detailed_results(data)
                    else:
                        print("❌ Falha na coleta - verifique a URL")
                else:
                    print("❌ URL vazia")
            
            elif opcao == "2":
                print("👋 Saindo...")
                break
            
            else:
                print("❌ Opção inválida")
        
    except Exception as e:
        print(f"💥 ERRO: {e}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()