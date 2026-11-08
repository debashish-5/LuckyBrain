import fitz 
import os 
import json


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