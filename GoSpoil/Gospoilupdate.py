import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import requests
import io
import os
import textwrap
import datetime
import sqlite3
import webbrowser

# ---------- CONFIG ----------
OMDB_API_KEY = "492917e1"   # <-- OMDb API key 
MODEL_NAME = "facebook/bart-large-cnn"    # summarization model 
POSTER_CACHE = "poster_cache"             # folder to cache posters
DB_PATH = "gospoil_local.db"              # local DB for saved movies

# ---------- Ensure poster cache dir ----------
os.makedirs(POSTER_CACHE, exist_ok=True)

# ---------- Minimal DB to save exported movies ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS exported_movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imdb_id TEXT,
                    title TEXT,
                    year TEXT,
                    summary TEXT,
                    exported_at TEXT
                )""")
    conn.commit()
    conn.close()

# ---------- OMDb functions ----------
def omdb_search(query):
    """Search OMDb for title (returns list of results or empty list)"""
    params = {"apikey": OMDB_API_KEY, "s": query}
    try:
        r = requests.get("http://www.omdbapi.com/", params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("Response") == "True":
            return data.get("Search", [])
        return []
    except Exception as e:
        # Return empty and present error upstream
        return []

def omdb_get_by_id(imdb_id):
    """Get detailed data by IMDb ID"""
    params = {"apikey": OMDB_API_KEY, "i": imdb_id, "plot": "full"}
    r = requests.get("http://www.omdbapi.com/", params=params, timeout=12)
    r.raise_for_status()
    return r.json()

def download_poster(url, title):
    """Download and cache poster; returns local path or None"""
    if not url or url in ("N/A", ""):
        return None
    # create safe filename
    base = "".join(c if c.isalnum() or c in "-_.() " else "_" for c in title)[:100]
    ext = os.path.splitext(url.split("?")[0])[1] or ".jpg"
    filename = f"{base}{ext}"
    path = os.path.join(POSTER_CACHE, filename)
    if os.path.exists(path):
        return path
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception:
        return None

# ---------- Transformers summarizer setup ----------
# Import pipeline lazily and handle errors so GUI starts even if model not yet downloaded.
summarizer = None
def ensure_summarizer():
    global summarizer
    if summarizer is not None:
        return
    try:
        from transformers import pipeline
        # instantiate; this will download the model the first time (may take time)
        summarizer = pipeline("summarization", model=MODEL_NAME)
    except Exception as e:
        summarizer = None
        raise e

def generate_summary_from_text(text):
    """Return 2-3 paragraph summary (string). Uses summarizer if available; falls back to a stub."""
    if not text:
        return "No plot text available to summarize."
    try:
        ensure_summarizer()
    except Exception as e:
        # If summarizer fails (no torch/model), fallback to a deterministic stub generator
        return generate_summary_stub("Movie", keywords=None)
    try:
        # Some models expect shorter input; clamp length by chopping to a reasonable size
        input_text = text.strip()
        # summarizer returns list of dicts with 'summary_text' on many models
        out = summarizer(input_text, max_length=180, min_length=60, do_sample=False)
        if isinstance(out, list) and len(out) > 0:
            summary = out[0].get("summary_text") or out[0].get("generated_text") or str(out[0])
            return summary.strip()
        return str(out)
    except Exception as e:
        # fallback stub
        return generate_summary_stub("Movie", keywords=None)

def generate_summary_stub(title, year=None, keywords=None):
    """Deterministic template stub if HF model unavailable."""
    import random
    random.seed((title + (str(year) if year else "") + (keywords or ""))[:64])
    openings = [
        f"{title} is a {random.choice(['taut', 'gentle', 'thrilling', 'surprising', 'wistful'])} film",
        f"In {title}, the story explores",
        f"{title} follows"
    ]
    mid = [
        "a character forced to confront their past",
        "a group of unlikely allies",
        "a dark secret that changes everything",
        "a bittersweet journey through memory and choice",
        "a high-stakes race against time"
    ]
    p1 = f"{random.choice(openings)}. It centers on {random.choice(mid)} and the emotional consequences that follow."
    p2 = f"The film blends {random.choice(['intimate drama', 'fast-paced action', 'moody atmosphere', 'dry humor', 'genre-bending twists'])} with strong character work, culminating in an ending that feels {random.choice(['earned', 'ambiguous', 'surprising', 'heartfelt'])}."
    return f"{p1}\n\n{p2}"

# ---------- GUI ----------
class GoSpoilApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GoSpoil")
        self.geometry("980x680")
        self.configure(bg="#121212")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#121212", foreground="#e6eef6")
        self.style.configure("TButton", background="#1f1f1f", foreground="#e6eef6")
        self.selected_imdb = None
        self.poster_img_ref = None
        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Search movie title:").pack(side="left", padx=(0,8))
        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var, width=50)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self.do_search())

        ttk.Button(top, text="Search", command=self.do_search).pack(side="left", padx=6)
        ttk.Button(top, text="Clear", command=self.clear_results).pack(side="left")

        # left: results list
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=(0,10))

        left = ttk.Frame(main, width=320)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Search results:").pack(anchor="w")
        self.results_list = tk.Listbox(left, width=45, height=30, bg="#0f1113", fg="#e6eef6", activestyle="none")
        self.results_list.pack(side="left", fill="y", pady=6)
        self.results_list.bind("<<ListboxSelect>>", self.on_result_select)

        scr = ttk.Scrollbar(left, orient="vertical", command=self.results_list.yview)
        scr.pack(side="left", fill="y")
        self.results_list.config(yscrollcommand=scr.set)

        # right: details
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True, padx=(12,0))

        header = ttk.Frame(right)
        header.pack(fill="x")
        self.title_label = ttk.Label(header, text="Select a movie", font=("Segoe UI", 14, "bold"))
        self.title_label.pack(side="left")

        btns = ttk.Frame(header)
        btns.pack(side="right")
        ttk.Button(btns, text="Generate Summary", command=self.on_generate_summary).pack(side="left", padx=6)
        ttk.Button(btns, text="Quick Spoil", command=self.on_quick_spoil).pack(side="left", padx=6)
        ttk.Button(btns, text="Export TXT", command=self.on_export).pack(side="left", padx=6)

        # poster + meta
        meta_frame = ttk.Frame(right)
        meta_frame.pack(fill="x", pady=(8,6))

        self.poster_label = tk.Label(meta_frame, bg="#121212")
        self.poster_label.pack(side="left", padx=(6,12))

        info = ttk.Frame(meta_frame)
        info.pack(side="left", fill="x", expand=True)
        self.info_text = tk.Text(info, height=6, width=60, bg="#0b0c0f", fg="#e6eef6", relief="flat", wrap="word")
        self.info_text.pack(fill="both", expand=True)

        # summary
        ttk.Label(right, text="AI Summary:").pack(anchor="w", pady=(6,0))
        self.summary_text = tk.Text(right, height=12, bg="#0b0c0f", fg="#e6eef6", wrap="word")
        self.summary_text.pack(fill="both", expand=True, pady=(4,0))

    # ---------- Search / results ----------
    def do_search(self):
        q = self.search_var.get().strip()
        if not q:
            messagebox.showinfo("Empty", "Enter a movie title to search.")
            return
        self.results_list.delete(0, tk.END)
        self.clear_details()
        # Perform OMDb search
        try:
            results = omdb_search(q)
        except Exception as e:
            messagebox.showerror("OMDb error", f"Failed to search: {e}")
            return
        if not results:
            messagebox.showinfo("No results", "No movies found (try a different title).")
            return
        # populate listbox
        self.search_results = results
        for item in results:
            title = item.get("Title")
            year = item.get("Year", "")
            typ = item.get("Type", "")
            label = f"{title} ({year}) [{typ}]"
            self.results_list.insert(tk.END, label)

    def clear_results(self):
        self.search_var.set("")
        self.results_list.delete(0, tk.END)
        self.clear_details()

    def on_result_select(self, evt):
        sel = self.results_list.curselection()
        if not sel:
            return
        idx = sel[0]
        item = self.search_results[idx]
        imdb_id = item.get("imdbID")
        if not imdb_id:
            messagebox.showerror("Error", "No imdbID found for selection.")
            return
        try:
            data = omdb_get_by_id(imdb_id)
        except Exception as e:
            messagebox.showerror("OMDb error", f"Failed to fetch details: {e}")
            return
        # display metadata + poster
        self.selected_imdb = imdb_id
        title = data.get("Title", "Unknown")
        year = data.get("Year", "")
        self.title_label.config(text=f"{title} ({year})")
        info = []
        if data.get("Genre"): info.append(f"Genre: {data.get('Genre')}")
        if data.get("Director"): info.append(f"Director: {data.get('Director')}")
        if data.get("Actors"): info.append(f"Actors: {data.get('Actors')}")
        if data.get("imdbRating"): info.append(f"IMDb: {data.get('imdbRating')}")
        plot_short = data.get("Plot", "")
        info_text = "\n".join(info) + "\n\n" + (plot_short or "")
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state="disabled")
        # poster
        poster_url = data.get("Poster")
        poster_path = download_poster(poster_url, title)
        if poster_path and os.path.exists(poster_path):
            try:
                img = Image.open(poster_path)
                img.thumbnail((260, 400), Image.Resampling.LANCZOS)
                self.poster_img_ref = ImageTk.PhotoImage(img)
                self.poster_label.config(image=self.poster_img_ref, text="")
            except Exception:
                self.poster_label.config(image="", text="Poster\nunavailable", fg="#e6eef6")
        else:
            self.poster_label.config(image="", text="Poster\nunavailable", fg="#e6eef6")
        # clear summary area (user chooses to generate)
        self.summary_text.delete("1.0", tk.END)    
    # ---------- Clear details ----------
    def clear_details(self):
        """Clears movie info, poster, and summary fields."""
        self.title_label.config(text="Select a movie")
        self.info_text.config(state="normal")
        self.info_text.delete("1.0", tk.END)
        self.info_text.config(state="disabled")
        self.poster_label.config(image="", text="", fg="#e6eef6")
        self.summary_text.delete("1.0", tk.END)
        self.poster_img_ref = None
        self.selected_imdb = None


    # ---------- AI summary ----------
    def on_generate_summary(self):
        if not self.selected_imdb:
            messagebox.showwarning("No selection", "Select a movie from the search results first.")
            return
        try:
            data = omdb_get_by_id(self.selected_imdb)
        except Exception as e:
            messagebox.showerror("OMDb error", f"Failed to fetch details: {e}")
            return
        plot = data.get("Plot") or data.get("Plot") or ""
        # produce a summary
        self.summary_text.delete("1.0", tk.END)
        # show a busy popup while generating
        popup = tk.Toplevel(self)
        popup.title("Generating summary")
        ttk.Label(popup, text="Generating AI summary — this may take a moment...").pack(padx=12, pady=12)
        popup.transient(self)
        popup.grab_set()
        self.update_idletasks()
        try:
            summary = generate_summary_from_text(plot)
        except Exception as e:
            summary = f"(Failed to generate with model: {e})\n\nFallback summary:\n\n" + generate_summary_stub(data.get("Title", "Movie"))
        finally:
            popup.destroy()
        self.summary_text.insert(tk.END, summary)

    def on_quick_spoil(self):
        if not self.selected_imdb:
            messagebox.showwarning("No selection", "Select a movie first.")
            return
        try:
            data = omdb_get_by_id(self.selected_imdb)
        except Exception as e:
            messagebox.showerror("OMDb error", f"Failed to fetch details: {e}")
            return
        # Quick spoil: just return one sentence from stub or first sentence of plot
        plot = data.get("Plot") or ""
        if plot:
            # try to pick a revealing sentence (naive)
            sentence = plot.split(".")[0].strip()
            if len(sentence) > 10:
                messagebox.showinfo("Quick Spoil", sentence + ".")
                return
        # fallback
        qs = generate_summary_stub(data.get("Title", "Movie")).split("\n")[0]
        messagebox.showinfo("Quick Spoil", qs)

    # ---------- Export ----------
    def on_export(self):
        if not self.selected_imdb:
            messagebox.showwarning("No selection", "Select a movie first.")
            return
        try:
            data = omdb_get_by_id(self.selected_imdb)
        except Exception as e:
            messagebox.showerror("OMDb error", f"Failed to fetch details: {e}")
            return
        title = data.get("Title", "Unknown")
        year = data.get("Year", "")
        summary = self.summary_text.get("1.0", tk.END).strip()
        if not summary:
            if messagebox.askyesno("No summary", "No AI summary present. Export plot instead?"):
                summary = data.get("Plot", "")
            else:
                return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")], initialfile=f"{title}.txt")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\n")
            if year: f.write(f"Year: {year}\n")
            f.write("\nSummary:\n")
            f.write(summary + "\n")
            f.write("\nMetadata:\n")
            f.write(f"IMDb ID: {self.selected_imdb}\n")
            f.write(f"Exported at: {datetime.datetime.utcnow().isoformat()}Z\n")
        # optional: save a small record to local DB
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO exported_movies (imdb_id, title, year, summary, exported_at) VALUES (?, ?, ?, ?, ?)",
                        (self.selected_imdb, title, year, summary, datetime.datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
        except Exception:
            pass
        messagebox.showinfo("Exported", f"Exported to {path}")

# ---------- run ----------
if __name__ == "__main__":
    init_db()
    app = GoSpoilApp()
    app.mainloop()
