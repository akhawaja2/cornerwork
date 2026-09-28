"""Single-gym offline demo. All external services are deterministic fakes."""
import csv, io, json, re, sqlite3, statistics
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from collections import Counter
GYM=dict(name="Cornerwork Demo Gym",phone="+15550000000",coach="Sam",coach_phone="+15550000999",owner="Alex (gym owner)",timezone="America/New_York")
VOICE="Clinch felt sharper today. Kept getting countered off the jab. My left shin is sore after checks."
CONSENT="Cornerwork for Cornerwork Demo Gym: service coaching texts only. Reply YES 18 to confirm you are 18 or older and consent. STOP anytime. Demo messages stay on this computer."

def now(): return datetime.now(timezone.utc).isoformat()
def rows(c,s,p=()): return [dict(r) for r in c.execute(s,p)]
def init_db(path):
    c=sqlite3.connect(path,check_same_thread=False);c.row_factory=sqlite3.Row
    c.executescript("""
CREATE TABLE IF NOT EXISTS athletes(id INTEGER PRIMARY KEY,name TEXT,phone TEXT UNIQUE,status TEXT DEFAULT 'pending',membership_start TEXT,goal TEXT DEFAULT '',adult INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY,athlete_id INTEGER,direction TEXT,body TEXT,kind TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY,athlete_id INTEGER,transcript TEXT,summary TEXT,techniques TEXT,sentiment TEXT,injury TEXT,concussion_flag INTEGER,coach_draft TEXT,kind TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS replies(id INTEGER PRIMARY KEY,log_id INTEGER UNIQUE,body TEXT,via TEXT,sent_at TEXT,reply_seconds REAL);
CREATE TABLE IF NOT EXISTS flags(id INTEGER PRIMARY KEY,athlete_id INTEGER,type TEXT,detail TEXT,opened_at TEXT);
CREATE TABLE IF NOT EXISTS concerns(id INTEGER PRIMARY KEY,athlete_id INTEGER,body TEXT,at TEXT,route TEXT);
CREATE TABLE IF NOT EXISTS consents(id INTEGER PRIMARY KEY,athlete_id INTEGER,action TEXT,raw_message TEXT,at TEXT);
CREATE TABLE IF NOT EXISTS classes(id INTEGER PRIMARY KEY,name TEXT,start_time TEXT,duration_min INTEGER,weekday INTEGER);
CREATE TABLE IF NOT EXISTS bookings(id INTEGER PRIMARY KEY,class_id INTEGER,athlete_id INTEGER,class_date TEXT,status TEXT,UNIQUE(class_id,athlete_id,class_date));
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,athlete_id INTEGER,type TEXT,meta TEXT,at TEXT,event_key TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY,result TEXT);
""")
    return c
def event(c,typ,aid=None,meta=None,at=None,key=None):
    c.execute("INSERT OR IGNORE INTO events(athlete_id,type,meta,at,event_key) VALUES(?,?,?,?,?)",(aid,typ,json.dumps(meta or {}),at or now(),key))
def send(c,aid,body,at=None,confirmation=False):
    a=c.execute("SELECT status FROM athletes WHERE id=?",(aid,)).fetchone()
    if not a or (a[0]!="active" and not confirmation): return False
    c.execute("INSERT INTO messages(athlete_id,direction,body,kind,at) VALUES(?,?,?,?,?)",(aid,"out",body,"simulated SMS",at or now()))
    return True
def cached(c,rid):
    r=c.execute("SELECT result FROM requests WHERE id=?",(rid,)).fetchone() if rid else None
    return json.loads(r[0]) if r else None
def done(c,result,rid=None):
    if rid: c.execute("INSERT INTO requests VALUES(?,?)",(rid,json.dumps(result)))
    c.commit();return result
