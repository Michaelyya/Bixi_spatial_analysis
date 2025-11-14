"""
Prompt Management Module
Contains all prompts for OpenAI interactions
"""
from typing import Dict, Any


class PromptManager:

    @staticmethod
    def get_data_analysis_prompt(data_summary: str) -> str:
        return f"""You are a spatial data analyst specializing in bike-sharing systems. 
Analyze the following BIXI (Montreal bike-sharing) data and provide insights:

{data_summary}

Please provide:
1. Key patterns and trends in station utilization
2. Geographic clusters of high/low availability
3. Recommendations for optimal station placement
4. Potential issues or anomalies
5. Suggestions for improving the bike-sharing system

Format your response in clear sections with actionable insights."""

    @staticmethod
    def get_map_design_prompt(analysis_results: str, data_summary: str) -> str:
        return f"""You are a cartographic expert. Based on the following analysis of BIXI data:

ANALYSIS RESULTS:
{analysis_results}

DATA SUMMARY:
{data_summary}

Provide recommendations for creating an effective map visualization:
1. Suggested symbology (colors, sizes, styles) for different data attributes
2. Layer organization and hierarchy
3. Classification methods (natural breaks, quantile, etc.)
4. Legend design recommendations
5. Layout suggestions (title, scale, north arrow placement)
6. Color schemes that highlight patterns effectively

Format your response as structured recommendations that can be implemented in ArcGIS Pro."""

    @staticmethod
    def get_arcpy_code_prompt(task_description: str, data_structure: str) -> str:
        """
        Generate prompt for creating ArcPy code
        
        Args:
            task_description: Description of the mapping task
            data_structure: Description of the data structure
        
        Returns:
            str: Formatted prompt
        """
        return f"""You are an ArcGIS Pro Python expert. Generate ArcPy code to accomplish the following:

TASK: {task_description}

DATA STRUCTURE:
{data_structure}

Requirements:
- Use arcpy.mp module for map and layout management
- Include proper error handling
- Add comments explaining each step
- Use best practices for ArcPy scripting
- Assume data is already loaded as a feature class or can be created from CSV

Provide complete, runnable Python code that:
1. Creates or accesses a map in ArcGIS Pro
2. Adds layers with appropriate symbology
3. Creates a layout with title, legend, scale bar, and north arrow
4. Exports the map to PDF or PNG

Return ONLY the Python code, no explanations outside of code comments."""

    @staticmethod
    def get_summary_prompt(dataframe_info: Dict[str, Any]) -> str:
        """
        Generate prompt for creating data summary
        
        Args:
            dataframe_info: Dictionary with dataframe statistics
        
        Returns:
            str: Formatted prompt
        """
        return f"""Summarize the following BIXI data statistics in a clear, concise format:

{dataframe_info}

Include:
- Total number of stations
- Average bikes available
- Average docks available
- Utilization patterns
- Geographic extent
- Any notable patterns or outliers

Keep it concise (2-3 paragraphs) and focus on key insights."""


def get_prompt_for_task(task_type: str, **kwargs) -> str:
    """
    Convenience function to get prompts
    
    Args:
        task_type: Type of task ('analysis', 'map_design', 'arcpy_code', 'summary')
        **kwargs: Additional arguments for the prompt
    
    Returns:
        str: Formatted prompt
    """
    manager = PromptManager()
    
    if task_type == "analysis":
        return manager.get_data_analysis_prompt(kwargs.get("data_summary", ""))
    elif task_type == "map_design":
        return manager.get_map_design_prompt(
            kwargs.get("analysis_results", ""),
            kwargs.get("data_summary", "")
        )
    elif task_type == "arcpy_code":
        return manager.get_arcpy_code_prompt(
            kwargs.get("task_description", ""),
            kwargs.get("data_structure", "")
        )
    elif task_type == "summary":
        return manager.get_summary_prompt(kwargs.get("dataframe_info", {}))
    else:
        raise ValueError(f"Unknown task type: {task_type}")

