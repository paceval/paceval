# Research sources and provenance

Source review date: 15 November 2026. The latest release and revision status of international standards must be verified again before industrial use. Sources provide background, not paceval result certification.

1. **FCL (Flexible Collision Library).** ROS indexed project documentation describes discrete and continuous collision and distance queries, supported geometry including spheres, capsules and mesh, and the project's provenance. https://index.ros.org/p/fcl/
2. **MoveIt developer concepts.** Official project documentation describes the FCL/Bullet collision environment and geometry management. https://moveit.ai/documentation/concepts/developer_concepts/
3. **MoveIt / OMPL edge discretization.** Documentation explains the longest-valid-segment fraction and limitations of discretized motion checking. https://moveit.github.io/moveit_tutorials/doc/ompl_interface/ompl_interface_tutorial.html
4. **Jung, Son and Kim (2025).** NeuralSVCD for Efficient Swept Volume Collision Detection, Conference on Robot Learning / PMLR 305. Current research on swept-volume collision methods. https://proceedings.mlr.press/v305/jung25e.html
5. **Distance fields for robot avoidance (2026).** Robotics and Autonomous Systems, doi:10.1016/j.robot.2026.105394. Uses Bernstein representations for continuous geometry within a different controller setting. https://doi.org/10.1016/j.robot.2026.105394
6. **ISO 10218-1 and ISO 10218-2 (2025).** Robot and cell safety requirements, not supplied as freely licensed standard text in this project. https://www.iso.org/sectors/engineering/robotics
7. **ISO/TS 15066:2016.** Collaborative robot technical specification, reviewed/confirmed 2022; application-level requirements must consider newer ISO 10218-2:2025. https://committee.iso.org/standard/62996.html
8. **Bernstein convex-hull interval property (Reliable Computing).** Mathematical foundation for enclosing a univariate polynomial's value range in the range of Bernstein control coefficients on each subinterval. https://interval.louisiana.edu/reliable-computing-journal/volume-14/reliable-computing-14-pp-117-137.pdf
9. **Continuous Collision Detection benchmark.** Community resource on CCD benchmarks and correctness of exact/interval formulations, useful for future external crosschecks. https://continuous-collision-detection.github.io/
10. **Original paceval API.** SDK functions and batch evaluation. Signatures were separately checked against the supplied header and compiled local runtime. https://paceval.com/api/

The original `docs/original_WP26_brief.pdf` is a two-page proposal, not previously executed research. The extended 3D quadratic sphere model, deterministic dyadic dataset, exact rational certification and all reported numerical outputs are newly constructed within WP 26.
