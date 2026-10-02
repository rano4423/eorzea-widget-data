// Builds Data/almanac.json (bundled into the app) from FF14 Fish Tracker and FFXIV Teamcraft data, both MIT.
// Inputs are downloaded into ./cache by fetch.sh; see README.md.
//
//   node build.js
//
// Fish Tracker's data.js is a JavaScript file (`const DATA = {...}`), so it is evaluated in an isolated vm context
// with no access to require, process or the file system.
const fs = require('fs'), vm = require('vm'), path = require('path');
const CACHE = path.join(__dirname, 'cache');
// ALMANAC_OUT: output folder (the data repository's CI writes to its own root); defaults to the app's Data folder
const OUT = process.env.ALMANAC_OUT || path.join(__dirname, '..', '..', 'Data');
const read = f => fs.readFileSync(path.join(CACHE, f), 'utf8');
const J = f => JSON.parse(read(f));

const ctx = {};
vm.runInNewContext(read('data.js') + ';this.DATA=DATA;', ctx, { timeout: 5000 });
const D = ctx.DATA;
const legendFish = J('tc_legendary-fish.json'), nodes = J('tc_nodes.json'), items = J('tc_items.json'),
  places = J('tc_places.json'), maps = J('tc_maps.json');

// Weather keys follow Core/WeatherData.cs ("Clear Skies" -> clear_skies); names are the game's Japanese ones.
const wkey = id => D.WEATHER_TYPES[id].name_en.toLowerCase().replace(/ /g, '_');
const weathers = {};
const useW = id => { const k = wkey(id); weathers[k] = D.WEATHER_TYPES[id].name_ja; return k; };

// territory -> name, region and cumulative weather rates [[key, upTo], ...] out of 100
const terr = {};
const useT = tid => {
  const t = D.WEATHER_RATES[tid]; if (!t) return null;
  if (!terr[tid]) terr[tid] = { name: D.ZONES[t.zone_id]?.name_ja ?? '', region: D.REGIONS[t.region_id]?.name_ja ?? '',
    rates: t.weather_rates.map(([w, c]) => [useW(w), c]) };
  return tid;
};
// expansion index: 0 新生 (2.x) ... 5 黄金 (7.x)
const expOfPatch = p => Math.min(5, Math.max(0, Math.floor(p) - 2));
const TUG = { light: '!', medium: '!!', heavy: '!!!' }, HOOK = { Precision: 'プレシジョン', Powerful: 'パワフル' };
const name = id => D.ITEMS[id]?.name_ja ?? items[id]?.ja ?? `#${id}`;

const out = [];
// Spearfishing fish worth tracking: the ones that only appear after intuition (predators) or at certain times/weather.
const GIG = { Small: '小', Normal: '中', Large: '大', All: 'すべて' };
const spearSpecial = f => f.gig && (f.predators.length || f.weatherSet.length || f.previousWeatherSet.length || !(f.startHour === 0 && f.endHour === 24));
for (const f of Object.values(D.FISH)) {
  if (!f.bigFish && !spearSpecial(f)) continue;
  const spot = D.FISHING_SPOTS[f.location] ?? D.SPEARFISHING_SPOTS?.[f.location];
  if (!spot) continue;
  const tid = useT(spot.territory_id); if (tid == null) continue;
  const spear = !!f.gig && !f.bigFish;
  out.push({ id: 'f' + f._id, kind: spear ? 'spear' : legendFish[f._id] ? 'oonushi' : 'nushi', method: f.gig ? '刺突漁' : '釣り',
    gigSize: f.gig ? GIG[f.gig] ?? f.gig : '', exp: expOfPatch(f.patch), patch: f.patch,
    name: name(f._id), terr: +tid, spot: spot.name_ja, xy: spot.map_coords ? [+spot.map_coords[0].toFixed(1), +spot.map_coords[1].toFixed(1)] : null,
    prev: f.previousWeatherSet.map(useW), wx: f.weatherSet.map(useW), et: [[f.startHour, f.endHour]],
    bait: f.bestCatchPath.map(name), pred: f.predators.map(([id, n]) => [name(id), n]), intuition: f.intuitionLength,
    tug: TUG[f.tug] ?? '', hook: HOOK[f.hookset] ?? '', folklore: !!f.folklore, gig: !!f.gig, missing: !!f.dataMissing });
}

// Timed gathering points. Teamcraft marks every timed point "legendary"; the ones that need a folklore tome are
// 伝説 (legendary), the rest 未知 (unspoiled); "ephemeral" points are 刻限.
const JOB = { 0: '採掘師', 1: '採掘師', 2: '園芸師', 3: '園芸師' };
const METHOD = { 0: '採掘', 1: '砕岩', 2: '伐採', 3: '草刈' };
for (const [nid, n] of Object.entries(nodes)) {
  if (!n.limited) continue;
  const m = maps[n.map]; const zone = m ? places[m.placename_id]?.ja ?? '' : '';
  const its = n.items.filter(i => items[i]).map(i => items[i].ja).filter(s => !/クリスタル|シャード|クラスター/.test(s));
  const kind = n.ephemeral ? 'ephem' : n.folklore ? 'legend' : 'unspoiled';
  const dur = n.duration / 60; // Eorzea minutes -> hours
  out.push({ id: 'n' + nid, kind, exp: Math.min(5, Math.max(0, Math.floor(n.level / 10) - 5)), level: n.level,
    name: its[0] ?? '?', items: its, zone, spot: '', xy: [n.x, n.y], prev: [], wx: [],
    et: n.spawns.map(s => [s, (s + dur) % 24]), job: JOB[n.type] ?? '', method: METHOD[n.type] ?? '', folklore: !!n.folklore });
}

fs.mkdirSync(OUT, { recursive: true });
const meta = { generated: new Date().toISOString().slice(0, 10),
  sources: ['FF14 Fish Tracker (icykoneko/ff14-fish-tracker-app, MIT)', 'FFXIV Teamcraft (ffxiv-teamcraft/ffxiv-teamcraft, MIT)'] };
fs.writeFileSync(path.join(OUT, 'almanac.json'), JSON.stringify({ meta, weathers, terr, items: out }));
fs.writeFileSync(path.join(OUT, 'THIRD-PARTY-almanac.txt'),
  'ギャザラー図鑑のデータは次のプロジェクトのデータから作っています。\n' +
  'The almanac data is derived from the following projects.\n\n' +
  '=== FF14 Fish Tracker (https://github.com/icykoneko/ff14-fish-tracker-app) ===\n' + read('ft_license.txt').trim() + '\n\n' +
  '=== FFXIV Teamcraft (https://github.com/ffxiv-teamcraft/ffxiv-teamcraft) ===\n' + read('tc_license.txt').trim() + '\n');

const count = {}; out.forEach(o => count[o.kind] = (count[o.kind] || 0) + 1);
console.log(out.length, 'items', count, Object.keys(terr).length, 'territories',
  (fs.statSync(path.join(OUT, 'almanac.json')).size / 1024 | 0) + ' KB');
