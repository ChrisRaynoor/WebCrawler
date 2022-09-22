import xlwings as xw
import os

origin_xl_path = "data/result_all_hs.xlsx"
processed_xl_path = "data/result_all_hs_filtered.xlsx"

with xw.App(visible=False,add_book=False) as app:
    if not os.path.exists(origin_xl_path):
        raise ValueError("invalid path")
    wb = app.books.open(origin_xl_path)
    sht = wb.sheets[0]
    used_range = sht.used_range
    last_row = used_range.last_cell.row
    # traverse
    for r in reversed(range(1, last_row+1)):
        vs = sht.range(f"G{r}:H{r}").value
        if vs[0] is None and vs[1] is None:
            sht.range(f"A{r}").api.EntireRow.Delete()
        if r%50==0:
            wb.save(processed_xl_path)
    
    # delete duplication
    used_range = sht.used_range
    last_row = used_range.last_cell.row
    print(f"last_row{last_row}")
    total_row = last_row
    seen = set()
    for r in reversed(range(1, last_row+1)):
        id = sht.range(f"B{r}").value
        if id in seen:
            sht.range(f"A{r}").api.EntireRow.Delete()
        else:
            seen.add(id)
        if r%50==0:
            wb.save(processed_xl_path)
    wb.save(processed_xl_path)