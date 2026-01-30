import { FC } from 'react';
import { Heart, Clock, Play } from 'lucide-react';

interface RecipeCardProps {
  id: string;
  title: string;
  image: string;
  cookTime: number;
  rating?: number;
  isFavorite: boolean;
  onToggleFavorite: (id: string) => void;
  onClick: () => void;
  onPlay: (id: string) => void;
  dateAdded?: number;
}

const formatDate = (timestamp: number): string => {
  const date = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  // Reset time for comparison
  const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const yesterdayOnly = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate());

  if (dateOnly.getTime() === todayOnly.getTime()) {
    return 'Today';
  } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
    return 'Yesterday';
  } else {
    // Format as "Jan 6, 2026"
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
};

export const RecipeCard: FC<RecipeCardProps> = ({
  id,
  title,
  image,
  cookTime,
  rating,
  isFavorite,
  onToggleFavorite,
  onClick,
  onPlay,
  dateAdded
}) => {
  return (
    <div className="group bg-card rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all">
      <div className="relative aspect-[4/3] overflow-hidden cursor-pointer" onClick={onClick}>
        <img
          src={image}
          alt={title}
          className="w-full h-full object-cover transition-transform group-hover:scale-105"
        />
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleFavorite(id);
          }}
          className="absolute top-3 right-3 w-12 h-12 bg-white/90 dark:bg-card/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm transition-colors hover:bg-white dark:hover:bg-card"
          aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
        >
          <Heart
            className={`w-6 h-6 transition-colors ${
              isFavorite ? 'fill-accent text-accent' : 'text-muted-foreground'
            }`}
          />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPlay(id);
          }}
          className="absolute bottom-3 right-3 w-12 h-12 bg-primary/90 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm transition-all hover:bg-primary hover:scale-110"
          aria-label="Play recipe"
        >
          <Play
            className="w-6 h-6 text-primary-foreground fill-primary-foreground"
          />
        </button>
      </div>
      <div className="p-4 cursor-pointer" onClick={onClick}>
        <h3 className="line-clamp-2 mb-2 min-h-[3em]">{title}</h3>
        <div className="flex items-center gap-3 text-muted-foreground text-sm">
          <div className="flex items-center gap-1.5">
            <Clock className="w-5 h-5" />
            <span>{cookTime} min</span>
          </div>
          {rating && (
            <div className="flex items-center gap-1.5">
              <span className="text-star">★</span>
              <span>{rating.toFixed(1)}</span>
            </div>
          )}
          {dateAdded && (
            <div className="flex items-center gap-1.5">
              <span>•</span>
              <span>{formatDate(dateAdded)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
