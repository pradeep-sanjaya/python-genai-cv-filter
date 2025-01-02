import os
import streamlit.components.v1 as components
from typing import List, Optional, Dict, Any

# Get absolute path to the frontend directory
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

# Create or get the component function
_component_func = components.declare_component(
    "folder_uploader",
    path=FRONTEND_DIR  # Point to the frontend directory containing index.html
)

def folder_uploader(
    key: str,
    label: str = "Upload Folder",
    help: str = "Drag and drop a folder here",
    accept_multiple_files: bool = True,
    allowed_extensions: Optional[List[str]] = None,
    max_file_size: int = 200 * 1024 * 1024,  # 200MB
    height: int = 200
) -> Optional[Dict[str, Any]]:
    """
    Create a folder upload component.
    
    Parameters
    ----------
    key : str
        Unique key for the component instance
    label : str
        Label text shown above the upload area
    help : str
        Help text shown below the upload area
    accept_multiple_files : bool
        Whether to allow multiple file selection
    allowed_extensions : List[str]
        List of allowed file extensions (e.g., ['.pdf', '.PDF'])
    max_file_size : int
        Maximum file size in bytes (default: 200MB)
    height : int
        Height of the upload area in pixels
    
    Returns
    -------
    Optional[Dict[str, Any]]
        Dictionary containing:
        - path: The selected folder path
        - files: List of files in the folder
        - error: Any error message
    """
    
    # Prepare component configuration
    component_config = {
        "label": label,
        "help": help,
        "accept_multiple_files": accept_multiple_files,
        "allowed_extensions": allowed_extensions or [],
        "max_file_size": max_file_size,
        "height": height
    }
    
    # Call component function
    component_value = _component_func(config=component_config, key=key)
    
    return component_value
