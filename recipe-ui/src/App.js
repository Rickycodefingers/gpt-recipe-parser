import React, { useState } from 'react';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);
  const [language, setLanguage] = useState('en');

  const languages = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese'
  };

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
            image: base64data,
            language: language
          }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Failed to extract recipe');
        }
        setRecipe(data);
      };
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'An error occurred while processing the image');
    } finally {
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
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              padding: '8px',
              marginRight: '10px',
              borderRadius: '4px',
              border: '1px solid #ccc'
            }}
          >
            {Object.entries(languages).map(([code, name]) => (
              <option key={code} value={code}>{name}</option>
            ))}
          </select>
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
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
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
            <h2 style={{ color: '#333', marginBottom: '20px' }}>{recipe.name}</h2>
            
            <div style={{ marginBottom: '20px' }}>
              <p><strong>Servings:</strong> {recipe.servings}</p>
              <p><strong>Prep Time:</strong> {recipe.prep_time} minutes</p>
              <p><strong>Cook Time:</strong> {recipe.cook_time} minutes</p>
              <p><strong>Total Time:</strong> {recipe.total_time} minutes</p>
            </div>

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
                  {ingredient}
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

            {recipe.notes && recipe.notes.length > 0 && (
              <div style={{ marginTop: '30px' }}>
                <h3 style={{ color: '#444', marginBottom: '15px' }}>Notes</h3>
                <ul style={{ 
                  listStyleType: 'disc',
                  paddingLeft: '20px'
                }}>
                  {recipe.notes.map((note, idx) => (
                    <li key={idx} style={{ marginBottom: '8px' }}>{note}</li>
                  ))}
                </ul>
              </div>
            )}

            {recipe.nutrition && (
              <div style={{ marginTop: '30px' }}>
                <h3 style={{ color: '#444', marginBottom: '15px' }}>Nutritional Information</h3>
                <div style={{ 
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: '10px'
                }}>
                  <div><strong>Calories:</strong> {recipe.nutrition.calories}</div>
                  <div><strong>Protein:</strong> {recipe.nutrition.protein}g</div>
                  <div><strong>Carbs:</strong> {recipe.nutrition.carbs}g</div>
                  <div><strong>Fat:</strong> {recipe.nutrition.fat}g</div>
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
