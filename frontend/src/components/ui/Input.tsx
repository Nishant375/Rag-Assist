import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export function Input({ label, id, className = "", ...rest }: InputProps) {
  return (
    <div className="mb-3.5">
      {label && (
        <label htmlFor={id} className="mb-1.5 block text-[13px] font-medium text-gray-300">
          {label}
        </label>
      )}
      <input id={id} className={`input ${className}`} {...rest} />
    </div>
  );
}
