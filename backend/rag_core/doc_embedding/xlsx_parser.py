from pathlib import Path
import pandas as pd

def excel_parse(path, max_len=2000):
    """
    Reads an .xlsx workbook and returns a list of text chunks for RAG.

    Each sheet is split into chunks of roughly `max_len` characters.
    Each row inside a chunk is represented as comma-separated values
    (e.g., 'ethanol, primary, final') for clean parsing and embedding.

    Returns
    -------
    chunks : list of str
        Each string represents one chunk containing the sheet name,
        header, and the text rows.
    """

    if not path.lower().endswith(".xlsx"):
        raise ValueError(f"Unsupported file type: {path}")

    xls = pd.ExcelFile(path)
    chunks = []

    for sheet_name in xls.sheet_names:
        df = xls.parse(sheet_name)
        df = df.fillna("")  # Prevent NaN showing as 'nan'
        header = df.columns.tolist()

        # Initialize chunk state
        current_rows, current_len = [], 0

        for _, row in df.iterrows():
            # Convert row to comma-separated text
            row_text = ", ".join(map(str, row.tolist()))
            row_len = len(row_text)

            # If adding this row would exceed limit → save current chunk
            if current_len + row_len > max_len and current_rows:
                chunk_text = "\n".join(current_rows)
                chunks.append(f"Sheet: {sheet_name}\nHeader: {', '.join(header)}\n {chunk_text}")
                current_rows = [row_text]
                current_len = row_len
            else:
                current_rows.append(row_text)
                current_len += row_len

        # Add remaining rows
        if current_rows:
            chunk_text = "\n".join(current_rows)
            chunks.append(f"Sheet: {sheet_name}\nHeader: {', '.join(header)}\n{chunk_text}")

    file_name = Path(path).parts[-1]
    print(f"✅ Created {len(chunks)} text chunks from workbook '{file_name}'")
    return chunks
