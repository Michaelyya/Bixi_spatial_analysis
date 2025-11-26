import openai
import config
from prompts import PromptManager


class OpenAIClient:
    
    def __init__(self, api_key=None):
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY in .env file")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = config.OPENAI_MODEL
    
    def analyze_data(self, data_summary):
        prompt = PromptManager.get_data_analysis_prompt(data_summary)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert spatial data analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return {
            "success": True,
            "analysis": response.choices[0].message.content,
            "model": self.model
        }
    
    def get_map_design_recommendations(self, analysis_results, data_summary):
        prompt = PromptManager.get_map_design_prompt(analysis_results, data_summary)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert cartographer and GIS specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return {
            "success": True,
            "recommendations": response.choices[0].message.content,
            "model": self.model
        }
    
    def create_data_summary(self, dataframe_info):
        prompt = PromptManager.get_summary_prompt(dataframe_info)
        
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
    
    def chat(self, message, context=None):
        messages = [{"role": "system", "content": "You are a helpful assistant for GIS and spatial data analysis."}]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
