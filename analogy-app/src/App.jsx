import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [question, setQuestion] = useState("");
  const [analogyResponse, setAnalogyResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState("");

  // Feedback state for each rating dimension + comment
  const [feedback, setFeedback] = useState({
    clarity: 0,
    relational: 0,
    familiarity: 0,
    overall: 0,
    comment: ""
  });

  // ----- Star Rating Component -----
  const StarRating = ({ label, value, onChange }) => {
    // Renders 5 stars, highlight them up to `value`.
    const stars = [1, 2, 3, 4, 5];
    return (
      <div className="star-rating"> 
      <div className="star-rating-row">
        <span className="rating-label">{label}</span>
        {stars.map((star) => (
          <span
            key={star}
            className={star <= value ? "star filled" : "star"}
            onClick={() => onChange(star)}
          >
            ★
          </span>
        ))}
      </div>
      </div>
    );
  };

  // ----- Generate Analogy -----
  const generateAnalogy = async () => {
    setLoading(true);
    setFeedbackMessage("");
    setAnalogyResponse(null);

    try {
      const { data } = await axios.post("http://127.0.0.1:5000/generate_analogy", { question });
      setAnalogyResponse(data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  // ----- Submit Feedback -----
  const submitFeedback = async () => {
    if (!analogyResponse) return;
    try {
      const payload = {
        target_domain: analogyResponse.target_domain,
        final_analogy: analogyResponse.final_analogy,
        source_domain: analogyResponse.source_domain,
        explanation: analogyResponse.explanation,
        rating_clarity: feedback.clarity,
        rating_relational: feedback.relational,
        rating_familiarity: feedback.familiarity,
        rating_overall: feedback.overall,
        comment: feedback.comment
      };

      const res = await axios.post("http://127.0.0.1:5000/submit_feedback", payload);
      setFeedbackMessage(res.data.message);
    } catch (error) {
      console.error("Feedback Error:", error);
      setFeedbackMessage("Error submitting feedback.");
    }
  };

  return (
    <div className="App">
      <h1>Analogical Reasoning via SMT</h1>
      <div className="input-section">
        <textarea
          className="question-input"
          placeholder="Enter the concept you want to understand..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button onClick={generateAnalogy} disabled={loading}>
          {loading ? "Generating..." : "Generate Analogy"}
        </button>
      </div>

      {analogyResponse && (
        <div className="analogy-output">
          <h2>Final Analogy:</h2>
          <p>{analogyResponse.final_analogy}</p>
          <h3>Source Domain:</h3>
          <p>{analogyResponse.source_domain}</p>
          <h3>Target Domain:</h3>
          <p>{analogyResponse.target_domain}</p>
          <h3>Explanation:</h3>
          <p>{analogyResponse.explanation}</p>

          <hr />
          <h2>Provide Your Feedback</h2>
          <StarRating
            label="How clear was this analogy?"
            value={feedback.clarity}
            onChange={(val) => setFeedback({ ...feedback, clarity: val })}
          />
          <StarRating
            label="Does the analogy accurately reflect relational similarities (not just surface-level)?"
            value={feedback.relational}
            onChange={(val) => setFeedback({ ...feedback, relational: val })}
          />
          <StarRating
            label="Was the chosen base domain familiar and helpful in understanding the concept?"
            value={feedback.familiarity}
            onChange={(val) => setFeedback({ ...feedback, familiarity: val })}
          />
          <StarRating
            label="Overall, how effective was this analogy in helping you understand the concept?"
            value={feedback.overall}
            onChange={(val) => setFeedback({ ...feedback, overall: val })}
          />

          <div className="feedback-comment">
            <label>Any suggestions to improve this analogy?</label>
            <textarea
              className="comment-input"
              value={feedback.comment}
              onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
            />
          </div>
          <button className="submit-feedback-btn" onClick={submitFeedback}>
            Submit Feedback
          </button>
          {feedbackMessage && <p className="feedback-message">{feedbackMessage}</p>}
        </div>
      )}
    </div>
  );
}

export default App;
