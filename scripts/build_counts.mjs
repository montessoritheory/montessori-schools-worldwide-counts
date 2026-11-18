// Rebuilds data/*.csv from the Montessori School Finder publish database.
// Usage: node build_counts.mjs [path/to/msf.sqlite] [output dir]
// Node 24+, node:sqlite only, database opened read-only. Aggregate counts only.
import { DatabaseSync } from 'node:sqlite';
import { mkdirSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const dbPath = process.argv[2] ?? process.env.MSF_DB ?? path.resolve(here, '../../../../data/msf.sqlite');
const outDir = process.argv[3] ?? path.resolve(here, '../data');
const SITE = 'https://www.montessorischoolfinder.com';
const MIN_CELL = 10; // verified and program cells are blank for countries with fewer schools
mkdirSync(outDir, { recursive: true });

const db = new DatabaseSync(dbPath, { readOnly: true });
const all = (sql) => db.prepare(sql).all();
const meta = Object.fromEntries(all('SELECT key, value FROM meta').map((r) => [r.key, r.value]));
const maxLastmod = all('SELECT MAX(lastmod) AS d FROM countries')[0].d;
const g = meta.google_data_to ? `${meta.google_data_to}-01`.slice(0, 10) : '';
// Same logic as directoryDataDate() on the site.
const directoryDate = [maxLastmod, g].reduce((m, d) => (d > m ? d : m), '') || meta.built_at.slice(0, 10);

const csvCell = (v) => (v === null || v === undefined ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replaceAll('"', '""')}"` : String(v));
const writeCsv = (name, cols, rows) => {
  const text = [cols.join(','), ...rows.map((r) => cols.map((c) => csvCell(r[c])).join(','))].join('\n') + '\n';
  writeFileSync(path.join(outDir, name), text, 'utf8');
  console.log(`${name}: ${rows.length} rows`);
};
const total = all('SELECT COUNT(*) AS n FROM schools')[0].n;

// by_country
const countries = all(`
  SELECT c.code, c.iso2, c.name, c.path,
         COUNT(s.id) AS schools,
         COUNT(DISTINCT s.city_geonameid) AS cities_with_schools,
         COUNT(DISTINCT s.region_code) AS regions_with_schools,
         SUM(s.status = 'verified') AS verified
  FROM countries c JOIN schools s ON s.country_code = c.code
  GROUP BY c.code ORDER BY schools DESC, c.name`);
writeCsv('by_country.csv',
  ['country_code', 'iso2', 'country', 'schools', 'share_of_directory_pct', 'cities_with_schools', 'regions_with_schools', 'verified_schools', 'verified_share_pct', 'msf_url', 'directory_date'],
  countries.map((c) => ({
    country_code: c.code, iso2: c.iso2, country: c.name, schools: c.schools,
    share_of_directory_pct: (100 * c.schools / total).toFixed(2),
    cities_with_schools: c.cities_with_schools, regions_with_schools: c.regions_with_schools,
    verified_schools: c.schools >= MIN_CELL ? c.verified : '',
    verified_share_pct: c.schools >= MIN_CELL ? (100 * c.verified / c.schools).toFixed(1) : '',
    msf_url: SITE + c.path, directory_date: directoryDate,
  })));

// by_region
const regions = all(`
  SELECT c.code AS ccode, c.name AS country, r.code AS rcode, r.name AS region, r.path,
         COUNT(s.id) AS schools, COUNT(DISTINCT s.city_geonameid) AS cities
  FROM regions r JOIN countries c ON c.code = r.country_code
  JOIN schools s ON s.country_code = r.country_code AND s.region_code = r.code
  GROUP BY r.country_code, r.code ORDER BY c.name, schools DESC, r.name`);
writeCsv('by_region.csv', ['country_code', 'country', 'region_code', 'region', 'schools', 'cities_with_schools', 'msf_url', 'directory_date'],
  regions.map((r) => ({ country_code: r.ccode, country: r.country, region_code: r.rcode, region: r.region, schools: r.schools, cities_with_schools: r.cities, msf_url: SITE + r.path, directory_date: directoryDate })));

// by_city
const cities = all(`
  SELECT c.code AS ccode, c.name AS country, r.name AS region, ci.geonameid, ci.name AS city, ci.path,
         COUNT(s.id) AS schools
  FROM cities ci JOIN schools s ON s.city_geonameid = ci.geonameid
  JOIN countries c ON c.code = ci.country_code
  JOIN regions r ON r.country_code = ci.country_code AND r.code = ci.region_code
  GROUP BY ci.geonameid ORDER BY c.name, r.name, schools DESC, ci.name`);
writeCsv('by_city.csv', ['country_code', 'country', 'region', 'city', 'geonames_id', 'schools', 'msf_url', 'directory_date'],
  cities.map((c) => ({ country_code: c.ccode, country: c.country, region: c.region, city: c.city, geonames_id: c.geonameid, schools: c.schools, msf_url: SITE + c.path, directory_date: directoryDate })));

// programs by country (multi-label: one school can offer several programs)
const PROGS = ['Infant', 'Toddler', 'Daycare', 'Preschool', 'Kindergarten', 'Elementary', 'Middle School', 'High School'];
const key = (p) => p.toLowerCase().replace(' ', '_');
const blank = () => ({ schools: 0, none: 0, ...Object.fromEntries(PROGS.map((p) => [key(p), 0])) });
const agg = new Map();
const bump = (code, progs) => {
  const a = agg.get(code) ?? blank();
  a.schools++;
  if (!progs.length) a.none++;
  for (const p of progs) if (PROGS.includes(p)) a[key(p)]++;
  agg.set(code, a);
};
for (const r of all('SELECT country_code, programs FROM schools')) {
  const p = JSON.parse(r.programs);
  bump(r.country_code, p);
  bump('ALL', p);
}
const nameOf = new Map(countries.map((c) => [c.code, c.name]));
const progCols = ['country_code', 'country', 'schools', ...PROGS.map(key), 'no_program_listed', 'directory_date'];
const toRow = (code, label, a) => ({ country_code: code, country: label, schools: a.schools, ...Object.fromEntries(PROGS.map((p) => [key(p), a[key(p)]])), no_program_listed: a.none, directory_date: directoryDate });
const progRows = [];
const other = blank();
for (const [code, a] of [...agg.entries()].sort((x, y) => y[1].schools - x[1].schools)) {
  if (code === 'ALL') continue;
  if (a.schools < MIN_CELL) { for (const k of Object.keys(other)) other[k] += a[k]; continue; }
  progRows.push(toRow(code, nameOf.get(code), a));
}
progRows.push(toRow('OTHER', `Countries with fewer than ${MIN_CELL} schools, combined`, other));
progRows.push(toRow('ALL', 'All countries', agg.get('ALL')));
writeCsv('programs_by_country.csv', progCols, progRows);

// US public vs other
const us = all("SELECT COUNT(*) AS n, SUM(public_type='charter') AS charter, SUM(public_type='district') AS district FROM schools WHERE country_code='US'")[0];
writeCsv('us_public_private_split.csv', ['country_code', 'schools', 'public_charter', 'public_district', 'private_or_not_classified', 'directory_date'],
  [{ country_code: 'US', schools: us.n, public_charter: us.charter, public_district: us.district, private_or_not_classified: us.n - us.charter - us.district, directory_date: directoryDate }]);

// summary + integrity checks
const sum = (a, k) => a.reduce((s, r) => s + r[k], 0);
const checks = {
  directory_date: directoryDate, total_schools: total, countries: countries.length, regions: regions.length, cities: cities.length,
  verified_schools: sum(countries, 'verified'),
  sum_countries: sum(countries, 'schools'), sum_regions: sum(regions, 'schools'), sum_cities: sum(cities, 'schools'),
};
if (!(checks.sum_countries === total && checks.sum_regions === total && checks.sum_cities === total)) throw new Error('Totals do not add up: ' + JSON.stringify(checks));
writeCsv('summary.csv', ['metric', 'value'], Object.entries(checks).map(([metric, value]) => ({ metric, value })));
console.log(checks);
