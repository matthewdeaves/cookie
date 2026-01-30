import { FC, useState, useEffect } from 'react';
import { X, Sparkles, RotateCcw } from 'lucide-react';

interface AIRemixModalProps {
  recipeName: string;
  onClose: () => void;
  onRemix: (prompt: string, newName: string) => void;
}

const SUGGESTED_PROMPTS = [
  [
    'Make it spicy with jalapeños',
    'Add pepperoni and mushrooms',
    'Make it vegetarian',
    'Add extra cheese',
    'Make it gluten-free',
    'Add a Mediterranean twist'
  ],
  [
    'Make it healthier with less oil',
    'Add garlic and herbs',
    'Make it kid-friendly',
    'Add a smoky flavor',
    'Make it vegan',
    'Add roasted vegetables'
  ],
  [
    'Reduce cooking time',
    'Make it more filling',
    'Add protein',
    'Make it dairy-free',
    'Add caramelized onions',
    'Make it low-carb'
  ],
  [
    'Add truffle oil',
    'Make it Thai-inspired',
    'Add sun-dried tomatoes',
    'Make it BBQ-style',
    'Add fresh herbs',
    'Make it Indian-spiced'
  ]
];

export const AIRemixModal: FC<AIRemixModalProps> = ({ recipeName, onClose, onRemix }) => {
  const [prompt, setPrompt] = useState('');
  const [newRecipeName, setNewRecipeName] = useState('');
  const [currentSuggestionSet, setCurrentSuggestionSet] = useState(0);
  const [isRemixing, setIsRemixing] = useState(false);

  const currentSuggestions = SUGGESTED_PROMPTS[currentSuggestionSet];

  // Generate AI-suggested name when prompt changes
  useEffect(() => {
    if (prompt.trim()) {
      // Generate a name based on the original recipe and the prompt
      const generateName = () => {
        const modifications: { [key: string]: string } = {
          'spicy': 'Spicy',
          'jalapeño': 'Spicy',
          'pepperoni': 'Pepperoni',
          'mushroom': 'Mushroom',
          'vegetarian': 'Vegetarian',
          'vegan': 'Vegan',
          'gluten-free': 'Gluten-Free',
          'Mediterranean': 'Mediterranean',
          'healthier': 'Healthy',
          'kid-friendly': 'Kid-Friendly',
          'smoky': 'Smoky',
          'protein': 'Protein-Packed',
          'dairy-free': 'Dairy-Free',
          'low-carb': 'Low-Carb',
          'truffle': 'Truffle',
          'Thai': 'Thai-Style',
          'BBQ': 'BBQ',
          'Indian': 'Indian-Spiced',
        };

        // Try to find a matching keyword
        let modifier = '';
        for (const [keyword, label] of Object.entries(modifications)) {
          if (prompt.toLowerCase().includes(keyword.toLowerCase())) {
            modifier = label;
            break;
          }
        }

        if (modifier) {
          return `${modifier} ${recipeName}`;
        } else {
          return `${recipeName} Remix`;
        }
      };

      setNewRecipeName(generateName());
    } else {
      setNewRecipeName('');
    }
  }, [prompt, recipeName]);

  const handleRefreshSuggestions = () => {
    setCurrentSuggestionSet((prev) => (prev + 1) % SUGGESTED_PROMPTS.length);
  };

  const handleSelectPrompt = (selectedPrompt: string) => {
    setPrompt(selectedPrompt);
  };

  const handleRemix = () => {
    if (!prompt.trim() || !newRecipeName.trim()) return;
    setIsRemixing(true);
    // Simulate AI processing time
    setTimeout(() => {
      onRemix(prompt, newRecipeName);
      setIsRemixing(false);
    }, 1000);
  };

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4 md:p-6">
      <div className="bg-card rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 md:p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg md:text-xl">AI Recipe Remix</h2>
              <p className="text-xs md:text-sm text-muted-foreground">Create a new version of {recipeName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-secondary transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 md:space-y-6">
          {/* Recipe Name Input */}
          <div>
            <label className="block text-sm font-medium mb-2">
              New recipe name (optional)
            </label>
            <input
              type="text"
              value={newRecipeName}
              onChange={(e) => setNewRecipeName(e.target.value)}
              placeholder="Leave blank - AI will choose a name based on your changes"
              className="w-full px-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm md:text-base"
              disabled={isRemixing}
            />
          </div>

          {/* Prompt Input */}
          <div>
            <label className="block text-sm font-medium mb-2">
              How would you like to remix this recipe?
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g., Make it spicy with jalapeños and add extra cheese"
              className="w-full h-32 px-4 py-3 bg-background border border-border rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary text-sm md:text-base"
              disabled={isRemixing}
            />
          </div>

          {/* Suggested Prompts */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-medium">
                Suggested variations
              </label>
              <button
                onClick={handleRefreshSuggestions}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-secondary transition-colors text-sm text-muted-foreground hover:text-foreground"
                disabled={isRemixing}
              >
                <RotateCcw className="w-4 h-4" />
                <span className="hidden md:inline">More ideas</span>
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {currentSuggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectPrompt(suggestion)}
                  className={`px-4 py-3 rounded-lg text-left text-sm transition-colors ${
                    prompt === suggestion
                      ? 'bg-primary/10 text-primary border-2 border-primary'
                      : 'bg-secondary hover:bg-muted border-2 border-transparent'
                  }`}
                  disabled={isRemixing}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 md:p-6 border-t border-border">
          <button
            onClick={onClose}
            className="h-12 px-4 md:px-6 rounded-lg bg-secondary text-secondary-foreground hover:bg-muted transition-colors text-sm md:text-base"
            disabled={isRemixing}
          >
            Cancel
          </button>
          <button
            onClick={handleRemix}
            disabled={!prompt.trim() || !newRecipeName.trim() || isRemixing}
            className="h-12 px-4 md:px-6 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm md:text-base"
          >
            {isRemixing ? (
              <>
                <div className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                <span className="hidden md:inline">Creating remix...</span>
                <span className="md:hidden">Creating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                <span className="hidden md:inline">Create Remix</span>
                <span className="md:hidden">Remix</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
