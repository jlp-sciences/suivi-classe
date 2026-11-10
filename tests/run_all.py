#!/usr/bin/env python3
"""Tests de non-régression de Suivi de classe.
   Usage : python3 tests/run_all.py   (depuis la racine du dépôt ; nécessite playwright + chromium)
   1. lance les vérifications intégrées (runSelfTests, dans index.html) ;
   2. vérifie l'affichage de la vue semaine (rien ne déborde ni ne se chevauche) sur 4 tailles d'écran ;
   3. parcourt les écrans principaux et s'assure qu'aucune erreur JavaScript n'apparaît ;
   4. vérifie que la position de défilement est gardée lors d'une mise à jour automatique ;
   5. importe un export Excel « Les devoirs » d'École Directe fabriqué (élèves fictifs) et compare les moyennes."""
import asyncio, http.server, socketserver, threading, functools, os, sys, tempfile
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8799
OVERLAP = """[...document.querySelectorAll('.blk')].filter(b => { const R = b.getBoundingClientRect(); const kids = [...b.children].filter(k => !k.classList.contains('bdots')).map(k => k.getBoundingClientRect());
  for (let i = 0; i < kids.length; i++) { if (kids[i].bottom > R.bottom + 0.5 || kids[i].top < R.top - 0.5 || kids[i].right > R.right + 0.5) return true; if (i && kids[i].top < kids[i-1].bottom - 0.5) return true; }
  const d = b.querySelector('.bdots'); if (d) { const dr = d.getBoundingClientRect(); if (dr.right > R.right + 0.5 || dr.bottom > R.bottom + 0.5) return true; for (const t of b.querySelectorAll('.bil, .bty, .bc, .bmore, .bnote')) { const tr = t.getBoundingClientRect(); const box = t.closest('.bit, .btop'); const vis = Math.min(tr.right, box.getBoundingClientRect().right - parseFloat(getComputedStyle(box).paddingRight)); if (tr.bottom > dr.top + 1 && tr.top < dr.bottom - 1 && vis > dr.left + 1) return true; } }
  return [...b.querySelectorAll('.bit')].some(x => x.getBoundingClientRect().height < 15.5) || [...b.querySelectorAll('.bits')].some(x => x.scrollHeight > x.clientHeight + 1); }).map(b => b.getAttribute('aria-label') + ' h=' + b.clientHeight + ' w=' + b.clientWidth)"""

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    h = functools.partial(Quiet, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(('127.0.0.1', PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

FAILS = []
def check(cond, msg):
    print(('  ok   ' if cond else '  ÉCHEC ') + msg)
    if not cond: FAILS.append(msg)

async def page(b, w, h, errs):
    pg = await (await b.new_context(viewport={'width': w, 'height': h}, locale='fr-FR', timezone_id='Europe/Paris')).new_page()
    pg.on('pageerror', lambda e: errs.append(f'{w}x{h}: {e}'))
    await pg.goto(f'http://127.0.0.1:{PORT}/index.html'); await pg.wait_for_timeout(300)
    await pg.click('text=Essayer avec des élèves fictifs'); await pg.wait_for_timeout(300)
    await pg.evaluate("DB.settings.lastBackup = todayStr(); save(); document.getElementById('toast').hidden = true")
    return pg

async def main():
    serve(); errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        print('1. Vérifications intégrées')
        pg = await page(b, 1280, 860, errs)
        r = await pg.evaluate("runSelfTests().then(r => ({n: r.n, fail: r.fail.map(x => x.g + ' | ' + x.msg)}))")
        check(not r['fail'], f"{r['n']} vérifications intégrées" + ('' if not r['fail'] else ' : ' + ' ; '.join(r['fail'])))
        await pg.close()

        print('2. Vue semaine : rien ne déborde')
        for (w, h) in [(1280, 800), (1024, 768), (1920, 1080), (800, 1280)]:
            pg = await page(b, w, h, errs)
            if await pg.evaluate("isNarrow()"): await pg.close(); continue
            weeks = await pg.evaluate("""(() => { const out = [], yb = yearBounds(); for (let m = mondayOf(yb.s); m <= yb.e && out.length < 6; m = addDays(m, 7)) if (slotsOn(addDays(m, 1)).length) out.push(m); return out; })()""")
            # contenu fictif de longueurs variées, créneaux de 30 min, 2 h et cours en parallèle
            await pg.evaluate("""(() => { const c = DB.classes[0];
              DB.slots.push({id:'z1', day: 3, start:'12:00', end:'12:30', cid: c.id, group:'all', week:'all'});
              DB.slots.push({id:'z2', day: 4, start:'11:00', end:'13:00', cid: DB.classes[1].id, group:'G1', week:'all'});
              DB.slots.push({id:'z3', day: 4, start:'11:30', end:'12:30', cid: DB.classes[2].id, group:'G2', week:'all'});
              DB.slots.push({id:'z4', day: 2, start:'16:00', end:'17:00', cid: c.id, group:'all', week:'all', vdc: true});
              SESS_CACHE = {}; const T = ['tp','act','exo','cours','corr','eval','autre']; let n = 0; const yb = yearBounds();
              for (let d = yb.s; d <= yb.e; d = addDays(d, 1)) slotsOn(d).forEach(x => { n++; const k = d + '|' + x.id, m = n % 6;
                DB.content[k] = {ch: n % 3 ? 2 : null, items: Array.from({length: m}, (_, j) => ({id: 'i'+n+'_'+j, type: T[(n+j) % 7], label: j % 2 ? '' : 'Intitulé très long numéro ' + j + ' pour tester la coupure', st: 'prev', graded: j === 1})), hw: [], ready: n % 4 === 0, ...(x.vdc ? {note: 'Préparation vie de classe'} : {})};
                if (n % 7 === 0) DB.cancelled[k] = true; if (n % 5 === 0) DB.cdt[k] = true; });
              SESS_CACHE = {}; })()""")
            bad = []
            for m in weeks:
                await pg.evaluate(f"STACK = []; V = homeV(); V.tab = 'edt'; V.mode = 'week'; V.date = '{m}'; WEEK_FIX_KEY = ''; render()"); await pg.wait_for_timeout(150)
                bad += await pg.evaluate(OVERLAP)
            check(not bad, f'{w}x{h} : {len(weeks)} semaines sans débordement' + ('' if not bad else ' : ' + ', '.join(bad[:4])))
            await pg.close()

        print('3. Parcours des écrans')
        for (w, h) in [(1280, 860), (390, 844)]:
            pg = await page(b, w, h, errs)
            for t in ['edt', 'suivi', 'prog', 'salles']:
                await pg.evaluate(f"document.querySelector('[data-act=htab][data-t={t}]').click()"); await pg.wait_for_timeout(120)
            await pg.evaluate("""(() => { const c = DB.classes[0], s = classSessions(c.id).find(x => !x.cancelled && x.date >= todayStr()) || classSessions(c.id)[0]; openSession({...s, cid: c.id}); })()"""); await pg.wait_for_timeout(150)
            for s in ['contenu', 'devoirs', 'bilan']:
                await pg.evaluate(f"V.stab = '{s}'; render()"); await pg.wait_for_timeout(100)
            await pg.evaluate("V.stab = 'contenu'; render(); openContent(V.ses)"); await pg.wait_for_timeout(150)
            check(await pg.locator('#ct-t').count() == 1, f'{w}x{h} : éditeur de contenu ouvert')
            await pg.evaluate("closeLayer(); CT = null; go({name: 'settings', tab: 'classes'})"); await pg.wait_for_timeout(100)
            for t in ['edt', 'periodes', 'etiquettes', 'sauvegarde', 'sync']:
                await pg.evaluate(f"V.tab = '{t}'; render()"); await pg.wait_for_timeout(80)
            await pg.evaluate("go({name: 'bul', cid: DB.classes[0].id, p: 0})"); await pg.wait_for_timeout(100)
            check(await pg.locator('.bullist li').count() > 0, f'{w}x{h} : page Appréciations')
            await pg.evaluate("go({name: 'notes', cid: DB.classes[0].id, p: 0})"); await pg.wait_for_timeout(100)
            check(await pg.locator('#gimp-in').count() == 1, f'{w}x{h} : page Notes')
            await pg.close()

        print('4. Position gardée lors des mises à jour automatiques')
        for (w, h) in [(1280, 800), (390, 844)]:
            pg = await page(b, w, h, errs)
            for t in ['suivi', 'prog']:
                await pg.evaluate(f"document.querySelector('[data-act=htab][data-t={t}]').click(); V.pAll = true; render()"); await pg.wait_for_timeout(200)
                await pg.evaluate("$('.main').scrollTop = 400"); await pg.wait_for_timeout(1400)
                await pg.evaluate("afterApply(1)"); await pg.wait_for_timeout(400)
                check(await pg.evaluate("$('.main').scrollTop") == 400, f'{w}x{h} {t} : position gardée')
            await pg.evaluate("document.querySelector('[data-act=htab][data-t=suivi]').click(); V.sv = 'list'; render()"); await pg.wait_for_timeout(200)
            await pg.evaluate("$('.main').scrollTop = 300"); await pg.wait_for_timeout(100)
            await pg.evaluate("document.querySelector('[data-act=sui-sort][data-k=impl]').click()"); await pg.wait_for_timeout(400)
            check(await pg.evaluate("$('.main').scrollTop") == 300, f'{w}x{h} suivi : position gardée après un tri')
            await pg.close()

        print("5. Import de l'export École Directe (.xlsx)")
        try:
            import openpyxl
            from openpyxl.styles import PatternFill
        except ImportError:
            openpyxl = None; print('  (openpyxl absent : étape ignorée)')
        if openpyxl:
            pg = await page(b, 1280, 860, errs)
            info = await pg.evaluate("(() => { const c = DB.classes.find(x => studentsOf(x.id).length > 5); return {cid: c.id, name: c.name.replace(/^(\\d)e /, '$1ème '), st: studentsOf(c.id).map(s => s.last.toUpperCase() + ' ' + s.first.toUpperCase())}; })()")
            evs = [("Exercice maison\n15/09/2026 (DL)", 0.5, 10), ("TP conductivité\n17/09/2026 (TP)", 1, 20), ("Interro 1\n01/10/2026 (IE)", 1.5, 20), ("DS1 : chap. 1 & 2\n06/11/2026 (DS)", 3, 20)]
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Les devoirs'
            ws.cell(1, 2, 'M. PROF\nClasse : ' + info['name'] + '\nTrimestre 1\nPHYSIQUE-CHIMIE'); ws.cell(1, 4, 'Moyennes'); ws.cell(1, 6, 'Rang')
            ws.cell(2, 2, 'Coefficients'); ws.cell(3, 2, 'Noté sur')
            for j, (t, co, mx) in enumerate(evs):
                ws.cell(1, 8 + j, t); ws.cell(2, 8 + j, co); ws.cell(3, 8 + j, mx)
            blue = PatternFill('solid', fgColor='C9F0FF'); lav = PatternFill('solid', fgColor='E0E2FE'); expect = {}
            for i, name in enumerate(info['st']):
                r = 5 + i; vals = [(i % 10) + 0.5, 10 + i % 9, 'Abs' if i == 2 else 8 + i % 11, None]
                if i == 1: vals[0] = 0
                ws.cell(r, 2, name)
                a = w = 0
                for j, v in enumerate(vals):
                    if v is None: continue
                    c = ws.cell(r, 8 + j, v)
                    if v == 'Abs': c.fill = lav; continue
                    if i == 1 and j == 0: c.fill = blue; continue
                    a += v / evs[j][2] * 20 * evs[j][1]; w += evs[j][1]
                ws.cell(r, 4, round(a / w, 2)); ws.cell(r, 6, i + 1); expect[name] = a / w
            r = 6 + len(info['st'])
            for lab in ['Moyenne Classe', 'Moyenne minimale', 'Moyenne maximale', '% inférieur à 8']: ws.cell(r, 2, lab); ws.cell(r, 8, 12); r += 1
            ws.cell(r + 1, 2, 'Edité le 10/11/2026 à 22h51')
            tmp = os.path.join(tempfile.mkdtemp(), 'Les_devoirs_test.xlsx'); wb.save(tmp)
            other = await pg.evaluate("(cid) => DB.classes.find(x => x.id !== cid).id", info['cid'])
            await pg.evaluate("(id) => go({name: 'notes', cid: id, p: 0})", other); await pg.wait_for_timeout(150)
            await pg.set_input_files('input[data-chg=gfile]', tmp); await pg.wait_for_timeout(500)
            g = await pg.evaluate("(() => ({cid: V.cid, n: GIMP && GIMP.evs.length, kinds: GIMP && GIMP.evs.map(e => e.type + (e.home ? '+maison' : '')), unk: GIMP && GIMP.rows.filter(r => !r.sid).length, ok: !!$('.gcheck.good'), nc: GIMP && GIMP.rows[1].nc[0]}))()")
            check(g['cid'] == info['cid'], 'classe reconnue d\'après l\'en-tête du fichier (« ' + info['name'] + ' »)')
            check(g['n'] == 3 and g['kinds'] == ['ecrit+maison', 'tp', 'ecrit'], 'évaluations lues (DL = écrit maison, TP, IE) ; DS sans note ignoré')
            check(g['unk'] == 0, 'tous les élèves reconnus')
            check(g['ok'] and g['nc'], 'aperçu : moyennes identiques à École Directe, note en bleu non comptée')
            await pg.click('[data-act=gimp-ok]'); await pg.wait_for_timeout(200)
            app = await pg.evaluate("(cid) => { const ev = DB.evals.filter(e => e.cid === cid); return Object.fromEntries(studentsOf(cid).map(s => [s.last.toUpperCase() + ' ' + s.first.toUpperCase(), avgOf(ev, s.id)])); }", info['cid'])
            check(all(abs(app[k] - v) < 1e-6 for k, v in expect.items()), 'moyennes calculées après import = moyennes École Directe')
            await pg.set_input_files('input[data-chg=gfile]', tmp); await pg.wait_for_timeout(400); await pg.click('[data-act=gimp-ok]'); await pg.wait_for_timeout(200)
            check(await pg.evaluate("(cid) => DB.evals.filter(e => e.cid === cid).length", info['cid']) == 3, 'réimport du même fichier : pas de doublon')
            await pg.close()
        await b.close()
    check(not errs, 'aucune erreur JavaScript' + ('' if not errs else ' : ' + ' | '.join(errs[:5])))
    print('\nRésultat :', 'TOUT EST CORRECT' if not FAILS else f'{len(FAILS)} ÉCHEC(S)')
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
