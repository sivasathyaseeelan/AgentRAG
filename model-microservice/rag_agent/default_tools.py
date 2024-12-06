from rag_agent.dynamic_cache_index import DynamicCacheIndex
from rag_agent.prompt import CONFIDENCE_PROMPT, WEBSEARCH_PROMPT
from llama_index.tools.tavily_research import TavilyToolSpec
from PyPDF2 import PdfReader
from rag_agent.ragagent import RAGAGENT
from rag_agent.utils import thought_agent_prompt, reasoning_agent_prompt, llm, chat_llm, chat_llm1
import gc
import os
from llama_index.core.tools import FunctionTool
from llama_index.core.query_engine import RetrieverQueryEngine


document_paths = []

def rag_agent(query, agent) -> str:
    """
    tool: rag_agent
    description: Used for answering query on the basis of the context retrieved from the user provided documents.
    Args:
        query (str): The query to be passed to the RAG agent.
            Example: "What was Nike's gross margin in FY 2022?"
    Returns:
        str: The response from the RAG agent.
    """
    
    global document_paths
    document_paths.append(agent.url)
    
    if len(document_paths)>=2 and document_paths[-1] != document_paths[-2]:
        gc.collect()
        
        agent.cache_index = DynamicCacheIndex(dim=agent.embedding_dim, batch_size=16)
        agent.previous_queries = {}
    
    if agent.reavaluate == True:
        res, jargons = agent.run(query ,False)
    else :
        res, jargons = agent.run(query ,True)
        
    score = chat_llm.invoke(CONFIDENCE_PROMPT.format(steps = agent.agent_input, answer = res)).content
    if agent.cache_index.process_pending_additions():
      pass
    return str(res) + ", Confidence Score : " + str(score), jargons, agent

def download_txt(content, filename="output.txt"):
    """
    Saves the given content to a .txt file in the current working directory.

    Args:
        content (str): The text content to be saved.
        file_name(str): Path to which content will be saved. Default -> output.txt

    Returns:
        str: Confirmation message indicating the file has been saved successfully.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
        return f"File '{filename}' has been saved successfully in the current working directory."
    except Exception as e:
        return f"An error occurred while saving the file: {e}"

def web_search_agent(query):
  """
  Used to get general online available information from the online source.
  Args :- query (str) - Query to be search online eg :- "Who is prime minister of Indi"
  """
  websearch = TavilyToolSpec(api_key= os.getenv('TAVILY_API_KEY'))
  results = websearch.search(query, max_results = 3)
  result = [r.text for r in results ]
  res = chat_llm.invoke(WEBSEARCH_PROMPT.format(query = query, response = result)).content
  return res

def end_tool(query):
  """
  Used to end the question-answering process. Returns "end" when correctly executed.

  Args : query(str) - this MUST be "end".

  Returns :
    str : "end"
  """
  return "end"

TOOL_MAP = {
    'rag_agent': rag_agent,
    'web_search_agent':web_search_agent,
    "END": end_tool
}

tools = [rag_agent, web_search_agent, end_tool]

l_tools = []

for tool in tools:
    tool = FunctionTool.from_defaults(tool)
    l_tools.append(tool)
    
TOOLS=[]
TOOLS_AUX = []

for i in l_tools:
  TOOLS.append(i.metadata.description)
  TOOLS_AUX.append(i.metadata.name)