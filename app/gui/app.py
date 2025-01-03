import warnings
# Suppress all deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import streamlit as st
import weaviate
import os
import plotly.graph_objects as go
from typing import List, Dict
import base64
import sys
import glob
from pathlib import Path
import re
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CV_GUI')

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import config
from processor.processor import CVProcessor

logger.info(f"Data directory: {config.DATA_DIR}")
logger.info(f"CV directory: {config.CV_DIR}")
logger.info(f"CV directory exists: {os.path.exists(config.CV_DIR)}")
if os.path.exists(config.CV_DIR):
    logger.info(f"CV directory contents: {os.listdir(config.CV_DIR)}")

# Define tech skills dictionary with colors
TECH_SKILLS = {
    "Python": {"aliases": ["python3", "py"], "color": "blue"},
    "JavaScript": {"aliases": ["js", "es6", "node.js", "nodejs"], "color": "yellow"},
    "Java": {"aliases": ["java8", "java11", "java17"], "color": "orange"},
    "C++": {"aliases": ["cpp", "c plus plus"], "color": "pink"},
    "C#": {"aliases": ["csharp", "c sharp", ".net"], "color": "purple"},
    "SQL": {"aliases": ["mysql", "postgresql", "oracle"], "color": "green"},
    "React": {"aliases": ["reactjs", "react.js"], "color": "cyan"},
    "Angular": {"aliases": ["angular.js", "angularjs"], "color": "red"},
    "Vue.js": {"aliases": ["vuejs", "vue"], "color": "teal"},
    "Docker": {"aliases": ["containerization", "docker-compose"], "color": "blue"},
    "Kubernetes": {"aliases": ["k8s", "container orchestration"], "color": "violet"},
    "AWS": {"aliases": ["amazon web services", "ec2", "s3"], "color": "orange"},
    "Azure": {"aliases": ["microsoft azure", "azure cloud"], "color": "blue"},
    "GCP": {"aliases": ["google cloud", "google cloud platform"], "color": "green"},
    "Git": {"aliases": ["github", "gitlab", "version control"], "color": "orange"},
    "CI/CD": {"aliases": ["continuous integration", "jenkins", "gitlab ci"], "color": "purple"},
    "Machine Learning": {"aliases": ["ml", "deep learning", "ai"], "color": "blue"},
    "Data Science": {"aliases": ["data analytics", "statistics"], "color": "green"},
    "DevOps": {"aliases": ["sre", "site reliability"], "color": "red"},
    "Agile": {"aliases": ["scrum", "kanban"], "color": "teal"},
}

