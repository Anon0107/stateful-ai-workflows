from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from pypdf import PdfReader
import anthropic
from dotenv import load_dotenv
import json

load_dotenv()

class overallstate(TypedDict):
    pdf_path: str
    text: str
    result: dict
    summary: str


class inputstate(TypedDict):
    pdf_path: str

class outputstate(TypedDict):
    summary: str

def extract(state: inputstate) -> dict:
    reader = PdfReader(state['pdf_path'])
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return {'text': text}

client = anthropic.Anthropic()
def claude(system,prompt):
    response = client.messages.create(
        model = 'claude-haiku-4-5-20251001',
        max_tokens = 1024,
        system = system,
        messages = prompt
    )
    return next((b.text for b in response.content if b.type == 'text'),'No response')

def classify(state: overallstate) -> str:
    system = 'You are a helpful assistant that classify articles into research papers and news. Respond ONLY with one phrase (either research paper or news). DO NOT explain.'
    prompt = [{'role': 'user', 'content': f"<article>{state['text']}</article>"}]
    text_class = claude(system,prompt)
    if 'research paper'in text_class.lower():
        return 'researchpaper'
    elif 'news' in text_class.lower():
        return 'news'
    else:
        return 'summary'

def researchpaper(state: overallstate) -> dict:
    system ='You are a research paper analyzer that compiles summary, methodology and findings. Respond ONLY a valid JSON object in the given format. DO NOT explain'
    prompt = [{'role':'user', 'content': f"<article>{state['text']}</article><format>{{'summary': 'summary','methodology':'methodology','findings':['finding1','finding2']}}</format>"}]
    prompt.append({'role':'assistant','content':'{'})
    result = claude(system,prompt)
    try:
        return {'result': json.loads("{" + result)}
    except (json.JSONDecodeError, Exception):
        return {'result': {'summary': 'Parse failed', 'methodology': '', 'findings': []}}


def news(state: overallstate) -> dict:
    system ='You are a news analyzer that compiles summary, sentiment and entities. Respond ONLY a valid JSON object in the given format. DO NOT explain'
    prompt = [{'role':'user', 'content': f"<article>{state['text']}</article><format>{{'summary': 'summary','sentiment':'sentiment','entities':['entity1','entity2']}}</format>"}]
    prompt.append({'role':'assistant','content':'{'})
    result = claude(system,prompt)
    try:
        return {'result': json.loads("{" + result)}
    except (json.JSONDecodeError, Exception):
        return {'result': {'summary': 'Parse failed', 'sentiment': '', 'entities': []}}

def summary(state: overallstate) -> dict:
    result = state['result']
    summary = f"Article: {state['text']}"
    for key, item in result.items():
        summary += f"\n{key.title()}: {item}"
    return {'summary': summary}

graph = StateGraph(overallstate,input_schema=inputstate,output_schema=outputstate)

graph.add_node(extract)
graph.add_node(researchpaper)
graph.add_node(news)
graph.add_node(summary)

graph.add_edge(START,'extract')
graph.add_conditional_edges('extract',classify)
graph.add_edge('researchpaper','summary')
graph.add_edge('news','summary')
graph.add_edge('summary',END)

app = graph.compile()

result1 = app.invoke({'pdf_path': 'files/research_paper.pdf'})
result2 = app.invoke({'pdf_path': 'files/news_article.pdf'})
print(result1)
print(result2)