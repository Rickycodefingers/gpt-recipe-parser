import React, { useState } from 'react';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);

  const handleImageChange = (e) => {
    setImage(e.target.files[0]);
    setRecipe(null);
    setError('');
    setStep(0);
  };

  const handleUpload = async () => {
    if (!image) return;
    setLoading(true);
    setError('');
    setRecipe(null);
    setStep(0);

    try {
      // Convert image to base64
      const reader = new FileReader();
      reader.readAsDataURL(image);
      reader.onloadend = async () => {
        const base64data = reader.result;
        
        const response = await fetch('https://gpt-recipe-parser.onrender.com/api/recipe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            image: base64data
          }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Failed to extract recipe');
        }
        setRecipe(data);
        setLoading(false);
      };
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'An error occurred while processing the image');
      setLoading(false);
    }
  };

  const nextStep = () => setStep((s) => s + 1);
  const prevStep = () => setStep((s) => Math.max(0, s - 1));

  return (
    <div className="App">
      <header className="App-header">
        <h1>Recipe Image to Table</h1>
        <div style={{ marginBottom: '20px' }}>
          <input 
            type="file" 
            accept="image/*" 
            onChange={handleImageChange}
            style={{ marginRight: '10px' }}
          />
          <button 
            onClick={handleUpload} 
            disabled={!image || loading}
            style={{
              padding: '8px 16px',
              backgroundColor: loading ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Processing...' : 'Upload & Extract'}
          </button>
        </div>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {recipe && (
          <div style={{ 
            marginTop: '32px', 
            textAlign: 'left', 
            maxWidth: '800px',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            color: 'black'
          }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>{recipe.title}</h2>
            
            <h3 style={{ color: '#444', marginBottom: '15px' }}>Ingredients</h3>
            <ul style={{ 
              listStyleType: 'none', 
              padding: 0,
              marginBottom: '30px'
            }}>
              {recipe.ingredients && recipe.ingredients.map((ingredient, idx) => (
                <li key={idx} style={{ 
                  padding: '8px 0',
                  borderBottom: '1px solid #eee'
                }}>
                  {ingredient.amount} {ingredient.item} {ingredient.notes ? `(${ingredient.notes})` : ''}
                </li>
              ))}
            </ul>

            <h3 style={{ color: '#444', marginBottom: '15px' }}>Instructions</h3>
            {recipe.instructions && recipe.instructions.length > 0 && (
              <div style={{ backgroundColor: '#f5f5f5', padding: '20px', borderRadius: '4px' }}>
                <div style={{ marginBottom: '20px', fontSize: '1.1em' }}>
                  <strong>Step {step + 1}:</strong> {recipe.instructions[step]}
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button 
                    onClick={prevStep} 
                    disabled={step === 0}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: step === 0 ? '#ccc' : '#2196F3',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: step === 0 ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Previous
                  </button>
                  <button 
                    onClick={nextStep} 
                    disabled={step === recipe.instructions.length - 1}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: step === recipe.instructions.length - 1 ? '#ccc' : '#2196F3',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: step === recipe.instructions.length - 1 ? 'not-allowed' : 'pointer'
                    }}
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
