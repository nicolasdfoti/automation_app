import { Link } from "react-router-dom";
import { Construction } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import EmptyState from "../components/ui/EmptyState";

export default function NotImplementedPage({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} subtitle="Módulo del pipeline OCR y automatización." />
      <EmptyState
        icon={Construction}
        title="Aún no está implementada"
        description="Esta sección forma parte del pipeline OCR, que se incorporará en próximos pasos del proyecto. Podés seguir usando Dashboard y Propiedades."
        action={
          <Link
            to="/"
            className="inline-flex h-9 items-center rounded-md bg-primary-500 px-4 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary-600"
          >
            Volver al dashboard
          </Link>
        }
      />
    </>
  );
}