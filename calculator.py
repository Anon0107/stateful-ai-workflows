from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class inputstate(TypedDict):
    sentance: str
class overallstate(TypedDict):
    sentance: str
    operations: list
    answer: float
class outputstate(TypedDict):
    answer: float

def read(state: inputstate) -> dict:
    sentance = state['sentance']
    operations = []
    nums = ''
    for char in sentance:
        if not char.isdigit():
            if char in ['+','-','*','/']:
                if nums:
                    operations.append(int(nums))
                nums = ''
                operations.append(char)
        else:
            nums += char
    if nums:
        operations.append(int(nums))
    print(operations)
    return {'operations': operations}

def route(state: overallstate) -> str:
    operations = state['operations']
    if not operations:
        return 'answer'
    elif len(operations)% 2 == 0 or operations[0] in ['+','-','*','/'] or operations[-1] in ['+','-','*','/']:
        return 'answer'
    elif '*' in operations or '/' in operations:
        return 'multiplydivide'
    elif '+' in operations or '-' in operations:
        return 'plusminus'
    else:
        return 'answer'
def multiplydivide(state: overallstate) -> dict:
    operations = state['operations']
    new = [operations[0]]
    for i in range(1,len(operations),2):
        if operations[i] == '*':
            num1 = new.pop()
            num2 = operations[i+1]
            new.append(num1*num2)
        elif operations[i] == '/':
            num1 = new.pop()
            num2 = operations[i+1]
            new.append(num1/num2)
        else:
            new.append(operations[i])
            new.append(operations[i+1])
    return {'operations': new}

def plusminus(state: overallstate) -> dict:
    operations = state['operations']
    new = [operations[0]]
    for i in range(1,len(operations),2):
        if operations[i] == '+':
            num1 = new.pop()
            num2 = operations[i+1]
            new.append(num1+num2)
        elif operations[i] == '-':
            num1 = new.pop()
            num2 = operations[i+1]
            new.append(num1-num2)
        else:
            new.append(operations[i])
            new.append(operations[i+1])
    return {'operations': new}

def answer(state: overallstate) -> dict:
    operations = state['operations']
    if len(operations) % 2 == 0 or operations[0] in ['+','-','*','/'] or operations[-1] in ['+','-','*','/']:
        return {'answer': 'Error'}
    else:
        return {'answer': float(operations[0])}

graph = StateGraph(overallstate,input_schema=inputstate,output_schema=outputstate)
graph.add_node(read)
graph.add_node(multiplydivide)
graph.add_node(plusminus)
graph.add_node(answer)

graph.add_edge(START,'read')
graph.add_conditional_edges('read',route)
graph.add_conditional_edges('plusminus',route)
graph.add_conditional_edges('multiplydivide',route)
graph.add_edge('answer', END)

app = graph.compile()

result1 = app.invoke({'sentance': '10     + 1 *8 -10 /5 + 42 /12 *54'})
print(result1)
result2 = app.invoke({'sentance': '5*8/   5  '})
print(result2)
result3 = app.invoke({'sentance': '  *8   * 8  2'})
print(result3)