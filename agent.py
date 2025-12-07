from google.genai import types


from google.adk.agents import LlmAgent, SequentialAgent, LoopAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import google_search
from pathlib import Path





retry_config = types.HttpRetryOptions(
    attempts=2,  # Maximum retry attempts
    exp_base=30,  # Delay multiplier
    initial_delay=30,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


file_name = "writing_style.md"

def get_writing_style():
    """
    Looks up the past articles of the user and returns all past articles
    """
    
    base = Path(__file__).parent  # directory of this Python file
    file_path = base / file_name

    with file_path.open("r", encoding="utf-8") as f:
        return f.read()
    


Writer_Agent = LlmAgent(
    name="Writer_Agent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    # Updated instruction
    instruction="""You are an expert writer. Using the provided research brief, write a
      clear, engaging, and well-structured draft of the article.
    --- Aggregated Research --
    {aggregation}
    """,
    output_key="writer"
)




Style_Review_Agent = LlmAgent(
    name="Style_Review_Agent",
    model=Gemini(model="gemini-2.5-pro", retry_options=retry_config),
    # Updated instruction
    instruction="""
    1. Analyse the style, tone, language, throw, of the users by getting string of past articels written by user by calling the tool get_writing_style.
    You just need to call the tool and get a text response from the tool.

    2. Suggest rewrites on the below draft Article to match the style, tone and throw of these contents in the above urls, the content should be the below Article from writer agent
    --- Article from writer agent ---
    {writer}
    """,
    tools=[get_writing_style],
    output_key="styled"
    
    
)


Revision_Agent = LlmAgent(
    name="Revision_Agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    # Updated instruction
    instruction="""
    You are the lead editor. Revise the draft by checking the output from base writer and styler.
    Make sure
    - it is complete, 
    - matches the style of the user
    - includes all pointers in the  request of the user
    Otherwise, summarize the changes you made so the next cycle can begin.
      
    Guidelines:
        - Make sure to include all the pointers mentioned by user in the final article
        - No "in conclusion", "in summary" paragraph to end with. if there are any conclusion/summary paragraph, ask to remove
      
    -- writer output--
    {writer}
    -- styler output--
    {styled}
    """,
    output_key= "revised"
  
    
)



General_Web_Search_Agent = LlmAgent(
    name ="General_Web_Search_Agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
    You are a research assistant. Use the Google Search tool to find relevant articles, studies, and data about the topic provided.
  Your job is to take a user's topic and pointers and perform search using google_search tool to gather information on this topic and pointers
  and synthesize them as output.
  
  The user input will be in this format:
  ## Topic
  <topic>
  ## Pointers
  <draft>
  ## Guidelines
  - Guideline 1
  - Guideline 2
      """,
    tools=[google_search],
    output_key= "general_web_search",
    
)


formatter_agent = LlmAgent(
    name ="Formatter_Agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    instruction="""
    You are a formatting expert. Take the final approved article content and
  format it into clean, readable markdown with appropriate headings, lists, bold, italics, highlights
  and blockquotes.
  Strictly DONT use em dashes.
  If the user has asked for,  visualizations using mermaid as well. But only if the user has asked for it.
  
    """,
    output_key="formated"
    
)


drafting_loop = LoopAgent(
    name="Drafting_and_Review_Loop",
    sub_agents=[Writer_Agent,Style_Review_Agent,Revision_Agent],
    max_iterations=2,
)


aggregator_agent = LlmAgent(
    name="Aggregator_Agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    # Updated instruction
    instruction="""
    You are an expert research aggregator. You will receive inputs from multiple
  research agents. Your job is to synthesize all the findings into a single,
  coherent, and well-structured research brief that the Writer Agent can use
  to draft an article.
  Aggregate this research
  ----- GENERAL RESEARCH ------
    {general_web_search}
    """,
    output_key="aggregation"
)





root_agent = SequentialAgent(
    name="Root_Agent",
    sub_agents=[General_Web_Search_Agent,aggregator_agent,drafting_loop,formatter_agent]
)



# # Define a runner
# runner = InMemoryRunner(agent=root_agent)

# async def main():
#     response = await runner.run_debug(
#         """
#         """
#     )
    
#     print(response)


# asyncio.run(main())

# def main():
#     print(get_writing_style())
    
# if __name__ == "__main__":
#     main()