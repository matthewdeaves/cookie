import { FC } from 'react';
import { Menu, Search, Sun, Moon } from 'lucide-react';
import { ProfileAvatar } from './ProfileAvatar';

interface HeaderProps {
  currentUser: { name: string; color: string } | null;
  onMenuClick: () => void;
  onProfileClick: () => void;
  showSearch?: boolean;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  onSearchSubmit?: () => void;
  darkMode?: boolean;
  onDarkModeToggle?: () => void;
}

export const Header: FC<HeaderProps> = ({
  currentUser,
  onMenuClick,
  onProfileClick,
  showSearch,
  searchValue,
  onSearchChange,
  onSearchSubmit,
  darkMode,
  onDarkModeToggle
}) => {
  return (
    <header className="bg-card border-b border-border px-4 md:px-6 py-3 md:py-4 flex items-center justify-between gap-3 md:gap-6">
      <div className="flex items-center gap-2 md:gap-4">
        <button
          onClick={onMenuClick}
          className="w-12 h-12 flex items-center justify-center rounded-lg hover:bg-secondary transition-colors"
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h1 className="text-primary">Cookie</h1>
      </div>

      {showSearch && (
        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search recipes or paste a URL..."
              value={searchValue}
              onChange={(e) => onSearchChange?.(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onSearchSubmit?.();
                }
              }}
              className="w-full h-12 pl-11 md:pl-12 pr-3 md:pr-4 bg-secondary rounded-lg outline-none focus:ring-2 focus:ring-primary transition-shadow text-sm md:text-base"
            />
          </div>
        </div>
      )}

      <div className="flex items-center gap-2 md:gap-4">
        {onDarkModeToggle && (
          <button
            onClick={onDarkModeToggle}
            className="w-12 h-12 flex items-center justify-center rounded-lg hover:bg-secondary transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        )}
        {currentUser && (
          <ProfileAvatar
            name={currentUser.name}
            color={currentUser.color}
            size="sm"
            onClick={onProfileClick}
          />
        )}
      </div>
    </header>
  );
};
