import warnings
# Suppress all deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import os
import weaviate
import PyPDF2  # Changed from pypdf to PyPDF2
from tqdm import tqdm
from typing import List, Dict, Optional, Callable
import time
import re
import glob
import sys
import logging
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CV_Processor')

class CVProcessor:
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

    def __init_tech_skills(self):
        """Initialize the dictionary of tech skills and their variations"""
        self.tech_skills = {
            "Python": ["python3", "py"],
            "JavaScript": ["js", "es6", "node.js", "nodejs"],
            "Java": ["java8", "java11", "java17"],
            "C++": ["cpp", "c plus plus"],
            "C#": ["csharp", "c sharp", ".net"],
            "SQL": ["mysql", "postgresql", "oracle"],
            "React": ["reactjs", "react.js"],
            "Angular": ["angular.js", "angularjs"],
            "Vue.js": ["vuejs", "vue"],
            "Docker": ["containerization", "docker-compose"],
            "Kubernetes": ["k8s", "container orchestration"],
            "AWS": ["amazon web services", "ec2", "s3"],
            "Azure": ["microsoft azure", "azure cloud"],
            "GCP": ["google cloud", "google cloud platform"],
            "Git": ["github", "gitlab", "version control"],
            "CI/CD": ["continuous integration", "jenkins", "gitlab ci"],
            "Machine Learning": ["ml", "deep learning", "ai"],
            "Data Science": ["data analytics", "statistics"],
            "DevOps": ["sre", "site reliability"],
            "Agile": ["scrum", "kanban"]
        }

    def _ensure_schema(self):
        """Ensure the Weaviate schema exists"""
        try:
            # Check if schema exists
            schema = self.client.schema.get()
            logger.info(f"Current schema: {schema}")
            
            class_name = "CV"
            
            # Only create schema if it doesn't exist
            if not any(cls['class'] == class_name for cls in schema.get('classes', [])):
                logger.info(f"Creating new {class_name} schema")
                # Create schema
                class_obj = {
                    "class": class_name,
                    "description": "A CV document",
                    "vectorizer": "text2vec-transformers",
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "vectorizeClassName": False,
                            "model": "sentence-transformers/all-MiniLM-L6-v2",
                            "options": {
                                "waitForModel": True
                            }
                        }
                    },
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "The text content of the CV",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": False,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "skills",
                            "dataType": ["text[]"],
                            "description": "List of skills found in the CV",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": True,
                                    "vectorizePropertyName": False
                                }
                            }
                        },
                        {
                            "name": "filename",
                            "dataType": ["text"],
                            "description": "Name of the CV file",
                            "moduleConfig": {
                                "text2vec-transformers": {
                                    "skip": True,
                                    "vectorizePropertyName": False
                                }
                            }
                        }
                    ]
                }
                
                self.client.schema.create_class(class_obj)
                logger.info("Created CV schema in Weaviate")
                
                # Verify schema was created
                new_schema = self.client.schema.get()
                logger.info(f"Updated schema: {new_schema}")
            else:
                logger.info(f"{class_name} schema already exists")
            
        except Exception as e:
            logger.error(f"Failed to ensure schema: {str(e)}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """Extract text content from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {str(e)}")
            return None

    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        try:
            # Common programming languages and tools
            skills_to_find = {
                # Programming Languages
                'Python', 'Java', 'JavaScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Go',
                'Rust', 'TypeScript', 'Scala', 'R', 'MATLAB', 'Perl', 'Haskell', 'Lua', 'Julia',
                
                # Web Development
                'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
                'ASP.NET', 'Laravel', 'Express.js', 'jQuery', 'Bootstrap', 'Sass', 'Less',
                
                # Databases
                'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'Oracle', 'SQLite',
                'MariaDB', 'DynamoDB', 'Neo4j', 'Elasticsearch',
                
                # Cloud & DevOps
                'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub', 'GitLab',
                'Terraform', 'Ansible', 'Chef', 'Puppet', 'CircleCI', 'Travis CI',
                
                # Data Science & ML
                'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Pandas',
                'NumPy', 'Data Science', 'NLP', 'Computer Vision', 'AI', 'Neural Networks',
                
                # Mobile Development
                'Android', 'iOS', 'React Native', 'Flutter', 'Xamarin', 'SwiftUI', 'Kotlin Multiplatform',
                
                # Testing
                'JUnit', 'TestNG', 'Selenium', 'Cypress', 'Jest', 'Mocha', 'PyTest', 'Robot Framework',
                
                # Other Tools
                'Jira', 'Confluence', 'Slack', 'Trello', 'Agile', 'Scrum', 'Kanban'
            }

            # Convert text to lowercase for case-insensitive matching
            text_lower = text.lower()
            
            # Find skills with word boundaries
            found_skills = set()
            for skill in skills_to_find:
                # Try exact match with word boundaries
                pattern = r'\b' + re.escape(skill.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_skills.add(skill)
                    continue
                    
                # Try with common variations
                variations = [
                    skill.lower(),  # lowercase
                    skill.upper(),  # uppercase
                    skill.title(),  # title case
                    re.sub(r'[.\s]', '', skill.lower()),  # no spaces or dots
                    re.sub(r'\.js$', 'js', skill.lower()),  # handle .js
                    re.sub(r'js$', '.js', skill.lower())  # handle js
                ]
                
                for var in variations:
                    pattern = r'\b' + re.escape(var) + r'\b'
                    if re.search(pattern, text_lower):
                        found_skills.add(skill)
                        break

            logger.info(f"Found skills: {found_skills}")
            return list(found_skills)
            
        except Exception as e:
            logger.error(f"Failed to extract skills: {str(e)}")
            return []

    def process_directory(self, directory_path: str, progress_callback: Callable[[float], None] = None) -> None:
        """Process all PDFs in a directory"""
        try:
            # Get list of PDF files
            pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
            logger.info(f"Directory path: {directory_path}")
            logger.info(f"Directory exists: {os.path.exists(directory_path)}")
            logger.info(f"Directory contents: {os.listdir(directory_path)}")
            logger.info(f"Found PDF files: {pdf_files}")
            
            if not pdf_files:
                logger.warning(f"No PDF files found in {directory_path}")
                return
                
            logger.info(f"Found {len(pdf_files)} PDF files")
            
            # Clear existing data
            self.clear_database()
            logger.info("Cleared existing database")
            
            # Process each PDF
            for i, pdf_file in enumerate(pdf_files):
                try:
                    # Update progress
                    if progress_callback:
                        progress = float(i) / len(pdf_files)
                        progress_callback(progress)
                        logger.info(f"Processing file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_file)} (Progress: {progress*100:.1f}%)")

                    # Extract text from PDF
                    text = self.extract_text_from_pdf(pdf_file)
                    if not text:
                        logger.warning(f"No text extracted from {pdf_file}")
                        continue
                    logger.info(f"Successfully extracted text from {os.path.basename(pdf_file)}")
                        
                    # Extract skills
                    skills = self.extract_skills(text)
                    logger.info(f"Found skills in {os.path.basename(pdf_file)}: {skills}")
                    
                    # Create data object
                    properties = {
                        "content": text,
                        "skills": skills,
                        "filename": os.path.basename(pdf_file)
                    }
                    
                    # Store in Weaviate
                    try:
                        self.client.data_object.create(
                            class_name="CV",
                            data_object=properties
                        )
                        logger.info(f"Successfully stored {os.path.basename(pdf_file)} in Weaviate")
                    except Exception as e:
                        logger.error(f"Failed to store {pdf_file} in Weaviate: {str(e)}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Failed to process {pdf_file}: {str(e)}")
                    continue

            # Update final progress
            if progress_callback:
                progress_callback(1.0)
                logger.info("Finished processing all files")
                
            # Verify data was stored
            try:
                results = (
                    self.client.query
                    .get("CV", ["filename"])
                    .do()
                )
                if results and 'data' in results and 'Get' in results['data'] and 'CV' in results['data']['Get']:
                    stored_files = [cv['filename'] for cv in results['data']['Get']['CV']]
                    logger.info(f"Successfully stored {len(stored_files)} CVs: {stored_files}")
                else:
                    logger.warning("No CVs found in database after processing!")
            except Exception as e:
                logger.error(f"Failed to verify stored data: {str(e)}")
                
        except Exception as e:
            logger.error(f"Failed to process directory: {str(e)}")
            raise

    def clear_database(self) -> None:
        """Clear all objects from the database"""
        try:
            # First get all objects
            result = self.client.query.get(
                "CV",
                ["_additional {id}"]
            ).do()

            if result and 'data' in result and 'Get' in result['data'] and 'CV' in result['data']['Get']:
                objects = result['data']['Get']['CV']
                
                # Delete each object
                for obj in objects:
                    if '_additional' in obj and 'id' in obj['_additional']:
                        self.client.data_object.delete(
                            class_name="CV",
                            uuid=obj['_additional']['id']
                        )
                
                logger.info(f"Cleared {len(objects)} objects from database")
            else:
                logger.info("No objects found to clear")
                
        except Exception as e:
            logger.error(f"Failed to clear database: {str(e)}")
            raise

if __name__ == "__main__":
    processor = CVProcessor()
    
    # Wait for Weaviate to be ready
    time.sleep(5)
    
    # Process CVs
    processor.process_directory("data/cv")
