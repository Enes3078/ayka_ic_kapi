import os
import fitz  # PyMuPDF
import json
import re

def extract_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    extracted_data = []
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        
        # Try to find images
        image_list = page.get_images(full=True)
        images = []
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append({
                "xref": xref,
                "size": len(image_bytes)
            })
            
        extracted_data.append({
            "page": page_num + 1,
            "text": text,
            "image_count": len(images),
            "images": images
        })
    
    return extracted_data

def main():
    desktop_dir = "/Users/erlikhan/Desktop/deneme"
    results = {}
    for i in range(1, 5):
        pdf_name = f"{i}.pdf"
        pdf_path = os.path.join(desktop_dir, pdf_name)
        if os.path.exists(pdf_path):
            print(f"Extracting {pdf_name}...")
            data = extract_from_pdf(pdf_path)
            results[pdf_name] = data
            
            # Print a snippet of the text from page 1 to see the format
            if data:
                print(f"--- {pdf_name} Page 1 Text ---")
                print(data[0]["text"][:1000])
                print("-" * 40)
        else:
            print(f"{pdf_name} not found.")
            
    # Save full text to a JSON for inspection
    with open(os.path.join(desktop_dir, "scratch/pdf_texts.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    os.makedirs("/Users/erlikhan/Desktop/deneme/scratch", exist_ok=True)
    main()
