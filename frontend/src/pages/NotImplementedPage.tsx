import { Link } from "react-router-dom";
import { Construction } from "lucide-react";

export default function NotImplementedPage({ title }: { title: string }) {
  return (
    <section>
      <h1 className="mb-6 text-2xl font-semibold text-slate-900">{title}</h1>
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center">
        <Construction className="mx-auto mb-3 text-slate-400" size={28} />
        <p className="font-medium text-slate-800">Esta sección aún no está implementada</p>
        <p className="mt-1 text-sm text-slate-500">
          En próximos pasos se incorporará la funcionalidad correspondiente del pipeline OCR.
        </p>
        <Link to="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Volver al dashboard
        </Link>
      </div>
    </section>
  );
}