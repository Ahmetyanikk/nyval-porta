from datetime import datetime

def today_str_fr() -> str:
    return datetime.now().strftime("%d/%m/%Y")