
import json
from generate_pdfs import generate_pdf

if __name__ == "__main__":
    # Load project data from projects.json
    with open("projects.json") as f:
        projects = json.load(f)
    # Find the Video RAG Retrieval Project entry
    project = next(p for p in projects if p["title"] == "Video RAG Retrieval Project")
    # If walkthrough is not present, try to load from text file as fallback
    source_items = []
    if "walkthrough" in project:
        for item in project["walkthrough"]:
            kind = item.get("kind", "body")
            text = item.get("text", "")
            source_items.append((kind, text))
    else:
        # fallback: use lines from text file as body
        with open("video_rag_text_noquotes.txt") as f:
            for line in f:
                line = line.strip()
                if line:
                    source_items.append(("body", line))
    # Output path
    out_path = project["pdf"]
    # Generate the PDF using the standard function
    generate_pdf(project, source_items, out_path)
