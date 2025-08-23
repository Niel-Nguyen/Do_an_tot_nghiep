#ce_text_builder.py
def _nz(v): return (v or "").strip()

def price_bucket(v):
    try: x=float(str(v).replace(',','.'))
    except: return ""
    return "rẻ" if x<=40000 else ("trung" if x<=80000 else "nhỉnh")

def time_bucket(v):
    try: m=int(float(str(v).replace(',','.')))
    except: return ""
    return "nhanh" if m<=20 else ("trung" if m<=40 else "bận")

def clip(s,n): return (s or "").replace("\n"," ").strip()[:n]

def ce_text_for_dish(d):
    region=_nz(getattr(d,"region",""))
    mood=_nz(getattr(d,"mood",""))
    typ=_nz(getattr(d,"dish_type","") or getattr(d,"type",""))
    veg=_nz(getattr(d,"meal_category",""))
    texture=_nz(getattr(d,"texture",""))
    p_bucket=price_bucket(getattr(d,"price",""))
    t_bucket=time_bucket(getattr(d,"cook_time",""))
    desc=clip(_nz(getattr(d,"description","")),160)

    tags="".join([
        f"[Region: {region or 'unknown'}]",
        f"[Mood: {mood or 'unknown'}]",
        f"[Type: {typ or 'unknown'}]",
        f"[Veg: {veg or 'unknown'}]",
        f"[Texture: {texture or 'unknown'}]",
        f"[PriceBucket: {p_bucket or 'unknown'}]",
        f"[TimeBucket: {t_bucket or 'unknown'}]",
    ])
    body = f"Mô tả: {desc}." if desc else ""
    return (tags+"\n"+f"Món ăn: {d.name}"+("\n"+body if body else "")).strip()
