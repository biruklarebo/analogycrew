import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateAnalogy = async () => {
    setLoading(true);
    setResponse(null);

    try {
      const { data } = await axios.post("http://127.0.0.1:5000/generate_analogy", { question });
      setResponse(data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h2>AI Analogical Reasoning</h2>
      <textarea
        placeholder="Enter your question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "80%", height: "100px" }}
      />
      <button onClick={generateAnalogy} disabled={loading}>
        {loading ? "Generating..." : "Generate Analogy"}
      </button>

      {response && (
        <div className="output">
          <h3>Key Concepts:</h3>
          <p>{response["Concept Extractor"]}</p>

          <h3>Generated Analogy:</h3>
          <p>{response["Analogy Generator"]}</p>

          <h3>Explanation:</h3>
          <p>{response["Mapping Explainer"]}</p>
        </div>
      )}
    </div>
  );
}

export default App;
