import json
from pathlib import Path
from collections import Counter
base=Path(r'C:\Users\Abu\Documents\Python\CornerWork\research')
assumptions=[
'Persona: founder. Stage: validation with a demo, not demonstrated product-market fit. Artifact: strategy research JSON. Decision: recommend bounded experiments, not a build commitment.',
'APP_CONTEXT is the conversation: attendance-triggered member feedback, voice notes, coach replies and pre-class briefs; $50-100/location/month hypothesis; eventual expansion beyond combat sports. Fighter contacts exist but reach and commercial commitments are unknown.',
'RESEARCH_BUNDLE is the sourced 2026-09-28-moat-strategy-frameworks.md report and primary pages cited in the insights. This skill run synthesizes that bundle; it is not a fresh comprehensive market search or customer interview study.',
'The user rejected passports, payouts, matchmaking and fighter-led programme distribution as compelling answers. They are not recommended here. Prior recommendations are hypotheses, not evidence.',
'Probability values are normalized exploratory portfolio weights required by this skill, NOT statistical odds of success. The skill caps every value below 0.15 without defining an event or calibration. Scores and time horizons are subjective conditional estimates, not measured facts.',
'No customer data, paid retention, exclusive contracts, approved API access or proprietary training corpus has been demonstrated. Outcomes research, expert review, data rights and partner demand remain unvalidated.',
'Metric targets are proposed experiment gates, not industry benchmarks. Small initial samples assess feasibility; they cannot prove retention effects or clinical safety.',
'Low cost means a founder-led manual test; medium means sustained engineering or paid specialist input; high means multi-site research, substantial integration or enterprise delivery. No dollar budget has been agreed.',
'The skill mandates 10 candidates and exactly three recommendations. These are sequenced options, not ten projects to build. No defensible moat is established for the current product.',
'No medical advice, injury clearance, exercise-safety certification or automated clinical assessment is included. A coaching-quality benchmark cannot certify medical safety.'
]
raw_insights=[
('The proposed demo has access to feedback immediately after class and before the next class.','APP_CONTEXT: user-defined attendance -> member voice/text -> coach queue -> next-class brief.','That timing supports testing intervention effectiveness rather than only storing conversations.'),
('Pre-class member context already exists in incumbent products.','PushPress Member Intel: https://www.pushpress.com/features/member-intel','A roster summary is a weak independent reason for long-term preference.'),
('Human-reviewed AI coaching workflows already exist.','Everfit Olly check-in documentation: https://help.everfit.io/en/articles/15393086-olly-on-check-in-dashboard-beta','Generic AI drafting and coach approval are not differentiated assets.'),
('A platform has acquired a complementary coaching-data and check-in tool.','ABC FitMetrics announcement, 2026-09-03: https://abcfitness.com/press-release/ai-agents-fitmetrics/','A component business is plausible, but the announcement does not establish purchase rationale, price or demand for Cornerwork.'),
('Gymdesk already stores member context and skill progression.','https://docs.gymdesk.com/en/help/docs/member-profile and https://docs.gymdesk.com/en/help/docs/skills','Record accumulation alone does not establish a learning advantage over Gymdesk.'),
('The proposed per-location price leaves little room for bespoke service.','APP_CONTEXT $50-100/month; prior report explicitly illustrative $75 minus $15 variable cost and $15 partner share leaves $45 before support.','Reusable delivery and lower support costs are necessary; expensive enterprise delivery needs different pricing.'),
('Incumbents already use education partnerships for distribution.','ABC/IPTA partnership announcement: https://abcfitness.com/press-release/abc-fitness-ipta-partnership/','Access to an educator is not structurally protected; do not rename referrals a moat.'),
('Repeated structured check-ins are already a product capability elsewhere.','Trainerize forms: https://help.trainerize.com/hc/en-us/articles/31369316335124-Sharing-Check-In-Forms-with-Clients','A new schema is insufficient; useful experimental labels or superior decisions must be demonstrated.'),
('The founder wants applicability outside combat sports.','APP_CONTEXT: explicit user requirement to extend beyond combat sports.','Prioritize general coaching operations while validating sport-specific transfer rather than assuming it.'),
('The current evidence contains no demonstrated customer outcome advantage.','Research bundle evidence limits: 2026-09-28-moat-strategy-frameworks.md; no field study was conducted.','Any efficacy, demand or switching-cost claim needs a prospective test.'),
('Platform dependence can threaten an add-on product.','APP_CONTEXT explicitly requires Mindbody and Gymdesk integrations; bundle identifies access and event reliability as unresolved.','Embedding as a supplier may change the commercial relationship, but does not remove buyer concentration or access risk.'),
('Fighter relationships are available but no distribution contract is established.','APP_CONTEXT: user says they know famous fighters; no signed rights or committed gym buyers supplied.','These contacts may recruit expert evaluators and pilot participants without assuming endorsements are a moat.')
]
insights=[dict(id=f'I{i}',insight=a,evidence=b,implication=c) for i,(a,b,c) in enumerate(raw_insights,1)]
S=[]
def add(title,typ,contra,mechanism,refs,now,nxt,later,pre,metrics,risks,time,cost,score,why,p):
 S.append(dict(title=title,moat_type=typ,contrarian=contra,mechanism=mechanism,research_link=refs,implementation_plan=dict(now_30d=now,next_90d=nxt,next_12m=later),prerequisites=pre,metrics=[dict(name=n,target=t) for n,t in metrics],risks_and_mitigations=[dict(risk=r,mitigation=m) for r,m in risks],time_to_moat=time,estimated_cost=cost,defensibility_score=score,defensibility_justification=why,probability=p))
