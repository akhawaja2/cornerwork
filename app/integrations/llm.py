"""LLM boundary. Two implementations behind one interface:
- FakeLLM: deterministic keyword rules (DEMO_MODE=1 or no ANTHROPIC_API_KEY). Offline, free, used in tests.
- ClaudeLLM: Anthropic SDK with structured outputs, validated by Pydantic, one retry.
safety_check() runs on every parse regardless of backend and is the last word on injury/concussion flags."""
import os
import re
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

PROMPTS = Path(__file__).resolve().parents[1] / "prompts"
REFERRAL = "If it persists or gets worse, please see a medical professional before your next session."
CONCUSSION_LINE = "Please get checked by a medical professional before training again; head knocks are not something to push through."


class Injury(BaseModel):
    area: str = Field(description="Body part in the athlete's words, e.g. 'left shin'")
    severity: Literal["minor", "moderate", "serious", "unknown"] = "unknown"
    quote: str = Field(description="The athlete's exact words about it")


class ParsedLog(BaseModel):
    summary: str = Field(description="At most two sentences, athlete's own words where possible")
    techniques: list[str] = Field(default_factory=list, description="Short lowercase phrases the athlete worked on")
    sentiment: Literal["pos", "neutral", "neg"]
    injury: Optional[Injury] = None
    concussion_flag: bool = False
    coach_draft: str = Field(description="1-2 sentence suggested reply the coach can edit")


class BriefNote(BaseModel):
    athlete: str
    note: str


class BriefOut(BaseModel):
    focus: str
    notes: list[BriefNote] = Field(default_factory=list)


# --- deterministic fake -------------------------------------------------------------------------
TECHNIQUES = ["jab", "cross", "hook", "uppercut", "clinch", "footwork", "guard pass", "guard", "roundhouse", "teep", "sparring",
              "defense", "slip", "counter", "takedown", "sweep", "armbar", "sprawl", "check", "knee", "elbow", "pad", "kick"]
CONCUSSION = re.compile(r"\b(concussion|head|dizzy|dizziness|blackout|blacked out|knocked out|headache|nause\w*|blurry|foggy|seeing stars)\b")
INJURY_WORDS = re.compile(r"\b(sore|pain|hurts?|injur\w*|swollen|swelling|tweak\w*|strain\w*|sprain\w*|pulled|bruis\w*|hyperextend\w*)\b")
AREAS = ["shin", "knee", "ankle", "shoulder", "wrist", "head", "neck", "back", "elbow", "hand", "rib", "hip", "foot", "toe", "finger",
         "nose", "jaw", "eye", "thumb", "calf", "hamstring", "groin"]
NEG = re.compile(r"\b(frustrat\w*|struggl\w*|stuck|quit|bad day|terrible|annoy\w*|gassed|nothing worked|might skip|nauseous)\b")
POS = re.compile(r"\b(better|sharper|clicked|great|good|excellent|fun|landed|landing|finally|love\w*|felt good)\b")


class FakeLLM:
    model = "fake-rules"

    def parse_log(self, transcript: str, goal: str, last_summaries: list[str]) -> ParsedLog:
        low = transcript.lower()
        techniques = [t for t in TECHNIQUES if re.search(r"\b" + re.escape(t) + r"s?\b", low)]
        concussion = bool(CONCUSSION.search(low))
        injury = None
        if concussion or INJURY_WORDS.search(low):
            area = "head" if concussion else next((a for a in AREAS if re.search(r"\b" + a + r"s?\b", low)), "unspecified")
            injury = Injury(area=area, severity="unknown", quote=transcript.strip()[:200])
        sentiment = "neg" if NEG.search(low) else ("pos" if POS.search(low) else "neutral")
        if concussion:
            draft = CONCUSSION_LINE + " Let me know how you feel tomorrow."
        elif injury:
            draft = f"Thanks for flagging the {injury.area}. Rest it and we will adjust drills next class. {REFERRAL}"
        elif techniques:
            draft = f"Nice work on the {techniques[0]}. Next class we will drill it together; keep logging."
        else:
            draft = "Thanks for the update. Let's check in before your next class."
        return ParsedLog(summary=transcript.strip()[:220], techniques=techniques, sentiment=sentiment, injury=injury,
                         concussion_flag=concussion, coach_draft=draft)

    def build_brief(self, class_name: str, class_date: str, athletes: list[dict], themes: list[dict]) -> BriefOut:
        focus = (f"Revisit {themes[0]['name']} with the group; check flags first." if themes
                 else "Check in individually before class; ask what each athlete wants to work on.")
        notes = [BriefNote(athlete=a["name"], note=f"Ask about: {a['flags'][0]['detail'] or a['flags'][0]['type']}")
                 for a in athletes if a.get("flags")]
        return BriefOut(focus=focus, notes=notes)


