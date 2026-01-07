import { useState, useEffect } from 'react';
import { toast, Toaster } from 'sonner';
import { 
  Heart, 
  BookOpen, 
  Settings as SettingsIcon, 
  Home as HomeIcon,
  Plus,
  X,
  Sun,
  Moon,
  ChefHat,
  Clock,
  Users,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Play,
  Search as SearchIcon,
  Filter,
  Grid3x3,
  List as ListIcon,
  Trash2,
  Link as LinkIcon,
  Sparkles,
  RotateCcw,
  Code,
  CheckCircle,
  XCircle,
  HelpCircle
} from 'lucide-react';
import { Header } from './components/Header';
import { ProfileAvatar } from './components/ProfileAvatar';
import { RecipeCard } from './components/RecipeCard';
import { BreadcrumbNav } from './components/BreadcrumbNav';
import { EmptyState } from './components/EmptyState';
import { TimerWidget } from './components/TimerWidget';
import { AIRemixModal } from './components/AIRemixModal';

// Types
interface Profile {
  id: string;
  name: string;
  color: string;
}

interface Recipe {
  id: string;
  title: string;
  image: string;
  cookTime: number;
  prepTime: number;
  servings: number;
  rating: number;
  source: string;
  ingredients: string[];
  instructions: string[];
  nutrition?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
  };
  aiTips?: string[];
}

interface RecipeList {
  id: string;
  name: string;
  recipeIds: string[];
}

type Screen = 
  | { type: 'profile-selector' }
  | { type: 'home' }
  | { type: 'search'; query: string }
  | { type: 'recipe-detail'; recipeId: string; fromScreen?: Screen; initialTab?: 'ingredients' | 'instructions' | 'nutrition' | 'tips' }
  | { type: 'play-mode'; recipeId: string; currentStep: number }
  | { type: 'favorites' }
  | { type: 'lists' }
  | { type: 'list-detail'; listId: string }
  | { type: 'all-recipes' }
  | { type: 'settings' };

// Mock Data
const MOCK_RECIPES: Recipe[] = [
  {
    id: '1',
    title: 'Classic Margherita Pizza',
    image: 'https://images.unsplash.com/photo-1604068549290-dea0e4a305ca?w=800&h=600&fit=crop',
    cookTime: 15,
    prepTime: 90,
    servings: 4,
    rating: 4.8,
    source: '101 Cookbooks',
    ingredients: [
      '500g pizza dough',
      '200g San Marzano tomatoes',
      '250g fresh mozzarella',
      'Fresh basil leaves',
      '2 tbsp olive oil',
      'Salt to taste'
    ],
    instructions: [
      'Preheat your oven to 475°F (245°C) with a pizza stone inside for at least 30 minutes.',
      'Roll out the pizza dough on a floured surface to about 12 inches in diameter.',
      'Spread the crushed San Marzano tomatoes evenly over the dough, leaving a 1-inch border.',
      'Tear the fresh mozzarella into pieces and distribute evenly over the sauce.',
      'Drizzle with olive oil and add a pinch of salt.',
      'Carefully transfer to the hot pizza stone and bake for 12-15 minutes until the crust is golden.',
      'Remove from oven, top with fresh basil leaves, slice and serve immediately.'
    ],
    nutrition: {
      calories: 285,
      protein: 12,
      carbs: 38,
      fat: 9
    },
    aiTips: [
      'Use a pizza stone preheated for at least 30 minutes for a crispier crust',
      'Fresh mozzarella should be patted dry to avoid a soggy pizza',
      'Add basil after baking to preserve its fresh flavor'
    ]
  },
  {
    id: '2',
    title: 'Creamy Garlic Butter Shrimp',
    image: 'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=800&h=600&fit=crop',
    cookTime: 15,
    prepTime: 10,
    servings: 4,
    rating: 4.9,
    source: 'BBC Food',
    ingredients: [
      '1 lb large shrimp, peeled and deveined',
      '4 tbsp butter',
      '6 cloves garlic, minced',
      '1/2 cup heavy cream',
      '1/4 cup chicken broth',
      '2 tbsp fresh parsley',
      'Salt and pepper to taste',
      'Red pepper flakes (optional)'
    ],
    instructions: [
      'Pat the shrimp dry with paper towels and season with salt and pepper.',
      'Heat 2 tablespoons of butter in a large skillet over medium-high heat.',
      'Add shrimp in a single layer and cook for 2 minutes per side until pink. Remove and set aside.',
      'In the same skillet, add remaining butter and minced garlic. Sauté for 1 minute until fragrant.',
      'Pour in chicken broth and heavy cream, stirring to combine.',
      'Let the sauce simmer for 3-4 minutes until slightly thickened.',
      'Return shrimp to the pan, toss to coat, and cook for 1 more minute.',
      'Garnish with fresh parsley and red pepper flakes if desired. Serve over pasta or rice.'
    ],
    nutrition: {
      calories: 245,
      protein: 24,
      carbs: 5,
      fat: 14
    },
    aiTips: [
      'Don\'t overcook shrimp - they should be pink and slightly curled',
      'Use freshly minced garlic for the best flavor',
      'Serve immediately while the sauce is hot and creamy'
    ]
  },
  {
    id: '3',
    title: 'Chocolate Chip Cookies',
    image: 'https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=800&h=600&fit=crop',
    cookTime: 12,
    prepTime: 15,
    servings: 24,
    rating: 4.7,
    source: 'Baker\'s Corner',
    ingredients: [
      '2 1/4 cups all-purpose flour',
      '1 tsp baking soda',
      '1 tsp salt',
      '1 cup butter, softened',
      '3/4 cup granulated sugar',
      '3/4 cup brown sugar',
      '2 large eggs',
      '2 tsp vanilla extract',
      '2 cups chocolate chips'
    ],
    instructions: [
      'Preheat oven to 375°F (190°C).',
      'Mix flour, baking soda, and salt in a bowl. Set aside.',
      'In a large bowl, beat butter and both sugars until creamy.',
      'Add eggs and vanilla, beating until well combined.',
      'Gradually stir in the flour mixture until just combined.',
      'Fold in chocolate chips.',
      'Drop rounded tablespoons of dough onto ungreased cookie sheets.',
      'Bake for 10-12 minutes or until golden brown.',
      'Cool on baking sheet for 2 minutes, then transfer to a wire rack.'
    ],
    nutrition: {
      calories: 165,
      protein: 2,
      carbs: 22,
      fat: 8
    }
  },
  {
    id: '4',
    title: 'Thai Green Curry',
    image: 'https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=800&h=600&fit=crop',
    cookTime: 25,
    prepTime: 15,
    servings: 4,
    rating: 4.6,
    source: 'A Cozy Kitchen',
    ingredients: [
      '2 tbsp green curry paste',
      '1 can coconut milk',
      '1 lb chicken breast, sliced',
      '1 cup bamboo shoots',
      '1 red bell pepper, sliced',
      '2 Thai eggplants, quartered',
      '1 tbsp fish sauce',
      '1 tbsp palm sugar',
      'Thai basil leaves',
      'Jasmine rice for serving'
    ],
    instructions: [
      'Heat a large pan or wok over medium-high heat.',
      'Add curry paste and cook for 1-2 minutes, stirring constantly.',
      'Pour in half the coconut milk and stir to combine with the paste.',
      'Add chicken and cook for 5-7 minutes until no longer pink.',
      'Add remaining coconut milk, vegetables, fish sauce, and palm sugar.',
      'Simmer for 10-15 minutes until vegetables are tender.',
      'Stir in Thai basil just before serving.',
      'Serve hot over jasmine rice.'
    ],
    nutrition: {
      calories: 385,
      protein: 28,
      carbs: 18,
      fat: 22
    }
  },
  {
    id: '5',
    title: 'Caesar Salad',
    image: 'https://images.unsplash.com/photo-1546793665-c74683f339c1?w=800&h=600&fit=crop',
    cookTime: 10,
    prepTime: 15,
    servings: 4,
    rating: 4.5,
    source: 'A Beautiful Mess',
    ingredients: [
      '2 romaine lettuce heads',
      '1/2 cup Caesar dressing',
      '1 cup croutons',
      '1/2 cup grated Parmesan',
      '2 chicken breasts, grilled',
      'Black pepper to taste',
      'Lemon wedges for serving'
    ],
    instructions: [
      'Wash and chop romaine lettuce into bite-sized pieces.',
      'Grill chicken breasts and let rest for 5 minutes, then slice.',
      'In a large bowl, toss lettuce with Caesar dressing.',
      'Add croutons and half the Parmesan cheese.',
      'Divide salad among plates.',
      'Top with sliced chicken and remaining Parmesan.',
      'Finish with freshly ground black pepper and lemon wedges.'
    ],
    nutrition: {
      calories: 320,
      protein: 26,
      carbs: 12,
      fat: 19
    }
  },
  {
    id: '6',
    title: 'Beef Tacos',
    image: 'https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=800&h=600&fit=crop',
    cookTime: 20,
    prepTime: 10,
    servings: 6,
    rating: 4.8,
    source: 'A Couple Cooks',
    ingredients: [
      '1 lb ground beef',
      '1 packet taco seasoning',
      '12 taco shells',
      '2 cups shredded lettuce',
      '1 cup diced tomatoes',
      '1 cup shredded cheese',
      '1/2 cup sour cream',
      'Salsa for serving'
    ],
    instructions: [
      'Brown the ground beef in a large skillet over medium-high heat.',
      'Drain excess fat from the beef.',
      'Add taco seasoning and water according to package directions.',
      'Simmer for 5 minutes until sauce thickens.',
      'Warm taco shells according to package directions.',
      'Fill each taco shell with seasoned beef.',
      'Top with lettuce, tomatoes, cheese, and sour cream.',
      'Serve with salsa on the side.'
    ],
    nutrition: {
      calories: 295,
      protein: 18,
      carbs: 24,
      fat: 14
    }
  }
];

const PROFILE_COLORS = [
  '#d97850', '#8fae6f', '#c9956b', '#6b9dad', '#d16b6b',
  '#9d80b8', '#e6a05f', '#6bb8a5', '#c77a9e', '#7d9e6f'
];

const RECIPE_SOURCES = [
  { name: 'AllRecipes', url: 'https://www.allrecipes.com/' },
  { name: 'BBC Good Food', url: 'https://www.bbcgoodfood.com/' },
  { name: 'BBC Food', url: 'https://www.bbc.co.uk/food' },
  { name: 'Bon Appétit', url: 'https://www.bonappetit.com/' },
  { name: 'Budget Bytes', url: 'https://www.budgetbytes.com/' },
  { name: 'Delish', url: 'https://www.delish.com/' },
  { name: 'Epicurious', url: 'https://www.epicurious.com/' },
  { name: 'Food Network', url: 'https://www.foodnetwork.com/' },
  { name: 'Jamie Oliver', url: 'https://www.jamieoliver.com/' },
  { name: 'Serious Eats', url: 'https://www.seriouseats.com/' },
  { name: 'Simply Recipes', url: 'https://www.simplyrecipes.com/' },
  { name: 'Taste of Home', url: 'https://www.tasteofhome.com/' },
  { name: 'The Kitchn', url: 'https://www.thekitchn.com/' },
  { name: 'NYT Cooking', url: 'https://cooking.nytimes.com/' },
  { name: 'Food52', url: 'https://food52.com/' }
];

