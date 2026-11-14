# Independent source overview (checked November 2026)

The original WP 21 defines four candidate expression families and proposes one thousand candidate thermal recipes, ten representative thermal nodes, and independent DSC-model checks if measured data are available. This implemented study develops a **smaller fully executed and independently checked 36-recipe / 10-node transient integration**, rather than claiming to have run one thousand full transient cases. All real outputs are in `results/`.

1. Original user-supplied WP 21 (archived at `docs/original_WP21_brief.pdf`): study hypothesis, Kamal-Sourour, volumetric heat, and qualitative constraints.
2. Kamal-Sourour kinetics and cure modeling, Polymers 2019: https://pmc.ncbi.nlm.nih.gov/articles/PMC6401829/
3. Vitrification and DiBenedetto glass-transition relation, Polymers 2019: https://www.mdpi.com/2073-4360/11/11/1804
4. Full thermal-fluid-solid coupling in autoclave composites, Materials 2025: https://www.mdpi.com/1996-1944/18/7/1471
5. Variable thermal boundary-condition effects, Composites Part A, July 2026: https://www.sciencedirect.com/science/article/pii/S1359835X26002496
6. Tool-part interaction and real-time autoclave cure control, Chinese Journal of Aeronautics, March 2026: https://www.sciencedirect.com/science/article/pii/S1000936125005540
7. A review of curing model paradigms and limits, Composites Part A, August 2026: https://www.sciencedirect.com/science/article/abs/pii/S1359835X26002460
8. Hexcel prepreg cure guidelines (industrial company guidance, not independent product-performance certification): https://www.hexcel.com/wp-content/uploads/2026/01/Prepreg_Technology.pdf
9. Ansys Composite Cure Simulation documentation, mathematical and industrial software context: https://storage.ansys.com/mbu-assets/accs/v221/ug/Best_Practices.html
10. Original paceval API and function signatures: https://paceval.com/api/

The source list establishes background context, *not* provenance for the synthetic coefficients chosen for this project. No external calibration and no claims of optimality are made. The 2026 works establish ongoing interest in more elaborate boundary-condition and tool-part models, not a measured advantage of paceval over dedicated software.
