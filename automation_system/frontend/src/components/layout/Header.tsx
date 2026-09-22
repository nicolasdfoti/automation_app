import { Link, useLocation } from "react-router-dom";
import { Menu } from "lucide-react";
import { breadcrumbsFor } from "../../lib/navigation";
import { useShell } from "./AppShell";

export default function Header() {
  const { setMenuOpen } = useShell();
  const { pathname } = useLocation();
  const crumbs = breadcrumbsFor(pathname);

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-slate-200 bg-white px-4 sm:px-6 lg:px-8">
      <button
        type="button"
        onClick={() => setMenuOpen(true)}
        aria-label="Abrir menú de navegación"
        className="flex h-8 w-8 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900 lg:hidden"
      >
        <Menu size={18} aria-hidden="true" />
      </button>

      <nav aria-label="Ruta de navegación">
        <ol className="flex items-center gap-1.5 text-sm">
          {crumbs.map((crumb, index) => {
            const isLast = index === crumbs.length - 1;
            return (
              <li key={`${crumb.label}-${index}`} className="flex items-center gap-1.5">
                {index > 0 && (
                  <span className="text-slate-300" aria-hidden="true">
                    /
                  </span>
                )}
                {crumb.to && !isLast ? (
                  <Link
                    to={crumb.to}
                    className="text-slate-500 transition-colors duration-150 hover:text-slate-900"
                  >
                    {crumb.label}
                  </Link>
                ) : (
                  <span className={isLast ? "font-medium text-slate-900" : "text-slate-500"}>
                    {crumb.label}
                  </span>
                )}
              </li>
            );
          })}
        </ol>
      </nav>
    </header>
  );
}