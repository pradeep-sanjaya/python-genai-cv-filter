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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CV_GUI')

# Add parent directory to Python path for imports
import config
from processor.processor import CVProcessor

logger.info(f"Data directory: {config.DATA_DIR}")
logger.info(f"CV directory: {config.CV_DIR}")
logger.info(f"CV directory exists: {os.path.exists(config.CV_DIR)}")
if os.path.exists(config.CV_DIR):
    logger.info(f"CV directory contents: {os.listdir(config.CV_DIR)}")

# Import the folder uploader component
# from components.streamlit_folder_upload.streamlit_folder_upload import folder_uploader

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
        # Get tech skills from processor
        self.tech_skills = list(self.processor.tech_skills.keys())

    def find_best_candidates(self, selected_skills: List[str], limit: int = 5) -> List[Dict]:
        """Find the best candidates based on selected skills (AND operator)"""
        if not selected_skills:
            return []

        try:
            # Build a query that requires ALL selected skills
            result = (
                self.client.query
                .get("Resume", ["filename", "skills", "content"])
                .with_where({
                    "path": ["skills"],
                    "operator": "ContainsAll",
                    "valueStringArray": selected_skills
                })
                .with_limit(limit)
                .do()
            )

            if result and "data" in result and "Get" in result["data"] and "Resume" in result["data"]["Get"]:
                return result["data"]["Get"]["Resume"]
            return []
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
            st.error(f"Error querying database: {str(e)}")
            return []

    def get_skill_distribution(self) -> Dict[str, int]:
        """Get distribution of skills across all CVs"""
        try:
            result = (
                self.client.query
                .get("Resume", ["skills"])
                .do()
            )
            
            if not result or "data" not in result or "Get" not in result["data"] or "Resume" not in result["data"]["Get"]:
                return {}

            # Count occurrences of each skill
            skill_counts = {}
            for cv in result["data"]["Get"]["Resume"]:
                if cv.get("skills"):
                    for skill in cv["skills"]:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            return skill_counts
        except Exception as e:
            logger.error(f"Error getting skill distribution: {str(e)}")
            st.error(f"Error getting skill distribution: {str(e)}")
            return {}

    def get_cv_count(self) -> int:
        """Get the total number of CVs in the database"""
        try:
            result = (
                self.client.query
                .aggregate("Resume")
                .with_meta_count()
                .do()
            )
            
            logger.info(f"CV count query result: {result}")
            if result and "data" in result and "Aggregate" in result["data"] and "Resume" in result["data"]["Aggregate"]:
                return result["data"]["Aggregate"]["Resume"][0]["meta"]["count"]
            return 0
        except Exception as e:
            logger.error(f"Error getting CV count: {str(e)}")
            st.error(f"Error getting CV count: {str(e)}")
            return 0

    def process_cv_directory(self, directory_path: str, progress_bar) -> int:
        """Process all PDFs in a directory"""
        try:
            # Clear existing data before processing
            self.clear_database()
            
            # Find all PDF files recursively
            pdf_files = []
            for ext in ['.pdf', '.PDF']:
                pdf_files.extend(glob.glob(os.path.join(directory_path, f'**/*{ext}'), recursive=True))
            
            total_files = len(pdf_files)
            if total_files == 0:
                return 0

            # Process each file
            for i, pdf_file in enumerate(pdf_files):
                try:
                    relative_path = os.path.relpath(pdf_file, directory_path)
                    text_content = self.processor.extract_text_from_pdf(pdf_file)
                    skills = self.processor.extract_skills(text_content)
                    
                    # Store in Weaviate
                    properties = {
                        "content": text_content,
                        "filename": relative_path,
                        "skills": skills
                    }
                    
                    self.client.data_object.create(
                        data_object=properties,
                        class_name="Resume"
                    )
                    
                    # Update progress
                    progress = (i + 1) / total_files
                    progress_bar.progress(progress)
                    
                except Exception as e:
                    logger.error(f"Error processing {pdf_file}: {str(e)}")
                    st.warning(f"Error processing {pdf_file}: {str(e)}")
                    continue
            
            return total_files
        except Exception as e:
            logger.error(f"Error processing directory: {str(e)}")
            st.error(f"Error processing directory: {str(e)}")
            return 0

    def clear_database(self):
        """Clear all data from the database"""
        try:
            self.processor.clear_database()
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            st.error(f"Error clearing database: {str(e)}")

def highlight_skills(text: str, skills: List[str]) -> str:
    """Highlight skills in text with color"""
    highlighted_text = text
    for skill in skills:
        # Create a case-insensitive pattern that matches whole words
        pattern = re.compile(f'\\b{re.escape(skill)}\\b', re.IGNORECASE)
        highlighted_text = pattern.sub(f'<span style="background-color: #ffd700; font-weight: bold;">{skill}</span>', highlighted_text)
    return highlighted_text

