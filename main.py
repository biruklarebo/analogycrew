from flask import Flask, request, jsonify
from flask_cors import CORS
from crewai import Agent, Task, Crew, LLM

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests for frontend communication

# Initialize LLM (Use Ollama for local models or OpenAI GPT)
llm = LLM(model="ollama/mistral")  # Replace with "gpt-4" if using OpenAI

### 🧠 Concept Extractor Agent
concept_extractor = Agent(
    name="Concept Extractor",
    role="Cognitive Parser",
    goal="Extract key concepts from a student's question to identify the target and base domains.",
    backstory="A linguistics expert skilled in identifying the most relevant concepts in natural language.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

### 🔄 Analogy Generator Agent
analogy_generator = Agent(
    name="Analogy Generator",
    role="Cognitive Analogist",
    goal="Generate an analogy using Structure Mapping Theory based on extracted key concepts.",
    backstory="A deep thinker who specializes in forming structured analogies between different domains.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

### 📖 Mapping Explanation Agent
mapping_explainer = Agent(
    name="Mapping Explainer",
    role="Cognitive Synthesizer",
    goal="Explain the structural mappings between the analogy's base and target domains and provide cognitive insights.",
    backstory="An articulate scientist who excels in breaking down complex analogies into clear explanations.",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

@app.route("/generate_analogy", methods=["POST"])
def generate_analogy():
    """Handles API request to generate an analogy based on user input."""
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "No question provided."}), 400

    try:
        # Step 1: Extract Key Concepts
        concept_extraction_task = Task(
            description=f"Extract key concepts from the question: '{question}'.",
            agent=concept_extractor,
            expected_output="A list of key concepts extracted from the question."
        )

        # Step 2: Generate Analogy
        analogy_generation_task = Task(
            description=f"Using the extracted key concepts, generate an analogy.",
            agent=analogy_generator,
            expected_output="A structured analogy with mappings."
        )

        # Step 3: Explain the Mapping
        mapping_explanation_task = Task(
            description=f"Explain the mappings in the analogy.",
            agent=mapping_explainer,
            expected_output="A clear breakdown of source-target relationships."
        )

        # Create Crew and Run
        crew = Crew(
            agents=[concept_extractor, analogy_generator, mapping_explainer],
            tasks=[concept_extraction_task, analogy_generation_task, mapping_explanation_task],
            verbose=True
        )

        print("🚀 Running Crew AI agents...")
        result = crew.kickoff()  # This returns a single CrewOutput object

        # 🔍 Debugging: Print Crew AI Output
        print("🔍 Crew AI Output:", result)

        # ✅ Convert CrewOutput into a JSON-serializable format
        result_dict = {
            "response": str(result)  # Ensure the entire output is returned as a single string
        }

        return jsonify(result_dict)

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
