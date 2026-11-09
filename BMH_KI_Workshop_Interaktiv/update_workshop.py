from pathlib import Path
import json, re
base=Path(__file__).resolve().parent
qpath=base/'fragen.json'; server=base/'ki_workshop.py'; participant=base/'assets/participant.js'; presenter=base/'assets/presenter.js'; css=base/'assets/style.css'
for f in (qpath,server,participant,presenter,css):
 if not f.exists(): raise SystemExit(f'Fehlende Datei: {f}')
questions=json.loads(qpath.read_text(encoding='utf-8'))
new=[
 ('Gemälde: Original oder KI?','Welches Bild hat die KI erstellt?','B','Links ist Vincent van Goghs Gemälde „Fischerboote bei Saintes-Maries-de-la-Mer“ (1888). Rechts wurde ein Bild im ähnlichen Stil mit KI erzeugt.'),
 ('Essen: Welches Steak ist künstlich?','Welches Steak kann man nicht wirklich essen?','A','Das Lachsgericht links wurde mit KI erzeugt. Auffällig sind unter anderem die ungewöhnlichen Proportionen der geschnittenen Stücke.'),
 ('Moderatorin: Welches Foto ist echt?','Auf welchem Bild sieht man die echte Moderatorin?','A','A ist die echte Aufnahme. B, C und D sind KI-generierte Variationen auf Grundlage eines echten Fotos.'),
 ('Katzen: Wer jagt nur digitale Mäuse?','Welche dieser Katzen ist KI-generiert?','D','Die springende Katze in D ist KI-generiert. Die Pfotenstellung und Perspektive können Hinweise liefern.'),
 ('Baby: Welches Foto ist künstlich?','Welches Baby-Foto hat die KI erstellt?','B','Das Baby mit Mütze (B) ist KI-generiert. Besonders Haut und Augen wirken ungewöhnlich glatt.'),
 ('Tiger: Original oder KI?','Welches Tiger-Bild wurde mit KI erstellt?','A','A ist KI-generiert. Gerade bei Tierporträts ohne viel Hintergrund sind künstliche Bilder schwer zu erkennen.'),
 ('Katzenbrille: Welches Bild ist KI?','Welches Bild stammt von der KI?','B','Die Katze mit der schwarzen Brille (B) wurde mit KI erstellt. Das echte Foto links zeigt unter anderem natürlich verschmutzte Brillengläser.'),
 ('Skifahren: Welche Skier sind digital?','Welche Skier sind rein digital?','B','B ist KI-generiert. Ein Hinweis ist die unplausible Ausrichtung der Skibindung.'),
 ('Urlaub: Welches Foto ist KI?','Welches Urlaubsfoto kommt von der KI?','B','B wurde mit einem KI-Bildgenerator erstellt. Die realistische Tiefenunschärfe macht die Erkennung besonders schwierig.')]
first=[dict(id=f'bild_{i}',part=1,type='detect',title=title,subtitle=subtitle,media='image',content=f'frage{i}.png',options=list('ABCD') if i in (3,4,9) else ['A','B'],solution=answer,reason=reason) for i,(title,subtitle,answer,reason) in enumerate(new,1)]
questions=first+[q for q in questions if q['part']!=1]
qpath.write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
s=server.read_text(encoding='utf-8')
s=s.replace("opts=['Grün','Gelb','Rot'] if q['type']=='scenario' else ['KI-generiert','Mensch'] if q['type']=='detect' else q['options']", "opts=['Grün','Gelb','Rot'] if q['type']=='scenario' else q.get('options',['KI-generiert','Mensch']) if q['type']=='detect' else q['options']")
s=s.replace("if v not in ('KI-generiert','Mensch'):return self.error(400,'Bitte eine Antwort wählen')", "if v not in q.get('options',['KI-generiert','Mensch']):return self.error(400,'Bitte eine Antwort wählen')")
s=s.replace("if path.startswith('/assets/quiz_') and path.endswith('.jpg'):","if path.startswith('/assets/') and Path(path).name.startswith(('quiz_','frage')) and path.lower().endswith(('.jpg','.jpeg','.png')):")
s=s.replace("mime='image/jpeg')", "mime='image/png' if f.suffix.lower()=='.png' else 'image/jpeg')")
server.write_text(s,encoding='utf-8')
p=participant.read_text(encoding='utf-8')
p=p.replace("q.type==='detect'?['KI-generiert','Mensch']:q.options", "q.type==='detect'?(q.options||['KI-generiert','Mensch']):q.options")
p=p.replace("'Auflösung: '+q.solution", "'✗ Leider falsch · Richtig: '+q.solution")
participant.write_text(p,encoding='utf-8')
c=css.read_text(encoding='utf-8')
c+='\n/* Bildquiz: ganze Collage sichtbar statt abgeschnitten */\n.quizimage{object-fit:contain;max-height:none;height:auto;background:#eef3f6}.scenarioPrompt:has(.quizimage):before{content:"BILDQUIZ"}.mobilecard .quizimage{max-height:none}.optiongrid:has(.option:nth-child(4)){grid-template-columns:repeat(2,minmax(0,1fr))}.optiongrid:has(.option:nth-child(4)) .option{justify-content:center;font-size:20px}\n'
css.write_text(c,encoding='utf-8')
print('Erfolgreich aktualisiert: fragen.json, ki_workshop.py, participant.js, style.css')
print('presenter.js benötigt keine Änderung: Die Balken werden aus den Server-Antwortmöglichkeiten erzeugt.')
