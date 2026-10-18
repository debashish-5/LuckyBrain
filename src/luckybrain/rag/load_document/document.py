import json
import re 
from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError
import json
from concurrent.futures import ThreadPoolExecutor


class PDFExtracor: 
    def __init__(self, path, password = None, clean = True, ocr_fallback = False): 
        self.path = Path(path)
        if not self.path.exists(): 
            raise ValueError("PDF not found",self.path)
        if self.path.suffix.lower() != ".pdf":
            raise ValueError("File must have a .pdf extension")
        self.password = password
        self.clean = clean
        self.ocr_fallback = ocr_fallback
        self._cache = {}

        try: 
            self.reader = PdfReader(str(self.path))
        except Exception as e: 
            raise ValueError(f"Can not read PDF: {e}") from e 
        if self.reader.is_encrypted: 
            if not self.reader.decrypt(password=password or ""): 
                raise ValueError("PDF is encrypted: Missing wrong password")

    @property
    def num_pages(self): 
        return len(self.reader.pages)

    def __len__(self): 
        return self.num_pages

    def __repr__(self):
        f"PDFExtractor(path = {self.path}, pages = {self.num_pages})"

    def metadata(self): 
        meta = self.reader.metadata
        return {
            'title':getattr(meta,"title", None), 
            'author':getattr(meta,'author',None), 
            'creator':getattr(meta, 'creator', None), 
            'created':getattr(meta,'creation_date',None), 
            'page':self.num_pages, 
        }

    @staticmethod
    def _clean(text): 
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)        # join hyphenated words
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)        # single newline -> space
        text = re.sub(r"[ \t]+", " ", text)                 # collapse spaces
        text = re.sub(r"\n{3,}", "\n\n", text)              # collapse blank lines
        return text.strip()

    def _check_page(self, n): 
        raise ValueError(f"Page must be between 1 and {self.num_pages}")

    def page_text(self,page_number): 
        """Page_number start at one."""
        self._check_page(page_number)
        if page_number in self._cache: 
            return self._cache[page_number]

        try: 
            text = self.reader.pages[page_number-1].extract_text() or ""

        except Exception as e: 
            text = ""
        if self.clean: 
            text = self._clean(text=text)
        text = text.strip()


        if not text and self.ocr_fallback:
            text = self._ocr_page(page_number)

        self._cache[page_number] = text
        return text

    def pages(self, start=1, end=None):
        """List of {'page': n, 'text': ...}. Range is inclusive, 1-based."""
        end = end or self.num_pages
        self._check_page(start)
        self._check_page(end)
        return [{"page": i, "text": self.page_text(i)} for i in range(start, end + 1)]

    def text(self, start=1, end=None):
        return "\n\n".join(p["text"] for p in self.pages(start, end) if p["text"])

    # ---------- chunking (for RAG / LLM prompts) ----------
    def chunks(self, size=1000, overlap=200):
        if size <= 0 or not 0 <= overlap < size:
            raise ValueError("Need size > 0 and 0 <= overlap < size")

        result = []
        for p in self.pages():
            text, start = p["text"], 0
            while start < len(text):
                end = min(start + size, len(text))
                if end < len(text):                      # try to cut at a natural boundary
                    cut = max(text.rfind(". ", start, end),
                              text.rfind("\n", start, end),
                              text.rfind(" ", start, end))
                    if cut > start + size // 2:
                        end = cut + 1
                piece = text[start:end].strip()
                if piece:
                    result.append({"id": len(result), "page": p["page"], "text": piece})
                if end >= len(text):
                    break
                start = max(end - overlap, start + 1)    # always move forward
        return result

    # ---------- search ----------
    def search(self, keyword, context=60):
        """Case-insensitive keyword search. Returns page numbers and snippets."""
        hits = []
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        for p in self.pages():
            for m in pattern.finditer(p["text"]):
                a, b = max(0, m.start() - context), min(len(p["text"]), m.end() + context)
                hits.append({"page": p["page"], "snippet": p["text"][a:b].replace("\n", " ")})
        return hits

    # ---------- scanned PDF detection ----------
    def is_scanned(self, sample=5, min_chars=20):
        """True if most sampled pages have almost no extractable text."""
        n = min(sample, self.num_pages)
        empty = sum(1 for i in range(1, n + 1) if len(self.page_text(i)) < min_chars)
        return empty > n / 2

    # ---------- optional: OCR ----------
    def _ocr_page(self, page_number):
        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ImportError:
            raise ImportError("OCR needs: pip install pytesseract pdf2image "
                              "(plus Tesseract and Poppler installed on your system)")
        images = convert_from_path(str(self.path), dpi=300,
                                   first_page=page_number, last_page=page_number,
                                   userpw=self.password)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
        return self._clean(text) if self.clean else text.strip()

    # ---------- optional: tables ----------
    def tables(self, page_number=None):
        """Extract tables as lists of rows. Needs: pip install pdfplumber"""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("Tables need: pip install pdfplumber")

        results = []
        with pdfplumber.open(str(self.path), password=self.password) as pdf:
            numbers = [page_number] if page_number else range(1, self.num_pages + 1)
            for n in numbers:
                self._check_page(n)
                for table in pdf.pages[n - 1].extract_tables():
                    results.append({"page": n, "rows": table})
        return results

    # ---------- saving ----------
    def save_text(self, out_path):
        Path(out_path).write_text(self.text(), encoding="utf-8")

    def save_json(self, out_path):
        data = {"metadata": self.metadata(), "pages": self.pages()}
        Path(out_path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )





