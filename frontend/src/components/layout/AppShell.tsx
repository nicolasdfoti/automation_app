import { createContext, useContext, useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

interface ShellContextValue {
  menuOpen: boolean;
  setMenuOpen: (open: boolean) => void;
}

const ShellContext = createContext<ShellContextValue>({
  menuOpen: false,
  setMenuOpen: () => undefined,
});

export function useShell(): ShellContextValue {
  return useContext(ShellContext);
}

export default function AppShell() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  // Close the mobile drawer with Escape and lock body scroll while open.
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [menuOpen]);

  return (
    <ShellContext.Provider value={{ menuOpen, setMenuOpen }}>
      <div className="min-h-screen bg-slate-50">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-slate-900 focus:shadow-md"
        >
          Saltar al contenido
        </a>
        <Sidebar />
        <div className="lg:pl-60">
          <Header />
          <main id="main-content" className="px-4 py-6 sm:px-6 lg:px-8">
            <div key={pathname} className="page-enter mx-auto w-full max-w-7xl">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </ShellContext.Provider>
  );
}