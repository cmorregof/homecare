/**
 * Compact form in which a document number is stored in `profiles.document_id`.
 *
 * Mirrors normalize_document_id in backend/db/repository.py:441, and must keep
 * mirroring it. Patients type their document with thousands separators
 * ("1.002.652.750") while the bot looks accounts up by the stored form. When
 * the two disagree the lookup misses, the bot offers to register an account
 * that already exists, and Supabase Auth rejects the duplicate — which is
 * exactly the production failure fixed in #12. The web forms were writing the
 * raw text, so they could still seed a row in the shape that caused it.
 *
 * '1.002.652.750' becomes '1002652750'; 'CC 1.002.652.750' becomes
 * 'cc1002652750'.
 *
 * Unicode-aware on purpose: Python's str.isalnum() keeps accented letters, and
 * a plain /[^a-z0-9]/ here would strip characters the backend preserves, so the
 * two would disagree on any non-ASCII document.
 */
export function normalizeDocumentId(documentId: string | null | undefined): string {
  const compact = String(documentId ?? "")
    .trim()
    .toLowerCase()
    .split("")
    .filter((character) => /[\p{L}\p{N}]/u.test(character))
    .join("");
  if (compact.startsWith("cc") && compact.length > 2 && /^\p{Nd}+$/u.test(compact.slice(2))) {
    return `cc${compact.slice(2)}`;
  }
  return compact;
}

/**
 * The value to store, keeping the original when normalising empties it.
 *
 * Mirrors `normalize_document_id(document_id) or document_id`
 * (backend/db/repository.py:226): a document made only of punctuation would
 * otherwise be silently dropped, which is worse than storing it oddly.
 */
export function storableDocumentId(documentId: string | null | undefined): string | null {
  const raw = String(documentId ?? "").trim();
  if (!raw) {
    return null;
  }
  return normalizeDocumentId(raw) || raw;
}
