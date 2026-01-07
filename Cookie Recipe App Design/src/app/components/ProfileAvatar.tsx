import { FC } from 'react';

interface ProfileAvatarProps {
  name: string;
  color: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  onClick?: () => void;
}

export const ProfileAvatar: FC<ProfileAvatarProps> = ({ name, color, size = 'md', onClick }) => {
  const sizeClasses = {
    sm: 'w-10 h-10 text-base',
    md: 'w-14 h-14 text-xl',
    lg: 'w-24 h-24 text-4xl',
    xl: 'w-32 h-32 text-5xl'
  };

  const initial = name.charAt(0).toUpperCase();

  return (
    <button
      onClick={onClick}
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center font-medium text-white shadow-sm transition-transform hover:scale-105 active:scale-95`}
      style={{ backgroundColor: color }}
      type="button"
    >
      {initial}
    </button>
  );
};
