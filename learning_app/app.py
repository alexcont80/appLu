"""Tk desktop UI for local document-field learning and review."""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .extractors import ExtractedDocument, read_document
from .learning_store import append_round, default_data_dir


DOC_TYPES: dict[str, list[str]] = {
    "Lettera di incarico": ["Nome docente", "Cognome docente", "Email", "Oggetto / titolo corso", "Compenso / tariffa", "Tipologia compenso", "Data corso", "Orario", "Numero protocollo", "Data protocollo"],
    "Programma Edizione": ["Titolo corso", "Data", "Orario intervento", "Docente associato", "Durata intervento"],
    "Curriculum Vitae": ["Nome docente", "Cognome docente", "Titoli di studio", "Laurea triennale", "Laurea magistrale", "Professione dichiarata"],
    "Accettazione incarico": ["Docente interno / esterno", "In orario / fuori orario di servizio", "Compenso orario / forfait / gratuito", "Rimborso spese richiesto"],
    "Dichiarazione docente esterno": ["Regime retributivo dichiarato", "Coordinate bancarie", "Dati identificativi"],
    "Dichiarazione conflitto d’interessi": ["Dati identificativi", "Dichiarazioni", "Firma presente"],
    "Altro / da classificare": [],
}

STATUSES = ("Da valutare", "Presente e chiaro", "Presente ma ambiguo", "Non trovato", "Illeggibile", "Non previsto")


class LearningApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AppLu · Apprendimento documenti")
        self.geometry("1280x820")
        self.minsize(1000, 680)
        self.documents: list[dict] = []
        self.current = -1
        self.field_rows: list[dict[str, tk.Widget]] = []
        self.selected_field_index = tk.IntVar(value=0)
        self.data_dir = default_data_dir()
        self._style()
        self._layout()
        self._bind_keys()
        self._render_documents()

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista" if self.tk.call("tk", "windowingsystem") == "win32" else "clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground="#12304a")
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#53677a")
        style.configure("Card.TLabelframe", padding=10)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=25)

    def _layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        header = ttk.Frame(self, padding=(18, 14, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="AppLu · Banco di apprendimento locale", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Etichetta i documenti, verifica i campi e registra ciò che le regole dovranno imparare.", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        banner = tk.Label(self, text="ELABORAZIONE LOCALE · nessun documento viene caricato online · l’estrazione mostra occorrenze letterali e non decide il significato", bg="#eaf3f8", fg="#184460", padx=12, pady=9, anchor="w", font=("Segoe UI", 9))
        banner.grid(row=1, column=0, sticky="ew", padx=18, pady=(2, 10))

        body = ttk.Panedwindow(self, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))
        left = ttk.Frame(body, padding=(0, 0, 8, 0), width=280)
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=4)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        actions = ttk.Frame(left)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="Aggiungi documenti…", command=self.add_files).pack(fill="x", pady=2)
        ttk.Button(actions, text="Rimuovi selezionato", command=self.remove_document).pack(fill="x", pady=2)
        self.doc_list = tk.Listbox(left, exportselection=False, activestyle="dotbox", font=("Segoe UI", 9), relief="solid", borderwidth=1)
        self.doc_list.grid(row=1, column=0, sticky="nsew")
        self.doc_list.bind("<<ListboxSelect>>", self.on_select)
        ttk.Label(left, text="Formati: PDF testuale, DOCX, TXT, MD, CSV", wraplength=260, style="Sub.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))

        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=3)
        right.rowconfigure(2, weight=2)
        meta = ttk.LabelFrame(right, text="Classificazione del documento", style="Card.TLabelframe")
        meta.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        meta.columnconfigure(1, weight=1)
        ttk.Label(meta, text="Tipo documento").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.type_var = tk.StringVar(value="Altro / da classificare")
        self.type_box = ttk.Combobox(meta, textvariable=self.type_var, values=list(DOC_TYPES), state="readonly", width=35)
        self.type_box.grid(row=0, column=1, sticky="ew", pady=4)
        self.type_box.bind("<<ComboboxSelected>>", self.on_type_change)
        ttk.Label(meta, text="Nota libera").grid(row=1, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.note_text = tk.Text(meta, height=2, wrap="word", font=("Segoe UI", 9))
        self.note_text.grid(row=1, column=1, sticky="ew", pady=4)

        review = ttk.Panedwindow(right, orient="horizontal")
        review.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        fields_frame = ttk.LabelFrame(review, text="Campi attesi · verifica umana", style="Card.TLabelframe")
        candidates_frame = ttk.LabelFrame(review, text="Occorrenze riconosciute · non interpretate", style="Card.TLabelframe")
        review.add(fields_frame, weight=3)
        review.add(candidates_frame, weight=2)
        fields_frame.columnconfigure(0, weight=1)
        fields_frame.rowconfigure(1, weight=1)
        field_toolbar = ttk.Frame(fields_frame)
        field_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ttk.Button(field_toolbar, text="Aggiungi campo atteso", command=self.add_field).pack(side="left")
        self.fields_canvas = tk.Canvas(fields_frame, highlightthickness=0)
        self.fields_scroll = ttk.Scrollbar(fields_frame, orient="vertical", command=self.fields_canvas.yview)
        self.fields_canvas.configure(yscrollcommand=self.fields_scroll.set)
        self.fields_canvas.grid(row=1, column=0, sticky="nsew")
        self.fields_scroll.grid(row=1, column=1, sticky="ns")
        self.fields_inner = ttk.Frame(self.fields_canvas)
        self.fields_window = self.fields_canvas.create_window((0, 0), window=self.fields_inner, anchor="nw")
        self.fields_inner.bind("<Configure>", lambda _e: self.fields_canvas.configure(scrollregion=self.fields_canvas.bbox("all")))
        self.fields_canvas.bind("<Configure>", lambda e: self.fields_canvas.itemconfigure(self.fields_window, width=e.width))
        self.fields_inner.columnconfigure(0, weight=1)

        candidates_frame.columnconfigure(0, weight=1)
        candidates_frame.rowconfigure(0, weight=1)
        self.candidates_tree = ttk.Treeview(candidates_frame, columns=("kind", "value", "where"), show="headings", selectmode="browse")
        for col, title, width in (("kind", "Tipo", 85), ("value", "Testo trovato", 170), ("where", "Fonte", 80)):
            self.candidates_tree.heading(col, text=title)
            self.candidates_tree.column(col, width=width, stretch=col == "value")
        self.candidates_tree.grid(row=0, column=0, sticky="nsew")
        cand_scroll = ttk.Scrollbar(candidates_frame, orient="vertical", command=self.candidates_tree.yview)
        cand_scroll.grid(row=0, column=1, sticky="ns")
        self.candidates_tree.configure(yscrollcommand=cand_scroll.set)
        ttk.Button(candidates_frame, text="Collega al campo selezionato →", command=self.attach_candidate).grid(row=1, column=0, sticky="ew", pady=(6, 0))

        source_box = ttk.LabelFrame(right, text="Testo di origine · consultazione locale", style="Card.TLabelframe")
        source_box.grid(row=2, column=0, sticky="nsew")
        source_box.columnconfigure(0, weight=1)
        source_box.rowconfigure(0, weight=1)
        self.source_text = tk.Text(source_box, wrap="word", font=("Consolas", 9), state="disabled", height=8)
        self.source_text.grid(row=0, column=0, sticky="nsew")
        source_scroll = ttk.Scrollbar(source_box, orient="vertical", command=self.source_text.yview)
        source_scroll.grid(row=0, column=1, sticky="ns")
        self.source_text.configure(yscrollcommand=source_scroll.set)

        footer = ttk.Frame(self, padding=(18, 0, 18, 14))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        self.save_values_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(footer, text="Log dettagliato: salva valori, contesti e mappature (disattiva per ometterli)", variable=self.save_values_var).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Apri cartella log", command=self.open_log_folder).grid(row=0, column=1, padx=5)
        ttk.Button(footer, text="Esporta log JSON…", command=self.export_log).grid(row=0, column=2, padx=5)
        ttk.Button(footer, text="Salva round di apprendimento", command=self.save_round).grid(row=0, column=3)
        self.status_var = tk.StringVar(value=f"Log locale: {self.data_dir / 'learning-log.jsonl'}")
        ttk.Label(footer, textvariable=self.status_var, style="Sub.TLabel").grid(row=1, column=0, columnspan=4, sticky="w", pady=(7, 0))

    def _bind_keys(self) -> None:
        self.doc_list.bind("<Delete>", lambda _e: self.remove_document())

    def add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Seleziona documenti da analizzare", filetypes=[("Documenti supportati", "*.pdf *.docx *.txt *.md *.csv"), ("Tutti i file", "*.*")])
        for name in files:
            if any(item["path"] == name for item in self.documents):
                continue
            try:
                parsed = read_document(name)
                doc = {"path": name, "name": Path(name).name, "parsed": parsed, "type": "Altro / da classificare", "note": "", "fields": self._make_fields(DOC_TYPES["Altro / da classificare"])}
            except Exception as exc:
                messagebox.showerror("Lettura documento", f"Non riesco a leggere {Path(name).name}:\n{exc}")
                continue
            self.documents.append(doc)
        self._render_documents()
        if self.documents and self.current < 0:
            self._select_document(0)

    @staticmethod
    def _make_fields(names: list[str]) -> list[dict[str, str]]:
        return [{"name": name, "status": "Da valutare", "value": "", "note": ""} for name in names]

    def _render_documents(self) -> None:
        self.doc_list.delete(0, "end")
        for item in self.documents:
            parsed: ExtractedDocument = item["parsed"]
            suffix = f" · {len(parsed.candidates)} occorrenze" if parsed.candidates else " · nessuna occorrenza"
            self.doc_list.insert("end", item["name"] + suffix)
        if self.current >= len(self.documents):
            self.current = -1

    def on_select(self, _event: object = None) -> None:
        selection = self.doc_list.curselection()
        if selection:
            self._select_document(selection[0])

    def _select_document(self, index: int) -> None:
        self._save_current_form()
        self.current = index
        self.doc_list.selection_clear(0, "end")
        self.doc_list.selection_set(index)
        self.doc_list.activate(index)
        doc = self.documents[index]
        self.type_var.set(doc["type"])
        self.note_text.delete("1.0", "end")
        self.note_text.insert("1.0", doc["note"])
        self._draw_fields()
        self._draw_candidates(doc["parsed"])
        parsed: ExtractedDocument = doc["parsed"]
        contents = parsed.text or "[Nessun testo selezionabile trovato nel documento.]"
        self.source_text.configure(state="normal")
        self.source_text.delete("1.0", "end")
        self.source_text.insert("1.0", contents[:1000000])
        self.source_text.configure(state="disabled")
        if parsed.warning:
            self.status_var.set(parsed.warning)
        else:
            self.status_var.set(f"{len(parsed.candidates)} occorrenze letterali candidate · fonte: {Path(doc['path']).name}")

    def _save_current_form(self) -> None:
        if self.current < 0 or self.current >= len(self.documents):
            return
        doc = self.documents[self.current]
        doc["type"] = self.type_var.get()
        doc["note"] = self.note_text.get("1.0", "end-1c").strip()
        for row in self.field_rows:
            field = row["field"]
            field["name"] = row["name"].get().strip()
            field["status"] = row["status"].get()
            field["value"] = row["value"].get().strip()
            field["note"] = row["note"].get().strip()

    def on_type_change(self, _event: object = None) -> None:
        if self.current < 0:
            return
        self._save_current_form()
        doc = self.documents[self.current]
        doc["type"] = self.type_var.get()
        if not doc["fields"]:
            doc["fields"] = self._make_fields(DOC_TYPES.get(doc["type"], []))
        self._draw_fields()

    def _draw_fields(self) -> None:
        for child in self.fields_inner.winfo_children():
            child.destroy()
        self.field_rows = []
        if self.current < 0:
            return
        doc = self.documents[self.current]
        header = ttk.Frame(self.fields_inner)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for col, label in enumerate(("Link", "Campo atteso", "Stato", "Valore/conferma manuale", "Motivo o domanda")):
            ttk.Label(header, text=label, font=("Segoe UI", 8, "bold")).grid(row=0, column=col, sticky="w", padx=(0, 5))
        for index, field in enumerate(doc["fields"], start=1):
            row = ttk.Frame(self.fields_inner)
            row.grid(row=index, column=0, sticky="ew", pady=2)
            row.columnconfigure(1, weight=2)
            row.columnconfigure(3, weight=2)
            row.columnconfigure(4, weight=2)
            ttk.Radiobutton(row, variable=self.selected_field_index, value=index - 1).grid(row=0, column=0, sticky="w", padx=(0, 5))
            name = ttk.Entry(row, width=22)
            name.insert(0, field["name"])
            name.grid(row=0, column=1, sticky="ew", padx=(0, 5))
            status = ttk.Combobox(row, values=STATUSES, state="readonly", width=20)
            status.set(field["status"])
            status.grid(row=0, column=2, sticky="ew", padx=(0, 5))
            value = ttk.Entry(row)
            value.insert(0, field["value"])
            value.grid(row=0, column=3, sticky="ew", padx=(0, 5))
            note = ttk.Entry(row)
            note.insert(0, field["note"])
            note.grid(row=0, column=4, sticky="ew")
            self.field_rows.append({"field": field, "name": name, "status": status, "value": value, "note": note})

    def add_field(self) -> None:
        if self.current < 0:
            messagebox.showinfo("Seleziona un documento", "Aggiungi e seleziona prima un documento.")
            return
        self._save_current_form()
        self.documents[self.current]["fields"].append({"name": "Nuovo campo", "status": "Da valutare", "value": "", "note": ""})
        self.selected_field_index.set(len(self.documents[self.current]["fields"]) - 1)
        self._draw_fields()

    def _draw_candidates(self, parsed: ExtractedDocument) -> None:
        self.candidates_tree.delete(*self.candidates_tree.get_children())
        for index, candidate in enumerate(parsed.candidates):
            self.candidates_tree.insert("", "end", iid=str(index), values=(candidate.kind, candidate.value[:120], candidate.location), tags=(candidate.context,))
        self.candidates_tree.tag_configure("context")
        self.candidates_tree.bind("<<TreeviewSelect>>", self._show_candidate_context)

    def _show_candidate_context(self, _event: object = None) -> None:
        selection = self.candidates_tree.selection()
        if not selection or self.current < 0:
            return
        index = int(selection[0])
        candidate = self.documents[self.current]["parsed"].candidates[index]
        self.status_var.set(f"{candidate.kind} · {candidate.location}: {candidate.context}")

    def attach_candidate(self) -> None:
        if self.current < 0:
            return
        selected = self.candidates_tree.selection()
        if not selected or not self.field_rows:
            messagebox.showinfo("Selezione necessaria", "Seleziona una occorrenza e il campo da collegare.")
            return
        self._save_current_form()
        selected_index = max(0, min(self.selected_field_index.get(), len(self.field_rows) - 1))
        row = self.field_rows[selected_index]
        candidate = self.documents[self.current]["parsed"].candidates[int(selected[0])]
        self._save_current_form()
        row["value"].delete(0, "end")
        row["value"].insert(0, candidate.value)
        row["status"].set("Presente ma ambiguo")
        row["note"].delete(0, "end")
        row["note"].insert(0, f"Da verificare · {candidate.location}")
        row["field"]["evidence"] = candidate.to_dict()

    def remove_document(self) -> None:
        selection = self.doc_list.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx == self.current:
            self._save_current_form()
        self.documents.pop(idx)
        self.current = -1
        self._render_documents()
        self._clear_review()
        if self.documents:
            self._select_document(min(idx, len(self.documents) - 1))

    def _clear_review(self) -> None:
        self.type_var.set("Altro / da classificare")
        self.note_text.delete("1.0", "end")
        self._draw_fields()
        self._draw_candidates(ExtractedDocument("", 0, "", ()))
        self.source_text.configure(state="normal")
        self.source_text.delete("1.0", "end")
        self.source_text.configure(state="disabled")

    def _serialize_document(self, doc: dict, include_values: bool) -> dict:
        parsed: ExtractedDocument = doc["parsed"]
        fields = []
        for field in doc["fields"]:
            item = {"expected_field": field["name"], "status": field["status"], "source_document": Path(doc["path"]).name if field["status"] in {"Presente e chiaro", "Presente ma ambiguo"} else None, "note": field["note"]}
            if include_values:
                item["reviewed_value"] = field["value"]
                item["evidence"] = field.get("evidence")
            fields.append(item)
        result = {"document_name": doc["name"], "document_type": doc["type"], "file_extension": Path(doc["path"]).suffix.lower(), "page_count": parsed.pages, "text_extracted": bool(parsed.text.strip()), "candidate_counts_by_type": {}, "expected_fields": fields, "review_note": doc["note"], "warnings": [parsed.warning] if parsed.warning else []}
        for candidate in parsed.candidates:
            result["candidate_counts_by_type"][candidate.kind] = result["candidate_counts_by_type"].get(candidate.kind, 0) + 1
        # Candidate values, page/section provenance, and surrounding excerpts
        # make the log useful for constructing exact extraction rules later.
        if include_values:
            result["candidates"] = [candidate.to_dict() for candidate in parsed.candidates]
        return result

    def save_round(self) -> None:
        if not self.documents:
            messagebox.showinfo("Round vuoto", "Aggiungi almeno un documento prima di salvare il round.")
            return
        self._save_current_form()
        docs = [self._serialize_document(doc, self.save_values_var.get()) for doc in self.documents]
        try:
            log_path = append_round(docs, include_values=self.save_values_var.get())
        except OSError as exc:
            messagebox.showerror("Salvataggio log", str(exc))
            return
        self.status_var.set(f"Round registrato · {log_path}")
        messagebox.showinfo("Round salvato", f"Il round di apprendimento è stato aggiunto al log locale:\n\n{log_path}\n\nIl log contiene gli elementi testuali riconosciuti, i contesti e le mappature revisionate. Il testo integrale e i file originali non vengono copiati.")

    def open_log_folder(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        try:
            import os, subprocess, sys
            if sys.platform == "win32":
                os.startfile(self.data_dir)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.data_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.data_dir)])
        except Exception as exc:
            messagebox.showerror("Cartella log", str(exc))

    def export_log(self) -> None:
        source = self.data_dir / "learning-log.jsonl"
        if not source.exists():
            messagebox.showinfo("Nessun log", "Non è ancora stato salvato alcun round.")
            return
        target = filedialog.asksaveasfilename(title="Esporta log", defaultextension=".json", filetypes=[("JSON", "*.json")], initialfile="appLu-learning-log.json")
        if not target:
            return
        try:
            rounds = []
            with source.open(encoding="utf-8") as stream:
                rounds = [json.loads(line) for line in stream if line.strip()]
            Path(target).write_text(json.dumps(rounds, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Esportazione completata", f"Log esportato in:\n{target}")
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Esportazione", str(exc))


def main() -> None:
    LearningApp().mainloop()


if __name__ == "__main__":
    main()

