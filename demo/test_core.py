"""Behavioral acceptance checks for the credential-free Cornerwork demo."""
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch

class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value = cls(2026, 9, 28, 12, tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)

try:
    from . import core
except ImportError:
    import core


class CoreAcceptance(unittest.TestCase):
    def setUp(self):
        self.clock = patch.object(core, 'datetime', FrozenDateTime)
        self.clock.start()
        self.temp = tempfile.TemporaryDirectory()
        self.conn = core.init_db(str(Path(self.temp.name) / 'demo.sqlite3'))
        core.seed(self.conn)

    def tearDown(self):
        self.conn.close()
        self.temp.cleanup()
        self.clock.stop()

    def snapshot(self, role='owner'):
        return core.state(self.conn, role=role)

    def athlete(self):
        return next(a for a in self.snapshot()['athletes'] if a['status'] == 'active')

    def send(self, athlete, text, **kwargs):
        return core.inbound(self.conn, athlete['phone'], text, **kwargs)

    def test_seed_is_repeatable_and_has_booked_brief(self):
        before = self.snapshot()
        self.assertEqual(len(before['athletes']), 10)
        self.assertTrue(before['logs'])
        self.assertTrue(before['bookings'])
        core.seed(self.conn)
        after = self.snapshot()
        for collection in ('athletes', 'logs', 'bookings', 'messages', 'events'):
            self.assertEqual(len(before[collection]), len(after[collection]), collection)
        self.assertTrue(after['brief'])

    def test_text_and_voice_follow_same_log_pipeline(self):
        athlete = self.athlete()
        for kind in ('text', 'voice'):
            content = 'My jab felt sharper but my left shin is sore after checks.'
            before = len(self.snapshot()['logs'])
            self.send(athlete, content, kind=kind)
            logs = self.snapshot()['logs']
            self.assertEqual(len(logs), before + 1)
            record = max(logs, key=lambda row: row['id'])
            self.assertEqual(record['athlete_id'], athlete['id'])
            self.assertEqual(record['transcript'], content)
            self.assertIn('shin', str(record).lower())
            self.assertIn('jab', str(record).lower())

    def test_duplicate_inbound_does_not_duplicate_log(self):
        athlete = self.athlete()
        before = len(self.snapshot()['logs'])
        for _ in range(2):
            self.send(athlete, 'Worked on jab exits today.', request_id='acceptance-duplicate')
        self.assertEqual(len(self.snapshot()['logs']), before + 1)

    def test_stop_blocks_logs_and_coach_reply(self):
        athlete = self.athlete()
        self.send(athlete, 'Working on jab exits.')
        log = max(self.snapshot()['logs'], key=lambda row: row['id'])
        self.send(athlete, 'STOP')
        stopped = next(a for a in self.snapshot()['athletes'] if a['id'] == athlete['id'])
        self.assertEqual(stopped['status'], 'stopped')
        before = self.snapshot()
        try:
            core.reply(self.conn, log['id'], 'Try a small exit step.')
        except ValueError:
            pass
        try:
            self.send(athlete, 'Here is another session log.')
        except ValueError:
            pass
        after = self.snapshot()
        self.assertEqual(len(after['logs']), len(before['logs']))
        outbound = lambda s: [m for m in s['messages'] if m.get('direction') == 'out' and m.get('athlete_id') == athlete['id']]
        self.assertEqual(len(outbound(after)), len(outbound(before)))

    def test_coach_reply_reaches_correct_athlete_once(self):
        athlete = self.athlete()
        self.send(athlete, 'Working on clinch entries.')
        log = max(self.snapshot()['logs'], key=lambda row: row['id'])
        before = len(self.snapshot()['messages'])
        for _ in range(2):
            core.reply(self.conn, log['id'], 'Keep the entry controlled.', request_id='same-reply')
        added = self.snapshot()['messages'][before:]
        matching = [m for m in added if 'Keep the entry controlled.' in m.get('body', '')]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0]['athlete_id'], athlete['id'])

    def test_concern_is_not_visible_in_coach_payload(self):
        athlete = self.athlete()
        marker = 'private-marker-726'
        self.send(athlete, f'My coach is harassing me. {marker}')
        self.assertNotIn(marker, str(self.snapshot('coach')))
        self.assertIn(marker, str(self.snapshot('owner')))

    def test_jobs_are_idempotent(self):
        clock = '2026-10-04T18:00:00-04:00'
        core.jobs(self.conn, clock)
        before = self.snapshot()
        core.jobs(self.conn, clock)
        after = self.snapshot()
        self.assertEqual(len(after['messages']), len(before['messages']))
        self.assertEqual(len(after['events']), len(before['events']))




    def test_join_requires_explicit_adult_confirmation(self):
        phone = '+12025550991'
        core.inbound(self.conn, phone, 'JOIN')
        athlete = next(a for a in self.snapshot()['athletes'] if a['phone'] == phone)
        self.assertNotEqual(athlete['status'], 'active')
        before = len(self.snapshot()['logs'])
        core.inbound(self.conn, phone, 'Practiced jab today.')
        self.assertEqual(len(self.snapshot()['logs']), before)
        core.inbound(self.conn, phone, 'YES 18')
        athlete = next(a for a in self.snapshot()['athletes'] if a['phone'] == phone)
        self.assertEqual(athlete['status'], 'active')
        core.inbound(self.conn, phone, 'STOP')
        athlete = next(a for a in self.snapshot()['athletes'] if a['phone'] == phone)
        self.assertEqual(athlete['status'], 'stopped')

    def test_stopped_athlete_receives_no_scheduled_messages(self):
        athlete = self.athlete()
        self.send(athlete, 'STOP')
        count = lambda: sum(m.get('direction') == 'out' and m.get('athlete_id') == athlete['id'] for m in self.snapshot()['messages'])
        before = count()
        core.jobs(self.conn, '2026-10-04T18:00:00-04:00')
        self.assertEqual(count(), before)





    def test_roster_reimport_updates_without_duplicates_or_consent(self):
        csv_text = 'name,phone,membership_start\nNew Adult,+12025550992,2026-09-01\n'
        before = len(self.snapshot()['athletes'])
        core.import_csv(self.conn, 'athletes', csv_text)
        core.import_csv(self.conn, 'athletes', csv_text.replace('New Adult', 'Renamed Adult'))
        after = self.snapshot()['athletes']
        self.assertEqual(len(after), before + 1)
        athlete = next(a for a in after if a['phone'] == '+12025550992')
        self.assertEqual(athlete['name'], 'Renamed Adult')
        self.assertNotEqual(athlete['status'], 'active')

    def test_csv_invalid_phone_does_not_create_member(self):
        before = len(self.snapshot()['athletes'])
        with self.assertRaises(ValueError):
            core.import_csv(self.conn, 'athletes', 'name,phone,membership_start\nBad Phone,nope,2026-09-01\n')
        self.assertEqual(len(self.snapshot()['athletes']), before)



    def test_bookings_import_is_idempotent_and_controls_brief(self):
        data = self.snapshot()
        athlete = self.athlete()
        class_id = data['classes'][0]['id']
        date = '2026-12-10'
        csv_text = f'phone,class_id,class_date,status\n{athlete["phone"]},{class_id},{date},booked\n'
        core.import_csv(self.conn, 'bookings', csv_text)
        count = len(self.snapshot()['bookings'])
        core.import_csv(self.conn, 'bookings', csv_text)
        self.assertEqual(len(self.snapshot()['bookings']), count)
        brief = core.brief(self.conn, class_id, date)
        self.assertEqual(len(brief['athletes']), 1)
        self.assertIn(athlete['name'], str(brief['athletes']))
        self.assertEqual(core.brief(self.conn, class_id, '2026-12-11')['athletes'], [])

    def test_registered_coach_requires_target_and_routes_explicit_id(self):
        data = self.snapshot()
        coach_phone = data['gym']['coach_phone']
        athletes = [a for a in data['athletes'] if a['status'] == 'active'][:2]
        for athlete in athletes:
            self.send(athlete, 'Clinch entries were improving.')
        previous = self.snapshot()
        try:
            core.inbound(self.conn, coach_phone, 'untargeted-marker-26')
        except ValueError:
            pass
        self.assertFalse(any(m.get('direction') == 'out' and m.get('athlete_id') is not None and 'untargeted-marker-26' in m.get('body', '') for m in self.snapshot()['messages']))
        target = athletes[0]
        core.inbound(self.conn, coach_phone, f'#{target["id"]} explicit-target-marker-26')
        sent = [m for m in self.snapshot()['messages'] if m.get('direction') == 'out' and 'explicit-target-marker-26' in m.get('body', '')]
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['athlete_id'], target['id'])




    def test_consent_records_original_commands_and_timestamp(self):
        phone = '+12025550993'
        for body in ('join', 'YES 18', 'STOP'):
            core.inbound(self.conn, phone, body)
        athlete = next(a for a in self.snapshot()['athletes'] if a['phone'] == phone)
        records = self.conn.execute('SELECT * FROM consents WHERE athlete_id=? ORDER BY id', (athlete['id'],)).fetchall()
        self.assertEqual([r['action'] for r in records], ['join_requested', 'join', 'stop'])
        self.assertEqual(records[0]['raw_message'], 'join')
        self.assertIn('YES 18', records[1]['raw_message'])
        self.assertIn('Cornerwork', records[1]['raw_message'])
        self.assertEqual(records[2]['raw_message'], 'STOP')
        from datetime import datetime
        for record in records:
            self.assertIsNotNone(datetime.fromisoformat(record['at']).tzinfo)

    def test_nudge_due_time_quiet_hours_no_show_and_daily_cap(self):
        athlete = self.athlete()
        second = [a for a in self.snapshot()['athletes'] if a['status'] == 'active'][1]
        csv_text = f'phone,class_id,class_date,status\n{athlete["phone"]},1,2026-12-10,attended\n{second["phone"]},1,2026-12-10,no_show\n'
        core.import_csv(self.conn, 'bookings', csv_text)
        self.assertEqual(core.jobs(self.conn, '2026-12-10T20:44:00-05:00')['sent'], 0)
        self.assertEqual(core.jobs(self.conn, '2026-12-10T20:45:00-05:00')['sent'], 1)
        self.assertEqual(core.jobs(self.conn, '2026-12-10T21:45:00-05:00')['sent'], 0)
        events = [e for e in self.snapshot()['events'] if e['type'] == 'nudge_sent']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['athlete_id'], athlete['id'])
        core.import_csv(self.conn, 'bookings', csv_text.replace('2026-12-10', '2026-12-11'))
        self.assertEqual(core.jobs(self.conn, '2026-12-11T22:00:00-05:00')['sent'], 0)

    def test_seed_dashboard_numbers_are_hand_checked(self):
        metrics = self.snapshot()['metrics']
        self.assertEqual(metrics['active_athletes'], 8)
        self.assertEqual(metrics['weekly_loggers'], 6)
        self.assertEqual(metrics['weekly_logging_rate'], 75.0)
        self.assertEqual(metrics['total_logs'], 25)
        self.assertEqual(metrics['total_replies'], 19)
        self.assertEqual(metrics['median_reply_hours'], 10.0)
        self.assertEqual(metrics['reply_rate'], 76.0)
        self.assertEqual([a['id'] for a in metrics['drift']], [7])

    def test_head_injury_has_referral_and_immediate_coach_alert(self):
        athlete = self.athlete()
        self.send(athlete, 'I felt dizzy after a head hit during sparring.')
        state = self.snapshot()
        record = max(state['logs'], key=lambda row: row['id'])
        self.assertTrue(record['concussion_flag'])
        self.assertTrue(any(e['type'] == 'coach_alert' and e['athlete_id'] == athlete['id'] for e in state['events']))
        outbound = [m for m in state['messages'] if m['direction'] == 'out' and m['athlete_id'] == athlete['id']]
        self.assertIn('medical evaluation', outbound[-1]['body'])

    def test_weekly_recaps_fit_sms_contract(self):
        before = {m['id'] for m in self.snapshot()['messages']}
        result = core.jobs(self.conn, '2026-10-04T18:00:00-04:00')
        self.assertGreater(result['sent'], 0)
        sent = [m for m in self.snapshot()['messages'] if m['id'] not in before and m['direction'] == 'out']
        self.assertTrue(sent)
        self.assertTrue(all(len(m['body']) <= 320 for m in sent))



    def test_invalid_second_csv_row_rolls_back_first(self):
        before = self.snapshot()
        csv_text = 'name,phone,membership_start\nValid New,+12025550888,2026-09-01\nInvalid,nope,2026-09-01\n'
        with self.assertRaises(ValueError):
            core.import_csv(self.conn, 'athletes', csv_text)
        self.assertEqual(self.snapshot()['athletes'], before['athletes'])
        self.assertEqual(self.snapshot()['events'], before['events'])

    def test_quiet_hours_recap_is_deferred_until_permitted(self):
        self.assertEqual(core.jobs(self.conn, '2026-10-04T07:59:00-04:00')['sent'], 0)
        self.assertEqual(core.jobs(self.conn, '2026-10-04T22:00:00-04:00')['sent'], 0)
        self.assertGreater(core.jobs(self.conn, '2026-10-04T18:00:00-04:00')['sent'], 0)



    def test_recap_contains_actual_coach_note(self):
        athlete = self.athlete()
        self.send(athlete, 'Jab exits clicked today.')
        record = max(self.snapshot()['logs'], key=lambda row: row['id'])
        core.reply(self.conn, record['id'], 'Remember the small outside step.')
        before = {m['id'] for m in self.snapshot()['messages']}
        core.jobs(self.conn, '2026-10-04T18:00:00-04:00')
        sent = [m for m in self.snapshot()['messages'] if m['id'] not in before and m['athlete_id'] == athlete['id']]
        self.assertEqual(len(sent), 1)
        self.assertIn('Remember the small outside step.', sent[0]['body'])
        self.assertLessEqual(len(sent[0]['body']), 320)

    def test_imported_checkin_uses_class_local_time(self):
        athlete = self.athlete()
        core.import_csv(self.conn, 'bookings', f'phone,class_id,class_date,status\n{athlete["phone"]},1,2026-12-10,attended\n')
        event = next(e for e in self.snapshot()['events'] if e['type'] == 'check_in' and e['meta'].get('date') == '2026-12-10')
        self.assertEqual(event['at'], '2026-12-11T00:00:00+00:00')


if __name__ == '__main__':
    unittest.main()
