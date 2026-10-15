"""Provider-neutral domain models shared across components."""

from dataclasses import dataclass, field
from collections.abc import Mapping
from openai import OpenAI
from groq import Groq
import os 

@dataclass(frozen=True, slots=True)
class Document:
    """A source document or passage with stable identity and metadata."""

    id: str
    content: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Document id must not be empty.")
        if not self.content.strip():
            raise ValueError("Document content must not be empty.")


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A document returned by retrieval with its provider-defined relevance score."""

    document: Document
    score: float


class OpenaiBrain: 
    def __init__(self, model:str= "gpt-4o-mini", temperature:float | None= None, api_key :str = None, system_prompt:str="You are a helpful assistant."): 
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.history = [{'role':'system','content':system_prompt}]

    def invoke(self,prompt:str) -> str: 
        self.history.append({'role':'user','content':prompt})
        response = self.client.chat.completions.create(
            model = self.model, 
            temperature=self.temperature, 
            messages=self.history
        )
        answer = response.choices[0].message.content
        self.history.append({'role':'assistant', 'content':answer})
        return answer

    def stream(self, prompt:str): 
        stream = self.client.chat.completions.create(
            model = self.model, 
            temperature=self.temperature, 
            messages=self.history + [{'role':'user','content':prompt}], 
            stream=True
        )
        for chunk in stream: 
            if chunk or chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content 




class GroqBrain: 
    def __init__(self, model:str = "llama-3.3-70b-versatile", temperature:float | None = None, api_key=None,system_prompt:str = "You are a helpful assistant."): 
        self.client  = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.history = [{'role':'system','content':system_prompt}]
    def invoke(self,prompt:str): 
        self.history.append({'role':'user','content':prompt})
        response = self.client.chat.completions.create(
            model = self.model, 
            temperature=self.temperature, 
            messages=self.history
        )
        answer = response.choices[0].message.content
        self.history.append({'role':'assistant', 'content':answer})
        return answer
    def stream(self, prompt:str): 
        stream = self.client.chat.completions.create(
            model=self.model, 
            temperature=self.temperature, 
            messages= self.history + [{'role':'user', 'content':prompt}], 
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content: 
                yield chunk.choices[0].delta.content
