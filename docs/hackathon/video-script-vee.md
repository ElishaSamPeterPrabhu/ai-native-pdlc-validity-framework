# Hackathon video: Script B, narrated by Vee

Same five phases and timestamps as [`video-plan.md`](video-plan.md) (Script A), so one edit timeline serves both. You record the audio; Vee is the on-screen guide.

**Vee:** a small original pixel robot, 16x16 sprite. Steel-blue head with a short antenna, a visor whose pixel eyes change expression, a red heart light on the chest (the human side), a lanyard badge reading REVIEWER, mitten hands, simple boots. Named after V*, the validity value.

**Poses:** idle, wave, point, think, overwhelmed (buried under PRs), celebrate.

**Delivery:** short sentences, friendly, a little dry. Numbers are read exactly as on the card. Say "associated with" for Faros and DORA.

| Time | Phase | Visual from Script A |
| --- | --- | --- |
| 0:00-0:40 | 1 Speed | CARD-01, REC-01 |
| 0:40-1:40 | 2 Trust bottleneck | REC-02, REC-03, CARD-02, CARD-02a-e, SHOT-01 |
| 1:40-3:05 | 3 Toolkit and formula | CARD-03, REC-04, MON-01 or REC-05, MON-02 or SHOT-02, CARD-04, SHOT-03 |
| 3:05-4:00 | 4 Beyond code | REC-06, SHOT-04, CARD-05 |
| 4:00-5:00 | 5 End-state | MON-04 or REC-03, REC-08, CARD-06 |

---

## Phase 1 (0:00-0:40)

| Time | Vee says | Pose | On screen |
| --- | --- | --- | --- |
| 0:00 | "Hi. I'm Vee." | wave | "VEE" name tag, CARD-01 |
| 0:04 | "A while ago, a feature took days of typing." | idle | "days" side of the split timeline |
| 0:12 | "Now I read an approved ticket and open a pull request in minutes." | run | "minutes" side, REC-01 sped up |
| 0:28 | "Writing code? That part is close to free." | celebrate | "Code is cheap" |
| 0:34 | "So what's slow now?" | think | question mark over the track |

## Phase 2 (0:40-1:40)

| Time | Vee says | Pose | On screen |
| --- | --- | --- | --- |
| 0:40 | "Every one of my pull requests still lands on one person." | point | REC-02: PR list |
| 0:50 | "That person has to read all of it. Review is the new bottleneck." | overwhelmed | REC-02: long thread, big diff; PR blocks pile on Vee |
| 1:00 | "Teams using AI a lot merge nearly twice the pull requests, and review time goes up with it. That's associated, not proven, but it's what the data shows." | think | CARD-02a, Faros source |
| 1:12 | "And the code that's almost right is the hardest to catch. Two in three developers say that's their top frustration." | idle | CARD-02b, Stack Overflow source |
| 1:24 | "Feeling faster isn't being faster. In one trial, developers were nineteen percent slower, and still thought they were twenty percent faster." | think | CARD-02c, METR source, early-2025 caveat |
| 1:34 | "So don't review harder. Trust the code by design." | point | CARD-02: four trust killers fade in |

## Phase 3 (1:40-3:05)

| Time | Vee says | Pose | On screen |
| --- | --- | --- | --- |
| 1:40 | "By design means the workflow does the checking: hooks, rules, skills, and validation that run on every change." | point | CARD-03: Build, Monitor, Measure, Improve |
| 1:52 | "You drop in the starter kit and ask for the workflow builder." | idle | REC-04: Cursor chat |
| 2:05 | "It reads your repo, asks how your team works, and writes the Dev, QA and Fix automations." | point | REC-04 continues |
| 2:20 | "Here's what that looks like on a real pull request. QA failed. The fix landed. QA passed." | celebrate | MON-01 or REC-05: #1509 |
| 2:35 | "Then the formula scores the setup. Recovery is what catches mistakes. Decay is what wears trust down. Validity is the balance." | think | CARD-04, then MON-02 or SHOT-02 |
| 2:50 | "In our pilot, one change took the directional score from 0.56 to 0.74. Placeholder weights, so read it as a direction, not a fitted number." | point | evidence caption with provenance |
| 3:00 | "Weakest layer, one fix, run it again." | wave | SHOT-03 |

## Phase 4 (3:05-4:00)

| Time | Vee says | Pose | On screen |
| --- | --- | --- | --- |
| 3:05 | "This isn't only for code." | idle | CARD-05: domain chips |
| 3:12 | "Meeting notes become a reviewed row. A person approves it, and a ticket appears." | point | REC-06: sheet flow |
| 3:30 | "Same skills, same rules, same human gates." | think | SHOT-04: product-to-issue map |
| 3:40 | "In a replayed test, the skills beat a bare agent: point nine nine against point six four on engineering, point nine eight against point four seven on tickets, and on tickets the bare agent broke a safety rule four times, the skills never did." | celebrate | evidence caption, n=3, replayed persona |
| 3:54 | "Design checks in Figma work the same way, and docs are next." | idle | CARD-05 chips: Design (Figma agents) highlighted, Docs and Data marked "not yet piloted" |

## Phase 5 (4:00-5:00)

| Time | Vee says | Pose | On screen |
| --- | --- | --- | --- |
| 4:00 | "The goal isn't more code." | idle | MON-04 or REC-03 full screen |
| 4:08 | "It's less friction. I build. The monitor watches. The formula measures. The skills fix the weak spots." | point | wall of lifelines, throughput strip |
| 4:30 | "You write the tickets. You decide what to build. You approve the result." | wave | REC-08: human gate |
| 4:48 | "Build it, watch it, measure it, improve it." | celebrate | title text |
| 4:54 | "Make AI delivery trustworthy by design." | idle | CARD-06: pip install, starter-kit, repo URL |
