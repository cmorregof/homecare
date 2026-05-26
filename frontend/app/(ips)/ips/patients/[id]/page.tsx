export default function IpsPatientDetailPage({ params }: { params: { id: string } }) {
  return <main className="p-8">Detalle clínico del paciente {params.id}</main>;
}
