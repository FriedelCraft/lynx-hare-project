# Arnav's final presentation material

Updated 28 October 2026. Use the two editable slides in `arnav_model_slides.pptx`; import them into the group presentation before Joel's section. The deck includes speaker notes and sources.

## Slide sequence and timing

1. **Model and pelt observations:** explain the two equations and O1. Allocate about one minute.
2. **Scaling and interpretation:** explain the scales, conditional biological interpretation and evaluation handoff. Allocate about one minute.

## Speaking script

Our question is whether a predator-prey model can explain the fluctuations and support useful forecasts. The observations are traded pelts, so H and P represent indices in thousands of pelts, rather than measured animal populations. O1 assumes constant proportionality between those indices and animal abundance. We absorb the unknown constants into the effective coefficients and fit no extra observation-scale factors. Annual totals are approximated as point samples with observation error.

Lotka-Volterra gives neutral cycles and unlimited predator-free prey growth. We add logistic resource limitation and saturating predation. In aH divided by b plus H, a is the maximum effective consumption coefficient and b is the hare index at half saturation. Multiplying by P gives prey loss; e converts that loss into predator gain, while mP describes mortality.

Scaling time by one over r, hares by K, and lynxes by rK over a gives these dimensionless equations. The notation matches Joel's analysis. The groups compare half saturation with carrying capacity, maximum predator growth with prey growth, and mortality with prey growth.

K, b, a and e depend on the index units. Constant observation scaling leaves r, m and the groups unchanged, but does not prove that fitted parameters are biologically accurate. The PINN retains fixed training normalization; the report supplies the mapping.

Fitting uses 1900 to 1915. Forecasts integrate frozen parameters from 1900, without restarting from a test observation. Separate hare and lynx errors assess the five held-out years. Stability classifications describe the fitted model; they do not establish a stable cycle in the real ecosystem.

The script has 255 words (whitespace count); at 140-150 words per minute it takes roughly two minutes, with additional time for pointing at equations. Rehearse and adjust to your actual pace. No timed personal rehearsal has been recorded.

## Questions you should be able to answer

**Why is the encounter coefficient not a?** At low prey abundance, aH/(b+H) is approximately (a/b)H. Thus a/b is the linear encounter coefficient; a is the saturated rate.

**What precisely does neutral stability mean here?** A nearby initial state stays on a nearby conserved orbit rather than converging to the original orbit. The positive equilibrium is a centre. It is not asymptotically stable.

**Why does logistic growth use 1−H/K?** It is the simplest linear decline in per-capita growth that is r at H=0 and zero at H=K. This is a modelling assumption, not a universal law of ecology.

**Why scale the predator by rK/a?** After substituting H=Kx and P=(rK/a)y, prey growth and prey consumption both carry a factor rK. Dividing through makes the predation coefficient one.

**Does the model force negative populations to zero?** No clipping is part of the mathematical model. Each derivative contains its own state as a factor, making zero boundaries invariant and keeping positive exact solutions positive. Numerical approximations still require checks.

**Can e exceed one?** Its meaning depends on units. With different species indices it has units UP/UH and is an effective conversion factor. An unqualified dimensionless biomass-efficiency interpretation is unjustified.

**Why not train the PINN directly with your scales?** r and a are trainable, so those coordinates would depend on unknown parameters. Fixed training-data normalization is simpler; the report proves the mapping between the coordinates.

**Does three dimensionless parameters mean six rates are identifiable?** No. Dimensionless groups describe combinations of parameters. Recovering six dimensional values also requires scale information, and identifiability depends on the data and observation model.

**What was independently checked?** The equations were derived term by term, their dimensions and boundary behaviour were inspected, and transformations were checked with exact rational arithmetic at multiple inputs. This does not validate real-world forecasts.

**What is the contribution beyond citing a known model?** An explained derivation, a consistent units and observation convention, a justified scaling choice, and a checked bridge to the actual implementation. The model itself is established literature, not a new discovery.

**Does no fitted observation scale mean cH=cP=1?** No. We choose model states already in pelt units and absorb unknown constants into effective coefficients. We cannot recover animal counts from this choice.

**Why do annual totals have state units instead of a rate unit?** This model approximates each annual count by a point-state observation. That is a declared approximation. H is in thousands of pelts and Hdot is in thousands of pelts per year.

**Why retain the soft initial-condition caveat?** The main ODE forecast starts exactly at (30,4), but the network is only penalized for missing that state. The historical implementation records that discrepancy; matching target values does not make the network constraint exact.

**What does the completed historical configuration fit?** All six coefficients. It imposes positive bounds without e<=1 or a coexistence constraint. These are the recorded settings, not proof of biological parameter ranges.

## Sources for slides and speaker notes

Slide 1 cites [Holling 1959](https://doi.org/10.4039/Ent91385-7), [Rosenzweig and MacArthur 1963](https://doi.org/10.1086/282272), [Carpenter 2018](https://mc-stan.org/learn-stan/case-studies/lotka-volterra-predator-prey.html), and [Advay's observation convention](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/docs/advay_observation_convention.md).

Slide 2 uses this contribution's derivation, [Joel's notation](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/report/joel_stability_section.tex), the [historical configuration](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/configs/historical.json) and [Yash's historical handoff](https://github.com/FriedelCraft/lynx-hare-project/blob/28dbe1e2a611719f3d65e5922db528ae423724f2/docs/yash_historical_handoff.md).

The script is AI-assisted. Use first-person claims about derivation or checking only for work you actually performed, and record that work in `ai_acknowledgement.md`.
