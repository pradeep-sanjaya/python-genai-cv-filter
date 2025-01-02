# Streamlit Folder Upload Component

A Streamlit component that provides a modern drag-and-drop interface for folder uploads.

## Features

- Drag and drop folder upload
- Click to browse folders
- Modern, responsive design
- Progress indicator
- File type filtering
- Error handling

## Installation

```bash
pip install streamlit-folder-upload
```

## Usage

```python
import streamlit as st
from streamlit_folder_upload import folder_uploader

# Use the component
selected_folder = folder_uploader(
    key="my_folder_uploader",
    label="Upload CV Folder",
    help="Drag and drop a folder containing CVs",
    accept_multiple_files=True,
    allowed_extensions=[".pdf", ".PDF"]
)

if selected_folder:
    st.write(f"Selected folder: {selected_folder}")
```

## Component Properties

- `key` (str): Unique key for the component instance
- `label` (str): Label text shown above the upload area
- `help` (str): Help text shown below the upload area
- `accept_multiple_files` (bool): Whether to allow multiple file selection
- `allowed_extensions` (List[str]): List of allowed file extensions
- `max_file_size` (int): Maximum file size in bytes (default: 200MB)
- `height` (int): Height of the upload area in pixels (default: 200)

## Events

The component returns a dictionary containing:
- `path`: The selected folder path
- `files`: List of files in the folder
- `error`: Any error message that occurred during upload

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