class PDFDirectory:
    def __init__(self, folder, recursive=False, password=None, clean=True, ocr_fallback=False):
        self.folder = Path(folder)
        if not self.folder.is_dir():
            raise NotADirectoryError(f"Folder not found: {self.folder}")

        self.password = password
        self.clean = clean
        self.ocr_fallback = ocr_fallback
        self.errors = {}          # {filename: error message}
        self._docs = {}           # {path: PDFExtractor}

        pattern = "**/*" if recursive else "*"
        self.files = sorted(
            p for p in self.folder.glob(pattern)
            if p.is_file() and p.suffix.lower() == ".pdf"
        )

    def __len__(self):
        return len(self.files)

    def __repr__(self):
        return f"PDFDirectory({str(self.folder)!r}, files={len(self.files)})"

    # ---------- loading ----------
    def _load(self, path):
        if path in self._docs:
            return self._docs[path]
        try:
            doc = PDFExtractor(
                path, password=self.password,
                clean=self.clean, ocr_fallback=self.ocr_fallback,
            )
        except Exception as e:
            self.errors[path.name] = str(e)
            return None
        self._docs[path] = doc
        return doc

    def documents(self):
        """Yield (path, PDFExtractor) for each readable PDF. Bad files are skipped."""
        for path in self.files:
            doc = self._load(path)
            if doc:
                yield path, doc

    # ---------- overview ----------
    def summary(self):
        """One row per PDF: name, pages, title, scanned or not."""
        rows = []
        for path, doc in self.documents():
            meta = doc.metadata()
            rows.append({
                "file": str(path.relative_to(self.folder)),
                "pages": doc.num_pages,
                "title": meta["title"],
                "scanned": doc.is_scanned(),
            })
        return rows

    # ---------- text ----------
    def texts(self, workers=1):
        """Return {relative_file_name: full_text}. Use workers=4 for big folders."""
        def work(path):
            doc = self._load(path)
            return str(path.relative_to(self.folder)), (doc.text() if doc else None)

        if workers > 1:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                results = list(pool.map(work, self.files))
        else:
            results = [work(p) for p in self.files]

        return {name: text for name, text in results if text is not None}

    def chunks(self, size=1000, overlap=200):
        """All chunks from all PDFs, each tagged with its source file (for RAG)."""
        result = []
        for path, doc in self.documents():
            for c in doc.chunks(size=size, overlap=overlap):
                result.append({
                    "id": len(result),
                    "file": str(path.relative_to(self.folder)),
                    "page": c["page"],
                    "text": c["text"],
                })
        return result

    # ---------- search ----------
    def search(self, keyword, context=60):
        """Search all PDFs. Returns file, page and snippet for each hit."""
        hits = []
        for path, doc in self.documents():
            for h in doc.search(keyword, context=context):
                hits.append({"file": str(path.relative_to(self.folder)), **h})
        return hits

    # ---------- saving ----------
    def save_texts(self, out_folder):
        """Write one .txt per PDF into out_folder."""
        out = Path(out_folder)
        out.mkdir(parents=True, exist_ok=True)
        for name, text in self.texts().items():
            target = out / (name.replace("/", "_").replace("\\", "_").rsplit(".", 1)[0] + ".txt")
            target.write_text(text, encoding="utf-8")
        return out

    def save_chunks_json(self, out_path, size=1000, overlap=200):
        data = self.chunks(size=size, overlap=overlap)
        Path(out_path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return len(data)# files that failed, with the reason# files that failed, with the reason








    