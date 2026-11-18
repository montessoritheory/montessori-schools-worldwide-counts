"""Builds notebooks/starter.ipynb and executes it. Needs nbformat, nbclient, ipykernel, pandas, matplotlib."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent.parent
nb = nbf.v4.new_notebook()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb.cells = [
    md("# Montessori Schools Worldwide: Counts by Country, Region and City\n\n"
       "Starter notebook for the open dataset from [Montessori School Finder](https://www.montessorischoolfinder.com/), published by [Montessori Theory](https://www.montessori-theory.com/). "
       "The files hold aggregate counts only. Every row has a `msf_url` that opens the matching place page on Montessori School Finder.\n\n"
       "Read the counts as a directory snapshot, not as a census."),
    code("import pandas as pd\nimport matplotlib.pyplot as plt\n\n"
         "BASE = '../data'  # or 'https://raw.githubusercontent.com/montessoritheory/montessori-schools-worldwide-counts/main/data'\n"
         "country = pd.read_csv(f'{BASE}/by_country.csv')\n"
         "region = pd.read_csv(f'{BASE}/by_region.csv')\n"
         "city = pd.read_csv(f'{BASE}/by_city.csv')\n"
         "programs = pd.read_csv(f'{BASE}/programs_by_country.csv')\n"
         "print('Directory snapshot:', country.directory_date.iloc[0])\n"
         "country.head()"),
    md("## Do the Levels Add Up?\n\nCities add up to regions add up to countries add up to the directory total."),
    code("print(country.schools.sum(), region.schools.sum(), city.schools.sum())\n"
         "assert country.schools.sum() == region.schools.sum() == city.schools.sum()"),
    md("## Where Are the Listed Schools?"),
    code("top = country.sort_values('schools', ascending=False).head(10)\n"
         "ax = top.set_index('country').schools.iloc[::-1].plot.barh(color='#2563eb', figsize=(8, 4.5))\n"
         "ax.set_xlabel('Schools in the directory'); ax.set_ylabel('')\n"
         "ax.set_title('Top 10 countries by listed Montessori schools')\n"
         "plt.tight_layout(); plt.show()\n"
         "print(f'Top 5 countries hold {country.schools.head(5).sum() / country.schools.sum():.0%} of the directory')"),
    md("## How Concentrated Are Cities?"),
    code("print('Cities with a page:', len(city))\n"
         "print('Cities with a single school:', (city.schools == 1).sum(), f'({(city.schools == 1).mean():.0%})')\n"
         "print('Cities with 10 or more schools:', (city.schools >= 10).sum())\n"
         "city.sort_values('schools', ascending=False).head(10)[['city', 'country', 'schools', 'msf_url']]"),
    md("## Verified Share by Country\n\nA school is counted as verified when an official record or the school's own website confirms it is Montessori. "
       "The share is left blank for countries with fewer than 10 schools."),
    code("v = country.dropna(subset=['verified_share_pct']).query('schools >= 100').sort_values('verified_share_pct')\n"
         "ax = v.set_index('country').verified_share_pct.plot.barh(color='#059669', figsize=(8, 5))\n"
         "ax.set_xlabel('Verified share of listed schools (%)'); ax.set_ylabel('')\n"
         "ax.set_title('Verified share, countries with 100 or more schools')\n"
         "plt.tight_layout(); plt.show()"),
    md("## Programs by Country\n\nOne school can list several programs, so program columns do not add up to `schools`."),
    code("cols = ['infant', 'toddler', 'daycare', 'preschool', 'kindergarten', 'elementary', 'middle_school', 'high_school', 'no_program_listed']\n"
         "world = programs[programs.country_code == 'ALL'].iloc[0]\n"
         "(world[cols] / world.schools * 100).round(1).sort_values(ascending=False)"),
    md("## Find a Place Page\n\nEach row links to its page on Montessori School Finder."),
    code("city[(city.country == 'Ireland') & (city.region == 'Dublin')][['city', 'schools', 'msf_url']].head()"),
    md("## Citation\n\nMontessori School Finder and Montessori Theory (2026). *Montessori Schools Worldwide: Counts by Country, Region and City*. CC BY 4.0. "
       "https://www.montessorischoolfinder.com/"),
]
nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
out = ROOT / "notebooks" / "starter.ipynb"
NotebookClient(nb, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(out.parent)}}).execute()
nbf.write(nb, out)
print("executed", out)
