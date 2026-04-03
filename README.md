# Docling Granite Layout Viewer

Containerized PDF layout viewer built with:

- Docling's VLM pipeline
- the `granite_docling` Hugging Face preset
- FastAPI for upload and conversion
- a Vite frontend using PDF.js to overlay detected regions

## What it does

Upload a PDF and the app will:

1. run Docling with the Granite-Docling VLM model on the backend
2. extract page provenance boxes from the resulting `DoclingDocument`
3. render the source PDF in the browser
4. overlay the detected layout regions directly on each page
5. show the exported Markdown and a label legend beside the viewer

## Run with Docker

```bash
docker compose up --build
```

Then open `http://localhost:8000`.

## Notes

- The first run will download the Granite-Docling model weights into the Docker volume mounted at `/root/.cache/huggingface`.
- This implementation currently accepts PDF uploads only, because the frontend viewer is intentionally centered on PDF page rendering plus layout overlays.
- Conversion is synchronous for now. Large PDFs will take noticeable time while the request is processed.

## Backend model configuration

The backend uses Docling's official preset-based VLM setup with the Hugging Face Transformers runtime:

```python
VlmConvertOptions.from_preset(
    "granite_docling",
    engine_options=TransformersVlmEngineOptions(),
)
```

This matches Docling's documented Granite-Docling VLM workflow for local Hugging Face inference.
