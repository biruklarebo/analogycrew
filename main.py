from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, LLM
from crewai.tasks.output_format import OutputFormat
from pydantic import BaseModel
import json, re, csv, os, time

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*", methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])

class Analogy(BaseModel):
    final_analogy: str
    source_domain: str
    target_domain: str
    explanation: str

# CSV file to store feedback
FEEDBACK_CSV = "feedback.csv"

# Initialize LLM (using Ollama for local models; switch to "gpt-4" or another if needed)
llm = LLM(model="ollama/deepseek-r1:14b")

def parse_final_answer(agent_output: str) -> dict:
    """
    Extracts JSON from an agent's final answer block.
    Expects output containing a line starting with "## Final Answer:" followed by JSON.
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

# Agent 1: Domain Analyzer
domain_analyzer = Agent(
    name="Domain Analyzer",
    role="Target Domain Analyzer",
    goal="Extract the core relational structures of the target domain. Parse the target domain to identify elements, properties, and relationships.",
    backstory="A cognitive specialist who identifies key relationships in a concept. Output is part of a larger analogical reasoning process based on Structure Mapping Theory.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 2: Candidate Generator
candidate_generator = Agent(
    name="Candidate Generator",
    role="Candidate Generator",
    goal="generate candidate domains that consist of familiar concepts, events, or experiences that help explain or illuminate the target domain. It’s typically easier to understand because it’s already well-known.",
    backstory="A creative agent skilled at brainstorming cross-domain analogies.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 3: Candidate Evaluator
candidate_evaluator = Agent(
    name="Candidate Evaluator",
    role="Candidate Evaluator",
    goal="Evaluate and rank the proposed candidate domains based on surface distance vs. structural similarity.",
    backstory="An analytical agent that scores each candidate to find the best far analogy with good structural fit.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 4: Base Domain Selector
base_domain_selector = Agent(
    name="Base Domain Selector",
    role="Base Domain Selector",
    goal="Choose the single best base domain from the evaluated candidates, ensuring a good balance of surface distance and structural alignment.",
    backstory="An expert in finalizing which domain to use for the analogy.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# Agent 5: Mapping Agent
mapping_agent = Agent(
    name="Mapping Agent",
    role="Mapping Agent",
    goal="Map the chosen base domain to the target domain and produce the final analogy explanation.",
    backstory="Skilled at drawing parallels between domains according to Structure Mapping Theory.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

# ----------------------------------------------------------------------------
# Main Route for Generating the Analogy
# ----------------------------------------------------------------------------

@app.route("/generate_analogy", methods=["POST"])
def generate_analogy():
    data = request.json
    target_concept = data.get("question")
    if not target_concept:
        return jsonify({"error": "No concept provided."}), 400

    try:
        start_time = time.perf_counter()
        # ------------------------------------------------
        # Task 1: Domain Analysis
        # ------------------------------------------------
        task1_prompt = f"""
        You are the 'Domain Analyzer'. The target domain is '{target_concept}'.
        1. Provide a concise definition of '{target_concept}'.
        2. Identify its key relational structures (elements, properties, processes, etc.).

        Return valid JSON:

        ## Final Answer:
        {{
          "definition": "...",
          "target_structures": ["...","...","..."]
        }}
        """

        task1 = Task(
            description=task1_prompt,
            agent=domain_analyzer,
            expected_output="JSON with target domain definition and structures."
        )

        # ------------------------------------------------
        # Task 2: Candidate Generation
        # ------------------------------------------------
        task2_prompt = f"""
        You are the 'Candidate Generator'.
        We have the target domain info from Task 1: {{task1}}
        1. Generate at least 5 distinct base domains from everyday life and try to make it as diverse and different from the {target_concept} as possible, think about the structure mapping theory.
        2. Each base domain should share some deeper relational structure with '{target_concept}'.
        3. Avoid the most common or trivial analogies.

        Return valid JSON with an array of candidates, e.g.:

        ## Final Answer:
        {{
          "candidates": [
            {{
              "base_domain": "...",
              "reasoning": "..."
            }},
            ...
          ]
        }}
        """

        task2 = Task(
            description=task2_prompt,
            agent=candidate_generator,
            expected_output="JSON with multiple candidate base domains."
        )

        # ------------------------------------------------
        # Task 3: Candidate Evaluation
        # ------------------------------------------------
        task3_prompt = f"""
        You are the 'Candidate Evaluator'.
        The target domain is '{target_concept}'.
        We have candidate base domains from Task 2: {{task2}}

        For each candidate:
        - Assign a 'distance_score' (1-10) indicating how different the surface features are from '{target_concept}' (10 = very different) Take points off if the candidate is too similar or in a similar field to {target_concept}.
        - Assign a 'structural_fit_score' (1-10) indicating how well it matches the key relational structures identified in Task 1 (10 = excellent fit) Take points off if the candidate is not easily understandable to a student who knows nothing about the target concept: {target_concept}.
        - Provide brief notes if needed.

        Return a JSON array of ranked_candidates sorted by your recommended priority
        (e.g., highest total score or your best judgment).

        ## Final Answer:
        {{
          "ranked_candidates": [
            {{
              "base_domain": "...",
              "distance_score": 0,
              "structural_fit_score": 0,
              "notes": "..."
            }},
            ...
          ]
        }}
        """

        task3 = Task(
            description=task3_prompt,
            agent=candidate_evaluator,
            expected_output="JSON with ranked candidate domains."
        )

        # ------------------------------------------------
        # Task 4: Base Domain Selection
        # ------------------------------------------------
        task4_prompt = f"""
        You are the 'Base Domain Selector'.
        The target domain is '{target_concept}'.
        We have ranked candidates from Task 3: {{task3}}

        1. Choose exactly one base domain that provides a strong balance of surface distance
           and structural fit with '{target_concept}'.
        2. Return it as 'chosen_base_domain'.

        Format your final answer as JSON:

        ## Final Answer:
        {{
          "chosen_base_domain": "..."
        }}
        """

        task4 = Task(
            description=task4_prompt,
            agent=base_domain_selector,
            expected_output="JSON with chosen base domain."
        )

        # ------------------------------------------------
        # Task 5: Mapping Agent
        # ------------------------------------------------
        task5_prompt = f"""
        You are the 'Mapping Agent'.
        - The target domain is '{target_concept}' (from Task 1).
        - The chosen base domain is from Task 4: {{task4}}

        1. Map the target domain to this base domain, forming a coherent analogy
           focusing on their structural parallels.
        2. Provide a brief explanation of how this analogy helps us understand '{target_concept}'.

        Return your final output as valid JSON:

        ## Final Answer:
        {{
          "final_analogy": "...",
          "source_domain": "",
          "target_domain": "{target_concept}",
          "explanation": "..."
        }}
        """

        task5 = Task(
            description=task5_prompt,
            agent=mapping_agent,
            expected_output="JSON with final analogy.",
            output_json=Analogy
        )

        # Create the Crew pipeline with all 5 tasks
        crew = Crew(
            agents=[
                domain_analyzer,
                candidate_generator,
                candidate_evaluator,
                base_domain_selector,
                mapping_agent
            ],
            tasks=[task1, task2, task3, task4, task5],
            verbose=True,
            allow_delegation=True,
            process="sequential"
        )

        crew_result = crew.kickoff()
        # Convert the crew's JSON output from a string to a dictionary
        final_json = json.loads(crew_result.json)
        # Calculate runtime and inject into the final JSON
        runtime = time.perf_counter() - start_time
        final_json["runtime_seconds"] = runtime
        print("Crew Output with runtime:", final_json)


        return jsonify(final_json)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

# ----------------------------------------------------------------------------
# Feedback Submission Endpoint
# ----------------------------------------------------------------------------

@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    required_fields = [
        "target_domain", "final_analogy", "source_domain", "explanation",
        "rating_clarity", "rating_relational", "rating_familiarity", "rating_overall", "runtime_seconds"
    ]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    file_exists = os.path.isfile(FEEDBACK_CSV)
    with open(FEEDBACK_CSV, mode="a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "target_domain", "final_analogy", "source_domain", "explanation",
            "rating_clarity", "rating_relational", "rating_familiarity", "rating_overall",
            "runtime_seconds", "comment"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "target_domain": data.get("target_domain"),
            "final_analogy": data.get("final_analogy"),
            "source_domain": data.get("source_domain"),
            "explanation": data.get("explanation"),
            "rating_clarity": data.get("rating_clarity"),
            "rating_relational": data.get("rating_relational"),
            "rating_familiarity": data.get("rating_familiarity"),
            "rating_overall": data.get("rating_overall"),
            "runtime_seconds": data.get("runtime_seconds"),
            "comment": data.get("comment", "")
        })

    return jsonify({"message": "Feedback submitted successfully."}), 200

if __name__ == "__main__":
    import csv
    app.run(debug=True)
