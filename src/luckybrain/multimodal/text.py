import fitz 
import os 
import json
import pdfplumber
from typing import Literal





class TextExtractor: 
    def __init__(self,output:str ="output"): 
        os.makedirs(output,exist_ok=True)
        self.output_dir = output


    def FileExtractor(self, file_name:str, saved_json_filename:str="text.json"):
        pdf = fitz.open(filename=file_name)
        outputfile = os.path.join(self.output_dir, saved_json_filename)
        for page_number, page in enumerate(pdf):
            text = page.get_text()  
            json_page_text = {
                "page_number":page_number, 
                "text":text
            }
            with open(outputfile,"w", encoding="utf-8") as f: 
                json.dump(json_page_text, f, ensure_ascii=False, indent=2)

        return "Data saved Successfully in json format."


class ImageExtractor: 
    def __init__(self,output_folder:str = "output"): 
        os.makedirs(output_folder, exist_ok=True)
        self.output_dir = output_folder

    
    def ImageExtractor(self,file_name:str): 
        pdf = fitz.open(file_name)
        for page_number, page in enumerate(pdf): 
            images = page.get_images(full=True)
            for index, image in enumerate(images): 
                xref = image[0]
                image_data = self.pdf.extract_image(xref)
                image_bytes = image_data['image']
                extension = image_data['ext']
                filename = f'{page_number}_img{index}.{extension}'
                path = os.path.join(self.output_dir, "images",file_name)
                with open(path, "wb") as f:
                    f.write(image_bytes)        
                print(f"Page Number: {page_number} - image : {index} is Saved")



class TableExtractor: 
    def __init__(self,source:str | Literal['file','folder'],output_folder:str = "outptut"): 
        self.output_dir = output_folder
        self.source = source

    def extract_tables_in_file(self, filepath:str): 
        all_tables_data = []
        with pdfplumber.open(filepath) as pdf: 
            for page_number,page in enumerate(pdf.pages): 
                tables = page.extract_tables()
                for index, table in enumerate(tables): 
                    if not table: 
                        continue
                    header = table[0]
                    rows = table[1:]
                    data = [dict(zip(header, row)) for row in rows]

                    all_tables_data.append({
                        "page":page_number + 1, 
                        "table_index":index, 
                        "data":data
                    })

        with open('output.json', "w", encoding="utf-8") as f: 
            json.dump(all_tables_data, f,indent=4)
        print("Everything saved.")
        

                    
