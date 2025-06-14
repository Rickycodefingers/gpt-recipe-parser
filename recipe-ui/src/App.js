import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [image, setImage] = useState(null);
  const [recipe, setRecipe] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);
  const [useMetric, setUseMetric] = useState(true);
  const [savedRecipes, setSavedRecipes] = useState([]);
  const [showSaveForm, setShowSaveForm] = useState(false);
  const [recipeDetails, setRecipeDetails] = useState({
    title: '',
    author: '',
    source: '',
    notes: ''
  });

  // Load saved recipes from localStorage on component mount
  useEffect(() => {
    const saved = localStorage.getItem('savedRecipes');
    if (saved) {
      setSavedRecipes(JSON.parse(saved));
    }
  }, []);

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
    const formData = new FormData();
    formData.append('image', image);
    try {
      const response = await fetch('http://127.0.0.1:5000/api/recipe', {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Failed to extract recipe.');
      const data = await response.json();
      setRecipe(data);
      // Pre-fill the title in the save form
      setRecipeDetails(prev => ({ ...prev, title: data.title }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRecipe = () => {
    const newRecipe = {
      ...recipe,
      ...recipeDetails,
      id: Date.now(), // Simple unique ID
      savedAt: new Date().toISOString()
    };
    
    const updatedRecipes = [...savedRecipes, newRecipe];
    setSavedRecipes(updatedRecipes);
    localStorage.setItem('savedRecipes', JSON.stringify(updatedRecipes));
    setShowSaveForm(false);
    setRecipeDetails({ title: '', author: '', source: '', notes: '' });
  };

  const handleViewRecipe = (savedRecipe) => {
    setRecipe(savedRecipe);
    setStep(0);
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
        
        {recipe && !showSaveForm && (
          <div style={{ 
            marginTop: '32px', 
            textAlign: 'left', 
            maxWidth: '800px',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            color: 'black'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ color: '#333', margin: 0 }}>{recipe.title}</h2>
              <button 
                onClick={() => setShowSaveForm(true)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Save Recipe
              </button>
            </div>
            
            <h3 style={{ color: '#444', marginBottom: '15px' }}>
              Ingredients
              <button 
                onClick={() => setUseMetric(!useMetric)}
                style={{
                  marginLeft: '15px',
                  padding: '4px 8px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.8em'
                }}
              >
                Switch to {useMetric ? 'Imperial' : 'Metric'}
              </button>
            </h3>
            <div style={{ 
              marginBottom: '30px',
              overflowX: 'auto'
            }}>
              <table style={{ 
                width: '100%',
                borderCollapse: 'collapse',
                backgroundColor: 'white'
              }}>
                <thead>
                  <tr style={{ 
                    backgroundColor: '#f5f5f5',
                    borderBottom: '2px solid #ddd'
                  }}>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Qty</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Measurement</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Ingredient</th>
                    <th style={{ padding: '12px', textAlign: 'left' }}>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {recipe.ingredients && recipe.ingredients.map((ingredient, idx) => {
                    // Parse the ingredient string
                    const parts = ingredient.match(/^([\d\s\/]+)?\s*(g|ml|oz|fl oz|cup|teaspoon|tablespoon|tbsp|tsp|lb|small|medium|large)?\s*(?:\(([^)]+)\))?\s*(.+?)(?:\(([^)]+)\))?$/i);
                    
                    let qty = '', measurement = '', name = '', notes = '';
                    
                    if (parts) {
                      const imperial = parts[3]?.trim() || '';
                      name = parts[4]?.trim() || '';
                      notes = parts[5]?.trim() || '';

                      if (useMetric) {
                        qty = parts[1]?.trim() || '';
                        measurement = parts[2]?.trim() || '';
                      } else {
                        // Extract imperial measurements
                        const imperialMatch = imperial.match(/^([\d\s\/]+)\s*(oz|fl oz|cup|lb|tbsp|tsp)/i);
                        if (imperialMatch) {
                          qty = imperialMatch[1]?.trim() || '';
                          measurement = imperialMatch[2]?.trim() || '';
                        } else {
                          qty = parts[1]?.trim() || '';
                          measurement = parts[2]?.trim() || '';
                        }
                      }

                      // Clean up the ingredient name by removing any remaining measurements
                      name = name.replace(/^\([^)]+\)\s*/, '').trim();
                    } else {
                      // If parsing fails, just show the full ingredient
                      name = ingredient;
                    }

                    return (
                      <tr key={idx} style={{ 
                        borderBottom: '1px solid #ddd',
                        '&:hover': { backgroundColor: '#f9f9f9' }
                      }}>
                        <td style={{ padding: '12px' }}>{qty}</td>
                        <td style={{ padding: '12px' }}>{measurement}</td>
                        <td style={{ padding: '12px' }}>{name}</td>
                        <td style={{ padding: '12px' }}>{notes}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

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

        {showSaveForm && (
          <div style={{
            marginTop: '32px',
            textAlign: 'left',
            maxWidth: '800px',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            color: 'black'
          }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>Save Recipe</h2>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Recipe Name:</label>
              <input
                type="text"
                value={recipeDetails.title}
                onChange={(e) => setRecipeDetails(prev => ({ ...prev, title: e.target.value }))}
                style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Author:</label>
              <input
                type="text"
                value={recipeDetails.author}
                onChange={(e) => setRecipeDetails(prev => ({ ...prev, author: e.target.value }))}
                style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Source:</label>
              <input
                type="text"
                value={recipeDetails.source}
                onChange={(e) => setRecipeDetails(prev => ({ ...prev, source: e.target.value }))}
                style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px' }}>Notes:</label>
              <textarea
                value={recipeDetails.notes}
                onChange={(e) => setRecipeDetails(prev => ({ ...prev, notes: e.target.value }))}
                style={{ width: '100%', padding: '8px', marginBottom: '10px', minHeight: '100px' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                onClick={handleSaveRecipe}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Save
              </button>
              <button
                onClick={() => setShowSaveForm(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {savedRecipes.length > 0 && !recipe && (
          <div style={{
            marginTop: '32px',
            textAlign: 'left',
            maxWidth: '800px',
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            color: 'black'
          }}>
            <h2 style={{ color: '#333', marginBottom: '20px' }}>Saved Recipes</h2>
            <div style={{ display: 'grid', gap: '10px' }}>
              {savedRecipes.map((savedRecipe) => (
                <div
                  key={savedRecipe.id}
                  style={{
                    padding: '15px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                  onClick={() => handleViewRecipe(savedRecipe)}
                >
                  <h3 style={{ margin: '0 0 5px 0' }}>{savedRecipe.title}</h3>
                  {savedRecipe.author && <p style={{ margin: '0 0 5px 0' }}>By: {savedRecipe.author}</p>}
                  {savedRecipe.source && <p style={{ margin: '0 0 5px 0' }}>Source: {savedRecipe.source}</p>}
                  <p style={{ margin: 0, fontSize: '0.8em', color: '#666' }}>
                    Saved on: {new Date(savedRecipe.savedAt).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;
