#!/usr/bin/env python3
"""Tests de non-régression de Suivi de classe.
   Usage : python3 tests/run_all.py   (depuis la racine du dépôt ; nécessite playwright + chromium)
   1. lance les vérifications intégrées (runSelfTests, dans index.html) ;
   2. vérifie l'affichage de la vue semaine (rien ne déborde ni ne se chevauche) sur 4 tailles d'écran ;
   3. parcourt les écrans principaux et s'assure qu'aucune erreur JavaScript n'apparaît ;
   4. vérifie que la position de défilement est gardée lors d'une mise à jour automatique."""
import asyncio, http.server, socketserver, threading, functools, os, sys
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
            for t in ['edt', 'periodes', 'sauvegarde', 'sync']:
                await pg.evaluate(f"V.tab = '{t}'; render()"); await pg.wait_for_timeout(80)
            await pg.close()

        print('4. Position gardée lors des mises à jour automatiques')
        for (w, h) in [(1280, 800), (390, 844)]:
            pg = await page(b, w, h, errs)
            for t in ['suivi', 'prog']:
                await pg.evaluate(f"document.querySelector('[data-act=htab][data-t={t}]').click(); V.pAll = true; render()"); await pg.wait_for_timeout(200)
                await pg.evaluate("$('.main').scrollTop = 400"); await pg.wait_for_timeout(1400)
                await pg.evaluate("afterApply(1)"); await pg.wait_for_timeout(400)
                check(await pg.evaluate("$('.main').scrollTop") == 400, f'{w}x{h} {t} : position gardée')
            await pg.close()
        await b.close()
    check(not errs, 'aucune erreur JavaScript' + ('' if not errs else ' : ' + ' | '.join(errs[:5])))
    print('\nRésultat :', 'TOUT EST CORRECT' if not FAILS else f'{len(FAILS)} ÉCHEC(S)')
    sys.exit(1 if FAILS else 0)

asyncio.run(main())
