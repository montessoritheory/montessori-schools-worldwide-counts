"""Builds ../huggingface/README.md and ../kaggle/dataset-metadata.json from README.md and data_dictionary.csv."""
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO.parent
GH = "https://raw.githubusercontent.com/montessoritheory/montessori-schools-worldwide-counts/main/"
HF = "https://huggingface.co/datasets/montessoritheory/montessori-schools-worldwide-counts/resolve/main/"
readme = (REPO / "README.md").read_text(encoding="utf8")

yaml = """---
license: cc-by-4.0
pretty_name: "Montessori Schools Worldwide: Counts by Country, Region and City"
language:
- en
tags:
- montessori
- education
- schools
- early-childhood
- directory
- counts
- tabular
size_categories:
- 1K<n<10K
source_datasets:
- original
configs:
- config_name: by_country
  data_files: data/by_country.csv
  default: true
- config_name: by_region
  data_files: data/by_region.csv
- config_name: by_city
  data_files: data/by_city.csv
- config_name: programs_by_country
  data_files: data/programs_by_country.csv
- config_name: us_public_private_split
  data_files: data/us_public_private_split.csv
- config_name: summary
  data_files: data/summary.csv
---

"""
hf = readme.replace("](images/", f"]({HF}images/")
hf = hf.replace("Load It\n\n```python", "Load It\n\n```python\n# or: from datasets import load_dataset; load_dataset(\"montessoritheory/montessori-schools-worldwide-counts\", \"by_country\")")
(PKG / "huggingface").mkdir(exist_ok=True)
(PKG / "huggingface" / "README.md").write_text(yaml + hf, encoding="utf8")

dd = list(csv.DictReader((REPO / "data_dictionary.csv").open(encoding="utf8")))
file_desc = {
    "by_country.csv": "37 rows, one per country or UK nation in the directory, with schools, cities, regions, verified count and share, and the page address.",
    "by_region.csv": "346 rows, one per region (state, county, province) with at least one school.",
    "by_city.csv": "6,018 rows, one per city with at least one school.",
    "programs_by_country.csv": "Program level counts by country. Countries with fewer than 10 schools are combined in one OTHER row, ALL is the world total.",
    "us_public_private_split.csv": "US schools split into public charter, public district and other.",
    "summary.csv": "Headline figures and the sum checks.",
}
tmap = {"str": "string", "integer": "integer", "number": "number", "date": "string"}
resources = []
for f, d in file_desc.items():
    resources.append({"path": f, "description": d, "schema": {"fields": [
        {"name": r["column"], "description": r["description"], "type": tmap[r["type"]]} for r in dd if r["file"] == f]}})
kaggle_desc = readme.replace("](images/", f"]({GH}images/").split("\n---\n\n## Version")[0]
meta = {
    "title": "Montessori Schools Worldwide: Counts by Country, Region and City",
    "subtitle": "Aggregate counts of the Montessori School Finder directory, no school records",
    "id": "mariamontessori/montessori-schools-worldwide-counts",
    "licenses": [{"name": "CC-BY-4.0"}],
    "keywords": ["education", "primary and secondary schools", "geography", "tabular", "early childhood"],
    "description": kaggle_desc,
    "resources": resources,
}
(PKG / "kaggle").mkdir(exist_ok=True)
(PKG / "kaggle" / "dataset-metadata.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf8")
print("ok", len(resources))
