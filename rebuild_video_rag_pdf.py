
import json
from generate_pdfs import generate_pdf

if __name__ == "__main__":
    # Load project data from the new JSON file (GitHub-based content)
    with open("video_rag_pdf_data.json") as f:
        project = json.load(f)
    # Prepare source_items from walkthrough
    source_items = [(item.get("kind", "body"), item.get("text", "")) for item in project["walkthrough"]]
    # Output path
    out_path = project["pdf"]
    # Generate the PDF using the standard function
    generate_pdf(project, source_items, out_path)
