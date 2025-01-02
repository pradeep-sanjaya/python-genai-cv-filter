# CV Analysis System

This system helps analyze CVs and find the best candidates based on technical skills. It uses Weaviate as a vector database for efficient searching and Streamlit for the user interface.

## Project Structure

```
hr-cv/
├── data/
│   └── cv/
│       └── (your CV files)
└── app/
    ├── cv_processor/
    │   ├── processor.py
    │   └── requirements.txt
    ├── cv_gui/
    │   ├── app.py
    │   └── requirements.txt
    ├── docker/
    │   ├── docker-compose.yml
    │   ├── Dockerfile.processor
    │   └── Dockerfile.gui
    └── README.md
```

## Components

1. **Weaviate Database**: Vector database for storing and searching CV content
2. **CV Processor**: Python application that processes PDFs and stores them in Weaviate
3. **CV GUI**: Streamlit-based web interface for analyzing CVs

## Prerequisites

- Docker and Docker Compose
- PDFs to analyze in the data/CV_Brut directory

## Getting Started

1. Place your CVs in the `data/CV_Brut` directory

2. Start the system:
   ```bash
   cd app/docker
   docker-compose up --build
   ```

3. Access the GUI:
   - Open your browser
   - Go to http://localhost:8501

## Using the GUI

1. Select skills using the checkboxes
2. View the best matching candidates
3. Explore the skill distribution across all CVs

## Features

- PDF text extraction
- Skill detection
- Vector-based similarity search
- Interactive visualization of skill distribution
- Detailed CV content viewing

## Technical Stack

- Python 3.9
- Weaviate
- Streamlit
- PyPDF2
- Plotly
- Langchain
- Docker
