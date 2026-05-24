"""
Excel Import Service — .xlsx dosyasını okuyup Draft Task verisi döner.
"""
import openpyxl
from io import BytesIO
import re

REQUIRED_HEADERS = {
    'ÜRETİLECEK ÜRÜN İSMİ': 'product_name',
    'KATEGORİ KODU': 'model_code',
    'SİPARİŞ SERİ': 'order_serial',
    'SİPARİŞ SIRA': 'order_sequence',
    'ÜRETİM MİKTARI': 'quantity',
    'SİPARİŞ AÇIKLAMA_1': 'description_1',
    'SİPARİŞ AÇIKLAMA_2': 'description_2',
}

OPTIONAL_HEADERS = {
    'İŞ EMRİ İSMİ': 'work_order_name',
    'DURUMU': 'status',
    'ÖLÇÜ': 'dimension',
    'RENK': 'color',
    'BIÇAK DERİNLİĞİ': 'blade_depth',
}


def normalize_text(value):
    text = str(value or '').strip().lower()
    return (
        text.replace('ı', 'i')
        .replace('ğ', 'g')
        .replace('ü', 'u')
        .replace('ş', 's')
        .replace('ö', 'o')
        .replace('ç', 'c')
    )


def is_excluded_model(product_name, model_code):
    searchable = f'{normalize_text(product_name)} {normalize_text(model_code)}'
    excluded_terms = ['takim', 'sarf urunu', 'sarf']
    return any(term in searchable for term in excluded_terms)


def format_descriptions(*descriptions):
    clean_descriptions = [str(item or '').strip() for item in descriptions if str(item or '').strip()]
    if len(clean_descriptions) <= 1:
        return clean_descriptions[0] if clean_descriptions else ''
    return '\n'.join(f'{index}) {description}' for index, description in enumerate(clean_descriptions, start=1))


def parse_excel_file(file_obj):
    warnings = []
    try:
        content = file_obj.read()
        wb = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        raise ValueError(f'Excel dosyası okunamadı: {str(e)}')

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError('Excel dosyası boş.')

    raw_headers = [str(h).strip().upper() if h else '' for h in rows[0]]
    header_map = {}
    missing = []

    for req_h, field in REQUIRED_HEADERS.items():
        found = False
        for idx, rh in enumerate(raw_headers):
            if rh == req_h:
                header_map[idx] = field
                found = True
                break
        if not found:
            missing.append(req_h)

    if missing:
        raise ValueError(f'Eksik zorunlu başlıklar: {", ".join(missing)}')

    for opt_h, field in OPTIONAL_HEADERS.items():
        for idx, rh in enumerate(raw_headers):
            if rh == opt_h:
                header_map[idx] = field
                break

    product_lines = []
    for row_idx, row in enumerate(rows[1:], start=2):
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue

        row_data = {}
        for col_idx, field_name in header_map.items():
            row_data[field_name] = row[col_idx] if col_idx < len(row) and row[col_idx] is not None else ''

        product_name = str(row_data.get('product_name', '')).strip()
        work_order_name = str(row_data.get('work_order_name', '')).strip()
        quantity_raw = str(row_data.get('quantity', '')).strip()
        
        if not work_order_name:
            continue

        if not product_name and not quantity_raw:
            continue

        model_code = str(row_data.get('model_code', '')).strip()
        if not model_code:
            model_code = product_name or 'Bilinmeyen Model'

        if is_excluded_model(product_name, model_code):
            warnings.append(
                f'Satır {row_idx}: Takım/sarf ürünü olduğu için içe aktarılmadı ({product_name or model_code}).'
            )
            continue

        try:
            quantity = max(1, int(float(quantity_raw or 1)))
        except (ValueError, TypeError):
            quantity = 1
            warnings.append(f'Satır {row_idx}: Miktar geçersiz, 1 ayarlandı.')

        try:
            blade_depth = float(str(row_data.get('blade_depth', 0)))
        except (ValueError, TypeError):
            blade_depth = 0

        desc1 = str(row_data.get('description_1', '')).strip()
        desc2 = str(row_data.get('description_2', '')).strip()
        notes = format_descriptions(desc1, desc2)

        # Regex ile Boyut (Ölçü) tespiti (Örn: 90x210, 100X200, 100*200, 1200 x 800, 90*197/18*45)
        dimension_match = re.search(r'(\d+[\s]*[xX\*/][\s]*\d+(?:[\s]*[xX\*/][\s]*\d+)*)', notes)
        extracted_dim = dimension_match.group(1).replace(' ', '').lower() if dimension_match else ''
        final_dim = str(row_data.get('dimension', '')).strip() or extracted_dim

        # Yaygın renkleri tespit etme
        common_colors = ['beyaz', 'siyah', 'antrasit', 'gri', 'meşe', 'ceviz', 'krem', 'kırmızı', 'lake', 'safir', 'mat', 'parlak', 'ahşap']
        extracted_color = []
        for color in common_colors:
            if re.search(rf'\b{color}\b', notes, re.IGNORECASE):
                extracted_color.append(color.capitalize())
        
        final_variant = str(row_data.get('color', '')).strip()
        if not final_variant and extracted_color:
            final_variant = ', '.join(extracted_color)

        product_lines.append({
            'product_name': product_name,
            'model_code': model_code,
            'dimension': final_dim,
            'variant': final_variant,
            'blade_depth': blade_depth,
            'unit_type': 'adet',
            'quantity': quantity,
            'qty_produced': 0,
            'fire_qty': 0,
            'planning_mode': 'manual',
            'unit_duration_minutes': 0,
            'brief_intro': notes,
        })

    if not product_lines:
        raise ValueError('Geçerli veri satırı bulunamadı.')

    # Başlık oluşturmak için ilk geçerli satırdan seri ve sıra alalım
    first_row_idx = 1
    for idx, r in enumerate(rows[1:], start=1):
        if r and any(c for c in r):
            first_row_idx = idx
            break
            
    os_idx = next((i for i, f in header_map.items() if f == 'order_serial'), None)
    oseq_idx = next((i for i, f in header_map.items() if f == 'order_sequence'), None)
    pn_idx = next((i for i, f in header_map.items() if f == 'product_name'), None)
    
    order_serial = str(rows[first_row_idx][os_idx] or '').strip() if os_idx is not None and len(rows) > first_row_idx else ''
    order_sequence = str(rows[first_row_idx][oseq_idx] or '').strip() if oseq_idx is not None and len(rows) > first_row_idx else ''
    product_name_title = str(rows[first_row_idx][pn_idx] or '').strip() if pn_idx is not None and len(rows) > first_row_idx else ''
    
    reference = f"{order_serial}-{order_sequence}".strip('-')
    draft_title = reference or product_name_title or "Excel İçe Aktarma"
    wb.close()

    return {
        'success': True,
        'draft_title': draft_title,
        'draft_description': f"Excel'den içe aktarıldı. {len(product_lines)} kalem.",
        'product_lines': product_lines,
        'row_count': len(product_lines),
        'warnings': warnings,
    }
