from xhtml2pdf import pisa
from pypdf import PdfWriter, PdfReader
import matplotlib.backends.backend_pdf as mpdf
import markdown
import os



def _append_figures_to_pdf(figures, existing_pdf_path):
    """Appends matplotlib figures as extra pages to an existing PDF."""
    # Save figures to a temp PDF
    temp_figs_path = existing_pdf_path.replace(".pdf", "_figs_temp.pdf")
    with mpdf.PdfPages(temp_figs_path) as pdf:
        for fig in figures:
            pdf.savefig(fig, bbox_inches='tight')

    # Merge narrative PDF + figures PDF
    writer = PdfWriter()
    for path in [existing_pdf_path, temp_figs_path]:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    with open(existing_pdf_path, "wb") as f:
        writer.write(f)

    # Clean up temp file
    os.remove(temp_figs_path)


def build_pdf_report(analysis_narrative, figures, output_path):
    try:
        # Convert markdown narrative to HTML
        narrative_html = markdown.markdown(analysis_narrative)
        
        # Wrap in basic styled HTML
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Helvetica; font-size: 11pt; margin: 40px; line-height: 1.6; }}
                h1, h2 {{ font-size: 14pt; }}
                h3, h4 {{ font-size: 12pt; }}
                li {{ margin-bottom: 4px; }}
            </style>
        </head>
        <body>
            {narrative_html}
        </body>
        </html>
        """
        
        # Render narrative to PDF
        with open(output_path, "wb") as f:
            pisa.CreatePDF(html, dest=f)
        
        # Append figures as additional pages
        # xhtml2pdf can't append matplotlib figs directly, so we use PdfPages to merge
        if figures:
            _append_figures_to_pdf(figures, output_path)
    except Exception as e:
        print(f"Error generating Analysis PDF report: {e}")


