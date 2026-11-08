import fitz
import os 
import json



class ImageExtractor: 
    def __init__(self,pdf_path:str, output_dir: str= "output", full_page:bool = False): 
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.pdf = fitz.open(self.pdf_path)
        os.makedirs(output_dir,exist_ok=True)


    def extract_images(self): 
        for page_number, page in enumerate(self.pdf): 
            images = page.get_images(full=True)
            for index,image in enumerate(images): 
                xref = image[0]
                image_data = self.pdf.extract_image(xref)   
                image_bytes = image_data['image']
                extension = image_data['ext']

                filename = (
                    f'{page_number}'
                    f'.{extension}'
                )

                path = os.path.join(self.output_dir,"images", filename)

                with open(path,"wb") as f: 
                    f.write(image_bytes)
        return "image saved Successfully."