def get_cv_download_link(filename: str, directory_path: str) -> str:
    """Generate a download link for a CV file"""
    try:
        # Search for the file recursively in the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower() == filename.lower():
                    file_path = os.path.join(root, file)
                    with open(file_path, "rb") as f:
                        pdf_bytes = f.read()
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 Download CV</a>'
                        return href
        return ""
    except Exception as e:
        logger.error(f"Error creating download link for {filename}: {str(e)}")
        st.error(f"Error creating download link for {filename}: {str(e)}")
        return ""

def show_documentation():
    """Show documentation in the sidebar"""
    st.sidebar.title("Documentation")
    
    # About section
    with st.sidebar.expander("About"):
        st.markdown("""
        ### CV Analysis Tool
        This tool helps you analyze CVs and find the best candidates based on their skills.
        
        Key features:
        - Upload and process CVs in PDF format
        - Extract skills automatically
        - Search candidates by required skills
        - View skill distribution across all CVs
        """)
    
    # How to Use section
    with st.sidebar.expander("How to Use"):
        st.markdown("""
        ### Quick Start Guide
        1. **Upload CVs**
           - Place your CV files in the `data/cv` directory
           - Click 'Process CV Directory' to analyze them
        
        2. **Find Candidates**
           - Select required skills from the dropdown
           - The system will show candidates matching ALL selected skills
        
        3. **View Results**
           - See skill distribution across all CVs
           - View matching candidates with highlighted skills
           - Download original CV files
        """)
    
    # Technical Details
    with st.sidebar.expander("Technical Details"):
        st.markdown("""
        ### System Architecture
        - Uses Weaviate vector database for CV storage
        - Implements semantic search for matching
        - Supports PDF file processing
        - Extracts skills using keyword matching
        
        ### File Requirements
        - Supported formats: PDF
        - Directory structure:
          ```
          data/
          └── cv/
              └── your_cv_files.pdf
          ```
        """)
    
    # Troubleshooting
    with st.sidebar.expander("Troubleshooting"):
        st.markdown("""
        ### Common Issues
        1. **CVs not found**
           - Ensure files are in the correct directory
           - Check file permissions
        
        2. **Skills not detected**
           - Verify PDF is text-based (not scanned)
           - Check if skills are written as expected
        
        3. **No results**
           - Try reducing the number of selected skills
           - Check if CVs were processed successfully
        """)

