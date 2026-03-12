from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

pdf_path = 'assets/projects/video-rag-retrieval-project.pdf'
text_path = 'video_rag_text_noquotes.txt'

c = canvas.Canvas(pdf_path, pagesize=letter)
width, height = letter

with open(text_path) as f:
    lines = f.readlines()


# Helper to clean and format lines
def clean_line(line):
    # Remove unwanted double quotes and smart quotes
    line = line.replace('"', '').replace('“', '').replace('”', '').replace("'", "")
    return line.strip()

y = height - 40
for idx, line in enumerate(lines):
    line = clean_line(line)
    # Center the title (first line)
    if idx == 0:
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, y, line)
        y -= 30
        c.setFont("Helvetica", 12)
        continue
    # Add extra space before section headers
    if line.isupper() and len(line) < 30:
        y -= 15
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, line)
        c.setFont("Helvetica", 12)
        y -= 20
        continue
    # Regular lines
    c.drawString(40, y, line)
    y -= 15
    if y < 40:
        c.showPage()
        y = height - 40
c.save()