add('Learn which follow-up actually helps','data moat',False,
'Accumulate permissioned evidence linking a specific coaching follow-up to a defined result. The asset is comparative intervention evidence, not transcript volume. A competitor can copy reminders but must reproduce useful experiments; it may still do so faster. Start with response and follow-up completion, then test attendance or retention only with sufficient study design.',
['I1','I5','I8','I10'],
['Select one nonclinical problem, such as an unanswered beginner question.','Define eligible cases, coach-approved follow-up variants and a fixed outcome window.','Secure pilot consent and collect a baseline without claiming effectiveness.'],
['Log assignment, actual delivery, coach edits and observed outcome separately.','With qualified study-design input, randomize acceptable variants where feasible; otherwise label results observational.','Assess follow-up completion and coach time, with missing outcomes reported.'],
['Estimate required sample sizes before testing retention or subgroup claims.','Replicate useful findings across gyms and one adjacent activity.','Evaluate whether accumulated evidence outperforms a simple rules baseline on unseen gyms.'],
['Active gym pilots','Permission to use appropriately scoped data','Sufficient eligible observations','Study-design expertise'],
[('Outcome linkage','At least 90% of pilot cases link the assigned action to delivery status and observation window.'),('Member burden','No more than one extra outcome question per eligible follow-up.'),('Useful learning','One pre-specified decision changes after analysis and is prospectively retested.')],
[('Selection bias','Separate randomized estimates from observational correlations.'),('Sparse or misleading outcomes','Use a narrow observable outcome first; disclose missingness and uncertainty.'),('Incumbent data advantage','Test unseen-gym performance; abandon a data-moat claim without measured lift.')],
'24+ months','high',7,'Conditional on repeatable decision improvement and lawful continued data access; raw logs alone score poorly.',.14)
add('Build a coaching-quality test suite competitors lack','IP/know-how',False,
'Create a permissioned, expert-adjudicated set of difficult coaching communication cases and a reliable review process. Use it to detect context errors, unsupported certainty, missed follow-ups and inappropriate replies. The defensible asset could be validated cases plus accumulated adjudication know-how, not prompts or famous names.',
['I1','I3','I9','I12'],
['Recruit two qualified coaches through existing contacts; pay for review if needed.','Write a rubric for context fidelity, useful next action and appropriate escalation to a human.','Independently label 40 consented/de-identified or clearly synthetic pilot cases; keep synthetic provenance explicit.'],
['Resolve disagreements and revise ambiguous rubric definitions.','Compare a generic AI draft, a simple rule-based workflow and the candidate system on held-out cases.','Record failure families and test whether fixes generalize without exposing test answers.'],
['Expand real-world failure coverage only as pilots supply legitimate cases.','Add reviewers from a second activity and measure transfer separately.','Maintain a private holdout while publishing methods and limitations to prospective buyers.'],
['Available expert reviewers','Rights to benchmark material','Separate development and held-out cases'],
[('Review consistency','At least 80% agreement on the agreed binary acceptance decision in the initial exercise; report chance-adjusted agreement too.'),('Coverage','At least 5 distinct recurring error categories with provenance.'),('Incremental quality','Pre-specified held-out improvement over a generic baseline without increased coach review time.')],
[('Subjective labels','Use independent review and adjudication; revise the rubric before expanding.'),('Benchmark gaming','Keep a held-out set and introduce new cases prospectively.'),('False safety claim','Scope to communication/workflow quality, never medical clearance or certified exercise safety.')],
'12-24 months','medium',6,'A rubric is copyable; difficult legitimate cases and a validated expert process may take time to reproduce. Expertise access alone is insufficient.',.14)
add('Sell the coaching component to other software companies','ecosystem/platform',True,
'Offer an embeddable coach queue, brief and follow-up engine to smaller gym software vendors that prefer purchasing to maintaining it. Their customers use their existing app; Cornerwork supplies the component. Multiple production contracts and operational dependence could create switching costs. This is a different buyer and pricing model, not a cosmetic API wrapper.',
['I2','I3','I4','I6','I11'],
['Identify five reachable smaller vendors or existing integration developers from actual introductions.','Show the existing demo as an embeddable component concept, explicitly unbuilt.','Ask which coaching requests they lose deals over and what they already buy from suppliers.'],
['Seek one paid design agreement with defined scope before building a full SDK.','Prototype one bounded integration using explicit permitted data access.','Measure vendor engineering effort, operator adoption and support load.'],
['Standardize the component only after a production design partner uses it.','Add a second vendor and document migration/export support rather than trapping customers.','Develop commercial reliability commitments only after measuring operational capability.'],
['A vendor with a real unmet need and budget','Production security and support capability','Commercial terms covering data and responsibilities'],
[('Buyer evidence','At least 2 of 5 vendor interviews identify the same funded gap.'),('Commercial commitment','At least 1 paid design partner before broad SDK investment.'),('Repeatability','Second deployment requires less than half the engineering time of the first.')],
[('Vendors simply build it','Require a paid buy-versus-build decision before major investment.'),('One buyer dominates revenue','Seek a second deployment; do not promise customer-independent economics prematurely.'),('Enterprise work exceeds capacity','Time-box discovery and stop if service obligations exceed founder capacity or available financing.')],
'12-24 months','high',6,'Production embed and proven operations can delay replacement. The generic component remains copyable; acquisition precedent is not proof of OEM demand.',.14)
add('Make personalized follow-up unusually cheap to deliver','scale economies',True,
'Learn how to turn repeated class questions into reusable coach-reviewed responses while routing exceptions for individual attention. A durable advantage would require declining cost per useful response as deployment grows, without lower quality. Mere caching or AI summaries are not economies of scale.',
['I1','I3','I6'],
['Measure coach minutes per resolved question in one pilot.','Identify genuinely repeated questions without merging distinct member contexts.','Manually test one batch response with coach-approved individual exceptions.'],
['Compare total staff effort and response usefulness with the original workflow.','Automate only the recurring step with demonstrated savings.','Record exception types and revise routing with human oversight.'],
['Test whether shared implementation learning lowers cost across new sites.','Verify savings after support and onboarding labour.','Price against demonstrated delivery economics rather than assuming a subsidy.'],
['Repeatable questions','Coach participation','Cost and quality measurement'],
[('Labour efficiency','At least 25% lower median staff minutes per resolved case in a bounded paired pilot.'),('Quality','No drop on the pre-specified blinded usefulness rubric.'),('Scalability','Support minutes per location decline across successive deployment cohorts.')],
[('Generic answers hurt members','Require context checks and retain individual handling.'),('Simple batching is easily copied','Call it efficiency until cross-site cost advantages are measured.'),('Founder labour is hidden','Include review, setup and support time in costs.')],
'12-24 months','medium',4,'Cost learning could compound, but larger vendors may have stronger scale and easy access to the same automation.',.12)
add('Become the handoff record for unresolved coaching work','switching costs',False,
'Maintain explicit ownership, due dates and resolutions for coaching commitments across rotating staff. The asset is an adopted operating process with open cases, rather than a pile of notes. This overlaps the earlier memory concept and is retained as a comparator, not presented as a new breakthrough.',
['I1','I2','I5'],
['Observe three real coach changes and missed follow-ups.','Define one owner and due class for each open case.','Test a minimal handoff list alongside existing tools.'],
['Measure voluntary use without founder reminders.','Resolve ownership conflicts and missing-attendance cases.','Provide complete export and test restoring the working list.'],
['Expand only into workflows staff demonstrably rely on.','Measure renewal and replacement effort in customer interviews.','Assess whether incumbent features erase the operational advantage.'],
['Multiple coaches sharing members','Recurring missed commitments','Owner willing to change process'],
[('Habit','Brief consulted voluntarily before at least 60% of eligible pilot classes.'),('Completion','At least 70% of due follow-ups resolved by agreed deadline.'),('Retention','At least 2 of 3 pilot sites renew at agreed price.')],
[('Adds administration','Track total staff time, not app activity.'),('Incumbent replicates workflow','Compare against available native tools before expanding.'),('Artificial lock-in','Preserve usable exports; rely on value and habit.')],
'6-12 months','low',4,'Adoption adds friction to replacement but most records and workflow concepts are portable and reproducible.',.11)
add('Independent cross-platform coaching benchmarks','data moat',False,
'Create comparable nonclinical operational measures across booking systems, such as question-to-reply time and due-follow-up completion. A buyer might value a sufficiently representative reference dataset unavailable within one vendor. No comparative benchmark is credible with a few unrepresentative gyms.',
['I6','I9','I10','I11'],
['Ask five operators which comparative decision they cannot make today.','Define denominators and reporting periods before collecting data.','Test a synthetic report and willingness to pay without claiming real benchmarks.'],
['Collect permissioned operational metrics from willing sites.','Assess missingness and differences in class and staffing models.','Publish only own-site trends until cohort disclosure thresholds are justified.'],
['Recruit enough comparable sites for defensible cohorts.','Validate measures across providers and activities.','Sell only reports linked to an actual management decision.'],
['Sufficient representative sites','Aggregation permissions','Comparable definitions'],
[('Demand','At least 3 of 5 operators identify a recurring decision the report would change.'),('Comparability','At least 90% completeness for agreed denominators.'),('Purchase','At least 2 buyers pay for a bounded reporting pilot.')],
[('Misleading rankings','Stratify comparable settings and show uncertainty.'),('Re-identification','Use justified aggregation and suppression rules.'),('Incumbent has more data','Test whether cross-provider coverage actually changes a decision.')],
'24+ months','high',5,'Cross-provider coverage could differentiate, but sufficient scale, access and useful buying demand are all missing.',.07)
add('Become the trusted evaluator of AI coaching tools','brand',True,
'Build a reputation from transparent, reproducible comparisons of coaching workflow tools, including Cornerwork failures. Trust might drive buyer preference. This is distinct from a private test suite: it requires independent governance and public credibility, which can conflict with selling the product being rated.',
['I3','I9','I10'],
['Publish a transparent proposed evaluation rubric, not rankings.','Invite independent reviewers to challenge it.','Disclose the conflict of interest from operating Cornerwork.'],
['Run a reproducible comparison on permissioned or synthetic cases.','Publish limitations and corrections.','Measure whether buyers use the work in actual selection.'],
['Separate evaluation governance from sales if demand supports it.','Replicate in a second activity with qualified reviewers.','Track repeat reliance by independent buyers.'],
['Independent reviewers','Reproducibility','Willingness to disclose weaknesses'],
[('External challenge','At least 3 independent reviewers critique the method.'),('Decision influence','At least 2 buyers cite the evaluation in a documented decision.'),('Repeat trust','At least 2 organizations return for a subsequent evaluation.')],
[('Self-serving marketing','Disclose conflicts and preserve independent review.'),('Attention without revenue','Track purchasing decisions rather than views.'),('Overbroad claims','Restrict claims to tested cases and capabilities.')],
'24+ months','medium',4,'Credibility develops slowly and is fragile; brand awareness alone does not protect the product.',.06)
add('Reach gyms through implementation consultants','distribution moat',False,
'Equip consultants who already configure gym software with a repeatable paid setup for the coaching workflow. Could reduce acquisition friction, but absent privileged access or repeatable partner economics this is ordinary distribution. Different intermediary from celebrity endorsement; still not recommended as an assumed moat.',
['I6','I7','I11'],
['Identify three consultants through verified public services or introductions.','Ask about recurring post-class workflow requests and current solutions.','Offer a manual installation playbook concept before building partner tooling.'],
['Test one paid referral with disclosed commercial terms.','Measure customer acquisition and support cost including commission.','Document the installation so another consultant can repeat it.'],
['Track repeat referrals independent of founder involvement.','Train a second consultant only after profitable conversions.','Negotiate actual commercial commitments where mutually useful.'],
['Consultants with relevant clients','Affordable support','Clear commercial terms'],
[('Channel demand','At least 2 consultants identify a real customer request.'),('Conversion','At least 1 paid customer from a partner introduction.'),('Repeatability','Partner brings a second paid customer without bespoke product work.')],
[('Partner sells incumbent alternative','Test actual preference, not enthusiasm.'),('Commission eliminates margin','Model contribution after full service costs.'),('Channel concentration','Keep direct customer learning and a second source of demand.')],
'12-24 months','low',3,'A useful route to customers; difficult to protect without scarce access and demonstrated repeat economics.',.06)
add('Shared library of proven coach-created responses','community',False,
'Coaches contribute adaptations to recurring teaching problems and earn recognition when peers find them useful. A trusted contributor community could accumulate valuable material. This is not simply licensing fighter content and is not a network effect until additional contributors improve others\' results.',
['I1','I8','I9','I12'],
['Ask five coaches to contribute one permissioned nonclinical teaching example.','Test whether another coach actually reuses it.','Document attribution, scope and the right to remove contributions.'],
['Moderate quality and separate opinions from observed results.','Track repeat contributors and useful adaptations.','Keep participation inside the existing workflow rather than adding a social feed.'],
['Test usefulness across different gyms before adding other activities.','Develop contributor governance and sustainable incentives.','Assess whether the corpus is better than public alternatives.'],
['Coach contribution motivation','Content permissions','Moderation capacity'],
[('Reuse','At least 3 of 5 test coaches reuse another coach\'s contribution.'),('Contribution','At least 3 coaches contribute again without payment or founder chasing.'),('Utility','Reused material meets the agreed usefulness rubric.')],
[('Nobody contributes','Stop if repeated founder recruitment is required.'),('Public content is sufficient','Compare against existing public material.'),('Low-quality advice','Use qualified moderation and appropriate boundaries.')],
'24+ months','medium',4,'Contributor relationships and curation could compound, but the cold start and abundant substitutes are substantial.',.06)
add('Contracted deployment permissions and enterprise assurance','regulatory/permissions',False,
'Become an approved supplier with repeatable access, security evidence and customer deployment permissions. Multiple completed approvals could accelerate future sales. This is procurement know-how, not regulatory capture; no exclusive licence or statutory barrier has been identified.',
['I4','I6','I11'],
['Identify actual access and procurement requirements for one willing buyer.','List gaps honestly; do not buy certifications speculatively.','Confirm whether approved-supplier status creates any reusable advantage.'],
['Complete only prerequisites for a paid deployment.','Document security, export and incident responsibilities.','Measure which evidence can be reused with a second buyer.'],
['Invest in assurance only against a demonstrated sales pipeline.','Maintain provider approvals and tested operating procedures.','Avoid promises beyond measured support and reliability capacity.'],
['Funded buyer','Required access approvals','Operational security capability'],
[('Commercial relevance','One buyer names a specific approval that blocks a funded purchase.'),('Conversion','One approved paid production deployment.'),('Reuse','At least half of second-buyer evidence accepted without rework.')],
[('Compliance cost without demand','Tie investment to actual paid opportunities.'),('Approval mistaken for exclusivity','Record revocability and actual rights.'),('Access revoked','Maintain contract-compliant exports and tested continuity plans.')],
'12-24 months','high',3,'Approvals can slow replacement but are normally available to rivals; no structural exclusive permission is shown.',.10)
recommended=[
 dict(strategy_title=S[1]['title'],rationale='First test: small expert-labelled comparison using existing contacts. Establish whether Cornerwork can reliably make better coaching communication decisions than generic tools; stop if the rubric or advantage fails.'),
 dict(strategy_title=S[0]['title'],rationale='Conditional second asset: move from message storage to measured action/result evidence. Initial work is instrumentation and study feasibility, not an immediate retention model or data moat.'),
 dict(strategy_title=S[2]['title'],rationale='Parallel low-cost buyer discovery, later conditional build: test whether an existing vendor would purchase the capability. If funded demand exists, distribution can come through the buyer\'s installed product. This is unvalidated and may require a business-model change.')]
