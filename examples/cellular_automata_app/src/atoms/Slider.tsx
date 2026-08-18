import React from 'react';

interface SliderProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Slider: React.FC<SliderProps> = (props) => {
  return (
    <input
      type="range"
      {...props}
      className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
    />
  );
};
