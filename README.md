# CV Analyzer

A Streamlit application for analyzing CVs/Resumes using Weaviate vector database and natural language processing.

## Features

- Upload multiple PDF CVs
- Extract text and skills from CVs
- Store CV data in Weaviate vector database
- Visualize skills distribution
- Search CVs by skills or content

## Project Structure

```
.
├── src/
│   ├── app/
│   │   └── main.py          # Streamlit application entry point
│   └── core/
│       ├── analyzer.py      # CV analysis logic
│       └── config.py        # Application configuration
├── data/                    # Data storage (created automatically)
├── docker-compose.yml       # Docker services configuration
├── Dockerfile              # Application container configuration
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## Setup

1. Install Docker and Docker Compose
2. Clone the repository
3. Run the application:
   ```bash
   docker-compose up --build
   ```

## Development

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run Streamlit locally:
   ```bash
   streamlit run src/app/main.py
   ```

## Environment Variables

- `WEAVIATE_URL`: URL of the Weaviate instance (default: http://localhost:8080)
- `WEAVIATE_STARTUP_PERIOD`: Timeout for Weaviate startup in seconds (default: 30)
