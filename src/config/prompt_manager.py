"""
Prompt Manager for Goldbell Leasing ChatGPT integration.
Handles loading and formatting of prompts from YAML configuration.
Author: Chris Yeo
"""

import os
import yaml
from typing import Dict, Any, Optional

class PromptManager:
    """
    Manages loading and formatting of prompts from YAML configuration.
    Provides easy access to different types of prompts and templates.
    """
    
    def __init__(self, config_path: str = "src/config/prompts.yaml"):
        """
        Initialize the PromptManager with a YAML configuration file.
        
        Args:
            config_path (str): Path to the prompts YAML file
        """
        self.config_path = config_path
        self.prompts = self._load_prompts()
        
    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading prompts: {str(e)}")
            return {}
            
    def get_system_prompt(self, prompt_type: str = "default") -> str:
        """Get a system prompt by type."""
        return self.prompts.get("system_prompts", {}).get(prompt_type, "")
        
    def get_analysis_prompt(self, prompt_type: str, **kwargs) -> str:
        """Get and format an analysis prompt."""
        template = self.prompts.get("analysis_prompts", {}).get(prompt_type, "")
        return template.format(**kwargs) if template else ""
        
    def get_query_template(self, template_type: str, **kwargs) -> str:
        """Get and format a query template."""
        template = self.prompts.get("query_templates", {}).get(template_type, "")
        return template.format(**kwargs) if template else ""
        
    def get_response_format(self, format_type: str, **kwargs) -> str:
        """Get and format a response template."""
        template = self.prompts.get("response_formats", {}).get(format_type, "")
        return template.format(**kwargs) if template else ""
        
    def reload_prompts(self) -> None:
        """Reload prompts from the YAML file."""
        self.prompts = self._load_prompts()
        
    def get_available_prompts(self) -> Dict[str, list]:
        """Get a dictionary of available prompt types and their names."""
        return {
            "system_prompts": list(self.prompts.get("system_prompts", {}).keys()),
            "analysis_prompts": list(self.prompts.get("analysis_prompts", {}).keys()),
            "query_templates": list(self.prompts.get("query_templates", {}).keys()),
            "response_formats": list(self.prompts.get("response_formats", {}).keys())
        }
