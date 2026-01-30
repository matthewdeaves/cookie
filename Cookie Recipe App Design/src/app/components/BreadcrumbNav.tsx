import { FC } from 'react';
import { ChevronRight } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  onClick?: () => void;
}

interface BreadcrumbNavProps {
  items: BreadcrumbItem[];
}

export const BreadcrumbNav: FC<BreadcrumbNavProps> = ({ items }) => {
  return (
    <nav className="flex items-center gap-2 px-4 md:px-6 py-3 border-b border-border bg-card overflow-x-auto">
      {items.map((item, index) => (
        <div key={index} className="flex items-center gap-2">
          {index > 0 && <ChevronRight className="w-4 h-4 text-muted-foreground flex-shrink-0" />}
          {item.onClick ? (
            <button
              onClick={item.onClick}
              className="text-sm leading-none text-muted-foreground hover:text-foreground transition-colors whitespace-nowrap"
            >
              {item.label}
            </button>
          ) : (
            <span className="text-sm leading-none text-foreground whitespace-nowrap">
              {item.label}
            </span>
          )}
        </div>
      ))}
    </nav>
  );
};
