"""Tk desktop UI for local document-field learning and review."""

from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .extractors import ExtractedDocument, read_document
from .learning_store import append_round, clear_session, default_data_dir, load_session, save_session
from .learning_session import summarize_guided_path, validate_document_type, validate_final_path


DOC_TYPES: dict[str, list[str]] = {
    "Lettera di incarico": ["Nome docente", "Cognome docente", "Email", "Oggetto / titolo corso", "Compenso / tariffa", "Tipologia compenso", "Data corso", "Orario", "Numero protocollo", "Data protocollo"],
    "Programma Edizione": ["Titolo corso", "Data", "Orario intervento", "Docente associato", "Durata intervento"],
    "Curriculum Vitae": ["Nome docente", "Cognome docente", "Titoli di studio", "Laurea triennale", "Laurea magistrale", "Professione dichiarata"],
    "Modello ordinativo interno": [],
    "Modello ordinativo esterno": [],
    "Piano Formativo Aziendale": ["Titolo corso", "Centro di costo", "Codice / riferimento del corso"],
    "Piano Formativo Regionale": ["Titolo corso", "Centro di costo", "Codice / riferimento del corso"],
    "Accettazione incarico": ["Docente interno / esterno", "In orario / fuori orario di servizio", "Compenso orario / forfait / gratuito", "Rimborso spese richiesto"],
    "Dichiarazione docente esterno": ["Regime retributivo dichiarato", "Coordinate bancarie", "Dati identificativi"],
    "Dichiarazione conflitto d’interessi": ["Dati identificativi", "Dichiarazioni", "Firma presente"],
    "Altro / da classificare": [],
}

