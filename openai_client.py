"""
OpenAI Client Module
Handles all interactions with OpenAI API
"""
import json
from typing import Dict, Any, Optional
import openai
import config


class OpenAIClient:
    """Client for interacting with OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to config value)
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = config.OPENAI_MODEL
    
    def analyze_data(self, data_summary: str) -> Dict[str, Any]:
        """
        Analyze BIXI data using GPT
        
        Args:
            data_summary: Summary of the data to analyze
        
        Returns:
            dict: Analysis results with insights
        """
        from prompts import PromptManager
        
        prompt = PromptManager.get_data_analysis_prompt(data_summary)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert spatial data analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis = response.choices[0].message.content
            
            return {
                "success": True,
                "analysis": analysis,
                "model": self.model
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": None
            }
    
    def get_map_design_recommendations(self, analysis_results: str, data_summary: str) -> Dict[str, Any]:
        """
        Get map design recommendations from GPT
        
        Args:
            analysis_results: Results from data analysis
            data_summary: Summary of the data
        
        Returns:
            dict: Design recommendations
        """
        from prompts import PromptManager
        
        prompt = PromptManager.get_map_design_prompt(analysis_results, data_summary)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert cartographer and GIS specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            recommendations = response.choices[0].message.content
            
            return {
                "success": True,
                "recommendations": recommendations,
                "model": self.model
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": None
            }
    
    def generate_arcpy_code(self, task_description: str, data_structure: str) -> Dict[str, Any]:
        """
        Generate ArcPy code using GPT
        
        Args:
            task_description: Description of the mapping task
            data_structure: Description of the data structure
        
        Returns:
            dict: Generated code and metadata
        """
        from prompts import PromptManager
        
        prompt = PromptManager.get_arcpy_code_prompt(task_description, data_structure)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert ArcGIS Pro Python developer. Generate clean, well-commented ArcPy code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for code generation
                max_tokens=2000
            )
            
            code = response.choices[0].message.content
            
            # Extract code if it's wrapped in markdown code blocks
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            return {
                "success": True,
                "code": code,
                "model": self.model
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": None
            }
    
    def create_data_summary(self, dataframe_info: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of the data
        
        Args:
            dataframe_info: Dictionary with dataframe statistics
        
        Returns:
            str: Formatted summary
        """
        from prompts import PromptManager
        
        prompt = PromptManager.get_summary_prompt(dataframe_info)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst who creates clear, concise summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error creating summary: {str(e)}"
    
    def chat(self, message: str, context: Optional[str] = None) -> str:
        """
        General chat interface for custom queries
        
        Args:
            message: User message
            context: Optional context about the data/project
        
        Returns:
            str: Response from GPT
        """
        messages = [
            {"role": "system", "content": "You are a helpful assistant for GIS and spatial data analysis."}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Error: {str(e)}"

