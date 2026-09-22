import { NavLink } from "react-router-dom";
import { X } from "lucide-react";
import { BRAND, NAV_SECTIONS } from "../../lib/navigation";
import { useShell } from "./AppShell";

function SidebarContent() {
  return (
    <div className="flex h-full flex-col bg-slate-900">
      {/* Brand */}
      <div className="flex items-center gap-3 px-4 py-4">
        <div
          className="flex h-8 w-8 items-center justify-center rounded-md bg-primary-500 text-white"
          aria-hidden="true"
        >
          <BRAND.icon size={17} />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-white">{BRAND.name}</p>
          <p className="text-[11px] text-slate-400">{BRAND.caption}</p>
        </div>
      </div>

      {/* Navigation */}
      <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto px-3 py-2">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-5">
            <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-slate-500">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.items.map(({ to, label, icon: Icon, upcoming }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    end={to === "/"}
                    className={({ isActive }) =>
                      `group relative flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors duration-150 ease-out focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-white/70 ${
                        isActive
                          ? "bg-primary-600 font-medium text-white"
                          : "text-slate-300 hover:bg-slate-800 hover:text-white"
                      }`
                    }
                  >
                    <Icon size={17} className="shrink-0 opacity-80 transition-opacity group-hover:opacity-100" />
                    <span>{label}</span>
                    {upcoming && (
                      <span className="ml-auto rounded border border-slate-700 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wide text-slate-500">
                        Próximo
                      </span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* User / profile area */}
      <div className="border-t border-slate-800 px-4 py-4">
        <div className="flex items-center gap-3">
          <div
            className="flex h-8 w-8 items-center justify-center rounded-md bg-slate-800 text-xs font-semibold text-slate-300"
            aria-hidden="true"
          >
            OP
          </div>
          <div className="leading-tight">
            <p className="text-sm font-medium text-slate-200">Operaciones</p>
            <p className="text-[11px] text-slate-500">Sesión de demostración</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const { menuOpen, setMenuOpen } = useShell();

  return (
    <>
      {/* Mobile drawer backdrop */}
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/50 lg:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-60 transform bg-slate-900 transition-transform duration-300 ease-out lg:hidden ${
          menuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
        aria-label="Navegación"
        aria-hidden={!menuOpen}
      >
        <button
          type="button"
          onClick={() => setMenuOpen(false)}
          aria-label="Cerrar menú"
          className="absolute right-3 top-4 flex h-7 w-7 items-center justify-center rounded-md text-slate-400 transition-colors hover:bg-slate-800 hover:text-white lg:hidden"
        >
          <X size={16} aria-hidden="true" />
        </button>
        <SidebarContent />
      </aside>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-60 lg:block" aria-label="Navegación">
        <SidebarContent />
      </aside>
    </>
  );
}