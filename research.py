import anthropic
import voyageai
import chromadb
import os
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from dotenv import load_dotenv

from langgraph.checkpoint.memory import MemorySaver

load_dotenv()
ant_client = anthropic.Anthropic()
vo_client = voyageai.Client()
chroma_client = chromadb.CloudClient(
    api_key= os.getenv('CHROMA_API_KEY'),
    database= os.getenv('CHROMA_DATABASE'),
    tenant= os.getenv('CHROMA_TENANT')
)

def claude(system,prompt):
    response = ant_client.messages.create(
        model = 'claude-haiku-4-5-20251001',
        max_tokens = 1024,
        system = system,
        messages = [{'role': 'user', 'content': prompt}]
    )
    return next((b.text for b in response.content if b.type == 'text'),'No response')

class inputstate(TypedDict):
    question: str
    coll_name: str

class overallstate(TypedDict):
    question: str
    coll_name: str
    sub_questions: list[str]
    rag_results: dict[list[str]]
    synthesis: str
    report: str

class outputstate(TypedDict):
    report: str

def breaks(state: inputstate)-> dict:
    system = 'You are a helpful assistant that breaks a question in more specific sub-questions if necessary. Respond ONLY with a python list in the given format. DO NOT explain. DO NOT wrap output in markdown code fences.'
    prompt = f"<question>{state['question']}</question><format>[sub_question1, sub_question2]</format>"
    result = claude(system,prompt)
    sub_qns = result.split(', ')
    for i in range(len(sub_qns)):
        sub_qns[i] = sub_qns[i].strip('"[] '+"'")
    return {'sub_questions': sub_qns}

def rag(state: overallstate)-> dict:
    sub_qns = state['sub_questions']
    embeddings = vo_client.embed(sub_qns, model = 'voyage-3', input_type = 'query').embeddings
    coll = chroma_client.get_collection(state['coll_name'])
    docs = coll.query(query_embeddings=embeddings, include= ['metadatas', 'documents'], n_results = 1)
    return {'rag_results':{
        'ids': [ids[0] for ids in docs['ids']],
        'docs': [doc[0] for doc in docs['documents']]
    }}

def synthesis(state: overallstate)-> dict:
    system = 'You are a research assistant. Synthesize the findings into a single coherent answer to the original question. Resolve contradictions. Remove redundancy.'
    prompt = "\n".join(
        [f"Sub-question: {state['sub_questions'][i]}\nFindings: {state['rag_results']['docs'][i]}"
        for i in range(len(state['sub_questions']))]
    )
    response = claude(system,prompt)
    return {'synthesis': response}

def report(state: overallstate)-> dict:
    system = 'You are a research assistant. Write a structured report. Cite sources inline as [source_id].'
    sources = "\n".join([
        f"{state['rag_results']['ids'][i]}: {state['rag_results']['docs'][i]}"
        for i in range(len(state['rag_results']['ids']))]
    )
    prompt = f"Write a research report based on this synthesis:\n{state['synthesis']}\nCite sources using these docs:\n{sources}"
    response = claude(system,prompt)
    return {'report': response}

graph = StateGraph(overallstate,input_schema=inputstate,output_schema=outputstate)

graph.add_node(breaks)
graph.add_node(rag)
graph.add_node(synthesis)
graph.add_node(report)

graph.add_edge(START,'breaks')
graph.add_edge('breaks','rag')
graph.add_edge('rag','synthesis')
graph.add_edge('synthesis','report')
graph.add_edge('report',END)

app = graph.compile()
question = input('Question: ')
coll = input('Collection name: ')

result = app.invoke({'question':question, 'coll_name':coll})

# 1. compile with checkpointer + interrupt
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer, interrupt_before=['report'])

# 2. first invoke — graph halts before report
config = {'configurable': {'thread_id': '1'}}
app.invoke({'question': question, 'coll_name': coll}, config=config)

# 3. inspect state, optionally edit it
current_state = app.get_state(config)
print(current_state.values['synthesis'])

approval = input('Approve? (y/edit): ')
if approval != 'y':
    edited = input('Enter revised synthesis: ')
    app.update_state(config, {'synthesis': edited})

# 4. resume — pass None to continue from checkpoint
result = app.invoke(None, config=config)
print(result)