class CVAnalyzer:
    def __init__(self, weaviate_url: str = None):
        """Initialize CVAnalyzer with Weaviate client"""
        try:
            self.client = weaviate.Client(weaviate_url or config.WEAVIATE_URL)
            logger.info(f"Connected to Weaviate at {weaviate_url or config.WEAVIATE_URL}")
            # Test connection
            self.client.schema.get()
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {str(e)}")
            st.error(f"""
            ⚠️ Could not connect to Weaviate database. Make sure Weaviate is running locally.
            
            Run this command in a separate terminal to start Weaviate:
            ```
            docker run -d -p 8080:8080 semitechnologies/weaviate:1.21.2
            ```
            
            Error: {str(e)}
            """)
            st.stop()
            
        self.processor = CVProcessor(weaviate_url=config.WEAVIATE_URL)
        self.tech_skills = list(TECH_SKILLS.keys())

    def find_candidates_by_skills(self, skills: List[str], limit: int = 10):
        """Find candidates that have any of the selected skills"""
        try:
            if not skills:
                return []

            logger.info(f"Searching for candidates with skills: {skills}")

            # Get all objects to verify data
            all_objects = (
                self.client.query
                .get("CV", ["content", "skills", "filename"])
                .do()
            )
            
            if all_objects and 'data' in all_objects and 'Get' in all_objects['data'] and 'CV' in all_objects['data']['Get']:
                all_cvs = all_objects['data']['Get']['CV']
                logger.info(f"Total CVs in database: {len(all_cvs)}")
                for cv in all_cvs:
                    logger.info(f"CV {cv['filename']} has skills: {cv.get('skills', [])}")
            else:
                logger.warning("No CVs found in database!")
                return []

            # First try exact skill matches
            where_filter = {
                "path": ["skills"],
                "operator": "ContainsAny",
                "valueStringArray": skills
            }

            # Query Weaviate with the filter
            results = (
                self.client.query
                .get("CV", ["content", "skills", "filename"])
                .with_where(where_filter)
                .with_limit(limit)
                .do()
            )
            
            candidates = []
            if results and 'data' in results and 'Get' in results['data'] and 'CV' in results['data']['Get']:
                candidates = results['data']['Get']['CV']
                logger.info(f"Found {len(candidates)} candidates by exact skills")
                for candidate in candidates:
                    logger.info(f"Candidate {candidate['filename']} matched by exact skills")
            else:
                logger.warning("No candidates found by exact skills")

            # If no results, try fuzzy content search
            if not candidates:
                content_filter = {
                    "operator": "Or",
                    "operands": [
                        {
                            "path": ["content"],
                            "operator": "Like",
                            "valueString": f"*{skill.lower()}*"
                        } for skill in skills
                    ]
                }

                results = (
                    self.client.query
                    .get("CV", ["content", "skills", "filename"])
                    .with_where(content_filter)
                    .with_limit(limit)
                    .do()
                )

                if results and 'data' in results and 'Get' in results['data'] and 'CV' in results['data']['Get']:
                    candidates = results['data']['Get']['CV']
                    logger.info(f"Found {len(candidates)} candidates by fuzzy search")
                    for candidate in candidates:
                        logger.info(f"Candidate {candidate['filename']} matched by fuzzy search")
                else:
                    logger.warning("No candidates found by fuzzy search")

            if not candidates:
                logger.warning("No candidates found with either method")
                return []

            # Calculate matching skills for each candidate
            for candidate in candidates:
                candidate_skills = set(candidate.get('skills', []))
                matching_skills = candidate_skills.intersection(set(skills))
                candidate['matching_count'] = len(matching_skills)
                logger.info(f"Candidate {candidate['filename']} has {len(matching_skills)} matching skills: {matching_skills}")

            # Sort by number of matching skills
            candidates.sort(key=lambda x: x['matching_count'], reverse=True)
            
            return candidates
            
        except Exception as e:
            logger.error(f"Failed to find candidates for skills {skills}: {str(e)}")
            return []

    def get_skill_distribution(self):
        """Get distribution of skills across all CVs"""
        try:
            results = (
                self.client.query
                .get("CV", ["skills"])
                .do()
            )
            
            if not results or 'data' not in results or 'Get' not in results['data'] or 'CV' not in results['data']['Get']:
                return {}
                
            # Count skills
            skill_counts = {}
            for cv in results['data']['Get']['CV']:
                if not cv.get('skills'):
                    continue
                for skill in cv['skills']:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1
                    
            return skill_counts
            
        except Exception as e:
            logger.error(f"Failed to get skill distribution: {str(e)}")
            return {}

    def get_cv_count(self):
        """Get the total number of CVs in the database"""
        try:
            results = (
                self.client.query
                .aggregate("CV")
                .with_meta_count()
                .do()
            )
            
            if results and 'data' in results and 'Aggregate' in results['data'] and 'CV' in results['data']['Aggregate']:
                return results['data']['Aggregate']['CV'][0]['meta']['count']
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get CV count: {str(e)}")
            return 0

    def process_cv_directory(self, directory_path: str, progress_bar):
        """Process all PDFs in a directory"""
        try:
            # Process the CVs
            self.processor.process_directory(directory_path, progress_bar.progress)
            # Force refresh the CV count
            st.session_state.cv_count = self.get_cv_count()
            st.session_state.cv_processed = True
        except Exception as e:
            logger.error(f"Failed to process CV directory: {str(e)}")
            raise

    def clear_database(self):
        """Clear all data from the database"""
        try:
            self.processor.clear_database()
            st.session_state.cv_processed = False
            st.session_state.cv_count = 0
        except Exception as e:
            logger.error(f"Failed to clear database: {str(e)}")
            raise

def highlight_skills(text: str, selected_skills: List[str]) -> str:
    """Highlight skills in text with their respective colors"""
    highlighted = text
    # Sort skills by length (longest first) to avoid partial matches
    sorted_skills = sorted(selected_skills, key=len, reverse=True)
    for skill in sorted_skills:
        color = TECH_SKILLS[skill]["color"]
        pattern = re.compile(re.escape(skill), re.IGNORECASE)
        highlighted = pattern.sub(f'**:{color}[{skill}]**', highlighted)
    return highlighted

def get_cv_download_link(filename: str, directory_path: str) -> str:
    """Generate a download link for a CV file"""
    try:
        file_path = os.path.join(directory_path, filename)
        with open(file_path, "rb") as f:
            bytes_data = f.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download {filename}</a>'
        return href
    except Exception as e:
        logger.error(f"Failed to generate download link for {filename}: {str(e)}")
        return ""

def show_documentation():
    """Show documentation in the sidebar"""
    st.sidebar.markdown("""
    # CV Analysis Tool Help
    
    ## Quick Start
    1. Place your CV files in the `data/cv` directory
    2. Click 'Process CV Directory' to analyze them
    3. Select skills to find matching candidates
    
    ## Features
    - Process PDF CVs automatically
    - Extract skills using AI
    - Search candidates by required skills
    - View skill distribution
    - Download original CVs
    
    ## Directory Structure
    ```
    data/
    └── cv/
        └── your_cv_files.pdf
    ```
    
    ## Common Issues
    1. **CVs not found**: Check if files are in `data/cv` directory
    2. **Skills not detected**: Ensure PDFs are text-based
    3. **No results**: Try selecting different skills
    
    ## Need More Help?
    Contact support at support@example.com
    """)

