declare module 'react-hot-toast' {
  const toast: {
    (message: string): void;
    success(message: string): void;
    error(message: string): void;
  };
  
  function Toaster(props: { position: string }): JSX.Element;
  
  export { toast, Toaster };
}

declare module '@heroicons/react/24/outline' {
  import { FC, SVGProps } from 'react';
  
  export const PlusIcon: FC<SVGProps<SVGSVGElement>>;
  export const TrashIcon: FC<SVGProps<SVGSVGElement>>;
  export const PlayIcon: FC<SVGProps<SVGSVGElement>>;
  export const PauseIcon: FC<SVGProps<SVGSVGElement>>;
} 