from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Process, Task, Crew, LLM
from crewai.tasks.output_format import OutputFormat
from pydantic import BaseModel
import json, re

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

class Analogy(BaseModel):
    final_analogy: str
    source_domain: str
    target_domain: str
    explanation: str

# Initialize LLM (using Ollama for local models; switch to "gpt-4" if needed)
llm = LLM(model="ollama/mistral")

def parse_final_answer(agent_output: str) -> dict:
    """
    Extracts JSON from an agent's final answer block.
    Expects a line starting with "## Final Answer:" followed by JSON.
    """
    pattern = r"## Final Answer:\s*(\{.*?\})"
    match = re.search(pattern, agent_output, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except Exception as e:
            print(f"JSON parse error: {e}")
    return {}

### Agent Definitions

# Agent 1: Target Domain Analyzer
domain_analyzer = Agent(
    name="Domain Analyzer",
    role="Target Domain Analyzer",
    goal="Extract the core relational structures of the target domain.",
    backstory="A cognitive specialist who identifies key relationships in a concept. Your output is one part of a larger analogical reasoning process based on Structure Mapping Theory.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 2: Base Domain Selector
base_domain_selector = Agent(
    name="Base Domain Selector",
    role="Base Domain Selector",
    goal="Select a base domain that exhibits relational structures similar to those of the target domain. Use the output of the Domain Analyzer for the relational structures.",
    backstory="An expert in linking abstract concepts to familiar domains. Your output is one part of a larger analogical reasoning process based on Structure Mapping Theory.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 3: Mapping Agent
mapping_agent = Agent(
    name="Mapping Agent",
    role="Mapping Agent",
    goal="Map the target domain to the selected base domain and generate a final analogy. Use the outputs of the previous tasks to create a coherent analogy.",
    backstory="Skilled at drawing parallels between domains in accordance with Structure Mapping Theory. Use the outputs of previous tasks to create a coherent analogy.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

@app.route("/generate_analogy", methods=["POST"])
def generate_analogy():
    data = request.json
    target_concept = data.get("question")
    if not target_concept:
        return jsonify({"error": "No concept provided."}), 400

    try:
        # Task 1: Target Domain Analyzer – Extract relational structures from the target domain.
        task1_prompt = f"""
        For the target domain '{target_concept}', identify its key relational structures.
        Return a structured JSON response in your final answer with the key "target_structures".
        ## Final Answer:
        {{
            "target_structures": []
        }}
        """
        task1 = Task(
            description=task1_prompt,
            agent=domain_analyzer,
            expected_output="JSON with target structures."
        )

        # Task 2: Base Domain Selector – Select a base domain using the output of Task 1.
        task2_prompt = f"""
        Using the output of the Domain Analyzer for the relational structures,
        select an appropriate base domain for the target domain '{target_concept}'.
        Choose based on relational similarity without hardcoding any example.
        Return a structured JSON response in your final answer with the key "base_domain".
        ## Final Answer:
        {{
            "base_domain": ""
        }}
        """
        task2 = Task(
            description=task2_prompt,
            agent=base_domain_selector,
            expected_output="JSON with base domain."
        )

        # Task 3: Mapping Agent – Generate the final analogy using outputs from Task 1 and Task 2.
        task3_prompt = f"""
        Using the outputs from Tasks 1 and 2,
        generate a final analogy that maps the target domain '{target_concept}' onto the selected base domain.
        Format the final output as a JSON object with the keys:
          "final_analogy", "source_domain", "target_domain", and "explanation".
        ## Final Answer:
        {{
            "final_analogy": "",
            "source_domain": "",
            "target_domain": "{target_concept}",
            "explanation": "lets keep this relatively short"
        }}
        """
        task3 = Task(
            description=task3_prompt,
            agent=mapping_agent,
            expected_output="JSON with final analogy.",
            output_json=Analogy
        )

        # Create the Crew with delegation enabled to pass outputs between tasks.
        crew = Crew(
            agents=[domain_analyzer, base_domain_selector, mapping_agent],
            tasks=[task1, task2, task3],
            verbose=True,
            allow_delegation=True,
            process=Process.sequential
        )
        crew_result = crew.kickoff()
        print("Crew Output:", crew_result.json)

        # The final output comes from Task 3.
        # final_output = parse_final_answer(crew_result)
        # return jsonify(final_output)
        return crew_result.json
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
