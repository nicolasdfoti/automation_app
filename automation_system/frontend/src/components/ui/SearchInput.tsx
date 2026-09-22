import { Search, X } from "lucide-react";

interface SearchInputProps {
  id?: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}

export default function SearchInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  className,
}: SearchInputProps) {
  const inputId = id ?? "search";
  return (
    <div className={`relative ${className ?? ""}`}>
      <label htmlFor={inputId} className="sr-only">
        {label}
      </label>
      <Search
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        size={16}
        aria-hidden="true"
      />
      <input
        id={inputId}
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck={false}
        className="h-9 w-full rounded-md border border-slate-300 bg-white pl-9 pr-9 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 transition-colors duration-150 hover:border-slate-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
      />
      {value && (
        <button
          type="button"
          onClick={() => onChange("")}
          aria-label="Limpiar búsqueda"
          className="absolute right-2 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
        >
          <X size={14} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}