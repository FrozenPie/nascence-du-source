# Strings and Sheets: re-pick candidates for the 10 wrong-file keys (J-2441, 2026-10-19)

Status: CANDIDATE LIST FOR FOUNDER REVIEW. Nothing has been downloaded, fetched as audio, or saved. Under D-0377 (reviewed before download) Travis approves this list first.

Origin: F-3141 (Travis's by-ear check, J-2402). Sources follow D-0377 and `docs/lab/strings_sheets_phase4_manifest.md`: Freesound CC0 1.0 only, xeno-canto (CC BY-NC-SA 4.0 / CC BY 4.0, local derivative features only), DOC NZ.

## Honest limits

- **Nobody has listened to any candidate.** Fit is judged from the page title, uploader description, tags, duration and comments, exactly the weakness the manifest warns about (the 10 failures came from the same method). Treat every "why it fits" as a hypothesis for a by-ear check.
- Licence and duration were read from each item page in this session (Freesound pages via WebFetch; xeno-canto pages via the browser pane). Freesound search listings show durations that sometimes differ from the page, so the page value is given.
- Freesound files would again be the ~128 kbps HQ preview (as in the manifest).
- Several searches returned zero results or were rate limited (HTTP 429), so coverage is partial, not exhaustive.
- Not a CAPTCHA bypass: xeno-canto showed its automatic "verifying visitor" page for the browser pane, which resolved on its own after a few seconds; plain WebFetch was denied, so xeno-canto data came from the pane.

## 1. `kingfisher_call` ("a dry staccato kek-kek-kek from a high perch")

Old file XC973960 was a *begging* call with 99% of energy below 300 Hz (rumble), so the energy axis tracked rumble. Candidates are all New Zealand, type "call", not playback.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://xeno-canto.org/293157 (XC293157, Dan Lane, Pureora, 2015) | 14.1 s | CC BY-NC-SA 4.0 | Remarks: "Natural rasp call and a bit of song" from a bird about 4 m up in midstory of native forest (the "high perch"). Typed call+song, short, so little room for rumble. | Includes "a bit of song"; "rasp" is not necessarily staccato kek. Rating not read. |
| b | https://xeno-canto.org/436725 (XC436725, Matt Slaymaker, Sanctuary Mountain, 2018) | 36.1 s, mp3 320 kbps | CC BY-NC-SA 4.0 | Typed call, no playback, background "none". "Two birds calling": likely a kek series from a pair. | Two birds may overlap and blur the periodicity; recordist remarks say nothing about kek. |
| c | https://xeno-canto.org/983505 (XC983505, Meena Haribal, Auckland, 2024) | 26.5 s, wav | CC BY-NC-SA 4.0 | Typed call, no playback, A-rated filter hit (query was q:A). | No remarks; urban Auckland site so traffic rumble is possible. Same failure class as old pick if rumble dominates. |

Suggest (a) first; low-band rumble can only be checked after download, so confirm by signal analysis and by ear after approval.

## 2. `wood_snap` ("a single crack from the deadfall")

Old pick 444007 ("Breaking A Branch") had more than one crack.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/martian/sounds/251464/ ("twig snap classic.wav") | 0.38 s | CC0 | Sub-half-second, tagged pop/snap/stick/twig, keyword line "twig snap stick pop nut crack"; strongly implies one event. Same uploader as an already-used manifest source (martian, cat_lapping). Two positive comments. | Very short (target is about 3 s); window logic would need padding or the key's duration expectation relaxed. Denoised. Twig, not deadfall branch. |
| b | https://freesound.org/people/payattention/sounds/82802/ ("stick snap.wav") | 3.5 s | CC0 | Description: "a stick being snapped in half"; 3.5 s matches the 3 s target. 646 downloads. | Page does not say single vs multiple; tags (click, tick, rubber-band, wasp) are noisy and suggest possible extra clicks/tail. |

Rejected: https://freesound.org/people/CheatinSloth/sounds/738787/ (1:08 of many chopstick snaps, explicitly multiple).

## 3. `herb_cut` ("a single snip of the shears")

Old pick 800082 (a Foley pack of snips) was rejected.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/BaggoNotes/sounds/704261/ ("Scissor_Close.wav") | 0.37 s | CC0 | Description "Snipping shut children's scissors" (one action), tags Short/Snip. Best single-snip evidence found. | Children's scissors, very short; a herb shear would be slightly more metallic/crisp. |
| b | https://freesound.org/people/evedel/sounds/517518/ ("scissors.m4a") | about 4 s (listing; page not opened) | CC0 (filtered listing; page not opened) | Plain scissors clip near the 3 s target. | Not opened: count of snips unknown; may be several. Verify before use. |

Rejected (multiple snips): Colonnades 792726 (13.3 s, "Scissor Snips"), RealSquink 788314 (19.3 s, snipping sequence).

## 4. `cat_chatter` ("fast dry jaw-chatter, many onsets"; Travis: "Not a very good one")

Old pick 850108 (3 s, "Excited and desperate chatter"). The same uploader, CatPhony, has two sibling items in the CC0 search for "cat chatter".

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/CatPhony/sounds/850103/ ("Chatter and Trill") | 3.9 s | CC0 | Description "Cat chatters and trills at a bird", tags cat/chatter/trill; phone recording with background noise removed. Genuine bird-directed chatter. | Includes a trill, which may soften the "dry jaw-chatter, many onsets" line; same uploader and recording style as the rejected pick, so may share its weakness. 19 downloads, no comments. |
| b | https://freesound.org/people/CatPhony/sounds/844717/ ("Chatter and Purr") | 2.7 s | CC0 | "Cat chatters at a bird and purrs." | Short; includes a purr; same uploader. |

Doubt overall: only 3 CC0 results for this query ("cat chatter chattering bird"); a CC0 chatter library is thin. Possible outcome: constructed-only, as was done for `moth_tap` (D-0477).

## 5. `cat_lapping` ("rapid liquid ticking"; Travis: "not very good")

Old pick 180275 ("cat bowl lapping milk").

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/PhilllChabbb/sounds/345983/ ("Cat Licking Water In Cup") | 55.5 s | CC0 | Tags cat, cup, drinking, lap, lapping, water; recorded on H4n; comment "Good quality". Water lapping gives liquid ticking; long enough to window a dense stretch. | Unknown where the dense lapping sits in 55 s; a cup resonance may colour it. |
| b | https://freesound.org/people/cognito%20perceptu/sounds/35900/ ("lapping.wav") | 9.8 s | CC0 | Description: cat lapping tuna juice, "very squishy sound". Right length for the 10 s target. | "Squishy" may be wetter/lower than "dry liquid ticking"; 2009-era upload, quality unknown. Sibling item 18512 (same uploader) not opened. |

## 6. `cat_purr` ("continuous very-low periodic bed"; Travis: "I cannot hear any purring")

Old pick 463790 ("Cat Purr.wav", 17.5 s) had no audible purr. Candidates were chosen for evidence the purr is loud and the recording is dedicated.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/aunrea/sounds/485373/ ("Cat Purring") | 8.5 s | CC0 | Male cat purring on a bed, Tascam DR-100MKIII + AT875R shotgun; tags purr/purring. Two positive comments ("exactly what we needed", "so good recording"). | Short (target is about 20 s); shotgun mic at unknown distance. |
| b | https://freesound.org/people/TSP-Talk/sounds/846064/ ("Norwegian Forest Cat - Purring & Grooming in Quiet Living Room (192 kHz)") | 103.96 s | CC0 | Description: first minute is mostly steady purring (a clean 20 s window exists); no EQ/filter/noise reduction, only gain+normalise; tags close-up, low-frequency, vibration, purr. | After 1:00 grooming/licking textures appear (use the first minute only). 192 kHz master but Freesound preview would be about 128 kbps mp3, which is fine for a low periodic bed. |
| c | https://bigsoundbank.com/cat-purr-s0436.html ("cat purr s0436") | 11 s | CC0 (stated on page) | "Loud, low-pitched, very dry purring" of an 8-month-old male cat, recorded about 10 cm from the muzzle. Most explicitly purr-forward description found. | **BigSoundBank is not a source named in D-0377 or the manifest**; needs Travis's explicit OK. Page admits "possibly too close and too much on axis", slight breath noise. |

## 7. `cat_yowl_cargo` ("the muffled announcing yowl, mouth full"; Travis: "Very bad, do not use")

Weak key by the manifest's own note (the recordings list says a mouth-full yowl "is rare"). No CC0 recording described as a carrying-prey or mouth-full call was found (searches "cat prey mouse meow", "cat carrying meow", "cat meow muffled" returned zero CC0 results). Candidates are therefore approximations; the honest alternative is constructed-only.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/tcurless/sounds/826683/ ("Siamese Cat Yowls") | 14.3 s | CC0 | A sustained "unearthly" yowl from an indoor cat (tags howl, yowl). Tonal announcing yowl. | Recorded in a bathtub with echo (not muffled); Siamese voice is thin. Approximates "announcing", not "mouth full". |
| b | https://freesound.org/people/olivierklein/sounds/815301/ ("Cat yowling - distant then close-up") | 121.8 s | CC0 | Quiet interior, no resonance, about a dozen takes, phone recording; the "distant" takes give a muffled quality. | Long; the distant segment location unknown; not mouth-full. |
| c | https://freesound.org/people/_stubb/sounds/406613/ ("Cat Meowing_Yowl_far_mono.wav") | 1.9 s | CC0 | "far" in the title suggests attenuated/muffled; tagged yowl. | Very short (target 3-8 s); page description is just "Cat meowing." |

Rejected: Organuz 686623 (15 min of a neighbourhood catfight, not a single announcing call).

## 8. `chair_desk_scrape` ("his own chair, scraped back"; Travis: "no good, do not use")

Old pick 188204 (27 s wooden chair slide on wood floor) was judged no good; the by-ear sheet does not say why (too long, too repeated, or wrong timbre are all possible, so ask).

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/bangcorrupt/sounds/832998/ ("Chair Scrape") | 8.5 s | CC0 | Wooden chair dragged across laminate floor in a small room, M/S Zoom H2n, tags squeaky/scrape/wood; short enough for the 4 s target, indoor like a study. | Built from two samples crossfaded, so it is not one continuous scrape. Page description also says free for non-commercial use and commercial by negotiation although the licence tag reads CC0; check this licence conflict before relying on it. |
| b | https://freesound.org/people/kyles/sounds/455673/ ("chair wood old push slide across concrete floor scrape") | 13.7 s | CC0 | Old wooden chair pushed and slid; title describes one action. | Concrete floor, not a desk-room surface; no description; scrape count unknown. |
| c | https://freesound.org/people/JohnsonBrandEditing/sounds/173940/ ("wood chair scrape on floor, papers,") | 33.7 s | CC0 | Wood chair on floor with paper (desk context); five comments, positive. | 34 s, repeated scrapes likely, may repeat the old file's failure. |

## 9. `woodpile_settle` ("the stocked woodpile settling at night"; Travis: "sounds like a car crash")

Old pick 811116 ("log collapse 1") was a loud collapse. The key needs a soft, small shift. Candidates here are weak; the CC0 filter returned 0 results for "woodpile logs", "log pile shift" and one result pair for "wood creak settle".

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/rombart/sounds/316728/ ("Bois-empile.wav") | 41.4 s | CC0 | Logs being piled up, 48 kHz/24 bit, denoised; contains many small wood-on-wood contacts to window a soft passage from. | It is deliberate piling (impacts), not settling; may contain loud thuds. |
| b | https://freesound.org/people/SuperSoundEater/sounds/761886/ ("Wood sticks 4") | 0.38 s | CC0 | "Wood falling on a pile of wood", one small clack, no car-crash energy. | Only 0.38 s, phone recording; a single clack is not a settle. Could be layered or used as a one-event version. |
| c | https://freesound.org/people/Sadiquecat/sounds/801812/ ("Moving woody gravel by hand (XY)") | 3.65 s | CC0 | Soft dry shifting of wood bark rubble in front of the mic, gentle rattle texture. | Bark rubble, not logs. Indoor France recording. |

Honest read: no candidate is a true quiet woodpile settle; probably the better route is a founder decision to accept (a) windowed on a soft passage, or mark the key constructed-only.

## 10. `cicada_chorus` ("loud continuous rough high wall"; Travis: "one cicada, not a chorus")

Old pick 824925 ("Cicadas W breeze 2"). The recordings list wanted an NZ chorus cicada (Amphipsalta zelandica). xeno-canto has no Amphipsalta recordings (search for "Amphipsalta" in the pane returned "No recordings found"). All candidates below are non-NZ Freesound CC0 choruses.

| # | Source | Length | Licence | Why it fits | Doubt |
|---|---|---|---|---|---|
| a | https://freesound.org/people/BayTsai/sounds/860235/ (Alishan Forest, Taiwan) | 56 s | CC0 | Described as "a heavy, immersive wall of sound consisting entirely of cicada choruses"; tags chorus, dense, wall-of-sound. The strongest chorus evidence found. | Taiwanese species; midday forest. Possibly very high-frequency wall; nothing about birds. |
| b | https://freesound.org/people/heyheymaimai/sounds/493058/ (Periodical cicada chorus, Pennsylvania) | 24.7 s | CC0 | "A chorus of 13-year periodical cicadas" (a swarm, tag swarm). | Periodical cicadas are a pulsing drone, a different character from NZ "clapping" chorus cicadas. |
| c | https://freesound.org/people/marc.om/sounds/806571/ (Erawan Forest, Thailand) | 60.2 s | CC0 | "Intense cicada chorus in the forest", high-pitched. | Tropical forest; may carry other insects/birds. |

NZ-species alternatives found by web search (not on a D-0377 source, NOT recommended without a founder ruling on licence): Te Papa (tepapa.govt.nz, chorus cicada sound clip), Te Ara (teara.govt.nz natural sounds; page says reuse may need clearance from the rights holder), BioAcoustica (bio.acousti.ca/node/13326, recording near Kaitaia 2006; filtered below 2 kHz; page returned 403 so the licence was not read), Macaulay Library (asset 161797, mixed cicada tape). None was opened; licences unverified.

## Summary

| Key | First choice | Confidence |
|---|---|---|
| kingfisher_call | xeno-canto XC293157 | medium |
| wood_snap | Freesound 251464 (or 82802 if length matters) | medium |
| herb_cut | Freesound 704261 | medium |
| cat_chatter | Freesound 850103 | low (thin supply; consider constructed-only) |
| cat_lapping | Freesound 345983 | medium |
| cat_purr | Freesound 846064 (first minute) or 485373 | medium-high |
| cat_yowl_cargo | Freesound 826683 (approximation) | low (consider constructed-only) |
| chair_desk_scrape | Freesound 832998 (check licence note) | medium |
| woodpile_settle | Freesound 316728 (window a soft passage) | low |
| cicada_chorus | Freesound 860235 | medium-high |

Every pick still needs a by-ear check after download approval, then re-measurement and re-seed under the J-2402 / D-0376 / D-0377 rules.