def add_log(c,aid,text,kind="text",at=None):
    at=at or now();low=text.lower()
    tags=[x for x in ["jab","clinch","footwork","guard","roundhouse","teep","sparring","defense"] if x in low]
    concussion=any(x in low for x in ["concussion","head","dizzy","blackout","knocked out"])
    injury=None
    if concussion or any(x in low for x in ["sore","pain","hurt","injur","swollen"]):
        injury=dict(area=next((x for x in ["shin","knee","ankle","shoulder","wrist","head","neck","back"] if x in low),"unspecified"),severity="unknown",quote=text)
    sentiment="neg" if any(x in low for x in ["frustrat","struggl","stuck","quit"]) else ("pos" if any(x in low for x in ["better","sharper","clicked","great"]) else "neutral")
    lid=c.execute("INSERT INTO logs(athlete_id,transcript,summary,techniques,sentiment,injury,concussion_flag,coach_draft,kind,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(aid,text,text[:220],json.dumps(tags),sentiment,json.dumps(injury),int(concussion),"Thanks for the update. Let’s check in before your next class.",kind,at)).lastrowid
    event(c,"log_received",aid,dict(log_id=lid,kind=kind),at);event(c,"log_parsed",aid,dict(log_id=lid,parser="deterministic demo rules"),at)
    if injury:
        typ="concussion" if concussion else "injury"
        c.execute("INSERT INTO flags(athlete_id,type,detail,opened_at) VALUES(?,?,?,?)",(aid,typ,text,at))
        event(c,"injury_flagged",aid,dict(type=typ,log_id=lid),at)
    if concussion: event(c,"coach_alert",aid,dict(log_id=lid,reason="Possible head injury: immediate coach review"),at)
    return lid,injury,concussion
def inbound(c,phone,body,kind="text",request_id=None):
    old=cached(c,request_id)
    if old is not None: return old
    phone,body=phone.strip(),body.strip()
    if not re.fullmatch(r"\+[1-9]\d{7,14}",phone): raise ValueError("Use an E.164 number, such as +15550000001.")
    if not body and kind!="voice": raise ValueError("Enter a message.")
    if len(body)>4000: raise ValueError("Keep messages under 4,000 characters.")
    if kind not in ("text","voice"): raise ValueError("Choose text or voice fixture.")
    if phone==GYM["coach_phone"]:
        m=re.match(r"^#(\d+)\s+(.+)$",body,re.S)
        if not m: raise ValueError("Coach SMS needs an athlete ID: #1 Your reply.")
        log=c.execute("SELECT l.id FROM logs l LEFT JOIN replies r ON r.log_id=l.id WHERE l.athlete_id=? AND r.id IS NULL ORDER BY l.id DESC LIMIT 1",(int(m[1]),)).fetchone()
        if not log: raise ValueError("No unanswered log for that athlete.")
        return reply(c,log["id"],m[2],via="sms",request_id=request_id)
    a=c.execute("SELECT * FROM athletes WHERE phone=?",(phone,)).fetchone()
    if not a:
        c.execute("INSERT INTO athletes(name,phone,membership_start) VALUES(?,?,?)",("New athlete",phone,now()[:10]))
        a=c.execute("SELECT * FROM athletes WHERE phone=?",(phone,)).fetchone()
    aid=a["id"];command=body.upper()
    c.execute("INSERT INTO messages(athlete_id,direction,body,kind,at) VALUES(?,?,?,?,?)",(aid,"in",body,kind,now()))
    if command=="STOP":
        c.execute("UPDATE athletes SET status='stopped' WHERE id=?",(aid,))
        c.execute("INSERT INTO consents(athlete_id,action,raw_message,at) VALUES(?,?,?,?)",(aid,"stop",body,now()))
        event(c,"opt_out",aid);send(c,aid,"You are opted out. No more coaching messages. Send JOIN to restart consent.",confirmation=True)
        return done(c,dict(ok=True,message="Stopped. Future coaching messages suppressed.",athlete_id=aid),request_id)
    if command=="JOIN":
        if a["status"]=="active": return done(c,dict(ok=True,message="Already opted in.",athlete_id=aid),request_id)
        c.execute("UPDATE athletes SET status='pending',adult=0 WHERE id=?",(aid,))
        c.execute("INSERT INTO consents(athlete_id,action,raw_message,at) VALUES(?,?,?,?)",(aid,"join_requested",body,now()))
        send(c,aid,CONSENT,confirmation=True)
        return done(c,dict(ok=True,message="Reply YES 18 to confirm adulthood and consent.",athlete_id=aid),request_id)
    if command=="YES 18" and a["status"]=="pending":
        if not c.execute("SELECT id FROM consents WHERE athlete_id=? AND action='join_requested'",(aid,)).fetchone(): raise ValueError("Send JOIN to see consent terms first.")
        c.execute("UPDATE athletes SET status='active',adult=1 WHERE id=?",(aid,))
        c.execute("INSERT INTO consents(athlete_id,action,raw_message,at) VALUES(?,?,?,?)",(aid,"join",body+" | "+CONSENT,now()))
        event(c,"opt_in",aid);send(c,aid,"Welcome! Text what clicked after class and what you need help with. Coach Sam will review. STOP anytime.")
        return done(c,dict(ok=True,message="Adult consent recorded. Ready to log.",athlete_id=aid),request_id)
    if a["status"]!="active": return done(c,dict(ok=False,message="Not opted in. Send JOIN, then YES 18. No coaching message sent.",athlete_id=aid),request_id)
    text=(body or VOICE) if kind=="voice" else body
    if any(x in text.lower() for x in ["harass","coach conduct","confidential","unsafe with coach","inappropriate"]):
        c.execute("INSERT INTO concerns(athlete_id,body,at,route) VALUES(?,?,?,?)",(aid,text,now(),GYM["owner"]))
        event(c,"concern_routed",aid,dict(route="owner only"));send(c,aid,"Your concern was routed to Alex, the gym owner, for private follow-up. It will not appear in the coach inbox or brief. This is not an emergency service.")
        return done(c,dict(ok=True,message="Concern routed to owner only.",athlete_id=aid),request_id)
    lid,injury,concussion=add_log(c,aid,text,"voice fixture transcript" if kind=="voice" else "text")
    ack="Got it — Coach Sam will review."
    if concussion: ack+=" Possible head-injury concern flagged for immediate coach review. Please seek prompt medical evaluation; this service cannot assess injuries."
    elif injury: ack+=" Flagged to Coach Sam. If it is serious, please see a medical professional."
    send(c,aid,ack);return done(c,dict(ok=True,message="Log added to coach inbox.",log_id=lid,athlete_id=aid),request_id)
def reply(c,log_id,body,via="web",request_id=None):
    old=cached(c,request_id)
    if old is not None: return old
    if not body.strip(): raise ValueError("Write a reply first.")
    if len(body)>1600: raise ValueError("Keep replies under 1,600 characters.")
    log=c.execute("SELECT * FROM logs WHERE id=?",(log_id,)).fetchone()
    if not log: raise ValueError("Log not found.")
    if c.execute("SELECT id FROM replies WHERE log_id=?",(log_id,)).fetchone(): raise ValueError("This log already has a reply.")
    if not send(c,log["athlete_id"],"Coach Sam: "+body.strip()): raise ValueError("Athlete opted out; reply suppressed.")
    sent=now();secs=max(0,(datetime.fromisoformat(sent)-datetime.fromisoformat(log["created_at"])).total_seconds())
    c.execute("INSERT INTO replies(log_id,body,via,sent_at,reply_seconds) VALUES(?,?,?,?,?)",(log_id,body.strip(),via,sent,secs))
    event(c,"reply_sent",log["athlete_id"],dict(log_id=log_id,reply_seconds=secs,coach="Sam",via=via))
    return done(c,dict(ok=True,message="Simulated SMS delivered.",log_id=log_id),request_id)
def brief(c,class_id,date,record=True):
    datetime.strptime(date,"%Y-%m-%d")
    cls=c.execute("SELECT * FROM classes WHERE id=?",(class_id,)).fetchone()
    if not cls: raise ValueError("Class not found.")
    athletes=rows(c,"SELECT a.*,b.status AS booking_status FROM bookings b JOIN athletes a ON a.id=b.athlete_id WHERE b.class_id=? AND b.class_date=? AND b.status IN ('booked','attended')",(class_id,date))
    themes=Counter();cutoff=(datetime.fromisoformat(date)-timedelta(days=7)).isoformat()
    for a in athletes:
        a["flags"]=rows(c,"SELECT type,detail FROM flags WHERE athlete_id=?",(a["id"],))
        if 0<=(datetime.fromisoformat(date).date()-datetime.fromisoformat(a["membership_start"]).date()).days<=14: a["flags"].append(dict(type="new",detail="Joined within two weeks"))
        ls=rows(c,"SELECT summary,techniques FROM logs WHERE athlete_id=? AND created_at>=? AND created_at<? ORDER BY created_at DESC",(a["id"],cutoff,date+"T23:59:59"))
        a["latest_summary"]=ls[0]["summary"] if ls else "No recent log."
        for log in ls: themes.update(json.loads(log["techniques"]))
    focus="Check in individually before class; ask what each athlete wants to work on."
    if themes: focus="Demo suggestion: revisit "+themes.most_common(1)[0][0]+" with the group. Adapt individually after checking flags."
    result=dict(class_id=class_id,class_name=cls["name"],date=date,start_time=cls["start_time"],athletes=athletes,themes=[dict(name=k,count=v) for k,v in themes.most_common(5)],focus=focus,generated_at=now(),model="deterministic demo rules")
    if record: event(c,"brief_generated",meta=dict(class_id=class_id,date=date));c.commit()
    return result
def jobs(c,now_iso=None):
    dt=datetime.fromisoformat(now_iso) if now_iso else datetime.now(timezone.utc)
    if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
    dt=dt.astimezone(timezone.utc);local=dt.astimezone(ZoneInfo(GYM["timezone"]));at=dt.isoformat();count=0
    if not 8<=local.hour<22: return dict(ok=True,message="Quiet hours: no scheduled messages sent.",sent=0)
    for b in rows(c,"SELECT b.*,cl.start_time,cl.duration_min FROM bookings b JOIN classes cl ON cl.id=b.class_id JOIN athletes a ON a.id=b.athlete_id WHERE b.class_date=? AND b.status IN ('booked','attended') AND a.status='active'",(local.date().isoformat(),)):
        end=datetime.fromisoformat(b["class_date"]+"T"+b["start_time"]).replace(tzinfo=local.tzinfo)+timedelta(minutes=b["duration_min"]+45)
        key=f"nudge:{b['athlete_id']}:{local.date()}"
        if local>=end and not c.execute("SELECT id FROM events WHERE event_key=?",(key,)).fetchone():
            send(c,b["athlete_id"],"Good session? Text or voice note: what clicked, anything sore?",at)
            event(c,"nudge_sent",b["athlete_id"],dict(class_id=b["class_id"]),at,key);count+=1
    if local.weekday()==6 and local.hour>=18:
        cutoff=(dt-timedelta(days=7)).isoformat()
        for a in rows(c,"SELECT * FROM athletes WHERE status='active'"):
            key=f"recap:{a['id']}:{local.date()}"
            if c.execute("SELECT id FROM events WHERE event_key=?",(key,)).fetchone(): continue
            ls=rows(c,"SELECT * FROM logs WHERE athlete_id=? AND created_at>=? AND created_at<=?",(a["id"],cutoff,at))
            if not ls:
                prior=c.execute("SELECT at FROM events WHERE athlete_id=? AND type='inactive_recap_sent' ORDER BY at DESC LIMIT 1",(a["id"],)).fetchone()
                if prior and (dt-datetime.fromisoformat(prior["at"])).total_seconds()<14*86400: continue
                text="No logs this week? Share a quick update when you are ready. Coach Sam is here to help."
            else:
                tags=Counter(t for log in ls for t in json.loads(log["techniques"]));focus=tags.most_common(1)[0][0] if tags else "your training goals"
                note=c.execute("SELECT r.body FROM replies r JOIN logs l ON l.id=r.log_id WHERE l.athlete_id=? AND r.sent_at>=? AND r.sent_at<=? ORDER BY r.sent_at DESC LIMIT 1",(a["id"],cutoff,at)).fetchone()
                coach_note=note["body"][:120] if note else "No coach reply this week."
                text=f"Your week: {len(ls)} training logs. Focus: {focus}.\nCoach Sam: {coach_note}\nNext step: check in with Sam before class."
            send(c,a["id"],text[:320],at);event(c,"recap_sent",a["id"],dict(logs=len(ls)),at,key)
            if not ls: event(c,"inactive_recap_sent",a["id"],at=at)
            count+=1
    c.commit();return dict(ok=True,message=f"{count} scheduled demo messages sent.",sent=count,at=at)
def import_csv(c,kind,text):
    if kind not in ("athletes","bookings"): raise ValueError("Choose athletes or bookings.")
    reader=csv.DictReader(io.StringIO(text));records=list(reader)
    required={"name","phone","membership_start"} if kind=="athletes" else {"phone","class_id","class_date","status"}
    if not required.issubset(reader.fieldnames or []): raise ValueError("Required CSV headers: "+", ".join(sorted(required)))
    if len(records)>1000: raise ValueError("Demo limit is 1,000 rows.")
    with c:
        for i,r in enumerate(records,2):
            if not all(r.get(k) for k in required): raise ValueError(f"Row {i}: missing values.")
            phone=r["phone"].strip()
            if not re.fullmatch(r"\+[1-9]\d{7,14}",phone): raise ValueError(f"Row {i}: invalid phone.")
            if kind=="athletes":
                datetime.strptime(r["membership_start"],"%Y-%m-%d")
                c.execute("INSERT INTO athletes(name,phone,membership_start) VALUES(?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name,membership_start=excluded.membership_start",(r["name"].strip(),phone,r["membership_start"]))
            else:
                a=c.execute("SELECT id FROM athletes WHERE phone=?",(phone,)).fetchone()
                if not a: raise ValueError(f"Row {i}: import athlete first.")
                cid=int(r["class_id"]);date=r["class_date"];datetime.strptime(date,"%Y-%m-%d")
                if not c.execute("SELECT id FROM classes WHERE id=?",(cid,)).fetchone(): raise ValueError(f"Row {i}: unknown class.")
                if r["status"] not in ("booked","attended","no_show"): raise ValueError(f"Row {i}: invalid status.")
                c.execute("INSERT INTO bookings(class_id,athlete_id,class_date,status) VALUES(?,?,?,?) ON CONFLICT(class_id,athlete_id,class_date) DO UPDATE SET status=excluded.status",(cid,a["id"],date,r["status"]))
                event(c,"booking_imported",a["id"],dict(class_id=cid,date=date,status=r["status"]),key=f"booking:{cid}:{a['id']}:{date}:{r['status']}")
                if r["status"]=="attended":
                    start=c.execute("SELECT start_time FROM classes WHERE id=?",(cid,)).fetchone()["start_time"]
                    attended_at=datetime.fromisoformat(date+"T"+start).replace(tzinfo=ZoneInfo(GYM["timezone"])).astimezone(timezone.utc).isoformat()
                    event(c,"check_in",a["id"],dict(class_id=cid,date=date),at=attended_at,key=f"checkin:{cid}:{a['id']}:{date}")
        event(c,"csv_imported",meta=dict(kind=kind,rows=len(records)))
    return dict(ok=True,message=f"Imported {len(records)} {kind} rows. Imports do not grant consent.",rows=len(records))
def seed(c):
    if c.execute("SELECT count(*) FROM athletes").fetchone()[0]: return
    dt=datetime.now(timezone.utc);today=dt.date()
    names=["Maya Chen","Jordan Rivera","Noah Williams","Priya Shah","Eli Brooks","Avery Taylor","Sofia Patel","Liam Jones","Zoe Wilson","Chris Park"]
    c.execute("INSERT INTO classes VALUES(1,'Thursday Muay Thai','19:00',60,3)")
    for i,name in enumerate(names,1):
        status="active" if i<=8 else ("pending" if i==9 else "stopped")
        start=(today-timedelta(days=3 if i==8 else 120)).isoformat()
        c.execute("INSERT INTO athletes VALUES(?,?,?,?,?,?,?)",(i,name,f"+155500000{i:02d}",status,start,"Build confidence and cleaner technique",int(i<=8)))
        if i<=8:
            event(c,"opt_in",i,dict(fixture=True),(dt-timedelta(days=14)).isoformat())
            c.execute("INSERT INTO consents(athlete_id,action,raw_message,at) VALUES(?,?,?,?)",(i,"join","DEMO FIXTURE: YES 18 | "+CONSENT,(dt-timedelta(days=14)).isoformat()))
        for age in ([13] if i==7 else ([13,9,5,1] if i<=6 else [])):
            at=(dt-timedelta(days=age,hours=i)).isoformat()
            text=["Jab felt sharper; working on footwork.","Clinch entries clicked today.","Struggling with guard and defense.","Left shin sore after checks.","Teep timing was better today.","Sparring was great; jab exits need work.","Footwork felt stuck."][i-1]
            lid,_,_=add_log(c,i,text,at=at)
            c.execute("INSERT INTO messages(athlete_id,direction,body,kind,at) VALUES(?,?,?,?,?)",(i,"in",text,"text",at))
            if age>1:
                sent=(datetime.fromisoformat(at)+timedelta(hours=6+i)).isoformat();body="Thanks for logging. Let’s revisit that together before class."
                c.execute("INSERT INTO replies(log_id,body,via,sent_at,reply_seconds) VALUES(?,?,?,?,?)",(lid,body,"web",sent,(6+i)*3600))
                send(c,i,"Coach Sam: "+body,sent);event(c,"reply_sent",i,dict(log_id=lid,reply_seconds=(6+i)*3600,coach="Sam"),sent)
        if i<=6:
            for age in [12,8,4,1]:
                date=(today-timedelta(days=age)).isoformat()
                c.execute("INSERT INTO bookings(class_id,athlete_id,class_date,status) VALUES(1,?,?,?)",(i,date,"attended"))
                event(c,"check_in",i,dict(class_id=1,date=date),date+"T20:00:00+00:00")
    date=(today+timedelta(days=(3-today.weekday())%7)).isoformat()
    for i in [1,2,3,4,5,6,8,9]: c.execute("INSERT INTO bookings(class_id,athlete_id,class_date,status) VALUES(1,?,?,?)",(i,date,"booked"))
    c.execute("INSERT INTO flags(athlete_id,type,detail,opened_at) VALUES(2,'fight_prep','Coach-entered demo fixture: preparing for a bout',?)",(now(),))
    c.execute("INSERT INTO flags(athlete_id,type,detail,opened_at) VALUES(6,'returning','Coach-entered demo fixture: returning after time away',?)",(now(),))
    event(c,"demo_seeded",meta=dict(athletes=10,days=14));c.commit()
def state(c,role="owner"):
    athletes=rows(c,"SELECT * FROM athletes ORDER BY id")
    logs=rows(c,"SELECT l.*,a.name,a.phone,a.status,r.body AS reply,r.sent_at AS replied_at,r.reply_seconds FROM logs l JOIN athletes a ON a.id=l.athlete_id LEFT JOIN replies r ON r.log_id=l.id ORDER BY l.created_at DESC,l.id DESC")
    for log in logs:
        log["techniques"]=json.loads(log["techniques"]);log["injury"]=json.loads(log["injury"]);log["concussion_flag"]=bool(log["concussion_flag"])
    events=rows(c,"SELECT * FROM events ORDER BY at DESC,id DESC")
    for e in events: e["meta"]=json.loads(e["meta"])
    cutoff=(datetime.now(timezone.utc)-timedelta(days=7)).isoformat()
    active={a["id"] for a in athletes if a["status"]=="active"}
    logged={e["athlete_id"] for e in events if e["type"]=="log_received" and e["at"]>=cutoff}&active
    secs=[e["meta"]["reply_seconds"] for e in events if e["type"]=="reply_sent"];drift=[]
    for a in athletes:
        activity=[e["at"] for e in events if e["athlete_id"]==a["id"] and e["type"] in ("log_received","check_in")]
        last=max(activity) if activity else a["membership_start"]+"T00:00:00+00:00"
        days=(datetime.now(timezone.utc)-datetime.fromisoformat(last)).days
        if a["status"]=="active" and days>=10: drift.append({**a,"days_inactive":days,"last_activity":last})
    median=round(statistics.median(secs)/3600,1) if secs else None
    metrics=dict(active_athletes=len(active),opt_ins=len(active),roster_count=len(athletes),weekly_loggers=len(logged),weekly_logging_rate=round(len(logged)/len(active)*100,1) if active else 0,median_reply_hours=median,replied_within_48h=sum(s<=172800 for s in secs),total_logs=len(logs),total_replies=len(secs),reply_rate=round(len(secs)/len(logs)*100,1) if logs else 0,within_48h_rate=round(sum(s<=172800 for s in secs)/len(logs)*100,1) if logs else 0,unanswered_logs=sum(log["reply"] is None for log in logs),drift=drift,per_coach=[dict(name="Sam",replies=len(secs),median_reply_hours=median)])
    bookings=rows(c,"SELECT b.*,a.name FROM bookings b JOIN athletes a ON a.id=b.athlete_id ORDER BY class_date DESC")
    next_date=c.execute("SELECT MIN(class_date) FROM bookings WHERE class_date>=?",(now()[:10],)).fetchone()[0] or now()[:10]
    result=dict(gym=GYM,athletes=athletes,logs=logs,classes=rows(c,"SELECT * FROM classes"),bookings=bookings,flags=rows(c,"SELECT f.*,a.name FROM flags f JOIN athletes a ON a.id=f.athlete_id"),metrics=metrics,demo=dict(offline=True,parser="deterministic rules, not live AI",voice_transcript=VOICE,next_class_date=next_date,consent_text=CONSENT),messages=[],events=[],concerns=[],brief=brief(c,1,next_date,record=False))
    class_clock=datetime.fromisoformat(next_date+"T19:00:00").replace(tzinfo=ZoneInfo(GYM["timezone"]))
    result["demo"]["nudge_at"]=(class_clock+timedelta(minutes=105)).isoformat()
    sunday=(class_clock+timedelta(days=(6-class_clock.weekday())%7)).replace(hour=18,minute=0)
    result["demo"]["recap_at"]=sunday.isoformat()
    if role=="owner":
        result["messages"]=rows(c,"SELECT m.*,a.name FROM messages m LEFT JOIN athletes a ON a.id=m.athlete_id ORDER BY m.id")
        result["events"]=events[:200];result["concerns"]=rows(c,"SELECT co.*,a.name FROM concerns co JOIN athletes a ON a.id=co.athlete_id ORDER BY co.id DESC")
    return result
