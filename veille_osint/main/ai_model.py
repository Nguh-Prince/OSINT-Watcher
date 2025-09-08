import os
import re
import requests

import json
import pickle
from typing import Dict
import google.generativeai as genai


from django.conf import settings

def get_recommendations_from_ai(prompt):
    """
    Call an AI service to get recommendations based on the alert details.
    This is a placeholder function and should be replaced with actual AI service integration.
    """
    # Example API call to an AI service (replace with actual implementation)
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": settings.GEMINI_API_KEY
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        # recommendations = response.json().get('recommendations', 'No recommendations available.')
        json_response = response.json()

        try:
            ai_answer = json_response['candidates'][0]
            text = ai_answer['content']['parts'][0]['text']
            json_text =  re.sub(f'(\n|```|json)', '', text)
            return json.loads(json_text)

        except (KeyError, IndexError):
            print("Unexpected response format from AI service.")
            return json_response
        
    except requests.RequestException as e:
        print(f"Failed to get recommendations: {e}")
        return "No recommendations available."


class AlertClassifier:
    """
    An abstraction of a neural network classifier powered by Gemini.
    It classifies text into: none, low, medium, high alert,
    and provides actionable recommendations if it's an alert.
    """

    def __init__(self, api_key: str = settings.GEMINI_API_KEY, model_name: str = "gemini-1.5-flash", language: str = settings.LANGUAGE_CODE):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.language = language
        self.classes = ["none", "low", "medium", "high"]

    def predict(self, text: str) -> Dict[str, str]:
        prompt = f"""
        You are a cybersecurity professional working in an African (specifically Cameroonian) bank.
        The following was picked up from a site:

        {text}

        Provide security recommendations for it considering it's for a bank system.
        Recommendations should be short, 2–5 items, in markdown format, each like:
        'Strengthen passwords: change old passwords to stronger ones...'

        Also, classify severity as {', '.join(self.classes)} based on relevance
        and risk to the bank's systems.

        Respond in JSON like this:
        {{
            "severity": "low" | "medium" | "high" | "none",
            "recommendations": ["Recommendation 1", "Recommendation 2", ...]
        }}

        Respond in {self.language}.

        Please don't translate the severity to the target language. Leave it in English (i.e. no matter the language, severity should either be none, high, medium or low). Don't give any recommendations if severity is none.
        """

        try:
            response = get_recommendations_from_ai(prompt)
            if isinstance(response, str):
                return {
                    "severity": "none",
                    "recommendations": []
                }
            return response

        except Exception as e:
            print(f"Prediction failed: {e}")
            return {
                "severity": "none",
                "recommendations": []
            }

    def save(self, path: str):
        """Pickle this object to a file."""
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str):
        """Load a pickled AlertClassifier."""
        with open(path, "rb") as f:
            return pickle.load(f)


"""
from main.ai_model import *
from main.models import *

classifier = AlertClassifier()
res = ScanResult.objects.first()

classifier.predict(res.details)
"""