def main():
    # Set page config at the very beginning
    st.set_page_config(
        page_title="CV Analysis Tool",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'selected_skills' not in st.session_state:
        st.session_state.selected_skills = []
    if 'cv_processed' not in st.session_state:
        st.session_state.cv_processed = False
    if 'cv_count' not in st.session_state:
        st.session_state.cv_count = 0

    # Initialize CV analyzer
    analyzer = CVAnalyzer()
    
    # Show documentation in sidebar
    show_documentation()
    
    # Main content
    st.title("CV Analysis Tool 📄")
    
    col1, col2 = st.columns(2)
    
    # Process CV directory
    if col1.button("Process CV Directory", use_container_width=True):
        try:
            progress_bar = st.progress(0)
            analyzer.process_cv_directory(config.CV_DIR, progress_bar)
            st.success("✅ Successfully processed CV directory!")
            time.sleep(1)  # Give time for the success message to show
            st.experimental_rerun()  # Rerun to update the interface
        except Exception as e:
            st.error(f"❌ Failed to process CV directory: {str(e)}")
    
    # Clear database
    if col2.button("Clear Database", use_container_width=True):
        try:
            analyzer.clear_database()
            st.session_state.selected_skills = []  # Clear selected skills
            st.success("✅ Successfully cleared database!")
            time.sleep(1)  # Give time for the success message to show
            st.experimental_rerun()  # Rerun to update the interface
        except Exception as e:
            st.error(f"❌ Failed to clear database: {str(e)}")
    
    # Show CV count
    cv_count = st.session_state.cv_count
    st.write(f"📊 Total CVs in database: {cv_count}")
    
    if cv_count > 0:
        # Get skill distribution
        skill_dist = analyzer.get_skill_distribution()
        
        # Plot skill distribution
        if skill_dist:
            fig = go.Figure(data=[
                go.Bar(
                    x=list(skill_dist.keys()),
                    y=list(skill_dist.values()),
                    text=list(skill_dist.values()),
                    textposition='auto',
                )
            ])
            
            fig.update_layout(
                title="Skill Distribution Across CVs",
                xaxis_title="Skills",
                yaxis_title="Number of CVs",
                showlegend=False,
                height=400  # Fixed height for better visibility
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Skill selection
        st.subheader("🔍 Find Candidates by Skills")
        
        # Create columns for skill checkboxes
        cols = st.columns(4)
        all_skills = sorted(TECH_SKILLS.keys())
        skills_per_col = len(all_skills) // 4 + (1 if len(all_skills) % 4 else 0)
        
        # Reset selected skills if requested
        if st.button("Clear Selected Skills", use_container_width=True):
            st.session_state.selected_skills = []
            st.experimental_rerun()
        
        # Display skill checkboxes in columns
        for i, col in enumerate(cols):
            with col:
                start_idx = i * skills_per_col
                end_idx = min((i + 1) * skills_per_col, len(all_skills))
                st.write("**Skills Group {}**".format(i + 1))
                for skill in all_skills[start_idx:end_idx]:
                    if st.checkbox(skill, key=f"skill_{skill}", value=skill in st.session_state.selected_skills):
                        if skill not in st.session_state.selected_skills:
                            st.session_state.selected_skills.append(skill)
                    elif skill in st.session_state.selected_skills:
                        st.session_state.selected_skills.remove(skill)
        
        # Find candidates for selected skills
        if st.session_state.selected_skills:
            candidates = analyzer.find_candidates_by_skills(st.session_state.selected_skills)
            
            if candidates:
                st.write(f"Found {len(candidates)} candidates with selected skills:")
                
                for candidate in candidates:
                    matching_skills = [s for s in candidate['skills'] if s in st.session_state.selected_skills]
                    other_skills = [s for s in candidate['skills'] if s not in st.session_state.selected_skills]
                    
                    with st.expander(f"📄 {candidate['filename']} ({candidate['matching_count']} matching skills)"):
                        # Show matching skills first, then other skills
                        if matching_skills:
                            st.write("**Matching Skills:**", ", ".join(matching_skills))
                        if other_skills:
                            st.write("**Other Skills:**", ", ".join(other_skills))
                        
                        # Show highlighted content
                        highlighted_content = highlight_skills(candidate['content'], st.session_state.selected_skills)
                        st.markdown(highlighted_content)
                        
                        # Add download link
                        download_link = get_cv_download_link(candidate['filename'], config.CV_DIR)
                        st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.warning("No candidates found with selected skills.")
        else:
            st.info("Select one or more skills to find matching candidates.")
    else:
        st.warning("No CVs in database. Please process CV directory first.")

if __name__ == "__main__":
    main()
