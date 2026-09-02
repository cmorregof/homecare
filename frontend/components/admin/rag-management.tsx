"use client";

import { ChangeEvent, useState } from "react";
import { Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { Table, TableWrap, Td, Th, Tr } from "@/components/ui/table";
import { Card, CardTitle } from "@/components/vitals/vital-card";
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
      <Card>
        <CardTitle>Subir documento</CardTitle>
        <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed border-border px-4 text-center text-base text-muted transition-colors hover:border-brand hover:bg-brand-soft focus-within:ring-2 focus-within:ring-brand focus-within:ring-offset-2">
          <Upload className="mb-2 h-5 w-5" aria-hidden />
          PDF, DOCX o TXT
          <input type="file" accept=".pdf,.doc,.docx,.txt" className="sr-only" onChange={handleFile} />
        </label>
        {fileName ? <p className="mt-3 text-base font-semibold text-brand">{fileName}</p> : null}
        <Button type="button" full className="mt-4">Indexar</Button>
      </Card>

      <TableWrap>
        {documents.length === 0 ? (
          <EmptyState>No hay documentos indexados.</EmptyState>
        ) : (
          <div className="min-w-[680px]">
            <Table>
              <thead>
                <tr>
                  <Th>Documento</Th>
                  <Th>Fuente</Th>
                  <Th>Chunks</Th>
                  <Th>Fecha</Th>
                </tr>
              </thead>
              <tbody>
                {documents.map((document) => (
                  <Tr key={document.id}>
                    <Td className="font-semibold text-ink">{document.title}</Td>
                    <Td className="text-muted">{document.source}</Td>
                    <Td>{document.chunk_count}</Td>
                    <Td className="text-muted">{document.created_at}</Td>
                  </Tr>
                ))}
              </tbody>
            </Table>
          </div>
        )}
      </TableWrap>
    </div>
  );
}
