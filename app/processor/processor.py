import warnings
# Suppress all deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import os
import weaviate
import pypdf
from tqdm import tqdm
from typing import List, Dict, Optional
import time
import re
import glob
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CV_Processor')

# Import config
import config

logger.info(f"Data directory: {config.DATA_DIR}")
logger.info(f"CV directory: {config.CV_DIR}")
logger.info(f"CV directory exists: {os.path.exists(config.CV_DIR)}")
if os.path.exists(config.CV_DIR):
    logger.info(f"CV directory contents: {os.listdir(config.CV_DIR)}")

class CVProcessor:
    def __init__(self, weaviate_url: str = None):
        """Initialize the CV processor with Weaviate client"""
        try:
            self.client = weaviate.Client(weaviate_url or config.WEAVIATE_URL)
            logger.info(f"Connected to Weaviate at {weaviate_url or config.WEAVIATE_URL}")
            self._ensure_schema()
        except Exception as e:
            logger.error(f"Failed to initialize CVProcessor: {str(e)}")
            raise

    def _ensure_schema(self):
        """Ensure the Weaviate schema exists"""
        try:
            class_obj = {
                "class": config.SCHEMA_CLASS_NAME,
                "vectorizer": "text2vec-transformers",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                    },
                    {
                        "name": "skills",
                        "dataType": ["text[]"],
                    },
                    {
                        "name": "filename",
                        "dataType": ["text"],
                    }
                ]
            }
            
            # Create schema if it doesn't exist
            if not self.client.schema.exists(config.SCHEMA_CLASS_NAME):
                logger.info("Creating Weaviate schema")
                self.client.schema.create_class(class_obj)
                logger.info("Schema created successfully")
        except Exception as e:
            logger.error(f"Error ensuring schema: {str(e)}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file"""
        try:
            logger.info(f"Extracting text from PDF: {pdf_path}")
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                logger.info(f"Text extracted successfully from PDF: {pdf_path}")
                return text
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {str(e)}")
            return ""

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text using improved keyword matching"""
        try:
            logger.info(f"Extracting skills from text")
            found_skills = set()
            text_lower = text.lower()
            
            # Create word boundaries for better matching
            text_lower = f" {text_lower} "
            
            for skill, keywords in self.tech_skills.items():
                for keyword in keywords:
                    # Create word boundary pattern
                    pattern = rf'\b{re.escape(keyword)}\b'
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        found_skills.add(skill)
                        break  # Found one keyword for this skill, move to next skill
            
            logger.info(f"Skills extracted successfully: {list(found_skills)}")
            return list(found_skills)
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return []

    def process_directory(self, directory_path: str, progress_callback=None):
        """Process all PDFs in a directory"""
        try:
            logger.info(f"Processing directory: {directory_path}")
            pdf_files = []
            for ext in ['.pdf', '.PDF']:
                pdf_files.extend(glob.glob(os.path.join(directory_path, f'**/*{ext}'), recursive=True))
            
            total_files = len(pdf_files)
            processed = 0

            for pdf_file in pdf_files:
                try:
                    # Extract text and skills
                    text_content = self.extract_text_from_pdf(pdf_file)
                    skills = self.extract_skills(text_content)
                    
                    # Get relative path for filename
                    rel_path = os.path.relpath(pdf_file, directory_path)
                    
                    # Store in Weaviate
                    properties = {
                        "content": text_content,
                        "filename": rel_path,
                        "skills": skills
                    }
                    
                    self.client.data_object.create(
                        data_object=properties,
                        class_name=config.SCHEMA_CLASS_NAME
                    )
                    
                    processed += 1
                    if progress_callback:
                        progress_callback(processed / total_files)
                        
                    logger.info(f"Successfully processed PDF: {pdf_file}")
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Error processing directory: {str(e)}")

    def clear_database(self):
        """Clear all objects from the database"""
        try:
            logger.info("Clearing database")
            self.client.schema.delete_all()
            self._ensure_schema()
            logger.info("Database cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            raise

    def __init_tech_skills(self):
        """Initialize tech skills dictionary"""
        self.tech_skills = {
            # Programming Languages
            "Python": ["python", "py"],
            "JavaScript": ["javascript", "js", "node.js", "nodejs", "node"],
            "Java": ["java", "spring", "hibernate"],
            "C++": ["c++", "cpp"],
            "TypeScript": ["typescript", "ts"],
            
            # Web Technologies
            "HTML": ["html", "html5"],
            "CSS": ["css", "css3", "sass", "scss", "less"],
            "React": ["react", "react.js", "reactjs"],
            "Angular": ["angular", "ng"],
            "Vue.js": ["vue", "vuejs", "vue.js"],
            
            # Databases
            "SQL": ["sql", "mysql", "postgresql", "oracle", "database"],
            "MongoDB": ["mongodb", "mongo", "nosql"],
            
            # Cloud & DevOps
            "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
            "Docker": ["docker", "container", "containerization"],
            "Kubernetes": ["kubernetes", "k8s"],
            "Git": ["git", "github", "gitlab", "version control"],
            "CI/CD": ["ci/cd", "jenkins", "gitlab ci", "github actions", "continuous integration", "continuous deployment"],
            
            # AI/ML
            "Machine Learning": ["machine learning", "ml", "scikit", "tensorflow", "pytorch", "deep learning"],
            "AI": ["artificial intelligence", "ai", "neural networks", "nlp"],
            "Data Science": ["data science", "pandas", "numpy", "data analysis", "jupyter"],
            
            # General
            "DevOps": ["devops", "sre", "site reliability"]
        }

    def __init__(self, weaviate_url: str = None):
        """Initialize the CV processor with Weaviate client"""
        try:
            self.client = weaviate.Client(weaviate_url or config.WEAVIATE_URL)
            logger.info(f"Connected to Weaviate at {weaviate_url or config.WEAVIATE_URL}")
            self._ensure_schema()
            self.__init_tech_skills()
        except Exception as e:
            logger.error(f"Failed to initialize CVProcessor: {str(e)}")
            raise

if __name__ == "__main__":
    processor = CVProcessor()
    
    # Wait for Weaviate to be ready
    time.sleep(10)
    
    # Process CVs from mounted volume
    cv_directory = "/app/data/CV_Brut"
    if os.path.exists(cv_directory):
        print(f"Processing CVs from {cv_directory}")
        processor.process_directory(cv_directory)
    else:
        print(f"Directory {cv_directory} not found")
