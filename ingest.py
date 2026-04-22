from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from pypdf import PdfReader
from dotenv import load_dotenv
import voyageai
import chromadb
import os
import time
import uuid

load_dotenv()
vo_client = voyageai.Client()
chroma_client = chromadb.CloudClient(
    api_key = os.getenv('CHROMA_API_KEY'),
    database = os.getenv('CHROMA_DATABASE'),
    tenant = os.getenv('CHROMA_TENANT')
)

class inputstate(TypedDict):
    file_path : str
    coll_name : str

class overallstate(TypedDict):
    file_path : str
    coll_name : str
    text : str
    chunks : list[str]
    count : int

class outputstate(TypedDict):
    count : int

def extract(state: inputstate) -> dict:
    path = state['file_path']
    if path.endswith('.pdf'):
        reader = PdfReader(path)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
    elif path.endswith('.txt') or path.endswith('.md'):
        with open(path,'r',encoding= 'utf-8') as f:
            text = f.read()
    else:
        raise ValueError(f'Unsupported file type: {path}')
    return {'text': text}

def chunk(state: overallstate) -> dict:
    text = state['text']
    words = text.split(' ')
    chunk_size = 500
    overlap = 20
    chunks = []
    front_ptr = chunk_size
    back_ptr = 0
    while len(words) > back_ptr:
        while len(words) > front_ptr and '.' not in words[front_ptr]:
            front_ptr += 1
        while back_ptr > 0 and '.' not in words[back_ptr - 1]:
            back_ptr -= 1
        if back_ptr != 0 and len(words) - back_ptr < overlap:
            break
        chunks.append(' '.join(words[back_ptr:front_ptr]))
        back_ptr = front_ptr - overlap
        front_ptr = back_ptr + chunk_size
    return {'chunks': chunks}

def embed_and_store(state: overallstate) ->  dict:
    chunks = state['chunks']
    embeddings = []
    for i in range(0, len(chunks), 5):
        while True:
            try:
                batch = vo_client.embed(chunks[i:i+5], model='voyage-3', input_type='document').embeddings
                embeddings.extend(batch)
                break
            except Exception as e:
                if '429' in str(e):
                    time.sleep(60)
                else:
                    raise
    coll = chroma_client.get_or_create_collection(state['coll_name'])
    coll.add(
        documents = state['chunks'],
        embeddings = embeddings,
        ids = [f'doc_{uuid.uuid4().hex[:8]}_{i}' for i in range(len(embeddings))]
    )
    return {'count': len(embeddings)}

graph = StateGraph(overallstate,input_schema=inputstate,output_schema=outputstate)

graph.add_node(extract)
graph.add_node(chunk)
graph.add_node(embed_and_store)

graph.add_edge(START,'extract')
graph.add_edge('extract','chunk')
graph.add_edge('chunk','embed_and_store')
graph.add_edge('embed_and_store',END)

app = graph.compile()
