import fitz
import os
import json
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




        

    
    