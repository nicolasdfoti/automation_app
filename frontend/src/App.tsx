import { NavLink, Outlet, Route, Routes } from "react-router-dom";
import { Boxes, Building2, Files, ScanLine, GitCompareArrows, Workflow } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyDetailPage from "./pages/PropertyDetailPage";
import NotImplementedPage from "./pages/NotImplementedPage";

const NAV = [
  { to: "/", label: "Dashboard", icon: Boxes },
  { to: "/propiedades", label: "Propiedades", icon: Building2 },
  { to: "/esquematicos", label: "Esquemáticos", icon: Files },
  { to: "/ocr", label: "OCR", icon: ScanLine },
  { to: "/comparar", label: "Comparar", icon: GitCompareArrows },
  { to: "/automatizar", label: "Automatizar", icon: Workflow },
];

function Layout() {
  return (
    <div className="flex min-h-screen">
      <nav className="w-56 shrink-0 border-r border-slate-200 bg-slate-100 p-4">
        <div className="mb-6 px-2 text-sm font-semibold text-slate-800">Automation Suite</div>
        <ul className="space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-md px-2 py-1.5 text-sm ${
                    isActive ? "bg-blue-600 font-medium text-white" : "text-slate-700 hover:bg-slate-200"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/propiedades" element={<PropertiesPage />} />
        <Route path="/propiedades/:codigo" element={<PropertyDetailPage />} />
        <Route path="/esquematicos" element={<NotImplementedPage title="Esquemáticos" />} />
        <Route path="/ocr" element={<NotImplementedPage title="OCR" />} />
        <Route path="/comparar" element={<NotImplementedPage title="Comparar" />} />
        <Route path="/automatizar" element={<NotImplementedPage title="Automatizar" />} />
        <Route path="*" element={<NotImplementedPage title="No encontrado" />} />
      </Route>
    </Routes>
  );
}