# --- Claude ---------------------------------------------------------------------------------------
class ClaudeLLM:
    def __init__(self, model: str | None = None):
        import anthropic  # imported lazily so the fake path never needs the SDK
        self.client = anthropic.Anthropic()
        self.model = model or os.environ.get("LLM_MODEL", "claude-opus-5-5")

    def _parse(self, system: str, user: str, schema):
        last = None
        for attempt in range(2):  # retry once on an invalid/refused response
            response = self.client.messages.parse(
                model=self.model, max_tokens=2000, system=system,
                messages=[{"role": "user", "content": user}], output_format=schema,
            )
            if response.stop_reason == "refusal":
                last = RuntimeError(f"model refused: {response.stop_details and response.stop_details.category}")
                continue
            if response.parsed_output is not None:
                return response.parsed_output
            last = RuntimeError(f"no parsed output (stop_reason={response.stop_reason})")
        raise last

    def parse_log(self, transcript: str, goal: str, last_summaries: list[str]) -> ParsedLog:
        system = (PROMPTS / "parse_log.md").read_text(encoding="utf-8")
        user = (f"Athlete goal: {goal or '(none stated)'}\n"
                f"Earlier summaries: {' | '.join(last_summaries) if last_summaries else '(none)'}\n\n"
                f"Log:\n{transcript}")
        return self._parse(system, user, ParsedLog)

    def build_brief(self, class_name: str, class_date: str, athletes: list[dict], themes: list[dict]) -> BriefOut:
        system = (PROMPTS / "class_brief.md").read_text(encoding="utf-8")
        lines = [f"Class: {class_name} on {class_date}", f"Themes: {', '.join(t['name'] + ' x' + str(t['count']) for t in themes) or '(none)'}"]
        for a in athletes:
            flags = "; ".join(f"{f['type']}: {f['detail']}" for f in a.get("flags", [])) or "none"
            lines.append(f"- {a['name']} ({a['booking_status']}): flags: {flags}. Recent logs: {' | '.join(a.get('summaries', [])) or 'none'}")
        return self._parse(system, "\n".join(lines), BriefOut)


def get_llm():
    if os.environ.get("DEMO_MODE") == "1" or not os.environ.get("ANTHROPIC_API_KEY"):
        return FakeLLM()
    return ClaudeLLM()


# --- safety post-check (runs on every parse) ------------------------------------------------------
def safety_check(transcript: str, parsed: ParsedLog) -> ParsedLog:
    """Keyword floor under the model: head/dizzy/etc always flags; injury words always produce an injury;
    drafts on flagged logs always carry the referral line and never say to train through it."""
    low = transcript.lower()
    if CONCUSSION.search(low):
        parsed.concussion_flag = True
        if not parsed.injury:
            parsed.injury = Injury(area="head", severity="unknown", quote=transcript.strip()[:200])
    elif INJURY_WORDS.search(low) and not parsed.injury:
        area = next((a for a in AREAS if re.search(r"\b" + a + r"s?\b", low)), "unspecified")
        parsed.injury = Injury(area=area, severity="unknown", quote=transcript.strip()[:200])
    if parsed.concussion_flag and "medical" not in parsed.coach_draft.lower():
        parsed.coach_draft = CONCUSSION_LINE + " " + parsed.coach_draft
    elif parsed.injury and "medical" not in parsed.coach_draft.lower():
        parsed.coach_draft = parsed.coach_draft.rstrip() + " " + REFERRAL
    if parsed.injury and re.search(r"\b(push through|train through|work through the pain|keep going on it)\b", parsed.coach_draft.lower()):
        parsed.coach_draft = f"Thanks for flagging the {parsed.injury.area}. Rest it and we will adjust drills next class. {REFERRAL}"
    return parsed


def edit_distance(a: str, b: str) -> int:
    """Levenshtein distance. ponytail: O(len(a)*len(b)) is fine for 1600-char replies."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
