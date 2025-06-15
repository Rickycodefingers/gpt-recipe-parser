import React, { useState } from 'react';
import { 
  Container, 
  Typography, 
  Button, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import { Recipe } from './types';
import './App.css';

function App() {
  const [image, setImage] = useState<File | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(0);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
      setRecipe(null);
      setError('');
      setStep(0);
    }
  };

  const handleUpload = async () => {
    if (!image) return;
    setLoading(true);
    setError('');
    setRecipe(null);
    setStep(0);

    try {
      const reader = new FileReader();
      reader.readAsDataURL(image);
      reader.onloadend = async () => {
        const base64data = reader.result as string;
        
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
      setError(err instanceof Error ? err.message : 'An error occurred while processing the image');
      setLoading(false);
    }
  };

  const nextStep = () => setStep((s) => s + 1);
  const prevStep = () => setStep((s) => Math.max(0, s - 1));

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Recipe Image to Table
        </Typography>
        
        <Box sx={{ mb: 3 }}>
          <input
            accept="image/*"
            style={{ display: 'none' }}
            id="image-upload"
            type="file"
            onChange={handleImageChange}
          />
          <label htmlFor="image-upload">
            <Button
              variant="contained"
              component="span"
              sx={{ mr: 2 }}
            >
              Choose Image
            </Button>
          </label>
          <Button
            variant="contained"
            color="primary"
            onClick={handleUpload}
            disabled={!image || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Upload & Extract'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {recipe && (
          <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
            <Typography variant="h4" component="h2" gutterBottom>
              {recipe.title}
            </Typography>
            
            <Typography variant="h5" component="h3" gutterBottom sx={{ mt: 3 }}>
              Ingredients
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>QTY</TableCell>
                    <TableCell>Ingredient</TableCell>
                    <TableCell>Notes</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {recipe.ingredients.map((ingredient, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{ingredient.amount}</TableCell>
                      <TableCell>{ingredient.item}</TableCell>
                      <TableCell>{ingredient.notes || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h5" component="h3" gutterBottom sx={{ mt: 4 }}>
              Instructions
            </Typography>
            {recipe.instructions.length > 0 && (
              <Paper variant="outlined" sx={{ p: 3, bgcolor: 'grey.50' }}>
                <Typography variant="body1" paragraph>
                  <strong>Step {step + 1}:</strong> {recipe.instructions[step]}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="contained"
                    onClick={prevStep}
                    disabled={step === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="contained"
                    onClick={nextStep}
                    disabled={step === recipe.instructions.length - 1}
                  >
                    Next
                  </Button>
                </Box>
              </Paper>
            )}
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App; 