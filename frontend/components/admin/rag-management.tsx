"use client";

import { ChangeEvent, useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { RagDocument } from "@/types";

export function RagManagement({ initialDocuments }: { initialDocuments: RagDocument[] }) {
  const [documents, setDocuments] = useState(initialDocuments);
  const [fileName, setFileName] = useState("");

  function handleFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setFileName(file.name);
    setDocuments((current) => [
      {
        id: `draft-${Date.now()}`,
        title: file.name.replace(/\.[^.]+$/, ""),
        source: "Carga pendiente",
        chunk_count: 0,
        created_at: new Date().toISOString(),
      },
      ...current,
    ]);
  }

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_1fr]">
      <section className="rounded-md border border-slate-200 bg-white p-5">
        <h2 className="font-semibold">Subir documento</h2>
        <label className="mt-4 flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-slate-300 px-4 text-center text-sm text-slate-600">
          <Upload className="mb-2 h-5 w-5" aria-hidden />
          PDF, DOCX o TXT
          <input type="file" accept=".pdf,.doc,.docx,.txt" className="sr-only" onChange={handleFile} />
        </label>
        {fileName ? <p className="mt-3 text-sm font-medium text-clinical">{fileName}</p> : null}
        <Button type="button" className="mt-4 w-full">Indexar</Button>
      </section>

      <section className="overflow-hidden rounded-md border border-slate-200 bg-white">
        <table className="w-full min-w-[680px] text-left text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 font-semibold">Documento</th>
              <th className="px-4 py-3 font-semibold">Fuente</th>
              <th className="px-4 py-3 font-semibold">Chunks</th>
              <th className="px-4 py-3 font-semibold">Fecha</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {documents.map((document) => (
              <tr key={document.id}>
                <td className="px-4 py-3 font-medium text-ink">{document.title}</td>
                <td className="px-4 py-3 text-slate-600">{document.source}</td>
                <td className="px-4 py-3">{document.chunk_count}</td>
                <td className="px-4 py-3">{document.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