GUIDED_STEPS = list(DOC_TYPES)
ISSUE_TYPES = ("Da tipizzare", "Significato del campo", "Posizione / etichetta", "Formato del dato", "Condizione / variante", "Associazione a docente o corso", "Differenza tra esemplari", "Altro")
STATUSES = ("Da verificare", "Presente e chiaro", "Presente ma ambiguo", "Non rilevato · da chiarire", "Assente in questa variante · confermato", "Illeggibile", "Non previsto · confermato")
UNDERSTOOD_STATUSES = {"Presente e chiaro", "Assente in questa variante · confermato", "Non previsto · confermato"}


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
        self.step_states = {name: "Da raccogliere" for name in GUIDED_STEPS}
        self.active_type = GUIDED_STEPS[0]
        self._session_save_job = None
        self.data_dir = default_data_dir()
        self._style()
        self._layout()
        self._bind_keys()
        self._render_documents()
        self._render_steps()
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self._restore_session()

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
        ttk.Label(header, text="AppLu · Percorso guidato di apprendimento", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Raccogli un esemplare per tipologia, confronta le varianti e chiudi con un log di mappature e domande.", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        banner = tk.Label(self, text="ELABORAZIONE LOCALE · nessun documento viene caricato online · l’estrazione mostra occorrenze letterali e non decide il significato", bg="#eaf3f8", fg="#184460", padx=12, pady=9, anchor="w", font=("Segoe UI", 9))
        banner.grid(row=1, column=0, sticky="ew", padx=18, pady=(2, 10))

        body = ttk.Panedwindow(self, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))
        left = ttk.Frame(body, padding=(0, 0, 8, 0), width=280)
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=1)
        body.add(right, weight=4)
        left.rowconfigure(4, weight=1)
        left.columnconfigure(0, weight=1)

        actions = ttk.Frame(left)
        actions.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(actions, text="Aggiungi un esemplare…", command=self.add_files).pack(fill="x", pady=2)
        ttk.Button(actions, text="Rimuovi selezionato", command=self.remove_document).pack(fill="x", pady=2)
        ttk.Label(left, text="PERCORSO PER TIPOLOGIA", font=("Segoe UI", 8, "bold")).grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.step_list = tk.Listbox(left, exportselection=False, height=9, activestyle="dotbox", font=("Segoe UI", 8), relief="solid", borderwidth=1)
        self.step_list.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.step_list.bind("<<ListboxSelect>>", self.on_step_select)
        ttk.Label(left, text="ESEMPLARI RACCOLTI", font=("Segoe UI", 8, "bold")).grid(row=3, column=0, sticky="w", pady=(0, 4))
        self.doc_list = tk.Listbox(left, exportselection=False, activestyle="dotbox", font=("Segoe UI", 9), relief="solid", borderwidth=1)
        self.doc_list.grid(row=4, column=0, sticky="nsew")
        self.doc_list.bind("<<ListboxSelect>>", self.on_select)
        ttk.Label(left, text="Formati: PDF testuale, DOCX, TXT, MD, CSV", wraplength=260, style="Sub.TLabel").grid(row=5, column=0, sticky="w", pady=(8, 0))

        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=3)
        right.rowconfigure(2, weight=2)
        meta = ttk.LabelFrame(right, text="Classificazione del documento", style="Card.TLabelframe")
        meta.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        meta.columnconfigure(1, weight=1)
        ttk.Label(meta, text="Tipo documento").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self.type_var = tk.StringVar(value=self.active_type)
        self.type_box = ttk.Combobox(meta, textvariable=self.type_var, values=list(DOC_TYPES), state="readonly", width=35)
        self.type_box.grid(row=0, column=1, sticky="ew", pady=4)
        self.type_box.bind("<<ComboboxSelected>>", self.on_type_change)
        ttk.Label(meta, text="Variante / caso rappresentato").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self.variant_var = tk.StringVar()
        self.variant_entry = ttk.Entry(meta, textvariable=self.variant_var)
        self.variant_entry.grid(row=1, column=1, sticky="ew", pady=4)
        self.variant_entry.bind("<KeyRelease>", self._schedule_session_save)
        ttk.Label(meta, text="Nota generale / osservazione").grid(row=2, column=0, sticky="nw", padx=(0, 8), pady=4)
        self.note_text = tk.Text(meta, height=2, wrap="word", font=("Segoe UI", 9))
        self.note_text.grid(row=2, column=1, sticky="ew", pady=4)
        self.note_text.bind("<KeyRelease>", self._schedule_session_save)

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
        ttk.Checkbutton(footer, text="Log dettagliato: salva valori, contesti e mappature (disattiva per ometterli)", variable=self.save_values_var).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 5))
        ttk.Button(footer, text="Apri cartella log", command=self.open_log_folder).grid(row=1, column=0, sticky="w", padx=(0, 5))
        ttk.Button(footer, text="Esporta log JSON…", command=self.export_log).grid(row=1, column=1, sticky="w", padx=5)
        ttk.Button(footer, text="Tipo compreso · prossimo →", command=self.complete_step).grid(row=1, column=2, sticky="w", padx=5)
        ttk.Button(footer, text="Genera log finale", command=self.save_round).grid(row=1, column=3, sticky="w", padx=5)
        ttk.Button(footer, text="Documento non disponibile", command=self.mark_step_unavailable).grid(row=1, column=4, sticky="w", padx=5)
        self.status_var = tk.StringVar(value=f"Log locale: {self.data_dir / 'learning-log.jsonl'}")
        ttk.Label(footer, textvariable=self.status_var, style="Sub.TLabel").grid(row=2, column=0, columnspan=5, sticky="w", pady=(7, 0))
        self.coverage_confirmed = tk.BooleanVar(value=False)
        ttk.Checkbutton(meta, text="Ho confrontato tutti gli esemplari e verificato che ogni variabile/campo sia mappato (aggiungi gli altri campi prima di continuare)", variable=self.coverage_confirmed).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 2))

    def _bind_keys(self) -> None:
        self.doc_list.bind("<Delete>", lambda _e: self.remove_document())

    def _restore_session(self) -> None:
        try:
            saved = load_session(data_dir=self.data_dir)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showwarning("Progressi non leggibili", f"Non riesco a riaprire la sessione salvata:\n{exc}")
            return
        if not saved:
            return
        for name, state in saved.get("step_states", {}).items():
            if name in self.step_states:
                self.step_states[name] = state
        active = saved.get("active_type")
        if active in GUIDED_STEPS:
            self.active_type = active
        for item in saved.get("documents", []):
            source = item.get("path", "")
            try:
                parsed = read_document(source)
            except Exception as exc:
                parsed = ExtractedDocument(source, 0, "", (), f"File non riletto: {exc}")
            self.documents.append({
                "path": source,
                "name": item.get("name", Path(source).name or "esemplare"),
                "parsed": parsed,
                "type": item.get("type", self.active_type),
                "variant": item.get("variant", ""),
                "note": item.get("note", ""),
                "fields": item.get("fields", []),
            })
        self._render_documents()
        self._render_steps()
        matching = [i for i, doc in enumerate(self.documents) if doc["type"] == self.active_type]
        if matching:
            self._select_document(matching[-1])
        else:
            self._clear_review()
        self.status_var.set("Progressi ripresi dal salvataggio locale. Verifica la tipologia selezionata e continua.")

    def _schedule_session_save(self, _event: object = None) -> None:
        if self._session_save_job is not None:
            try:
                self.after_cancel(self._session_save_job)
            except tk.TclError:
                pass
        self._session_save_job = self.after(500, self._auto_save_session)

    def _auto_save_session(self) -> None:
        self._session_save_job = None
        self._save_current_form()

    def _persist_session(self) -> None:
        try:
            save_session(self.documents, self.step_states, self.active_type, data_dir=self.data_dir)
        except OSError as exc:
            if hasattr(self, "status_var"):
                self.status_var.set(f"Errore nel salvataggio progressi: {exc}")

    def close_app(self) -> None:
        if self._session_save_job is not None:
            try:
                self.after_cancel(self._session_save_job)
            except tk.TclError:
                pass
        self._save_current_form()
        self._persist_session()
        self.destroy()

    def add_files(self) -> None:
        self._save_current_form()
        name = filedialog.askopenfilename(title=f"Scegli un esemplare · {self.active_type}", filetypes=[("Documenti supportati", "*.pdf *.docx *.txt *.md *.csv"), ("Tutti i file", "*.*")])
        if not name:
            return
        try:
            parsed = read_document(name)
            doc = {"path": name, "name": Path(name).name, "parsed": parsed, "type": self.active_type, "variant": "", "note": "", "fields": self._make_fields(DOC_TYPES[self.active_type])}
        except Exception as exc:
            messagebox.showerror("Lettura documento", f"Non riesco a leggere {Path(name).name}:\n{exc}")
            return
        self.documents.append(doc)
        self.step_states[self.active_type] = "Esemplari raccolti"
        self._persist_session()
        self._render_documents()
        self._render_steps()
        self._select_document(len(self.documents) - 1)

    @staticmethod
    def _make_fields(names: list[str]) -> list[dict[str, str]]:
        return [{"name": name, "status": "Da valutare", "value": "", "issue_type": "Da tipizzare", "question": "", "evidence": None} for name in names]

    def _render_documents(self) -> None:
        self.doc_list.delete(0, "end")
        for item in self.documents:
            variant = f" · {item['variant']}" if item["variant"] else ""
            self.doc_list.insert("end", f"[{item['type']}] {item['name']}{variant}")
        if self.current >= len(self.documents):
            self.current = -1

    def _render_steps(self) -> None:
        if not hasattr(self, "step_list"):
            return
        self.step_list.delete(0, "end")
        for index, name in enumerate(GUIDED_STEPS):
            specimens = sum(doc["type"] == name for doc in self.documents)
            state = self.step_states[name]
            marker = "✓" if state == "Tipologia chiusa" else ("!" if state == "In attesa del documento" else ("◉" if specimens else "○"))
            self.step_list.insert("end", f"{marker} {name} ({specimens})")
            if name == self.active_type:
                self.step_list.selection_set(index)
                self.step_list.activate(index)

    def on_step_select(self, _event: object = None) -> None:
        selection = self.step_list.curselection()
        if not selection:
            return
        selected_step = selection[0]
        blocked_prior = [name for name in GUIDED_STEPS[:selected_step] if self.step_states[name] != "Tipologia chiusa"]
        if blocked_prior:
            self.step_list.selection_clear(0, "end")
            active_index = GUIDED_STEPS.index(self.active_type)
            self.step_list.selection_set(active_index)
            self.step_list.activate(active_index)
            messagebox.showinfo("Percorso sequenziale", f"Completa «{blocked_prior[0]}» prima di passare a un documento successivo.")
            return
        self._save_current_form()
        self.current = -1
        self.active_type = GUIDED_STEPS[selected_step]
        self._persist_session()
        self.coverage_confirmed.set(False)
        self.type_var.set(self.active_type)
        matching = [i for i, doc in enumerate(self.documents) if doc["type"] == self.active_type]
        if matching:
            self._select_document(matching[-1])
        else:
            self._clear_review()
            self.status_var.set(f"Prossimo esemplare richiesto: {self.active_type}")

    def on_select(self, _event: object = None) -> None:
        selection = self.doc_list.curselection()
        if selection:
            self._select_document(selection[0])

    def _select_document(self, index: int) -> None:
        self._save_current_form()
        self.current = index
        self.coverage_confirmed.set(False)
        self.coverage_confirmed.set(False)
        self.doc_list.selection_clear(0, "end")
        self.doc_list.selection_set(index)
        self.doc_list.activate(index)
        doc = self.documents[index]
        self.type_var.set(doc["type"])
        self.active_type = doc["type"]
        self.variant_var.set(doc.get("variant", ""))
        self.note_text.delete("1.0", "end")
        self.note_text.insert("1.0", doc["note"])
        self._render_steps()
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
        self._persist_session()

    def _save_current_form(self) -> None:
        if self.current < 0 or self.current >= len(self.documents):
            return
        doc = self.documents[self.current]
        doc["type"] = self.type_var.get()
        doc["variant"] = self.variant_var.get().strip()
        doc["note"] = self.note_text.get("1.0", "end-1c").strip()
        for row in self.field_rows:
            field = row["field"]
            field["name"] = row["name"].get().strip()
            field["status"] = row["status"].get()
            field["value"] = row["value"].get().strip()
            field["issue_type"] = row["issue_type"].get()
            field["question"] = row["question"].get().strip()
        self._persist_session()

    def on_type_change(self, _event: object = None) -> None:
        if self.current < 0:
            return
        previous_type = self.documents[self.current]["type"]
        self._save_current_form()
        doc = self.documents[self.current]
        doc["type"] = self.type_var.get()
        self.active_type = doc["type"]
        if previous_type != doc["type"]:
            if not any(item["type"] == previous_type for item in self.documents):
                self.step_states[previous_type] = "Da raccogliere"
            self.step_states[doc["type"]] = "Esemplari raccolti"
        if not doc["fields"]:
            doc["fields"] = self._make_fields(DOC_TYPES.get(doc["type"], []))
        self._draw_fields()
        self._render_steps()
        self._render_documents()
        self._persist_session()

    def _draw_fields(self) -> None:
        for child in self.fields_inner.winfo_children():
            child.destroy()
        self.field_rows = []
        if self.current < 0:
            return
        doc = self.documents[self.current]
        for index, field in enumerate(doc["fields"]):
            card = ttk.LabelFrame(self.fields_inner, text=f"Campo {index + 1}", padding=6)
            card.grid(row=index, column=0, sticky="ew", pady=3)
            card.columnconfigure(1, weight=1)
            card.columnconfigure(3, weight=2)
            ttk.Radiobutton(card, text="Collega l’occorrenza selezionata a questo campo", variable=self.selected_field_index, value=index).grid(row=0, column=0, sticky="w", padx=(0, 8))
            name = ttk.Entry(card, width=24)
            name.insert(0, field["name"])
            name.grid(row=0, column=1, sticky="ew", padx=(0, 8))
            ttk.Label(card, text="Stato").grid(row=0, column=2, sticky="e", padx=(0, 4))
            status = ttk.Combobox(card, values=STATUSES, state="readonly", width=22)
            status.set(field["status"])
            status.grid(row=0, column=3, sticky="ew")
            ttk.Label(card, text="Valore revisionato").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(5, 0))
            value = ttk.Entry(card)
            value.insert(0, field["value"])
            value.grid(row=1, column=1, columnspan=3, sticky="ew", pady=(5, 0))
            ttk.Label(card, text="Natura del dubbio").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(5, 0))
            issue_type = ttk.Combobox(card, values=ISSUE_TYPES, state="readonly", width=25)
            issue_type.set(field.get("issue_type", "Da tipizzare"))
            issue_type.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(5, 0))
            ttk.Label(card, text="Domanda da chiarire").grid(row=2, column=2, sticky="e", padx=(0, 4), pady=(5, 0))
            question = ttk.Entry(card)
            question.insert(0, field.get("question", ""))
            question.grid(row=2, column=3, sticky="ew", pady=(5, 0))
            self.field_rows.append({"field": field, "name": name, "status": status, "value": value, "issue_type": issue_type, "question": question})
            for widget in (name, value, question):
                widget.bind("<KeyRelease>", self._schedule_session_save)
            status.bind("<<ComboboxSelected>>", self._schedule_session_save)
            issue_type.bind("<<ComboboxSelected>>", self._schedule_session_save)

    def add_field(self) -> None:
        if self.current < 0:
            messagebox.showinfo("Seleziona un documento", "Aggiungi e seleziona prima un documento.")
            return
        self._save_current_form()
        self.documents[self.current]["fields"].append({"name": "Nuovo campo", "status": "Da valutare", "value": "", "issue_type": "Da tipizzare", "question": "", "evidence": None})
        self.selected_field_index.set(len(self.documents[self.current]["fields"]) - 1)
        self._draw_fields()
        self._persist_session()

    def _draw_candidates(self, parsed: ExtractedDocument) -> None:
        self.candidates_tree.delete(*self.candidates_tree.get_children())
        for index, candidate in enumerate(parsed.candidates):
            self.candidates_tree.insert("", "end", iid=str(index), values=(candidate.kind, candidate.value[:120], candidate.location))
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
        row["value"].delete(0, "end")
        row["value"].insert(0, candidate.value)
        row["status"].set("Presente ma ambiguo")
        row["issue_type"].set("Significato del campo")
        row["question"].delete(0, "end")
        row["question"].insert(0, f"Confermare la mappatura · {candidate.location}")
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
        self._persist_session()

    def _clear_review(self) -> None:
        self.type_var.set(self.active_type)
        self.variant_var.set("")
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
            evidence = field.get("evidence")
            item = {"expected_field": field["name"], "status": field["status"], "source_document": Path(doc["path"]).name, "source_location": evidence.get("location") if evidence else None, "issue_type": field.get("issue_type", "Da tipizzare"), "question_to_resolve": field.get("question", "")}
            if include_values:
                item["reviewed_value"] = field["value"]
                item["evidence"] = field.get("evidence")
            fields.append(item)
        result = {"document_name": doc["name"], "document_type": doc["type"], "sample_variant": doc.get("variant", ""), "file_extension": Path(doc["path"]).suffix.lower(), "page_count": parsed.pages, "text_extracted": bool(parsed.text.strip()), "candidate_counts_by_type": {}, "expected_fields": fields, "review_note": doc["note"], "warnings": [parsed.warning] if parsed.warning else []}
        for candidate in parsed.candidates:
            result["candidate_counts_by_type"][candidate.kind] = result["candidate_counts_by_type"].get(candidate.kind, 0) + 1
        # Candidate values, page/section provenance, and surrounding excerpts
        # make the log useful for constructing exact extraction rules later.
        if include_values:
            result["candidates"] = [candidate.to_dict() for candidate in parsed.candidates]
        return result

    def _unresolved_questions(self, docs: list[dict]) -> list[str]:
        unresolved = []
        for doc in docs:
            for field in doc["fields"]:
                if field["status"] in UNDERSTOOD_STATUSES:
                    if field["status"] == "Assente in questa variante · confermato" and not field.get("question", "").strip():
                        unresolved.append(f"{doc['name']} · {field['name']} · annota perché è confermato assente")
                    continue
                if not field.get("question", "").strip() or field.get("issue_type", "Da tipizzare") == "Da tipizzare":
                    unresolved.append(f"{doc['name']} · {field['name']}")
                else:
                    unresolved.append(f"{doc['name']} · {field['name']} · {field['status']}")
        return unresolved

    def complete_step(self) -> None:
        self._save_current_form()
        specimens = [doc for doc in self.documents if doc["type"] == self.active_type]
        blockers = validate_document_type(specimens, coverage_confirmed=self.coverage_confirmed.get())
        if blockers:
            messagebox.showinfo("Il percorso resta su questa tipologia", "Non passo al documento successivo finché tutto non è compreso. Aggiungi esemplari, chiarisci i campi o completa la mappatura:\n\n" + "\n".join(blockers[:14]))
            return
        self.step_states[self.active_type] = "Tipologia chiusa"
        self._render_steps()
        self._persist_session()
        self._advance_step()

    def mark_step_unavailable(self) -> None:
        self.step_states[self.active_type] = "In attesa del documento"
        self._render_steps()
        self.status_var.set(f"Percorso sospeso su «{self.active_type}»: carica l’esemplare per riprendere.")
        self._persist_session()
        messagebox.showinfo("Percorso in attesa", f"Non salto questa tipologia. Il percorso resterà fermo su «{self.active_type}» finché non sarà caricato e compreso un esemplare.")

    def _advance_step(self) -> None:
        next_index = next((i for i, name in enumerate(GUIDED_STEPS) if self.step_states[name] != "Tipologia chiusa"), None)
        if next_index is None:
            self.status_var.set("Percorso concluso: genera il log finale con le mappature e le richieste residue.")
            return
        self.active_type = GUIDED_STEPS[next_index]
        self.step_list.selection_clear(0, "end")
        self.step_list.selection_set(next_index)
        self.step_list.activate(next_index)
        self.on_step_select()

    def save_round(self) -> None:
        if not self.documents:
            messagebox.showinfo("Percorso vuoto", "Raccogli almeno un esemplare prima di generare il log finale.")
            return
        self._save_current_form()
        pending_steps = validate_final_path(self.step_states)
        if pending_steps:
            messagebox.showinfo("Percorso non concluso", "Per generare il log finale devi completare ogni tipologia. I documenti mancanti restano in attesa e non possono essere saltati:\n\n" + "\n".join(pending_steps))
            return
        unresolved = self._unresolved_questions(self.documents)
        if unresolved:
            messagebox.showinfo("Tipizza i dubbi", "Prima del log finale, indica la natura e la domanda per ogni campo non risolto:\n\n" + "\n".join(unresolved[:12]))
            return
        docs = [self._serialize_document(doc, self.save_values_var.get()) for doc in self.documents]
        guided_path = summarize_guided_path(GUIDED_STEPS, self.step_states, self.documents)
        try:
            log_path = append_round(docs, include_values=self.save_values_var.get(), guided_path=guided_path)
        except OSError as exc:
            messagebox.showerror("Salvataggio log", str(exc))
            return
        clear_session(data_dir=self.data_dir)
        self.status_var.set(f"Log finale generato · {log_path}")
        messagebox.showinfo("Log finale generato", f"Il percorso guidato e le mappature sono stati registrati:\n\n{log_path}\n\nIl log include candidati, contesti, fonti, varianti e domande tipizzate. I file originali e il testo integrale non vengono copiati.")

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

