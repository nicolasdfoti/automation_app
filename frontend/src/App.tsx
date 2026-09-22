import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import PropertiesPage from "./pages/PropertiesPage";
import PropertyDetailPage from "./pages/PropertyDetailPage";
import EsquematicosPage from "./pages/EsquematicosPage";
import OcrPage from "./pages/OcrPage";
import ComparePage from "./pages/ComparePage";
import AutomationPage from "./pages/AutomationPage";
import NotImplementedPage from "./pages/NotImplementedPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/propiedades" element={<PropertiesPage />} />
        <Route path="/propiedades/:codigo" element={<PropertyDetailPage />} />
        <Route path="/esquematicos" element={<EsquematicosPage />} />
        <Route path="/ocr" element={<OcrPage />} />
        <Route path="/comparar" element={<ComparePage />} />
        <Route path="/automatizar" element={<AutomationPage />} />
        <Route path="*" element={<NotImplementedPage title="No encontrado" />} />
      </Route>
    </Routes>
  );
}