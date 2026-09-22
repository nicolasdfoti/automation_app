import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyDetailPage from "./pages/PropertyDetailPage";
import EsquematicosPage from "./pages/EsquematicosPage";
import NotImplementedPage from "./pages/NotImplementedPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/propiedades" element={<PropertiesPage />} />
        <Route path="/propiedades/:codigo" element={<PropertyDetailPage />} />
        <Route path="/esquematicos" element={<EsquematicosPage />} />
        <Route path="/ocr" element={<NotImplementedPage title="OCR" />} />
        <Route path="/comparar" element={<NotImplementedPage title="Comparar" />} />
        <Route path="/automatizar" element={<NotImplementedPage title="Automatizar" />} />
        <Route path="*" element={<NotImplementedPage title="No encontrado" />} />
      </Route>
    </Routes>
  );
}