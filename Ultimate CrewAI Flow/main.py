import os
import json
import openai
import wikipedia
import logging
from dotenv import load_dotenv
from googleapiclient.discovery import build
from crewai import Agent, Task, Crew
from typing import Dict, List, Optional

load_dotenv()

os.getenv("GOOGLE_API_KEY")
os.getenv("GEMINI_API_KEY")
google_cse_id = os.getenv("GOOGLE_CSE_ID")

# Custom Exceptions
class ConfigError(Exception):
    pass

class APIError(Exception):
    pass

# Load Configuration
def load_config(config_file: str = "config.json") -> Dict:
    """Load configuration from a JSON file."""
    try:
        if not os.path.exists(config_file):
            raise ConfigError(f"Configuration file '{config_file}' not found. Please create it.")
        
        with open(config_file, "r") as f:
            content = f.read().strip()
            if not content:
                raise ConfigError(f"Configuration file '{config_file}' is empty. Please add the required keys.")
            
            config = json.loads(content)
        
        # Validate required keys
        required_keys = ["OPENAI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CSE_ID"]
        for key in required_keys:
            if key not in config:
                raise ConfigError(f"Missing required key '{key}' in configuration file.")
        
        return config
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {e}")

# Set up logging
def setup_logging(log_level: str = "INFO"):
    """Configure logging based on the provided log level."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)
    return logger

# Initialize APIs
def initialize_apis(config: Dict):
    """Initialize all required APIs."""
    try:
        openai.api_key = config["OPENAI_API_KEY"]
        google_api_key = config["GOOGLE_API_KEY"]
        google_cse_id = config["GOOGLE_CSE_ID"]
        google_service = build("customsearch", "v1", developerKey=google_api_key)
        logger.info("APIs initialized successfully.")
        return google_service
    except Exception as e:
        raise APIError(f"Failed to initialize APIs: {e}")

# Define helper functions
def search_google(query: str, google_service) -> List[Dict]:
    """Search Google using the Custom Search API."""
    try:
        logger.info(f"Searching Google for: {query}")
        res = google_service.cse().list(q=query, cx=google_cse_id).execute()
        return res.get("items", [])
    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return []

def search_wikipedia(query: str) -> str:
    """Search Wikipedia for relevant information."""
    try:
        logger.info(f"Searching Wikipedia for: {query}")
        return wikipedia.summary(query, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        logger.warning(f"Disambiguation error for Wikipedia search: {e}")
        return wikipedia.summary(e.options[0], sentences=2)
    except wikipedia.exceptions.PageError:
        logger.warning(f"No Wikipedia page found for: {query}")
        return "No relevant Wikipedia page found."
    except Exception as e:
        logger.error(f"Wikipedia search failed: {e}")
        return "Error fetching Wikipedia data."

def ask_chatgpt(question: str, context: str) -> str:
    """Ask ChatGPT to answer the question based on the context."""
    try:
        logger.info(f"Asking ChatGPT: {question}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Context: {context}\nQuestion: {question}"},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"ChatGPT request failed: {e}")
        return "Error generating response from ChatGPT."

# Define Agents
def create_researcher_agent():
    """Create the Researcher agent."""
    return Agent(
        role="Researcher",
        goal="Find relevant information from Google and Wikipedia",
        backstory="You are a skilled researcher who can find accurate information quickly.",
        tools=[],
        verbose=True,
    )

def create_analyzer_agent():
    """Create the Analyzer agent."""
    return Agent(
        role="Analyzer",
        goal="Analyze and summarize the information found by the Researcher",
        backstory="You are an expert at analyzing and summarizing complex information.",
        tools=[],
        verbose=True,
    )

# Define Tasks
def research_task(question: str, google_service):
    """Task to search Google and Wikipedia for information."""
    logger.info(f"Starting research task for: {question}")
    google_results = search_google(question, google_service)
    wikipedia_results = search_wikipedia(question)
    return {
        "google_results": google_results,
        "wikipedia_results": wikipedia_results,
    }

def analyze_task(results: Dict, question: str):
    """Task to analyze and summarize the information."""
    logger.info(f"Starting analysis task for: {question}")
    context = (
        f"Google Results: {results['google_results']}\n"
        f"Wikipedia Results: {results['wikipedia_results']}"
    )
    return ask_chatgpt(question, context)

# Define Crew
def create_crew(researcher, analyzer):
    """Create the Crew with Researcher and Analyzer agents."""
    return Crew(
        agents=[researcher, analyzer],
        tasks=[
            Task(
                description="Search Google and Wikipedia for information related to the user's question.",
                agent=researcher,
                action=lambda question: research_task(question, google_service),
                expected_output="A dictionary containing Google and Wikipedia search results.",
            ),
            Task(
                description="Analyze the information found by the Researcher and provide a summarized answer.",
                agent=analyzer,
                action=lambda results, question: analyze_task(results, question),
                expected_output="A summarized answer based on the research results.",
            ),
        ],
        verbose=True,  # Use a boolean value (True or False)
    )

# Main Loop
def main():
    """Main loop to handle user input and execute the CrewAI flow."""
    logger.info("Starting CrewAI flow. Type 'exit' to quit or 'help' for instructions.")
    while True:
        try:
            question = input("\nAsk a question (or type 'exit' to quit): ").strip()
            if question.lower() == "exit":
                logger.info("Exiting the program.")
                break
            elif question.lower() == "help":
                print("\nHelp:")
                print("1. Type your question to get an answer.")
                print("2. Type 'exit' to quit the program.")
                continue

            if not question:
                logger.warning("Please enter a valid question.")
                continue

            # Execute the CrewAI flow
            logger.info(f"Processing question: {question}")
            results = crew.kickoff(inputs={"question": question})
            print(f"\nAnswer: {results}\n")

        except KeyboardInterrupt:
            logger.info("\nExiting the program.")
            break
        except Exception as e:
            logger.error(f"An error occurred: {e}")

# Entry Point
if __name__ == "__main__":
    try:
        # Set up logging first
        logger = setup_logging()

        # Load configuration
        config = load_config()

        # Initialize APIs
        google_service = initialize_apis(config)

        # Create agents and crew
        researcher = create_researcher_agent()
        analyzer = create_analyzer_agent()
        crew = create_crew(researcher, analyzer)

        # Start the main loop
        main()
    except ConfigError as e:
        logger.error(e)
    except APIError as e:
        logger.error(e)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")