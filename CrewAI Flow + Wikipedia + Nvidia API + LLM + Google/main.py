import wikipedia
import os
import wikipediaapi
from dotenv import load_dotenv
from googlesearch import search  # Import the Google Search module

load_dotenv()

NVIDIA_API_KEY_AND_LLM = os.getenv("NVIDIA_API_KEY")

class ProjectManagerAgent:
    def initialize_project(self, tasks):
        print("Project Manager: Initializing project and assigning tasks.")
        return tasks

    def review_feedback(self, feedback):
        print(f"Project Manager: Reviewing client feedback: {feedback}")
        return "Adjust tasks if needed."


class DeveloperAgent:
    def __init__(self):
        # Initialize both Wikipedia modules
        self.wiki_simple = wikipedia
        self.wiki_advanced = wikipediaapi.Wikipedia('english')

    def write_code(self, task):
        print(f"Developer: Processing task: {task}")

        # Check if the task is a question
        if "what" in task.lower() or "who" in task.lower() or "net worth" in task.lower():
            print("Developer: Detected a question. Fetching answer from Wikipedia or Google.")
            try:
                # Try using the simple wikipedia module first
                answer = self.wiki_simple.summary(task, sentences=2)
                print(f"Developer: Wikipedia summary: {answer}")
                return answer
            except:
                # Fallback to wikipedia-api for more detailed search
                print("Developer: Falling back to wikipedia-api for detailed search.")
                page = self.wiki_advanced.page(task)
                if page.exists():
                    return page.summary[:500]  # Return first 500 characters of the summary
                else:
                    # If Wikipedia fails, try Google Search
                    print("Developer: No Wikipedia page found. Trying Google Search.")
                    google_results = list(search(task, num=1, stop=1, pause=2))  # Fetch the first result
                    if google_results:
                        return f"Google Search result: {google_results[0]}"
                    else:
                        return "Developer: No relevant information found on Wikipedia or Google."
        else:
            # If it's not a question, treat it as a regular task
            print(f"Developer: Writing code for task: {task}")
            return f"Code for {task} completed."


class QAAgent:
    def test_code(self, code):
        print(f"QA Agent: Testing code or answer: {code}")
        return "Code or answer passed QA."


class DevOpsAgent:
    def deploy_code(self, code):
        print(f"DevOps Agent: Deploying code or answer: {code}")
        return "Code or answer deployed successfully."


class ClientCommunicationAgent:
    def send_update(self, message):
        print(f"Client Communication Agent: Sending update to client: {message}")
        return "Client notified."

    def get_feedback(self):
        return "Client feedback: Everything looks good!"


def crewai_flow():
    # Initialize agents
    project_manager = ProjectManagerAgent()
    developer = DeveloperAgent()
    qa = QAAgent()
    devops = DevOpsAgent()
    client_comm = ClientCommunicationAgent()

    # Step 1: Get tasks from the terminal
    tasks = []
    print("Enter the tasks for the project (type 'done' to finish):")
    while True:
        task = input("> ")
        if task.lower() == "done":
            break
        tasks.append(task)

    if not tasks:
        print("No tasks provided. Exiting.")
        return

    # Step 2: Project Initialization
    assigned_tasks = project_manager.initialize_project(tasks)

    # Step 3: Task Execution
    for task in assigned_tasks:
        print(f"\nProcessing task: {task}")
        result = developer.write_code(task)

        # Step 4: Quality Assurance
        qa_result = qa.test_code(result)

        # Step 5: Deployment
        if "passed" in qa_result:
            deployment_result = devops.deploy_code(result)
            print(deployment_result)

            # Step 6: Client Communication
            client_comm.send_update(f"Task completed: {task}")
        else:
            print("QA failed. Code or answer not deployed.")

    # Step 7: Feedback Loop
    feedback = client_comm.get_feedback()
    project_manager.review_feedback(feedback)


# Run the flow
crewai_flow()
