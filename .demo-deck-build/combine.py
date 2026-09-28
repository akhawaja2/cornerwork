from pathlib import Path
s=Path('build-v2.mjs').read_text(encoding='utf-8-sig')
s=s.replace('A CLASS-TO-CLASS COACHING DEMO','CORNERWORK  /  FOUNDING GYM CONVERSATION')
s=s.replace("let s=slide('DEMO'","let s=slide('FOUNDING GYM PROGRAM'")
s=s.replace('LOCAL PROTOTYPE  ·  FICTIONAL ATHLETES','PRODUCT VISION + LOCAL DEMO')
before="""s=slide('THE PROBLEM','Members can drift before anyone notices.',{notes:'Contextualizes the original problem slide without repeating unverified industry percentages. This is the problem hypothesis to discuss, not a measured Cornerwork retention result. Ask for a recent example from the gym.'});
text(s,'A question goes unanswered.',64,267,1120,60,36,c.teal,true);text(s,'A member feels stuck.',64,370,1120,60,36,c.teal,true);text(s,'The next coach never hears about it.',64,473,1120,70,36,c.teal,true);
text(s,'Our hypothesis: better follow-up makes coaching feel more continuous.',64,592,1140,60,25,c.muted);
s=slide('WHAT KEEPS THEM ENGAGED','Help members feel known.',{notes:'Preserves the original human-coaching rationale. Community, progress and accountability are value hypotheses here; we are not claiming a proven retention effect or repeating unsourced survey/injury statistics.'});
text(s,'Continuity',64,260,340,55,35,c.teal,true);text(s,'Someone remembers what I am working on.',456,266,753,76,30,c.dark);
text(s,'Progress',64,383,340,55,35,c.teal,true);text(s,'I know what to focus on next.',456,389,753,76,30,c.dark);
text(s,'Accountability',64,506,360,55,35,c.teal,true);text(s,'My coach checks back with me.',456,512,753,76,30,c.dark);
s=slide('THE GAP','Keep the coaching going after class.',{teal:true,notes:'Replaces the original assertion that gym software only handles billing. Gymdesk already supports notes, tasks and skills; PushPress offers Member Intel. The proposed differentiation is the complete feedback-to-human-response-to-next-class loop, which needs validation. Sources: https://docs.gymdesk.com/en/help/docs/member-profile ; https://docs.gymdesk.com/en/help/docs/skills ; https://www.pushpress.com/features/member-intel'});
text(s,'Collect the question.\\nMake time for a human response.\\nBring the context into the next class.',64,267,1130,236,43,c.cream,true);
text(s,'Designed to work alongside the gym’s booking system.\\nStart in combat sports; test the same loop in other coached activities.',64,558,1140,80,25,c.mint);
"""
s=s.replace("s=slide('THE LOOP'",before+"s=slide('THE LOOP'",1)
start=s.index("s=slide('TECH DETAILS / APPENDIX'")
end=s.index('await (await PresentationFile.exportPptx(p)).save',start)
tech=s[start:end].replace('TECH DETAILS / APPENDIX','TECH DETAILS')
s=s[:start]+s[end:]
s=s.replace("s=slide('INTEGRATION TEST'",tech+"s=slide('INTEGRATION TEST'",1)
after="""s=slide('THE MODEL','A gym subscription. Optional member add-on.',{notes:'Replaces the original $25 member / $10 coach / $5 platform split. $50–100 per gym per month and optional $10 member pricing are hypotheses from the current discussion, not a finalized offer. Scope and usage limits must reflect messaging, transcription, support and integration costs.'});
text(s,'$50–100',64,252,550,104,73,c.teal,true);text(s,'per gym / month',64,366,520,50,31,c.dark,true);text(s,'Proposed platform pricing\\nto test with pilot gyms.',64,441,520,90,27,c.muted);
text(s,'Optional $10',690,262,526,90,50,c.teal,true);text(s,'member add-on / month',690,366,526,60,30,c.dark,true);text(s,'The gym chooses whether\\nto charge members separately.',690,441,526,90,27,c.muted);
text(s,'5–10 members cover the platform fee before coach labor and other costs.',64,587,1140,55,24,c.teal,true);
s=slide('THE COACH’S WORK','Make the work clear before adding the tool.',{notes:'Preserves the original coach-adoption section without promising one hour per week, $150 pay or a 48-hour SLA. Time, compensation and response cadence require agreement with each pilot gym. Measure rather than assume.'});
text(s,'One owner for the queue',64,251,1140,58,34,c.teal,true);text(s,'Decide who responds and who covers an absent coach.',64,318,1140,55,27,c.dark);
text(s,'A realistic response rhythm',64,411,1140,58,34,c.teal,true);text(s,'Agree when replies happen and how that work is paid.',64,478,1140,55,27,c.dark);
text(s,'Measure coach minutes and useful follow-ups during the pilot.',64,585,1140,60,25,c.muted);
s=slide('TRUST / PILOT REQUIREMENTS','Members choose. Coaches stay accountable.',{notes:'Updates the original trust section as pilot requirements, not completed production safeguards. Local consent commands exist, but no real authentication or permission isolation exists. Before live use establish access controls, opt-out handling, data retention and export/deletion policies. Injury information must not be treated as an automated diagnosis. Anonymous/owner dashboard remains out of current scope.'});
text(s,'Opt in, and leave easily.',64,249,1140,55,34,c.teal,true);text(s,'Begin with consenting adults and reliable opt-out handling.',64,310,1140,50,26,c.dark);
text(s,'Human review of advice.',64,404,1140,55,34,c.teal,true);text(s,'Read the original message; raise concerns without diagnosing.',64,465,1140,50,26,c.dark);
text(s,'Before going live: staff permissions, privacy rules and data controls.',64,579,1140,65,25,c.muted);
s=slide('WHO’S BUILDING IT','A fighter who writes software.',{dark:true,notes:'Founder background carried from the user-supplied original pitch deck, not independently verified. Removed the broken founder-photo placeholder rather than inventing a portrait. Original background: nationally ranked Muay Thai fighter, 9-1-1; about ten years of Muay Thai, BJJ and wrestling; senior software engineer in AI and data systems.'});
text(s,'Muay Thai competitor · 9–1–1',64,266,1140,62,37,c.mint,true);text(s,'Around ten years in Muay Thai, BJJ and wrestling.',64,354,1140,73,31,c.cream);text(s,'Senior software engineer working with AI and data systems.',64,458,1140,87,31,c.cream);text(s,'Built from training experience. Refined with working coaches.',64,595,1140,47,25,c.mint);
s=slide('FOUNDING GYM PILOT','Start small. Measure whether it helps.',{notes:'Retains the original founding-gym invitation, reframed as a proposed pilot. No three-month waiver, lifetime rate or live-within-a-week promise is approved. Agree duration, price, scope, delivery and staff responsibility before starting. Small pilots measure usage and feasibility, not causal retention lift.'});
text(s,'START WITH',64,249,525,33,19,c.teal,true);text(s,'One responsible coach\\nA small adult member group\\nOne verified booking connection',64,313,536,192,30,c.dark);
text(s,'LOOK FOR',684,249,532,33,19,c.teal,true);text(s,'Members sharing useful feedback\\nCoaches following up\\nWillingness to keep paying',684,313,532,192,30,c.dark);
text(s,'Agree the offer and service cadence together before a live pilot.',64,577,1140,62,26,c.teal,true);
"""
s=s.replace("s=slide('THE CONVERSATION'",after+"s=slide('THE CONVERSATION'",1)
s=s.replace("root+'/demo-materials/cornerwork-demo-flow-v2.pptx'","root+'/cornerwork-pitch-deck-combined.pptx'")
s=s.replace('explicitTotalSlideCount:10','explicitTotalSlideCount:18').replace('previews-v2','previews-combined').replace('validation-v2.json','validation-combined.json').replace('ten previews','18 previews')
Path('build-combined.mjs').write_text(s,encoding='utf-8')