export default function App() {
  // State
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null);
  const [screen, setScreen] = useState<Screen>({ type: 'profile-selector' });
  const [favorites, setFavorites] = useState<Record<string, string[]>>({}); // profileId -> recipeIds
  const [lists, setLists] = useState<Record<string, RecipeList[]>>({}); // profileId -> lists
  const [recentRecipes, setRecentRecipes] = useState<Record<string, Array<{ id: string; timestamp: number }>>>({}); // profileId -> recipe entries with timestamps
  const [searchQuery, setSearchQuery] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [timers, setTimers] = useState<Array<{ id: string; label: string; duration: number }>>([]);
  
  // Profile selector state
  const [showCreateProfile, setShowCreateProfile] = useState(false);
  const [newProfileName, setNewProfileName] = useState('');
  const [selectedProfileColor, setSelectedProfileColor] = useState(PROFILE_COLORS[0]);
  
  // Recipe detail state
  const [activeRecipeTab, setActiveRecipeTab] = useState<'ingredients' | 'instructions' | 'nutrition' | 'tips'>('ingredients');
  const [showListPicker, setShowListPicker] = useState(false);
  const [pendingRecipeToAdd, setPendingRecipeToAdd] = useState<string | null>(null);
  const [adjustedServings, setAdjustedServings] = useState<{ [recipeId: string]: number }>({});
  const [isAdjustingServings, setIsAdjustingServings] = useState(false);
  const [showAIRemixModal, setShowAIRemixModal] = useState(false);
  const [remixingRecipeId, setRemixingRecipeId] = useState<string | null>(null);
  const [remixedRecipes, setRemixedRecipes] = useState<Recipe[]>([]);
  const [unitPreference, setUnitPreference] = useState<'metric' | 'imperial'>('metric');
  const [isMetaInfoCollapsed, setIsMetaInfoCollapsed] = useState(() => {
    // Collapse by default on mobile (screens smaller than 640px)
    return window.innerWidth < 640;
  });

  // AI Settings state
  const [settingsTab, setSettingsTab] = useState<'general' | 'ai-prompts' | 'sources' | 'source-selectors'>('general');
  const [openRouterApiKey, setOpenRouterApiKey] = useState('');
  const [enabledSources, setEnabledSources] = useState<Record<string, boolean>>(() => {
    // Initialize all sources as enabled by default
    const initial: Record<string, boolean> = {};
    RECIPE_SOURCES.forEach(source => {
      initial[source.name] = true;
    });
    return initial;
  });
  const [aiPrompts, setAiPrompts] = useState({
    recipeRemix: {
      prompt: `You are a culinary expert helping to remix recipes. Given a recipe and a user's modification request, provide creative suggestions while maintaining the dish's essence. Consider dietary restrictions, ingredient substitutions, and cooking methods. Be specific and practical in your recommendations.`,
      model: 'anthropic/claude-3-haiku'
    },
    servingAdjustment: {
      prompt: `You are a precise culinary calculator. Adjust ingredient quantities proportionally based on the new serving size. Maintain proper ratios for baking recipes. Consider that some ingredients like salt and spices don't scale linearly. Provide exact measurements in both metric and imperial units.`,
      model: 'anthropic/claude-3-haiku'
    },
    tipsGeneration: {
      prompt: `You are an experienced chef providing cooking tips. Generate 3-5 practical, actionable tips for this recipe. Focus on technique improvements, ingredient quality, timing, common mistakes to avoid, and serving suggestions. Keep tips concise and easy to understand.`,
      model: 'anthropic/claude-3-haiku'
    },
    nutritionAnalysis: {
      prompt: `You are a nutritionist analyzing recipes. Calculate approximate nutritional values per serving including calories, protein, carbohydrates, and fats. Consider cooking methods and ingredient combinations. Provide brief health insights or dietary notes if relevant.`,
      model: 'anthropic/claude-3-haiku'
    }
  });
  const [editingPrompt, setEditingPrompt] = useState<string | null>(null);
  const [tempPromptValue, setTempPromptValue] = useState('');
  const [tempModelValue, setTempModelValue] = useState('');

  // Source Selectors state
  type SourceSelectorStatus = 'untested' | 'working' | 'broken';
  const [sourceSelectors, setSourceSelectors] = useState<Record<string, {
    cssSelector: string;
    status: SourceSelectorStatus;
    lastTested: number | null;
    failCount: number;
  }>>(() => {
    const initial: Record<string, { cssSelector: string; status: SourceSelectorStatus; lastTested: number | null; failCount: number }> = {};
    RECIPE_SOURCES.forEach(source => {
      initial[source.name] = {
        cssSelector: '.recipe-content',
        status: 'untested',
        lastTested: null,
        failCount: 0
      };
    });
    return initial;
  });

  // Handle initial tab when navigating to recipe detail
  useEffect(() => {
    if (screen.type === 'recipe-detail' && screen.initialTab) {
      setActiveRecipeTab(screen.initialTab);
    }
  }, [screen]);

  // Set collapsed state based on screen size on mount and resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 640) {
        setIsMetaInfoCollapsed(true);
      } else {
        setIsMetaInfoCollapsed(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Reset search page when query changes
  useEffect(() => {
    if (screen.type === 'search') {
      setSearchPage(1);
    }
  }, [screen.type === 'search' ? screen.query : null]);
  
  // Lists state
  const [showCreateList, setShowCreateList] = useState(false);
  const [newListName, setNewListName] = useState('');
  
  // Home view state
  const [homeView, setHomeView] = useState<'favorites' | 'discover'>('favorites');

  // Search pagination state
  const [searchPage, setSearchPage] = useState(1);
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const RESULTS_PER_PAGE = 6;

  // Load from localStorage
  useEffect(() => {
    const savedProfiles = localStorage.getItem('cookie-profiles');
    const savedFavorites = localStorage.getItem('cookie-favorites');
    const savedLists = localStorage.getItem('cookie-lists');
    const savedRecent = localStorage.getItem('cookie-recent');
    const savedRemixed = localStorage.getItem('cookie-remixed');
    const savedTheme = localStorage.getItem('cookie-theme');
    const savedApiKey = localStorage.getItem('cookie-openrouter-api-key');
    const savedAiPrompts = localStorage.getItem('cookie-ai-prompts');
    const savedEnabledSources = localStorage.getItem('cookie-enabled-sources');

    if (savedProfiles) {
      setProfiles(JSON.parse(savedProfiles));
    }
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
    if (savedLists) {
      setLists(JSON.parse(savedLists));
    }
    if (savedRecent) {
      setRecentRecipes(JSON.parse(savedRecent));
    }
    if (savedRemixed) {
      setRemixedRecipes(JSON.parse(savedRemixed));
    }
    if (savedTheme === 'dark') {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
    if (savedApiKey) {
      setOpenRouterApiKey(savedApiKey);
    }
    if (savedAiPrompts) {
      setAiPrompts(JSON.parse(savedAiPrompts));
    }
    if (savedEnabledSources) {
      setEnabledSources(JSON.parse(savedEnabledSources));
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    localStorage.setItem('cookie-profiles', JSON.stringify(profiles));
  }, [profiles]);

  useEffect(() => {
    localStorage.setItem('cookie-favorites', JSON.stringify(favorites));
  }, [favorites]);

  useEffect(() => {
    localStorage.setItem('cookie-lists', JSON.stringify(lists));
  }, [lists]);

  useEffect(() => {
    localStorage.setItem('cookie-recent', JSON.stringify(recentRecipes));
  }, [recentRecipes]);

  useEffect(() => {
    localStorage.setItem('cookie-remixed', JSON.stringify(remixedRecipes));
  }, [remixedRecipes]);

  useEffect(() => {
    localStorage.setItem('cookie-openrouter-api-key', openRouterApiKey);
  }, [openRouterApiKey]);

  useEffect(() => {
    localStorage.setItem('cookie-ai-prompts', JSON.stringify(aiPrompts));
  }, [aiPrompts]);

  useEffect(() => {
    localStorage.setItem('cookie-enabled-sources', JSON.stringify(enabledSources));
  }, [enabledSources]);

  // Toggle dark mode
  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
    localStorage.setItem('cookie-theme', !isDarkMode ? 'dark' : 'light');
  };

  // Profile management
  const createProfile = (name: string, color: string) => {
    const newProfile: Profile = {
      id: Date.now().toString(),
      name,
      color
    };
    setProfiles([...profiles, newProfile]);
    setCurrentProfile(newProfile);
    setScreen({ type: 'home' });
    toast.success(`Welcome, ${name}!`);
  };

  const selectProfile = (profile: Profile) => {
    setCurrentProfile(profile);
    setScreen({ type: 'home' });
  };

  const deleteProfile = (profileId: string) => {
    setProfiles(profiles.filter(p => p.id !== profileId));
    if (currentProfile?.id === profileId) {
      setCurrentProfile(null);
      setScreen({ type: 'profile-selector' });
    }
    toast.success('Profile deleted');
  };

  // Recipe interactions
  const toggleFavorite = (recipeId: string) => {
    if (!currentProfile) return;
    
    const profileFavorites = favorites[currentProfile.id] || [];
    const isFavorite = profileFavorites.includes(recipeId);
    
    if (isFavorite) {
      setFavorites({
        ...favorites,
        [currentProfile.id]: profileFavorites.filter(id => id !== recipeId)
      });
      toast.success('Removed from favorites');
    } else {
      setFavorites({
        ...favorites,
        [currentProfile.id]: [...profileFavorites, recipeId]
      });
      toast.success('Added to favorites');
    }
  };

  const addToRecent = (recipeId: string) => {
    if (!currentProfile) return;
    
    const profileRecent = recentRecipes[currentProfile.id] || [];
    const filtered = profileRecent.filter(entry => entry.id !== recipeId);
    setRecentRecipes({
      ...recentRecipes,
      [currentProfile.id]: [{ id: recipeId, timestamp: Date.now() }, ...filtered]
    });
  };

  const viewRecipe = (recipeId: string, options?: { fromScreen?: Screen; initialTab?: 'ingredients' | 'instructions' | 'nutrition' | 'tips' }) => {
    addToRecent(recipeId);
    setScreen({ type: 'recipe-detail', recipeId, fromScreen: options?.fromScreen, initialTab: options?.initialTab });
  };

  // AI Serving Adjustment
  const adjustServings = (recipeId: string, newServings: number) => {
    setIsAdjustingServings(true);
    
    // Simulate AI processing time
    setTimeout(() => {
      setAdjustedServings({
        ...adjustedServings,
        [recipeId]: newServings
      });
      setIsAdjustingServings(false);
      toast.success(`Recipe adjusted for ${newServings} servings`);
    }, 800);
  };

  const resetServings = (recipeId: string) => {
    const newAdjusted = { ...adjustedServings };
    delete newAdjusted[recipeId];
    setAdjustedServings(newAdjusted);
    toast.success('Reset to original servings');
  };

  // AI Recipe Remix
  const handleRemixRecipe = (prompt: string, newName: string) => {
    if (!remixingRecipeId) return;
    
    const originalRecipe = getRecipe(remixingRecipeId);
    if (!originalRecipe) return;

    // Create a remixed version of the recipe
    const remixedRecipe: Recipe = {
      ...originalRecipe,
      id: `remix-${Date.now()}`,
      title: newName,
      source: `AI Remix of ${originalRecipe.source}`,
      aiTips: [
        `This is an AI-remixed version of ${originalRecipe.title}`,
        `Modification: ${prompt}`,
        ...(originalRecipe.aiTips || [])
      ]
    };

    // Add to remixed recipes list
    setRemixedRecipes([...remixedRecipes, remixedRecipe]);
    
    // Add to recent recipes
    addToRecent(remixedRecipe.id);
    
    // Close modal and navigate to new recipe
    setShowAIRemixModal(false);
    setRemixingRecipeId(null);
    
    toast.success('Recipe remix created! Check your recently viewed recipes.');
    
    // Navigate to the new remixed recipe
    viewRecipe(remixedRecipe.id);
  };

  const openRemixModal = (recipeId: string) => {
    setRemixingRecipeId(recipeId);
    setShowAIRemixModal(true);
  };

  const getAdjustedRecipe = (recipe: Recipe): Recipe => {
    const currentServings = adjustedServings[recipe.id];
    if (!currentServings || currentServings === recipe.servings) {
      return recipe;
    }

    const scale = currentServings / recipe.servings;
    
    // Scale ingredients (simple multiplication for demo)
    const scaledIngredients = recipe.ingredients.map(ing => {
      // Try to find and scale numbers in ingredient strings
      return ing.replace(/(\d+(?:\.\d+)?(?:\/\d+)?)/g, (match) => {
        let num: number;
        if (match.includes('/')) {
          const [numerator, denominator] = match.split('/').map(Number);
          num = numerator / denominator;
        } else {
          num = parseFloat(match);
        }
        const scaled = num * scale;
        // Round to reasonable precision
        if (scaled < 1) return scaled.toFixed(2).replace(/\.?0+$/, '');
        if (scaled % 1 === 0) return scaled.toString();
        return scaled.toFixed(1).replace(/\.0$/, '');
      });
    });

    // Scale nutrition
    const scaledNutrition = recipe.nutrition ? {
      calories: Math.round(recipe.nutrition.calories * scale),
      protein: Math.round(recipe.nutrition.protein * scale),
      carbs: Math.round(recipe.nutrition.carbs * scale),
      fat: Math.round(recipe.nutrition.fat * scale)
    } : undefined;

    // Add AI note to tips if they exist
    const scaledTips = recipe.aiTips ? [
      `Recipe has been adjusted from ${recipe.servings} to ${currentServings} servings`,
      ...recipe.aiTips
    ] : undefined;

    return {
      ...recipe,
      servings: currentServings,
      ingredients: scaledIngredients,
      nutrition: scaledNutrition,
      aiTips: scaledTips
    };
  };

  // List management
  const createList = (name: string) => {
    if (!currentProfile) return;
    
    const newList: RecipeList = {
      id: Date.now().toString(),
      name,
      recipeIds: pendingRecipeToAdd ? [pendingRecipeToAdd] : []
    };
    
    const profileLists = lists[currentProfile.id] || [];
    setLists({
      ...lists,
      [currentProfile.id]: [...profileLists, newList]
    });
    
    if (pendingRecipeToAdd) {
      toast.success(`Added to "${name}"`);
      setPendingRecipeToAdd(null);
    } else {
      toast.success('List created');
    }
  };

  const deleteList = (listId: string) => {
    if (!currentProfile) return;
    
    const profileLists = lists[currentProfile.id] || [];
    setLists({
      ...lists,
      [currentProfile.id]: profileLists.filter(l => l.id !== listId)
    });
    toast.success('List deleted');
    setScreen({ type: 'lists' });
  };

  const addRecipeToList = (recipeId: string, listId: string) => {
    if (!currentProfile) return;
    
    const profileLists = lists[currentProfile.id] || [];
    const updatedLists = profileLists.map(list => {
      if (list.id === listId && !list.recipeIds.includes(recipeId)) {
        return { ...list, recipeIds: [...list.recipeIds, recipeId] };
      }
      return list;
    });
    
    setLists({
      ...lists,
      [currentProfile.id]: updatedLists
    });
    toast.success('Added to list');
  };

  const removeRecipeFromList = (recipeId: string, listId: string) => {
    if (!currentProfile) return;
    
    const profileLists = lists[currentProfile.id] || [];
    const updatedLists = profileLists.map(list => {
      if (list.id === listId) {
        return { ...list, recipeIds: list.recipeIds.filter(id => id !== recipeId) };
      }
      return list;
    });
    
    setLists({
      ...lists,
      [currentProfile.id]: updatedLists
    });
    toast.success('Removed from list');
  };

  // Search
  const performSearch = (query: string) => {
    setSearchQuery(query);
    setScreen({ type: 'search', query });
  };

  const getSearchResults = (query: string): Recipe[] => {
    const allRecipes = [...MOCK_RECIPES, ...remixedRecipes];
    if (!query.trim()) return allRecipes;
    
    const lowerQuery = query.toLowerCase();
    return allRecipes.filter(recipe => 
      recipe.title.toLowerCase().includes(lowerQuery) ||
      recipe.ingredients.some(ing => ing.toLowerCase().includes(lowerQuery))
    );
  };

  // Get recipe data
  const getRecipe = (id: string) => {
    // Check remixed recipes first
    const remixed = remixedRecipes.find(r => r.id === id);
    if (remixed) return remixed;
    // Then check original recipes
    return MOCK_RECIPES.find(r => r.id === id);
  };
  
  const isFavorite = (recipeId: string) => {
    if (!currentProfile) return false;
    return (favorites[currentProfile.id] || []).includes(recipeId);
  };

  // Render functions
  const renderProfileSelector = () => {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="max-w-4xl w-full px-4 md:px-8">
          <div className="text-center mb-8 md:mb-12">
            <h1 className="text-4xl md:text-5xl mb-3 md:mb-4 text-primary">Cookie</h1>
            <p className="text-lg md:text-xl text-muted-foreground">Who's cooking today?</p>
          </div>

          {!showCreateProfile ? (
            <div className="flex flex-wrap justify-center gap-6 md:gap-8 mb-6 md:mb-8">
              {profiles.map(profile => (
                <div key={profile.id} className="flex flex-col items-center gap-3">
                  <ProfileAvatar
                    name={profile.name}
                    color={profile.color}
                    size="xl"
                    onClick={() => selectProfile(profile)}
                  />
                  <span>{profile.name}</span>
                </div>
              ))}
              <div className="flex flex-col items-center gap-3">
                <button
                  onClick={() => setShowCreateProfile(true)}
                  className="w-32 h-32 rounded-full border-4 border-dashed border-muted flex items-center justify-center text-muted-foreground hover:border-primary hover:text-primary transition-colors"
                >
                  <Plus className="w-12 h-12" />
                </button>
                <span className="text-muted-foreground">Add Profile</span>
              </div>
            </div>
          ) : (
            <div className="bg-card rounded-2xl p-6 md:p-8 max-w-md mx-auto">
              <div className="flex items-center justify-between mb-6">
                <h2>Create Profile</h2>
                <button onClick={() => setShowCreateProfile(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-6 h-6" />
                </button>
              </div>
              
              <div className="space-y-6">
                <div>
                  <label className="block mb-2">Name</label>
                  <input
                    type="text"
                    value={newProfileName}
                    onChange={(e) => setNewProfileName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full h-14 px-4 bg-secondary rounded-lg outline-none focus:ring-2 focus:ring-primary"
                    autoFocus
                  />
                </div>
                
                <div>
                  <label className="block mb-3">Choose a color</label>
                  <div className="grid grid-cols-5 gap-3">
                    {PROFILE_COLORS.map(color => (
                      <button
                        key={color}
                        onClick={() => setSelectedProfileColor(color)}
                        className={`w-12 h-12 rounded-full transition-transform ${
                          selectedProfileColor === color ? 'ring-4 ring-primary scale-110' : ''
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
                
                <button
                  onClick={() => {
                    if (newProfileName.trim()) {
                      createProfile(newProfileName.trim(), selectedProfileColor);
                      setNewProfileName('');
                      setShowCreateProfile(false);
                    }
                  }}
                  disabled={!newProfileName.trim()}
                  className="w-full h-14 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Profile
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderHome = () => {
    const profileFavorites = currentProfile ? (favorites[currentProfile.id] || []) : [];
    const favoriteRecipes = MOCK_RECIPES.filter(r => profileFavorites.includes(r.id));
    
    const profileRecent = currentProfile ? (recentRecipes[currentProfile.id] || []) : [];
    const recentRecipesList = profileRecent
      .map(entry => getRecipe(entry.id))
      .filter(Boolean) as Recipe[];
    
    // AI-suggested recipes for Discover (not in favorites)
    const discoverRecipes = MOCK_RECIPES.filter(r => !profileFavorites.includes(r.id));

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Search and Toggle Bar */}
          <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-4 md:left-5 top-1/2 -translate-y-1/2 w-5 md:w-6 h-5 md:h-6 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search recipes or paste a URL..."
                className="w-full h-14 md:h-16 pl-12 md:pl-16 pr-4 md:pr-5 bg-card rounded-xl shadow-sm outline-none focus:ring-2 focus:ring-primary transition-shadow text-sm md:text-base"
                onFocus={(e) => {
                  const value = e.target.value.trim();
                  if (value) performSearch(value);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const value = (e.target as HTMLInputElement).value.trim();
                    if (value) performSearch(value);
                  }
                }}
              />
            </div>
            
            {/* View Toggle */}
            <div className="inline-flex bg-secondary rounded-lg p-1 w-full md:w-auto">
              <button
                onClick={() => setHomeView('favorites')}
                className={`flex-1 md:flex-initial px-4 md:px-6 h-12 md:h-14 rounded-md transition-all whitespace-nowrap text-sm md:text-base ${
                  homeView === 'favorites' 
                    ? 'bg-card shadow-sm text-foreground' 
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                My Favorites
              </button>
              <button
                onClick={() => setHomeView('discover')}
                className={`flex-1 md:flex-initial px-4 md:px-6 h-12 md:h-14 rounded-md transition-all whitespace-nowrap text-sm md:text-base ${
                  homeView === 'discover' 
                    ? 'bg-card shadow-sm text-foreground' 
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Discover
              </button>
            </div>
          </div>

          {/* My Favorites View */}
          {homeView === 'favorites' && (
            <>
              {/* Recently Viewed */}
              {recentRecipesList.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2>Recently Viewed</h2>
                <button
                  onClick={() => setScreen({ type: 'all-recipes' })}
                  className="text-primary hover:underline text-sm font-medium"
                >
                  View All ({recentRecipesList.length})
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                {recentRecipesList.slice(0, 9).map(recipe => (
                  <RecipeCard
                    key={recipe.id}
                    id={recipe.id}
                    title={recipe.title}
                    image={recipe.image}
                    cookTime={recipe.cookTime}
                    rating={recipe.rating}
                    isFavorite={isFavorite(recipe.id)}
                    onToggleFavorite={toggleFavorite}
                    onClick={() => viewRecipe(recipe.id)}
                    onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                  />
                ))}
              </div>
            </section>
              )}

              {/* All Favorites */}
              {favoriteRecipes.length > 0 ? (
                <section>
                  <h2 className="mb-4">My Favorite Recipes</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                    {favoriteRecipes.map(recipe => (
                      <RecipeCard
                        key={recipe.id}
                        id={recipe.id}
                        title={recipe.title}
                        image={recipe.image}
                        cookTime={recipe.cookTime}
                        rating={recipe.rating}
                        isFavorite={true}
                        onToggleFavorite={toggleFavorite}
                        onClick={() => viewRecipe(recipe.id)}
                        onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                      />
                    ))}
                  </div>
                </section>
              ) : (
                <EmptyState
                  icon={<Heart className="w-10 h-10" />}
                  title="No favorites yet"
                  description="Start adding recipes to your favorites to see them here"
                  action={
                    <button
                      onClick={() => setHomeView('discover')}
                      className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                    >
                      Discover Recipes
                    </button>
                  }
                />
              )}
            </>
          )}

          {/* Discover View */}
          {homeView === 'discover' && (
            <section>
              <div className="mb-4">
                <h2 className="mb-1">Discover New Recipes</h2>
                <p className="text-muted-foreground">AI-suggested recipes based on your preferences</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                {discoverRecipes.map(recipe => (
                  <RecipeCard
                    key={recipe.id}
                    id={recipe.id}
                    title={recipe.title}
                    image={recipe.image}
                    cookTime={recipe.cookTime}
                    rating={recipe.rating}
                    isFavorite={isFavorite(recipe.id)}
                    onToggleFavorite={toggleFavorite}
                    onClick={() => viewRecipe(recipe.id)}
                    onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                  />
                ))}
              </div>
            </section>
          )}
        </div>
      </div>
    );
  };

  const renderSearch = (query: string) => {
    const allResults = getSearchResults(query);
    const isUrl = query.startsWith('http://') || query.startsWith('https://');

    // Get unique sources from results
    const uniqueSources = Array.from(new Set(allResults.map(recipe => recipe.source))).sort();

    // Filter by selected source
    const results = selectedSource 
      ? allResults.filter(recipe => recipe.source === selectedSource)
      : allResults;

    // Pagination logic
    const totalPages = Math.ceil(results.length / RESULTS_PER_PAGE);
    const startIndex = (searchPage - 1) * RESULTS_PER_PAGE;
    const endIndex = startIndex + RESULTS_PER_PAGE;
    const paginatedResults = results.slice(startIndex, endIndex);
    const hasMoreResults = searchPage < totalPages;

    // Simulate load more action
    const handleLoadMore = () => {
      setIsLoadingMore(true);
      setTimeout(() => {
        setSearchPage(searchPage + 1);
        setIsLoadingMore(false);
      }, 800);
    };

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-6">
            <div>
              <h2 className="mb-1">
                {isUrl ? 'Import Recipe' : `Search Results`}
              </h2>
              {!isUrl && (
                <p className="text-muted-foreground text-sm md:text-base">
                  Found {results.length} recipe{results.length !== 1 ? 's' : ''} for "{query}"
                  {selectedSource && ` from ${selectedSource}`}
                </p>
              )}
            </div>
          </div>

          {/* Source Filter */}
          {!isUrl && uniqueSources.length > 1 && (
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-3">
                <Filter className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Filter by source:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => {
                    setSelectedSource(null);
                    setSearchPage(1);
                  }}
                  className={`h-10 px-4 rounded-lg transition-colors text-sm ${
                    selectedSource === null
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-secondary hover:bg-muted'
                  }`}
                >
                  All Sources ({allResults.length})
                </button>
                {uniqueSources.map(source => {
                  const count = allResults.filter(r => r.source === source).length;
                  return (
                    <button
                      key={source}
                      onClick={() => {
                        setSelectedSource(source);
                        setSearchPage(1);
                      }}
                      className={`h-10 px-4 rounded-lg transition-colors text-sm ${
                        selectedSource === source
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary hover:bg-muted'
                      }`}
                    >
                      {source} ({count})
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {isUrl ? (
            <div className="bg-card rounded-xl p-6 md:p-8 text-center max-w-md mx-auto">
              <LinkIcon className="w-12 h-12 text-primary mx-auto mb-4" />
              <h3 className="mb-2">Recipe Import</h3>
              <p className="text-muted-foreground mb-6">
                In a real app, this would scrape and import the recipe from the URL you provided.
              </p>
              <p className="text-sm text-muted-foreground mb-6 break-all">{query}</p>
              <button
                onClick={() => {
                  toast.success('Recipe imported successfully!');
                  setScreen({ type: 'home' });
                }}
                className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
              >
                Simulate Import
              </button>
            </div>
          ) : results.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
                {paginatedResults.map(recipe => (
                  <RecipeCard
                    key={recipe.id}
                    id={recipe.id}
                    title={recipe.title}
                    image={recipe.image}
                    cookTime={recipe.cookTime}
                    rating={recipe.rating}
                    isFavorite={isFavorite(recipe.id)}
                    onToggleFavorite={toggleFavorite}
                    onClick={() => viewRecipe(recipe.id, { fromScreen: screen, initialTab: 'ingredients' })}
                    onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                  />
                ))}
              </div>

              {/* Infinite Scroll Indication */}
              {hasMoreResults && (
                <div className="mt-8 flex flex-col items-center gap-4">
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground mb-2">
                      Showing {paginatedResults.length} of {results.length} results
                    </p>
                    <div className="w-full max-w-xs bg-secondary rounded-full h-2 overflow-hidden">
                      <div 
                        className="bg-primary h-full transition-all duration-300"
                        style={{ width: `${(endIndex / results.length) * 100}%` }}
                      />
                    </div>
                  </div>
                  <button
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                    className="h-12 px-8 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center gap-2"
                  >
                    {isLoadingMore ? (
                      <>
                        <div className="w-5 h-5 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-5 h-5" />
                        Load More Recipes
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* End of Results Indicator */}
              {!hasMoreResults && results.length > RESULTS_PER_PAGE && (
                <div className="mt-8 text-center">
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-secondary/50 rounded-lg text-sm text-muted-foreground">
                    <ChefHat className="w-4 h-4" />
                    You've reached the end of the results
                  </div>
                </div>
              )}
            </>
          ) : (
            <EmptyState
              icon={<SearchIcon className="w-10 h-10" />}
              title="No recipes found"
              description="Try a different search term or browse all recipes from the home screen."
              action={
                <button
                  onClick={() => setScreen({ type: 'home' })}
                  className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Back to Home
                </button>
              }
            />
          )}
        </div>
      </div>
    );
  };

  const renderRecipeDetail = (recipeId: string) => {
    const originalRecipe = getRecipe(recipeId);
    if (!originalRecipe) return null;

    const recipe = getAdjustedRecipe(originalRecipe);
    const isAdjusted = adjustedServings[recipeId] && adjustedServings[recipeId] !== originalRecipe.servings;
    const currentServings = adjustedServings[recipeId] || originalRecipe.servings;

    const profileLists = currentProfile ? (lists[currentProfile.id] || []) : [];

    return (
      <div className="pb-4 md:pb-8">
        {/* Hero Image */}
        <div className="px-4 md:px-6 pt-4 md:pt-8 pb-4 md:pb-6">
          <div className="max-w-6xl mx-auto">
            <div className="relative h-60 md:h-80 rounded-t-xl">
              <div className="overflow-hidden rounded-t-xl h-full">
                <img 
                  src={recipe.image} 
                  alt={recipe.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute inset-0 bg-gradient-to-b from-background/90 via-transparent to-background/90 rounded-t-xl pointer-events-none" />
              
              {/* Title and Rating - Top Left */}
              <div className="absolute top-0 left-0 right-0 p-4 md:p-8 pr-4 md:pr-8 pointer-events-none">
                <div>
                  <h1 className="text-[clamp(1.25rem,5vw,1.5rem)] md:text-[clamp(2rem,4vw,2.5rem)] lg:text-[clamp(2.5rem,5vw,3rem)] mb-1 leading-tight">{recipe.title}</h1>
                  <div className="flex items-center gap-2 text-sm md:text-base">
                    <p>From {recipe.source}</p>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <span className="text-star text-lg">★</span>
                      <span>{recipe.rating.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons - Bottom Right */}
              <div className="absolute bottom-4 right-4 md:bottom-8 md:right-8 flex items-center gap-2 pointer-events-auto">
                {/* Favorite and Collection buttons */}
                <button
                  onClick={() => toggleFavorite(recipe.id)}
                  className={`w-12 h-12 rounded-lg flex items-center justify-center transition-colors backdrop-blur-sm ${
                    isFavorite(recipe.id)
                      ? 'bg-accent/90 text-accent-foreground'
                      : 'bg-card/60 text-foreground hover:bg-card/80'
                  }`}
                  aria-label={isFavorite(recipe.id) ? 'Remove from favorites' : 'Add to favorites'}
                >
                  <Heart className={`w-5 h-5 ${isFavorite(recipe.id) ? 'fill-current' : ''}`} />
                </button>
                
                <div className="relative">
                  <button
                    onClick={() => setShowListPicker(!showListPicker)}
                    className="w-12 h-12 rounded-lg flex items-center justify-center bg-card/60 backdrop-blur-sm text-foreground hover:bg-card/80 transition-colors"
                    aria-label="Save to collection"
                  >
                    <Plus className="w-5 h-5" />
                  </button>
                  
                  {showListPicker && (
                    <div className="absolute right-0 top-14 w-64 bg-popover border border-border rounded-xl shadow-lg p-2 z-50">
                      {profileLists.length > 0 && (
                        <>
                          {profileLists.map(list => (
                            <button
                              key={list.id}
                              onClick={() => {
                                addRecipeToList(recipe.id, list.id);
                                setShowListPicker(false);
                              }}
                              className="w-full text-left px-4 py-3 rounded-lg hover:bg-accent transition-colors"
                            >
                              {list.name}
                            </button>
                          ))}
                          <div className="h-px bg-border my-2" />
                        </>
                      )}
                      <button
                        onClick={() => {
                          setPendingRecipeToAdd(recipe.id);
                          setShowListPicker(false);
                          setShowCreateList(true);
                          setScreen({ type: 'lists' });
                        }}
                        className="w-full text-left px-4 py-3 rounded-lg hover:bg-accent transition-colors flex items-center gap-2 text-primary"
                      >
                        <Plus className="w-4 h-4" />
                        Create New Collection
                      </button>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => openRemixModal(recipe.id)}
                  className="w-12 h-12 sm:w-auto sm:px-4 md:px-5 bg-secondary/90 backdrop-blur-sm text-secondary-foreground rounded-lg hover:bg-secondary transition-colors flex items-center justify-center sm:justify-start gap-2 text-sm md:text-base"
                >
                  <Sparkles className="w-5 h-5" />
                  <span className="hidden sm:inline">Remix</span>
                </button>

                <button
                  onClick={() => setScreen({ type: 'play-mode', recipeId: recipe.id, currentStep: 0 })}
                  className="w-12 h-12 sm:w-auto sm:px-5 md:px-6 bg-primary/90 backdrop-blur-sm text-primary-foreground rounded-lg hover:bg-primary transition-opacity flex items-center justify-center sm:justify-start gap-2 text-sm md:text-base"
                >
                  <Play className="w-5 h-5" />
                  <span className="hidden sm:inline">Cook!</span>
                </button>
              </div>
            </div>
            
            {/* Meta Info */}
            <div className="bg-card rounded-b-xl shadow-lg mb-4 md:mb-6">
              <button
                onClick={() => setIsMetaInfoCollapsed(!isMetaInfoCollapsed)}
                className="sm:hidden w-full p-3 flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {isMetaInfoCollapsed ? (
                  <>
                    <ChevronDown className="w-5 h-5" />
                    <span className="text-sm">Show recipe details</span>
                  </>
                ) : (
                  <>
                    <ChevronUp className="w-5 h-5" />
                    <span className="text-sm">Hide recipe details</span>
                  </>
                )}
              </button>
              
              {!isMetaInfoCollapsed && (
                <div className="flex flex-wrap items-start justify-center gap-4 sm:gap-6 md:gap-12 px-4 md:px-6 sm:pt-6 pb-4 md:pb-6">
                  <div className="flex items-start gap-3">
                    <Clock className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <div className="text-sm text-muted-foreground">Prep Time</div>
                      <div className="font-medium">{recipe.prepTime} min</div>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <Clock className="w-5 h-5 text-muted-foreground mt-0.5" />
                    <div>
                      <div className="text-sm text-muted-foreground">Cook Time</div>
                      <div className="font-medium">{recipe.cookTime} min</div>
                    </div>
                  </div>
                  
                  <div className="flex flex-col items-center">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="w-5 h-5 text-muted-foreground" />
                      <div className="text-sm text-muted-foreground">Servings</div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          if (currentServings > 1) {
                            adjustServings(recipeId, currentServings - 1);
                          }
                        }}
                        disabled={isAdjustingServings || currentServings <= 1}
                        className="w-10 h-10 rounded-lg bg-secondary hover:bg-muted transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="text-lg leading-none">−</span>
                      </button>
                      <div className="w-10 flex flex-col items-center">
                        <div className="font-medium text-lg">{currentServings}</div>
                      </div>
                      <button
                        onClick={() => {
                          adjustServings(recipeId, currentServings + 1);
                        }}
                        disabled={isAdjustingServings}
                        className="w-10 h-10 rounded-lg bg-secondary hover:bg-muted transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <span className="text-lg leading-none">+</span>
                      </button>
                      <button
                        onClick={() => resetServings(recipeId)}
                        disabled={!isAdjusted || isAdjustingServings}
                        className="w-10 h-10 rounded-lg bg-secondary hover:bg-muted transition-colors flex items-center justify-center disabled:opacity-30 disabled:cursor-not-allowed"
                        aria-label="Reset servings"
                      >
                        <RotateCcw className="w-5 h-5 text-muted-foreground" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-1.5">
                    <div className="flex flex-col items-center">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="text-sm text-muted-foreground">Units</div>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setUnitPreference('metric')}
                          className={`px-3 h-10 rounded-lg transition-colors flex items-center justify-center text-sm ${
                            unitPreference === 'metric' 
                              ? 'bg-primary text-primary-foreground' 
                              : 'bg-secondary hover:bg-muted'
                          }`}
                        >
                          Metric
                        </button>
                        <button
                          onClick={() => setUnitPreference('imperial')}
                          className={`px-3 h-10 rounded-lg transition-colors flex items-center justify-center text-sm ${
                            unitPreference === 'imperial' 
                              ? 'bg-primary text-primary-foreground' 
                              : 'bg-secondary hover:bg-muted'
                          }`}
                        >
                          Imperial
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-2 md:gap-4 mb-4 md:mb-6 border-b border-border overflow-x-auto">
              <button
                onClick={() => setActiveRecipeTab('ingredients')}
                className={`pb-3 px-2 transition-colors relative ${
                  activeRecipeTab === 'ingredients' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Ingredients
                {activeRecipeTab === 'ingredients' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
              <button
                onClick={() => setActiveRecipeTab('instructions')}
                className={`pb-3 px-2 transition-colors relative ${
                  activeRecipeTab === 'instructions' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Instructions
                {activeRecipeTab === 'instructions' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                )}
              </button>
              {recipe.nutrition && (
                <button
                  onClick={() => setActiveRecipeTab('nutrition')}
                  className={`pb-3 px-2 transition-colors relative ${
                    activeRecipeTab === 'nutrition' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Nutrition
                  {activeRecipeTab === 'nutrition' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                  )}
                </button>
              )}
              {recipe.aiTips && recipe.aiTips.length > 0 && (
                <button
                  onClick={() => setActiveRecipeTab('tips')}
                  className={`pb-3 px-2 transition-colors relative ${
                    activeRecipeTab === 'tips' ? 'text-primary' : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Cooking Tips
                  {activeRecipeTab === 'tips' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                  )}
                </button>
              )}
            </div>

            {/* Tab Content */}
            <div className="bg-card rounded-xl p-4 md:p-6">
            {activeRecipeTab === 'ingredients' && (
              <div className="space-y-3">
                {recipe.ingredients.map((ingredient, index) => (
                  <div key={index} className="flex items-start gap-4 py-2">
                    <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 text-sm font-medium">
                      {index + 1}
                    </div>
                    <span className="flex-1 pt-0.5">{ingredient}</span>
                  </div>
                ))}
              </div>
            )}

            {activeRecipeTab === 'instructions' && (
              <div className="space-y-3">
                {recipe.instructions.map((instruction, index) => (
                  <div key={index} className="flex items-start gap-4 py-2">
                    <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 text-sm font-medium">
                      {index + 1}
                    </div>
                    <p className="flex-1 leading-relaxed pt-0.5">{instruction}</p>
                  </div>
                ))}
              </div>
            )}

            {activeRecipeTab === 'nutrition' && recipe.nutrition && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                <div className="bg-secondary rounded-xl p-6 text-center">
                  <div className="text-3xl font-medium text-primary mb-1">{recipe.nutrition.calories}</div>
                  <div className="text-sm text-muted-foreground">Calories</div>
                </div>
                <div className="bg-secondary rounded-xl p-6 text-center">
                  <div className="text-3xl font-medium text-primary mb-1">{recipe.nutrition.protein}g</div>
                  <div className="text-sm text-muted-foreground">Protein</div>
                </div>
                <div className="bg-secondary rounded-xl p-6 text-center">
                  <div className="text-3xl font-medium text-primary mb-1">{recipe.nutrition.carbs}g</div>
                  <div className="text-sm text-muted-foreground">Carbs</div>
                </div>
                <div className="bg-secondary rounded-xl p-6 text-center">
                  <div className="text-3xl font-medium text-primary mb-1">{recipe.nutrition.fat}g</div>
                  <div className="text-sm text-muted-foreground">Fat</div>
                </div>
              </div>
            )}

            {activeRecipeTab === 'tips' && recipe.aiTips && recipe.aiTips.length > 0 && (
              <div className="space-y-3">
                {recipe.aiTips.map((tip, index) => (
                  <div key={index} className="flex items-start gap-4 py-2">
                    <div className="w-7 h-7 rounded-full bg-primary text-primary-foreground flex items-center justify-center flex-shrink-0 text-sm font-medium">
                      {index + 1}
                    </div>
                    <p className="flex-1 leading-relaxed pt-0.5">{tip}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
        </div>
      </div>
    );
  };

  const renderPlayMode = (recipeId: string, currentStep: number) => {
    const originalRecipe = getRecipe(recipeId);
    if (!originalRecipe) return null;

    const recipe = getAdjustedRecipe(originalRecipe);
    const isAdjusted = adjustedServings[recipeId] && adjustedServings[recipeId] !== originalRecipe.servings;

    const totalSteps = recipe.instructions.length;
    const progress = ((currentStep + 1) / totalSteps) * 100;

    const nextStep = () => {
      if (currentStep < totalSteps - 1) {
        setScreen({ type: 'play-mode', recipeId, currentStep: currentStep + 1 });
      }
    };

    const prevStep = () => {
      if (currentStep > 0) {
        setScreen({ type: 'play-mode', recipeId, currentStep: currentStep - 1 });
      }
    };

    // Generate a smart timer label from the step text
    const generateTimerLabel = (stepText: string, duration: number): string => {
      const text = stepText.toLowerCase();
      
      // Common cooking actions and their contexts
      const actions: { [key: string]: string[] } = {
        'bake': ['baking', 'oven'],
        'cook': ['cooking', 'heat'],
        'simmer': ['simmering'],
        'boil': ['boiling'],
        'rest': ['resting', 'sit'],
        'chill': ['chilling', 'refrigerate', 'fridge', 'cool'],
        'freeze': ['freezing', 'freezer'],
        'marinate': ['marinating'],
        'proof': ['proofing', 'rise', 'rising'],
        'soak': ['soaking'],
        'steep': ['steeping'],
        'roast': ['roasting'],
        'grill': ['grilling'],
        'fry': ['frying'],
        'saute': ['sauteing', 'sauté'],
        'brown': ['browning'],
        'caramelize': ['caramelizing'],
        'reduce': ['reducing'],
        'thicken': ['thickening']
      };

      // Find the action in the step text
      let action = '';
      for (const [key, variations] of Object.entries(actions)) {
        if (variations.some(v => text.includes(v)) || text.includes(key)) {
          action = key.charAt(0).toUpperCase() + key.slice(1);
          break;
        }
      }

      // Common food items to extract
      const foodItems = [
        'dough', 'sauce', 'mixture', 'vegetables', 'meat', 'chicken', 'beef', 'pork',
        'fish', 'pasta', 'rice', 'pizza', 'bread', 'cake', 'cookies', 'pie',
        'soup', 'stew', 'broth', 'stock', 'potatoes', 'onions', 'garlic'
      ];

      let foodItem = '';
      for (const item of foodItems) {
        if (text.includes(item)) {
          foodItem = item.charAt(0).toUpperCase() + item.slice(1);
          break;
        }
      }

      // Build the label
      if (action && foodItem) {
        return `${action} ${foodItem.toLowerCase()}`;
      } else if (action) {
        return action;
      } else if (foodItem) {
        return foodItem;
      } else {
        // Fallback: use duration as label
        const minutes = Math.floor(duration / 60);
        return `${minutes} min`;
      }
    };

    const addTimer = (duration: number) => {
      const stepText = recipe.instructions[currentStep];
      const label = generateTimerLabel(stepText, duration);
      setTimers([...timers, { id: Date.now().toString(), label, duration }]);
    };

    const removeTimer = (id: string) => {
      setTimers(timers.filter(t => t.id !== id));
    };

    return (
      <div className="min-h-screen bg-card flex flex-col">
        {/* Progress Bar */}
        <div className="h-1.5 bg-secondary">
          <div 
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Header with Navigation */}
        <div className="border-b border-border">
          {/* Recipe Title Row */}
          <div className="px-4 md:px-6 pt-3 pb-2">
            <h2 className="text-base md:text-lg text-center truncate">{recipe.title}</h2>
            {isAdjusted && (
              <p className="text-muted-foreground text-xs md:text-sm text-center">
                {recipe.servings} servings
              </p>
            )}
          </div>

          {/* Navigation Row */}
          <div className="flex items-center justify-between px-4 md:px-6 pb-3">
            {/* Previous Button */}
            <button
              onClick={prevStep}
              disabled={currentStep === 0}
              className="h-12 px-4 md:px-6 bg-secondary text-secondary-foreground rounded-lg hover:bg-muted transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-2 text-sm md:text-base"
              aria-label="Previous step"
            >
              <ChevronLeft className="w-5 h-5" />
              <span className="hidden sm:inline">Prev</span>
            </button>

            {/* Step Counter */}
            <div className="text-center">
              <div className="text-lg md:text-xl font-medium">
                Step {currentStep + 1} <span className="text-muted-foreground">of</span> {totalSteps}
              </div>
            </div>

            {/* Next/Finish Button */}
            {currentStep === totalSteps - 1 ? (
              <button
                onClick={() => {
                  toast.success('Recipe completed! Enjoy your meal! 🎉');
                  setScreen({ type: 'recipe-detail', recipeId });
                }}
                className="h-12 px-4 md:px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm md:text-base flex items-center gap-2"
              >
                <span className="hidden sm:inline">Finish</span>
                <span className="sm:hidden">Done</span>
              </button>
            ) : (
              <button
                onClick={nextStep}
                className="h-12 px-4 md:px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2 text-sm md:text-base"
                aria-label="Next step"
              >
                <span className="hidden sm:inline">Next</span>
                <ChevronRight className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Exit Button - Centered Below */}
          <div className="px-4 md:px-6 pb-3">
            <button
              onClick={() => setScreen({ type: 'recipe-detail', recipeId })}
              className="w-full h-10 flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground transition-colors text-sm md:text-base"
            >
              <X className="w-4 h-4" />
              Exit Cook Mode
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-4xl mx-auto">
            {/* Current Step */}
            <div className="bg-background rounded-2xl p-6 md:p-12 mb-6 md:mb-8 shadow-sm">
              <div className="text-4xl md:text-6xl font-medium text-primary mb-4 md:mb-8 text-center">
                {currentStep + 1}
              </div>
              <p className="text-lg md:text-2xl leading-relaxed text-center">
                {recipe.instructions[currentStep]}
              </p>
            </div>

            {/* Quick Timer Actions */}
            <div className="flex items-center justify-center gap-2 md:gap-4 mb-6 md:mb-8">
              <button
                onClick={() => addTimer(300)}
                className="h-12 px-4 md:px-6 bg-secondary rounded-lg hover:bg-muted transition-colors text-sm md:text-base"
              >
                <span className="hidden md:inline">+ 5 min timer</span>
                <span className="md:hidden">5 min</span>
              </button>
              <button
                onClick={() => addTimer(600)}
                className="h-12 px-4 md:px-6 bg-secondary rounded-lg hover:bg-muted transition-colors text-sm md:text-base"
              >
                <span className="hidden md:inline">+ 10 min timer</span>
                <span className="md:hidden">10 min</span>
              </button>
              <button
                onClick={() => addTimer(900)}
                className="h-12 px-4 md:px-6 bg-secondary rounded-lg hover:bg-muted transition-colors text-sm md:text-base"
              >
                <span className="hidden md:inline">+ 15 min timer</span>
                <span className="md:hidden">15 min</span>
              </button>
            </div>

            {/* Timers */}
            {timers.length > 0 && (
              <div className="space-y-3 mb-6 md:mb-8">
                {timers.map(timer => (
                  <TimerWidget
                    key={timer.id}
                    id={timer.id}
                    label={timer.label}
                    duration={timer.duration}
                    onComplete={() => {
                      toast.success(`Timer complete: ${timer.label}`);
                    }}
                    onDelete={() => removeTimer(timer.id)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderFavorites = () => {
    const profileFavorites = currentProfile ? (favorites[currentProfile.id] || []) : [];
    const favoriteRecipes = MOCK_RECIPES.filter(r => profileFavorites.includes(r.id));

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <h2 className="mb-6">Favorite Recipes</h2>

          {favoriteRecipes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              {favoriteRecipes.map(recipe => (
                <RecipeCard
                  key={recipe.id}
                  id={recipe.id}
                  title={recipe.title}
                  image={recipe.image}
                  cookTime={recipe.cookTime}
                  rating={recipe.rating}
                  isFavorite={true}
                  onToggleFavorite={toggleFavorite}
                  onClick={() => viewRecipe(recipe.id, { fromScreen: { type: 'favorites' } })}
                  onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Heart className="w-10 h-10" />}
              title="No favorites yet"
              description="Heart recipes you love to see them here. Your favorited recipes will be saved to your profile."
              action={
                <button
                  onClick={() => setScreen({ type: 'home' })}
                  className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Browse Recipes
                </button>
              }
            />
          )}
        </div>
      </div>
    );
  };

  const renderAllRecipes = () => {
    const profileRecent = currentProfile ? (recentRecipes[currentProfile.id] || []) : [];
    const recentRecipesWithData = profileRecent
      .map(entry => {
        const recipe = getRecipe(entry.id);
        return recipe ? { ...recipe, viewedAt: entry.timestamp } : null;
      })
      .filter(Boolean) as (Recipe & { viewedAt: number })[];

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <h2 className="mb-6">All Recipes</h2>

          {recentRecipesWithData.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              {recentRecipesWithData.map(recipe => (
                <RecipeCard
                  key={recipe.id}
                  id={recipe.id}
                  title={recipe.title}
                  image={recipe.image}
                  cookTime={recipe.cookTime}
                  rating={recipe.rating}
                  isFavorite={isFavorite(recipe.id)}
                  onToggleFavorite={toggleFavorite}
                  onClick={() => viewRecipe(recipe.id, { fromScreen: { type: 'all-recipes' } })}
                  onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                  dateAdded={recipe.viewedAt}
                />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<BookOpen className="w-10 h-10" />}
              title="No recipes viewed yet"
              description="Start browsing and viewing recipes to see them here. All recipes you view will be saved automatically."
              action={
                <button
                  onClick={() => setScreen({ type: 'home' })}
                  className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Browse Recipes
                </button>
              }
            />
          )}
        </div>
      </div>
    );
  };

  const renderLists = () => {
    const profileLists = currentProfile ? (lists[currentProfile.id] || []) : [];

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h2>Recipe Collections</h2>
            <button
              onClick={() => setShowCreateList(true)}
              className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center justify-center gap-2 text-sm md:text-base"
            >
              <Plus className="w-5 h-5" />
              New Collection
            </button>
          </div>

          {showCreateList && (
            <div className="bg-card rounded-xl p-4 md:p-6 mb-6 border-2 border-primary">
              <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3 md:gap-4">
                <input
                  type="text"
                  value={newListName}
                  onChange={(e) => setNewListName(e.target.value)}
                  placeholder="Collection name (e.g., Weeknight Dinners)"
                  className="flex-1 h-12 px-4 bg-secondary rounded-lg outline-none focus:ring-2 focus:ring-primary"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newListName.trim()) {
                      createList(newListName.trim());
                      setNewListName('');
                      setShowCreateList(false);
                    }
                  }}
                />
                <button
                  onClick={() => {
                    if (newListName.trim()) {
                      createList(newListName.trim());
                      setNewListName('');
                      setShowCreateList(false);
                    }
                  }}
                  className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateList(false);
                    setNewListName('');
                  }}
                  className="h-12 px-6 bg-secondary rounded-lg hover:bg-muted transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {profileLists.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              {profileLists.map(list => {
                const listRecipes = MOCK_RECIPES.filter(r => list.recipeIds.includes(r.id));
                const coverImage = listRecipes[0]?.image || 'https://images.unsplash.com/photo-1495521821757-a1efb6729352?w=800&h=600&fit=crop';

                return (
                  <div
                    key={list.id}
                    onClick={() => setScreen({ type: 'list-detail', listId: list.id })}
                    className="bg-card rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer group"
                  >
                    <div className="relative aspect-[4/3] overflow-hidden">
                      <img 
                        src={coverImage} 
                        alt={list.name}
                        className="w-full h-full object-cover transition-transform group-hover:scale-105"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                      <div className="absolute bottom-4 left-4 right-4">
                        <h3 className="text-white mb-1">{list.name}</h3>
                        <p className="text-white/80 text-sm">{list.recipeIds.length} recipe{list.recipeIds.length !== 1 ? 's' : ''}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <EmptyState
              icon={<BookOpen className="w-10 h-10" />}
              title="No collections yet"
              description="Create collections to organize your recipes. Try making lists like 'Weeknight Dinners', 'Holiday Baking', or 'Meal Prep'."
            />
          )}
        </div>
      </div>
    );
  };

  const renderListDetail = (listId: string) => {
    const profileLists = currentProfile ? (lists[currentProfile.id] || []) : [];
    const list = profileLists.find(l => l.id === listId);
    
    if (!list) return null;

    const listRecipes = MOCK_RECIPES.filter(r => list.recipeIds.includes(r.id));

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="mb-1">{list.name}</h2>
              <p className="text-muted-foreground">{list.recipeIds.length} recipe{list.recipeIds.length !== 1 ? 's' : ''}</p>
            </div>
            <button
              onClick={() => {
                if (confirm('Delete this collection?')) {
                  deleteList(list.id);
                }
              }}
              className="h-12 px-6 bg-destructive text-destructive-foreground rounded-lg hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <Trash2 className="w-5 h-5" />
              Delete Collection
            </button>
          </div>

          {listRecipes.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
              {listRecipes.map(recipe => (
                <div key={recipe.id} className="relative">
                  <RecipeCard
                    id={recipe.id}
                    title={recipe.title}
                    image={recipe.image}
                    cookTime={recipe.cookTime}
                    rating={recipe.rating}
                    isFavorite={isFavorite(recipe.id)}
                    onToggleFavorite={toggleFavorite}
                    onClick={() => viewRecipe(recipe.id, { fromScreen: { type: 'list-detail', listId } })}
                    onPlay={(id) => setScreen({ type: 'play-mode', recipeId: id, currentStep: 0 })}
                  />
                  <button
                    onClick={() => removeRecipeFromList(recipe.id, list.id)}
                    className="absolute top-3 left-3 w-10 h-10 bg-destructive text-destructive-foreground rounded-full flex items-center justify-center shadow-sm hover:opacity-90 transition-opacity"
                    aria-label="Remove from list"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<BookOpen className="w-10 h-10" />}
              title="No recipes in this collection"
              description="Add recipes to this collection from any recipe detail page using the 'Add to List' button."
              action={
                <button
                  onClick={() => setScreen({ type: 'home' })}
                  className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                >
                  Browse Recipes
                </button>
              }
            />
          )}
        </div>
      </div>
    );
  };

  const renderSettings = () => {
    const handleEditPrompt = (key: string) => {
      setEditingPrompt(key);
      setTempPromptValue(aiPrompts[key as keyof typeof aiPrompts].prompt);
      setTempModelValue(aiPrompts[key as keyof typeof aiPrompts].model);
    };

    const handleSavePrompt = (key: string) => {
      if (!tempPromptValue.trim()) {
        toast.error('Prompt cannot be blank');
        return;
      }
      setAiPrompts(prev => ({
        ...prev,
        [key]: {
          prompt: tempPromptValue,
          model: tempModelValue
        }
      }));
      setEditingPrompt(null);
      toast.success('Prompt saved successfully');
    };

    const handleCancelEdit = () => {
      setEditingPrompt(null);
      setTempPromptValue('');
      setTempModelValue('');
    };

    const availableModels = [
      { value: 'anthropic/claude-3-haiku', label: 'Claude 3 Haiku' },
      { value: 'anthropic/claude-3-sonnet', label: 'Claude 3 Sonnet' },
      { value: 'anthropic/claude-3-opus', label: 'Claude 3 Opus' },
      { value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
      { value: 'openai/gpt-4o', label: 'GPT-4o' },
      { value: 'openai/gpt-4o-mini', label: 'GPT-4o Mini' },
      { value: 'openai/gpt-4-turbo', label: 'GPT-4 Turbo' },
      { value: 'google/gemini-pro-1.5', label: 'Gemini Pro 1.5' }
    ];

    const promptConfigs = [
      { key: 'recipeRemix', title: 'Recipe Remix', description: 'Used when creating recipe variations with AI' },
      { key: 'servingAdjustment', title: 'Serving Adjustment', description: 'Used when scaling recipe quantities' },
      { key: 'tipsGeneration', title: 'Tips Generation', description: 'Used to generate cooking tips for recipes' },
      { key: 'nutritionAnalysis', title: 'Nutrition Analysis', description: 'Used to calculate nutritional information' }
    ];

    return (
      <div className="p-4 md:p-8">
        <div className="max-w-4xl mx-auto">
          <h2 className="mb-6">Settings</h2>

          {/* Tab Navigation */}
          <div className="flex gap-2 mb-6 border-b border-border">
            <button
              onClick={() => setSettingsTab('general')}
              className={`px-4 md:px-6 py-3 font-medium transition-colors relative ${
                settingsTab === 'general'
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              General
              {settingsTab === 'general' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
            <button
              onClick={() => setSettingsTab('ai-prompts')}
              className={`px-4 md:px-6 py-3 font-medium transition-colors relative flex items-center gap-2 ${
                settingsTab === 'ai-prompts'
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Sparkles className="w-4 h-4" />
              AI Prompts
              {settingsTab === 'ai-prompts' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
            <button
              onClick={() => setSettingsTab('sources')}
              className={`px-4 md:px-6 py-3 font-medium transition-colors relative flex items-center gap-2 ${
                settingsTab === 'sources'
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Sources
              {settingsTab === 'sources' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
            <button
              onClick={() => setSettingsTab('source-selectors')}
              className={`px-4 md:px-6 py-3 font-medium transition-colors relative flex items-center gap-2 ${
                settingsTab === 'source-selectors'
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Code className="w-4 h-4" />
              Source Selectors
              {settingsTab === 'source-selectors' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          </div>

          {/* General Tab */}
          {settingsTab === 'general' && (
            <div className="space-y-4 md:space-y-6">
            {/* Theme */}
            <div className="bg-card rounded-xl p-4 md:p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="mb-1">Appearance</h3>
                  <p className="text-muted-foreground text-sm">Switch between light and dark mode</p>
                </div>
                <button
                  onClick={toggleDarkMode}
                  className="w-14 h-14 bg-secondary rounded-full flex items-center justify-center hover:bg-muted transition-colors"
                  aria-label="Toggle theme"
                >
                  {isDarkMode ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
                </button>
              </div>
            </div>

            {/* Profile Management */}
            <div className="bg-card rounded-xl p-4 md:p-6">
              <h3 className="mb-4">Profile Management</h3>
              <div className="space-y-3">
                {profiles.map(profile => (
                  <div key={profile.id} className="flex items-center justify-between py-3 border-b border-border last:border-0">
                    <div className="flex items-center gap-3">
                      <ProfileAvatar name={profile.name} color={profile.color} size="sm" />
                      <span>{profile.name}</span>
                      {currentProfile?.id === profile.id && (
                        <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded">Current</span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        if (confirm(`Delete profile "${profile.name}"?`)) {
                          deleteProfile(profile.id);
                        }
                      }}
                      className="text-destructive hover:underline text-sm"
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Data Management */}
            <div className="bg-card rounded-xl p-4 md:p-6">
              <h3 className="mb-4">Data Management</h3>
              <div className="space-y-3">
                <button
                  onClick={() => {
                    if (confirm('Clear all cached data? This will not affect your recipes or profiles.')) {
                      // Clear any cached data
                      localStorage.removeItem('cookie-cache');
                      toast.success('Cache cleared successfully');
                    }
                  }}
                  className="w-full h-12 px-6 bg-secondary text-foreground rounded-lg hover:bg-muted transition-colors text-left flex items-center justify-between"
                >
                  <span>Clear Cache</span>
                  <Trash2 className="w-5 h-5 text-muted-foreground" />
                </button>
                <button
                  onClick={() => {
                    if (confirm('Clear your viewing history? This cannot be undone.')) {
                      if (currentProfile) {
                        setRecentRecipes(prev => ({
                          ...prev,
                          [currentProfile.id]: []
                        }));
                        toast.success('View history cleared');
                      }
                    }
                  }}
                  className="w-full h-12 px-6 bg-secondary text-foreground rounded-lg hover:bg-muted transition-colors text-left flex items-center justify-between"
                >
                  <span>Clear View History</span>
                  <Trash2 className="w-5 h-5 text-muted-foreground" />
                </button>
              </div>
            </div>

            {/* OpenRouter API Key */}
            <div className="bg-card rounded-xl p-4 md:p-6">
              <h3 className="mb-4">OpenRouter API Key</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Enter your OpenRouter API key to enable AI features
              </p>
              <input
                type="password"
                value={openRouterApiKey}
                onChange={(e) => setOpenRouterApiKey(e.target.value)}
                placeholder="sk-or-v1-..."
                className="w-full h-12 px-4 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            {/* About */}
            <div className="bg-card rounded-xl p-4 md:p-6">
              <h3 className="mb-2">About Cookie</h3>
              <p className="text-muted-foreground text-sm mb-4">
                Version 1.0.0
              </p>
              <a 
                href="https://github.com/matthewdeaves/cookie.git"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline text-sm"
              >
                View on GitHub
              </a>
            </div>
          </div>
          )}

          {/* AI Prompts Tab */}
          {settingsTab === 'ai-prompts' && (
            <div className="space-y-4 md:space-y-6">
              <div className="bg-card rounded-xl p-4 md:p-6">
                <div className="mb-6">
                  <h3 className="mb-2">AI Integration Prompts</h3>
                  <p className="text-muted-foreground text-sm">
                    Customize the prompts and models used for each AI feature. All prompts are required and cannot be blank.
                  </p>
                </div>

                <div className="space-y-6">
                  {promptConfigs.map(({ key, title, description }) => {
                    const config = aiPrompts[key as keyof typeof aiPrompts];
                    const isEditing = editingPrompt === key;
                    const currentModel = availableModels.find(m => m.value === (isEditing ? tempModelValue : config.model));

                    return (
                      <div key={key} className="border border-border rounded-lg p-4 md:p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h4 className="font-medium mb-1">{title}</h4>
                            <p className="text-sm text-muted-foreground">{description}</p>
                          </div>
                          {!isEditing && (
                            <button
                              onClick={() => handleEditPrompt(key)}
                              className="h-10 px-4 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm"
                            >
                              Edit
                            </button>
                          )}
                        </div>

                        {isEditing ? (
                          <>
                            <div className="mb-4">
                              <label className="block text-sm font-medium mb-2">Prompt</label>
                              <textarea
                                value={tempPromptValue}
                                onChange={(e) => setTempPromptValue(e.target.value)}
                                rows={6}
                                className="w-full px-4 py-3 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
                              />
                            </div>

                            <div className="mb-4">
                              <label className="block text-sm font-medium mb-2">Model</label>
                              <select
                                value={tempModelValue}
                                onChange={(e) => setTempModelValue(e.target.value)}
                                className="w-full h-12 px-4 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                              >
                                {availableModels.map(model => (
                                  <option key={model.value} value={model.value}>
                                    {model.label}
                                  </option>
                                ))}
                              </select>
                            </div>

                            <div className="flex gap-3">
                              <button
                                onClick={() => handleSavePrompt(key)}
                                className="h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                              >
                                Save Changes
                              </button>
                              <button
                                onClick={handleCancelEdit}
                                className="h-12 px-6 bg-secondary text-foreground rounded-lg hover:bg-muted transition-colors"
                              >
                                Cancel
                              </button>
                            </div>
                          </>
                        ) : (
                          <>
                            <div className="mb-4">
                              <label className="block text-sm font-medium mb-2 text-muted-foreground">Prompt</label>
                              <div className="p-4 bg-secondary/50 rounded-lg border border-border">
                                <p className="text-sm font-mono whitespace-pre-wrap">{config.prompt}</p>
                              </div>
                            </div>
                            <div>
                              <label className="block text-sm font-medium mb-2 text-muted-foreground">Model</label>
                              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary/10 text-primary rounded-lg text-sm">
                                <Sparkles className="w-4 h-4" />
                                {currentModel?.label || config.model}
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Sources Tab */}
          {settingsTab === 'sources' && (
            <div className="space-y-4 md:space-y-6">
              <div className="bg-card rounded-xl p-4 md:p-6">
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="mb-2">Recipe Sources</h3>
                      <p className="text-muted-foreground text-sm">
                        Enable or disable recipe sources for search results. Disabled sources will not appear in search.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          const allEnabled: Record<string, boolean> = {};
                          RECIPE_SOURCES.forEach(source => {
                            allEnabled[source.name] = true;
                          });
                          setEnabledSources(allEnabled);
                          toast.success('All sources enabled');
                        }}
                        className="h-10 px-4 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm"
                      >
                        Enable All
                      </button>
                      <button
                        onClick={() => {
                          const allDisabled: Record<string, boolean> = {};
                          RECIPE_SOURCES.forEach(source => {
                            allDisabled[source.name] = false;
                          });
                          setEnabledSources(allDisabled);
                          toast.success('All sources disabled');
                        }}
                        className="h-10 px-4 bg-secondary text-foreground rounded-lg hover:bg-muted transition-colors text-sm"
                      >
                        Disable All
                      </button>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {RECIPE_SOURCES.map((source) => {
                    const isEnabled = enabledSources[source.name] ?? true;
                    return (
                      <div
                        key={source.name}
                        className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                          isEnabled
                            ? 'border-border bg-secondary/50'
                            : 'border-border/50 bg-secondary/20 opacity-60'
                        }`}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-1">
                            <h4 className="font-medium">{source.name}</h4>
                            {isEnabled && (
                              <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                                Active
                              </span>
                            )}
                          </div>
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
                          >
                            {source.url}
                            <LinkIcon className="w-3 h-3" />
                          </a>
                        </div>
                        <button
                          onClick={() => {
                            setEnabledSources(prev => ({
                              ...prev,
                              [source.name]: !isEnabled
                            }));
                            toast.success(`${source.name} ${isEnabled ? 'disabled' : 'enabled'}`);
                          }}
                          className={`relative w-16 h-8 rounded-full transition-colors ${
                            isEnabled ? 'bg-primary' : 'bg-secondary'
                          }`}
                          aria-label={`Toggle ${source.name}`}
                        >
                          <span
                            className={`absolute top-1 left-1 w-6 h-6 bg-card rounded-full transition-transform ${
                              isEnabled ? 'translate-x-8' : 'translate-x-0'
                            }`}
                          />
                        </button>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-6 p-4 bg-secondary/50 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">
                    <strong className="text-foreground">
                      {Object.values(enabledSources).filter(Boolean).length} of {RECIPE_SOURCES.length}
                    </strong>{' '}
                    sources currently enabled
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Source Selectors Tab */}
          {settingsTab === 'source-selectors' && (
            <div className="space-y-4 md:space-y-6">
              <div className="bg-card rounded-xl p-4 md:p-6">
                <div className="mb-6">
                  <h3 className="mb-2">Search Source Selector Management</h3>
                  <p className="text-muted-foreground text-sm">
                    Edit CSS selectors and test source connectivity
                  </p>
                </div>

                <div className="space-y-4">
                  {RECIPE_SOURCES.map((source) => {
                    const selectorData = sourceSelectors[source.name];
                    
                    const getStatusIcon = () => {
                      switch (selectorData.status) {
                        case 'working':
                          return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-500" />;
                        case 'broken':
                          return <XCircle className="w-5 h-5 text-red-600 dark:text-red-500" />;
                        default:
                          return <HelpCircle className="w-5 h-5 text-muted-foreground" />;
                      }
                    };

                    const formatLastTested = (timestamp: number | null) => {
                      if (!timestamp) return 'Never tested';
                      const date = new Date(timestamp);
                      const now = new Date();
                      const diffMs = now.getTime() - date.getTime();
                      const diffMins = Math.floor(diffMs / 60000);
                      const diffHours = Math.floor(diffMs / 3600000);
                      const diffDays = Math.floor(diffMs / 86400000);

                      if (diffMins < 1) return 'Just now';
                      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
                      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    };

                    const testSelector = (sourceName: string) => {
                      // Simulate testing
                      const isSuccess = Math.random() > 0.3; // 70% success rate
                      const newFailCount = isSuccess ? 0 : selectorData.failCount + 1;
                      
                      setSourceSelectors(prev => ({
                        ...prev,
                        [sourceName]: {
                          ...prev[sourceName],
                          status: isSuccess ? 'working' : 'broken',
                          lastTested: Date.now(),
                          failCount: newFailCount
                        }
                      }));

                      if (isSuccess) {
                        toast.success(`${sourceName} connection test passed`);
                      } else {
                        toast.error(`${sourceName} connection test failed`);
                      }

                      // Auto-disable if failed 3 times
                      if (newFailCount >= 3) {
                        setEnabledSources(prev => ({
                          ...prev,
                          [sourceName]: false
                        }));
                      }
                    };

                    return (
                      <div
                        key={source.name}
                        className="border border-border rounded-lg p-4"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium">{source.name}</h4>
                              {getStatusIcon()}
                            </div>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-muted-foreground hover:text-primary transition-colors flex items-center gap-1"
                            >
                              {new URL(source.url).hostname}
                              <LinkIcon className="w-3 h-3" />
                            </a>
                          </div>
                        </div>

                        <div className="space-y-3">
                          <div>
                            <label className="block text-sm font-medium mb-2">CSS Selector</label>
                            <input
                              type="text"
                              value={selectorData.cssSelector}
                              onChange={(e) => {
                                setSourceSelectors(prev => ({
                                  ...prev,
                                  [source.name]: {
                                    ...prev[source.name],
                                    cssSelector: e.target.value
                                  }
                                }));
                              }}
                              className="w-full h-10 px-3 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
                              placeholder=".recipe-content"
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="text-sm text-muted-foreground">
                              Last tested: {formatLastTested(selectorData.lastTested)}
                            </div>
                            <button
                              onClick={() => testSelector(source.name)}
                              className="h-10 px-4 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm"
                            >
                              Test
                            </button>
                          </div>

                          {selectorData.status === 'broken' && selectorData.failCount >= 3 && (
                            <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                              <XCircle className="w-4 h-4 text-red-600 dark:text-red-500 flex-shrink-0" />
                              <span className="text-sm text-red-600 dark:text-red-500 font-medium">
                                Failed {selectorData.failCount} times - auto-disabled
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="mt-6">
                  <button
                    onClick={() => {
                      RECIPE_SOURCES.forEach(source => {
                        setTimeout(() => {
                          const isSuccess = Math.random() > 0.3;
                          const currentData = sourceSelectors[source.name];
                          const newFailCount = isSuccess ? 0 : currentData.failCount + 1;
                          
                          setSourceSelectors(prev => ({
                            ...prev,
                            [source.name]: {
                              ...prev[source.name],
                              status: isSuccess ? 'working' : 'broken',
                              lastTested: Date.now(),
                              failCount: newFailCount
                            }
                          }));

                          // Auto-disable if failed 3 times
                          if (newFailCount >= 3) {
                            setEnabledSources(prev => ({
                              ...prev,
                              [source.name]: false
                            }));
                          }
                        }, Math.random() * 2000);
                      });
                      toast.success('Testing all sources...');
                    }}
                    className="w-full h-12 px-6 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity"
                  >
                    Test All Sources
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Navigation
  const getBreadcrumbs = () => {
    const items = [{ label: 'Home', onClick: () => setScreen({ type: 'home' }) }];

    if (screen.type === 'search') {
      items.push({ label: 'Search Results' });
    } else if (screen.type === 'recipe-detail') {
      const recipe = getRecipe(screen.recipeId);
      // If we came from search, add a clickable breadcrumb back to search
      if (screen.fromScreen?.type === 'search') {
        items.push({ 
          label: 'Search Results', 
          onClick: () => setScreen(screen.fromScreen!) 
        });
      }
      // If we came from favorites, add a clickable breadcrumb back to favorites
      if (screen.fromScreen?.type === 'favorites') {
        items.push({ 
          label: 'Favorites', 
          onClick: () => setScreen({ type: 'favorites' }) 
        });
      }
      // If we came from all recipes, add a clickable breadcrumb back to all recipes
      if (screen.fromScreen?.type === 'all-recipes') {
        items.push({ 
          label: 'All Recipes', 
          onClick: () => setScreen({ type: 'all-recipes' }) 
        });
      }
      // If we came from a collection, add clickable breadcrumbs back to collections
      if (screen.fromScreen?.type === 'list-detail') {
        const profileLists = currentProfile ? (lists[currentProfile.id] || []) : [];
        const list = profileLists.find(l => l.id === screen.fromScreen!.listId);
        items.push({ 
          label: 'Collections', 
          onClick: () => setScreen({ type: 'lists' }) 
        });
        if (list) {
          items.push({ 
            label: list.name, 
            onClick: () => setScreen(screen.fromScreen!) 
          });
        }
      }
      if (recipe) items.push({ label: recipe.title });
    } else if (screen.type === 'play-mode') {
      const recipe = getRecipe(screen.recipeId);
      if (recipe) {
        items.push({ 
          label: recipe.title, 
          onClick: () => setScreen({ type: 'recipe-detail', recipeId: screen.recipeId })
        });
        items.push({ label: 'Cooking' });
      }
    } else if (screen.type === 'favorites') {
      items.push({ label: 'Favorites' });
    } else if (screen.type === 'all-recipes') {
      items.push({ label: 'All Recipes' });
    } else if (screen.type === 'lists') {
      items.push({ label: 'Collections' });
    } else if (screen.type === 'list-detail') {
      const profileLists = currentProfile ? (lists[currentProfile.id] || []) : [];
      const list = profileLists.find(l => l.id === screen.listId);
      items.push({ label: 'Collections', onClick: () => setScreen({ type: 'lists' }) });
      if (list) items.push({ label: list.name });
    } else if (screen.type === 'settings') {
      items.push({ label: 'Settings' });
    }

    return items;
  };

  // Render
  if (screen.type === 'profile-selector') {
    return (
      <div className="min-h-screen overflow-x-hidden">
        {renderProfileSelector()}
        <Toaster position="bottom-center" />
      </div>
    );
  }

  if (screen.type === 'play-mode') {
    return (
      <div className="min-h-screen overflow-x-hidden">
        {renderPlayMode(screen.recipeId, screen.currentStep)}
        <Toaster position="bottom-center" />
      </div>
    );
  }

  return (
    <div className="min-h-screen overflow-x-hidden">
      <Header
        currentUser={currentProfile}
        onMenuClick={() => setMenuOpen(!menuOpen)}
        onProfileClick={() => setScreen({ type: 'profile-selector' })}
        showSearch={false}
        darkMode={isDarkMode}
        onDarkModeToggle={toggleDarkMode}
      />
      
      {screen.type !== 'home' && <BreadcrumbNav items={getBreadcrumbs()} />}

      {/* Side Menu */}
      {menuOpen && (
        <>
          <div 
            className="fixed inset-0 bg-black/50 z-40 transition-opacity"
            onClick={() => setMenuOpen(false)}
          />
          <div className="fixed left-0 top-0 bottom-0 w-72 md:w-80 bg-card border-r border-border z-50 p-4 md:p-6 transform transition-transform duration-300 ease-out animate-slide-in-left">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-primary">Cookie</h2>
              <button onClick={() => setMenuOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-6 h-6" />
              </button>
            </div>
            
            <nav className="space-y-2">
              <button
                onClick={() => {
                  setScreen({ type: 'home' });
                  setMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-secondary transition-colors text-left"
              >
                <HomeIcon className="w-5 h-5" />
                Home
              </button>
              <button
                onClick={() => {
                  setScreen({ type: 'favorites' });
                  setMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-secondary transition-colors text-left"
              >
                <Heart className="w-5 h-5" />
                Favorites
              </button>
              <button
                onClick={() => {
                  setScreen({ type: 'lists' });
                  setMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-secondary transition-colors text-left"
              >
                <BookOpen className="w-5 h-5" />
                Collections
              </button>
              <button
                onClick={() => {
                  setScreen({ type: 'settings' });
                  setMenuOpen(false);
                }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-secondary transition-colors text-left"
              >
                <SettingsIcon className="w-5 h-5" />
                Settings
              </button>
            </nav>
          </div>
        </>
      )}

      <main>
        {screen.type === 'home' && renderHome()}
        {screen.type === 'search' && renderSearch(screen.query)}
        {screen.type === 'recipe-detail' && renderRecipeDetail(screen.recipeId)}
        {screen.type === 'favorites' && renderFavorites()}
        {screen.type === 'all-recipes' && renderAllRecipes()}
        {screen.type === 'lists' && renderLists()}
        {screen.type === 'list-detail' && renderListDetail(screen.listId)}
        {screen.type === 'settings' && renderSettings()}
      </main>

      <Toaster position="bottom-center" />
      
      {/* AI Remix Modal */}
      {showAIRemixModal && remixingRecipeId && (
        <AIRemixModal
          recipeName={getRecipe(remixingRecipeId)?.title || ''}
          onClose={() => {
            setShowAIRemixModal(false);
            setRemixingRecipeId(null);
          }}
          onRemix={handleRemixRecipe}
        />
      )}
    </div>
  );
}