kill=[
 dict(strategy_title=S[1]['title'],criteria=['After one rubric revision, two independent reviewers still agree on fewer than 80% of binary acceptance decisions across 40 initial cases: stop benchmark expansion.','By day 90, no pre-specified held-out improvement over the baseline without extra review time: drop the quality-moat claim.']),
 dict(strategy_title=S[0]['title'],criteria=['By day 90, fewer than two sites permit the narrowly defined action/outcome measurement: stop cross-site data investment.','After two measurement revisions, fewer than 80% of eligible cases have interpretable delivery and outcome status: stop effectiveness modelling.','If a prospectively designed, adequately powered follow-up study rules out the pre-agreed minimum useful improvement: abandon that intervention hypothesis, not reinterpret clicks as retention.']),
 dict(strategy_title=S[2]['title'],criteria=['Fewer than two of five qualified vendor interviews identify the same funded unmet need: stop the proposed component scope.','No paid design agreement by the end of month 3: defer SDK build.','Proposed revenue fails to cover full estimated implementation and support costs within the agreed contract: reject the deal or change scope/pricing.'])]
seq=[
 dict(month='M1',focus='Founder: run the 40-case rubric exercise and five vendor interviews; define one measurable follow-up outcome. Do not build new platforms.',dependencies=['Two qualified reviewers','Existing demo','Prospective data-use permission for real cases']),
 dict(month='M2',focus='Founder plus reviewers: adjudicate disagreements and compare held-out cases; instrument two willing gym pilots. Seek a paid vendor design scope.',dependencies=['M1 rubric passes','Sites permit narrow measurement','Real buyer problem identified']),
 dict(month='M3',focus='Apply kill criteria. Select at most one funded integration; otherwise keep the useful core product and stop the OEM branch.',dependencies=['Held-out evaluation result','Data completeness audit','Paid agreement before integration work']),
 dict(month='M4',focus='If gates pass, deliver the bounded component and run the approved follow-up comparison; assess full support cost.',dependencies=['Production prerequisites and defined responsibilities','Study design adequate for intended claim']),
 dict(month='M5',focus='Test independent site transfer and interview coaches in one adjacent activity; keep sport-specific evidence separate.',dependencies=['Operational stability','Sufficient permissioned cases','Qualified adjacent-domain reviewer']),
 dict(month='M6',focus='Review renewal, quality, cost and paid second-buyer interest. Continue only the mechanisms showing evidence of repeatable advantage.',dependencies=['Full cost record','Buyer decision','Documented limitations and negative results'])]
result=dict(assumptions=assumptions,insights=insights,moat_strategies=S,recommended_portfolio=recommended,kill_criteria=kill,sequencing=seq)
assert len(S)==10 and 8<=len(insights)<=15
assert all(0<=s['probability']<.15 for s in S)
assert sum(s['probability']<.07 for s in S)>=3
assert abs(sum(s['probability'] for s in S)-1)<1e-9
assert max(Counter(s['moat_type'] for s in S).values())<=2
assert sum(s['contrarian'] for s in S)>=2
assert len(recommended)==3 and len(kill)==3 and len(seq)==6
for s in S:
 assert all(3<=len(v)<=6 for v in s['implementation_plan'].values())
 assert 3<=len(s['metrics'])<=6 and 3<=len(s['risks_and_mitigations'])<=6
 assert all(r in {i['id'] for i in insights} for r in s['research_link'])
assert all(2<=len(k['criteria'])<=3 for k in kill)
p=base/'2026-09-28-productize-moat-portfolio.json'
p.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
assert json.loads(p.read_text(encoding='utf-8'))==result
print(f'Validated: {len(insights)} insights, {len(S)} strategies, 3 recommendations, 6 months. Saved {p}')
