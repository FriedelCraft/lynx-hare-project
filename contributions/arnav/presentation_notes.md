# Arnav's two-minute presentation and explanation guide

## Suggested two-slide content

**Slide 1 — Question and model.** Show the two dimensional equations, a one-line explanation of logistic growth and saturating consumption, and a short note that pelts are abundance proxies. Avoid putting the whole parameter table on the slide.

**Slide 2 — Scaling and handoff.** Show x = H/K, y = aP/(rK), s = rt and the three dimensionless groups. End with the link to stability analysis and fair held-out validation. These are slide notes, not a separate PowerPoint deck.

## Speaking script

Our question is whether a simple predator-prey model can explain recurring hare and lynx fluctuations and make useful predictions beyond the years used for fitting. The historical measurements are traded pelts, so we treat them as abundance indices rather than exact animal populations.

We begin with Lotka–Volterra. It models prey growth, encounters, predator reproduction and mortality. Its limitation is that a conserved quantity produces neutral cycles: a disturbed trajectory moves to another orbit instead of returning to one preferred cycle. Without predators, the prey also grows without a resource limit.

We therefore use logistic prey growth and a Holling type II consumption rate. Logistic growth introduces carrying capacity K. Consumption is aH divided by b plus H: a is the maximum rate per predator, and b is the hare abundance at half that rate. Multiplying consumption by P gives total prey loss, and multiplying again by e gives predator gain. Predator mortality contributes minus mP.

I checked the units and derived a dimensionless form. Time is scaled by one over r, hares by K, and lynxes by rK over a. This leaves three ratios: b over K, ea over r, and m over r. The notation matches Joel's theory section. If K changes, scaled initial states must also change to keep the original starting populations fixed.

The report also maps these variables to the PINN's fixed training normalization, so both descriptions remain consistent. Our next claims must come from stability analysis, checked simulations and held-out observations. A sophisticated method or a good training fit alone does not establish predictive accuracy.

Rehearse aloud and shorten to your actual pace; the time estimate has not been verified by an audio recording.

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

## Sources for the slide footnotes

Slide 1: [Rosenzweig and MacArthur 1963](https://doi.org/10.1086/282272), [Holling 1959](https://doi.org/10.4039/Ent91385-7), and [Carpenter 2018](https://mc-stan.org/learn-stan/case-studies/lotka-volterra-predator-prey.html). Slide 2: the derivation in this package and [Joel's existing dimensionless convention](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/report/joel_stability_section.tex); PINN compatibility follows [Yash's method](https://github.com/FriedelCraft/lynx-hare-project/blob/7d17deee1cb685f016ff16cb6706e8db12ebe6b2/docs/method.md).
