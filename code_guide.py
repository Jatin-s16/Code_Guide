import os
from tavily import TavilyClient
from groq import Groq
import gradio as gr
import requests
from bs4 import BeautifulSoup


# API keys from env variables
TAVILY_API_KEY="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"
GROQ_API_KEY="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"

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)


def get_code_snippet_from_url(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    tag = soup.find('pre')
    if tag:
        return tag.get_text()
    tag = soup.find('code')
    if tag:
        return tag.get_text()
    return None


def explain_code(code, language, question):
    prompt = (
        f"Explain this {language} code for - {question}. "
        "Please describe each step and give its time and space complexity.\n"
        "```\n"
        f"{code}\n"
        "```"
    )
    chat = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat.choices[0].message.content


def solve_question(question, language):
    query = f"{question} in {language}"
    
    query = " ".join(query.strip().split())
    query = query[:400]
    
    domains = ["stackoverflow.com", "geeksforgeeks.org"]
    
    response = tavily_client.search(query=query, include_domains=domains, max_results=1)
    
    results = response.get("results", [])
    if not results:
        return "No results found.", ""
    link = results[0].get("url", "")
    snippet = results[0].get("content", "")
    
    if not snippet:
        snippet = get_code_snippet_from_url(link) or ""
    explanation = ""
    
    if snippet:
        explanation = explain_code(snippet, language, question)
    return snippet or "No code snippet found.", f"{explanation}\n\nSource: {link}"


# Gradio Interface

interface = gr.Interface(
    fn=solve_question,
    
    inputs=[
        gr.Textbox(lines=2, placeholder="Enter coding question here...", label="Question"),
        gr.Dropdown(["Python", "Java", "C++", "JavaScript", "Go", "C"], label="Language")
    ],
    
    outputs=[
        gr.Textbox(label="Code Snippet"),
        gr.Markdown(label="Explanation")
    ],
    
    title="Your personal coding guide"
)

if __name__ == "__main__":
    interface.launch()