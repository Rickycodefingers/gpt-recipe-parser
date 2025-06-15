export interface Ingredient {
  item: string;
  amount: string;
  notes?: string;
}

export interface Recipe {
  title: string;
  ingredients: Ingredient[];
  instructions: string[];
} 