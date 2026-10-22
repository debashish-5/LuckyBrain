import fitz
import os
import json
from pathlib import Path
import re 
import pdfplumber

import csv

class DocumentParsing: 
    def __int__(self,path:str, imagepath_to_save:str): 
        self.path = path
        self.document = {
            'file_name':"{path}", 
            'pages':[
            ]

        }
        self.output_img_path = imagepath_to_save
        os.makedirs(imagepath_to_save, exist_ok=True)
        self.structured_data = {
            "document":os.path.basename(path), 
            "pages":[]
        }
        self.doc = self.fitz.open(path)
        

    def parsing(self): 
        for page_num in range(len(self.doc)): 
            page = self.doc[page_num]
            page_data = {
                "page_number":page_num + 1, 
                "elements":[]
            }
            blocks = page.get_text("blocks")
            for b in blocks: 
                text = b[4].strip()
                if not text: 
                    continue

                if len(text.split("\n")) == 1 and len(text) < 60 or text.isupper(): 
                    element_type = "heading"
                else: 
                    element_type = "paragraph"

                page_data['elements'].append(
                    {
                        "type":element_type, 
                        "text":text
                    }
                )

            ## let's parsing images
            images = page.get_images(full=True)
            for img_idx, img_info in enumerate(images):
                xref = img_info[0]
                base_image = self.doc.extract_images(xref)
                image_bytes = base_image['image']
                image_ext = base_image['ext']
                img_filename = (
                    f'page{page_num + 1}_image{img_idx + 1}.{image_ext}'
                )
                img_path = os.path.join(self.output_img_path,img_filename)
                with open(img_path,"wb") as f: 
                    f.write(image_bytes)

                page_data["elements"].append({
                    "type":"image",
                    "path":img_path
                })

            if page_data['elements']: 
                self.structured_data['pages'].append(page_data)

        return json.dumps(
            self.structured_data, indent=2
        )




        

class TableExtractor: 
    STRATEGIES = {
        "lines":{'vertical_strategy':"lines", "horizontal_strategy":"lines"}, 
        "text":{"vertical_strategy":"text","horizontal_strategy":"text"}
    }
    def __init__(self, path:str, password = None): 
        self.path = Path(path)
        if not self.path.exists(): 
            raise ValueError(f"PDF not found:{self.path}")
        self.password = password

    #main method
    def extract(self,page=None, strategy = "auto",header = True, merge = True): 
        """
        pages:    None (all), one page number, or a list/range. Page numbers start at 1.
        strategy: "lines" (tables with borders), "text" (borderless tables),
                  or "auto" (try lines first, fall back to text).
        header:   treat the first row as column names.
        merge:    join a table continued on the next page (when the header repeats).
        Returns a list of {'id', 'page', 'header', 'rows'}.
        """
        if strategy not in ("auto","lines","text"): 
            raise ValueError("Strategy must be 'auto','lines'or 'text'")
        
        tables = []

        with pdfplumber.open(str(self.path),password=self.password) as pdf: 
            for n in self._page_number(page, len(pdf.pages)): 
                page = pdf.pages[n-1]
                for raw in self._find(page, strategy): 
                    rows = self._clean(raw)
                    if len(rows) < 2 or len(rows[0]) < 2: 
                        continue
                    if header: 
                        head, body = self._unique(rows[0]), rows[1:]
                    else:
                        head, body = [f"col_{i + 1}" for i in range(len(rows[0]))], rows
                    tables.append({"page": n, "header": head, "rows": body})

        if merge and header: 
            tables = self._merge(tables)
        for i, t in enumerate(tables): 
            t['id'] = i+1
        return tables

    @staticmethod
    def _page_numbers(pages, total):
        if pages is None:
            nums = range(1, total + 1)
        elif isinstance(pages, int):
            nums = [pages]
        else:
            nums = list(pages)
        for n in nums:
            if not 1 <= n <= total:
                raise ValueError(f"Page must be between 1 and {total}")
        return nums

    def _find(self, page, strategy):
        if strategy in ("auto", "lines"):
            found = page.extract_tables(self.STRATEGIES["lines"])
            if found or strategy == "lines":
                return found
        return page.extract_tables(self.STRATEGIES["text"])

    @staticmethod
    def _clean(raw):
        rows = [
            [re.sub(r"\s+", " ", c).strip() if c else "" for c in row]
            for row in raw
        ]
        width = max((len(r) for r in rows), default=0)
        rows = [r + [""] * (width - len(r)) for r in rows]
        rows = [r for r in rows if any(r)]                    # drop empty rows
        keep = [i for i in range(width) if any(r[i] for r in rows)]
        return [[r[i] for i in keep] for r in rows]           # drop empty columns

    @staticmethod
    def _unique(names):
        """Empty or repeated column names become col_N / name_2."""
        seen, result = {}, []
        for i, name in enumerate(names):
            name = name or f"col_{i + 1}"
            seen[name] = seen.get(name, 0) + 1
            result.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
        return result

    
    @staticmethod
    def _merge(tables):
        merged = []
        for t in tables:
            prev = merged[-1] if merged else None
            if (prev and t["page"] == prev["pages"][-1] + 1
                    and t["header"] == prev["header"]):
                prev["rows"].extend(t["rows"])
                prev["pages"].append(t["page"])
            else:
                merged.append({**t, "pages": [t["page"]]})
        for t in merged:
            t["page"] = t["pages"][0]
            del t["pages"]
        return merged

    # ---------- convert one table ----------
    @staticmethod
    def to_dicts(table):
        return [dict(zip(table["header"], row)) for row in table["rows"]]

    @staticmethod
    def to_markdown(table):
        """Good format for sending a table to an LLM."""
        esc = lambda c: c.replace("|", "\\|")
        lines = ["| " + " | ".join(esc(h) for h in table["header"]) + " |",
                 "|" + "|".join("---" for _ in table["header"]) + "|"]
        lines += ["| " + " | ".join(esc(c) for c in r) + " |" for r in table["rows"]]
        return "\n".join(lines)

    @staticmethod
    def to_dataframe(table):
        import pandas as pd                   # pip install pandas
        return pd.DataFrame(table["rows"], columns=table["header"])

    # ---------- save ----------
    @staticmethod
    def save_csv(tables, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for t in tables:
            p = folder / f"table_{t['id']}_page_{t['page']}.csv"
            with open(p, "w", newline="", encoding="utf-8-sig") as f:   # opens cleanly in Excel
                w = csv.writer(f)
                w.writerow(t["header"])
                w.writerows(t["rows"])
            paths.append(p)
        return paths


    @staticmethod
    def save_excel(tables, out_path): 
        """All tables in one .xlsx file, one sheet each. Needs: pip install pandas openpyxl"""
        import pandas as pd 
        with pd.ExcelWriter(out_path) as writer: 
            for t in tables:
                df = pd.DataFrame(t['rows'],columns=t['header'])
                df.to_excel(writer, sheet_name=f"t{t['id']}_p{t['page']}"[:31], index=False)

    @staticmethod
    def save_json(tables, out_path): 
        Path(out_path).write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")