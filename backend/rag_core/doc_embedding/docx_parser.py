from docx import Document as DocReader
from pathlib import Path
import re

def read_docx_file(path):
    if path.lower().endswith(".docx"):
        src = DocReader(path)
        return "\n".join(p.text for p in src.paragraphs)
    else:
        raise ValueError(f"Unsupported file type")


def is_divider(line):
    stripped = line.strip()
    # Skip short or empty line
    if not stripped or len(stripped) < 3:
        return True

    # If it’s made of mostly non-alphanumeric chars like **** or ----
    if re.fullmatch(r"[^a-zA-Z0-9]{3,}", stripped):
        return True
    return False

def split_headings(raw_text):
    chunked_text = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue  # skip empty lines
        if is_divider(line):
            continue  # skip divider lines
        elif ("* .. _section_" in line) or ("* .. _param" in line):         # section heading patterns in .gms files
            heading_line = line.replace("* .. _", "")
            chunked_text.append(f"heading: {heading_line}")  
        else:
            chunked_text.append(line)
    return chunked_text

def split_into_sections(chunked_text):
    # Now split into chunks based on "heading:" lines
    sections = []
    for line in chunked_text:
        if line.startswith("heading: "):
            sections.append([])  # start a new chunk
        if sections:
            sections[-1].append(line)  # add line to the current chunk
    return sections

def split_section_into_chunks(sections, max_len=800):
    chunks = []
    for section in sections:
        if not section:
            continue

        heading = section[0]
        sentences = "\n".join(section[1:]).split("\n")

        current, current_len = [], 0
        section_chunks = []  # chunks for this single section

        for s in sentences:
            s = s.strip()
            if not s:
                continue
            # if adding this sentence exceeds limit → start new chunk
            if current_len + len(s) > max_len:
                section_chunks.append([heading, "\n".join(current)])
                current = [s]
                current_len = len(s)
            else:
                current.append(s)
                current_len += len(s)

        # append any remainder
        if current:
            section_chunks.append([heading, "\n".join(current)])

      #  print(f"{len(section_chunks)} chunks created for {heading}")
        chunks.extend(section_chunks)
    return chunks


def docx_parse(input_file_path, max_len):
    '''
    Reads a .docx file and returns a list of text chunks for RAG.

    read_docx_file: read the input file
    split_into_sections: split the raw text into section based on "heading:" lines, removing junk and dividers
    split_section_into_chunks: split each section into ~1000 (or max_length) character chunks, but only at newline boundaries
    '''
    
    raw_text = read_docx_file(input_file_path)
    #print(raw_text)
    chunked_text = split_headings(raw_text)
    sections = split_into_sections(chunked_text)
    chunks = split_section_into_chunks(sections, max_len)
    return chunks