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
      <h2>Analogical Reasoning via SMT</h2>
      <textarea
        placeholder="Enter the concept you want to understand..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{ width: "80%", height: "100px" }}
      />
      <button onClick={generateAnalogy} disabled={loading}>
        {loading ? "Generating..." : "Generate Analogy"}
      </button>
      {response && (
        <div className="output">
          <h3>Final Analogy:</h3>
          <p>{response.final_analogy}</p>
          <h3>Source Domain:</h3>
          <p>{response.source_domain}</p>
          <h3>Target Domain:</h3>
          <p>{response.target_domain}</p>
          <h3>Explanation:</h3>
          <p>{response.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default App;
