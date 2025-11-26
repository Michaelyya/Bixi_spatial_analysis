class PromptManager:

    @staticmethod
    def get_data_analysis_prompt(data_summary):
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
    def get_map_design_prompt(analysis_results, data_summary):
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

Format your response as structured recommendations."""

    @staticmethod
    def get_summary_prompt(dataframe_info):
        return f"""Summarize the following BIXI data statistics in a clear, concise format:

{dataframe_info}

Keep it concise (2-3 paragraphs) and focus on key insights."""


def get_prompt_for_task(task_type, **kwargs):
    manager = PromptManager()
    
    if task_type == "analysis":
        return manager.get_data_analysis_prompt(kwargs.get("data_summary", ""))
    elif task_type == "map_design":
        return manager.get_map_design_prompt(kwargs.get("analysis_results", ""), kwargs.get("data_summary", ""))
    elif task_type == "summary":
        return manager.get_summary_prompt(kwargs.get("dataframe_info", {}))
    else:
        raise ValueError(f"Unknown task type: {task_type}")
