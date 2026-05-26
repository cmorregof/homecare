export function AlertRow({ message }: { message: string }) {
  return <div className="rounded-md border border-danger/30 bg-white p-4 text-sm text-danger">{message}</div>;
}
