from __future__ import annotations

from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.datamodel.vlm_engine_options import TransformersVlmEngineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline


def _extract_item_text(item: Any, document: Any) -> str:
    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    caption_text = getattr(item, "caption_text", None)
    if callable(caption_text):
        try:
            value = caption_text(document)
        except Exception:
            value = None
        if isinstance(value, str) and value.strip():
            return value.strip()

    name = getattr(item, "name", None)
    if isinstance(name, str) and name.strip():
        return name.strip()

    return ""


@lru_cache(maxsize=1)
def get_converter() -> DocumentConverter:
    pipeline_options = VlmPipelineOptions(
        vlm_options=VlmConvertOptions.from_preset(
            "granite_docling",
            engine_options=TransformersVlmEngineOptions(),
        ),
        generate_page_images=False,
    )

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline,
                pipeline_options=pipeline_options,
            )
        }
    )


def convert_pdf(source_path: Path) -> dict[str, Any]:
    result = get_converter().convert(source=source_path)
    document = result.document

    pages: dict[int, dict[str, Any]] = {}
    for page_no, page in sorted(document.pages.items()):
        pages[page_no] = {
            "pageNo": page_no,
            "width": page.size.width,
            "height": page.size.height,
            "items": [],
        }

    label_counts: Counter[str] = Counter()
    total_items = 0

    for item, level in document.iterate_items():
        label = getattr(item, "label", None)
        if label is None:
            continue

        label_value = getattr(label, "value", str(label))
        item_text = _extract_item_text(item, document)
        prov_items = getattr(item, "prov", None) or []

        for prov_index, prov in enumerate(prov_items):
            page = pages.get(prov.page_no)
            if page is None:
                continue

            bbox = prov.bbox.to_top_left_origin(page["height"])
            left, top, right, bottom = bbox.as_tuple()

            page["items"].append(
                {
                    "id": f"{item.self_ref}:{prov_index}",
                    "label": label_value,
                    "level": level,
                    "text": item_text,
                    "bbox": {
                        "left": left,
                        "top": top,
                        "width": max(0.0, right - left),
                        "height": max(0.0, bottom - top),
                    },
                }
            )
            label_counts[label_value] += 1
            total_items += 1

    for page in pages.values():
        page["items"].sort(
            key=lambda item: (
                item["bbox"]["top"],
                item["bbox"]["left"],
                -(item["bbox"]["width"] * item["bbox"]["height"]),
            )
        )

    return {
        "markdown": document.export_to_markdown(),
        "pages": list(pages.values()),
        "summary": {
            "pageCount": len(pages),
            "itemCount": total_items,
            "labels": dict(sorted(label_counts.items())),
        },
    }

