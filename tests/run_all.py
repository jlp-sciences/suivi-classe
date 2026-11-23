#!/usr/bin/env python3
"""Tests de non-régression de Suivi de classe.
   Usage : python3 tests/run_all.py   (depuis la racine du dépôt ; nécessite playwright + chromium)
   1. lance les vérifications intégrées (runSelfTests, dans index.html) ;
   2. vérifie l'affichage de la vue semaine (rien ne déborde ni ne se chevauche) sur 4 tailles d'écran ;
   3. parcourt les écrans principaux et s'assure qu'aucune erreur JavaScript n'apparaît ;
   4. vérifie que la position de défilement est gardée lors d'une mise à jour automatique ;
   5. importe un export Excel « Les devoirs » d'École Directe fabriqué (élèves fictifs) et compare les moyennes ;
   6. simule la publication d'une nouvelle version : l'application doit se mettre à jour dès l'ouverture, avant de synchroniser ;
   7. bouton « retour » du téléphone : il revient en arrière dans l'application, et ne quitte que depuis l'emploi du temps."""
import asyncio, http.server, socketserver, threading, functools, os, sys, tempfile, shutil, re
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
            # une saisie en cours ne doit pas être effacée par un redessin automatique (synchronisation)
            await pg.evaluate("go({name: 'bul', cid: DB.classes.find(x => studentsOf(x.id).length > 5).id, p: 0})"); await pg.wait_for_timeout(200)
            ta = pg.locator('.bullist textarea').first; await ta.click(); await pg.keyboard.type('Saisie en cours'); await pg.wait_for_timeout(1400)
            await pg.evaluate("autoRender()"); await pg.wait_for_timeout(300)
            check(await pg.locator('.bullist textarea').first.input_value() == 'Saisie en cours', f'{w}x{h} appréciations : texte en cours de saisie gardé pendant une synchronisation')
            over = await pg.evaluate("[...document.querySelectorAll('.bullist .bh > *')].filter(el => el.getBoundingClientRect().right > window.innerWidth + 1).length")
            check(over == 0, f'{w}x{h} appréciations : rien ne dépasse de l\'écran')
            await pg.evaluate("document.activeElement && document.activeElement.blur()")
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

        print("6. Mise à jour dès l'ouverture")
        src = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read(); swsrc = open(os.path.join(ROOT, 'sw.js'), encoding='utf-8').read()
        c1 = re.search(r"const SW_CACHE = '([^']+)'", src).group(1); c2 = re.search(r"const CACHE = '([^']+)'", swsrc).group(1)
        check(c1 == c2, f'index.html et sw.js annoncent le même cache ({c1})')
        tmpd = tempfile.mkdtemp()
        for f in os.listdir(ROOT):
            if os.path.isfile(os.path.join(ROOT, f)): shutil.copy(os.path.join(ROOT, f), tmpd)
        class Q2(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a): pass
            def end_headers(self): self.send_header('Cache-Control', 'max-age=600'); super().end_headers()  # comme GitHub Pages
        srv2 = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(Q2, directory=tmpd)); port2 = srv2.server_address[1]
        threading.Thread(target=srv2.serve_forever, daemon=True).start()
        ctx = await b.new_context(viewport={'width': 1024, 'height': 768}); pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        url = f'http://localhost:{port2}/?swtest=1'
        await pg.goto(url); await pg.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
        v1 = await pg.evaluate("APP_VERSION.n")
        # « publication » : nouvelle version sur le serveur
        n = int(re.search(r'(\d+)$', c1).group(1)) + 1
        open(os.path.join(tmpd, 'index.html'), 'w', encoding='utf-8').write(src.replace(c1, f'suivi-classe-v{n}').replace("const APP_VERSION = {n: '" + v1 + "'", "const APP_VERSION = {n: '99.0'"))
        open(os.path.join(tmpd, 'sw.js'), 'w', encoding='utf-8').write(swsrc.replace(c2, f'suivi-classe-v{n}'))
        for f in ('index.html', 'sw.js'): os.utime(os.path.join(tmpd, f), (os.path.getatime(os.path.join(tmpd, f)), os.path.getmtime(os.path.join(tmpd, f)) + 10))  # date de modification nettement différente (le serveur de test répond à la seconde près)
        await pg.goto(url)   # une seule ouverture : l'ancienne version démarre, voit la nouvelle, l'installe et recharge
        try:
            await pg.wait_for_function("typeof APP_VERSION !== 'undefined' && APP_VERSION.n === '99.0'", timeout=30000); okv = True
        except Exception: okv = False
        check(okv, 'nouvelle version chargée dès la première ouverture (sans fermer puis rouvrir)')
        await pg.wait_for_timeout(1500)
        check(await pg.evaluate("APP_VERSION.n") == '99.0' and await pg.evaluate("sessionStorage.getItem('sc-upd')") == '1', 'un seul rechargement, pas de boucle')
        await ctx.close(); srv2.shutdown()

        print("7. Bouton « retour » du téléphone")
        ctx = await b.new_context(viewport={'width': 390, 'height': 844}); pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'http://localhost:{PORT}/'); await pg.wait_for_timeout(300); await pg.click('text=Essayer avec des élèves fictifs'); await pg.wait_for_timeout(400)
        await pg.evaluate("document.querySelector('[data-act=htab][data-t=suivi]').click()"); await pg.wait_for_timeout(150)
        await pg.evaluate("go({name: 'fiche', sid: studentsOf(DB.classes[0].id)[0].id})"); await pg.wait_for_timeout(150)
        await pg.evaluate("openModal('<p>test</p>')"); await pg.wait_for_timeout(100)
        st = []
        for _ in range(3):
            await pg.go_back(); await pg.wait_for_timeout(300)
            st.append(await pg.evaluate("[V.name, V.tab || '', !!$('#modal').innerHTML]"))
        check(st == [['fiche', '', False], ['today', 'suivi', False], ['today', 'edt', False]], f'retour : fenêtre fermée, puis fiche → Suivi → emploi du temps ({st})')
        check(await pg.evaluate("!(history.state && history.state.sc === 'app')"), 'à l\'emploi du temps, le retour suivant quitte l\'application')
        await pg.evaluate("window.__alive = 1; openModal('<p>a</p>'); closeModal(); openModal('<p>b</p>'); closeModal(); render(); openModal('<p>c</p>'); closeModal(); render()"); await pg.wait_for_timeout(600)
        check(await pg.evaluate("window.__alive === 1 && V.name === 'today'"), 'ouvrir et fermer des fenêtres à l\'emploi du temps ne fait jamais quitter la page')
        await pg.go_back(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("typeof window.__alive") == 'undefined', 'à l\'emploi du temps, un seul retour quitte l\'application')
        await pg.go_forward(); await pg.wait_for_timeout(600)
        if await pg.evaluate("typeof DB === 'undefined' || !DB.classes.length"):
            await pg.click('text=Essayer avec des élèves fictifs'); await pg.wait_for_timeout(400)
        await pg.evaluate("go({name: 'bul', cid: DB.classes[0].id, p: 0})"); await pg.wait_for_timeout(150)
        await pg.click('[data-act=back]'); await pg.wait_for_timeout(300)
        check(await pg.evaluate("[V.name, V.tab, !(history.state && history.state.sc === 'app')]") == ['today', 'edt', True], 'bouton Retour de l\'écran : pas de retour « fantôme » à refaire ensuite')
        await ctx.close()
        await b.close()
    check(not errs, 'aucune erreur JavaScript' + ('' if not errs else ' : ' + ' | '.join(errs[:5])))
    print('\nRésultat :', 'TOUT EST CORRECT' if not FAILS else f'{len(FAILS)} ÉCHEC(S)')
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
