import os
import sys
import django
import fitz
import re

sys.path.append('/Users/erlikhan/Desktop/deneme/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tasks.models import Product

def main():
    desktop_dir = "/Users/erlikhan/Desktop/deneme"
    total_imported = 0
    
    for i in range(1, 5):
        pdf_path = os.path.join(desktop_dir, f"{i}.pdf")
        if not os.path.exists(pdf_path):
            continue
            
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
            
        # Parse AY-XX blocks
        blocks = re.split(r'(AY-\d+)', text)
        
        if len(blocks) > 1:
            for j in range(1, len(blocks), 2):
                model_code = blocks[j].strip()
                content = blocks[j+1]
                
                # Extract Duration (DK)
                duration_match = re.search(r'İŞLEME SÜRESİ\s*:\s*([\d,]+)\s*DK', content, re.IGNORECASE)
                duration = 0
                if duration_match:
                    dur_str = duration_match.group(1).replace(',', '.')
                    duration = float(dur_str)
                    
                # Extract Blade Depth
                blade_match = re.search(r'BIÇAK DERİNLİĞİ\s*:\s*([\d,]+)\s*MM', content, re.IGNORECASE)
                blade_max = 0
                if blade_match:
                    blade_str = blade_match.group(1).replace(',', '.')
                    blade_max = float(blade_str)
                    
                Product.objects.update_or_create(
                    code=model_code,
                    defaults={
                        'name': 'İç Kapı',
                        'duration_minutes': duration,
                        'blade_max_mm': blade_max,
                    }
                )
                print(f"Imported {model_code} (Duration: {duration} min, Blade: {blade_max} mm)")
                total_imported += 1

    print(f"\nTotal products imported/updated: {total_imported}")

if __name__ == "__main__":
    main()
