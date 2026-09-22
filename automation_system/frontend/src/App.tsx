import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import EsquematicosPage from "./pages/EsquematicosPage";
import OcrPage from "./pages/OcrPage";
import ComparePage from "./pages/ComparePage";
import AutomationPage from "./pages/AutomationPage";
import NotImplementedPage from "./pages/NotImplementedPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/esquematicos" replace />} />
        <Route path="/esquematicos" element={<EsquematicosPage />} />
        <Route path="/ocr" element={<OcrPage />} />
        <Route path="/comparar" element={<ComparePage />} />
        <Route path="/automatizar" element={<AutomationPage />} />
        <Route path="*" element={<NotImplementedPage title="No encontrado" />} />
      </Route>
    </Routes>
  );
}