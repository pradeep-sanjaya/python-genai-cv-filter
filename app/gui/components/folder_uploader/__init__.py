import os
import streamlit.components.v1 as components
import json

# Define the component's directory and build files
COMPONENT_DIR = os.path.dirname(os.path.abspath(__file__))

def folder_uploader(key=None):
    """Custom folder upload component"""
    
    _component_func = components.declare_component(
        "folder_uploader",
        path=COMPONENT_DIR
    )
    
    # Call the component function
    result = _component_func(key=key)
    return result