def main():
    st.set_page_config(
        page_title="CV Analysis Tool",
        page_icon="📄",
        layout="wide",
        menu_items={
            'Get Help': """
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
            3. **No results**: Try reducing selected skills
            
            ## Need More Help?
            Contact support at support@example.com
            """,
            
            'Report a Bug': "https://github.com/yourusername/cv-analyzer/issues",
            
            'About': """
            ### CV Analysis Tool v1.0
            
            A powerful tool for analyzing CVs and finding the best candidates based on their skills.
            
            **Key Features:**
            - PDF Processing
            - Skill Extraction
            - Candidate Matching
            - Skill Distribution Analysis
            
            **Technologies Used:**
            - Python
            - Streamlit
            - Weaviate Vector Database
            - PyPDF for PDF processing
            
            **Created by:** Your Company Name
            **License:** MIT
            
            2025 All rights reserved.
            """
        }
    )
    
    # Main content
    st.title("CV Analysis Tool")
    
    analyzer = CVAnalyzer()
    
    # Database management section
    st.sidebar.header("Database Management")
    cv_count = analyzer.get_cv_count()
    st.sidebar.write(f"Current CVs in database: {cv_count}")
    
    if st.sidebar.button(" Clear Database"):
        analyzer.clear_database()
        st.sidebar.success("Database cleared successfully!")
        st.experimental_rerun()
    
    # CV Directory Processing
    st.sidebar.header("Process CV Directory")
    
    # Use the folder upload component
    # upload_result = folder_uploader(
    #     key="cv_folder",
    #     label="Upload CV Folder",
    #     help="Drag and drop a folder containing CVs",
    #     allowed_extensions=[".pdf", ".PDF"],
    #     max_file_size=50 * 1024 * 1024  # 50MB per file
    # )
    
    # if upload_result:
    #     if 'error' in upload_result:
    #         st.sidebar.error(upload_result['error'])
    #     elif 'files' in upload_result:
    #         st.sidebar.success(f"Found {len(upload_result['files'])} files")
            
    #         # Show file details
    #         with st.sidebar.expander("View Files"):
    #             total_size = 0
    #             for file in upload_result['files']:
    #                 size_mb = file['size'] / (1024 * 1024)
    #                 total_size += file['size']
    #                 st.write(f" {file['name']} ({size_mb:.1f} MB)")
    #             st.write(f"Total size: {total_size / (1024 * 1024):.1f} MB")
            
    #         # Process the files
    #         if st.sidebar.button(" Process Files"):
    #             progress_bar = st.sidebar.progress(0)
    #             st.sidebar.write("Processing CVs...")
                
    #             # Create full paths for files
    #             full_path = os.path.join(config.DATA_DIR, upload_result.get('path', ''))
                
    #             # Process directory
    #             total_files = analyzer.process_cv_directory(full_path, progress_bar)
                
    #             if total_files > 0:
    #                 st.sidebar.success(f"Processed {total_files} CVs successfully!")
    #             else:
    #                 st.sidebar.warning("No PDF files found in the directory")
                
    #             progress_bar.empty()
    #             st.experimental_rerun()
    
    # Manual path input as fallback
    st.sidebar.markdown("---")
    st.sidebar.write("Or enter path manually:")
    cv_dir = st.sidebar.text_input(
        "Directory path (relative to data folder)",
        help="Enter the path to your CV directory, relative to the data folder"
    )
    
    if cv_dir and st.sidebar.button(" Process Directory"):
        full_path = os.path.join(config.DATA_DIR, cv_dir)
        if not os.path.exists(full_path):
            st.sidebar.error(f"Directory not found: {cv_dir}")
        else:
            progress_bar = st.sidebar.progress(0)
            st.sidebar.write("Processing CVs...")
            
            total_files = analyzer.process_cv_directory(full_path, progress_bar)
            
            if total_files > 0:
                st.sidebar.success(f"Processed {total_files} CVs successfully!")
            else:
                st.sidebar.warning("No PDF files found in the directory")
            
            progress_bar.empty()
            st.experimental_rerun()
    
    # Skill selection section
    st.subheader("Select Required Skills")
    selected_skills = []
    cols = st.columns(3)
    for idx, skill in enumerate(analyzer.tech_skills):
        col_idx = idx % 3
        with cols[col_idx]:
            if st.checkbox(skill):
                selected_skills.append(skill)
    
    if selected_skills:
        st.subheader("Best Matching Candidates")
        candidates = analyzer.find_best_candidates(selected_skills)
        
        if not candidates:
            st.warning("No matching candidates found with the selected skills.")
            return
        
        for idx, candidate in enumerate(candidates, 1):
            if not isinstance(candidate, dict):
                continue
                
            filename = candidate.get('filename', 'Unknown')
            skills = candidate.get('skills', [])
            content = candidate.get('content', '')
            
            with st.expander(f"{idx}. {filename}"):
                if skills:
                    # Highlight matched skills in the skills list
                    skill_text = []
                    for skill in skills:
                        if skill in selected_skills:
                            skill_text.append(f'<span style="background-color: #ffd700; font-weight: bold;">{skill}</span>')
                        else:
                            skill_text.append(skill)
                    st.markdown("**Skills:** " + ", ".join(skill_text), unsafe_allow_html=True)
                
                if content:
                    # Highlight skills in content
                    highlighted_content = highlight_skills(content, selected_skills)
                    st.markdown("**CV Content:**", unsafe_allow_html=True)
                    st.markdown(f'<div style="border: 1px solid #ddd; padding: 10px; height: 200px; overflow-y: auto;">{highlighted_content}</div>', 
                              unsafe_allow_html=True)
                
                # Add download button
                download_link = get_cv_download_link(filename, config.DATA_DIR)
                if download_link:
                    st.markdown(download_link, unsafe_allow_html=True)
                else:
                    st.error("CV file not found")

    # Show skill distribution
    st.subheader("Skill Distribution Across All CVs")
    skill_dist = analyzer.get_skill_distribution()
    
    if not skill_dist:
        st.warning("No CVs found in the database. Please upload some CVs first.")
        return
        
    # Sort skills by frequency
    sorted_skills = sorted(skill_dist.items(), key=lambda x: x[1], reverse=True)
    skills = [s[0] for s in sorted_skills]
    counts = [s[1] for s in sorted_skills]
    
    # Create bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=skills,
            y=counts,
            text=counts,
            textposition='auto',
        )
    ])
    
    # Update layout
    fig.update_layout(
        title="Skill Distribution",
        xaxis_title="Skills",
        yaxis_title="Number of CVs",
        showlegend=False,
        xaxis_tickangle=-45,
        height=500,
        margin=dict(t=30, b=100)  # Increase bottom margin for rotated labels
    )
    
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
